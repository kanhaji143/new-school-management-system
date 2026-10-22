# API Contract

Base path: `/api`. All responses use a standard envelope. All mutating endpoints require a JWT
and are scoped to the caller's institution.

## 1. Standard response envelope

```jsonc
// success
{ "success": true, "message": "OK", "data": { } }

// paginated success
{ "success": true, "data": { "items": [], "page": 1, "pageSize": 20, "total": 0 } }

// error
{
  "success": false,
  "message": "Validation failed",
  "errors": { "fieldErrors": { "email": ["This field is required."] }, "formErrors": [] }
}
```

HTTP status: `200` ok, `201` created, `202` accepted (async), `400` validation,
`401` unauthenticated, `403` forbidden (RBAC / cross-tenant), `404` not found, `409` conflict,
`422` business-rule violation, `429` throttled, `500` server error.

## 2. Authentication

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/api/auth/register/` | Public | create institution + admin |
| POST | `/api/auth/login/` | Public | returns access + refresh |
| POST | `/api/auth/refresh/` | Cookie | rotate refresh token |
| POST | `/api/auth/logout/` | Bearer | revoke refresh |
| GET/PATCH | `/api/auth/me/` | Bearer | current user / profile |

## 3. Endpoint groups (by app)

### tenancy
```
GET/PUT  /api/institutions/me/            current institution profile
GET/PUT  /api/institutions/me/settings/   feature flags + defaults
```

### users & roles
```
GET/POST /api/users/                      list / create (filter role, search)
GET/PATCH/DELETE /api/users/{id}/
GET/POST /api/roles/   GET/PATCH/DELETE /api/roles/{id}/
POST /api/invitations/  POST /api/invitations/{id}/resend/
```

### academics
```
GET/POST /api/academic-years/        POST /api/academic-years/{id}/activate/
GET/POST /api/terms/                 POST /api/terms/{id}/activate/
GET/POST /api/grade-levels/
GET/POST /api/classes/               GET/POST /api/classes/{id}/sections/
GET/POST /api/courses/
GET/POST /api/subjects/
GET/POST /api/class-subjects/
GET/POST /api/enrollments/
```

### people
```
GET/POST /api/students/              GET/PATCH /api/students/{id}/
GET/POST /api/teachers/              GET/PATCH /api/teachers/{id}/
GET/POST /api/guardians/             POST /api/students/{id}/guardians/
```

### timetable
```
GET/POST /api/period-templates/
GET/POST /api/timetables/
GET     /api/timetables/{id}/
POST    /api/timetables/{id}/validate/
POST    /api/timetables/{id}/publish/
POST    /api/timetables/{id}/change-requests/
GET     /api/timetable-conflicts/
```

### attendance
```
GET/POST /api/teacher-attendance/
GET/POST /api/leave-types/
GET/POST /api/leave-requests/        POST /api/leave-requests/{id}/approve|reject/
GET/POST /api/student-attendance/    GET/POST /api/period-attendance/
```

### substitution
```
GET/POST /api/substitution-requests/
GET     /api/substitution-requests/{id}/recommendations/
POST    /api/substitution-requests/{id}/assign/       coordinator approval
POST    /api/substitution-requests/{id}/handover/     attach material
POST    /api/substitution-requests/{id}/outcome/      record class outcome
```

### curriculum
```
GET/POST /api/syllabi/     GET/POST /api/syllabi/{id}/chapters/
GET/POST /api/chapters/{id}/lesson-plans/
GET/POST /api/class-session-logs/
POST    /api/chapters/{id}/complete/     explicit completion (never auto)
```

### content
```
GET/POST /api/content/      GET/PATCH/DELETE /api/content/{id}/
POST   /api/content/{id}/attachments/
```

### assessments
```
GET/POST /api/question-banks/   GET/POST /api/question-banks/{id}/questions/
GET/POST /api/assessments/
POST   /api/assessments/{id}/marks/     bulk marks entry
GET    /api/assessments/{id}/results/
GET/POST /api/grade-scales/
```

### notifications
```
GET/POST /api/notification-templates/
GET     /api/notifications/                 outbox list
GET     /api/notifications/{id}/logs/       delivery attempts
POST    /api/notifications/{id}/retry/
GET/POST /api/provider-configs/
```

### ai
```
POST   /api/ai/jobs/                        request generation (async)
GET    /api/ai/jobs/{id}/
GET    /api/ai/generated-content/           list (filter status)
POST   /api/ai/generated-content/{id}/review/   approve | reject (human gate)
```

### coordinator
```
GET     /api/coordinator/dashboard/
GET/POST /api/coordinator/tasks/
GET/PATCH /api/coordinator/widgets/
```

### analytics
```
GET /api/analytics/students/{id}/progress/
GET /api/analytics/teachers/{id}/workload/
GET /api/analytics/institution/overview/
```

### audit & system
```
GET /api/audit-logs/          (filter actor, model, date)
GET /api/backups/             POST /api/backups/  POST /api/backups/{id}/restore-test/
GET/PUT /api/system-settings/
```

## 4. Cross-cutting conventions

- **Filtering:** `?search=`, `?page=`, `?pageSize=`, plus entity-specific filters.
- **Ordering:** `?ordering=-created_at`.
- **Institution scoping:** implicit via the authenticated user; never accept `institution_id`
  from the client for non-super-admins.
- **Idempotency:** mutating endpoints accept an optional `Idempotency-Key` header.
- **Async jobs:** return `202` with a job id; clients poll a status endpoint or receive a webhook.
