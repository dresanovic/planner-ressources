# Feature Specification: Configurable Generation Constraints

**Working Branch**: `master`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "Slice 3: Configurable Generation Constraints. Office staff can configure generation constraints for a selected course before generating a draft schedule. The planning period defaults to the selected semester start and end dates. Users can optionally override the planning period with a custom start date and custom end date. Users can define one or more allowed weekly teaching windows. Each allowed teaching window includes weekday, start time, and end time. If users do not customize constraints, the system uses defaults from the selected semester and the course study type's default time windows. The generator must use the configured planning period and allowed teaching windows when creating Draft Sessions. The UI should make clear that these are generation constraints, not review filters. Manual session editing, conflict detection, multi-course generation, holiday avoidance, exam scheduling, dashboards or validation alerts, optimization across multiple courses, and multiple lecturers or multiple rooms per course are out of scope."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-07

- Q: Should custom constraints be saved after generation? -> A: Save custom constraints for the selected course and selected semester and reload them the next time staff generate for that course-semester combination.
- Q: What scope should saved custom constraints use? -> A: Save custom constraints per selected course and selected semester.
- Q: When should custom constraints be saved? -> A: Save custom constraints only after draft schedule generation succeeds.
- Q: What should clearing custom constraints do? -> A: Delete saved constraints for that course and semester and restore semester and study type defaults.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate With Default Constraints (Priority: P1)

Office staff generate a draft schedule for a selected course without customizing constraints, relying on the system to use the selected semester dates and the course study type's default teaching windows unless saved course-semester-specific constraints already exist.

**Why this priority**: Defaults preserve the existing single-course generation workflow while making the constraint model explicit. Office staff should not have to enter dates and weekly windows for routine generation cases.

**Independent Test**: Can be fully tested by selecting a course with no saved custom constraints, a semester, and study type defaults, leaving generation constraints unchanged, generating a draft schedule, and confirming every Draft Session uses the semester date range and one of the study type's default weekly teaching windows.

**Acceptance Scenarios**:

1. **Given** a selected course has a selected semester with start and end dates and a study type with default teaching windows, **When** office staff open the generation controls, **Then** the planning period is prefilled with the semester start and end dates and the allowed teaching windows are prefilled from the study type defaults.
2. **Given** office staff leave the default generation constraints unchanged, **When** they generate a draft schedule, **Then** every Draft Session occurs within the semester planning period and inside one of the default study type teaching windows.
3. **Given** default constraints are visible before generation, **When** office staff review the controls, **Then** the UI labels them as generation constraints used for creating the draft schedule, not as filters for hiding or showing already generated sessions.
4. **Given** saved custom constraints exist for the selected course and selected semester, **When** office staff open the generation controls for that course and semester again, **Then** the saved custom constraints are loaded instead of the semester and study type defaults.

---

### User Story 2 - Override The Planning Period (Priority: P2)

Office staff override the default semester planning period for a selected course so generated Draft Sessions are limited to a custom start date and custom end date.

**Why this priority**: Real planning often needs a narrower teaching period than the full semester. Date overrides give staff control without changing the underlying semester definition.

**Independent Test**: Can be tested by entering a custom planning start and end date inside the selected semester, generating a draft schedule, and confirming no Draft Session falls outside the custom period.

**Acceptance Scenarios**:

1. **Given** the generation controls show semester defaults, **When** office staff enter a custom planning start date and custom planning end date, **Then** the custom dates are shown as the active planning period for the next generation request.
2. **Given** a valid custom planning period is active, **When** office staff generate a draft schedule, **Then** every Draft Session occurs on or after the custom start date and on or before the custom end date.
3. **Given** office staff clear their custom planning period, **When** the generation controls return to defaults, **Then** the selected semester start and end dates become the active planning period again and the saved custom constraint set for that course-semester combination is deleted.

---

### User Story 3 - Configure Allowed Weekly Teaching Windows (Priority: P3)

Office staff define one or more allowed weekly teaching windows for a selected course so the generator only places Draft Sessions on allowed weekdays and within allowed time ranges.

**Why this priority**: Weekly teaching windows are the main scheduling constraint Slice 3 adds beyond the existing selected-window behavior. Multiple windows allow staff to express practical availability such as Monday morning and Wednesday midday.

**Independent Test**: Can be tested by configuring at least two allowed weekly teaching windows, generating a draft schedule, and confirming every Draft Session starts and ends within one of those configured windows.

**Acceptance Scenarios**:

1. **Given** generation controls are available for a selected course, **When** office staff add allowed teaching windows for Monday 08:00-12:00 and Wednesday 09:00-13:00, **Then** both windows are shown as active generation constraints.
2. **Given** custom allowed teaching windows are active, **When** office staff generate a draft schedule, **Then** every Draft Session occurs only on one of the configured weekdays and within the configured time ranges.
3. **Given** office staff remove all custom teaching windows, **When** the generation controls return to defaults, **Then** the course study type's default teaching windows become the active allowed windows again and the saved custom constraint set for that course-semester combination is deleted.

### Edge Cases

- If office staff enter a custom planning start date after the custom end date, generation must be blocked and the staff member must see a clear message explaining that the planning period is invalid.
- If office staff enter custom planning dates outside the selected semester, generation must be blocked because Slice 3 narrows or matches the semester period rather than redefining the semester.
- If no allowed weekly teaching window is available from either custom constraints or study type defaults, generation must be blocked with a clear message that at least one allowed teaching window is required.
- If an allowed teaching window has an end time equal to or earlier than its start time, generation must be blocked and the invalid window must be identifiable to office staff.
- If the configured planning period and allowed windows cannot fit all required sessions, generation must not create a partial draft schedule and must explain that the constraints are too restrictive.
- If generation fails or is blocked, the attempted custom constraints must not replace the saved custom constraints for that course-semester combination.
- If office staff clear custom constraints, saved custom constraints for that course-semester combination must be deleted and the semester and study type defaults must become active.
- If custom constraints are changed after a draft schedule already exists, the existing Draft Sessions remain unchanged until office staff explicitly generate a new draft schedule.
- Generation constraints must not hide already generated Draft Sessions in the review view; review filtering remains the responsibility of Slice 2.
- Manual session editing, conflict detection, multi-course generation, holiday avoidance, exam scheduling, dashboards, validation alerts, multi-course optimization, multiple lecturers, and multiple rooms remain out of scope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide generation constraint controls for the currently selected course before draft schedule generation is triggered.
- **FR-002**: System MUST default the active planning period to the selected semester start date and selected semester end date.
- **FR-003**: Users MUST be able to override the active planning period with a custom start date and custom end date.
- **FR-004**: System MUST allow users to clear custom planning period dates, delete the saved custom constraint set for the selected course and selected semester, and return to the selected semester defaults.
- **FR-005**: System MUST save custom generation constraints for the selected course and selected semester only after draft schedule generation succeeds.
- **FR-006**: System MUST reload saved custom generation constraints the next time office staff open generation controls for the same selected course and selected semester.
- **FR-007**: System MUST prevent generation when the active planning period start date is after the active planning period end date.
- **FR-008**: System MUST prevent generation when a custom planning period falls outside the selected semester date range.
- **FR-009**: System MUST default allowed weekly teaching windows to the selected course study type's default time windows when users have not customized windows and no saved custom windows exist for the selected course and selected semester.
- **FR-010**: Users MUST be able to define one or more custom allowed weekly teaching windows for generation.
- **FR-011**: Each allowed weekly teaching window MUST include a weekday, a start time, and an end time.
- **FR-012**: System MUST prevent generation when any active allowed weekly teaching window has an end time that is equal to or earlier than its start time.
- **FR-013**: System MUST prevent generation when there are no active allowed weekly teaching windows.
- **FR-014**: Users MUST be able to remove custom allowed weekly teaching windows, delete the saved custom constraint set for the selected course and selected semester, and return to the course study type's default time windows.
- **FR-015**: System MUST clearly distinguish generation constraints from review filters in labels, grouping, and workflow placement.
- **FR-016**: System MUST send the active planning period and active allowed weekly teaching windows into draft schedule generation for the selected course.
- **FR-017**: System MUST create Draft Sessions only within the active planning period.
- **FR-018**: System MUST create Draft Sessions only within the active allowed weekly teaching windows.
- **FR-019**: System MUST not create a partial draft schedule when the configured constraints cannot accommodate all required sessions.
- **FR-020**: System MUST leave existing Draft Sessions unchanged when users modify generation constraints without triggering generation.
- **FR-021**: System MUST continue to support the single-course generation scope from Slice 1 and the review-only planner UI behavior from Slice 2.
- **FR-022**: System MUST NOT include manual session editing, conflict detection, multi-course generation, holiday avoidance, exam scheduling, dashboards or validation alerts, optimization across multiple courses, or multiple lecturers or multiple rooms per course in this feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Backend generation and validation behavior MUST be verified with FastAPI-compatible tests, normally using `pytest`.
- **TR-003**: Frontend generation constraint controls MUST be verified through React/Vite-appropriate checks, such as build, lint, component, or UI tests.
- **TR-004**: Cross-stack behavior MUST be verified for the contract that passes active planning period and allowed weekly teaching windows into generation.
- **TR-005**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Course**: The selected teaching offering for which office staff configure generation constraints and generate Draft Sessions.
- **Semester**: The academic date range that provides the default planning period and bounds any custom planning period.
- **Study Type**: The course's study organization category that provides default allowed weekly teaching windows.
- **Generation Constraints**: The active planning period and active allowed weekly teaching windows used by the generator for the next draft schedule creation. Custom generation constraints are saved for the selected course and selected semester after successful generation, reloaded for later generation of the same course-semester combination, and deleted when office staff clear them.
- **Planning Period**: The start date and end date within which generated Draft Sessions may be placed.
- **Allowed Weekly Teaching Window**: A weekday and time interval during which generated Draft Sessions may be placed.
- **Draft Schedule**: The generated schedule for the selected course, created from the active generation constraints when office staff trigger generation.
- **Draft Session**: A generated teaching block with a date, start time, end time, and teaching units that must satisfy the active generation constraints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Office staff can generate a draft schedule using default semester and study type constraints without entering any additional constraint values.
- **SC-002**: Office staff can set or clear a custom planning period in no more than three interactions after opening the generation controls.
- **SC-003**: Office staff can add a weekly teaching window with weekday, start time, and end time in no more than four interactions.
- **SC-004**: 100% of generated Draft Sessions in validation examples occur within the active planning period used for generation.
- **SC-005**: 100% of generated Draft Sessions in validation examples start and end within one of the active allowed weekly teaching windows.
- **SC-006**: 100% of invalid planning periods, invalid teaching windows, and missing teaching windows are blocked before Draft Sessions are created.
- **SC-007**: At least 90% of office staff in review or usability checks can correctly identify that the controls affect future generation, not the currently visible review results.
- **SC-008**: In impossible scheduling examples caused by restrictive constraints, the system creates no partial draft schedule and provides an actionable explanation.
- **SC-009**: 100% of saved custom constraints in validation examples reload when office staff return to generation controls for the same selected course and selected semester.
- **SC-010**: 100% of failed or blocked generation attempts in validation examples leave previously saved custom constraints unchanged.
- **SC-011**: 100% of cleared saved constraints in validation examples are absent the next time office staff open generation controls for the same selected course and selected semester.

## Assumptions

- Office staff already have access to the planner UI and permission to generate draft schedules for a selected course.
- Slice 1 single-course draft schedule generation is available before this feature is implemented.
- Slice 2 planner review UI and planning option loading are available before this feature is implemented.
- A custom planning period may narrow or match the selected semester period but may not extend outside it.
- Time values are interpreted in the institution's local time.
- Allowed weekly teaching windows describe recurring weekly availability and do not account for public holidays in this slice.
- Saved custom constraints affect later generation requests for the same selected course and selected semester but do not automatically edit or regenerate existing Draft Sessions.
- Clearing custom constraints is a deliberate reset to selected semester and study type defaults for the same course-semester combination.
- Clearing either custom planning dates or custom teaching windows resets the entire saved course-semester constraint set.
