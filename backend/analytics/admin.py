from django.contrib import admin

from . import models


@admin.register(models.StudentProgressSnapshot)
class StudentProgressSnapshotAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TeacherWorkloadSnapshot)
class TeacherWorkloadSnapshotAdmin(admin.ModelAdmin):
    pass