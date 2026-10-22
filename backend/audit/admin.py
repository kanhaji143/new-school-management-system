from django.contrib import admin

from . import models


@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Backup)
class BackupAdmin(admin.ModelAdmin):
    pass

@admin.register(models.SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    pass