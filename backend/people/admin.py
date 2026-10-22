from django.contrib import admin

from . import models


@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Guardian)
class GuardianAdmin(admin.ModelAdmin):
    pass

@admin.register(models.StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    pass