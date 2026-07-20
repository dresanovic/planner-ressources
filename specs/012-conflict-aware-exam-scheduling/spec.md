# Feature Specification: FS-012 Conflict-Aware Exam Scheduling

**Working Branch**: `master`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Generate and manage exams only for explicitly enabled courses, without teaching/exam resource conflicts. Include exam configuration, conflict-aware placement, resource availability, holidays, planner review and correction, and understandable failures."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-20

- Q: How many historical and active exam records may a course-semester have? → A: Unlimited past exam records; only one exam dated today or later may be active per course-semester.
- Q: Once an exam is in the past, may the planner change or remove it? → A: Past exams may be corrected or deleted using the same validation, confirmation, and stale-state safeguards as active exams.
- Q: What happens when a planner places an exam outside its configured date range? → A: The range is only a recommendation for automatic generation; planners may override it without changing the saved recommendation, but no exam may start before the final lecture ends.
- Q: What happens to an exam's configuration after that exam becomes past? → A: The past exam preserves its own saved details, and preparing the next exam starts with a fresh current configuration.
- Q: How does the planner specify an exam's type? → A: The planner enters a required free-text type for each exam; FS-012 adds no fixed or planner-managed type catalog.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Exam Requirements Explicitly (Priority: P1)

A planner explicitly enables the next exam for a course-semester and records the information needed to determine whether it can be placed validly. A course-semester may retain any number of past exams but may have only one active exam dated today or later. The normal timing window is one to two weeks after the course's final teaching session, and the planner may override that window. Courses that are not enabled remain teaching-only and receive no generated exam.

**Why this priority**: Explicit, valid configuration is the control that prevents unintended exams and supplies every hard constraint needed by generation.

**Independent Test**: Prepare one course-semester with a final teaching session, several past exams, and no active exam, save a complete enabled next-exam configuration, leave another course disabled, reload the planning state, and verify that the enabled configuration is eligible, its default recommendation is derived correctly, every past exam remains unchanged, and the disabled course has no exam requirement or missing-exam warning.

**Acceptance Scenarios**:

1. **Given** a course has no exam requirement, **When** the planner reviews its exam-planning state, **Then** no exam configuration, proposed exam, or missing-exam warning is shown for that course.
2. **Given** a course-semester has no active exam and has a final teaching session, **When** the planner enables its next exam and supplies a complete valid configuration, **Then** the configuration is saved and becomes eligible for generation.
3. **Given** a course-semester has one or more past exams but no active exam, **When** the planner enables and configures its next exam, **Then** the new configuration is accepted and every past exam remains unchanged.
4. **Given** the previous active exam has become past, **When** the planner prepares the next exam, **Then** a fresh current configuration is started and no value change in it alters the past exam's saved details.
5. **Given** a course-semester already has an exam dated today or later, **When** the planner attempts to enable, edit, disable, replace, or freshen its consumed current configuration, **Then** the action is rejected, the configuration remains read-only, the existing active exam remains unchanged, and the planner is told to correct or delete the active exam or wait until it becomes past.
6. **Given** an enabled course has no active exam and has a valid unscheduled current exam configuration, **When** the planner changes its duration, recommended date range, required room capacity, free-text exam type, or responsible lecturer, **Then** subsequent planning uses its saved current values without changing any active or past exam session.
7. **Given** an exam configuration has a missing required value, a blank or whitespace-only exam type, a non-positive duration, a non-positive capacity, an override end date before its start date, or an unavailable referenced course or lecturer, **When** the planner attempts to save it, **Then** the configuration is not enabled and every invalid value is identified.
8. **Given** a course has a final teaching session and the planner has not changed the next exam's timing preference, **When** its configuration is prepared, **Then** the recommended date range defaults to the period from seven through fourteen calendar days after the final teaching session.
9. **Given** the next exam has the default recommended date range, **When** the planner changes it to any internally valid earlier or later range, including one partly or wholly before the final teaching session, **Then** the recommendation is saved and preferred only where it overlaps hard-valid placement dates; no exam is placed before the final teaching session.
10. **Given** a course has no saved teaching session, **When** the planner saves a complete enabled next-exam configuration, **Then** the configuration is retained as unscheduled, its derived default recommendation is unavailable, and it is identified as ineligible for placement until a final teaching session exists.

---

### User Story 2 - Generate Valid Exams or Understand Failure (Priority: P1)

A planner starts exam generation for explicitly enabled course-semesters that have no active exam and receives either one valid active exam or a clear failure explanation for each selected course-semester.

**Why this priority**: Valid conflict-aware placement is the principal scheduling outcome of this slice, and understandable failure keeps the planner in control when no feasible placement exists.

**Independent Test**: Prepare enabled course-semesters with feasible and infeasible current exam configurations, a disabled course, a course with an existing active exam, past exams, teaching sessions, holidays, resource availability, and room capacities; run generation and verify each eligible course receives exactly one permitted outcome while disabled courses, existing active exams, past exams, and prior saved work remain unchanged.

**Acceptance Scenarios**:

1. **Given** an enabled course-semester has no active exam and its current exam configuration has at least one feasible placement within the automatic proposal domain, **When** exam generation completes, **Then** one active exam is scheduled with its configured duration, type, responsible lecturer, cohort, and a capacity-sufficient eligible room, preferably inside its recommended date range.
2. **Given** an exam uses its default timing recommendation and the course's final teaching session is known, **When** generation evaluates that exam, **Then** it prefers placements from seven through fourteen calendar days after the final teaching session.
3. **Given** the planner has changed an exam's recommended date range to less than seven days after teaching or more than fourteen days after teaching, **When** generation evaluates that exam, **Then** it prefers the changed range but may use another hard-constraint-valid placement after the final teaching session when no placement inside the recommendation is feasible.
4. **Given** candidate placements overlap teaching or exam sessions for the same lecturer, room, or cohort, **When** generation evaluates them, **Then** every overlapping placement is rejected.
5. **Given** candidate placements overlap lecturer or room unavailability, fall on an institution-wide holiday, use an insufficient room, or start before the final teaching session ends, **When** generation evaluates them, **Then** every such placement is rejected regardless of whether it falls inside the recommended date range.
6. **Given** one or more enabled course-semesters have no feasible placement, **When** generation completes, **Then** each affected course receives a failure reason identifying its current exam configuration, substantiated blocking constraint categories, and relevant dates or resources, while no invalid exam is saved.
7. **Given** selected enabled courses include both feasible and infeasible current exam configurations, **When** generation completes, **Then** valid active exams may be retained for feasible courses and clear failures are retained for infeasible courses without presenting the overall operation as wholly successful.
8. **Given** a disabled course is included in the same planning context, **When** exam generation runs, **Then** no exam is created, changed, or reported as missing for that course.
9. **Given** relevant teaching sessions, exams, holiday data, availability, capacity, eligibility, or exam configuration changes after generation starts, **When** a prepared result is no longer valid against the current saved planning state, **Then** the stale result is not saved and the planner is asked to review or retry.
10. **Given** a selected course-semester already has an exam dated today or later, **When** generation runs, **Then** no additional exam is created, the active exam is not moved or replaced, and past exams remain unchanged.
11. **Given** an enabled course has no active Study Type Time Window from which an automatic start time can be proposed, **When** generation runs, **Then** no exam is created and the course receives an `AUTOMATIC_START_TIME_UNAVAILABLE` failure that explains how the planner can correct the planning inputs or place the exam manually.
---

### User Story 3 - Create, Review, Correct, and Delete Exams Safely (Priority: P2)

A planner can distinguish exams from teaching sessions, inspect their defining details and conflict context, manually create an exam session for a configured exam, correct its placement, or deliberately delete it.

**Why this priority**: Automatic placement needs a complete planner-controlled management path, but every saved exam and destructive action must preserve the guarantees that make the schedule usable.

**Independent Test**: Manually create a valid exam session for an unplaced configuration, review it alongside teaching sessions, correct it to a valid alternative, reject invalid placements, delete it after confirming the exact consequence, and verify that all affected exam outcomes and conflict context refresh while unrelated sessions remain unchanged.

**Acceptance Scenarios**:

1. **Given** a semester contains teaching and exam sessions, **When** the planner reviews the schedule, **Then** each exam is visibly distinguishable and exposes its course, type, duration, date and time, responsible lecturer, cohort, room, and configuration context.
2. **Given** an enabled course-semester has a current exam configuration and no active exam, **When** the planner supplies a valid date, time, lecturer, and room and creates it manually, **Then** exactly one active exam session is saved without changing any teaching session or past exam.
3. **Given** a saved active or past exam has a valid alternative placement, **When** the planner changes its date, time, responsible lecturer, or room and saves, **Then** the corrected exam replaces only that exam placement and remains valid against every exam hard constraint and the one-active-exam rule.
4. **Given** a proposed manual creation or correction falls outside the recommended date range but starts after the final teaching session and satisfies every resource, conflict, capacity, availability, holiday, and semester constraint, **When** the planner saves it, **Then** the exam is retained as an explicit planner override and the saved recommendation remains unchanged.
5. **Given** a proposed manual creation or correction conflicts with teaching or another exam for the lecturer, room, or cohort, violates capacity or availability, falls on a holiday, or starts before the course's final teaching session ends, **When** the planner attempts to save it, **Then** the change is rejected, prior state remains unchanged, and every blocking reason is identified.
6. **Given** a saved active or past exam exists, **When** the planner requests deletion, **Then** a confirmation identifies the course, exam configuration, scheduled date and time, whether the exam is active or past, and the exact post-deletion consequence.
7. **Given** an exam-deletion confirmation is displayed, **When** the planner cancels, **Then** no exam, teaching session, configuration, failure outcome, or conflict context changes.
8. **Given** the planner confirms deletion of an unchanged active exam, **When** deletion succeeds, **Then** only that exam session is removed, its current configuration remains enabled and visibly unscheduled, and all past and unrelated sessions remain unchanged.
9. **Given** the planner confirms deletion of an unchanged past exam, **When** deletion succeeds, **Then** only that historical exam session is removed and the current exam configuration, any active exam, other past exams, and all unrelated sessions remain unchanged.
10. **Given** an exam or a related planning input changed after the editor or deletion confirmation was opened, **When** the planner submits a stale creation, correction, or deletion, **Then** current state is preserved and the planner is prompted to review the refreshed exam and conflict context before trying again.
11. **Given** a valid manual creation, correction, or deletion succeeds, **When** the save completes, **Then** exam outcomes and conflict and availability information for the affected semester reflect the saved current state without requiring the planner to leave and reopen it.
12. **Given** a course-semester already has an exam dated today or later, **When** the planner attempts to manually create another active exam, **Then** the action is rejected and every active and past exam remains unchanged.

### Edge Cases

- An enabled course has no teaching session from which to derive the default exam window or enforce the hard earliest time. Generation must not invent a final-teaching date and must explain that the required timing anchor is unavailable.
- The last teaching session is moved after an exam has been generated. The existing exam is preserved for review, but it is no longer presented as valid if it now starts before that teaching session ends.
- The configured recommended date range extends partly or wholly outside the semester. Automatic generation prefers only its in-semester portion but may use another hard-constraint-valid in-semester date after the final teaching session.
- A duration would cross midnight, a holiday boundary, a resource-availability boundary, or the end of the semester. The placement is invalid rather than shortened.
- A lecturer or room is available for only part of the requested duration. Partial availability is insufficient.
- Several capacity-sufficient rooms exist, but all are unavailable or conflicting. The failure distinguishes lack of feasible availability from lack of capacity.
- A room's capacity or availability changes after an exam is saved. The exam remains visible and unchanged but is identified as currently invalid until the planner corrects it.
- A holiday is added on the date of a saved exam. The exam remains visible and unchanged but is identified as currently invalid; holiday maintenance does not move or delete it.
- Two courses share a cohort or responsible lecturer and each can be placed separately but not simultaneously. Generation must choose non-overlapping placements or report the course-specific unresolved outcome.
- Back-to-back sessions are not overlapping when one ends exactly when the next begins and all availability boundaries permit both.
- A failure has several simultaneous causes. The planner sees all substantiated blocking categories useful for correction, without unsupported claims that any one cause was decisive.
- A generation or manual save fails. Existing teaching sessions, other exams, course configuration, and resource data remain unchanged.
- A planner attempts to create a second active exam for a course-semester. Creation is rejected without changing the existing active exam or any past exam.
- A planner reviews an exam configuration that already has a saved generated, manually created, or manually corrected exam. No generation action is available for that configuration.
- The current date advances beyond an active exam's date. That exam becomes a past exam, remains reviewable, and no longer prevents the planner from enabling and scheduling the next exam.
- Past exams remain historical schedule records and do not count against the one-active-exam limit.
- When the next exam is prepared, its fresh current configuration does not inherit or remain linked to values that could change a past exam's saved details.
- Correcting a past exam onto today or a future date is rejected when another active exam already exists for the course-semester.
- Deleting one past exam does not alter the current exam configuration, an active exam, or any other past exam.
- A planner places an exam outside the recommended date range. The placement is allowed when every hard constraint is satisfied, is visibly identifiable as outside the recommendation, and does not silently change the recommendation.

### Scope Boundaries

This slice includes explicit per-course-semester enablement of the next exam; unlimited retained past exam records; at most one exam dated today or later per course-semester; conflict-aware exam placement; hard enforcement of timing, lecturer, room, cohort, capacity, availability, and institution-holiday constraints; distinguishable exam review; planner correction; current validity feedback; and understandable generation failures.

This slice does not include student registration, exam grading, external exam systems, broad invigilator or supervision rosters beyond the responsible lecturer, lecturer editing, publication lifecycle, external room booking, or a redesign of the calendar-centered workspace. It does not reopen the teaching-generation, resource-administration, or holiday-administration behavior established by its dependencies.
It also does not introduce a fixed or planner-maintained exam-type catalog.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow the planner to explicitly enable or leave disabled the next exam for each course-semester planning context.
- **FR-002**: A course without an explicitly enabled and valid exam requirement MUST NOT receive a generated exam and MUST NOT be reported as missing an exam.
- **FR-003**: The current exam configuration MUST define a planner-visible identifier, a positive duration, a positive whole-number required room capacity, one non-empty planner-entered free-text exam type, and one current responsible lecturer. It MAY define paired inclusive recommended start and end overrides with the end not before the start; otherwise effective recommendation dates are derived only after a final teaching anchor exists.
- **FR-004**: The system MUST reject invalid or incomplete planner-entered exam configuration, including a blank or whitespace-only exam type or an invalid override pair, without enabling it or partially changing its previously saved values and MUST identify every value requiring correction. Absence of a final teaching session is placement ineligibility rather than an invalid planner-entered configuration.
- **FR-005**: A course-semester MAY retain any number of past exam sessions but MUST have no more than one active exam session whose institution-local scheduled calendar date is today or later.
- **FR-006**: When an exam becomes past, it MUST retain its own saved duration, exam type, date and time, lecturer, cohort, room, required capacity, recommendation context, and validity context independently of later current configurations; preparing the next exam MUST start a fresh current configuration whose changes affect only subsequent planning and MUST NOT silently change, move, replace, or delete any active or past exam.
- **FR-007**: While a related active exam exists, the consumed current configuration MUST be read-only. An attempt to edit, disable, replace, remove, or freshen it MUST NOT silently change or delete that exam and MUST tell the planner to correct or delete the active exam, or wait until it becomes past, before preparing the next configuration.
- **FR-008**: When a final teaching session exists and the planner has not changed an exam's recommended date range, the system MUST default that recommendation to the period from seven through fourteen calendar days after the end date of the chronologically last saved teaching session for the same course-semester; while no final teaching session exists, the enabled configuration MUST remain saved with no derived effective recommendation and MUST be ineligible for placement.
- **FR-009**: The planner MUST be able to change the recommended date range in either direction, including to fewer than seven or more than fourteen days after the final teaching session; the recommendation MUST remain a soft generation preference, while no generated or manually placed exam MAY start before that final teaching session ends.
- **FR-010**: An otherwise valid exam configuration MAY be enabled and saved without a final teaching session, but no exam MAY be placed from it; generation MUST create no session and MUST return `FINAL_TEACHING_SESSION_MISSING` identifying the course and configuration. If a final teaching session exists but no hard-constraint-valid date and automatic proposal time remains after it, generation MUST create no session and MUST identify the substantiated blocking reasons.
- **FR-011**: The planner MUST be able to initiate exam generation for one or more explicitly enabled course-semesters that have no active exam.
- **FR-012**: A generated exam MUST retain the configured duration, exam type, responsible lecturer, cohort, and required capacity context and MUST prefer the recommended date range over otherwise equivalent placements.
- **FR-013**: A generated exam MUST use one current room that is eligible for the course, available for the full exam interval, and has capacity at least equal to the configured exam capacity requirement.
- **FR-014**: The responsible lecturer MUST be current, eligible for the course, and available for the full exam interval.
- **FR-015**: No generated exam MAY overlap a teaching session or exam assigned to the same lecturer, room, or cohort.
- **FR-016**: No generated exam MAY overlap lecturer or room unavailability or occur on an institution-wide holiday.
- **FR-017**: The final-teaching-session boundary, semester boundary, capacity, eligibility, full-interval resource availability, institution holidays, duration, and lecturer, room, and cohort non-overlap MUST be hard constraints for automatic exam generation; the recommended date range MUST NOT be treated as a hard constraint. On each eligible date, automatic generation MUST consider the start time of every active Study Type Time Window applicable to the course's current Study Type. These start times define the bounded automatic proposal domain only and MUST NOT restrict manual exam placement.
- **FR-018**: When generation covers several enabled course-semesters, the system MUST evaluate their proposed active exam placements together so that one newly proposed exam cannot conflict with another proposed exam.
- **FR-019**: Exam generation MUST NOT create, move, resize, replace, or delete any teaching session.
- **FR-020**: Exam generation MUST NOT change an exam for a disabled or unselected course-semester and MUST NOT move, replace, or delete an existing active or past exam.
- **FR-021**: For every selected enabled course-semester without an active exam, generation MUST retain either one valid active exam outcome or one clear failure outcome; it MUST NOT present an invalid or missing outcome as successful.
- **FR-022**: A failure explanation MUST identify the affected course and current exam configuration, every substantiated hard-constraint category that prevented placement, and relevant dates, intervals, or resources where doing so helps the planner correct the cause. When no active Study Type Time Window supplies an automatic proposal time, the failure MUST use `AUTOMATIC_START_TIME_UNAVAILABLE` and explain that the proposal domain is unavailable rather than claiming a resource conflict.
- **FR-023**: A mixed generation outcome MUST distinguish course-semesters with valid active exams from course-semesters with failures and MUST preserve every valid outcome that can be saved without making another saved outcome invalid.
- **FR-024**: A generated result that has become stale against current exam configuration, teaching sessions, exams, holidays, eligibility, availability, or capacity MUST NOT overwrite current planning state when it would violate a hard constraint.
- **FR-025**: Every saved exam MUST be visibly distinguishable from teaching sessions in the existing planner review context.
- **FR-026**: Exam review MUST expose the exam's course, configuration identifier, exam type, duration, date and time, responsible lecturer, cohort, assigned room, required capacity, default or planner-changed recommended date range, final teaching session, whether the exam is outside the recommendation, and current hard-constraint status.
- **FR-027**: The planner MUST be able to manually create exactly one active exam session for an enabled valid current exam configuration when the course-semester has no active exam.
- **FR-028**: The planner MUST be able to correct a saved active or past exam's date, start time, responsible lecturer, and room while retaining its configured duration and other requirement context.
- **FR-029**: A manual exam creation or correction outside the recommended date range MUST be allowed without changing that recommendation when it satisfies the final-teaching-session boundary, semester boundary, duration, eligibility, capacity, full-interval availability, holiday, and lecturer, room, and cohort non-overlap constraints.
- **FR-030**: Manual creation MUST reject a second active exam for the same course-semester and MUST NOT change its existing active or past exams.
- **FR-031**: The planner MUST be able to request deletion of exactly one saved active or past exam session without deleting its course, teaching sessions, resource data, current exam configuration, or any other exam.
- **FR-032**: Before deleting an exam, the system MUST require confirmation that identifies its course, exam configuration, scheduled date and time, whether it is active or past, and whether deletion will leave the current configuration unscheduled or remove only one historical record.
- **FR-033**: Cancelling exam deletion MUST leave all schedule, configuration, outcome, and conflict-context state unchanged.
- **FR-034**: If the selected exam or related planning state changed after a manual editor or deletion confirmation was opened, the system MUST reject the stale creation, correction, or deletion, preserve current state, refresh the affected context, and require the planner to review it before trying again.
- **FR-035**: A rejected, failed, or stale manual action MUST preserve every previously saved exam and all unrelated schedule and planning data while identifying each blocking reason.
- **FR-036**: After successful deletion of an active exam, the current exam configuration MUST remain enabled and visible as unscheduled so that the planner can create it manually or run generation again; deletion of a past exam MUST leave the current configuration and any active exam unchanged.
- **FR-037**: After an exam, teaching session, holiday, resource, or exam requirement changes, the planner's current review context MUST identify any saved exam that no longer satisfies a hard constraint without moving or deleting it automatically.
- **FR-038**: After successful exam generation, manual creation, correction, or deletion, visible exam outcomes and affected conflict context MUST refresh from the saved semester state without requiring the planner to leave and reopen the planning context.
- **FR-039**: This feature MUST NOT provide student registration, grading, broad invigilator management, lecturer editing, external exam publication or booking, publication lifecycle, bulk exam deletion, a fixed or planner-maintained exam-type catalog, or unrelated teaching-schedule behavior.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each implemented user story where automated testing is practical.
- **TR-002**: Configuration coverage MUST verify explicit enablement, disabled-course exclusion, every required planner-entered value, accepted free-text exam types, blank and whitespace-only type rejection, internally valid recommendation overrides in either direction, anchorless enabled/ineligible state with null effective recommendations, boundary-valid values, invalid-value feedback, safe unscheduled changes, and read-only consumed configuration while an active exam exists.
- **TR-003**: Generation coverage MUST verify every applicable Study Type Time Window start is considered, missing proposal domains return `AUTOMATIC_START_TIME_UNAVAILABLE`, missing teaching anchors return `FINAL_TEACHING_SESSION_MISSING`, and every hard constraint is enforced independently and in combination, including exact-boundary non-overlap, full-duration availability, mixed feasible and infeasible courses, and stale-result rejection.
- **TR-004**: Failure coverage MUST verify that each substantiated blocking category is understandable and course-specific and that no failed course retains an invalid newly generated exam.
- **TR-005**: Manual-management coverage MUST verify exam/teaching distinction, required context, valid creation and correction at times both inside and outside the automatic proposal domain, duplicate prevention, rejection of every hard-constraint violation, consequence-aware deletion confirmation, cancellation, stale-action rejection, selected-exam isolation, preservation, unscheduled status after deletion, and refreshed current-validity feedback.
- **TR-006**: Regression coverage MUST verify that teaching-session generation, saved teaching sessions, resource eligibility and availability, and the institution holiday calendar retain their established behavior.
- **TR-007**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Course Exam Requirement**: The explicit course-semester decision that the next exam is enabled, with one current configuration available when no active exam blocks another placement.
- **Exam Configuration**: The fresh planner-visible definition of the next required exam, including its identifier, duration, default or planner-changed recommended date range, required room capacity, required free-text exam type, and responsible lecturer; it does not rewrite a past exam's saved details.
- **Exam Session**: A distinguishable scheduled exam occurrence for an enabled course-semester, with a date and interval, responsible lecturer, cohort, assigned room, and a relationship to the applicable configuration.
- **Active Exam**: The single permitted exam session for a course-semester whose institution-local scheduled calendar date is today or later.
- **Past Exam**: An exam session whose institution-local scheduled calendar date is before today; it retains its own saved scheduling and configuration details, remains reviewable and planner-maintainable, and does not count against the one-active-exam limit.
- **Recommended Exam Window**: The soft date preference used by automatic generation. It defaults to seven through fourteen calendar days after the final teaching session and may be changed by the planner without becoming a hard placement boundary.
- **Responsible Lecturer**: The single lecturer assigned to the exam in this slice; the lecturer is both an exam requirement and a hard conflict and availability resource.
- **Exam Placement Outcome**: The result for one selected enabled course-semester without an active exam: either a saved valid active exam or a clear failure containing the course, configuration, and substantiated blocking constraint context.
- **Exam Validity Issue**: Current review information showing why an already saved exam no longer satisfies a hard constraint after related planning data changes; it does not automatically alter the exam.

## Dependencies

- **Required — FS-008: Resource Eligibility and Availability** supplies current lecturers and rooms, course eligibility, room capacity, and recurring or dated availability.
- **Required — FS-010: Conflict-Aware Semester Optimization** supplies the semester-wide hard-conflict and partial-outcome planning boundary that exam placement extends without redefining teaching optimization.
- **Required — FS-011: Institution-Wide Holiday Calendar and Avoidance** supplies the current institution-wide holidays that exams must treat as hard unavailable full dates.
- Existing manual session review and correction behavior from FS-004 and FS-009 is integration context. FS-012 defines its own exam-specific hard-constraint, confirmation, preservation, and stale-state safeguards without expanding those earlier slices.
- FS-013 publication lifecycle and FS-014 calendar workspace are downstream features and are not delivered by FS-012.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across acceptance datasets, 100% of course-semesters without an explicitly enabled valid current exam requirement receive no generated exam and no false missing-exam failure.
- **SC-002**: Across acceptance datasets, 100% of selected enabled course-semesters without an active exam finish generation with either one valid active exam or one configuration-specific understandable failure; no course-semester receives a silent or duplicate outcome.
- **SC-003**: In 100% of generation acceptance cases, the selected placement is inside the recommended date range whenever a hard-constraint-valid placement exists there within the automatic proposal domain; otherwise generation may place the exam outside the recommendation, while every generated exam still uses an active Study Type Time Window start and satisfies the final-teaching, semester, duration, responsible-lecturer, room-eligibility, room-capacity, full-interval availability, holiday, and lecturer, room, and cohort non-overlap rules.
- **SC-004**: In 100% of infeasible and stale-result acceptance cases, no invalid newly generated exam is retained and existing teaching sessions, active exams, and past exams remain unchanged.
- **SC-005**: With valid inputs, the planner can enable and save an exam configuration through one form submission; an invalid submission identifies every invalid field together and changes no previously saved value.
- **SC-006**: Exam review displays Teaching/Exam and Active/Past labels directly and exposes the course, type, date, time, lecturer, room, and current validity without navigating away from the Schedule context.
- **SC-007**: Every failed placement names the affected course and configuration, identifies every substantiated blocking category, and includes relevant date, interval, resource, or session evidence when available.
- **SC-008**: In 100% of manual-management acceptance cases, valid creation, correction, or deletion changes only the selected exam configuration's session, while an invalid, cancelled, failed, duplicate, or stale action changes no saved exam or teaching session.
- **SC-009**: For a reference semester containing up to 100 enabled exam requirements, 500 teaching sessions, and 100 existing exams, generation provides a complete mixed outcome within 60 seconds, and saved outcomes and conflict context become visible without a manual reload.
- **SC-010**: All applicable acceptance scenarios from FS-008, FS-010, and FS-011 continue to pass after exam scheduling is introduced.

## Assumptions

- The planner-only MVP has one planner-user role with authority to configure, generate, review, and correct exams; authentication and lecturer editing remain outside this slice.
- One responsible lecturer and one cohort apply to an exam. Broad invigilator or supervision assignments are not modeled.
- An exam-enabled course-semester has at most one current configuration for its next active exam. It may retain unlimited past exam sessions, and only one exam session dated today or later may be active at a time.
- An enabled configuration may be saved before teaching sessions exist, but it has no derived effective recommendation and cannot produce an exam until a final teaching session supplies the hard timing anchor.
- While an active exam exists, its consumed current configuration is read-only. Once that exam becomes past, preparing the next exam replaces it with a fresh configuration without altering the past exam snapshot.
- Each past exam retains the details saved for that exam. A fresh current configuration is prepared for the next exam rather than sharing mutable configuration values with past exams.
- Exam type is required planner-entered free text for each exam. FS-012 deliberately avoids prescribing or administering an institution-wide exam-type taxonomy.
- The one-to-two-week timing is a soft recommendation for automatic generation rather than a hard delay or boundary. The planner may change the recommendation or place an individual exam outside it, while the exam's start may never precede the end of the course's final teaching session.
- Automatic generation uses active Study Type Time Window start times as its bounded proposal domain. These proposal times are not manual-placement hard constraints, and the planner may choose another time manually when every approved hard constraint passes.
- The responsible lecturer and assigned room come from the course's current eligible resources established by FS-008.
- Required room capacity is a positive whole-number exam requirement and may differ from the course cohort size; the assigned room must meet the configured exam requirement.
- Exam duration is elapsed clock time and must fit wholly inside every applicable date, availability, and conflict boundary.
- Institution holidays remain named full dates from the single current FS-011 calendar; partial-day closures and alternate campus calendars are outside this slice.
- A saved exam is not automatically regenerated, moved, or deleted when its configuration or related teaching, holiday, or resource data changes. The planner sees current invalidity and initiates correction.
- The existing planner review context is extended incrementally; FS-012 does not deliver the broader FS-014 calendar workspace.
- Manual deletion removes only the selected exam session. Its exam configuration remains enabled and visibly unscheduled until the planner creates a replacement manually, runs generation again, removes the configuration, or disables exams for the course.
- Past exams remain planner-maintainable in FS-012: they may be corrected when the result still satisfies all hard constraints and the one-active-exam rule, or deleted after the same consequence-aware confirmation and stale-state checks used for active exams.
- Exam generation may retain feasible results alongside failures, consistent with the product goal of understandable partial planning, provided every retained exam remains valid in the combined semester state.
- Publication and historical schedule-revision semantics are deferred to FS-013; FS-012 operates on the current planning state.
