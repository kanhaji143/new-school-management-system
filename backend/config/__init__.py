# This project uses Celery. Ensure the shared `config.celery_app` is imported
# as soon as Django starts so the `celery` CLI can find it.
from .celery import app as celery_app

__all__ = ("celery_app",)
