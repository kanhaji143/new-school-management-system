# Smart School & College Management Automation System

A secure, responsive, multi-tenant web platform for academic operations management of
schools and colleges (500–2,000 students per institution).

> This repository is the **implementation scaffold** derived from the project blueprint
> `Smart_School_College_Management_Blueprint.pdf`. See `docs/00-project-brief.md` for the
> original requirements and `docs/01-competitive-research.md` for the market research that
> shaped this structure.

---

## 1. Vision

Digitize the entire academic workflow of an institution — admissions → classes → timetable →
attendance → teaching → assessments → reporting → parent engagement — with **real database
backing, server-enforced permissions, institution-level data isolation, and auditable
corrections**. The architecture is designed so a single deployment can serve many institutions.

---

## 2. Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | Django + Django REST Framework |
| Database | PostgreSQL |
| Cache / Broker | Redis |
| Background jobs | Celery (+ Celery Beat) |
| File storage | S3-compatible object storage (MinIO locally) |
| Auth | JWT (SimpleJWT) + role-based permissions |
| Infra | Docker + Docker Compose, Nginx reverse proxy |

---

## 3. Repository Layout

```
New School Management System/
├── docs/                     # Brief, research, architecture, schema, API, roadmap
├── backend/                  # Django REST API
│   ├── config/               # settings, urls, celery, wsgi/asgi
│   ├── common/               # tenant mixin, base models, permissions, audit, pagination
│   ├── tenancy/              # Institution + settings + domains
│   ├── users/                # User, Role, permissions, invitations
│   ├── academics/            # AcademicYear, Term, GradeLevel, Class/Section, Course, Subject
│   ├── people/               # Student, Teacher, Guardian, links
│   ├── timetable/            # Timetable, entries, change requests, conflicts
│   ├── attendance/           # Teacher & student attendance, leave
│   ├── substitution/         # Substitute recommendations, approval, handover, outcome
│   ├── curriculum/           # Syllabus, chapters, lesson plans, session logs
│   ├── content/              # Notes, classwork, homework
│   ├── assessments/          # Question bank, tests, marks, results
│   ├── notifications/        # Templates, notifications, delivery logs
│   ├── ai/                   # AI jobs + human review of generated content
│   ├── coordinator/          # Coordinator command center
│   ├── analytics/            # Progress & workload reports
│   └── audit/                # Audit log, backups, system settings
├── frontend/                 # Next.js application
│   └── src/
│       ├── app/              # App Router (auth) / (dashboard) / (parent) route groups
│       ├── components/       # UI, layout, feature components
│       ├── lib/              # api client, auth, utils
│       ├── hooks/            # SWR data hooks
│       ├── store/            # client state
│       └── types/            # shared TS interfaces
├── infra/                    # nginx, CI, deployment helpers
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Core Domain Concepts

- **Institution (Tenant)** — top-level isolation boundary. Every business record carries an
  `institution` foreign key and every query is scoped by it.
- **AcademicYear / Term** — the academic calendar. One active year + one active term at a time.
- **GradeLevel / Class / Section** (school) and **Course / Semester** (college).
- **Subject / ClassSubject** — what is taught, by whom, to which class.
- **Timetable / TimetableEntry** — the weekly schedule grid; versioned and publish-gated.
- **Attendance** — daily + period-wise for students; daily + leave for teachers.
- **Substitution** — the flagship workflow (see `docs/06-substitution-engine.md`).
- **Curriculum** — syllabus → chapters → lesson plans → session logs → completion.
- **Assessment** — question bank → tests → marks → results/grades.
- **Notification** — multi-channel, templated, logged, retried.
- **AI** — generated content always passes a **human review gate** before publishing.

---

## 5. Quick Start (Docker)

```bash
cp .env.example .env
docker compose up -d --build

# first-time DB setup (inside the backend container)
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo   # optional demo data
docker compose exec backend python manage.py createsuperuser
```

- Frontend → http://localhost:3000
- API → http://localhost:8000/api
- Django Admin → http://localhost:8000/admin

---

## 6. Non-Negotiable Requirements (from the brief)

These are hard constraints — the implementation is considered incomplete without them:

1. Responsive desktop / tablet / mobile UI.
2. Real database-backed CRUD and workflows (no static mockups).
3. Server-enforced role permissions.
4. Institution-level data isolation.
5. No automatic class completion based only on elapsed time.
6. No unapproved timetable changes.
7. Human review before AI-generated educational content is published.
8. Notification delivery logs and controlled retries.
9. Auditable attendance, marks and timetable corrections.
10. Secure file access, backups and restore testing.
11. School and college workflows configurable without duplicating the application.

---

## 7. Status

🚧 **Scaffold / in progress.** Structure and core data models exist; feature implementation
continues per `docs/05-roadmap.md`.

---

## 8. Documentation Index

| Doc | Purpose |
| --- | --- |
| `docs/00-project-brief.md` | Original blueprint (verbatim) |
| `docs/01-competitive-research.md` | Market research on existing systems |
| `docs/02-architecture.md` | High-level architecture & decisions |
| `docs/03-data-model.md` | Entities, relations, key constraints |
| `docs/04-api-contract.md` | REST endpoint conventions & groups |
| `docs/05-roadmap.md` | Phased build plan |
| `docs/06-substitution-engine.md` | Substitute recommendation design |
| `docs/07-timetable-conflict.md` | Conflict detection design |
