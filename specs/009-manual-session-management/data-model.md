# Data Model: FS-009 Manual Session Management

No database migration is required. FS-009 reuses existing entities and adds derived/transport concepts only.

## Existing Persisted Entity: Draft Schedule

Represents the current non-empty draft for one course in one semester.

### Relevant fields

- `id`: Stable Draft Schedule identity.
- `course_id`, `semester_id`: Unique course-semester identity.
- `revision`: Positive optimistic-concurrency token for every schedule-content mutation.
- Course, cohort, study-type, and semester snapshot fields: Existing display and validation context captured when the schedule is created.
- `sessions`: One or more Draft Sessions. Cascade deletes remove sessions with their parent.

### Rules

- At most one Draft Schedule exists for a course-semester.
- A new manual-only schedule starts at revision 1 and uses current Course, Cohort, Study Type, and Semester values for the existing snapshots.
- Adding or deleting a session while the parent survives increments revision by one.
- Editing and regeneration continue their established revision behavior.
- Removing the last session deletes the parent; an empty Draft Schedule is never retained.
- Complete-draft deletion removes only this parent and its child sessions.
- Generation constraints and source planning records are not children of Draft Schedule and remain untouched.

## Existing Persisted Entity: Draft Session

Represents one generated, manually edited, or manually created teaching occurrence.

### Relevant fields

- `id`: Stable session identity.
- `draft_schedule_id`: Required parent.
- `course_id`: Same course as the parent.
- `lecturer_id`: Inherited from the current course when manually created.
- `cohort_id`: Inherited from the current course when manually created.
- `room_id`: Existing room selected by the planner.
- `date`: Session date.
- `start_time`, `end_time`: Final clock interval, including any planner override.
- `units`: Positive whole teaching-unit count used for scheduled/remaining calculations.
- `time_window_id`: Nullable; manual creation does not claim a generated source window.
- `constraint_window_index`: Existing field; manual creation uses a neutral default and validation derives active-window alerts from actual date/time.

### Manual-creation validation

- Course, Semester, course-assigned Lecturer, Cohort, and selected Room must exist at save time.
- Date must lie inside the selected Semester.
- End time must be later than start time on the same date.
- Units must be a positive whole number and may not exceed current remaining units.
- No sibling session in the same Draft Schedule may use the same date.
- Selected Room capacity must be at least the current Cohort size used for hard capacity validation.
- Lecturer, room, cohort overlap and active/default window findings do not block persistence; they appear as Validation Alerts.
- Session origin is not persisted because generated and manual sessions have identical behavior in FS-009.

## Existing Persisted Entity: Generation Constraint Set

Represents saved planning limits for one course and semester.

### FS-009 rule

- Manual creation, single-session deletion, last-session deletion, and complete-draft deletion never create, update, or delete this entity or its windows.
- Its revision is independent of Draft Schedule revision.

## Existing Persisted Source Entities

`Course`, `Semester`, `Lecturer`, `Room`, `Cohort`, `StudyType`, and `StudyTypeTimeWindow` provide current planning context.

### FS-009 rules

- Schedule deletion never deletes or updates a source entity.
- Manual creation reads the Course's current Lecturer and Cohort.
- The planner may select any existing Room; capacity is the hard selection rule in this slice.
- FS-008 eligible-resource and availability relationships are not required or enforced by FS-009.

## Derived Concept: Course-Semester Progress

Not persisted.

### Fields

- `course_id`: Course identity.
- `semester_id`: Semester identity.
- `total_units`: Current `Course.total_units`.
- `scheduled_units`: Sum of `units` across the current Draft Schedule's sessions, or zero when no draft exists.
- `remaining_units`: `max(total_units - scheduled_units, 0)`.

### Rules

- Progress is calculated from the complete saved schedule, not active UI filters.
- A course with no Draft Schedule has zero scheduled units and all current course units remaining.
- Manual creation is rejected if requested units exceed current remaining units.
- If prior source changes leave scheduled units above current total units, remaining units display as zero; FS-009 does not repair existing sessions.

## Transient Concept: Deletion Confirmation Snapshot

Client-held and not persisted.

### Fields

- `kind`: `session` or `course_draft`.
- `draft_schedule_id`: Confirmed parent identity.
- `expected_draft_revision`: Revision displayed to the planner and submitted together with the parent identity on confirm.
- `session_id`: Required only for single-session deletion.
- `course_id`, `course_name`, `semester_id`, `semester_name`: Consequence context.
- `session_count`: One for single deletion; complete current count for full deletion.
- `units_removed`: Units removed from scheduled coverage.
- `resulting_remaining_units`: Remaining-unit value calculated from the confirmed current schedule.
- `last_session`: Whether single deletion will remove the parent.

### Rules

- Cancel discards the snapshot without a write.
- A revision mismatch makes the snapshot stale. The action is rejected, current state is refreshed, and a new confirmation snapshot is required.

## Transport Concept: Draft Schedule Mutation Result

Not persisted.

### Fields

- `course_id`, `semester_id`: Affected planning context.
- `scheduled_units`, `remaining_units`: Authoritative post-action progress.
- `draft_schedule`: Updated Draft Schedule with validation alerts, or null when no sessions remain.

## State Transitions

```text
No Draft Schedule
  -- create valid manual session --> Draft Schedule revision 1, one session

Draft Schedule revision N
  -- create valid manual session --> Draft Schedule revision N+1, new session added
  -- delete one of many sessions with expected revision N --> revision N+1
  -- delete last session with expected revision N --> No Draft Schedule
  -- clear full draft with expected revision N --> No Draft Schedule
  -- stale delete with expected revision != N --> unchanged
  -- invalid create/delete or persistence failure --> unchanged
```

Every transition preserves source planning records and saved Generation Constraint Sets.
