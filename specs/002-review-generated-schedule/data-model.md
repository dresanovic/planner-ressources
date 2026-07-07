# Data Model: Review Generated Schedule In Planner UI

## Draft Schedule

Represents the current generated schedule for one selected course.

Fields used by this feature:

- `draftScheduleId`: Unique draft schedule identifier.
- `courseId`: Selected course identifier.
- `semesterId`: Semester identifier for the generated schedule.
- `selectedTimeWindowId`: Study Type Time Window selected during generation.
- `context`: Human-readable planning context for the selected course.
- `sessions`: Chronological list of generated Draft Sessions.

Relationships:

- Belongs to one Course.
- Contains many Draft Sessions.
- References one Semester.
- References one selected Study Type Time Window.

Validation rules:

- At most one current Draft Schedule exists for a course.
- Empty or missing schedule states must be represented clearly to the UI.

## Draft Session

Represents one generated teaching block shown in list and weekly review modes.

Fields used by this feature:

- `id`: Unique Draft Session identifier.
- `date`: Scheduled session date.
- `startTime`: Scheduled start time.
- `endTime`: Scheduled end time.
- `units`: Number of teaching units.
- `courseId`: Course identifier.
- `lecturerId`: Lecturer identifier.
- `cohortId`: Cohort identifier.
- `roomId`: Room identifier.
- `studyTypeId`: Study Type identifier.
- `timeWindowId`: Study Type Time Window identifier.

Relationships:

- Belongs to one Draft Schedule.
- References one Course, Lecturer, Cohort, Room, and Study Type through the selected course context.

Validation rules:

- Sessions display in chronological order in list mode.
- Weekly mode groups sessions by week and day without changing session data.
- This feature does not modify Draft Sessions.

## Review Context

Represents display labels for the current selected course schedule.

Fields:

- `course`: `{ id, name }`
- `cohort`: `{ id, name }`
- `lecturer`: `{ id, name }`
- `room`: `{ id, name }`
- `studyType`: `{ id, name }`

Relationships:

- Derived from the Course and its related planning records.
- Used by every visible Draft Session for display and filters.

Validation rules:

- Labels must be available for all generated sessions shown in the review view.
- Long labels must remain readable in the UI.

## Review Filter

Represents active UI selections used to narrow visible sessions.

Fields:

- `courseId`: Current selected course ID.
- `cohortId`: Optional selected Cohort ID.
- `lecturerId`: Optional selected Lecturer ID.
- `roomId`: Optional selected Room ID.
- `studyTypeId`: Optional selected Study Type ID.

Relationships:

- Applies to the current Draft Schedule's sessions.

Validation rules:

- Active filters combine using match-all behavior.
- If no sessions match active filters, the UI shows a no-results state.
- Clearing filters restores all sessions from the current selected course schedule.

## View Mode

Represents the current review presentation.

Allowed values:

- `list`
- `weekly`

Validation rules:

- Switching modes does not change generated schedule data.
- Switching modes preserves active filters.
