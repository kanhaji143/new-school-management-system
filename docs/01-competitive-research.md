# Competitive Research — What already exists, and what it teaches us

Date: 2026-10
Purpose: Study existing school / college management systems before designing our own structure.
The goal is to **borrow proven domain decomposition, avoid known pitfalls, and find the gaps**
our blueprint (substitute recommendation, timetable conflict detection, auditable corrections,
human-reviewed AI content, multi-tenancy) deliberately targets.

---

## 1. The competitive landscape

| System | Stack | Focus | Notable modules | License |
| --- | --- | --- | --- | --- |
| **OpenEduCat** | Python / Odoo | Full education ERP | 73+ modules: SIS, LMS, exams, gradebook, fees, hostel, library, transport, timetable, OMR | LGPL-3.0 |
| **Fedena / Fedena Pro** | Ruby on Rails | School ERP | 60+ modules across 4 tiers: courses/batches, timetable, attendance, exams, fees, HR, payroll, certificates, SMS | Apache (oss) / EULA (plugins) |
| **openSIS** | PHP / MySQL | Student Information System | Enrollment, scheduling, attendance, gradebook, behavior, billing, portals, AI add-on | GPL / commercial |
| **RosarioSIS** | PHP / PostgreSQL | K-12 SIS | Records, scheduling, attendance, grades, discipline, billing, reporting | GPL-2.0 |
| **Gibbon** | PHP / MySQL | School admin | Roles, enrollment, timetable, markbook, behavior, messaging, extensions | GPL-3.0 |
| **Unifiedtransform** | PHP / Laravel | School ERP | Users/roles, academics, attendance, exams, fees, noticeboard | GPL-3.0 |
| **foBrain AI** | PHP | K-12 | 100+ features, 8 dashboards, LMS, accounting, library, e-shop, ID cards | Apache-2.0 |
| **InnoCore / school-saas** | Next.js + Prisma + PostgreSQL | Multi-tenant SaaS | Tenant isolation, result engine, ranking, PDF, parent portal, scratch cards | MIT |
| **Edu-Sekai** | Next.js + Django + Prisma | Multi-tenant SaaS | Schema-based multi-tenancy, centralized identity | — |
| **Campus Connect** | Django REST + Next.js | Campus social / starter | JWT auth, route groups, SWR hooks, Docker Compose | — |

---

## 2. What mature systems agree on (borrow these)

### 2.1 Domain decomposition
Every serious system separates the same core domains:

```
Institution / Settings
├── User & Role Management
├── Student Information (admissions, enrollment, records)
├── Staff / HR (teachers, leave, payroll)
├── Academic Structure (classes, courses, subjects, sections)
├── Timetable / Scheduling
├── Attendance (student + staff)
├── Examination / Gradebook / Assessment
├── Fees / Finance
├── Communication (messaging, SMS, parent portal)
├── Reports / Analytics
└── Library / Hostel / Transport (operations)
```

Our Django app list mirrors this and adds the modules the brief demands (substitution,
coordinator command center, AI review, audit, backups).

### 2.2 The academic calendar is the backbone
Fedena, openSIS and RosarioSIS all model **Course & Batch**, **Academic Year**, **Term / Marking
Period**, **Grade Level** as first-class objects. Nothing else (enrollment, timetable, exams)
can exist without an academic context. → Our `academics` app is a hard dependency.

### 2.3 Attendance has *two* distinct forms
- **Student attendance**: daily + period-wise, drives parent notifications and compliance.
- **Staff attendance**: daily + leave/absence, drives payroll and substitution.

Both are separate modules in Fedena and openSIS. → We keep `attendance` for students and fold
teacher attendance + leave into the same app (they share the calendar), but expose distinct
serializers/workflows.

### 2.4 Timetable is a first-class, versioned entity
Fedena and openSIS treat timetabling as "class timing sets + entries + publishing". openSIS
explicitly lists **room/resource allocation + conflict detection + substitution management**
as scheduler features. → Our `timetable` app stores `PeriodTemplate`, `Timetable` (versioned,
DRAFT→PUBLISHED), and `TimetableEntry`, plus `TimetableChangeRequest` for the "no unapproved
changes" rule.

### 2.5 Assessment is a pipeline, not a table
Question bank → exam schedule → marks entry → grading → report card → transcript. InnoCore's
result engine (CA + Exam → total → grade → remark → **rank with tie handling** → publish) is a
clean reference for our `assessments` app.

### 2.6 Parent/student portals are scoped and role-filtered
openSIS: "administrators, teachers, students and parents do not see the same interface." InnoCore
uses a many-to-many parent↔student link so both parents see only *their* children. → Our
`people.StudentGuardian` join + role-filtered portal routes.

### 2.7 Multi-tenancy is a cross-cutting, query-level concern
InnoCore and Edu-Sekai both scope **every query by institution**. Edu-Sekai uses schema-based
tenancy; InnoCore uses a shared DB with a `schoolId` on every row and on every query. For a
500–2,000-student institution that may later scale to many institutions, **shared DB +
row-level isolation + a tenant middleware** is the pragmatic choice (with schema-based as a
future migration path). → `common.TenantModel` + `institution` FK + a DRF filter/mixin.

### 2.8 Security is layered
InnoCore documents the exact OWASP mitigations we should adopt: bcrypt hashing, short-lived
access tokens + refresh rotation in HttpOnly cookies, RBAC enforced at middleware **and** route
level, user-enumeration prevention, mass-assignment protection via whitelisted serializers,
IDOR prevention via `institution` scoping, and `select`/field whitelisting so secrets never
leave the API.

### 2.9 Multi-channel notifications with logs
Fedena's SMS module, openSIS's "multichannel communication", and the brief's own
"notification delivery logs and controlled retries" all point to a **template + outbox + retry
log** pattern (transactional outbox) rather than fire-and-forget sends. → `notifications` app.

### 2.10 AI is an emerging, *gated* capability
openSIS ships an "AI-enabled experience" add-on. Our brief goes further: **AI-generated content
must pass human review before publishing**. → `ai` app with a review gate.

---

## 3. Gaps in existing systems (our differentiators)

| Gap in incumbents | What we do |
| --- | --- |
| Substitution is a small feature, not an intelligent engine | `substitution` app with scoring, eligibility, approval, handover, outcome |
| Timetable conflicts detected late | `timetable` validates on save and on publish |
| Changes to timetable/marks are hard to audit | immutable `AuditLog` with before/after diffs on every correction |
| AI output published raw | mandatory `DRAFT → PENDING_REVIEW → APPROVED` gate |
| School and college are separate products | one configurable workflow model (`GradeLevel`/`Course`) |
| Mobile is often an afterthought | responsive-first UI, one codebase, three breakpoints |
| Backups are infra-only | first-class `Backup` records + restore testing |

---

## 4. Decisions taken from this research

1. **Django app per domain** (mirrors the market's consensus decomposition).
2. **Institution scoping on every model + query** (proven by InnoCore/Edu-Sekai).
3. **Versioned, publish-gated timetable** (proven by Fedena/openSIS).
4. **Transactional-outbox notifications** (proven by Fedena SMS + brief).
5. **Question-bank → assessment → result pipeline with ranking** (InnoCore).
6. **RBAC with route-level guards + field whitelisting** (OWASP set).
7. **Human review gate for AI content** (brief + market trend).
8. **Audit log as a first-class, append-only entity** (brief).

---

## 5. Reference material used

- OpenEduCat module catalogue — https://openeducat.org/open-source-campus-management-system/
- Fedena feature tour — https://fedena.com/feature-tour
- Fedena core modules (support) — https://support.fedena.com/support/solutions/16434
- openSIS product page — https://www.opensis.com/
- Unifiedtransform — https://github.com/changeweb/Unifiedtransform
- RosarioSIS — https://github.com/francoisjacquet/rosariosis
- Gibbon — https://github.com/GibbonEdu/core
- OpenEduCat ERP — https://github.com/openeducat/openeducat_erp
- InnoCore (school-saas) — https://github.com/inno-stack/school-saas
- Edu-Sekai (multi-tenant) — https://github.com/webdev-roshan/Edu-Sekai
- Campus Connect (Django + Next starter) — https://github.com/Limbo-corps/campus-connect
- OpenEduCat buyer's guide — https://openeducat.org/resources/buyers-guide/
- 2026 open-source school software roundup — https://geeksourcecodes.com/6-best-open-source-school-management-systems-2026/
