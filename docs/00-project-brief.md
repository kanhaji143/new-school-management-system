# Project Brief — Smart School & College Management Automation System

> Source: `Smart_School_College_Management_Blueprint.pdf`

## Objective

Build a secure, responsive, web-based academic operations management platform for schools and
colleges with approximately 500–2,000 students per institution. Design the architecture to
support multiple institutions in the future.

## Core Modules

1. Institution and academic configuration
2. Authentication and role-based access
3. Student, teacher and guardian management
4. School classes, sections, college courses and semesters
5. Timetable creation and conflict detection
6. Teacher attendance, leave and absence tracking
7. Student daily and period-wise attendance
8. Smart substitute teacher recommendations
9. Class session logs and lesson completion
10. Syllabus, chapters and lesson plans
11. Notes, classwork and homework management
12. Question bank, tests and assessments
13. Student progress and academic analytics
14. Teacher workload and monthly reports
15. Parent portal and configurable notifications
16. AI-assisted question and learning-material generation
17. Coordinator command center
18. Audit logs, backups and system settings
19. *(the brief lists 18 numbered groups; the 19th is the closing section)*

## Primary Workflow

Teacher absence → identify affected timetable periods → recommend eligible available substitutes
→ obtain coordinator approval → provide lesson handover material → record actual class outcome →
update confirmed syllabus progress → generate relevant reports and notifications.

## Suggested Technology

- **Frontend:** Next.js and TypeScript
- **Backend:** Django REST Framework
- **Database:** PostgreSQL
- **File storage:** Private S3-compatible object storage
- **Background jobs:** Celery, Redis or equivalent
- **Integrations:** Configurable SMS/WhatsApp/email providers and AI provider

## Non-Negotiable Requirements

- Responsive desktop, tablet and mobile UI
- Real database-backed CRUD and workflows
- Server-enforced role permissions
- Institution-level data isolation
- No automatic class completion based only on elapsed time
- No unapproved timetable changes
- Human review before AI-generated educational content is published
- Notification delivery logs and controlled retries
- Auditable attendance, marks and timetable corrections
- Secure file access, backups and restore testing
- School and college workflows configurable without duplicating the entire application

## Definition of Done

The system is complete only when the core workflows work end-to-end with persistent database
records, validated permissions, error handling, audit history, mobile-responsive screens and
tested reporting. Static mockups alone do not satisfy the requirements.
