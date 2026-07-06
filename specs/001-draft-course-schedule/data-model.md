# Data Model: Draft Course Schedule

## Entity: Course

Represents the teaching offering to be scheduled.

Fields:

- `id`: stable identifier
- `name`: display name
- `total_units`: positive integer count of 45-minute teaching units
- `min_session_units`: positive integer lecturer preference lower bound
- `max_session_units`: positive integer lecturer preference upper bound
- `lecturer_id`: assigned Lecturer identifier
- `cohort_id`: assigned Cohort identifier
- `room_id`: assigned Room identifier
- `study_type_id`: assigned Study Type identifier

Validation rules:

- `total_units` must be greater than 0.
- `min_session_units` must be greater than 0.
- `max_session_units` must be greater than or equal to `min_session_units`.
- First feature supports one lecturer, one Cohort, one room, and one study type per course.

## Entity: Lecturer

Represents the person teaching the course for this first slice.

Fields:

- `id`: stable identifier
- `name`: display name

Validation rules:

- A generated draft schedule must reference exactly one lecturer.

## Entity: Cohort

Represents the fixed student group attending the course.

Fields:

- `id`: stable identifier
- `name`: display name
- `student_count`: non-negative integer

Validation rules:

- `student_count` must be less than or equal to the assigned room capacity for generation to succeed.

## Entity: Room

Represents the assigned teaching location.

Fields:

- `id`: stable identifier
- `name`: display name
- `capacity`: non-negative integer

Validation rules:

- `capacity` must be greater than or equal to the Cohort student count.
- Capacity violation is a hard generation failure.

## Entity: Semester

Represents the date range in which generated sessions must occur.

Fields:

- `id`: stable identifier
- `name`: display name
- `start_date`: inclusive calendar date
- `end_date`: inclusive calendar date

Validation rules:

- `start_date` must be on or before `end_date`.
- All generated sessions must occur within the date range.

## Entity: Study Type

Represents the study organization category whose time plan constrains teaching sessions.

Fields:

- `id`: stable identifier
- `name`: display name

Relationships:

- Has one or more Study Type Time Windows.

## Entity: Study Type Time Window

Represents an allowed weekday/time interval for a study type.

Fields:

- `id`: stable identifier
- `study_type_id`: owning Study Type identifier
- `weekday`: day of week
- `start_time`: local start time
- `end_time`: local end time
- `sort_order`: configured order for display and selection

Validation rules:

- `start_time` must be before `end_time`.
- Windows are local-time intervals and do not cross midnight in this feature.
- A generation request must include one selected Study Type Time Window as the preferred recurring slot.

## Entity: Draft Schedule

Represents the current generated draft for one course.

Fields:

- `id`: stable identifier
- `course_id`: owning Course identifier
- `semester_id`: Semester identifier used for generation
- `selected_time_window_id`: preferred Study Type Time Window selected by the admin
- `status`: `generated`
- `created_at`: creation timestamp

Lifecycle:

- Successful generation replaces any existing generated Draft Schedule and Draft Sessions for the same course.
- Failed generation creates no Draft Schedule and no Draft Sessions.

## Entity: Draft Session

Represents one generated teaching block.

Fields:

- `id`: stable identifier
- `draft_schedule_id`: owning Draft Schedule identifier
- `course_id`: Course identifier
- `lecturer_id`: Lecturer identifier
- `cohort_id`: Cohort identifier
- `room_id`: Room identifier
- `date`: session date
- `start_time`: local start time
- `end_time`: local end time
- `units`: number of teaching units in the session
- `time_window_id`: Study Type Time Window used for this placement

Validation rules:

- `units` must be within the course's preferred minimum and maximum session units.
- Session duration is `units * 45 minutes + (units - 1) * 10 minutes`.
- Session must start and end inside its Study Type Time Window.
- At most one generated session for the course may occur on the same date.
- All generated sessions for a successful draft must sum to the course `total_units`.

## Scheduling State Transitions

```text
No current draft
  -> generation succeeds
  -> Draft Schedule generated

Draft Schedule generated
  -> generation succeeds again
  -> Previous draft sessions replaced by new Draft Schedule

No current draft or Draft Schedule generated
  -> generation fails
  -> No new draft sessions created
```

## Failure Reasons

The generation result may include multiple detected failure reasons:

- `INSUFFICIENT_ROOM_CAPACITY`
- `INVALID_SESSION_PREFERENCE`
- `NO_FITTING_TIME_WINDOW`
- `INSUFFICIENT_SEMESTER_CAPACITY`
