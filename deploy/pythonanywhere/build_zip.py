"""Build a zip of the backend for manual upload to PythonAnywhere.

The archive contains the Django project files plus `setup.py` (one-shot
bootstrap) and `wsgi_template.py` (Web tab configuration). Migrations are
included so `manage.py migrate` works on the server.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "backend"
HERE = Path(__file__).resolve().parent
OUT = HERE / "school-backend.zip"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "media", "staticfiles", "node_modules", ".venv"}
EXCLUDE_SUFFIX = {".pyc", ".sqlite3", ".log"}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            if path.suffix in EXCLUDE_SUFFIX:
                continue
            archive.write(path, path.relative_to(ROOT))
            count += 1
        for extra, name in ((HERE / "setup.py", "setup.py"), (HERE / "wsgi.py", "wsgi_template.py")):
            archive.write(extra, name)
            count += 1
    print(f"Created {OUT} with {count} files")


if __name__ == "__main__":
    main()
