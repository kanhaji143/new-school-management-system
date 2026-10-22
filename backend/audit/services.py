"""Operational database backups and integrity verification."""
import hashlib
import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from .models import Backup


class BackupError(Exception):
    pass


def create_backup(*, actor=None):
    """Write a consistent SQLite snapshot and persist checksum metadata.

    Backups are global database snapshots (not tenant exports), so the endpoint
    is intentionally restricted to SUPER_ADMIN. Other database engines must
    be backed up by their managed/platform tooling.
    """
    if connection.vendor != "sqlite":
        raise BackupError(
            "In-app backups currently support SQLite only; configure managed database backups for this engine."
        )

    target_dir = Path(settings.MEDIA_ROOT) / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%dT%H%M%S%fZ")
    path = target_dir / f"school-{timestamp}.sqlite3"
    try:
        connection.ensure_connection()
        # serialize() creates an in-memory consistent snapshot and avoids
        # backup-lock deadlocks when a request is inside an outer transaction.
        snapshot = connection.connection.serialize()
        path.write_bytes(snapshot)
        check_db = sqlite3.connect(str(path))
        try:
            integrity = check_db.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check_db.close()
        if integrity != "ok":
            raise BackupError(f"SQLite integrity check failed: {integrity}")

        backup = Backup.objects.create(
            institution=None,
            kind=Backup.Kind.FULL,
            path=str(path),
            size_bytes=path.stat().st_size,
            checksum=hashlib.sha256(snapshot).hexdigest(),
            status=Backup.Status.SUCCESS,
        )
        return backup
    except Exception as exc:
        path.unlink(missing_ok=True)
        if isinstance(exc, BackupError):
            raise
        raise BackupError(f"Backup failed: {exc}") from exc


def verify_backup(backup):
    """Restore the snapshot into an isolated temp DB and verify its contents.

    The live database is never opened for writing during this test. A successful
    restore copy must pass SQLite integrity_check and contain schema tables.
    """
    path = Path(backup.path)
    if not path.is_file():
        backup.restore_tested_at = timezone.now()
        backup.restore_test_passed = False
        backup.save(update_fields=["restore_tested_at", "restore_test_passed", "updated_at"])
        return False, "Backup file is missing."

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != backup.checksum:
        backup.restore_tested_at = timezone.now()
        backup.restore_test_passed = False
        backup.save(update_fields=["restore_tested_at", "restore_test_passed", "updated_at"])
        return False, "Checksum mismatch."

    try:
        readonly_uri = path.resolve().as_uri() + "?mode=ro"
        with tempfile.TemporaryDirectory(prefix="restore-test-", dir=path.parent) as temp_dir:
            restored_path = Path(temp_dir) / "restored.sqlite3"
            source = sqlite3.connect(readonly_uri, uri=True)
            restored = sqlite3.connect(str(restored_path))
            try:
                source.backup(restored)
                result = restored.execute("PRAGMA integrity_check").fetchone()[0]
                table_count = restored.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchone()[0]
            finally:
                restored.close()
                source.close()
            passed = result == "ok" and table_count > 0
            if result == "ok" and table_count == 0:
                result = "restored database contains no application tables"
    except (sqlite3.Error, OSError) as exc:
        passed = False
        result = str(exc)

    backup.restore_tested_at = timezone.now()
    backup.restore_test_passed = passed
    backup.save(update_fields=["restore_tested_at", "restore_test_passed", "updated_at"])
    return passed, "Isolated restore test passed." if passed else f"Isolated restore test failed: {result}"
