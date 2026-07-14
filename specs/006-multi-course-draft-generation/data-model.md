# Data Model: Multi-Course Draft Generation

## Persisted Entities

### Draft Schedule

The current generated teaching plan for one course in one semester.

#### Fields

- `id`: Stable Draft Schedule identifier.
- `course_id`: Related Course.
- `semester_id`: Related Semester.
- `revision`: Positive integer optimistic-concurrency token; starts at 1.
- `selected_time_window_id`: Existing nullable legacy traceability field.
- `status`: Existing schedule state, currently `generated`.
- `created_at`: Existing creation timestamp.
- `sessions`: Ordered child Draft Sessions.

#### Identity And Relationships

- Exactly zero or one Draft Schedule may exist for each `(course_id, semester_id)` pair.
- One Course may therefore retain Draft Schedules in multiple Semesters.
- A Draft Schedule owns zero or more Draft Sessions through the existing delete-orphan relationship.

#### Revision Rules

- Creating a Draft Schedule sets `revision = 1`.
- Successful regeneration for the same course-semester replaces its Draft Sessions and increments `revision` by 1.
- A successful manual Draft Session edit increments the parent Draft Schedule revision by 1.
- Failed generation, cancelled confirmation, and rejected manual edits do not change the revision.
- Batch replacement uses the prepared `id` and `revision` as a conditional write precondition.
- If a prepared course expected no Draft Schedule but one now exists, the course is stale and the new schedule is preserved.

#### Migration Rules

- Existing Draft Schedule rows retain their IDs, semester IDs, sessions, and status.
- Existing rows receive `revision = 1`.
- The current global unique constraint on `course_id` is replaced with `uq_draft_schedule_course_semester` on `(course_id, semester_id)`.
- The migration must be valid for SQLite table recreation/batch operations and must be verified against existing data.

### Draft Session

One generated or manually edited teaching occurrence belonging to a Draft Schedule.

#### Existing Fields

- `id`
- `draft_schedule_id`
- `course_id`
- `lecturer_id`
- `cohort_id`
- `room_id`
- `date`
- `start_time`
- `end_time`
- `units`
- `time_window_id`
- `constraint_window_index`

#### Rules

- Existing one-session-per-date-per-Draft-Schedule uniqueness remains unchanged.
- Successful regeneration replaces all sessions for the target course-semester only.
- A failed or stale course outcome preserves all existing sessions and manual edits.
- Session persistence does not store batch outcome or conflict-alert data.

### Generation Constraint Set

The saved planning period and ordered allowed weekly teaching windows for one course in one semester.

#### Fields

- `id`: Stable saved constraint-set identifier.
- `course_id`: Related Course.
- `semester_id`: Related Semester.
- `planning_start_date`
- `planning_end_date`
- `revision`: Positive integer optimistic-concurrency token; starts at 1.
- `created_at`
- `updated_at`
- `windows`: Ordered child Generation Constraint Windows.

#### Identity And Relationships

- At most one saved set exists for `(course_id, semester_id)`.
- A set owns one or more ordered Generation Constraint Windows after a successful save.

#### Revision And Batch Rules

- Creating a saved set sets `revision = 1`.
- Changing a saved planning period or its windows increments `revision` by 1.
- Clearing a saved set deletes it; a later new set receives a new ID and revision 1.
- Batch execution snapshots the active source at operation start:
  - saved set ID and revision when one exists;
  - a normalized fingerprint of semester dates and Study Type Time Window defaults when no saved set exists.
- Unchanged saved constraints used by a successful batch course are not rewritten or revision-incremented.
- Defaults used by a course with no saved set are persisted after successful generation, matching existing generation behavior.
- If the active constraint source changes before conditional persistence, the course receives `STALE_GENERATION_CONSTRAINTS`; its schedule and newer constraints remain unchanged.

### Generation Constraint Window

One ordered recurring weekly teaching window owned by a Generation Constraint Set.

#### Existing Fields

- `id`
- `constraint_set_id`
- `source_time_window_id`
- `weekday`
- `start_time`
- `end_time`
- `sort_order`

#### Rules

- Window validation remains the same as single-course generation.
- A normalized constraint snapshot includes source ID, weekday, start, end, and order for every active window.

## Transient Contract Entities

These entities exist only in request/response or in-process state. They are not persisted.

### Batch Preparation Request

The user's proposed selection before confirmation.

#### Fields

- `semesterId`: Target Semester.
- `operationKind`: `initial` or `retry`.
- `courseIds`: Ordered distinct course identifiers.

#### Validation

- `initial` requires 2-50 distinct IDs.
- `retry` requires 1-50 distinct IDs.
- Duplicate IDs reject the whole preparation request.
- A nonexistent Semester rejects the whole preparation request.
- A nonexistent Course does not reject preparation; it is represented as unavailable and later receives a failed execution outcome.

### Prepared Course Snapshot

Backend-derived state for one requested course at confirmation time.

#### Fields

- `courseId`
- `courseName`: Nullable when the Course is unavailable.
- `available`: Whether current planning data for the Course exists.
- `draftScheduleId`: Same-semester Draft Schedule ID, or null.
- `draftRevision`: Same-semester Draft Schedule revision, or null.
- `replacementRequired`: True only when a same-semester Draft Schedule exists.

#### Rules

- `draftScheduleId` and `draftRevision` are both null or both present.
- Another-semester Draft Schedule is never a replacement target.
- The client treats the complete prepared list as immutable while confirmation is open.
- Cancelling confirmation discards this snapshot and performs no execution request.

### Batch Execution Request

The immutable prepared selection submitted for generation.

#### Fields

- `semesterId`
- `operationKind`
- `replacementConfirmed`
- `courses`: Ordered list of course IDs plus their expected same-semester Draft Schedule ID/revision pair.

#### Validation

- Count and uniqueness rules match preparation.
- When any prepared item has an expected Draft Schedule, `replacementConfirmed` must be true.
- Course order is preserved for deterministic outcome display but does not affect placement.

### Course Generation Candidate

In-memory successful output from one call to the existing single-course generator before persistence.

#### Fields

- `coursePlan`
- `semesterPlan`
- `activeConstraints`
- `constraintSnapshot`
- `expectedDraftSnapshot`
- `generatedSessions`

#### Rules

- No database write occurs while candidates are being generated.
- Candidate sessions do not consider other courses' sessions or conflicts.
- A generation validation failure produces a failed Course Generation Outcome instead of a candidate.

### Course Generation Outcome

One result for every requested course after normal execution.

#### Fields

- `courseId`
- `courseName`: Nullable only when the Course is unavailable.
- `status`: `succeeded` or `failed`.
- `draftScheduleId`: Present for success, absent for failure.
- `draftRevision`: Present for success, absent for failure.
- `errors`: Empty for success; one or more course failure details for failure.

#### Course Failure Codes

- Existing single-course generation codes:
  - `INSUFFICIENT_ROOM_CAPACITY`
  - `INVALID_SESSION_PREFERENCE`
  - `NO_FITTING_TIME_WINDOW`
  - `INSUFFICIENT_SEMESTER_CAPACITY`
  - `INVALID_PLANNING_PERIOD`
  - `INVALID_TEACHING_WINDOW`
  - `MISSING_TEACHING_WINDOW`
- Batch course codes:
  - `COURSE_NOT_FOUND`
  - `PLANNING_INPUT_INCOMPLETE`
  - `STALE_DRAFT_SCHEDULE`
  - `STALE_GENERATION_CONSTRAINTS`

#### Rules

- A normal execution response contains exactly one outcome per requested course.
- Expected course failures preserve that course's pre-operation Draft Schedule, sessions, manual edits, and saved constraints.
- Lecturer, room, and Cohort overlaps do not produce failed outcomes; they remain non-blocking alerts in the refreshed overview.

### Batch Generation Result

The transient current-session result returned after a normal execution.

#### Fields

- `semesterId`
- `operationKind`
- `summary.total`
- `summary.succeeded`
- `summary.failed`
- `outcomes`

#### Invariants

- `summary.total = number of requested courses`.
- `summary.succeeded + summary.failed = summary.total`.
- Outcome order matches the request order.
- All-success, partial-success, and all-expected-failure executions return this shape.
- An unexpected operation-wide failure returns an operation error, no success outcomes, and leaves no attempt changes.
- The result and failed-course retry set are not persisted and may clear after reload/remount.

## State Transitions

### Request-Level Flow

```text
selection
  -> prepared
  -> ready (no replacements)
  -> confirmation required -> cancelled
                           -> confirmed
  -> executing
  -> completed (all success | partial success | all expected failure)
  -> operation failed (all attempt changes rolled back)
```

### Course-Level Flow

```text
requested
  -> unavailable -> failed
  -> generation invalid -> failed
  -> candidate
      -> draft stale -> failed, newer data preserved
      -> constraints stale -> failed, newer data preserved
      -> conditionally saved -> succeeded
```

## Transaction Boundaries

- Preparation is read-only.
- Execution owns one database transaction for the attempt.
- Candidate generation is side-effect free.
- Each candidate persistence runs in a nested savepoint.
- Known stale precondition failures roll back the course savepoint and become failed outcomes.
- Any unexpected persistence or infrastructure exception rolls back the outer transaction and returns no successful outcomes.
- The outer transaction commits once after all expected outcomes are final.
