# PythonAnywhere WSGI configuration.
#
# Paste this into the WSGI configuration file that PythonAnywhere creates for
# your web app, then reload the web app from the Web tab.
#
# Replace <username> with your PythonAnywhere username and set a strong
# DJANGO_SECRET_KEY (50+ characters).

import os
import sys

HOME = os.path.expanduser("~")
PROJECT_DIR = os.path.join(HOME, "school", "backend")

sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, os.path.join(HOME, ".virtualenvs", "schoolapi", "lib",
                                f"python{sys.version_info.major}.{sys.version_info.minor}",
                                "site-packages"))

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DEBUG"] = "false"
os.environ["DJANGO_SECRET_KEY"] = "REPLACE_WITH_A_LONG_RANDOM_SECRET_KEY_AT_LEAST_50_CHARS_LONG_1234"
os.environ["DJANGO_ALLOWED_HOSTS"] = "<username>.pythonanywhere.com"
os.environ["DJANGO_CORS_ALLOWED_ORIGINS"] = "https://new-school-management-system.web.app"
os.environ["DJANGO_SECURE_SSL_REDIRECT"] = "false"
os.environ["DJANGO_SESSION_COOKIE_SECURE"] = "true"
os.environ["DJANGO_CSRF_COOKIE_SECURE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(PROJECT_DIR, "db.sqlite3")
os.environ["MEDIA_ROOT"] = os.path.join(HOME, "media")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
