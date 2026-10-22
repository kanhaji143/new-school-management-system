# Architecture

## 1. High-level diagram

```
                    ┌──────────────────────────────────────────┐
   Browser  ──────► │  Next.js (App Router, TypeScript)        │
   (desktop/tablet/ │  Tailwind · shadcn/ui · SWR · Zustand    │
    mobile)         └───────────────┬──────────────────────────┘
                                    │ HTTPS  REST /api/*  (JWT Bearer)
                    ┌───────────────▼──────────────────────────┐
                    │  Nginx reverse proxy (TLS, static, /media)│
                    └───────────────┬──────────────────────────┘
                                    │
                    ┌───────────────▼──────────────────────────┐
                    │  Django REST Framework (config/)          │
                    │   • Tenant middleware (resolves Institution)│
                    │   • Auth (SimpleJWT) + RBAC permission     │
                    │   • DRF viewsets → serializers             │
                    │   • Celery task dispatch (outbox pattern)  │
                    └───┬───────────────┬──────────────┬────────┘
                        │               │              │
              ┌─────────▼──────┐ ┌──────▼───────┐ ┌────▼──────────┐
              │ PostgreSQL     │ │ Redis        │ │ S3 / MinIO    │
              │ transactional  │ │ cache+broker │ │ media, exports│
              └────────────────┘ └──────┬───────┘ └───────────────┘
                                       │
                    ┌──────────────────▼────────────────────────┐
                    │ Celery worker / beat                      │
                    │  notification send + retries · backups    │
                    │  AI content generation · report building  │
                    └───────────────────────────────────────────┘
```

## 2. Request lifecycle

1. Next.js renders a route under a route group (`(dashboard)`, `(parent)`).
2. The `api-client` axios instance attaches the JWT access token and transparently refreshes on
   401 via `/api/auth/refresh/`.
3. Django middleware resolves the **Institution** from the authenticated user (or a `Host` header
   / `X-Institution` header for domain-based tenants) and stores it on `request.institution`.
4. DRF permissions (`IsInInstitution`, `HasRole`) enforce **server-side** access.
5. The viewset runs inside `TenantQuerySetMixin`, so the queryset is automatically filtered by
   `institution` — cross-tenant access is architecturally impossible.
6. Writes go through the serializer; business rules (conflict checks, approval gates, review
   gates) run in the model/service layer and emit `AuditLog` rows.

## 3. Layered backend structure (Django)

```
config/            project: settings, urls, celery, wsgi/asgi
common/            cross-cutting: TenantModel, TimeStampedModel, permissions,
                   pagination, audit helpers, exception handlers
<domain apps>/     tenancy, users, academics, people, timetable, attendance,
                   substitution, curriculum, content, assessments, notifications,
                   ai, coordinator, analytics, audit
```

Each domain app follows the same internal layout:

```
app/
├── models.py        # entities + constraints (unique_together, indexes)
├── serializers.py   # input validation + field whitelisting
├── views.py         # DRF viewsets / APIViews + permissions
├── urls.py          # router registration
├── services.py      # business logic (conflicts, scoring, workflows)
├── signals.py       # audit hooks, notification triggers
├── admin.py
├── tasks.py         # Celery tasks (async work)
├── tests/
└── apps.py
```

## 4. Multi-tenancy

- **Pattern:** shared database, shared schema, **row-level isolation** via `institution` FK.
- **Why:** 500–2,000 students per institution; a single deployment serves many institutions;
  schema-based tenancy (one schema per tenant) is heavier to operate and reserved as a future
  migration for strict data-residency customers.
- **Enforcement:** `TenantQuerySetMixin` + a `TenantModel` abstract base + `institution` FK on
  every business model + a `current_institution` contextvar set by middleware.
- **Escaping the boundary:** only `SUPER_ADMIN` (platform operator) may query across
  institutions, via an explicit unscoped manager.

## 5. Authentication & authorization

- **JWT** via `rest_framework_simplejwt`; access token short-lived (~15 min), refresh token
  stored server-side and rotated.
- **RBAC:** roles (`SUPER_ADMIN`, `COORDINATOR`, `TEACHER`, `ACCOUNTANT`, `PARENT`, `STUDENT`,
  `LIBRARIAN`, …) map to permissions; permission checks run on the **server** in DRF.
- **Object-level:** `IsOwner`, `IsInInstitution`, `HasRole`, `CanApproveTimetable`, etc.

## 6. Cross-cutting concerns

| Concern | Approach |
| --- | --- |
| Auditing | append-only `AuditLog` (actor, action, model, object id, before/after JSON, IP, ts) |
| Notifications | template + outbox; Celery worker sends via provider; delivery log + capped retries |
| AI content | `AIJob` + `GeneratedContent` with mandatory human review before publish |
| File access | private S3 objects; time-limited signed URLs generated server-side |
| Errors | DRF custom exception handler → standard JSON error envelope |
| Pagination | cursor + page-number pagination; standardized metadata |
| Backups | scheduled Celery beat job + `Backup` records + periodic restore test |

## 7. Key architectural rules (from the brief)

1. **No automatic class completion by elapsed time** — completion is a human/coordinator action.
2. **No unapproved timetable changes** — changes go through `TimetableChangeRequest` + approval.
3. **Human review gate** before any AI-generated educational content is published.
4. **Auditable corrections** — attendance, marks and timetable edits are versioned/logged.
5. **Configurable school vs college workflows** without duplicating the application.

## 8. Deployment

- Docker Compose for local/dev: `postgres`, `redis`, `minio`, `backend`, `celery-worker`,
  `celery-beat`, `frontend`.
- Production: managed PostgreSQL with PITR backups, managed Redis, S3 bucket, autoscaling web +
  worker tiers behind a load balancer, Nginx/TLS edge.
