from django.contrib import admin

from . import models


@admin.register(models.ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ContentAttachment)
class ContentAttachmentAdmin(admin.ModelAdmin):
    pass