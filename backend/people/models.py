"""People: students, teachers, guardians and their relationships."""
from django.db import models

from common.models import TenantModel
from users.models import User


class PersonBase(TenantModel):
    GENDER_CHOICES = [("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other")]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="%(class)s_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    photo = models.ImageField(upload_to="people/photos/", null=True, blank=True)

    class Meta:
        abstract = True


class Student(PersonBase):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        GRADUATED = "GRADUATED", "Graduated"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        SUSPENDED = "SUSPENDED", "Suspended"
        DROPPED = "DROPPED", "Dropped"

    roll_number = models.CharField(max_length=30)
    admission_number = models.CharField(max_length=30, unique=True)
    admission_date = models.DateField(null=True, blank=True)
    section = models.ForeignKey(
        "academics.Section", null=True, blank=True, on_delete=models.SET_NULL, related_name="students"
    )
    course = models.ForeignKey(
        "academics.Course", null=True, blank=True, on_delete=models.SET_NULL, related_name="students"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = ("institution", "roll_number")

    def __str__(self):
        return f"{self.roll_number} - {self.user.full_name}"


class Teacher(PersonBase):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        RESIGNED = "RESIGNED", "Resigned"

    employee_id = models.CharField(max_length=30)
    department = models.CharField(max_length=120, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    max_periods_per_week = models.PositiveIntegerField(default=30)
    joining_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = ("institution", "employee_id")

    def __str__(self):
        return f"{self.employee_id} - {self.user.full_name}"


class Guardian(PersonBase):
    RELATION_CHOICES = [
        ("FATHER", "Father"),
        ("MOTHER", "Mother"),
        ("GUARDIAN", "Guardian"),
    ]
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES)
    occupation = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.full_name} ({self.relation})"


class StudentGuardian(TenantModel):
    """Many-to-many link; both parents can have portal access to the same student."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardian_links")
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name="student_links")
    is_primary = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)

    class Meta:
        unique_together = ("institution", "student", "guardian")

    def __str__(self):
        return f"{self.guardian} → {self.student}"
