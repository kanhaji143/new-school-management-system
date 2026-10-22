from django.contrib import admin

from . import models


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.InstitutionSettings)
class InstitutionSettingsAdmin(admin.ModelAdmin):
    pass

@admin.register(models.InstitutionDomain)
class InstitutionDomainAdmin(admin.ModelAdmin):
    pass