# Phase 1 Data Model: FS-012 Conflict-Aware Exam Scheduling

## Persistence Decision

FS-012 adds two revisioned tables and migration `0006_conflict_aware_exam_scheduling.py`. Teaching `DraftSchedule` and `DraftSession` rows remain unchanged. Configuration history is not stored as a third table: each `ExamSession` preserves the defining configuration values under which that occurrence was saved.

## Persisted Entity: CourseExamConfiguration

Represents the planner-controlled current configuration for the next exam in one course-semester.

| Field | Meaning | Rules |
|---|---|---|
| `id` | Stable configuration aggregate identity | Positive generated integer primary key |
| `course_id` | Course being configured | Required FK to `courses`; part of unique course-semester identity |
| `semester_id` | Semester planning context | Required FK to `semesters`; part of unique course-semester identity |
| `enabled` | Whether the next exam is explicitly required | Required boolean; disabled rows produce no generated exam or missing-exam warning |
| `identifier` | Planner-visible exam label | Trimmed 1–200 characters when enabled |
| `duration_minutes` | Fixed elapsed exam duration | Positive integer when enabled |
| `recommended_start_override` | Optional planner-authored soft-window start | Nullable date; both override dates are absent or both present |
| `recommended_end_override` | Optional planner-authored soft-window end | Nullable date; not before override start |
| `required_capacity` | Minimum room capacity for this exam | Positive whole number when enabled; independent of cohort size |
| `exam_type` | Planner-entered exam type | Trimmed free text, 1–200 characters when enabled |
| `responsible_lecturer_id` | Configured lecturer | Required FK to an active lecturer eligible for the course when enabled |
| `configuration_consumed` | Whether the current values have already produced an exam occurrence | Required boolean; false for a fresh/unscheduled configuration, true after a generated or manual session is saved |
| `revision` | Optimistic concurrency token | Positive integer; increments on successful configuration or lifecycle mutation |

Database invariants:

- Unique constraint on `(course_id, semester_id)`.
- Positive checks for non-null `duration_minutes`, `required_capacity`, and `revision`.
- Paired override-date check: both nullable or both non-null, with end not before start.
- Foreign keys protect referenced course, semester, and responsible lecturer according to existing catalog deletion/inactivation rules.
- Mapper versioning uses `revision`, following existing course/resource/holiday aggregates.

Service validation:

- Enabling requires all planner-entered configuration values but does not require a final saved teaching-session anchor. Without that anchor, the configuration remains enabled and unscheduled, its effective recommendation dates are null, and generation/manual creation are ineligible with `FINAL_TEACHING_SESSION_MISSING`.
- The free-text type and identifier are trimmed and must not be blank.
- Recommendation overrides are validated only as a paired, internally ordered date range. They may lie partly or wholly before the final teaching anchor because they remain a soft preference; generation can use only the portion satisfying the hard final-teaching boundary and may place outside the recommendation.
- The responsible lecturer must be current, active, and course-eligible.
- An active exam makes its consumed current configuration read-only and blocks enabling, editing, disabling, replacing, or freshening a configuration for another active exam.
- Disabled configuration values are ignored by generation. They may be retained for planner convenience only when no active exam blocks disabling.
- Saving a fresh next configuration after the previous exam is past replaces the current values, sets `configuration_consumed=false`, and does not alter past sessions. Edits are allowed only while no active exam exists.
- Saving an exam session from the configuration sets `configuration_consumed=true`.
- Deleting the active exam created from the current configuration returns it to enabled/unscheduled (`configuration_consumed=false`). Deleting a past exam does not mutate the current configuration.

## Persisted Entity: ExamSession

Represents one generated or manually created exam occurrence. Unlimited past rows may exist for a course-semester; at most one row may be active by the institution-local date rule.

### Identity and live assignment

| Field | Meaning | Rules |
|---|---|---|
| `id` | Stable exam identity | Positive generated integer primary key |
| `course_id` | Course identity | Required FK to `courses`; indexed with semester/date |
| `semester_id` | Semester identity | Required FK to `semesters` |
| `cohort_id` | Cohort whose conflicts are blocked | Required FK to `cohorts` |
| `lecturer_id` | Actual responsible lecturer for this saved occurrence | Required FK to `lecturers`; must be active/eligible for new or corrected placement |
| `room_id` | Actual assigned room | Required FK to `rooms`; must be active/eligible/capacity-sufficient for new or corrected placement |
| `exam_date` | Institution-local calendar date | Required valid date inside semester and not before the final teaching boundary |
| `start_time` | Inclusive interval start | Required local time |
| `end_time` | Exclusive interval end | Required local time; recomputed from start plus snapshotted duration; later than start; no cross-midnight |
| `source` | How the occurrence was created | `generated` or `manual`; later edits do not change provenance |
| `revision` | Optimistic concurrency token | Positive integer; increments on successful correction |

### Preserved configuration and context snapshot

| Field | Meaning | Rules |
|---|---|---|
| `configuration_identifier` | Label saved for this occurrence | Required trimmed text |
| `configuration_revision` | Current configuration revision observed at creation | Positive integer evidence; does not join past reads to mutable values |
| `duration_minutes` | Duration saved for this occurrence | Positive; correction retains it and recomputes `end_time` |
| `exam_type` | Free-text type saved for this occurrence | Required trimmed 1–200 characters |
| `required_capacity` | Capacity requirement used for validation | Positive integer |
| `recommended_start_date` | Effective recommendation observed at save | Required date after resolving default or override |
| `recommended_end_date` | Effective recommendation observed at save | Required date not before recommendation start |
| `recommendation_was_overridden` | Whether planner-authored override dates supplied the recommendation | Required boolean |
| `final_teaching_date` | Final teaching anchor observed at save | Required date |
| `final_teaching_end_time` | End of the final teaching session observed at save | Required time |
| `final_teaching_session_id_snapshot` | Identity of the final teaching session observed at save | Required positive integer snapshot; intentionally not a foreign key so later teaching deletion cannot erase exam history |
| `course_name_snapshot` | Planner-readable course context | Required non-empty text |
| `semester_name_snapshot` | Planner-readable semester context | Required non-empty text |
| `cohort_name_snapshot` | Planner-readable cohort context | Required non-empty text |
| `lecturer_name_snapshot` | Responsible lecturer name at save | Required non-empty text |
| `lecturer_reference_snapshot` | Responsible lecturer code at save | Required non-empty text |
| `room_name_snapshot` | Assigned room name at save | Required non-empty text |
| `room_reference_snapshot` | Assigned room code at save | Required non-empty text |

Database invariants and indexes:

- Positive checks for duration, capacity, and revision.
- `end_time > start_time` check prevents zero/negative same-day intervals.
- Source check limits provenance values.
- Index `(course_id, semester_id, exam_date)` supports lifecycle and history queries.
- Indexes on `(semester_id, exam_date, lecturer_id)`, room, and cohort support conflict loads.
- No static unique constraint attempts to encode active status because `today` moves.

Mutation rules:

- Generated/manual insert and correction to today/future run under the serialized semester write boundary and recheck that no other active exam exists for the course-semester.
- All new/corrected placements use half-open `[start,end)` intervals; back-to-back occupancy is valid.
- Manual placement outside the recommendation is allowed and does not change configuration.
- Corrections may change date, start, actual lecturer, and room; duration and saved configuration context remain unless the past exam itself is deliberately corrected under the approved manual workflow.
- Correcting a past exam onto today/future is allowed only when no other active exam exists.
- Active and past deletion remove only the selected row after revision/snapshot validation. Past deletion leaves current configuration unchanged.

## Derived Values

### Institution Today

`institution_today` is the current date in `INSTITUTION_TIMEZONE`, default `Europe/Vienna`, derived through a central injectable clock. It is included in relevant preparation/snapshot evidence.

### Exam Lifecycle Status

```text
exam_date >= institution_today -> active
exam_date <  institution_today -> past
```

The status is returned by the backend and never derived independently by the browser.

### Final Teaching Anchor

The maximum `(date, end_time)` among saved teaching `DraftSession` rows for the same course-semester. No anchor means the configuration may remain explicitly enabled but has no derived effective recommendation and cannot be placed; generation/manual creation returns `FINAL_TEACHING_SESSION_MISSING`.

### Effective Recommended Window

- If both planner overrides and a final teaching anchor are present, use those dates after applying configuration validation against the anchor.
- If a final teaching anchor is present and overrides are absent, use `final_teaching_date + 7 days` through `final_teaching_date + 14 days`, inclusive.
- If the final teaching anchor is absent, both effective recommendation dates are null even when planner overrides are retained; placement remains ineligible until the anchor exists.
- The window is a soft automatic-generation preference.
- `outsideRecommendedWindow` is true when an exam date is outside the effective saved window; it is not a validity issue.

### Current Exam Validity Issue

Derived on reads, not persisted. Each issue contains `code`, `message`, and optional structured date/resource evidence.

Codes:

- `FINAL_TEACHING_SESSION_MISSING`
- `BEFORE_FINAL_TEACHING`
- `OUTSIDE_SEMESTER`
- `RESPONSIBLE_LECTURER_INELIGIBLE`
- `ROOM_INELIGIBLE`
- `INSUFFICIENT_ROOM_CAPACITY`
- `LECTURER_UNAVAILABLE`
- `ROOM_UNAVAILABLE`
- `INSTITUTION_HOLIDAY`
- `LECTURER_OCCUPIED`
- `ROOM_OCCUPIED`
- `COHORT_OCCUPIED`
- `DUPLICATE_ACTIVE_EXAM`
- `INVALID_EXAM_INTERVAL`
- `VALIDATION_CONTEXT_UNAVAILABLE`
- `AUTOMATIC_START_TIME_UNAVAILABLE` (generation failure only; not a saved-exam validity issue)

Named holiday evidence carries both date and current holiday name. Overlap evidence identifies the related teaching or exam session without exposing unrelated mutable objects.

## Existing Entities Used Without Redesign

### Course, Semester, Cohort

- Supply course-semester identity, semester bounds, cohort conflict identity, names, active state, and revisions.
- Catalog deletion/inactivation checks must treat ExamSession references as schedule history requiring preservation.

### Lecturer and Room

- Configuration/manual choices come from current active course-eligible resources.
- Room capacity is compared to `required_capacity`, not cohort size.
- Recurring and dated `ResourceUnavailabilityPeriod` rows use existing half-open overlap semantics.
- Resource removal behavior must preserve referenced exam sessions and identify affected current configurations/courses.

### DraftSession

- Supplies the final teaching anchor and fixed lecturer/room/cohort occupancy.
- Exam scheduling never moves, replaces, resizes, or deletes DraftSession rows.

### InstitutionHoliday

- Current full dates are hard exclusions.
- Holiday snapshots participate in stale detection; changes do not mutate existing exams.

### StudyTypeTimeWindow

- Every applicable active window start time forms the finite automatic exam start-time proposal set.
- They are not persisted into ExamSession as a hard rule and do not block manual placement at other times.
- If no applicable active window exists, generation returns `AUTOMATIC_START_TIME_UNAVAILABLE` rather than claiming that a hard resource conflict prevented placement.

## Transient Generation Entities

### Exam Generation Preparation

| Field | Meaning |
|---|---|
| `semester_id` | Selected semester |
| `institution_today` | Date used for lifecycle classification |
| `shared_snapshot_token` | Opaque digest of semester bounds/revision, fixed teaching/exam occupancy, holidays, and clock date |
| `courses` | Ordered per-course preparation records |

Each per-course record contains course/configuration identities and revisions, eligibility status, active exam identity if any, final teaching anchor, and an opaque input snapshot token covering configuration, course/cohort, lecturer, eligible rooms, availability, and relevant occupancy.

### Exam Candidate

| Field | Meaning |
|---|---|
| stable key | Canonical course/date/time/room ordering key |
| course/configuration identity | Selected next exam |
| date/start/end | Proposed fixed-duration interval |
| lecturer/cohort | Fixed conflict resources |
| room | One eligible active capacity-sufficient choice |
| inside recommendation | Soft-objective flag |

Candidate rules:

- Date lies after the final teaching boundary and inside the semester.
- Start time is one of the applicable active Study Type Time Window start proposals; absence of all such proposals produces `AUTOMATIC_START_TIME_UNAVAILABLE`.
- End is same day and inside semester.
- Date is not a current holiday.
- Lecturer and room are available for the full interval.
- Candidate does not conflict with fixed teaching/exam occupancy.

### Exam Generation Outcome

Status values:

- `scheduled`: one valid exam was saved.
- `failed`: no valid candidate or invalid input; no exam saved; all substantiated reasons returned.
- `stale`: material input changed; no affected exam saved; fresh preparation required.
- `skipped_active`: an active exam already exists and remains unchanged.
- `skipped_disabled`: the course is not explicitly enabled and receives no missing-exam failure.

No preparation, solver variable, failure outcome, or validity issue is persisted.

## Lifecycle and State Transitions

```text
absent/disabled configuration
  -> valid enable/save -> enabled + fresh unscheduled configuration
      -> no final teaching anchor -> retained but ineligible; effective recommendation unavailable
  -> generate/manual create -> one active ExamSession + configuration consumed
      -> consumed active configuration -> read-only until active exam is past or deleted
  -> active date becomes past -> retained past ExamSession + consumed configuration
  -> prepare/save next -> fresh unscheduled configuration; past sessions unchanged

active ExamSession
  -> valid correction -> corrected active/past row, revision incremented
  -> confirmed delete -> row removed; current configuration enabled + unscheduled
  -> related input changes -> row preserved; current validity issues derived

past ExamSession
  -> valid correction -> corrected row; may become active only if active slot free
  -> confirmed delete -> selected history row removed; current configuration unchanged
```

Generation lifecycle:

```text
selection -> preparation + snapshot tokens
  -> generation request echoes preparation
  -> solve deterministic joint arrangement
  -> serialized write boundary
  -> snapshot and exact-result revalidation
      -> unchanged input -> save valid scheduled outcomes
      -> changed input -> stale affected outcomes
  -> return mixed scheduled/failed/stale/skipped results
  -> client refreshes combined teaching/exam review
```
