# Data Model: Manual Session Editing

## Draft Session

An existing generated teaching block that office staff can edit.

### Existing Fields Used

- `id`: Stable Draft Session identifier used by the edit contract.
- `draft_schedule_id`: Parent Draft Schedule.
- `course_id`: Course context copied from generation.
- `lecturer_id`: Lecturer context copied from generation; not editable in Slice 4.
- `cohort_id`: Cohort context copied from generation; used to validate replacement room capacity.
- `room_id`: Editable Room assignment.
- `date`: Editable session date.
- `start_time`: Editable start time.
- `end_time`: Editable end time; changing this adjusts derived session length.
- `units`: Existing teaching-unit coverage metadata from generation; not directly edited in Slice 4.
- `time_window_id`: Generation traceability; not changed by manual edits.
- `constraint_window_index`: Generation traceability; not changed by manual edits.

### Validation Rules

- Target Draft Session must exist.
- Edited `date` must fall within the parent Draft Schedule semester start/end dates.
- Edited `date` must not duplicate another Draft Session date in the same Draft Schedule.
- Edited `end_time` must be later than edited `start_time`.
- Edited `room_id` must refer to an existing Room.
- Replacement Room capacity must be greater than or equal to the session Cohort student count.
- Room occupancy at the edited date/time is not checked in this slice.
- Active generation constraints and teaching windows are not checked in this slice.
- Source planning records are not edited.

### State Transitions

- `generated` -> `generated with manual values`: saving a valid edit changes Draft Session fields in place.
- `generated with manual values` -> `generated with newer manual values`: saving another valid edit replaces the editable fields.
- `generated with manual values` -> `replaced by regeneration`: generating a replacement draft schedule for the same course follows existing replacement behavior and prior session records are not preserved.

## Draft Schedule

The generated schedule containing editable Draft Sessions.

### Existing Fields Used

- `id`
- `course_id`
- `semester_id`
- `status`
- `sessions`
- `course`

### Rules

- Slice 4 edits one Draft Session within a Draft Schedule.
- Returning the updated Draft Schedule after a save lets the Courses overview refresh the affected schedule.
- The existing one-generated-draft-per-course behavior remains unchanged.

## Room

The teaching location assigned to a Draft Session.

### Existing Fields Used

- `id`
- `name`
- `capacity`

### Rules

- Room choices come from existing room records.
- Capacity must be sufficient for the edited session's Cohort.
- Occupancy and overlap are deferred to Slice 5.

## Cohort

The student group associated with a Draft Session.

### Existing Fields Used

- `id`
- `name`
- `student_count`

### Rules

- `student_count` is compared with Room capacity during room edits.
- Cohort itself is not editable in Slice 4.

## Semester

The date range that scopes the Courses overview and bounds manual date edits.

### Existing Fields Used

- `id`
- `name`
- `start_date`
- `end_date`

### Rules

- Edited session dates must be within the parent Draft Schedule semester.
- Manual date edits outside the selected semester are rejected.

## Planning Options

The client-side planning metadata used by the planner page.

### Additive Response Shape

Add room options to the existing planning-options response:

- `rooms`: list of existing rooms
- each room includes `id`, `name`, and `capacity`

### Rules

- Adding room options is backward-compatible for existing clients.
- Backend edit validation remains authoritative even if the frontend filters room choices.
