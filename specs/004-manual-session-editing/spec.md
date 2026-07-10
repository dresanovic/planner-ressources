# Feature Specification: Manual Session Editing

**Working Branch**: `master`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "Create Slice 4 for the planner resource roadmap: Manual Session Editing. Office staff need to manually adjust generated Draft Sessions after reviewing them in the semester Courses overview. The feature builds on Slices 1-3, where staff can generate single-course draft schedules, configure generation constraints, and inspect generated plans across the selected semester. Users must be able to edit an existing generated Draft Session's date, start time, room, and session length. Editing should update the draft schedule data so the changed session remains visible in the Courses overview and is preserved when the user changes filters or view modes. The slice should focus only on manual editing of already generated Draft Sessions. It should not add conflict detection, conflict warnings, public holiday handling, exam scheduling, multi-course generation, dashboard summaries, validation alert workflows, multiple lecturers per course, or multiple eligible rooms per course. Those remain future slices. The goal is that office staff can correct generated sessions manually before conflict detection is introduced in the next slice."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-10

- Q: Should manual date edits be bounded by semester dates or active generation/teaching windows? -> A: Manual date edits must stay within the selected semester; generation-window and teaching-window violations are allowed for now.
- Q: How should office staff edit session length? -> A: Session length is edited by changing the end time.
- Q: Which room validity checks belong to manual room editing? -> A: Manual room edits must enforce room capacity; occupancy and overlap checks are deferred to Slice 5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Edit Session Time And Length (Priority: P1)

Office staff edit the date, start time, and end time of an existing generated Draft Session after reviewing it in the semester Courses overview.

**Why this priority**: Time and length corrections are the core value of manual editing. Without this story, staff can only inspect generated plans but cannot correct the most common scheduling issues.

**Independent Test**: Can be fully tested by opening a generated Draft Session from the Courses overview, changing its date, start time, and end time, saving the edit, and confirming the updated session is shown with the new values in both list and weekly review modes.

**Acceptance Scenarios**:

1. **Given** a generated Draft Session is visible in the Courses overview, **When** office staff open it for editing, **Then** the edit view shows the current date, start time, end time, room, and derived session length values.
2. **Given** office staff enter a valid new date, start time, and end time for a generated Draft Session, **When** they save the edit, **Then** the Draft Session is updated and the Courses overview shows the changed date, time range, and derived length.
3. **Given** an edited Draft Session is visible in list mode, **When** office staff switch to weekly mode, **Then** the edited session appears in the week and day matching its updated date.
4. **Given** office staff start editing a Draft Session, **When** they cancel without saving, **Then** the Draft Session remains unchanged in the Courses overview.

---

### User Story 2 - Change Session Room (Priority: P2)

Office staff change the room assigned to an existing generated Draft Session when the generated room assignment needs manual correction.

**Why this priority**: Room changes are a common manual planning adjustment and are explicitly part of Slice 4, but they can build on the editing workflow established by time and length edits.

**Independent Test**: Can be tested by opening a generated Draft Session, selecting a different room with sufficient capacity, saving, and confirming that the updated room is preserved in the Courses overview and in room-based filters.

**Acceptance Scenarios**:

1. **Given** a generated Draft Session has an assigned room, **When** office staff edit the session, **Then** they can choose a different room from rooms with sufficient capacity for the session's cohort.
2. **Given** office staff select a valid replacement room and save the edit, **When** the Courses overview refreshes, **Then** the Draft Session displays the replacement room.
3. **Given** a Draft Session's room was changed, **When** office staff filter the Courses overview by the replacement room, **Then** the edited Draft Session is included in the filtered results.
4. **Given** a Draft Session's room was changed, **When** office staff filter by the previous room, **Then** the edited Draft Session is no longer included because its room value changed.
5. **Given** a room does not have enough capacity for the session's cohort, **When** office staff try to use that room for the Draft Session, **Then** the edit is blocked and the existing room remains unchanged.

---

### User Story 3 - Preserve Manual Edits During Review (Priority: P3)

Office staff continue reviewing generated plans after manual edits without losing changes when they switch filters, switch view modes, or leave and return to the same selected semester.

**Why this priority**: Manual editing only supports a real planning workflow if saved edits remain durable and visible across normal review actions.

**Independent Test**: Can be tested by saving edits to a Draft Session, changing overview filters and review modes, returning to the edited session, and confirming the saved values are still present.

**Acceptance Scenarios**:

1. **Given** office staff save an edit to a Draft Session, **When** they change Courses overview filters, **Then** the saved edit remains part of the Draft Session data and appears whenever the edited session matches the active filters.
2. **Given** office staff save an edit to a Draft Session, **When** they switch between list and weekly review modes, **Then** both modes show the edited values.
3. **Given** office staff save an edit to a Draft Session, **When** they leave and later reopen the same selected semester's Courses overview, **Then** the edited values are still shown.
4. **Given** office staff regenerate the same course's draft schedule, **When** the regenerated schedule replaces previous generated sessions, **Then** the system follows the existing regeneration replacement behavior and no longer guarantees preservation of prior manual edits for replaced sessions.

### Edge Cases

- If a Draft Session no longer exists when office staff try to save an edit, the system must explain that the session cannot be updated and must not create a new session from the stale edit.
- If office staff enter an invalid date, a date outside the selected semester, invalid time, or an end time equal to or earlier than the start time, the edit must be blocked with a clear message and the existing Draft Session must remain unchanged.
- If the edited end time changes the derived session length, the Courses overview must show the updated length consistently with the saved start and end times.
- If a valid manual edit places a session outside the active generation constraints or teaching windows, the edit is still saved in this slice because conflict and window validation belongs to Slice 5.
- If a replacement room does not have enough capacity for the session's cohort, the room edit must be blocked and the existing Draft Session room must remain unchanged.
- If a replacement room is already occupied at the edited date and time, this slice does not block the edit because room overlap detection belongs to Slice 5.
- If an edit changes a session so it no longer matches active filters, the session may disappear from the current filtered result and must reappear when filters match the edited values.
- If office staff cancel an edit or close the edit controls without saving, no Draft Session fields may change.
- If saving an edit fails, the visible schedule must not pretend the edit was saved.
- Manual edits must not trigger conflict detection, conflict warnings, public holiday warnings, exam scheduling behavior, dashboard summaries, or validation alert workflows in this slice.
- Manual edits must apply only to existing generated Draft Sessions, not to creating new sessions, deleting sessions, splitting sessions, merging sessions, or editing source planning records.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow office staff to open an existing generated Draft Session from the Courses overview for manual editing.
- **FR-002**: System MUST show the current date, start time, end time, room, and derived session length when a Draft Session is opened for editing.
- **FR-003**: Users MUST be able to change the date of an existing generated Draft Session.
- **FR-004**: Users MUST be able to change the start time of an existing generated Draft Session.
- **FR-005**: Users MUST be able to change the room of an existing generated Draft Session.
- **FR-006**: Users MUST be able to change the end time of an existing generated Draft Session to adjust session length.
- **FR-007**: System MUST recalculate and display the session length after a saved start time or end time change.
- **FR-008**: System MUST save valid manual edits to the Draft Session so updated values are preserved across Courses overview filters and view modes.
- **FR-009**: System MUST keep existing Draft Session data unchanged when office staff cancel an edit.
- **FR-010**: System MUST block edits with invalid date values, invalid time values, or end times equal to or earlier than start times and show a clear message.
- **FR-011**: System MUST prevent stale edits from creating new Draft Sessions when the target Draft Session no longer exists.
- **FR-012**: System MUST update Courses overview filter behavior so edited room, date, and time-related values are reflected in the visible session set after saving.
- **FR-013**: System MUST preserve saved manual edits when office staff switch between list and weekly review modes.
- **FR-014**: System MUST preserve saved manual edits when office staff leave and reopen the same selected semester's Courses overview.
- **FR-015**: System MUST continue to use the existing regeneration replacement behavior when office staff generate a replacement draft schedule for the same course.
- **FR-016**: System MUST block manual date edits that fall outside the selected semester.
- **FR-017**: System MUST allow otherwise valid manual edits even if the edited session falls outside active generation constraints or teaching windows.
- **FR-018**: System MUST block manual room edits when the replacement room capacity is below the session cohort size.
- **FR-019**: System MUST allow otherwise valid manual room edits even if the replacement room is occupied at the edited date and time.
- **FR-020**: System MUST NOT add conflict detection, conflict warnings, public holiday handling, exam scheduling, multi-course generation, dashboard summaries, validation alert workflows, multiple lecturers per course, or multiple eligible rooms per course in this feature.
- **FR-021**: System MUST NOT add creating, deleting, splitting, or merging Draft Sessions as part of this feature.
- **FR-022**: System MUST NOT edit source planning records such as Course, Cohort, Lecturer, Room catalog details, Semester, Study Type, or generation constraints as part of a Draft Session edit.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Backend edit behavior MUST be verified with FastAPI-compatible tests, normally using `pytest`.
- **TR-003**: Frontend manual editing behavior MUST be verified through React/Vite-appropriate checks, such as build, lint, component, or UI tests.
- **TR-004**: Cross-stack behavior MUST be verified for the contract that saves and reloads edited Draft Session values.
- **TR-005**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Draft Session**: An existing generated teaching block that office staff can edit for date, start time, end time, and room.
- **Draft Schedule**: The generated schedule containing the Draft Session being edited.
- **Courses Overview**: The selected-semester review surface where office staff find, inspect, filter, and reopen edited Draft Sessions.
- **Room**: The teaching location assigned to a Draft Session and selectable as a replacement during manual editing.
- **Manual Edit**: A saved correction to an existing Draft Session's editable scheduling fields.
- **Review Filter**: A course, Cohort, lecturer, room, or study type value that controls Draft Session visibility after edits are saved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Office staff can open a generated Draft Session for editing and save a valid date, start time, end time, or room change in no more than four interactions after locating the session.
- **SC-002**: 100% of saved manual edits in validation examples are visible in both list and weekly review modes.
- **SC-003**: 100% of saved room edits in validation examples are reflected in room filter results.
- **SC-004**: 100% of invalid date, out-of-semester date, invalid time, and end-before-start edits in validation examples are blocked before existing Draft Session data changes.
- **SC-005**: 100% of canceled edit attempts in validation examples leave the Draft Session unchanged.
- **SC-006**: 100% of saved edits in validation examples remain visible after office staff leave and reopen the same selected semester's Courses overview.
- **SC-007**: Office staff can correctly identify that this slice edits only existing Draft Sessions, not source planning records or future generation constraints, in at least 90% of review checks.
- **SC-008**: 100% of room edits to rooms with insufficient capacity in validation examples are blocked before existing Draft Session data changes.
- **SC-009**: No room occupancy conflict warning, holiday warning, exam scheduling, dashboard summary, multi-course generation, session creation, session deletion, session split, or session merge action is available from this feature's workflow.

## Assumptions

- Office staff already have access to the planner UI and permission to view and edit generated Draft Sessions.
- Slices 1-3 are available before this feature is implemented: single-course generation, semester Courses overview, review filters, and configurable generation constraints.
- Session length is derived from the Draft Session's start time and end time; office staff adjust length by editing the end time.
- Room choices come from the planner's existing room records and must satisfy the session cohort's capacity need.
- Manual edits change generated Draft Session data only; they do not change generation constraints or the source planning records used to generate future schedules.
- Conflict safety is intentionally deferred to Slice 5, so this slice does not warn about lecturer, room occupancy, Cohort, generation-window, teaching-window, or holiday conflicts caused by edits.
- Manual date edits must stay inside the selected semester because the Courses overview is scoped by selected semester.
- Regenerating a draft schedule for the same course may replace existing generated sessions according to the behavior established in earlier slices.
