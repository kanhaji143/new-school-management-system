from django.contrib import admin

from . import models


@admin.register(models.QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.StudentAssessment)
class StudentAssessmentAdmin(admin.ModelAdmin):
    pass