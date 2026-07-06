# Feature Specification: Draft Course Schedule

**Working Branch**: `master`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "Create a feature spec for explicit draft schedule generation for one course in a university resource planner. The system should allow an admin to trigger generation of a draft teaching schedule for one course. The course has a total number of teaching units, where one unit is 45 minutes. Sessions must include 10-minute breaks between units. The lecturer has a preferred session size range, and the generator should use the maximum preferred session size by default. If the final remaining units would be below the minimum preferred session size, the previous session should be reduced so the final session reaches the minimum where possible. The first version supports one course, one lecturer, one room, one Cohort, one semester date range, and one study type. The study type defines one or more allowed weekday/time windows. The generated schedule should place sessions once per week by default and keep the same weekday and start time where possible. If there are not enough valid weeks, the generator may place multiple sessions in the same week. If the course still cannot be fully scheduled, the system must inform the admin and not silently create an incomplete plan. Room capacity is a hard validation rule. Public holiday avoidance, exams, multi-course optimization, multiple lecturers, multiple rooms, cross-course conflicts, manual drag/drop editing, and calendar UI polish are out of scope."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-06

- Q: When an admin generates a draft schedule for a course that already has generated draft sessions, what should happen? -> A: A new generation replaces the previous draft sessions for that course.
- Q: When multiple Study Type Time Windows are valid at the start of scheduling, how should the generator choose the preferred recurring slot? -> A: The admin selects one Study Type Time Window at generation time.
- Q: When the generator needs multiple sessions in one week, may it place more than one session on the same day? -> A: Multiple sessions may be placed in the same week, but at most one session per day.
- Q: If the admin-selected Study Type Time Window cannot fit a generated session, but another allowed window can, what should happen? -> A: The system tries another allowed Study Type Time Window before failing.
- Q: What level of detail should the admin-facing failure message provide when generation fails? -> A: The system shows all detected reasons at once.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Complete Draft Schedule (Priority: P1)

An admin generates a draft teaching schedule for one course so the course's required teaching units are split into valid teaching sessions across the semester.

**Why this priority**: This is the core planning value of the feature. Without a complete generated schedule, admins still have to manually calculate session dates, lengths, and time slots.

**Independent Test**: Can be fully tested by providing a valid course, lecturer preference, Cohort, room, semester, and Study Type Time Windows, then triggering generation and confirming that the resulting sessions cover all required units and satisfy the placement rules.

**Acceptance Scenarios**:

1. **Given** a course with 20 teaching units, a lecturer preference of 2 to 4 units per session, a valid room, a Cohort, a semester with enough valid weeks, and a Study Type Time Window that can fit a 4-unit session, **When** the admin triggers draft schedule generation, **Then** the system creates 5 sessions of 4 units each.
2. **Given** a course with 18 teaching units, a lecturer preference of 3 to 4 units per session, and valid planning inputs, **When** the admin triggers draft schedule generation, **Then** the system creates sessions whose unit distribution is 4, 4, 4, 3, and 3.
3. **Given** valid planning inputs, a selected Study Type Time Window, and enough valid weeks, **When** the admin triggers draft schedule generation, **Then** the system places sessions once per week by default and keeps the selected window's weekday and start time where possible.

---

### User Story 2 - Respect Study Type Time Windows (Priority: P2)

An admin relies on the generated schedule to use only the weekday and time windows defined for the course's study type.

**Why this priority**: Study Type Time Windows are a central scheduling constraint. A generated schedule that ignores them would not be usable for real semester planning.

**Independent Test**: Can be tested by defining one or more Study Type Time Windows, generating a schedule, and confirming that every session starts and ends within an allowed Study Type Time Window.

**Acceptance Scenarios**:

1. **Given** a study type with Friday 17:00-22:00 and Saturday 08:00-16:00 windows, **When** the admin generates a draft schedule for a course using that study type, **Then** every generated session occurs only within one of those windows.
2. **Given** a study type with multiple allowed windows in the same week, **When** the default weekly placement does not provide enough valid dates to complete the course, **Then** the system may place more than one session in a week using available allowed windows, with no more than one generated session on the same day.
3. **Given** a generated session of 4 teaching units, **When** the system determines its end time, **Then** the session duration includes four 45-minute units and three 10-minute breaks.
4. **Given** the selected Study Type Time Window cannot fit a generated session but another allowed window can, **When** the admin triggers draft schedule generation, **Then** the system uses another allowed window before failing generation.

---

### User Story 3 - Block Invalid Generation Requests (Priority: P3)

An admin receives clear feedback when a draft schedule cannot be generated because required constraints are not satisfied.

**Why this priority**: The system must not silently create unusable or incomplete schedules, especially when room capacity or available time windows make the request invalid.

**Independent Test**: Can be tested by providing invalid capacity or impossible scheduling inputs and confirming that no draft schedule is created and the admin receives a clear reason.

**Acceptance Scenarios**:

1. **Given** a room with capacity 40 and a Cohort with 45 students, **When** the admin triggers draft schedule generation, **Then** the system rejects generation and explains that the room capacity is insufficient.
2. **Given** valid course and capacity inputs but not enough allowed Study Type Time Windows within the semester to place all required sessions, **When** the admin triggers draft schedule generation, **Then** the system reports that the course cannot be fully scheduled and does not create a partial draft schedule.
3. **Given** a lecturer preference where the minimum session units are greater than the maximum session units, **When** the admin triggers draft schedule generation, **Then** the system rejects generation and explains that the session preference is invalid.
4. **Given** a generation request with more than one invalid condition, **When** the admin triggers draft schedule generation, **Then** the system reports all detected failure reasons together.

### Edge Cases

- If the total teaching units divide evenly by the maximum preferred session size, all generated sessions use the maximum size.
- If the final remaining units would be below the minimum preferred session size, the system reduces the previous session enough to make the final session valid where mathematically possible.
- If a single preferred session cannot fit into any allowed Study Type Time Window, generation fails with a clear reason.
- If a semester contains too few valid weeks for once-per-week placement, the system attempts multiple sessions in the same week before failing, but does not place more than one generated session on the same day.
- If multiple windows are available, the system prioritizes the admin-selected window and uses another allowed window only when needed to complete the schedule.
- Public holidays are not considered by this feature and may appear in generated schedules until holiday handling is implemented separately.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow an admin to explicitly trigger draft schedule generation for one course.
- **FR-002**: System MUST generate a draft schedule only from one course, one lecturer, one room, one Cohort, one semester date range, and one study type for this feature.
- **FR-003**: System MUST treat one teaching unit as 45 minutes.
- **FR-004**: System MUST include 10-minute breaks between teaching units when calculating session duration.
- **FR-005**: System MUST use the lecturer's maximum preferred session size as the default generated session size.
- **FR-006**: System MUST ensure every generated session respects the lecturer's preferred minimum and maximum session units, except where generation fails because no valid distribution exists.
- **FR-007**: System MUST adjust the previous session when the final remaining units would otherwise be below the lecturer's minimum preferred session size and an adjusted valid distribution is possible.
- **FR-008**: System MUST place generated sessions within the semester start and end dates.
- **FR-009**: System MUST place generated sessions only inside Study Type Time Windows defined by the course's study type.
- **FR-010**: System MUST support more than one allowed Study Type Time Window for a study type, including multiple windows in the same week.
- **FR-011**: System MUST place sessions once per week by default when enough valid weeks and windows are available.
- **FR-012**: System MUST allow the admin to select one Study Type Time Window as the preferred recurring slot for generation.
- **FR-013**: System MUST keep the selected Study Type Time Window's weekday and start time across generated sessions where possible.
- **FR-014**: System MUST place multiple sessions in one week when once-per-week placement cannot fully schedule the course within the semester.
- **FR-015**: System MUST place no more than one generated session for the course on the same day.
- **FR-016**: System MUST try another allowed Study Type Time Window before failing when the selected window cannot fit a generated session.
- **FR-017**: System MUST reject generation when the assigned room capacity is lower than the Cohort student count.
- **FR-018**: System MUST not create a partial draft schedule when the course cannot be fully scheduled.
- **FR-019**: System MUST provide all detected admin-facing failure reasons when generation is rejected or cannot complete the full course schedule.
- **FR-020**: System MUST replace any existing generated draft sessions for the same course when the admin successfully generates a new draft schedule.
- **FR-021**: System MUST exclude public holiday avoidance, exam scheduling, multi-course optimization, multiple lecturers per course, multiple rooms per course, cross-course conflicts, manual drag/drop editing, and calendar UI polish from this feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Schedule generation and validation behavior MUST be verified with automated service-level tests.
- **TR-003**: Any admin-facing generation interaction implemented for this feature MUST be verified through appropriate user-interface checks.
- **TR-004**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Course**: The teaching offering to be scheduled. Includes the total number of teaching units and the lecturer's preferred minimum and maximum units per session.
- **Lecturer**: The person assigned to teach the course for this feature.
- **Cohort**: The fixed student group attending the course. Includes the student count used for room capacity validation.
- **Room**: The assigned teaching location. Includes capacity used to determine whether the room can host the Cohort.
- **Semester**: The planning date range within which all generated sessions must occur.
- **Study Type**: The category of study organization that defines allowed weekday/time windows for scheduled teaching.
- **Study Type Time Window**: An allowed weekday and time interval in which sessions for the study type may be placed.
- **Draft Schedule**: The current generated draft for one course. Owns the generated Draft Sessions and is replaced when the admin successfully regenerates the course schedule.
- **Draft Session**: A proposed scheduled teaching block for the course, with date, start time, end time, and number of teaching units.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admins can generate a complete draft schedule for a valid single-course planning case in under 1 minute.
- **SC-002**: 100% of generated sessions in validation examples occur within the semester date range and allowed Study Type Time Windows.
- **SC-003**: 100% of generated sessions in validation examples include correct duration calculations for 45-minute units and 10-minute breaks.
- **SC-004**: 100% of room capacity violations are blocked before a draft schedule is created.
- **SC-005**: In tested cases where once-per-week placement is insufficient but weekly capacity exists, the system successfully completes the schedule by placing multiple sessions in one week.
- **SC-006**: In tested impossible scheduling cases, the system produces no partial schedule and provides a clear reason that an admin can act on.

## Assumptions

- The admin already has permission to manage planning data and trigger draft schedule generation.
- The course, lecturer, room, Cohort, semester, study type, and time windows already exist or are provided as inputs before generation is triggered.
- A session's breaks occur only between units, so a 1-unit session has no break, a 2-unit session has one break, and a 4-unit session has three breaks.
- When several valid placements exist, the system favors the admin-selected Study Type Time Window and stable weekly repetition over distributing sessions across varied days and times.
- Time windows are interpreted in the institution's local time.
- Public holidays may be scheduled over in this feature because holiday avoidance is intentionally out of scope.
