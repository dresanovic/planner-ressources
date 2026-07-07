Planner Resource Scope

Here is the clean slice roadmap I’d use for this resource planner.

Slice 1: Single-Course Draft Schedule Generation

Status: specified, planned, task-ready.

Admin generates a draft schedule for one course using total units, lecturer session preference, one Cohort, one room, one semester, and Study Type Time Windows.

Value: proves the core scheduling engine.

Slice 2: Review Generated Schedule In Planner UI

Show generated Draft Sessions in a simple weekly/list calendar view, with filters for course, Cohort, lecturer, room, and study type.

Value: lets office staff inspect the generated result before editing.

Slice 3: Manual Session Editing

Allow admins to change date, start time, room, or session length for generated Draft Sessions.

Value: turns the tool from generator into planner workflow.

Slice 4: Conflict Detection

Detect conflicts after generation or manual edits:

lecturer overlap

room overlap

Cohort overlap

room capacity violation

session outside Study Type Time Window

Value: makes manual changes safe.

Slice 5: Multi-Course Draft Generation

Generate schedules for multiple courses in one semester, initially without full optimization.

Value: moves from proof-of-concept to real semester planning.

Slice 6: Conflict-Aware Multi-Course Scheduling

Improve multi-course generation so it avoids known lecturer, room, and Cohort conflicts during generation.

Value: reduces manual correction work.

Slice 7: Public Holiday Avoidance

Add holiday calendars and prevent generated sessions from landing on holidays.

Value: removes a common real-world planning error.

Slice 8: Exam Scheduling

Generate and manage exams separately from teaching sessions, usually at least one week after the last teaching session.

Value: covers the full academic planning lifecycle.

Slice 9: Multiple Lecturers And Rooms Per Course

Support courses taught by two or more lecturers and courses that can use multiple eligible rooms.

Value: handles real-world exceptions without forcing manual workarounds.

Slice 10: Planning Dashboard And Validation Alerts

Add the left-panel style overview:

unscheduled units

courses with conflicts

room capacity issues

hours remaining

generation failures

Value: gives office staff an operational control center.

My recommendation: after Slice 1, do Slice 2 then Slice 3 then Slice 4. That gives you the core loop: generate, inspect, adjust, validate.

