"""Shared pytest fixtures for the backend test-suite."""
import pytest
from rest_framework.test import APIClient

from tenancy.models import Institution, InstitutionSettings
from users.models import Role, User, UserRole


def make_institution(name, slug, code):
    institution = Institution.objects.create(
        name=name, slug=slug, code=code, type="SCHOOL"
    )
    InstitutionSettings.objects.create(institution=institution)
    return institution


def make_user(institution, email, role_name):
    user = User.objects.create_user(
        email=email, password="Pass@12345", institution=institution
    )
    # Roles are shared inside the institution; creating them twice would break
    # the unique (institution, name) constraint.
    role, _ = Role.objects.get_or_create(
        institution=institution, name=role_name, defaults={"permissions": ["*"]}
    )
    UserRole.objects.get_or_create(user=user, role=role)
    return user


@pytest.fixture
def institution(db):
    return make_institution("Test School", "test-school", "TST")


@pytest.fixture
def other_institution(db):
    return make_institution("Other School", "other-school", "OTH")


@pytest.fixture
def admin_user(institution):
    return make_user(institution, "admin@test.school", "SCHOOL_ADMIN")


@pytest.fixture
def teacher_user(institution):
    return make_user(institution, "teacher@test.school", "TEACHER")


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def teacher_client(teacher_user):
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    return client
