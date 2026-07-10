# Planner Resource Scope

This is the current slice roadmap for the resource planner after the Slice 3 feedback update.

## Slice 1: Single-Course Draft Schedule Generation

**Status**: Implemented.

Admin generates a draft schedule for one course using total units, lecturer session preference, one Cohort, one room, one semester, and Study Type Time Windows.

**Value**: Proves the core scheduling engine.

## Slice 2: Review Generated Schedule In Planner UI

**Status**: Implemented, then refined by Slice 3.

Show generated Draft Sessions in a simple weekly/list calendar view, with filters for course, Cohort, lecturer, room, and study type.

Slice 2 originally reviewed only the currently selected course. Slice 3 refined the review surface into a semester-scoped Courses overview so those filters are useful across all generated plans in the selected semester.

**Value**: Lets office staff inspect the generated result before editing.

## Slice 3: Configurable Generation Constraints And Courses Overview

**Status**: Implemented.

Let office staff control generation inputs for the currently selected course before creating a draft schedule:

- planning period defaults to the selected semester dates
- optional custom start date and end date
- one or more allowed weekly teaching windows by weekday and hour range
- system-selected defaults when no custom constraints are provided
- custom constraints saved per selected course and semester after successful generation

The generation controls and Generate button live with the left-side planning inputs. The central panel is now a Courses overview that shows generated plans for the selected semester, independent from the selected planning input. Overview filters are compact dropdowns derived from all generated plans in that semester.

This slice still does not generate multiple courses in one action. It only lets staff browse generated single-course drafts together in one semester overview.

**Value**: Gives office staff control over when units may be planned and makes the review filters useful across generated plans.

## Slice 4: Manual Session Editing

**Status**: Next recommended slice.

Allow admins to change date, start time, room, or session length for generated Draft Sessions.

**Value**: Turns the tool from generator into planner workflow.

## Slice 5: Conflict Detection

Detect conflicts after generation or manual edits:

- lecturer overlap
- room overlap
- Cohort overlap
- room capacity violation
- session outside allowed generation or Study Type Time Window

**Value**: Makes manual changes safe.

## Slice 6: Multi-Course Draft Generation

Generate schedules for multiple courses in one semester, initially without full optimization.

This is distinct from the Slice 3 Courses overview. Slice 3 can display multiple already-generated course plans, but each Generate action still targets one selected course.

**Value**: Moves from proof-of-concept to real semester planning.

## Slice 7: Conflict-Aware Multi-Course Scheduling

Improve multi-course generation so it avoids known lecturer, room, and Cohort conflicts during generation.

**Value**: Reduces manual correction work.

## Slice 8: Public Holiday Avoidance

Add holiday calendars and prevent generated sessions from landing on holidays.

**Value**: Removes a common real-world planning error.

## Slice 9: Exam Scheduling

Generate and manage exams separately from teaching sessions, usually at least one week after the last teaching session.

**Value**: Covers the full academic planning lifecycle.

## Slice 10: Multiple Lecturers And Rooms Per Course

Support courses taught by two or more lecturers and courses that can use multiple eligible rooms.

**Value**: Handles real-world exceptions without forcing manual workarounds.

## Slice 11: Planning Dashboard And Validation Alerts

Add an operational overview for:

- unscheduled units
- courses with conflicts
- room capacity issues
- hours remaining
- generation failures
- schedules that need review

The dashboard should not replace the left-side planning input panel. It should be a separate overview/control-center surface or a clearly separated dashboard section.

**Value**: Gives office staff an operational control center.

## Recommended Order

The current core loop is now:

1. Generate one course.
2. Inspect generated plans in the semester Courses overview.
3. Constrain future generation inputs.
4. Adjust sessions manually.
5. Validate conflicts.

Next recommended slices: Slice 4, then Slice 5. After that, move to Slice 6 and Slice 7 for multi-course generation and conflict-aware scheduling.
