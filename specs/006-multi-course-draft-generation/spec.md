# Feature Specification: Multi-Course Draft Generation

**Working Branch**: `master`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "Create Slice 6: Multi-Course Draft Generation for the Resource Planner. Office staff need to generate draft schedules for several explicitly selected courses in one action for a selected semester. Each course is generated independently with its own saved constraints or defaults. The operation allows partial success, preserves failed courses, confirms replacement of existing schedules, refreshes the semester overview and conflict alerts, retains schedules independently by course and semester, and preserves the existing single-course workflow. Conflict-aware generation and later roadmap capabilities remain out of scope."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-13

- Q: When one selected course is nonexistent or no longer available, should valid courses still be generated? → A: Report that course as failed and continue generating valid courses.
- Q: If an unexpected operation-wide failure occurs after some courses have been processed, should changes from that attempt remain? → A: Roll back all changes from the attempt and report an operation-wide failure.
- Q: What happens if a course's existing draft changes after replacement confirmation but before the regenerated draft is saved? → A: Fail that course as stale, preserve its newer draft, and continue other valid courses.
- Q: What is the maximum number of courses in one initial or retry operation? → A: Allow 2-50 courses initially and 1-50 failed courses on retry.
- Q: What happens if a selected course's generation constraints change after the operation starts? → A: Fail that course as stale, preserve its newer constraints, and continue other valid courses.
- Q: How long must the result summary and failed-course retry set remain available? → A: Keep them only in the current planner session; they may clear after reload or when the session ends.

- Q: What usability protocol validates the 90% comprehension and retry success criteria? → A: Use at least 10 representative office staff or acceptance reviewers familiar with the existing planner and not coached on the batch workflow; each criterion passes when at least 90% complete its scenario unaided.
- Q: How is the 10-second performance target measured? → A: Use the documented reference performance environment with 50 seeded valid courses, a warm start, and no artificial latency; the median of three runs from activating Generate until the complete summary is rendered must be at most 10 seconds.
- Q: How is the two-minute semester/course selection and generation-start criterion validated? → A: Use the same at-least-10-participant unaided protocol with first-time courses; time from presenting the named-semester generation instruction until Generate is activated, and require at least 90% to finish within two minutes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Several Course Drafts (Priority: P1)

An office staff member selects a semester and at least two courses, then starts one generation action. Each selected course is generated independently with its own active generation constraints, and the staff member receives a result for every course.

**Why this priority**: Generating several course drafts in one action is the core value of this slice and moves the planner from repeated proof-of-concept generation toward practical semester planning.

**Independent Test**: Select two courses without existing drafts, give one saved custom constraints and leave the other on defaults, start generation, and verify that both resulting schedules use their own course-specific constraints and appear in the selected semester overview.

**Acceptance Scenarios**:

1. **Given** a selected semester and two or more distinct courses without existing drafts in that semester, **When** office staff start multi-course generation, **Then** the system independently generates each selected course and reports an outcome for every selected course.
2. **Given** one selected course has saved custom generation constraints and another has none, **When** both are generated together, **Then** the first uses its saved constraints and the second uses its semester and Study Type Time Window defaults.
3. **Given** the course currently displayed in the single-course planning controls has edited constraints, **When** several courses are generated together, **Then** those constraints are not applied to any other selected course.
4. **Given** every selected course can be generated, **When** the operation completes, **Then** the result summary reports all courses as successful and the selected semester overview contains their current Draft Schedules.
5. **Given** fewer than two or more than 50 distinct valid courses are selected, **When** office staff attempt multi-course generation, **Then** generation does not start and the system explains the allowed range of 2-50 courses.

---

### User Story 2 - Handle Partial Success and Retry Failures (Priority: P2)

An office staff member can complete useful semester planning even when one or more selected courses cannot be generated. Successful courses remain available, failed courses retain their previous data, and failures can be retried without regenerating successes.

**Why this priority**: One invalid course should not discard useful work for every other selected course. Clear per-course outcomes let staff correct planning inputs efficiently.

**Independent Test**: Generate one valid course together with one course whose active constraints cannot fit its sessions, verify that only the valid course changes, and retry only the failed course after correcting its inputs.

**Acceptance Scenarios**:

1. **Given** a selection containing both valid and invalid courses, **When** multi-course generation completes, **Then** valid courses succeed, invalid courses fail, and the overall summary shows the correct success and failure counts.
2. **Given** a course fails generation, **When** results are displayed, **Then** its result identifies the course and presents understandable reasons for the failure.
3. **Given** a failed course already has a Draft Schedule, manual session edits, or saved constraints, **When** that course fails during a multi-course operation, **Then** all of its pre-operation data remains unchanged.
4. **Given** some selected courses succeeded and one or more courses failed, **When** office staff retry the failures, **Then** only the failed courses are included in the retry and successful courses are not regenerated, including when only one course needs retrying.
5. **Given** selected courses independently produce overlapping sessions, **When** generation completes, **Then** those courses remain successful because overlap conflicts do not block generation in this slice.
6. **Given** one selected course is nonexistent or no longer available while other selections are valid, **When** multi-course generation runs, **Then** the unavailable course receives a failed outcome and the valid courses continue.
7. **Given** an unexpected operation-wide failure occurs after course processing has begun, **When** the operation ends, **Then** every change made by that attempt is rolled back and the system reports an operation-wide failure rather than partial course outcomes.
8. **Given** a selected course's generation constraints change after the operation starts, **When** that course is processed, **Then** it fails as stale, its newer constraints and existing schedule remain unchanged, and other valid courses continue.
9. **Given** a completed operation has failed courses, **When** office staff remain in the current planner session, **Then** its result summary and failed-course retry set remain available; after a reload or later session, the system is not required to restore that batch result.

---

### User Story 3 - Safely Replace Existing Semester Drafts (Priority: P3)

Before regenerating a course that already has a Draft Schedule in the selected semester, office staff can see that the existing schedule and manual edits will be replaced and must explicitly confirm that consequence.

**Why this priority**: Batch generation increases the risk of unintentionally overwriting reviewed or manually adjusted work. Explicit identification and confirmation protect staff from accidental data loss.

**Independent Test**: Select a mixture of courses with and without existing drafts, cancel the replacement confirmation, verify no course changed, then repeat and confirm to verify that only successfully regenerated course-semester drafts are replaced.

**Acceptance Scenarios**:

1. **Given** one or more selected courses already have Draft Schedules in the selected semester, **When** office staff prepare to generate them, **Then** the system identifies those courses and states that their schedules and manual edits will be replaced.
2. **Given** replacement confirmation is required, **When** office staff cancel it, **Then** the entire requested operation is cancelled and no Draft Schedule or generation constraint changes.
3. **Given** office staff confirm replacement, **When** an existing course is successfully regenerated, **Then** only that course's Draft Schedule in the selected semester is replaced and its newly active constraints are retained.
4. **Given** a selected course has a Draft Schedule in another semester but none in the selected semester, **When** generation succeeds, **Then** the other semester's schedule remains unchanged and no replacement confirmation is required for it.
5. **Given** the same course has Draft Schedules in multiple semesters, **When** one semester is regenerated, **Then** all Draft Schedules and manual edits for that course in other semesters remain unchanged.
6. **Given** a selected course's existing Draft Schedule or manual edits change after replacement confirmation, **When** the operation attempts to save that course's regenerated draft, **Then** that course fails as stale, its newer data remains unchanged, other valid courses continue, and retry requires confirmation against the current draft.

---

### User Story 4 - Review the Semester After Generation (Priority: P4)

After multi-course generation, office staff can immediately review the selected semester's complete Courses overview, including existing conflict alerts across newly generated and previously saved course drafts.

**Why this priority**: Independent generation can produce overlaps. Immediate review preserves the established planning loop without expanding this slice into conflict-aware scheduling.

**Independent Test**: Generate courses that share a lecturer, room, or Cohort at overlapping times and verify that the refreshed overview shows all schedules and the corresponding non-blocking alerts.

**Acceptance Scenarios**:

1. **Given** at least one course succeeds, **When** the operation completes, **Then** the selected semester Courses overview refreshes to show all current Draft Schedules for that semester.
2. **Given** newly generated sessions conflict with other sessions in the semester, **When** the refreshed overview is displayed, **Then** the existing lecturer, room, and Cohort conflict alerts identify the affected sessions.
3. **Given** conflict alerts are present, **When** office staff review the batch results and overview, **Then** the alerts do not convert otherwise successful course outcomes into generation failures.
4. **Given** the multi-course operation is complete, **When** office staff return to single-course planning, **Then** they can still select one course, configure its constraints, and generate it through the existing workflow.

### Edge Cases

- No courses, only one course, or the same course repeated in the request does not satisfy the minimum of two distinct courses.
- An initial request contains more than 50 distinct courses, or a retry contains more than 50 failed courses; the operation does not start and the allowed limit is explained.
- A nonexistent or no-longer-available course receives a failed course outcome while other valid courses continue; no schedule in another semester is modified.
- A nonexistent semester invalidates the entire request before any selected course is generated.
- A selected course has saved constraints that are no longer valid; the course fails with its validation reasons rather than silently falling back to defaults.
- A selected course has defaults with no usable Study Type Time Window; that course fails while other valid courses continue.
- A course has an existing Draft Schedule only in another semester; that schedule is not treated as a replacement target and remains unchanged.
- A mixture of replacement and first-time courses is selected, and the user cancels the replacement confirmation; none of the courses are generated.
- Every selected course fails; the summary reports zero successes, all existing data remains unchanged, and the failed set remains available for retry.
- Only one course fails in a multi-course operation; that single course remains retryable without adding or regenerating another course.
- A course becomes unavailable after selection but before generation starts; it receives a failed outcome and other valid selections continue.
- An unexpected infrastructure or persistence failure occurs during the operation; all changes made by that attempt are rolled back, and earlier saved data remains unchanged.
- A confirmed replacement target changes before its regenerated draft is saved; the changed course receives a stale-data failure, keeps its newer schedule and edits, and does not prevent other valid courses from succeeding.
- A selected course's saved constraints change after the operation starts; that course receives a stale-data failure, keeps its newer constraints and existing schedule, and does not prevent other valid courses from succeeding.
- Independent generation creates many conflict alerts; successful schedules remain saved and the existing alert presentation remains usable.
- The refreshed overview already contains schedules that were not part of the operation; they remain present and participate in cross-course conflict detection.
- The page is reloaded after a completed operation; saved Draft Schedules remain available, but the prior result summary and failed-course retry set may be cleared.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow office staff to choose one semester as the target of a multi-course generation operation.
- **FR-002**: System MUST allow office staff to explicitly select courses from the planning options currently available to them.
- **FR-003**: System MUST require between 2 and 50 distinct courses before an initial multi-course generation operation can start.
- **FR-004**: System MUST reject duplicate course selections and nonexistent semesters before generating any selected course, with understandable feedback.
- **FR-005**: System MUST scope every schedule created or replaced by the operation to the selected semester.
- **FR-006**: System MUST generate each selected course independently using that course's existing units, session-size preferences, lecturer, Cohort, room, and Study Type.
- **FR-007**: System MUST use each selected course's own saved generation constraints for the selected semester when they exist.
- **FR-008**: System MUST use the selected semester dates and the course's Study Type Time Window defaults when that course has no saved custom constraints.
- **FR-009**: System MUST NOT apply one course's constraints to another selected course.
- **FR-010**: System MUST evaluate all selected courses so that an expected generation failure for one course does not prevent other valid courses from succeeding.
- **FR-011**: System MUST provide an outcome for every selected course identifying the course and whether generation succeeded or failed.
- **FR-012**: System MUST provide an overall summary with the total selected, successful, and failed course counts.
- **FR-013**: System MUST provide understandable, course-specific reasons for every expected generation failure.
- **FR-014**: System MUST allow office staff to retry between 1 and 50 failed courses without including courses that already succeeded, even though an initial multi-course request requires at least two courses.
- **FR-015**: System MUST save the complete Draft Schedule and active generation constraints for each successfully generated course.
- **FR-016**: System MUST preserve a failed course's pre-operation Draft Schedule, Draft Sessions, manual edits, and saved generation constraints unchanged.
- **FR-017**: System MUST NOT leave a failed course with a partially replaced or partially created Draft Schedule.
- **FR-018**: System MUST identify selected courses that already have a Draft Schedule in the selected semester before generation begins.
- **FR-019**: System MUST inform office staff that successful regeneration of an identified course will replace its existing Draft Schedule and manual session edits.
- **FR-020**: System MUST require explicit confirmation before starting an operation that includes at least one existing Draft Schedule in the selected semester.
- **FR-021**: System MUST leave every selected course's schedule and constraints unchanged when office staff cancel the replacement confirmation.
- **FR-022**: System MUST replace an existing Draft Schedule only when that course successfully regenerates for the same selected semester.
- **FR-023**: System MUST retain Draft Schedules independently for each course and semester.
- **FR-024**: System MUST NOT modify a course's Draft Schedule, Draft Sessions, manual edits, or generation constraints in any semester other than the selected semester.
- **FR-025**: System MUST refresh the selected semester Courses overview after the operation finishes.
- **FR-026**: System MUST show newly generated schedules together with all other current Draft Schedules in the selected semester.
- **FR-027**: System MUST evaluate and display existing validation alerts across the complete refreshed semester schedule set.
- **FR-028**: System MUST allow schedules with lecturer, room, or Cohort overlaps to succeed and MUST present those overlaps as non-blocking validation alerts.
- **FR-029**: System MUST preserve the existing single-course generation and per-course constraint configuration workflow.
- **FR-030**: System MUST NOT attempt conflict-aware placement, optimization, or automatic conflict resolution during multi-course generation.
- **FR-031**: System MUST keep public holiday avoidance, exam scheduling, multiple lecturers or eligible rooms per course, individual session creation/deletion/splitting/merging, course-semester eligibility administration, dashboards, approval workflows, and background processing outside this feature.
- **FR-032**: System MUST report a nonexistent or no-longer-available selected course as a failed course outcome and continue processing other valid selected courses.
- **FR-033**: System MUST roll back every schedule and generation-constraint change made by the current attempt when an unexpected operation-wide failure occurs, and MUST report that operation-wide failure without presenting uncommitted course outcomes as successful.
- **FR-034**: System MUST fail a course as stale when its replacement target changes after confirmation and before save, preserve the newer course data, continue other valid courses, and require current replacement confirmation before retrying that course.
- **FR-035**: System MUST reject a retry operation containing more than 50 failed courses before generation begins and explain the maximum retry size of 50 courses.
- **FR-036**: System MUST fail a course as stale when its saved generation constraints change after the operation starts, preserve its newer constraints and existing schedule, and continue processing other valid selected courses.
- **FR-037**: System MUST keep the completed operation's result summary and failed-course retry set available for the current planner session, but MUST NOT require batch-result history to persist across a reload or later session.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Backend behavior MUST be verified with FastAPI-compatible tests, normally using `pytest`.
- **TR-003**: Frontend behavior MUST be verified through React/Vite-appropriate checks, such as build, lint, component, or UI tests.
- **TR-004**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.
- **TR-005**: Automated coverage MUST verify all-success, partial-success, all-failed, confirmation-cancelled, and cross-semester data-retention outcomes.
- **TR-006**: Automated coverage MUST verify that existing single-course generation, manual editing, semester overview, and conflict-alert behavior remain available.

### Key Entities

- **Multi-Course Generation Request**: One staff-initiated attempt targeting a single semester and 2-50 distinct selected courses, including confirmation when existing drafts will be replaced; a retry may target 1-50 failed courses.
- **Course Generation Outcome**: The result for one selected course, including its identity, success or failure status, and any understandable failure reasons.
- **Generation Result Summary**: Transient current-session aggregate counts for selected, successful, and failed courses, plus the failed course set available for retry; it is not retained as batch history across reloads or later sessions.
- **Generation Constraints**: The planning period and allowed weekly teaching windows active for one course in one semester, sourced from saved customization or course-specific defaults.
- **Draft Schedule**: The current generated plan for one course in one semester, containing its Draft Sessions and retained independently from schedules for other semesters.
- **Draft Session**: One scheduled teaching occurrence belonging to a Draft Schedule and carrying its date, time, units, lecturer, Cohort, room, and validation alerts.
- **Validation Alert**: A non-blocking explanation of a detected overlap or other existing schedule-safety issue in the refreshed semester overview.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the same at-least-10-participant unaided usability protocol, using first-time courses that require no replacement confirmation, at least 90% of participants MUST select the named semester, select at least two courses, and activate Generate within two minutes measured from receiving the generation instruction.
- **SC-002**: In the documented reference performance environment with 50 seeded valid courses, a warm start, and no artificial latency, the median of three runs measured from office staff activating Generate until the complete result summary is rendered MUST be at most 10 seconds.
- **SC-003**: 100% of selected courses receive exactly one clearly identifiable success or failure outcome.
- **SC-004**: In all tested partial-success cases, every valid course is generated and every failed course retains its complete pre-operation schedule, manual edits, and saved constraints.
- **SC-005**: In all tested replacement-cancellation cases, no selected schedule or generation constraint changes.
- **SC-006**: In all tested cross-semester cases, generating or regenerating a course in one semester leaves that course's data in every other semester unchanged.
- **SC-007**: After completion, 100% of successfully generated schedules are visible in the selected semester overview together with any applicable non-blocking validation alerts.
- **SC-008**: In a usability review with at least 10 representative office staff or acceptance reviewers who are familiar with the existing planner and receive no batch-workflow coaching, at least 90% MUST correctly identify which courses will be replaced, which courses failed, and that conflict avoidance is not part of this slice.
- **SC-009**: In the same usability-review protocol, at least 90% of participants MUST retry only failed courses on their first unaided attempt without regenerating successful courses.
- **SC-010**: Existing single-course generation, manual editing, semester review, and conflict-alert acceptance scenarios continue to pass after this feature is delivered.
- **SC-011**: In 100% of tested unexpected operation-wide failure cases, no schedule or generation-constraint change from the failed attempt remains.

## Assumptions

- Office staff already have access to the existing Resource Planner; this slice does not introduce new roles or permissions.
- Slices 1 through 5 are available: single-course generation, semester Courses overview, per-course generation constraints, manual session editing, and non-blocking validation alerts.
- Each course continues to have one lecturer, one Cohort, one assigned room, one Study Type, and existing unit and session-size preferences.
- The available planning options define which courses can be selected. Creating or administering course-semester eligibility is outside this slice.
- Saved generation constraints are scoped to one course and one semester. Invalid saved constraints cause that course to fail rather than being silently replaced by defaults.
- Defaults consist of the selected semester dates and the selected course's Study Type Time Windows.
- Multi-course generation is a foreground staff action for normal semester-sized selections; background job management is unnecessary for this slice.
- Expected course-level validation failures permit partial success. Unexpected infrastructure or persistence failures are operation-wide failures and leave no change from the failed attempt.
- Successful regeneration continues the established behavior of replacing the current Draft Schedule and any manual edits for the same course and semester.
- Validation alerts are recalculated from the current selected-semester schedule data and remain informational rather than blocking.
- Batch result summaries and retry selections are current-session workflow state rather than retained operation history; saved Draft Schedules and constraints remain durable according to their existing rules.
