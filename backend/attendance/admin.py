from django.contrib import admin

from . import models


@admin.register(models.StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PeriodAttendance)
class PeriodAttendanceAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    pass

@admin.register(models.LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(models.LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    pass