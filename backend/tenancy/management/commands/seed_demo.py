"""
Seed a demo institution with an admin user and a small academic structure.

Usage:
    python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import AcademicYear, GradeLevel, SchoolClass, Section, Subject
from people import services
from timetable.models import PeriodTemplate
from tenancy.models import Institution, InstitutionSettings
from users.models import Role, User, UserRole


DEMO_PASSWORD = "Demo@12345"
PERIODS = [
    ("Period 1", "09:00", "09:45"),
    ("Period 2", "09:45", "10:30"),
    ("Interval", "10:30", "10:50"),
    ("Period 3", "10:50", "11:35"),
    ("Period 4", "11:35", "12:20"),
    ("Period 5", "12:20", "13:05"),
    ("Period 6", "13:05", "13:50"),
]


class Command(BaseCommand):
    help = "Create a demo institution with an admin user and sample data."

    @transaction.atomic
    def handle(self, *args, **options):
        institution, _ = Institution.objects.get_or_create(
            slug="demo-school",
            defaults={
                "name": "Demo School",
                "code": "DEMO",
                "type": "SCHOOL",
            },
        )
        InstitutionSettings.objects.get_or_create(institution=institution)

        admin, _ = User.objects.get_or_create(
            email="admin@demo.school",
            defaults={
                "institution": institution,
                "first_name": "Demo",
                "last_name": "Admin",
                "is_staff": True,
            },
        )
        admin.set_password(DEMO_PASSWORD)
        admin.save()

        role, _ = Role.objects.get_or_create(
            institution=institution, name="SCHOOL_ADMIN", defaults={"permissions": ["*"]}
        )
        UserRole.objects.get_or_create(user=admin, role=role)

        year, _ = AcademicYear.objects.get_or_create(
            institution=institution,
            name="2026-2027",
            defaults={"start_date": "2026-06-01", "end_date": "2027-03-31", "is_active": True},
        )
        grade, _ = GradeLevel.objects.get_or_create(
            institution=institution, name="Grade 10", defaults={"order_index": 1}
        )
        school_class, _ = SchoolClass.objects.get_or_create(
            institution=institution, grade_level=grade, name="Grade 10"
        )
        section, _ = Section.objects.get_or_create(
            institution=institution, school_class=school_class, name="A"
        )
        math, _ = Subject.objects.get_or_create(
            institution=institution, code="MATH", defaults={"name": "Mathematics"}
        )
        Subject.objects.get_or_create(institution=institution, code="ENG", defaults={"name": "English"})

        # Period templates for the weekly grid.
        for index, (name, start, end) in enumerate(PERIODS, start=1):
            PeriodTemplate.objects.get_or_create(
                institution=institution,
                name=name,
                day=1,
                defaults={
                    "start_time": start,
                    "end_time": end,
                    "order_index": index,
                },
            )

        # Two teachers and a class full of students.
        services.create_teacher(
            institution.id, "neha@demo.school", password=DEMO_PASSWORD,
            first_name="Neha", last_name="Sharma", employee_id="EMP-001",
            department="Mathematics",
        )
        services.create_teacher(
            institution.id, "rajan@demo.school", password=DEMO_PASSWORD,
            first_name="Rajan", last_name="Verma", employee_id="EMP-002",
            department="Languages",
        )
        import random

        random.seed(7)
        for index in range(1, 9):
            services.create_student(
                institution.id,
                f"student{index:02d}@demo.school",
                password=DEMO_PASSWORD,
                first_name=f"Student{index:02d}",
                last_name="Kumar",
                roll_number=f"DEMO-{index:03d}",
                admission_number=f"ADM-2026-{index:03d}",
                section=section,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo institution '{institution.name}' ready.\n"
            f"Admin login   : admin@demo.school / {DEMO_PASSWORD}\n"
            f"Teacher login : neha@demo.school  / {DEMO_PASSWORD}\n"
            f"Student login : student01@demo.school / {DEMO_PASSWORD}"
        ))
