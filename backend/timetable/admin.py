from django.contrib import admin

from . import models


@admin.register(models.PeriodTemplate)
class PeriodTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Timetable)
class TimetableAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TimetableChangeRequest)
class TimetableChangeRequestAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TimetableConflict)
class TimetableConflictAdmin(admin.ModelAdmin):
    pass