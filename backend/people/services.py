"""People domain services.

Creating a student/teacher/guardian always implies creating a login account,
so that logic lives here and is reused by the API, the admin and seed commands.
"""
from django.db import transaction
from django.utils.crypto import get_random_string

from users.models import Role, User, UserRole

from .models import Guardian, Student, StudentGuardian, Teacher

STUDENT_ROLE = "STUDENT"
TEACHER_ROLE = "TEACHER"
PARENT_ROLE = "PARENT"


def ensure_role(institution_id, name):
    """Fetch (or create) a role inside the institution."""
    role, _ = Role.objects.get_or_create(institution_id=institution_id, name=name)
    return role


def assign_role(user, role_name, academic_year=None):
    """Give `user` a role in their own institution (idempotent)."""
    role = ensure_role(user.institution_id, role_name)
    UserRole.objects.get_or_create(
        user=user, role=role, defaults={"academic_year": academic_year}
    )
    return role


def _create_user(institution_id, email, password=None, first_name="", last_name="", phone=""):
    email = email.strip().lower()
    if User.objects.filter(email__iexact=email).exists():
        raise ValueError(f"A user with email '{email}' already exists.")
    # Django 5.1 removed `BaseUserManager.make_random_password()`.
    password = password or get_random_string(12)
    return User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name or "",
        last_name=last_name or "",
        phone=phone or "",
        institution_id=institution_id,
    )


@transaction.atomic
def create_student(institution_id, email, password=None, first_name="", last_name="",
                   phone="", **profile_data):
    """Create a login account + Student profile + STUDENT role."""
    user = _create_user(
        institution_id, email, password, first_name, last_name, phone
    )
    student = Student.objects.create(
        institution_id=institution_id, user=user, **profile_data
    )
    assign_role(user, STUDENT_ROLE)
    return student


@transaction.atomic
def create_teacher(institution_id, email, password=None, first_name="", last_name="",
                   phone="", **profile_data):
    """Create a login account + Teacher profile + TEACHER role."""
    user = _create_user(
        institution_id, email, password, first_name, last_name, phone
    )
    teacher = Teacher.objects.create(
        institution_id=institution_id, user=user, **profile_data
    )
    assign_role(user, TEACHER_ROLE)
    return teacher


@transaction.atomic
def create_guardian(institution_id, email, password=None, first_name="", last_name="",
                    phone="", **profile_data):
    """Create a login account + Guardian profile + PARENT role."""
    user = _create_user(
        institution_id, email, password, first_name, last_name, phone
    )
    guardian = Guardian.objects.create(
        institution_id=institution_id, user=user, **profile_data
    )
    assign_role(user, PARENT_ROLE)
    return guardian


@transaction.atomic
def link_guardian(student, guardian, is_primary=False, is_emergency_contact=False):
    """Attach a guardian to a student.

    Only one guardian can be the primary contact for a given student.
    """
    if student.institution_id != guardian.institution_id:
        raise ValueError("Student and guardian belong to different institutions.")

    if is_primary:
        StudentGuardian.all_objects.filter(
            student=student, is_primary=True
        ).exclude(guardian=guardian).update(is_primary=False)

    link, _ = StudentGuardian.all_objects.update_or_create(
        institution_id=student.institution_id,
        student=student,
        guardian=guardian,
        defaults={
            "is_primary": is_primary,
            "is_emergency_contact": is_emergency_contact,
        },
    )
    return link


@transaction.atomic
def unlink_guardian(student, guardian):
    """Remove a guardian's access to a student."""
    deleted, _ = StudentGuardian.all_objects.filter(
        student=student, guardian=guardian
    ).delete()
    return bool(deleted)
