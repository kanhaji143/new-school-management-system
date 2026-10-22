# Roadmap

Phased build plan. Each phase ends with working, database-backed, tested functionality.

---

## Phase 0 — Foundation ✅ (this scaffold)
- Monorepo structure, docs, research.
- Docker Compose: postgres, redis, minio, backend, celery, frontend.
- `common` app: `TenantModel`, `TimeStampedModel`, permissions, pagination, audit helpers.
- Auth skeleton (JWT + custom user + roles).

## Phase 1 — Core academic spine
- `tenancy` (Institution, settings, domains).
- `academics` (AcademicYear, Term, GradeLevel, Class/Section, Course, Subject, Enrollment).
- `people` (Student, Teacher, Guardian, links).
- RBAC + institution scoping enforced everywhere.
- Basic dashboards (admin, teacher, student, parent).

## Phase 2 — Timetable
- `timetable` (PeriodTemplate, Timetable, entries).
- Conflict detection (hard + soft) on validate/publish.
- Change-request + approval workflow.
- Manual entry UI + weekly grid views.

## Phase 3 — Attendance & leave
- `attendance` (student daily + period-wise, teacher attendance + leave).
- Parent notifications on absence.
- Audit logging of corrections.

## Phase 4 — Substitution engine ⭐
- `substitution` (request → recommendations → approval → handover → outcome).
- Scoring service + eligibility rules.
- Coordinator approval UI.
- Syllabus progress update from outcome.

## Phase 5 — Curriculum & content
- `curriculum` (syllabus, chapters, lesson plans, session logs, completion).
- `content` (notes, classwork, homework) + S3 attachments.

## Phase 6 — Assessment & analytics
- `assessments` (question bank, tests, marks, results, grade scales, ranking).
- `analytics` (student progress, teacher workload, institution overview).
- Report export (PDF/CSV).

## Phase 7 — Notifications & AI
- `notifications` (templates, outbox, delivery logs, retries, provider configs).
- `ai` (jobs + generated content with mandatory human review gate).

## Phase 8 — Operations & hardening
- `coordinator` command center.
- `audit` (backups + restore testing, system settings).
- Security hardening, rate limiting, signed URLs.
- Responsive polish across all breakpoints.

## Phase 9 — Multi-institution & scale
- Domain-based tenant resolution.
- Optional schema-based tenancy for strict isolation customers.
- Performance tuning, caching, load testing.

---

## Definition of Done (per brief)
Core workflows work end-to-end with persistent DB records, validated permissions, error
handling, audit history, mobile-responsive screens and tested reporting. Static mockups do not
count.

## Suggested sprint order
Phase 0 → 1 → 2 → 3 → 4 (the flagship workflow) → 5 → 6 → 7 → 8 → 9.
