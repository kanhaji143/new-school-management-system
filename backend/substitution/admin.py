from django.contrib import admin

from . import models


@admin.register(models.SubstitutionRequest)
class SubstitutionRequestAdmin(admin.ModelAdmin):
    pass

@admin.register(models.SubstituteRecommendation)
class SubstituteRecommendationAdmin(admin.ModelAdmin):
    pass

@admin.register(models.SubstituteAssignment)
class SubstituteAssignmentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.HandoverMaterial)
class HandoverMaterialAdmin(admin.ModelAdmin):
    pass

@admin.register(models.HandoverAttachment)
class HandoverAttachmentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ClassOutcome)
class ClassOutcomeAdmin(admin.ModelAdmin):
    pass