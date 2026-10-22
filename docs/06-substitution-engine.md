# Substitute Teacher Recommendation Engine

This is the **flagship workflow** of the brief:

> Teacher absence → identify affected timetable periods → recommend eligible available
> substitutes → obtain coordinator approval → provide lesson handover material → record actual
> class outcome → update confirmed syllabus progress → generate relevant reports and notifications.

---

## 1. Trigger

A teacher is absent. Sources:
- `TeacherAttendance` marked ABSENT, or
- an approved `LeaveRequest` for today, or
- a manual "mark absent" action by the coordinator.

The system finds the teacher's **timetable entries for the affected date/periods** and, for each,
creates a `SubstitutionRequest`.

## 2. Eligibility rules

A candidate substitute is **eligible** only if **all** of these hold at the period in question:

1. **Not already teaching** in that period (no `TimetableEntry` for the candidate at that
   day/period in a PUBLISHED timetable).
2. **Not on approved leave** covering that date.
3. **Not marked absent** that day.
4. **Subject match** — candidate teaches the same `Subject` (hard constraint when
   `strict_subject=True`, soft otherwise).
5. **Workload cap** — candidate's periods this week < `max_periods_per_week`
   (or the institution's configured weekly cap).
6. **No back-to-back overloaded block** if the institution flags it (optional soft rule).

## 3. Scoring (ranking)

Each eligible candidate receives a score; the top-N (default 3) become
`SubstituteRecommendation` rows ranked by `rank`.

```
score = w1 * subject_match        # 40  (1.0 same subject, 0.3 related, 0.0 other)
      + w2 * availability         # 20  (free periods remaining this week, normalized)
      + w3 * workload_balance     # 15  (inverse of current week load)
      + w4 * past_substitution    # 10  (recent successful substitutions / feedback)
      + w5 * preference           # 10  (teacher self-declared willingness)
      + w6 * proximity            #  5  (same department / same building)
```

Weights are configurable per institution via `InstitutionSettings`. Each recommendation stores
the individual `reasons` (JSON) so the coordinator sees **why** a teacher is suggested.

## 4. Approval gate

- Recommendations are **suggestions only**. Nothing is auto-assigned.
- The coordinator selects one (or overrides) → `SubstituteAssignment` with
  `status=APPROVED`, `approved_by`, `approved_at`.
- If no eligible candidate exists, the request escalates to the coordinator as
  `status=UNRESOLVED` and can trigger a notification.

## 5. Handover

Once approved, the system collects **HandoverMaterial**:
- the lesson plan / chapter for that period,
- pending homework / notes,
- any attachments (from `content` / `curriculum`),
and marks it ready for the substitute.

## 6. Outcome & syllabus update

- The substitute (or coordinator) records a `ClassOutcome`: `COMPLETED`, `PARTIAL`, `SKIPPED`,
  with notes.
- Only a **COMPLETED/PARTIAL** outcome may update `LessonCompletion` / `ClassSessionLog`, and
  the update is **explicit** — never inferred from elapsed time (brief requirement #5).
- This feeds the curriculum progress and analytics.

## 7. Notifications

At each transition the `notifications` app emits templated, multi-channel messages:
absence detected → request created → substitute proposed → approved → outcome recorded →
progress updated. Every send is logged with retries.

## 8. Data flow

```
TeacherAttendance(ABSENT) / LeaveRequest(APPROVED)
        │
        ▼
SubstitutionRequest  ──►  find TimetableEntry(teacher, date)
        │
        ▼
score candidates ──► SubstituteRecommendation (ranked)
        │
        ▼  coordinator picks
SubstituteAssignment (APPROVED) ──► HandoverMaterial
        │
        ▼  substitute records
ClassOutcome ──► LessonCompletion / ClassSessionLog
        │
        ▼
Reports + Notifications
```

## 9. Edge cases

- Multiple periods absent in a row → group into one request with multiple entries.
- Same candidate free for consecutive periods → prefer grouping (fewer disruptions).
- Substitute later cancels → re-open request and re-rank (history preserved).
- No published timetable for the class → skip auto-detection, notify coordinator.
