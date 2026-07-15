# Data Model: Academic Planning Data Administration

## Modeling principles

- Academic source records remain mutable; saved Draft Schedule academic facts are immutable snapshots.
- Permanent deletion is allowed only after explicit usage checks prove there are no dependent records or saved schedule references.
- Inactivity is reversible and never cascades to dependent status. Planning availability is derived from the complete active relationship chain.
- Every catalog mutation uses an integer revision for optimistic concurrency.
- Names remain reserved across active and inactive records within the same named category.

## Shared catalog fields

Every administrable academic entity has:

| Field | Meaning | Validation |
|---|---|---|
| `id` | Stable internal identity | Generated, immutable |
| `is_active` | Planner-controlled lifecycle state | Required; defaults true; no automatic date-based transition |
| `revision` | Optimistic-write token | Positive integer; increments once per successful edit/archive/reactivate |

Semester, Cohort, Course, and Study Type additionally have `name`, a canonical nullable `normalized_name`, a collision-safe internal `normalized_name_key`, and `name_repair_required`. The display name is trimmed and case-folded for comparison. New and repaired rows store that canonical value under a unique constraint across active and inactive rows. Supported legacy conflicts temporarily have no canonical unique value, retain distinct internal keys, and are visibly marked for planner repair; a successful edit or reactivation requires a unique canonical name.

## Semester / Planning Period

| Field | Meaning | Validation |
|---|---|---|
| `id` | Semester identity | Stable |
| `name`, `normalized_name` | Planner-facing name and uniqueness key | Required; normalized name unique among Semesters |
| `start_date` | Inclusive first planning date | Required |
| `end_date` | Inclusive final planning date | Required; on or after start |
| Shared catalog fields | Lifecycle and concurrency | As above |

Relationships:

- One Semester is the current assignment for zero or more Courses.
- One Semester is referenced historically by zero or more Draft Schedules and Generation Constraint Sets.

Mutation rules:

- A date edit is rejected if any saved Draft Session for the Semester would lie outside the proposed interval.
- Archive does not change Course status; affected Courses become unavailable for new planning.
- Delete is blocked by current Course assignments, saved Draft Schedules, or retained constraint data.

## Cohort / Class

| Field | Meaning | Validation |
|---|---|---|
| `id` | Cohort identity | Stable |
| `name`, `normalized_name` | Planner-facing name and uniqueness key | Required; normalized name unique among Cohorts |
| `student_count` | Current cohort size for future planning | Positive whole number; no additional FS-007 upper limit |
| Shared catalog fields | Lifecycle and concurrency | As above |

Relationships:

- One Cohort is the current required relationship for zero or more Courses.
- Draft Schedule snapshots retain captured Cohort ID, name, and size.

Mutation rules:

- Editing size affects new/replaced schedules only.
- Archive leaves Course status unchanged but makes related Courses unavailable.
- Delete is blocked by current Courses and saved schedule references.

## Study Type

| Field | Meaning | Validation |
|---|---|---|
| `id` | Study Type identity | Stable |
| `name`, `normalized_name` | Planner-facing name and uniqueness key | Required; normalized name unique among Study Types |
| Shared catalog fields | Lifecycle and concurrency | As above |

Relationships:

- One Study Type owns zero or more Study Type Time Windows.
- One Study Type is required by zero or more Courses.
- Draft Schedule snapshots retain captured Study Type ID and name.

Mutation rules:

- Archive does not archive Time Windows or Courses; their own statuses remain unchanged.
- Delete is blocked by owned Time Windows, current Courses, or saved schedule references.

## Study Type Time Window

| Field | Meaning | Validation |
|---|---|---|
| `id` | Window identity | Stable |
| `study_type_id` | Owning Study Type | Required; immutable ownership after creation |
| `weekday` | Weekly day | Integer 0–6 using the existing Monday-first convention |
| `start_time` | Inclusive start | Required |
| `end_time` | Exclusive end | Required; later than start |
| `sort_order` | Stable display ordering | Non-negative whole number; server normalizes sibling ordering after mutations |
| Shared catalog fields | Lifecycle and concurrency | As above |

Constraints and rules:

- Exact `(study_type_id, weekday, start_time, end_time)` duplicates are rejected across active and inactive windows.
- Partial overlaps remain valid and are not merged.
- An active window whose Study Type is inactive is active-but-unavailable for planning.
- Delete is blocked by saved Generation Constraint Window provenance, Draft Schedule selection, or Draft Session references.
- Removing or archiving the final usable window is allowed only when it does not violate an explicit dependent constraint; otherwise Courses remain visible and new generation returns the specified missing-window feedback.

## Course

| Field | Meaning | Validation |
|---|---|---|
| `id` | Course identity | Stable |
| `name`, `normalized_name` | Planner-facing name and uniqueness key | Required; normalized name unique among Courses |
| `total_units` | Current total teaching units | Positive whole number |
| `min_session_units` | Existing minimum units per generated session | Positive whole number; not greater than maximum or total |
| `max_session_units` | Existing maximum units per generated session | Positive whole number; at least minimum and not greater than total |
| `cohort_id` | Current Cohort | Required and must exist |
| `study_type_id` | Current Study Type | Required and must exist |
| `current_semester_id` | Sole current Semester for new planning | Required for new and successfully updated Courses; nullable only for legacy repair |
| `lecturer_id` | Existing single Lecturer assignment | Required for generator compatibility; resource is read-only in FS-007 |
| `room_id` | Existing single Room assignment | Required for generator compatibility; resource is read-only in FS-007 |
| Shared catalog fields | Lifecycle and concurrency | As above |

Academic relationship eligibility is true when Course, current Semester, Cohort, and Study Type are active and valid. An otherwise eligible Course with no active usable Study Type Time Window remains in planning options with `available = false` and `MISSING_ACTIVE_TIME_WINDOW`; generation is blocked with actionable feedback. Lecturer/Room assignment continues to follow the established FS-001–FS-006 generation validation.

Reassignment changes `current_semester_id` only. It never changes Draft Schedule `semester_id`, saved constraints, snapshots, or sessions from earlier assignments.

Delete is blocked by Draft Schedules, Draft Sessions, Generation Constraint Sets, and any other saved planning reference.

## Draft Schedule academic snapshot

Draft Schedule remains the saved aggregate and retains its current IDs, revision, status, and sessions. Add these immutable values, populated on every successful create/replacement:

| Snapshot field | Captured fact |
|---|---|
| `course_name_snapshot` | Current trimmed Course name |
| `course_total_units_snapshot` | Course total units used for the schedule |
| `course_min_session_units_snapshot` | Minimum session units used for generation |
| `course_max_session_units_snapshot` | Maximum session units used for generation |
| `cohort_id_snapshot` | Cohort relationship at save time |
| `cohort_name_snapshot` | Cohort name at save time |
| `cohort_size_snapshot` | Cohort size used for capacity behavior |
| `study_type_id_snapshot` | Study Type relationship at save time |
| `study_type_name_snapshot` | Study Type name at save time |
| `semester_name_snapshot` | Assigned Semester name at save time |
| `semester_start_date_snapshot` | Semester start captured at save time |
| `semester_end_date_snapshot` | Semester end captured at save time |

Snapshot rules:

- Source `course_id` and `semester_id` remain for traceability and delete protection.
- Response context and academic validation for a saved schedule use snapshot values, including Cohort size and Study Type identity.
- Lecturer and Room remain live in FS-007 because their administration is out of scope; a later resource-administration slice must decide its own historical snapshot boundary.
- Editing an existing Draft Session does not refresh academic snapshots.
- Regenerating/replacing a Draft Schedule captures a new complete snapshot from current valid catalog values.
- Legacy schedules are backfilled once from the values available at migration time; earlier values cannot be reconstructed.

## Generation Constraint Set and Window

Existing Course/Semester uniqueness, revision, copied planning dates, and copied window weekday/time values remain. `source_time_window_id` is provenance only; historical constraint behavior uses the copied values.

Deletion usage includes both constraint sets and source-window references. Course reassignment does not move or remove existing constraint sets.

## Usage projection

Usage is calculated, not stored as mutable counts:

```text
UsageSummary
|- recordId
|- revision
|- canDelete
|- dependentRecords[]
|  |- type
|  `- count
|- savedSchedules
|  `- count
`- blockers[]
   |- kind: dependent | saved_schedule
   |- type
   |- count
   |- message
   `- prerequisiteAction (optional)
```

Examples of dependency edges:

| Source | Dependent catalog records | Saved planning references |
|---|---|---|
| Semester | Current Courses | Draft Schedules, Generation Constraint Sets |
| Cohort | Current Courses | Draft Sessions and Draft Schedule snapshots |
| Study Type | Current Courses, owned Time Windows | Draft Schedule snapshots |
| Course | None | Draft Schedules, Draft Sessions, Generation Constraint Sets |
| Time Window | None | Constraint Window provenance, Draft Schedule selection, Draft Sessions |

## State transitions

```text
Active --archive(expected revision)--> Inactive
Inactive --reactivate(expected revision + valid relationships/name)--> Active
Active/Inactive --delete(expected revision + no usage)--> Deleted
Active/Inactive --edit(expected revision + validation)--> same lifecycle state, revision + 1
Any stale mutation --> no change, STALE_REVISION
```

Dependent record statuses never change during a parent transition. Planning availability is recalculated from current relationships after every transition.

## Migration and backfill

1. Preflight normalized names; retain supported collisions as categorized planner-visible repair states rather than rename, merge, or stop startup.
2. Add lifecycle, revision, and normalized-name fields with safe backfill values.
3. Add Course current Semester assignment as nullable for migration.
4. Infer assignment from newest Draft Schedule, else newest Generation Constraint Set, else the sole Semester. Leave other ambiguous legacy Courses in repair-required state.
5. Add Draft Schedule snapshot columns, backfill them from current source relationships, then require values for every schedule.
6. Add canonical normalized-name uniqueness for new/repaired rows, collision-safe internal keys for legacy conflicts, and exact-window unique constraints after successful backfill.
7. Update startup schema recognition so supported legacy schemas and name conflicts migrate sequentially while unknown partial states stop safely.
8. Enable SQLite foreign-key enforcement for runtime and test connections while retaining explicit domain blocker checks.
