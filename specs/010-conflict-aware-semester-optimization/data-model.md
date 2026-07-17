# Phase 1 Data Model: FS-010 Conflict-Aware Semester Optimization

## Persistence Decision

FS-010 adds no database table or migration. Optimization preparation, candidates, solver state, reasons, and summaries are transient request/service objects. Successful results reuse the existing `DraftSchedule` and `DraftSession` aggregates; current generation constraints and source records remain authoritative.

## Existing Persisted Entities

### Semester

**Purpose**: Defines the selected planning boundary.

**Fields used**: `id`, `start_date`, `end_date`, `is_active`, `revision`.

**Rules**:

- Every selected course and generated session belongs to the one requested semester.
- Generated dates remain within both the semester and active course-semester planning period.
- A changed revision or date boundary makes dependent prepared input stale.

### Course

**Purpose**: Defines requested units, session-size bounds, cohort, Study Type, semester assignment, and eligible-resource relationships.

**Fields used**: `id`, `name`, `total_units`, `min_session_units`, `max_session_units`, `cohort_id`, `study_type_id`, `current_semester_id`, `is_active`, `revision`.

**Relationships**: One Cohort, one Study Type, zero or more eligible Lecturers, zero or more eligible Rooms, at most one Draft Schedule per semester, and at most one Generation Constraint Set per semester.

**Rules**:

- Selection contains 1–20 distinct course IDs.
- `total_units` is positive; minimum and maximum session units must form a valid positive range.
- Generated scheduled units never exceed current total units.
- Non-worsening uses the actual `sum(current DraftSession.units)` as the baseline. When that sum exceeds current total units, a generated alternative cannot qualify and the current draft remains unchanged.
- A changed Course revision or relationship set makes that course input stale.

### Lecturer and Room

**Purpose**: Supply eligible resources for generated sessions.

**Fields used**:

- Lecturer: `id`, `normalized_reference_code`, `is_active`, `revision`.
- Room: `id`, `normalized_reference_code`, `capacity`, `is_active`, `revision`.

**Relationships**: Course eligibility junctions, Resource Unavailability Periods, and Draft Session assignments.

**Rules**:

- Every generated session has exactly one active eligible Lecturer and one active eligible Room.
- Room capacity is at least current Cohort size.
- Resource active state, code, capacity, eligibility, or unavailability changes make dependent input stale.

### Resource Unavailability Period

**Purpose**: Excludes Lecturer or Room assignments over recurring or dated local wall-clock intervals.

**Fields used**: owner, kind, dates/weekday set, start/end time, revision.

**Rules**:

- Reuse FS-008 half-open overlap semantics.
- Any matching period excludes that resource assignment candidate.
- Changed periods make every candidate depending on the owner stale.

### Study Type Time Window / Generation Constraint Set

**Purpose**: Supplies active allowed weekdays, start/end times, and planning dates for each course.

**Rules**:

- Saved course-semester constraints replace defaults; otherwise active Study Type windows apply.
- A generated session starts at its selected allowed window start and ends within that window.
- One course has at most one generated session on a date.
- Changed active windows, constraint identity, constraint revision, or values make the course input stale.
- Existing saved custom constraints remain unchanged by optimization. When a successfully generated course had no saved set, persist the exact active defaults used by that result through the established generation behavior. Failed, stale, unchanged, and cancelled outcomes do not create or modify a set.

### Draft Schedule

**Purpose**: Stores the current course-semester schedule and acts as the whole replacement/stale-confirmation aggregate.

**Fields used**: `id`, `course_id`, `semester_id`, `revision`, source snapshots, sessions.

**Rules**:

- At most one Draft Schedule exists per Course/Semester.
- No empty Draft Schedule is created or retained by optimization.
- Retention means every current Draft Session remains unchanged.
- Replacement is permitted only after explicit preparation-based confirmation and only for a generated result meeting non-worsening and comparison rules.
- A changed identity or revision makes the course a stale replacement target.

### Draft Session

**Purpose**: Stores one current or generated teaching occurrence.

**Fields used**: Course, Lecturer, Cohort, Room, date, start/end time, units, source window identity/index.

**Rules**:

- Generated occurrences have positive allowed unit sizes and positive time intervals.
- Generated occurrences introduce no Lecturer, Room, or Cohort overlap.
- Existing retained conflicts remain countable baselines and are not automatically repaired.
- Conflict intervals are half-open; back-to-back sessions do not overlap.

## Transient Domain Entities

### Optimization Preparation

**Purpose**: Captures the planner-reviewed replacement scope and opaque evidence of material input state.

**Fields**:

- `semester_id`
- `unavailable_dates`: sorted distinct dates
- `shared_snapshot_token`: opaque fingerprint of semester boundary and fixed semester occupancy
- `courses`: ordered Course Preparation Snapshots
- `replacement_course_ids`

**Validation**:

- Tokens are equality/staleness evidence, not authentication secrets.
- Tokens are built from canonical identities, revisions, and relevant values; the raw input does not need to be returned to the client.
- The generate request must echo the preparation exactly.

### Course Preparation Snapshot

**Purpose**: Describes one selected course at confirmation time.

**Fields**:

- `course_id`, `course_name`, `available`
- nullable `draft_schedule_id`, nullable `draft_revision`
- `scheduled_units`, `remaining_units`, `replacement_required`
- `input_snapshot_token`: opaque fingerprint of course, cohort, resource eligibility/availability, active constraints, and current draft inputs

**Identity rule**: Unique by `course_id` within one preparation.

### Optimization Input

**Purpose**: Solver-independent, immutable model of the complete operation.

**Fields**:

- Semester dates and unavailable dates
- Ordered selected Course Optimization Inputs
- Ordered fixed semester sessions outside replaceable alternatives
- Overall monotonic deadline

**Rules**:

- Contains no ORM sessions or FastAPI schemas.
- All lists and keys are canonically sorted before candidate/model construction.
- Requested units across the supported reference workload are at most 600; fixed sessions are at most 500.

### Course Optimization Input

**Purpose**: Supplies one course's hard rules, resource candidates, allowed windows, current baseline, and explanation context.

**Fields**:

- Course identity, total/minimum/maximum units, cohort identity/size
- Planning period and allowed windows
- Active eligible Lecturer choices with unavailability
- Active eligible Room choices with capacity and unavailability
- Optional Current Draft Alternative

### Current Draft Alternative

**Purpose**: Represents complete preservation of a selected course's current Draft Schedule.

**Fields**: Draft identity/revision, ordered immutable current-session facts, actual scheduled units used for non-worsening comparison, existing conflict relationships, Lecturer changes, Room changes.

**State**: Either retained whole or excluded whole from a solver result.

### Temporal Candidate

**Purpose**: Represents one optional generated session before resource assignment.

**Fields**:

- Stable candidate key
- Course ID, date, integer start/end minutes, units
- Source time-window ID/index
- Feasible Lecturer IDs and Room IDs

**Uniqueness**: `(course_id, date, start_minutes, end_minutes, units)` after canonical deduplication; source window tie is retained by the lowest canonical window key.

**Rules**:

- Not on an unavailable date.
- Within planning period/semester and an allowed window.
- At least one feasible Lecturer and Room.
- Does not overlap unselected fixed occupancy for its Cohort; resource choices overlapping fixed occupancy are removed.

### Solver Arrangement

**Purpose**: One proven selected combination of retained drafts and generated sessions.

**Fields**:

- Per-course retained/generated selection
- Temporal and resource assignments
- `total_scheduled_units`
- `conflict_relationship_count`
- `lecturer_change_count`
- `room_change_count`
- `preserved_draft_count`
- `stable_rank_cost`
- Solver status and elapsed time per stage

**Lexicographic order**:

1. Maximize total scheduled units.
2. Minimize distinct `(session pair, Lecturer|Room|Cohort)` conflicts.
3. Minimize course-local adjacent Lecturer changes summed across courses.
4. Minimize course-local adjacent Room changes summed across courses.
5. Maximize current Draft Schedules retained completely unchanged.
6. Minimize canonical stable rank.

### Blocking Reason

**Purpose**: Explains substantiated categories encountered while units remain.

**Fields**: `code`, planner-readable `message`, optional related count.

**Codes**:

- `LECTURER_OCCUPIED`
- `ROOM_OCCUPIED`
- `COHORT_OCCUPIED`
- `LECTURER_UNAVAILABLE`
- `ROOM_UNAVAILABLE`
- `NO_ELIGIBLE_LECTURER`
- `NO_ELIGIBLE_ROOM`
- `INSUFFICIENT_ROOM_CAPACITY`
- `UNAVAILABLE_DATE`
- `NO_ALLOWED_DATE_OR_WINDOW`
- `COURSE_CONSTRAINT`
- `SELECTED_COURSE_COMPETITION`
- `INVALID_PLANNING_INPUT`
- `STALE_PLANNING_INPUT`

**Rule**: Reasons are evidence categories and never claim unique mathematical causation.

### Course Optimization Outcome

**Purpose**: Reports the final saved state for exactly one selected course.

**Fields**: Course identity/name, status, nullable Draft identity/revision, scheduled units, remaining units, saved flag, improvement facts, reasons/errors.

**Status enum**:

- `complete`: saved or retained state has zero remaining units and is the accepted course result.
- `improved_partial`: saved result improves the course but still has remaining units.
- `unchanged`: no allowed improvement; current/no-draft state remains.
- `failed`: invalid input, unproven optimization, validation, or persistence failure prevents an accepted course result.
- `stale`: material input changed; current state is preserved and fresh preparation is required.

### Optimization Summary

**Purpose**: Provides one result count and elapsed-time overview.

**Fields**: Total courses, counts for all five statuses, scheduled units, remaining units, elapsed milliseconds, and `optimal_for_prepared_snapshot`. A stale mixed result does not assert global optimality for refreshed final state.

## Lifecycle and State Transitions

```text
selection
  -> prepared
  -> confirmation cancelled -> no changes
  -> confirmed
  -> input stale before solve -> stale outcomes, no affected writes
  -> solving
      -> optimum not proven -> operation failure, no writes
      -> proven arrangement
  -> exact-result revalidation
      -> stale/invalid courses preserved
      -> unaffected exact results remain eligible
  -> per-course atomic saves
  -> committed saved-state outcomes
  -> semester overview/alerts refreshed
```

No operation state is persisted. Retrying always starts with a fresh preparation.
