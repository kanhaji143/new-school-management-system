"""PythonAnywhere deployment helper.

Creates the virtualenv, installs dependencies, applies migrations and seeds
the demo data. Run it from the PythonAnywhere Bash console:

    bash ~/school-setup.sh
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

HOME = Path.home()
PROJECT_DIR = HOME / "school" / "backend"
VENV_DIR = HOME / ".virtualenvs" / "schoolapi"


def run(command, **kwargs):
    print(f"$ {' '.join(command)}")
    subprocess.run(command, check=True, **kwargs)


def main():
    if not PROJECT_DIR.exists():
        sys.exit(
            f"Project not found at {PROJECT_DIR}. Upload the project folder to "
            "$HOME/school first (Files tab -> upload -> unzip)."
        )

    if not VENV_DIR.exists():
        print("Creating virtualenv...")
        venv.create(VENV_DIR, with_pip=True)

    python = VENV_DIR / "bin" / "python"
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", str(PROJECT_DIR / "requirements.txt")])

    os.chdir(PROJECT_DIR)
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"}
    run([str(python), "manage.py", "migrate", "--noinput"], env=env)
    run([str(python), "manage.py", "collectstatic", "--noinput"], env=env)

    # Seed demo data (safe to re-run).
    run([str(python), "manage.py", "seed_demo"], env=env)

    print("")
    print("Setup complete.")
    print(f"Virtualenv: {VENV_DIR}")
    print("WSGI file: /var/www/<username>_pythonanywhere_com_wsgi.py")
    print("Set DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS and DJANGO_CORS_ALLOWED_ORIGINS there.")


if __name__ == "__main__":
    main()
