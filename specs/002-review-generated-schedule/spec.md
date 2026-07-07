# Feature Specification: Review Generated Schedule In Planner UI

**Working Branch**: `master`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: "Review Generated Schedule In Planner UI. Create Slice 2 for the planner resource roadmap. Office staff need to review generated Draft Sessions before editing them. The planner UI should show the generated schedule in a simple review view that supports both a weekly calendar-style view and a list view. Users should be able to filter visible sessions by course, Cohort, lecturer, room, and study type. The feature builds on Slice 1, where a single-course draft schedule can already be generated and read. This slice should focus on inspection and review only. It should not include manual session editing, conflict detection, multi-course generation, holiday avoidance, exam scheduling, dashboards, or validation alerts. The goal is that office staff can quickly verify when sessions are planned, who/what they involve, and whether the generated result looks plausible before moving on to manual edits in a later slice."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-07

- Q: Should Slice 2 review only the current selected course's generated schedule, or all generated schedules across courses in the semester? -> A: Review only the current selected course's generated schedule; filters narrow within that available schedule context.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Generated Sessions In A Review View (Priority: P1)

Office staff review the generated Draft Sessions for planning work so they can understand when sessions are scheduled and which planning context each session belongs to before any manual adjustment work begins.

**Why this priority**: This is the core value of Slice 2. A generated schedule is not useful to office staff until they can inspect the proposed sessions clearly and confirm the generated result is plausible.

**Independent Test**: Can be fully tested by opening a course with generated Draft Sessions and confirming that the review view shows each session with date, start time, end time, units, course, Cohort, lecturer, room, and study type context.

**Acceptance Scenarios**:

1. **Given** a course has generated Draft Sessions, **When** office staff open the schedule review view, **Then** they see all generated sessions for that schedule with date, start time, end time, units, course, Cohort, lecturer, room, and study type context.
2. **Given** a generated schedule has no sessions available to display, **When** office staff open the schedule review view, **Then** they see a clear empty state instead of a blank or misleading schedule.
3. **Given** generated sessions span multiple dates, **When** office staff review the schedule, **Then** sessions are presented in chronological order within the selected view.

---

### User Story 2 - Switch Between Weekly And List Review Modes (Priority: P2)

Office staff switch between a weekly calendar-style view and a list view so they can inspect generated sessions either by week layout or by compact chronological detail.

**Why this priority**: Different review tasks need different presentation modes. A weekly view helps staff see distribution across days, while a list view helps them scan all session details quickly.

**Independent Test**: Can be tested by opening a generated schedule, switching between weekly and list modes, and confirming that both modes show the same visible sessions without changing the generated data.

**Acceptance Scenarios**:

1. **Given** generated Draft Sessions are visible in list mode, **When** office staff switch to weekly mode, **Then** the same currently visible sessions appear in a week-based calendar-style layout.
2. **Given** generated Draft Sessions are visible in weekly mode, **When** office staff switch to list mode, **Then** the same currently visible sessions appear in chronological list form.
3. **Given** office staff switch views after applying filters, **When** the new view is shown, **Then** the active filters still determine which sessions are visible.

---

### User Story 3 - Filter Visible Draft Sessions (Priority: P3)

Office staff filter visible Draft Sessions by course, Cohort, lecturer, room, and study type so they can focus on the planning context they are checking.

**Why this priority**: Filtering is necessary once the review screen contains more planning context than a single session table, but it depends on the primary review display being understandable first.

**Independent Test**: Can be tested by using generated schedule data with distinguishable course, Cohort, lecturer, room, and study type values, applying each filter, and confirming that only matching sessions remain visible.

**Acceptance Scenarios**:

1. **Given** generated Draft Sessions are visible, **When** office staff filter by course, **Then** only sessions for the selected course remain visible.
2. **Given** generated Draft Sessions are visible, **When** office staff filter by Cohort, lecturer, room, or study type, **Then** only sessions matching the selected filter value remain visible.
3. **Given** multiple filters are active, **When** office staff review the result, **Then** only sessions matching all active filters remain visible.
4. **Given** active filters match no generated Draft Sessions, **When** the filtered result is displayed, **Then** office staff see a clear no-results state and can change or clear filters.

### Edge Cases

- A generated schedule may not exist yet for the selected course; the review view must clearly communicate that there is nothing to review.
- A generated schedule may contain sessions across multiple weeks; the weekly view must allow staff to inspect each relevant week.
- Filter values may reduce the visible set to zero sessions; the UI must distinguish this from loading or missing data.
- Session details may contain long course, Cohort, lecturer, room, or study type names; the review view must keep the information readable.
- The review view must not allow changes to session date, time, room, length, or generated data in this slice.
- Conflict warnings, capacity validation alerts, holiday warnings, exam sessions, dashboard summaries, and multi-course generation controls are out of scope for this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a planner review view for the current selected course's generated Draft Sessions.
- **FR-002**: System MUST show each visible Draft Session's date, start time, end time, number of units, course, Cohort, lecturer, room, and study type context.
- **FR-003**: System MUST present visible Draft Sessions in chronological order in list mode.
- **FR-004**: System MUST provide a weekly calendar-style mode that groups visible Draft Sessions by week and day.
- **FR-005**: System MUST allow office staff to switch between weekly calendar-style mode and list mode without changing generated schedule data.
- **FR-006**: System MUST preserve active filters when office staff switch between review modes.
- **FR-007**: System MUST allow office staff to confirm or narrow the visible Draft Sessions by the current selected course, without introducing semester-wide multi-course review.
- **FR-008**: System MUST allow office staff to filter visible Draft Sessions by Cohort.
- **FR-009**: System MUST allow office staff to filter visible Draft Sessions by lecturer.
- **FR-010**: System MUST allow office staff to filter visible Draft Sessions by room.
- **FR-011**: System MUST allow office staff to filter visible Draft Sessions by study type.
- **FR-012**: System MUST combine active filters so visible sessions match all selected filter values.
- **FR-013**: System MUST provide a clear empty state when no generated schedule or no generated Draft Sessions are available for review.
- **FR-014**: System MUST provide a clear no-results state when active filters hide all generated Draft Sessions.
- **FR-015**: System MUST allow office staff to clear active filters from the review view.
- **FR-016**: System MUST support review of the current generated Draft Sessions from Slice 1 without requiring manual editing capability.
- **FR-017**: System MUST NOT allow office staff to change session date, start time, room, or session length as part of this feature.
- **FR-018**: System MUST NOT include conflict detection, public holiday avoidance, exam scheduling, multi-course generation, planning dashboard summaries, or validation alerts in this feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Backend behavior MUST be verified with FastAPI-compatible tests, normally using `pytest`.
- **TR-003**: Frontend behavior MUST be verified through React/Vite-appropriate checks, such as build, lint, component, or UI tests.
- **TR-004**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Draft Schedule**: The current generated schedule available for office staff review.
- **Draft Session**: A generated teaching block shown in the review view. Includes date, start time, end time, teaching units, and related planning context.
- **Course**: The teaching offering associated with visible Draft Sessions.
- **Cohort**: The student group associated with visible Draft Sessions and available as a filter.
- **Lecturer**: The assigned teacher associated with visible Draft Sessions and available as a filter.
- **Room**: The assigned teaching location associated with visible Draft Sessions and available as a filter.
- **Study Type**: The study organization category associated with visible Draft Sessions and available as a filter.
- **Review Filter**: A selected course, Cohort, lecturer, room, or study type value used to limit which Draft Sessions are visible.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Office staff can identify the date, time, units, course, Cohort, lecturer, room, and study type for any visible generated Draft Session within 10 seconds during review.
- **SC-002**: Office staff can switch between weekly and list review modes in one interaction without losing the currently visible session set.
- **SC-003**: Office staff can apply or clear any supported filter in no more than two interactions.
- **SC-004**: 100% of supported filters show only sessions matching all active filter values in acceptance test data.
- **SC-005**: 100% of empty, no-schedule, and no-filter-results states provide a clear message that distinguishes the condition.
- **SC-006**: No manual session edit action is available from this feature's review workflow.

## Assumptions

- Office staff already have access to the planner UI and permission to view generated Draft Sessions.
- Slice 1 generation and read behavior is available before this feature is implemented.
- This feature reviews only the current generated schedule for one selected course; semester-wide multi-course review remains out of scope until a later slice.
- Filter options come from generated Draft Session context or the related planning records available to the planner.
- Weekly review means a simple calendar-style grouping by week and day, not a polished drag-and-drop calendar.
- Manual editing, conflict detection, validation alerts, public holidays, exams, and dashboard-style summaries remain separate future slices.
