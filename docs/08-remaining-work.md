# Remaining Work Checklist

Generated from a full-repo audit on 2026-10-21. Status: **Phases 1–2 backend done + core UI wired (~35%)**.

Use `[ ]` to tick items as they are finished. Each item links to the exact file to edit.

Legend:
- ✅ = done
- ❌ = not started (stub or missing)

---

## 0. State of the repo (quick summary)

| Area | State |
| --- | --- |
| Docs (00–07) | ✅ complete |
| `common/` foundation (tenant, soft-delete, permissions, middleware, pagination, audit, exceptions) | ✅ complete |
| `config/` settings, urls, celery | ✅ complete |
| Docker / compose / nginx | ✅ complete |
| Auth API + login UI (fixed: `/auth/me/` called without token; CORS origins) | ✅ working |
| Data models (all 15 apps) | ✅ defined |
| Substitution scoring service | ✅ done |
| Test harness (pytest-django, `backend/conftest.py`) | ✅ 49 tests passing |
| Phase 1 — Academics + People API (serializers/views/urls/services/signals/tests) | ✅ done |
| Phase 2 — Timetable API (conflict detection, draft → validate → publish, change requests) | ✅ done |
| Demo seed (`python manage.py seed_demo` — admin/teacher/student logins) | ✅ done |
| Frontend: students, timetable, dashboard wired to real API | ✅ core done |
| Parent route conflict fixed (`/parent` instead of `/dashboard`) | ✅ done |
| Remaining app APIs (attendance, substitution UI, … Phases 3–9) | ❌ see below |
| Remaining frontend screens | ❌ see below |

---

## 1. Backend — build real API per app

Every app below has **models ✅ + admin ✅**, but `serializers.py`, `views.py`,
`urls.py`, `services.py`, `signals.py`, `tasks.py` are 2–7 line TODO stubs, and
`tests/test_models.py` is a placeholder.

### 1.1 Academics ✅
- [x] `academics/serializers.py` — AcademicYear, Term, GradeLevel, SchoolClass, Section, Course, Subject, ClassSubject, Enrollment
- [x] `academics/views.py` — CRUD viewsets, institution-scoped querysets, active-year/term actions
- [x] `academics/urls.py`
- [x] `academics/services.py` — promotion, active-term rollover, duplicate-year helpers
- [x] `academics/signals.py` — enforce single active AcademicYear/Term
- [x] `academics/tests/` — model + permission + tenant-isolation tests

### 1.2 People ✅
- [x] `people/serializers.py` — Student, Teacher, Guardian, StudentGuardianLink
- [x] `people/views.py` — CRUD, guardian linking, profile search
- [x] `people/urls.py`
- [x] `people/services.py` — guardian auto-link, user-account creation for student/parent
- [x] `people/tests/` — model + permission tests

### 1.3 Timetable ✅ (Phase 2)
- [x] `timetable/serializers.py`
- [x] `timetable/views.py` — draft → validate → publish workflow (+ `grid`, `entries` actions)
- [x] `timetable/urls.py`
- [x] `timetable/services.py` — conflict detection: teacher/room/section double-book (HARD), teacher overload + subject frequency (SOFT); published versions excluded as superseded
- [x] Change-request + approval workflow (published entries immutable, approval applies change)
- [x] `timetable/tests/` — 11 real tests (conflicts, publish gate, versioning, change requests)

### 1.4 Attendance (Phase 3) - DONE (backend + frontend)
- [x] `attendance/serializers.py` - StudentAttendance, PeriodAttendance, TeacherAttendance, LeaveType, LeaveRequest
- [x] `attendance/views.py` - bulk marking, period-wise, corrections, leave approve/reject
- [x] `attendance/urls.py`
- [x] `attendance/services.py` - audit-logged corrections (brief requirement #9)
- [x] `attendance/tests/` - 15 real tests
- [x] `frontend/src/hooks/useAttendance.ts` + `attendance/page.tsx`
- [x] Direct WhatsApp `wa.me` individual/bulk alert queue + saved absent/general templates (user confirms Send in WhatsApp)
- [ ] Automated WhatsApp Business API delivery and provider delivery logs

### 1.5 Substitution (Phase 4) - DONE (backend + frontend)
- [x] `substitution/serializers.py`
- [x] `substitution/views.py` - request -> recommend -> assign -> handover -> outcome
- [x] `substitution/urls.py`
- [x] `substitution/signals.py` - auto-create request on teacher absence
- [x] `substitution/services.py` wired into views
- [x] `substitution/tests/` - 8 real tests
- [x] `frontend/src/hooks/useSubstitution.ts` + `substitution/page.tsx`
- [ ] `substitution/tasks.py` - async recommendation generation (optional)

### 1.6 Curriculum (Phase 5) - DONE (backend + frontend)
- [x] `curriculum/serializers.py` - Syllabus, Chapter, LessonPlan, ClassSessionLog, LessonCompletion
- [x] `curriculum/views.py` - syllabi, chapters (nested), lesson-plans (nested), session-logs, complete
- [x] `curriculum/urls.py`
- [x] `curriculum/tests/` - 6 real tests
- [x] `frontend/src/hooks/useCurriculum.ts` + `curriculum/page.tsx`
- [ ] `curriculum/services.py` - completion % roll-up (optional)
### 1.7 Content (Phase 5)
- [ ] `content/serializers.py` — Note, Classwork, Homework
- [ ] `content/views.py` — signed-URL uploads to S3/MinIO
- [ ] `content/urls.py`
- [ ] `content/tests/`

### 1.8 Assessments (Phase 6) - DONE (backend + frontend)
- [x] `assessments/serializers.py` - QuestionBank, Question (including vocabulary terms), GradeScale, Assessment, StudentAssessment, QuestionImport
- [x] `assessments/views.py` - question banks, marks/results, paste/file question import with preview and confirm
- [x] `assessments/urls.py`
- [x] `assessments/services.py` - bulk marks, grade assignment, results/ranking
- [x] `assessments/tests/` - 17 API tests including file imports, assignments, student visibility and answer submission
- [x] `frontend/src/hooks/useAssessments.ts` + `assessments/page.tsx`
- [ ] Report export PDF/CSV (deferred)

### 1.9 Notifications (Phase 7) - DONE (backend + frontend)
- [x] `notifications/serializers.py` - Template, Notification, DeliveryLog, ProviderConfig
- [x] `notifications/views.py` - outbox, retry, templates, provider-configs
- [x] `notifications/urls.py`
- [x] `notifications/services.py` - enqueue, retry, mark_sent/failed
- [x] `notifications/tests/` - 4 real tests
- [x] Absence hook in attendance (parent notification on absence)
- [x] `frontend/src/hooks/useNotifications.ts` + `notifications/page.tsx`
- [ ] `notifications/tasks.py` - async dispatch with backoff (optional)

### 1.10 AI (Phase 7) - DONE (backend + frontend)
- [x] `ai/serializers.py` - AIJob, GeneratedContent
- [x] `ai/views.py` - jobs, generated-content, human review gate
- [x] `ai/urls.py`
- [x] `ai/services.py` - generation abstraction
- [x] `ai/tests/` - 4 real tests
- [x] `frontend/src/hooks/useAI.ts` + `ai/page.tsx`
- [ ] `ai/tasks.py` - async generation (optional)
### 1.11 Coordinator (Phase 8) - DONE (backend + frontend)
- [x] `coordinator/serializers.py`
- [x] `coordinator/views.py` - tenant-scoped command-center metrics, task list/create/complete, widgets
- [x] `coordinator/urls.py`
- [x] `coordinator/tests/` - 3 workflow, tenancy and permission tests
- [x] `frontend/src/hooks/useCoordinator.ts` + `coordinator/page.tsx`

### 1.12 Analytics (Phase 6/8)
- [ ] `analytics/serializers.py`
- [ ] `analytics/views.py` — student progress, teacher workload, institution overview
- [ ] `analytics/urls.py`
- [ ] `analytics/services.py`
- [ ] `analytics/tests/`

### 1.13 Audit (Phase 8) - PARTIAL
- [x] `audit/serializers.py` - read-only audit log, backup metadata, system settings
- [x] `audit/views.py` - tenant-scoped audit reader, admin settings, SUPER_ADMIN backup operations
- [x] `audit/urls.py`
- [x] `audit/services.py` - SQLite snapshot + checksum + isolated temporary-database restore test
- [x] `audit/tests/` - tenant isolation, roles, settings and isolated restore verification
- [x] `frontend/src/hooks/useAuditOps.ts` + settings/audit screen
- [ ] Production PostgreSQL backup/restore integration
- [ ] `audit/tasks.py` - scheduled backups

### 1.14 Operations hardening (Phase 8) - PARTIAL
- [x] `.github/workflows/ci.yml` - backend checks/migrations/tests + frontend typecheck/build
- [x] `infra/nginx/default.conf` - security headers and forwarded-protocol headers
- [x] Production-only HTTPS, cookie, HSTS and strong-secret/explicit-host safeguards in Django settings
- [ ] Signed URLs/private-media access enforcement
- [ ] Responsive polish and browser QA across all modules

