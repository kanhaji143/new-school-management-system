from django.contrib import admin

from . import models


@admin.register(models.Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Chapter)
class ChapterAdmin(admin.ModelAdmin):
    pass

@admin.register(models.LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ClassSessionLog)
class ClassSessionLogAdmin(admin.ModelAdmin):
    pass

@admin.register(models.LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    pass