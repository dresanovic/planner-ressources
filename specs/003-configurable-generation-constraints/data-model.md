# Data Model: Configurable Generation Constraints

## Entity: GenerationConstraintSet

Represents saved custom generation constraints for one course-semester combination.

**Fields**:

- `id`: unique identifier.
- `course_id`: references Course; required.
- `semester_id`: references Semester; required.
- `planning_start_date`: custom planning period start date; required for saved custom constraints.
- `planning_end_date`: custom planning period end date; required for saved custom constraints.
- `created_at`: timestamp when the saved set was first created.
- `updated_at`: timestamp when the saved set was last replaced by a successful generation.

**Relationships**:

- Belongs to one Course.
- Belongs to one Semester.
- Owns one or more GenerationConstraintWindow rows.

**Validation rules**:

- `(course_id, semester_id)` is unique.
- `planning_start_date` must be on or after the Semester start date.
- `planning_end_date` must be on or before the Semester end date.
- `planning_start_date` must be on or before `planning_end_date`.
- A set is saved only after draft schedule generation succeeds.
- A set is deleted when office staff clear custom constraints for the course-semester combination.

## Entity: GenerationConstraintWindow

Represents one saved allowed weekly teaching window within a GenerationConstraintSet.

**Fields**:

- `id`: unique identifier.
- `constraint_set_id`: references GenerationConstraintSet; required.
- `weekday`: integer weekday, where existing project convention uses Monday as `0` through Sunday as `6`.
- `start_time`: window start time; required.
- `end_time`: window end time; required.
- `sort_order`: stable display and generation order.
- `source_time_window_id`: optional reference to StudyTypeTimeWindow when the saved window originated from a study type default.

**Relationships**:

- Belongs to one GenerationConstraintSet.
- May reference one StudyTypeTimeWindow.

**Validation rules**:

- `weekday` must be between `0` and `6`.
- `start_time` must be earlier than `end_time`.
- A GenerationConstraintSet must contain at least one GenerationConstraintWindow.
- Windows are allowed to be custom and do not create or modify StudyTypeTimeWindow records.

## Entity: ActiveGenerationConstraints

Read model returned to the frontend for a selected course and semester. It may be assembled from saved custom constraints or from defaults.

**Fields**:

- `course_id`: selected course.
- `semester_id`: selected semester.
- `source`: `saved` when backed by GenerationConstraintSet, otherwise `default`.
- `planning_period.start_date`: active planning period start date.
- `planning_period.end_date`: active planning period end date.
- `allowed_teaching_windows`: ordered list of active generation windows.

**Validation rules**:

- Defaults use Semester start/end dates and the selected course study type's Study Type Time Windows.
- Saved constraints take precedence over defaults for the same course-semester combination.
- If no saved set exists and the study type has no default windows, the active window list is empty and generation is blocked until office staff add at least one window.

## Value Object: GenerationWindowInput

One allowed weekly teaching window submitted with a generation request.

**Fields**:

- `weekday`: integer Monday `0` through Sunday `6`.
- `start_time`: `HH:MM` local time string.
- `end_time`: `HH:MM` local time string.
- `source_time_window_id`: optional StudyTypeTimeWindow ID when the window came from defaults.

**Validation rules**:

- `weekday` must be `0` through `6`.
- `start_time` must be earlier than `end_time`.
- The submitted request must contain at least one GenerationWindowInput.
- Source IDs are optional because custom windows do not belong to the global study type catalog.

## Entity Changes: DraftSchedule

Current DraftSchedule continues to represent the generated schedule for one course.

**Changes**:

- Keep `course_id` and `semester_id`.
- Replace the single selected-window concept in the generation flow with the active planning period and list of allowed teaching windows.
- Use DraftSession-level `time_window_id` and `constraint_window_index` traceability; DraftSchedule does not need a separate saved constraint reference or generation snapshot in this slice.

**Validation rules**:

- A successful generation replaces the previous draft schedule for the course, as established by Slice 1.
- Draft Sessions are created only when the full course can be scheduled within the active constraints.

## Entity Changes: DraftSession

DraftSession remains the generated teaching block shown in the review UI.

**Changes**:

- Keep concrete `date`, `start_time`, `end_time`, and `units`.
- Keep `time_window_id` only as optional source traceability for sessions generated from a StudyTypeTimeWindow.
- Add a stable `constraint_window_index` or equivalent traceability field so sessions generated from custom windows can be linked back to the generation input order.

**Validation rules**:

- `date` must be within the active planning period.
- `start_time` and `end_time` must fit inside one active allowed teaching window for the session date's weekday.
- At most one generated Draft Session for the course may occur on the same date, preserving Slice 1 behavior.

## State Transitions

```text
No saved constraints
  -> Load defaults from selected semester and study type
  -> Staff customize constraints
  -> Successful generation
  -> Saved constraints for course-semester

Saved constraints for course-semester
  -> Load saved constraints
  -> Staff generate successfully with changed custom constraints
  -> Replace saved constraints

Saved constraints for course-semester
  -> Staff clear custom constraints
  -> Delete saved constraints
  -> Load defaults from selected semester and study type

Any active constraints
  -> Generation fails or is blocked
  -> Existing saved constraints remain unchanged
```
