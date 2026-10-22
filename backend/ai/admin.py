from django.contrib import admin

from . import models


@admin.register(models.AIJob)
class AIJobAdmin(admin.ModelAdmin):
    pass

@admin.register(models.GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    pass