"""Academic structure: years, terms, grade levels, classes, courses, subjects, enrollment."""
from django.db import models

from common.models import TenantModel


class AcademicYear(TenantModel):
    name = models.CharField(max_length=50)  # e.g. 2026-2027
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ("institution", "name")
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Term(TenantModel):
    class TermType(models.TextChoices):
        TERM = "TERM", "Term"
        SEMESTER = "SEMESTER", "Semester"

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="terms"
    )
    name = models.CharField(max_length=50)  # Term 1 / Semester 2
    term_type = models.CharField(max_length=10, choices=TermType.choices, default=TermType.TERM)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ("institution", "academic_year", "name")
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class GradeLevel(TenantModel):
    class LevelType(models.TextChoices):
        SCHOOL = "SCHOOL", "School"
        COLLEGE = "COLLEGE", "College"

    name = models.CharField(max_length=80)  # Grade 10 / FY BSc
    level_type = models.CharField(max_length=10, choices=LevelType.choices, default=LevelType.SCHOOL)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("institution", "name")
        ordering = ["order_index"]

    def __str__(self):
        return self.name


class SchoolClass(TenantModel):
    """A class in the school sense (e.g. Grade 10), parent of sections."""

    grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.CASCADE, related_name="classes"
    )
    name = models.CharField(max_length=80)
    capacity = models.PositiveIntegerField(default=40)

    def __str__(self):
        return f"{self.name} ({self.grade_level})"


class Section(TenantModel):
    """A section/arm of a school class (e.g. Grade 10 - A)."""

    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name="sections"
    )
    name = models.CharField(max_length=80)
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        unique_together = ("institution", "school_class", "name")

    def __str__(self):
        return f"{self.school_class} - {self.name}"


class Course(TenantModel):
    """A college programme (e.g. BSc Computer Science)."""

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    credits = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("institution", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(TenantModel):
    class SubjectType(models.TextChoices):
        THEORY = "THEORY", "Theory"
        PRACTICAL = "PRACTICAL", "Practical"
        ELECTIVE = "ELECTIVE", "Elective"

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    subject_type = models.CharField(
        max_length=10, choices=SubjectType.choices, default=SubjectType.THEORY
    )

    class Meta:
        unique_together = ("institution", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClassSubject(TenantModel):
    """A subject taught to a class/section (school) or course (college)."""

    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="class_subjects")
    section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.CASCADE, related_name="class_subjects"
    )
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.CASCADE, related_name="class_subjects"
    )
    teacher = models.ForeignKey(
        "people.Teacher", null=True, blank=True, on_delete=models.SET_NULL, related_name="class_subjects"
    )
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    term = models.ForeignKey(Term, null=True, blank=True, on_delete=models.SET_NULL)
    planned_periods_per_week = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("institution", "subject", "section", "course", "academic_year")

    def __str__(self):
        target = self.section or self.course
        return f"{self.subject} → {target}"


class Enrollment(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PROMOTED = "PROMOTED", "Promoted"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        DROPPED = "DROPPED", "Dropped"

    student = models.ForeignKey(
        "people.Student", on_delete=models.CASCADE, related_name="enrollments"
    )
    section = models.ForeignKey(
        Section, null=True, blank=True, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.CASCADE, related_name="enrollments"
    )
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    term = models.ForeignKey(Term, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = ("institution", "student", "academic_year", "term")

    def __str__(self):
        return f"{self.student} @ {self.academic_year}"
