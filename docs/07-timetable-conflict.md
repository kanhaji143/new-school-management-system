# Timetable Conflict Detection

Timetable is a **versioned, publish-gated** entity. Changes are validated **on save** and again
**on publish**, and any real change to a published timetable requires an approved
`TimetableChangeRequest` (brief requirement: *no unapproved timetable changes*).

---

## 1. Conflict types

| Code | Type | Description |
| --- | --- | --- |
| `TEACHER_DOUBLE_BOOKED` | Hard | Same teacher in two entries at the same day+period |
| `ROOM_DOUBLE_BOOKED` | Hard | Same room in two entries at the same day+period |
| `CLASS_DOUBLE_BOOKED` | Hard | Same class/section has two subjects in one period |
| `TEACHER_UNAVAILABLE` | Hard | Teacher on approved leave / marked absent |
| `TEACHER_OVERLOAD` | Soft | Teacher exceeds weekly period cap |
| `CLASS_OVERLOAD` | Soft | Class exceeds daily period cap |
| `SUBJECT_FREQUENCY` | Soft | Subject weekly frequency deviates from plan |
| `WORKLOAD_IMBALANCE` | Soft | Large disparity in teacher workloads |

Hard conflicts **block publish**; soft conflicts are **warnings** the coordinator can override
(with a recorded reason).

## 2. Detection algorithm

```
validate(timetable):
    entries = timetable.entries (day, period, teacher, room, class, subject)
    index by (day, period)

    for each (day, period) bucket:
        # hard: one resource used once
        if duplicate teacher  -> TEACHER_DOUBLE_BOOKED
        if duplicate room     -> ROOM_DOUBLE_BOOKED
        if duplicate class    -> CLASS_DOUBLE_BOOKED

    for each teacher:
        weekly = count entries across the week
        if weekly > max_periods_per_week -> TEACHER_OVERLOAD

    for each (teacher, day):
        if teacher on leave/absent that day -> TEACHER_UNAVAILABLE

    for each class:
        daily = count entries that day
        if daily > max_periods_per_day -> CLASS_OVERLOAD

    # soft: subject frequency vs plan
    compare per-subject weekly counts to ClassSubject.planned_periods

    return ConflictReport(hard=[...], soft=[...])
```

Complexity is O(n) with hash maps keyed by `(day, period)` — fine for a single timetable
(hundreds of entries). For whole-institution validation, run per timetable and aggregate.

## 3. Lifecycle

```
DRAFT ──validate──► DRAFT (conflicts listed)
   │
   │  all HARD conflicts resolved
   ▼
PUBLISHED  ──change requested──► TimetableChangeRequest(PENDING)
                                   │ coordinator approves
                                   ▼
                               new version DRAFT ──validate──► PUBLISHED
```

- `Timetable` carries a `version` and `status`. Publishing a new version archives the old one.
- Editing a PUBLISHED timetable is not allowed directly; a `TimetableChangeRequest` is created
  and, on approval, applied to a new draft version.
- Every change is written to `AuditLog`.

## 4. Auto-generation (optional, later phase)

A constraint-based generator (greedy + backtracking, or OR-Tools CP-SAT) can propose a draft
timetable from `ClassSubject` assignments + `PeriodTemplate` + room inventory, then run the
validator above. This is a **phase-2** feature; phase 1 ships manual entry + validation.

## 5. APIs (summary)

```
POST   /api/timetables/                         create draft
GET    /api/timetables/{id}/                    detail + entries
POST   /api/timetables/{id}/validate/           run conflict check
POST   /api/timetables/{id}/publish/            publish (blocked on hard conflicts)
POST   /api/timetables/{id}/change-requests/    request a change
GET    /api/timetable-conflicts/                list conflicts (filter by status)
```
