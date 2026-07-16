# Feature Specification: Manual Session Creation, Deletion, and Remaining Units

**Working Branch**: `master`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Create FS-009 so a planner can add one Draft Session, delete one generated or manual session, or clear one course-semester draft while immediately understanding remaining units and refreshed alerts. Preserve hard structural and capacity rules, source records, and saved generation constraints; keep generation, optimization, bulk semester deletion, splitting/merging, source deletion, and automatic conflict repair out of scope."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-15

- Q: For a manually created Draft Session, how should units and clock time relate? → A: Units and start time calculate a default end time; the planner may override the end time, while units continue to drive remaining units.
- Q: How should a course-semester draft be represented after its last session is deleted? → A: Remove the empty Draft Schedule and keep the course visible with all units remaining.
- Q: Which confirmation behavior should apply to single-session and complete-draft deletion? → A: Confirm both actions, with each confirmation identifying its exact scope, units removed from scheduled coverage, and resulting remaining-unit count.
- Q: Which lecturer and room choices should manual session creation allow? → A: Inherit the course's lecturer and let the planner select any existing room with sufficient capacity.
- Q: What happens if the target session or course draft changes after its deletion confirmation appears? → A: Cancel the stale deletion, refresh current state, and require confirmation again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add One Draft Session Manually (Priority: P1)

A planner adds one Draft Session to a selected course in one semester and immediately sees how that session changes the course's remaining units and the semester's validation alerts.

**Why this priority**: Manual creation completes the existing correction workflow by letting the planner fill unscheduled course units without running generation.

**Independent Test**: Select a course-semester with remaining units, enter one structurally valid session with sufficient room capacity, save it, and verify that the session appears, the remaining-unit count decreases by the session's units, and all applicable alerts reflect the saved semester state.

**Acceptance Scenarios**:

1. **Given** a course-semester has no Draft Schedule and has all course units remaining, **When** the planner saves one valid manual Draft Session, **Then** a Draft Schedule containing that session exists for only that course and semester, and remaining units decrease by the session's units.
2. **Given** a course-semester has a partial Draft Schedule, **When** the planner saves one valid manual Draft Session whose units do not exceed the remaining units, **Then** the session is added without replacing or changing existing sessions, and remaining units decrease by exactly the added units.
3. **Given** the planner enters a start time and whole-unit count for a manual session, **When** either value is set or changed, **Then** the proposed end time is calculated from the start time using the established teaching-unit and inter-unit break durations.
4. **Given** a proposed end time has been calculated, **When** the planner moves it earlier to represent merged teaching units or later to represent an unplanned pause and then saves a structurally valid session, **Then** the adjusted end time is retained and the explicit unit count remains unchanged.
5. **Given** the selected course has an assigned lecturer and existing rooms are available, **When** the planner prepares a manual session, **Then** the course's lecturer is used and the planner may select any existing room whose capacity is sufficient without requiring resource-eligibility data.
6. **Given** a valid manual session uses a time or resource that creates one or more non-blocking lecturer, room, cohort, or allowed-window alerts, **When** the planner saves it, **Then** the session remains saved and every applicable alert is visible after the refresh.
7. **Given** a manual session has an out-of-semester date, a non-positive or non-whole unit count, units greater than the course's remaining units, invalid time order, a missing referenced record, a second session for the same course on the same date, or a room below cohort capacity, **When** the planner attempts to save it, **Then** the session is not created, remaining units do not change, and the planner receives an understandable reason.
8. **Given** the new session accounts for all remaining units, **When** it is saved, **Then** the course shows zero remaining units without triggering generation or changing saved generation constraints.

---

### User Story 2 - Delete One Draft Session (Priority: P2)

A planner deletes one selected generated or manually created Draft Session after confirming the exact consequence and immediately sees the resulting remaining-unit count and refreshed alerts.

**Why this priority**: Removing one incorrect or unwanted session is the smallest safe way to reduce a draft without clearing unrelated course work.

**Independent Test**: Select one session from a multi-session course draft, review and accept its deletion confirmation, then verify that only that session is removed, scheduled coverage decreases by its units, remaining units follow FR-026, and alerts on all affected sessions are refreshed.

**Acceptance Scenarios**:

1. **Given** a selected generated or manually created Draft Session exists, **When** the planner requests deletion, **Then** the confirmation identifies the session, its course and semester, the units being removed from scheduled coverage, and the resulting remaining-unit count.
2. **Given** the single-session deletion confirmation is displayed, **When** the planner cancels, **Then** no session, remaining-unit count, alert, source record, or saved generation constraint changes.
3. **Given** the planner confirms deletion of one session from a multi-session draft, **When** deletion succeeds, **Then** only that session is removed, all other sessions remain unchanged, scheduled units decrease by exactly the deleted session's units, and remaining units are recalculated from the resulting schedule.
4. **Given** the session being deleted participates in validation alerts, **When** deletion succeeds, **Then** alerts are refreshed for the complete affected semester state, including related sessions that were not deleted.
5. **Given** the selected session is the course-semester's last session, **When** the planner confirms its deletion, **Then** no empty Draft Schedule remains, the course remains available in the planning context, and all course units are shown as remaining.
6. **Given** the selected session or its course draft changes after the deletion confirmation appears, **When** the planner confirms deletion, **Then** the stale deletion is cancelled, no current session is removed, the current state is refreshed, and deletion requires a new confirmation.

---

### User Story 3 - Clear One Course-Semester Draft (Priority: P3)

A planner explicitly clears every Draft Session for one course in one semester after reviewing an understandable confirmation, while preserving the course, its planning data, and its saved generation constraints.

**Why this priority**: Clearing one course draft provides a deliberate reset when individual deletion would be tedious, without introducing bulk semester deletion or source-data loss.

**Independent Test**: Choose a course that has several generated, manually edited, and manually created sessions in one semester, confirm the clear action, and verify that only those sessions and their Draft Schedule are removed while full remaining units, saved constraints, source records, and other semesters remain intact.

**Acceptance Scenarios**:

1. **Given** a course-semester draft contains one or more sessions, **When** the planner requests to clear it, **Then** the confirmation identifies the course and semester, the number of sessions to be removed, the units that will become remaining, and that source records and saved generation constraints will be preserved.
2. **Given** the complete-draft confirmation is displayed, **When** the planner cancels, **Then** the Draft Schedule, every session, remaining-unit count, alerts, source records, and saved generation constraints remain unchanged.
3. **Given** the planner confirms clearing a course-semester draft, **When** deletion succeeds, **Then** its generated, manually edited, and manually created sessions and the now-empty Draft Schedule are removed, while all course units are shown as remaining.
4. **Given** the same course has a draft in another semester or other courses have drafts in the selected semester, **When** one course-semester draft is cleared, **Then** every other course-semester draft remains unchanged.
5. **Given** saved generation constraints exist for the cleared course and semester, **When** its draft is cleared, **Then** those constraints remain available unchanged for later planner actions.
6. **Given** the cleared sessions participated in validation alerts, **When** deletion succeeds, **Then** the selected semester's alerts are refreshed so no alert refers to a deleted session and alerts between surviving sessions remain accurate.
7. **Given** any session in the course draft changes after the complete-draft confirmation appears, **When** the planner confirms deletion, **Then** the stale deletion is cancelled, the current draft remains unchanged, the confirmation details are refreshed, and clearing requires a new confirmation.

### Edge Cases

- A course-semester has no Draft Schedule. Its remaining-unit state shows all current course units, and the clear-draft action does not imply that any session data exists to delete.
- A course-semester has exactly one session. Deleting that session through the single-session action states that the course draft will become empty and results in the same empty representation as clearing the draft.
- A manual session would schedule more units than remain. Creation is rejected rather than producing a negative remaining-unit count or changing existing sessions.
- A course's scheduled units already equal its total units. Remaining units show zero, and another session cannot be added unless units first become remaining.
- A course's current total units are lower than the units already represented by existing sessions because of prior planning-data changes. Remaining units show zero rather than a negative number, and this slice does not move, resize, or delete sessions automatically.
- A manual session is otherwise structurally valid but creates several non-blocking alerts. It is saved and all applicable alerts are presented together.
- A room, lecturer, course, semester, or other required referenced record is unavailable when creation is submitted. No session is created and no remaining-unit state changes.
- A deletion target no longer exists, or the target session or course draft changes after confirmation is displayed. The stale deletion is cancelled, no current schedule data is removed, the current state and confirmation details are refreshed, and the planner must confirm again.
- A requested create or delete action cannot be completed. The previously saved draft remains unchanged and the planner is told that the action did not succeed.
- Clearing one course draft removes alerts involving its deleted sessions but does not suppress unrelated alerts among surviving sessions.
- Filters or alternate semester views hide an affected session. Remaining-unit and alert calculations still reflect the complete selected-semester state, not only currently visible sessions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a planner to add exactly one manual Draft Session per creation action to one selected course in one selected semester.
- **FR-002**: The system MUST allow manual creation whether the course-semester currently has a partial Draft Schedule or no Draft Schedule.
- **FR-003**: A manual Draft Session MUST identify one existing course-semester context, one date, one start time, one end time, a positive whole number of teaching units, the course's existing lecturer and cohort context, and one existing room selected by the planner.
- **FR-004**: Whenever the start time or whole-unit count is set or changed, the system MUST calculate a proposed end time using the established teaching-unit and inter-unit break durations; the planner MUST be able to move that end time earlier or later before saving; and the system MUST retain a structurally valid adjusted end time while continuing to use the explicit unit count for scheduled and remaining units without inferring units from elapsed duration.
- **FR-005**: The system MUST require a manual session's date to fall within the selected semester and its end time to be later than its start time.
- **FR-006**: The system MUST reject a manual session when any required course, semester, course-assigned lecturer, planner-selected room, or cohort reference does not exist.
- **FR-007**: The system MUST preserve the existing rule that one course Draft Schedule cannot contain more than one Draft Session on the same date.
- **FR-008**: The system MUST reject a manual session whose assigned room capacity is below the course cohort size.
- **FR-009**: The system MUST reject a manual session whose units exceed the course's current remaining units. Validation and persistence MUST use the same current saved schedule state so concurrent creation requests cannot together schedule more than the current remaining units.
- **FR-010**: The system MUST leave the existing Draft Schedule, sessions, remaining-unit count, alerts, source records, and saved generation constraints unchanged when manual-session creation fails.
- **FR-011**: The system MUST allow an otherwise valid manual session to be saved when it produces non-blocking lecturer, room, cohort, generation-constraint, or Study Type Time Window alerts.
- **FR-012**: The system MUST NOT automatically move, resize, split, merge, delete, regenerate, optimize, or otherwise repair sessions in response to manual creation or its alerts.
- **FR-013**: The system MUST allow a planner to request deletion of exactly one generated or manually created Draft Session per single-session deletion action.
- **FR-014**: Before deleting one session, the system MUST require explicit confirmation that identifies the session, course, semester, units being removed from scheduled coverage, and the resulting remaining-unit count.
- **FR-015**: A cancelled single-session deletion MUST leave all planning and schedule data unchanged.
- **FR-016**: The system MUST reject a confirmed single-session deletion if the selected session or its course draft has changed since confirmation was displayed; otherwise it MUST remove only the selected session and preserve every other session, source record, and saved generation constraint.
- **FR-017**: When single-session deletion removes the last session, the system MUST remove the empty Draft Schedule representation and MUST continue to show the course with all course units remaining.
- **FR-018**: The system MUST allow a planner to request complete deletion of all Draft Sessions for exactly one selected course in exactly one selected semester.
- **FR-019**: Complete course-semester draft deletion MUST include generated, manually edited, and manually created Draft Sessions belonging to that one draft.
- **FR-020**: Before clearing a course-semester draft, the system MUST require explicit confirmation that identifies the course, semester, number of affected sessions, number of units that will become remaining, and preservation of source records and saved generation constraints.
- **FR-021**: A cancelled complete-draft deletion MUST leave all planning and schedule data unchanged.
- **FR-022**: The system MUST reject a confirmed complete-draft deletion if any session in the selected course-semester draft has changed since confirmation was displayed; otherwise it MUST remove only that course-semester's Draft Schedule and Draft Sessions.
- **FR-023**: Complete-draft deletion MUST preserve the source course, semester, lecturer, room, cohort, Study Type, and other planning records.
- **FR-024**: Complete-draft deletion MUST preserve the selected course-semester's saved generation constraints unchanged.
- **FR-025**: Creation and deletion actions MUST NOT modify any draft belonging to another course or semester.
- **FR-026**: The system MUST calculate remaining units as the course's current total units minus the sum of units in its current Draft Sessions, with a minimum displayed value of zero.
- **FR-027**: After a successful creation or deletion, the system MUST recalculate and display remaining units from the saved schedule state without requiring the planner to reload or revisit the planning context.
- **FR-028**: When a course-semester has no Draft Sessions, the system MUST show all current course units as remaining.
- **FR-029**: After a successful creation or deletion, the system MUST refresh validation alerts for the complete affected semester state without requiring the planner to reload or revisit it.
- **FR-030**: The system MUST remove alerts that no longer apply, retain alerts that still apply, and expose new alerts caused by the saved action.
- **FR-031**: The system MUST provide understandable failure feedback when a requested creation or deletion cannot be completed and MUST NOT present the requested change as successful; for a stale deletion, it MUST refresh the current state and require a new confirmation before another deletion attempt.
- **FR-032**: This feature MUST NOT provide bulk deletion across a semester, schedule generation or optimization, session splitting or merging, source-record deletion, automatic conflict repair, drag-and-drop scheduling, or resource-eligibility administration.
- **FR-033**: Existing course-semester generation constraints and existing generation behavior MUST remain unchanged by this feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each implemented user story where automated testing is practical.
- **TR-002**: Automated coverage MUST verify remaining-unit calculations after valid creation, single-session deletion, last-session deletion, and complete-draft deletion.
- **TR-003**: Automated coverage MUST verify default end-time calculation, planner override in both directions, all hard creation rules, and that every rejected creation leaves the prior saved state unchanged.
- **TR-004**: Automated coverage MUST verify that applicable non-blocking alerts permit creation and refresh after every successful creation or deletion.
- **TR-005**: Automated coverage MUST verify both deletion confirmation paths, cancellation, stale-state rejection and renewed confirmation, course-semester isolation, source-record preservation, and saved-generation-constraint preservation.
- **TR-006**: Automated coverage MUST verify that manual editing, generation, semester review, filters, and validation-alert behavior established by earlier slices remain available.
- **TR-007**: Any exception to automated test-first work MUST document the reason and the manual verification path in the implementation plan.

### Key Entities

- **Course-Semester Planning Context**: One course planned within one semester, including its current total units, saved generation constraints, Draft Schedule if present, and computed remaining units.
- **Draft Schedule**: The current collection of one or more planned teaching sessions for one course in one semester. Within this feature, no empty Draft Schedule is retained after its last session is removed.
- **Draft Session**: One generated or manually created teaching occurrence with a date, start and end time, explicit teaching-unit count, the course's lecturer and cohort context, and one planner-selected room.
- **Remaining Units**: The unscheduled portion of a course's current total units, calculated from all current Draft Sessions for that course and semester and never displayed below zero.
- **Generation Constraints**: Saved course-semester planning limits retained unchanged when sessions or the complete Draft Schedule are deleted.
- **Validation Alert**: A non-blocking explanation of an overlap, allowed-window issue, or other established schedule concern, recalculated from the current semester state after a saved action.
- **Source Planning Record**: A course, semester, lecturer, room, cohort, Study Type, or related record used to create schedules but never deleted by a session or draft deletion action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an unaided usability review with at least 10 representative planners or acceptance reviewers familiar with the existing planner, at least 90% can add one valid manual session and correctly identify the resulting remaining units within two minutes.
- **SC-002**: Across all acceptance cases, 100% of successful additions reduce remaining units by exactly the added units; 100% of single-session deletions reduce scheduled units by exactly the deleted units and produce the remaining value required by FR-026; and 100% of complete-draft deletions restore all course units as remaining.
- **SC-003**: In the documented reference acceptance environment, the updated remaining-unit count and refreshed alert state are visible within one second after confirmation of a successful creation or deletion, without a manual reload.
- **SC-004**: In 100% of tested invalid-creation cases, no new session is retained and the prior schedule, remaining units, source records, and saved generation constraints remain unchanged.
- **SC-005**: In 100% of tested cancellation cases, no schedule, remaining-unit, alert, source-record, or saved-generation-constraint state changes.
- **SC-006**: In 100% of tested single-session deletions, only the selected session is removed; in 100% of tested complete-draft deletions, only the selected course-semester draft is removed.
- **SC-007**: In 100% of tested cross-course and cross-semester cases, manual creation or deletion leaves every out-of-scope course-semester draft unchanged.
- **SC-008**: In 100% of tested alert cases, every applicable alert reflects the saved post-action semester state and no alert refers to a deleted session.
- **SC-009**: In the same usability-review protocol as SC-001, at least 90% of participants can distinguish single-session deletion from complete-draft deletion and correctly state which records and constraints each action preserves before confirming.
- **SC-010**: All applicable acceptance scenarios from manual session editing, validation alerts, single-course generation, and multi-course generation continue to pass after this feature is delivered.
- **SC-011**: In 100% of tested cases where a target session or course draft changes after confirmation is displayed, no current session is deleted until the planner reviews the refreshed state and confirms again.

## Assumptions

- The planner user already has access to the existing planner-only workflow; this slice adds no authentication, roles, or permissions.
- FS-006 and its dependencies provide course-semester drafts, saved generation constraints, manual session editing, semester review, and non-blocking validation alerts.
- Manual creation uses an explicit positive whole-unit input because remaining work is measured in teaching units. The unit count and start time initially calculate the end time using the existing duration convention; the planner may then shorten or extend that interval for merged teaching units or unplanned pauses without changing the unit count.
- One teaching unit remains 45 minutes, with the established 10-minute inter-unit breaks included in the calculated default end time. A planner-adjusted end time changes the scheduled clock interval only and does not retroactively change units.
- A manual Draft Session inherits the course's existing lecturer and cohort. The planner may select any existing room that passes the hard capacity rule; defining or enforcing eligible-resource and availability relationships belongs to FS-008, not this slice.
- A room-capacity failure is blocking. Existing lecturer, room, cohort, generation-window, and Study Type Time Window alerts remain non-blocking when all structural rules pass.
- A course-semester with no sessions has no retained empty Draft Schedule. It remains visible through its course-semester planning context with all course units remaining.
- Single-session deletion always uses an explicit confirm-or-cancel step. If it removes the last session, the confirmation also explains that the course draft will become empty.
- Complete-draft deletion uses a distinct confirmation describing the broader consequence; typed confirmation or additional approval is not required for this slice.
- Remaining-unit and alert refreshes are based on the complete saved state for the affected semester, regardless of active filters or view mode.
- Drag-and-drop interaction is not required. Manual creation and deletion extend the existing editor and may gradually adopt relevant concepts from `docs/designs/resource-planner-calendar-screen-reference.png` without requiring a broader workspace redesign.
