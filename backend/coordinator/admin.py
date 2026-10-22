from django.contrib import admin

from . import models


@admin.register(models.CommandCenterWidget)
class CommandCenterWidgetAdmin(admin.ModelAdmin):
    pass

@admin.register(models.CoordinatorTask)
class CoordinatorTaskAdmin(admin.ModelAdmin):
    pass