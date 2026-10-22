from django.apps import AppConfig


class SubstitutionConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'substitution'
    verbose_name = 'Substitution'

    def ready(self):
        from . import signals  # noqa: F401
        return super().ready()
