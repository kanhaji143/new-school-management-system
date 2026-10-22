# Data Model

Entities are grouped by Django app. All business entities inherit `TenantModel`
(`institution` FK) and `TimeStampedModel` (`created_at`, `updated_at`).

---

## tenancy

```
Institution
  id, name, slug (unique), code, type [SCHOOL|COLLEGE], address,
  phone, email, logo, is_active, created_at, updated_at

InstitutionSettings
  institution (OneToOne), features (JSON flags), academic defaults,
  timezone, date_format, notification defaults

InstitutionDomain
  institution (FK), domain (unique), is_primary
```

## users

```
User  (email unique, password, first/last name, phone, is_active,
       institution FK, is_superuser flag)
Role  (institution FK, name, permissions JSON)
UserRole (user FK, role FK, academic_year FK null)
Invitation (institution FK, email, role, token, status, expires_at)
```

## academics

```
AcademicYear (institution FK, name, start_date, end_date, is_active)
Term         (academic_year FK, name, type [TERM|SEMESTER], start_date, end_date, is_active)
GradeLevel   (institution FK, name, order_index, level_type [SCHOOL|COLLEGE])
SchoolClass  (institution FK, grade_level FK, name)
Section      (school_class FK, name, capacity)
Course       (institution FK, code, name, credits)              # college
Subject      (institution FK, code, name, type)
ClassSubject (institution FK, class_or_section FK, course FK null,
              subject FK, teacher FK, academic_year FK, term FK)
Enrollment   (institution FK, student FK, section FK null, course FK null,
              academic_year FK, term FK, status)
```

## people

```
Student   (user OneToOne, institution FK, roll_number, admission_no,
           grade/section FK, status, date_of_birth, gender)
Teacher   (user OneToOne, institution FK, employee_id, department,
           qualification, max_periods_per_week, joining_date, status)
Guardian  (user OneToOne, institution FK, relation, occupation)
StudentGuardian (student FK, guardian FK, is_primary, is_emergency_contact)
```

## timetable

```
PeriodTemplate (institution FK, name, start_time, end_time, order_index, day)
Timetable       (institution FK, class_or_section FK, course FK null,
                 academic_year FK, term FK, version, status [DRAFT|PUBLISHED|ARCHIVED])
TimetableEntry  (timetable FK, day, period FK, subject FK, teacher FK,
                 room, status, is_substitution, source_entry FK null)
TimetableChangeRequest (institution FK, entry FK, proposed_* fields,
                 reason, status [PENDING|APPROVED|REJECTED], requested_by,
                 approved_by, approved_at)
TimetableConflict (institution FK, timetable FK, conflict_type,
                 description, entry_a FK, entry_b FK, resolved_at)
```

## attendance

```
TeacherAttendance (institution FK, teacher FK, date, status, check_in, check_out)
LeaveType         (institution FK, name, paid, max_days)
LeaveRequest      (institution FK, teacher FK, leave_type FK, start_date, end_date,
                   reason, status [PENDING|APPROVED|REJECTED], approved_by, approved_at)
StudentAttendance (institution FK, student FK, date, status, marked_by, remark)
PeriodAttendance  (institution FK, student FK, entry FK, date, status, marked_by)
```

## substitution

```
SubstitutionRequest     (institution FK, absent_teacher FK, entry FK, date,
                         reason, status, created_by)
SubstituteRecommendation (request FK, teacher FK, score, reasons JSON, rank)
SubstituteAssignment    (request FK, substitute_teacher FK, status
                         [PROPOSED|APPROVED|REJECTED|COMPLETED], approved_by, approved_at)
HandoverMaterial        (assignment FK, notes, created_by)
HandoverAttachment      (material FK, file, filename, uploaded_by)
ClassOutcome            (assignment FK, status, notes, recorded_by, recorded_at)
```

## curriculum

```
Syllabus      (institution FK, subject FK, class_or_section FK, course FK null,
               academic_year FK, term FK, title)
Chapter       (syllabus FK, title, order_index, planned_hours)
LessonPlan    (chapter FK, title, objectives, content, duration_minutes, resources JSON)
ClassSessionLog (institution FK, entry FK null, subject FK, class_or_section FK,
               chapter FK null, topic, date, status [COMPLETED|PARTIAL|SKIPPED],
               teacher FK, notes)
LessonCompletion (institution FK, chapter FK, completed_date, status, verified_by)
```

## content

```
ContentItem (institution FK, type [NOTE|CLASSWORK|HOMEWORK], title, body,
             subject FK null, class_or_section FK null, course FK null,
             due_date, created_by, status [DRAFT|PUBLISHED|ARCHIVED])
ContentAttachment (content FK, file, filename, uploaded_by)
```

## assessments

```
QuestionBank    (institution FK, subject FK, name, description)
Question        (bank FK, type [MCQ|TRUE_FALSE|SHORT|LONG], text, marks,
                 options JSON, correct_answer, difficulty)
Assessment      (institution FK, title, type [QUIZ|TEST|EXAM|ASSIGNMENT],
                 subject FK null, class_or_section FK null, course FK null,
                 academic_year FK, term FK, date, total_marks, pass_marks, status)
AssessmentQuestion (assessment FK, question FK, marks_override)
StudentAssessment  (assessment FK, student FK, obtained_marks, grade,
                 remarks, status, submitted_at)
GradeScale      (institution FK, grade, min_mark, max_mark, remark)
```

## notifications

```
NotificationTemplate (institution FK, event, channel [EMAIL|SMS|WHATSAPP|PUSH],
                      subject, body)
Notification         (institution FK, recipient_user FK, template FK null,
                      channel, status [PENDING|SENT|FAILED|CANCELLED], payload JSON,
                      sent_at)
NotificationDeliveryLog (notification FK, provider, attempt, status,
                      provider_response, error, created_at)
ProviderConfig   (institution FK, channel, provider, config JSON, is_active, priority)
```

## ai

```
AIJob           (institution FK, job_type [QUESTION_GEN|MATERIAL_GEN|SUMMARIZE],
                status [QUEUED|RUNNING|SUCCESS|FAILED], input JSON, output JSON,
                error, created_by)
GeneratedContent (institution FK, job FK null, content_type, title, body,
                status [DRAFT|PENDING_REVIEW|APPROVED|REJECTED],
                reviewed_by, reviewed_at, review_note)
```

## coordinator

```
CommandCenterWidget (institution FK, key, label, config JSON, order_index, visible_roles)
CoordinatorTask     (institution FK, type, title, payload JSON,
                     status [OPEN|IN_PROGRESS|DONE], assignee FK, created_by)
```

## analytics

```
StudentProgressSnapshot (institution FK, student FK, term FK, metrics JSON, computed_at)
TeacherWorkloadSnapshot (institution FK, teacher FK, month, periods_taught,
                         substitutions, leave_days, metrics JSON, computed_at)
```

## audit

```
AuditLog     (institution FK, actor FK null, action, model, object_id,
              object_repr, before JSON, after JSON, ip_address, user_agent, created_at)
Backup       (institution FK, kind [FULL|INCREMENTAL], path, size_bytes,
              status, checksum, created_at)
SystemSetting (institution FK, key, value, description)
```

---

## Key constraints & indexes

- `@@unique` on natural keys: `(institution, email)`, `(institution, roll_number)`,
  `(institution, code)` for subjects/courses, `(timetable, day, period)` for entries,
  `(institution, student, date)` for attendance, `(request, teacher)` for recommendations.
- Index `institution` on **every** business model; composite indexes on hot paths
  (e.g. `(institution, student, date)`, `(institution, teacher, date)`, `(timetable, day)`).
- `on_delete=PROTECT` for referenced masters (subject, teacher) to prevent orphaning history;
  `CASCADE` from institution to all tenant data.
- Soft-delete / status fields instead of hard deletes for auditability.
