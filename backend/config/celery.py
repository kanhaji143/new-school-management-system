"""Celery application wiring."""
import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Read config from Django settings using the `CELERY_` namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in every installed app's `tasks.py`.
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):  # pragma: no cover - keeps Django logging config
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # pragma: no cover - sanity check
    print(f"Request: {self.request!r}")
