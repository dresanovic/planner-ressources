# Data Model: Conflict Detection

## Draft Session

A generated teaching block evaluated for validation alerts.

### Existing Fields Used

- `id`: Stable Draft Session identifier used in alert references.
- `draft_schedule_id`: Parent Draft Schedule.
- `course_id`: Course context used to identify cross-course conflicts.
- `lecturer_id`: Lecturer context used for lecturer overlap detection.
- `cohort_id`: Cohort context used for Cohort overlap detection and capacity needs.
- `room_id`: Room assignment used for room overlap and capacity detection.
- `date`: Session date used for overlap and window checks.
- `start_time`: Session start time used for overlap and window checks.
- `end_time`: Session end time used for overlap and window checks.
- `units`: Existing teaching-unit coverage metadata; not used to create alerts in Slice 5.
- `time_window_id`: Generation traceability; may support reference context but is not the authoritative current-window rule.
- `constraint_window_index`: Generation traceability; not authoritative for current generation-constraint validation.

### Additive Response Shape

Each Draft Session response gains:

- `validationAlerts`: list of validation alerts associated with this session.

### Validation Rules

- Sessions are compared only within the selected semester.
- Sessions overlap when they share a date and their time ranges intersect with positive duration.
- Sessions where one ends exactly when the other starts are not overlapping.
- A session may have zero, one, or multiple alerts.
- Alerts are non-blocking and do not change Draft Session persistence rules.

## Validation Alert

A non-blocking issue associated with a Draft Session.

### Fields

- `code`: Machine-readable alert category.
- `message`: Readable summary for office staff.
- `relatedSessions`: list of related conflicting sessions for overlap alerts.

### Alert Codes

- `LECTURER_OVERLAP`: Another session in the selected semester uses the same lecturer at an overlapping date/time.
- `ROOM_OVERLAP`: Another session in the selected semester uses the same room at an overlapping date/time.
- `COHORT_OVERLAP`: Another session in the selected semester uses the same Cohort at an overlapping date/time.
- `ROOM_CAPACITY`: The assigned room capacity is below the session Cohort size.
- `GENERATION_CONSTRAINT_VIOLATION`: The session is outside the currently active course-semester generation constraints.
- `STUDY_TYPE_WINDOW_VIOLATION`: The session is outside the Study Type Time Window.
- `VALIDATION_DATA_MISSING`: Required reference data is missing, so the session cannot be fully evaluated.

### Rules

- Overlap alerts must identify every related conflicting session available in the selected semester.
- Capacity and window alerts may have an empty `relatedSessions` list because they describe a single-session violation.
- Missing reference data must produce `VALIDATION_DATA_MISSING` instead of silently treating a session as valid.

## Related Session

Readable context for a session involved in an overlap alert.

### Fields

- `sessionId`
- `draftScheduleId`
- `courseId`
- `courseName`
- `date`
- `startTime`
- `endTime`
- `cohortName`
- `lecturerName`
- `roomName`

### Rules

- Related session references are limited to sessions available in the selected semester.
- The affected session itself must not appear as its own related session.

## Draft Schedule

The generated schedule containing evaluated Draft Sessions.

### Existing Fields Used

- `id`
- `course_id`
- `semester_id`
- `status`
- `sessions`
- `course`

### Rules

- Draft Schedule persistence does not change.
- Returning a Draft Schedule after generation or edit save should include sessions with current validation alerts.
- Regeneration replacement removes prior sessions from future validation results.

## Courses Overview

The selected-semester review surface that displays generated Draft Sessions and validation alerts.

### Rules

- Alerts are displayed with the sessions they affect.
- Filters do not remove alert association from visible affected sessions.
- List and weekly modes show the same alert state for the same sessions.

## Room

The teaching location assigned to a Draft Session.

### Existing Fields Used

- `id`
- `name`
- `capacity`

### Rules

- Room overlap checks compare `room_id`.
- Capacity checks compare `capacity` to the session Cohort `student_count`.

## Cohort

The student group associated with a Draft Session.

### Existing Fields Used

- `id`
- `name`
- `student_count`

### Rules

- Cohort overlap checks compare `cohort_id`.
- Capacity checks use `student_count`.

## Lecturer

The teacher assigned to a Draft Session.

### Existing Fields Used

- `id`
- `name`

### Rules

- Lecturer overlap checks compare `lecturer_id`.

## Generation Constraint

The currently active course-semester planning period and weekly allowed teaching windows.

### Existing Fields Used

- `course_id`
- `semester_id`
- `planning_start_date`
- `planning_end_date`
- `weekday`
- `start_time`
- `end_time`

### Rules

- A session violates generation constraints when its date is outside the active planning period or its weekday/time range is not contained by any active allowed teaching window for its course and semester.
- If no custom constraints exist, default semester dates and Study Type Time Windows are the active generation constraints.

## Study Type Time Window

The standard teaching availability window for a course's Study Type.

### Existing Fields Used

- `study_type_id`
- `weekday`
- `start_time`
- `end_time`
- `sort_order`

### Rules

- A session violates Study Type Time Windows when no custom active generation constraints exist and its weekday/time range is not contained by any Study Type Time Window for the related course study type.
