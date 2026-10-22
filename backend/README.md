# Backend — Django REST API

Part of the Smart School & College Management Automation System. See `../README.md` and
`../docs/` for the full design.

## Layout

```
backend/
├── config/            settings, urls, celery, wsgi/asgi
├── common/            tenant mixin, base models, permissions, pagination, audit, middleware
├── tenancy/           Institution, settings, domains
├── users/             User, Role, UserRole, Invitation, auth endpoints
├── academics/         AcademicYear, Term, GradeLevel, Class, Section, Course, Subject, Enrollment
├── people/            Student, Teacher, Guardian, StudentGuardian
├── timetable/         PeriodTemplate, Timetable, entries, change requests, conflicts
├── attendance/        Student/teacher attendance, leave
├── substitution/      Substitute recommendations, approval, handover, outcome
├── curriculum/        Syllabus, chapters, lesson plans, session logs, completion
├── content/           Notes, classwork, homework
├── assessments/       Question banks, assessments, marks, results, grade scales
├── notifications/     Templates, outbox, delivery logs, providers
├── ai/                AI jobs + human-review gate
├── coordinator/       Command center widgets + tasks
├── analytics/         Progress & workload snapshots
└── audit/             AuditLog, Backup, SystemSetting
```

Each app follows the same internal layout: `models.py`, `serializers.py`, `views.py`,
`urls.py`, `services.py`, `tasks.py`, `signals.py`, `admin.py`, `tests/`.

## Run

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Or with Docker from the repo root:

```bash
docker compose up -d --build
```

## Conventions

- Every business model inherits `TenantModel` → automatically scoped to `request.institution`.
- Business rules live in `services.py`, not views.
- Writes emit `AuditLog` entries.
- Long work (notifications, AI, reports, backups) runs in Celery tasks.
- Tests: `pytest` or `python manage.py test`.

## API docs

With the server running: http://localhost:8000/api/docs/
