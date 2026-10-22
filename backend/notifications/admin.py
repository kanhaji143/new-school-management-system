from django.contrib import admin

from . import models


@admin.register(models.NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass

@admin.register(models.NotificationDeliveryLog)
class NotificationDeliveryLogAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ProviderConfig)
class ProviderConfigAdmin(admin.ModelAdmin):
    pass