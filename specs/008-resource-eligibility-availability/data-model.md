# Data Model: FS-008 Resource Eligibility and Availability

## Conventions

- Integer identifiers remain stable and are never reused.
- Planner-visible JSON uses camelCase; storage names below use snake_case.
- Local dates and times follow the existing institution-local scheduling convention. No timezone conversion or positive availability override is introduced.
- Availability and session intervals are half-open: `[start, end)`. Touching boundaries do not overlap.
- Mutable aggregate roots carry a positive integer `revision`. A successful mutation increments the relevant revision; stale expected revisions fail without mutation.
- Display names may repeat. Reference codes are trimmed, case-folded for comparison, and unique within the Lecturer catalog and within the Room catalog.

## Entity: Lecturer

Represents a planner-maintained teaching resource.

| Field | Meaning |
|---|---|
| `id` | Stable identity |
| `name` | Non-empty display name, maximum 200 characters |
| `reference_code` | Non-empty planner-maintained code shown with the name |
| `normalized_reference_code` | Trimmed, case-folded code; unique among Lecturers |
| `is_active` | Whether the Lecturer may be added to eligibility or assigned anew |
| `revision` | Optimistic concurrency token |

Relationships:

- Has zero or more CourseEligibleLecturer relationships.
- Owns zero or more ResourceUnavailabilityPeriods.
- May be referenced by any number of DraftSessions.

Lifecycle:

```text
Active --retirement with active-course/session usage--> Inactive
Active --retirement without protected usage---------> Deleted
Inactive --valid reactivation------------------------> Active
Inactive --retirement without protected usage-------> Deleted
```

Deletion removes eligibility links belonging only to inactive Courses and owned unavailability only when no active-Course eligibility and no DraftSession reference exists. Inactivation preserves every relationship and assignment.

## Entity: Room

Represents a planner-maintained scheduling location.

| Field | Meaning |
|---|---|
| `id` | Stable identity |
| `name` | Non-empty display name, maximum 200 characters |
| `reference_code` | Non-empty planner-maintained code shown with the name |
| `normalized_reference_code` | Trimmed, case-folded code; unique among Rooms |
| `capacity` | Positive whole-number maximum cohort size |
| `is_active` | Whether the Room may be added to eligibility or assigned anew |
| `revision` | Optimistic concurrency token |

Relationships and lifecycle match Lecturer, using CourseEligibleRoom and Room DraftSession assignments.

Capacity behavior:

- A Room cannot be newly added to a Course whose current Cohort size exceeds capacity.
- Reducing Room capacity preserves existing eligibility but makes affected relationships unusable.
- Increasing Cohort size removes newly insufficient Room eligibility relationships atomically.
- Existing DraftSession assignments are never changed by capacity updates.

## Entity: CourseEligibleLecturer

Represents one distinct Lecturer the planner permits for a Course.

| Field | Meaning |
|---|---|
| `course_id` | Course aggregate owner; composite primary key member |
| `lecturer_id` | Eligible Lecturer; composite primary key member |

Rules:

- Duplicate `(course_id, lecturer_id)` relationships are impossible.
- The Course `revision` protects replacement of the complete Lecturer and Room eligibility sets.
- A planner-initiated replacement must retain at least one Lecturer.
- Inactive preserved relationships remain visible but are unusable until valid reactivation.
- Usability is computed from current resource state and is not stored.

## Entity: CourseEligibleRoom

Represents one distinct Room the planner permits for a Course.

| Field | Meaning |
|---|---|
| `course_id` | Course aggregate owner; composite primary key member |
| `room_id` | Eligible Room; composite primary key member |

Rules:

- Duplicate `(course_id, room_id)` relationships are impossible.
- A planner-initiated replacement must retain at least one Room and cannot newly add an inactive or capacity-insufficient Room.
- Existing relationships made insufficient by Room capacity reduction remain visible and unusable.
- Cohort growth deletes newly insufficient relationships and increments every affected Course revision.

## Entity: ResourceUnavailabilityPeriod

Represents one recurring weekly or dated interval during which exactly one Lecturer or Room is unavailable.

| Field | Meaning |
|---|---|
| `id` | Stable period identity |
| `lecturer_id` | Lecturer owner, nullable |
| `room_id` | Room owner, nullable |
| `kind` | `recurring` or `dated` |
| `start_date` | Dated start date; null for recurring |
| `end_date` | Dated end date; null for recurring |
| `start_time` | Inclusive local start time |
| `end_time` | Exclusive local end time |
| `revision` | Optimistic concurrency token for this period |

Owner invariant:

- Exactly one of `lecturer_id` and `room_id` is present.

Kind invariants:

- `recurring`: dates are absent, end time is later than start time, and at least one ResourceUnavailabilityWeekday exists.
- `dated`: start/end dates are present, no weekday children exist, and the combined local end date/time is later than the combined start date/time.
- A recurring rule never crosses midnight; use a dated period or two recurring rules for that case.

Duplicate rules:

- A recurring duplicate has the same owner, weekday set, start time, and end time.
- A dated duplicate has the same owner and start/end local date/time.
- Exact duplicates are rejected; partial overlaps remain separate records and evaluate as their union.

## Entity: ResourceUnavailabilityWeekday

Stores a selected weekday for one recurring unavailability period.

| Field | Meaning |
|---|---|
| `period_id` | Parent recurring period; composite primary key member |
| `weekday` | Integer `0` through `6`, Monday through Sunday; composite primary key member |

Deleting a period deletes its weekday children. A dated period cannot own weekday rows.

## Modified Entity: Course

FS-007 fields and relationships remain except for scalar `lecturer_id` and `room_id`, which are replaced by the eligibility junctions.

Resource-related state:

- Owns one or more CourseEligibleLecturer rows for normal planner-initiated updates.
- Owns one or more CourseEligibleRoom rows for normal planner-initiated updates.
- Uses its existing `revision` as the aggregate concurrency token for atomic replacement of both sets.
- Has fixed, derived preference semantics: minimize Lecturer changes and minimize Room changes inside one Course-Semester DraftSchedule. These booleans are contract metadata, not stored settings.

Generation readiness adds these reasons to existing FS-007 reasons:

| Reason | Condition |
|---|---|
| `NO_ACTIVE_ELIGIBLE_LECTURER` | No eligibility relationship points to an active Lecturer |
| `NO_USABLE_ELIGIBLE_ROOM` | No active eligible Room currently satisfies Cohort capacity |

A Course remains visible when either reason applies but is unavailable for new generation.

## Existing Entity: DraftSession

DraftSession remains the concrete resource assignment.

| Existing field | FS-008 rule |
|---|---|
| `lecturer_id` | Required; exactly one Lecturer assignment |
| `room_id` | Required; exactly one Room assignment |

Rules:

- Migration never rewrites these fields.
- New generated assignments must reference active eligible resources, satisfy Room capacity, and avoid current resource unavailability.
- An existing assignment remains readable after eligibility, lifecycle, availability, or capacity changes.
- Validation may attach all applicable resource alerts without mutating the session.
- A session edit that changes a resource must choose an active eligible resource. An unrelated edit may retain an unchanged invalid legacy assignment.

## Derived Model: CourseResourceConfiguration

Returned for Course eligibility administration; not stored as a separate record.

| Field | Meaning |
|---|---|
| `course_id` | Course identity |
| `course_revision` | Expected revision for atomic replacement |
| `cohort_size` | Current capacity requirement |
| `eligible_lecturers` | Current relationships with active/usability state |
| `eligible_rooms` | Current relationships with capacity/usability state |
| `lecturer_candidates` | Active and preserved Lecturer choices visible to the planner |
| `room_candidates` | Active and preserved Room choices with capacity and reasons |
| `preferences` | Fixed `minimizeLecturerChanges=true`, `minimizeRoomChanges=true` |

Replacement validates both submitted ID sets and either commits all changes plus one Course revision increment or commits none.

## Derived Model: ResourceUsageAssessment

Computed immediately before confirmation and rechecked inside retirement.

| Field | Meaning |
|---|---|
| `resource_id` | Lecturer or Room identity |
| `resource_revision` | Expected retirement revision |
| `disposition` | `delete` or `inactivate` based on current usage |
| `active_courses` | Active Course identities and names using the resource |
| `inactive_courses` | Inactive Course relationships that deletion would remove |
| `draft_session_count` | Total protected DraftSession assignments |
| `draft_schedule_count` | Distinct affected DraftSchedules |

The mutation response reports the actual transactional disposition rather than relying on the preflight value.

## Derived Model: CohortCapacityImpact

Returned after a successful Cohort size increase.

| Field | Meaning |
|---|---|
| `removed_relationships` | Course and Room identities automatically disconnected |
| `courses_without_rooms` | Courses left with no eligible Room relationship |
| `affected_course_revisions` | New revisions after automatic cleanup |

No DraftSession is updated or deleted.

## Validation Alerts

FS-008 adds these independently applicable codes:

| Code | Trigger |
|---|---|
| `LECTURER_INELIGIBLE` | Assigned Lecturer is outside the current Course eligibility set or inactive |
| `ROOM_INELIGIBLE` | Assigned Room is outside the current Course eligibility set or inactive |
| `LECTURER_UNAVAILABLE` | Session positively overlaps applicable Lecturer unavailability |
| `ROOM_UNAVAILABLE` | Session positively overlaps applicable Room unavailability |

Existing `ROOM_CAPACITY` remains and uses current Room capacity and current Cohort size for current validation. Other FS-005 alerts remain unchanged.

## Course-Local Assignment

For each temporally placed session:

1. Build active eligible Lecturer candidates not unavailable during the full session.
2. Build active eligible Room candidates not unavailable during the full session and with capacity at least the current Cohort size.
3. If either set is empty, reject that temporal candidate and continue existing course-local placement search.
4. Across the completed Course DraftSchedule, minimize Lecturer transitions and Room transitions independently.
5. Break equal-cost choices by normalized reference code and then stable ID.

No candidate scoring uses another Course, persisted rank, planner weight, quota, or global completion objective.

## Migration 0004

Upgrade from the recognized FS-007 schema:

1. Add Lecturer/Room code, normalization, active, and revision fields.
2. Backfill collision-free editable codes `LECT-<id>` and `ROOM-<id>`.
3. Create eligibility junctions and backfill one Lecturer and Room relationship from every Course scalar assignment.
4. Create ResourceUnavailabilityPeriod and ResourceUnavailabilityWeekday structures.
5. Refactor application contracts and services to use eligibility sets.
6. Remove scalar Course lecturer/room foreign keys without changing DraftSession assignments.
7. Verify current schema shape and foreign-key integrity.

Clean databases are created directly at the current model shape. Existing databases migrate before current metadata creation so migration-owned tables are not pre-created accidentally.

