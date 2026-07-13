# Feature Specification: Conflict Detection

**Working Branch**: `master`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "Create Slice 5: Conflict Detection for the planner resource app. Office staff need to see validation alerts after draft schedule generation and after manual session edits so they can identify unsafe schedules before using them for planning. The system should detect and display these conflict types for generated Draft Sessions in the selected semester: lecturer overlap, room overlap, Cohort overlap, room capacity violation, session outside the allowed generation constraints or Study Type Time Window. Conflict detection must work across all generated plans visible in the semester Courses overview, including sessions from different courses. It must also update after saved manual edits. Users should be able to inspect which sessions are affected, understand the conflict reason, and continue reviewing or editing without conflict detection blocking saves or generation. Do not implement automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summaries, multi-course generation, session creation/deletion/splitting/merging, or multiple lecturers/rooms per course."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-13

- Q: How much related-session detail should each validation alert expose? -> A: Each alert identifies every related conflicting session available in the selected semester.
- Q: Which generation constraints are authoritative for window validation alerts after constraints change? -> A: Validate against the currently active constraints for that course and semester.
- Q: Should Study Type Time Window alerts appear when custom active generation constraints exist? -> A: No; custom active generation constraints replace Study Type window validation for that course-semester.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Overlap Conflicts In Semester Overview (Priority: P1)

Office staff review the selected semester Courses overview and see alerts when generated Draft Sessions overlap for the same lecturer, room, or Cohort, including overlaps between sessions from different courses.

**Why this priority**: Overlap detection is the core safety value of this slice. It lets staff identify the most disruptive scheduling conflicts immediately after generation or manual edits while preserving the existing planning workflow.

**Independent Test**: Can be fully tested by preparing generated Draft Sessions in the same selected semester with overlapping lecturer, room, and Cohort assignments, opening the Courses overview, and confirming the affected sessions show clear alerts with the matching conflict reasons.

**Acceptance Scenarios**:

1. **Given** two generated Draft Sessions in the selected semester use the same lecturer during overlapping times, **When** office staff view the Courses overview, **Then** both affected sessions show a lecturer overlap alert that identifies the conflicting session context.
2. **Given** two generated Draft Sessions in the selected semester use the same room during overlapping times, **When** office staff view the Courses overview, **Then** both affected sessions show a room overlap alert that identifies the conflicting session context.
3. **Given** two generated Draft Sessions in the selected semester use the same Cohort during overlapping times, **When** office staff view the Courses overview, **Then** both affected sessions show a Cohort overlap alert that identifies the conflicting session context.
4. **Given** overlapping sessions belong to different generated course plans in the same selected semester, **When** office staff inspect either affected session, **Then** the alert makes clear that the conflict crosses course boundaries.

---

### User Story 2 - See Capacity And Window Violations (Priority: P2)

Office staff see validation alerts when generated Draft Sessions violate room capacity or fall outside the allowed generation constraints or Study Type Time Window.

**Why this priority**: Capacity and window violations make a schedule unsafe even when no two sessions overlap. These alerts complete the validation set described for Slice 5 without changing generation or edit behavior.

**Independent Test**: Can be tested by preparing generated Draft Sessions with a room below Cohort capacity, a session outside the active generation constraints, and a session outside the Study Type Time Window, then confirming each affected session displays the correct violation reason.

**Acceptance Scenarios**:

1. **Given** a generated Draft Session is assigned to a room whose capacity is below the session Cohort size, **When** office staff view or inspect that session, **Then** the session shows a room capacity violation alert.
2. **Given** a generated Draft Session falls outside the currently active allowed generation constraints for its course and semester, **When** office staff view or inspect that session, **Then** the session shows an allowed generation constraint violation alert.
3. **Given** no custom active generation constraints exist and a generated Draft Session falls outside the Study Type Time Window for the course's study type, **When** office staff view or inspect that session, **Then** the session shows a Study Type Time Window violation alert.
4. **Given** a Draft Session has multiple validation problems, **When** office staff inspect it, **Then** all relevant conflict or violation reasons are available without hiding one behind another.

---

### User Story 3 - Refresh Alerts After Generation And Manual Edits (Priority: P3)

Office staff continue generating and manually editing Draft Sessions while validation alerts update to match the saved schedule state, without blocking generation or edit saves.

**Why this priority**: Conflict detection must stay useful during the normal planning loop. Alerts that do not refresh after changes would become misleading, while blocking behavior would expand the slice into conflict-aware editing or generation.

**Independent Test**: Can be tested by generating a draft schedule, observing alerts, manually editing a session to create or resolve a conflict, saving the edit, and confirming the Courses overview shows the updated alert state while the edit itself is allowed when otherwise valid.

**Acceptance Scenarios**:

1. **Given** office staff generate or replace a draft schedule for a course in the selected semester, **When** the Courses overview refreshes, **Then** validation alerts reflect the generated sessions now visible in that semester overview.
2. **Given** office staff save a manual edit that creates a lecturer, room, Cohort, capacity, generation-window, or Study Type Time Window issue, **When** the save completes, **Then** the affected sessions show the new alert state.
3. **Given** office staff save a manual edit that resolves an existing validation issue, **When** the save completes, **Then** the resolved alert is removed from sessions that are no longer affected.
4. **Given** a manual edit is otherwise valid under the manual editing rules, **When** it creates or leaves a validation issue, **Then** the edit is saved and the issue is reported as an alert rather than blocking the save.
5. **Given** generated sessions contain validation alerts, **When** office staff continue filtering, switching between list and weekly modes, or opening edit controls, **Then** the alerts remain associated with the correct affected sessions.

### Edge Cases

- If no generated Draft Sessions exist for the selected semester, the Courses overview must show no validation alerts and must not imply that validation failed.
- If only one generated Draft Session exists in the selected semester, overlap checks must not report self-conflicts.
- If two sessions touch at a boundary where one ends exactly when the other starts, they must not be treated as overlapping.
- If a conflict involves more than two sessions, each affected session must identify every related conflicting session available in the selected semester.
- If active filters hide one side of a conflict, the visible affected session must still show that it has a conflict in the selected semester.
- If a session has missing or stale reference data needed for validation, the system must show a clear validation-data issue instead of silently declaring the session safe.
- If manual editing moves a session outside currently active allowed generation constraints, the edit must be saved when it is otherwise valid and then shown with a generation-constraint alert. Study Type Time Window alerts apply only when no custom active generation constraints exist.
- If regenerating a course replaces its prior draft sessions, validation alerts must reflect the replacement schedule and must not keep alerts for sessions that no longer exist.
- Conflict detection must not create, delete, split, merge, or automatically move Draft Sessions.
- Conflict detection must not add public holiday alerts, exam scheduling alerts, dashboard summaries, multi-course generation controls, conflict-aware generation, automatic conflict resolution, or support for multiple lecturers or rooms per course.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST evaluate generated Draft Sessions in the selected semester for validation alerts.
- **FR-002**: System MUST detect overlapping Draft Sessions that share the same lecturer.
- **FR-003**: System MUST detect overlapping Draft Sessions that share the same room.
- **FR-004**: System MUST detect overlapping Draft Sessions that share the same Cohort.
- **FR-005**: System MUST evaluate overlaps across all generated plans visible in the selected semester Courses overview, including sessions from different courses.
- **FR-006**: System MUST treat sessions as overlapping only when their date and time ranges intersect with positive duration.
- **FR-007**: System MUST NOT treat two sessions as overlapping when one ends exactly when the other begins.
- **FR-008**: System MUST detect room capacity violations when a Draft Session's assigned room capacity is below the session Cohort size.
- **FR-009**: System MUST detect Draft Sessions outside the currently active allowed generation constraints for the related course and semester.
- **FR-010**: System MUST detect Draft Sessions outside the Study Type Time Window for the related course study type only when no custom active generation constraints exist for the course-semester.
- **FR-011**: System MUST display validation alerts in the Courses overview so office staff can identify affected Draft Sessions.
- **FR-012**: System MUST provide an inspectable conflict reason for each affected Draft Session.
- **FR-013**: System MUST identify every related conflicting session available in the selected semester for each lecturer, room, or Cohort overlap alert, using readable context such as course, Cohort, lecturer, room, date, or time information available from the schedule.
- **FR-014**: System MUST support multiple validation alerts on the same Draft Session.
- **FR-015**: System MUST update validation alerts after draft schedule generation or regeneration changes the selected semester's generated sessions.
- **FR-016**: System MUST update validation alerts after a saved manual session edit changes date, start time, end time, or room.
- **FR-017**: System MUST remove validation alerts that no longer apply after generation, regeneration, or manual edits.
- **FR-018**: System MUST keep validation alerts associated with the correct sessions when office staff use overview filters.
- **FR-019**: System MUST keep validation alerts associated with the correct sessions when office staff switch between list and weekly review modes.
- **FR-020**: System MUST allow office staff to continue reviewing and editing sessions when validation alerts are present.
- **FR-021**: System MUST NOT block generation solely because validation alerts would be produced.
- **FR-022**: System MUST NOT block otherwise valid manual edits solely because validation alerts would be produced or remain.
- **FR-023**: System MUST show a clear validation-data issue when a session cannot be evaluated because required reference information is missing.
- **FR-024**: System MUST NOT implement automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summaries, multi-course generation, session creation, session deletion, session splitting, session merging, or multiple lecturers or rooms per course as part of this feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Schedule validation behavior MUST be verified with automated tests that cover conflict and violation detection rules.
- **TR-003**: Conflict display behavior MUST be verified with automated checks that cover alert visibility, alert reasons, filters, and view-mode changes.
- **TR-004**: Cross-stack behavior MUST be verified for the contract that exposes validation alerts with generated Draft Sessions in the semester Courses overview.
- **TR-005**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Draft Session**: A generated teaching block evaluated for overlaps, capacity violations, and window violations.
- **Validation Alert**: A non-blocking issue associated with one or more Draft Sessions that explains why the generated schedule may be unsafe.
- **Conflict Reason**: The specific validation category and readable context shown to office staff for an affected session.
- **Courses Overview**: The selected-semester review surface where validation alerts appear across all generated plans.
- **Lecturer**: The assigned teacher used to detect same-person overlaps.
- **Room**: The assigned teaching location used to detect room overlaps and room capacity violations.
- **Cohort**: The student group used to detect Cohort overlaps and determine capacity needs.
- **Generation Constraint**: The currently active course-semester date and teaching-window rules used to evaluate whether a generated Draft Session falls outside allowed planning bounds.
- **Study Type Time Window**: The standard teaching availability window for the related study type, used to evaluate time-window violations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of lecturer, room, and Cohort overlap examples in validation data show alerts on all affected Draft Sessions.
- **SC-002**: 100% of non-overlapping back-to-back session examples show no overlap alert.
- **SC-003**: 100% of room capacity violation examples show a capacity alert on the affected Draft Session.
- **SC-004**: 100% of currently active generation-constraint and applicable Study Type Time Window violation examples show the correct window alert on the affected Draft Session.
- **SC-005**: 100% of validation examples with multiple issues on one Draft Session expose every applicable conflict reason.
- **SC-006**: After a saved manual edit creates or resolves a validation issue, the Courses overview reflects the changed alert state before office staff need to leave and reopen the semester.
- **SC-007**: Office staff can identify the affected session and reason for a validation alert within two interactions after seeing the alert indicator.
- **SC-008**: 100% of otherwise valid manual edits in validation examples remain saveable even when they create or retain validation alerts.
- **SC-009**: 100% of generation attempts in validation examples can complete even when the resulting schedule contains validation alerts.
- **SC-010**: No automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summary, multi-course generation, session creation, session deletion, session split, session merge, or multiple lecturer/room behavior is available from this feature's workflow.

## Assumptions

- Office staff already have access to the planner UI and permission to view generated Draft Sessions.
- Slices 1-4 are available before this feature is implemented: single-course generation, semester Courses overview, configurable generation constraints, and manual session editing.
- A Draft Session has one lecturer, one room, and one Cohort for this slice.
- Conflict detection is scoped to generated Draft Sessions in the selected semester Courses overview.
- Validation alerts are non-blocking warnings; they do not change the rules for whether generation or manual edits may be saved.
- Currently active allowed generation constraints and Study Type Time Windows already exist from prior slices and are available for evaluating generated Draft Sessions. Custom active generation constraints replace default Study Type Time Window validation for the course-semester.
- Room capacity and Cohort size are available from existing planning data.
- Manual edits remain responsible for their existing validation rules from Slice 4; this slice only adds post-save alerting for unsafe schedules.
