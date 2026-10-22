"""Question banks, assessments, marks, results and grade scales."""
from django.db import models

from common.models import TenantModel


class QuestionBank(TenantModel):
    name = models.CharField(max_length=200)
    subject = models.ForeignKey(
        "academics.Subject", null=True, blank=True,
        on_delete=models.CASCADE, related_name="question_banks"
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Question(TenantModel):
    class QuestionType(models.TextChoices):
        MCQ = "MCQ", "Multiple choice"
        TRUE_FALSE = "TRUE_FALSE", "True/False"
        SHORT = "SHORT", "Short answer"
        LONG = "LONG", "Long answer"

    class Difficulty(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(max_length=12, choices=QuestionType.choices, default=QuestionType.MCQ)
    text = models.TextField()
    marks = models.PositiveIntegerField(default=1)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    vocabulary_terms = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.text[:80]


class GradeScale(TenantModel):
    grade = models.CharField(max_length=5)
    min_mark = models.PositiveIntegerField()
    max_mark = models.PositiveIntegerField()
    remark = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-min_mark"]

    def __str__(self):
        return f"{self.grade} ({self.min_mark}-{self.max_mark})"


class Assessment(TenantModel):
    class AssessmentType(models.TextChoices):
        QUIZ = "QUIZ", "Quiz"
        TEST = "TEST", "Test"
        EXAM = "EXAM", "Exam"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=12, choices=AssessmentType.choices, default=AssessmentType.TEST)
    subject = models.ForeignKey(
        "academics.Subject", null=True, blank=True, on_delete=models.CASCADE, related_name="assessments"
    )
    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.CASCADE, related_name="assessments"
    )
    course = models.ForeignKey(
        "academics.Course", null=True, blank=True, on_delete=models.CASCADE, related_name="assessments"
    )
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT)
    term = models.ForeignKey("academics.Term", null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=40)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        indexes = [models.Index(fields=["institution", "date"])]


class AssessmentQuestion(TenantModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="questions")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="assessment_links")
    marks_override = models.PositiveIntegerField(null=True, blank=True)


def question_import_upload_path(instance, filename):
    from pathlib import Path

    safe_name = Path(filename).name.replace("..", "_")
    return f"assessments/imports/{instance.institution_id}/{safe_name}"


class QuestionImport(TenantModel):
    class Status(models.TextChoices):
        PREVIEW = "PREVIEW", "Preview"
        IMPORTED = "IMPORTED", "Imported"

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="question_imports"
    )
    source_file = models.FileField(upload_to=question_import_upload_path, null=True, blank=True)
    original_file_name = models.CharField(max_length=255, blank=True)
    pasted_text = models.TextField(blank=True)
    extraction_warning = models.CharField(max_length=500, blank=True)
    parsed_questions = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PREVIEW)
    imported_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]


class StudentAssessment(TenantModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUBMITTED = "SUBMITTED", "Submitted"
        GRADED = "GRADED", "Graded"

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="student_marks")
    student = models.ForeignKey(
        "people.Student", on_delete=models.CASCADE, related_name="assessment_marks"
    )
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    grade = models.CharField(max_length=5, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("institution", "assessment", "student")
