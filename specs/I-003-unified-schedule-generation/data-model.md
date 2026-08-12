# Data Model: Unified Teaching Schedule Generation

## Ownership overview

```text
Semester
  |-- default start/end dates
  |-- active editable ScheduleRevision
  |-- Course (1..20 selected per operation)
  |     |-- StudyType -> active StudyTypeTimeWindow rows (weekly authority)
  |     |-- optional GenerationConstraintSet (date override only)
  |     |-- DraftSchedule -> DraftSession rows
  |     `-- ExamSession rows (active or past)
  `-- Holiday rows / planner unavailable dates
```

## Existing persisted entities

### Semester

Authoritative semester boundary and lifecycle container.

Relevant fields:

- `id`
- `start_date`, `end_date`
- active editable schedule revision relationship

Rules:

- A course date override must remain inside these dates.
- In the absence of an override, these dates are the course planning period.

### Course

Academic source for generation demand and relationships.

Relevant fields and relationships:

- `id`, `name`, teaching-unit/session-unit configuration
- `cohort_id`
- `study_type_id`
- eligible lecturer and room relationships

Rules:

- The current `study_type_id` selects weekly windows at read/preparation time.
- A study-type change revalidates existing sessions and invalidates preparations
  made from the previous mapping.

### StudyTypeTimeWindow

The sole persisted weekly-window authority.

Relevant fields:

- `id`, `study_type_id`
- `weekday`, `start_time`, `end_time`, `sort_order`
- `is_active`, `revision`

Rules:

- Only active rows are generation candidates.
- Windows are never copied as course-specific overrides.
- A course is unavailable for automatic generation when no active mapped window
  can host its minimum session duration.

### GenerationConstraintSet (reinterpreted without schema change)

Persisted optional course-semester date override. The existing model name and
table remain to avoid an unnecessary migration.

Relevant fields:

- `id`
- `course_id`, `semester_id` (unique pair)
- `planning_start_date`, `planning_end_date`
- `revision`

Rules and transitions:

- No row: effective dates inherit `Semester.start_date/end_date`; API reports
  `isCustom=false` and `revision=null`.
- Save a valid override: insert revision 1 or update and increment revision;
  commit immediately.
- Idempotent save of identical dates: retain the revision.
- Reset: delete the override, returning effective semester dates.
- Any save/reset requires the active editable schedule revision and optimistic
  constraint revision (`null` when creating).
- Saving dates triggers refreshed validation output but never moves sessions.

### GenerationConstraintWindow (legacy child data)

No longer authoritative.

Transition policy:

- Readers and tokens ignore these rows.
- Saving or resetting the parent clears existing children.
- No new child row is written.
- The table may remain in this feature to avoid unrelated migration work; later
  physical removal requires a separate data-migration feature.

### DraftSchedule and DraftSession

Persisted teaching plan for one course and semester/revision context.

Generation roles:

- Selected-course drafts are replacement candidates and require confirmation.
- Unselected-course sessions are immutable protected occupancy.
- Selected-course old sessions are not carried as fixed occupancy; they remain
  unchanged unless a proven permitted result is committed.
- Manual edits are preserved on every rejected, cancelled, stale, timed-out, or
  unproven operation.

### ExamSession

Persisted exam occurrence with snapshot resource relationships.

Derived lifecycle:

- `active`: `exam_date >= institution_today()`
- `past`: `exam_date < institution_today()`

Generation roles:

- Every active exam in the selected semester is immutable protected lecturer,
  room, and cohort occupancy.
- An active exam for a selected course supplies `latest_teaching_end` equal to its
  start timestamp.
- Past exams are stored and displayed but omitted from generation occupancy,
  deadlines, and freshness evidence.

No exam record is changed by teaching generation.

## Planning-time value objects

### EffectiveCourseConstraints

Not a new table. Built when constraints are read or preparation is loaded.

Fields:

- `course_id`, `semester_id`
- `planning_period { start_date, end_date }`
- `is_custom`
- `constraint_revision | null`
- `study_type { id, revision }`
- `allowed_windows[] { id, revision, weekday, start_time, end_time, sort_order }`

Invariants:

- Period lies within semester and start is not after end.
- Windows exactly match current active study-type mappings.
- Empty/too-short mappings make the course unavailable rather than falling back
  to copied or user-entered windows.

### ProtectedOccupancy

Not a new table. Normalized immutable intervals passed into candidate filtering.

Fields:

- `source_kind`: `teaching_session` or `active_exam`
- `source_id`, `course_id`
- `date`, `start_time`, `end_time`
- `lecturer_id | null`, `room_id | null`, `cohort_id | null`

Invariants:

- Teaching entries come only from unselected schedules.
- Exam entries come only from active exams in the selected semester.
- Intervals use half-open overlap: `a.start < b.end && b.start < a.end`.
- Equal boundaries are adjacent, not overlapping.

### OptimizationCourse extension

The existing solver input gains:

- `latest_teaching_end: datetime | null`

Candidate rule:

- Reject a candidate when its end timestamp is later than
  `latest_teaching_end`.
- Record the blocking category `ACTIVE_EXAM_BOUNDARY` when substantiated.

### UnifiedTeachingGenerationPreparation

Existing prepared optimization response, extended for UI review and freshness.

Per-course fields:

- course identity and availability
- draft identity/revision and replacement requirement
- scheduled and remaining units
- effective planning period and whether it is custom
- study type identity/name
- read-only mapped weekly windows
- input snapshot token

Shared fields:

- semester and active schedule revision
- unavailable dates
- shared snapshot token
- replacement course IDs

Freshness evidence includes:

- selected course/draft state
- unselected protected teaching occupancy
- active exam occupancy and selected-course exam boundaries
- effective date constraints and study-type windows
- resources, holidays, unavailable dates, semester, and working revision

Past exams are deliberately excluded.

### CourseOptimizationOutcome

Existing result entity retained. Blocking reasons add:

- `ACTIVE_EXAM_BOUNDARY`
- `STUDY_TYPE_WINDOW_UNAVAILABLE`

Lecturer, room, and cohort occupancy continue to use the existing
`LECTURER_OCCUPIED`, `ROOM_OCCUPIED`, and `COHORT_OCCUPIED` codes regardless of
whether the protected occurrence is teaching or an active exam. A substantiated
occupancy or boundary reason may additionally carry:

- `source_kind`: `teaching_session` or `active_exam`
- `source_id`: the protected teaching-session or exam identifier

`ACTIVE_EXAM_BOUNDARY` is reserved for the same-course latest teaching-end rule;
it does not replace a resource-specific occupancy category.

`STUDY_TYPE_WINDOW_UNAVAILABLE` identifies a course whose current study type has
no active mapped window capable of hosting the course's minimum session length.
Outcomes are always associated with one selected course.

## Validation alert identity

An overlap alert is logically identified by:

```text
(affected_session_id, related_session_id, conflict_code)
```

The conflict code is one of `LECTURER_OVERLAP`, `ROOM_OVERLAP`, or
`COHORT_OVERLAP`. This permits three warnings for one session pair only when all
three resources genuinely conflict, while preventing duplicate warnings within a
single category.

## Transaction boundaries

### Constraint save/reset transaction

1. Claim active editable revision.
2. Validate expected constraint revision and dates.
3. Insert/update/delete date override and clear legacy window children.
4. Commit.
5. Reload effective constraints and validation state.

This transaction is independent from generation.

### Unified generation transaction

1. Preparation is read-only.
2. Generation revalidates all tokens before solve/save.
3. Solver evaluates selected courses against protected occupancy.
4. If a permitted, proven, non-worsening result exists, replace applicable
   selected drafts in one transaction.
5. On stale, invalid, rejected, timeout, unproven, or persistence failure, roll
   back all draft changes. Never mutate constraints or exams.
