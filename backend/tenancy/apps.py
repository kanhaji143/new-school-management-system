from django.apps import AppConfig


class TenancyConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenancy'
    verbose_name = 'Tenancy'
