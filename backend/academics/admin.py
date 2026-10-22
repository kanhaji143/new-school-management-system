from django.contrib import admin

from . import models


@admin.register(models.AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Term)
class TermAdmin(admin.ModelAdmin):
    pass

@admin.register(models.GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    pass

@admin.register(models.SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Section)
class SectionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    pass