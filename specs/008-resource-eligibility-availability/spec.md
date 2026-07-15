# Feature Specification: FS-008 Resource Eligibility and Availability

**Working Branch**: `master`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Create FS-008 so planner users can maintain lecturers, rooms, room capacity, recurring or dated resource availability, and multiple eligible lecturers and rooms per course for later generation and validation."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-15

- Q: How should deletion behave when a lecturer or room is still referenced? → A: Delete it when only inactive-course eligibility links remain and no Draft Session references it, removing those obsolete links automatically; otherwise mark it inactive, preserve history, and identify affected active courses.
- Q: How should contiguous lecturer blocks and same-room reuse be configured? → A: Both soft preferences are always considered within each individual course's Draft Schedule, but hard constraints may require multiple lecturers or rooms.
- Q: How should resources with the same display name be distinguished? → A: Allow duplicate names but require a planner-maintained reference code that is unique within each resource catalog.
- Q: What should happen when cohort growth makes an eligible room too small? → A: Automatically remove every insufficient room from affected course eligibility sets, preserve existing session assignments with validation alerts, and make a course unavailable if no eligible room remains.
- Q: What should happen when the planner reactivates an inactive lecturer or room? → A: Reactivate it after current values are valid and restore preserved course eligibility wherever current capacity and other hard rules permit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain Scheduling Resources Safely (Priority: P1)

A planner creates, views, corrects, and removes lecturer and room records so scheduling no longer depends on developer-maintained resource data. Rooms include the capacity needed to determine whether they can host a course.

**Why this priority**: Resource records are the prerequisite for expressing availability, course eligibility, and valid session assignments.

**Independent Test**: Starting with no unreferenced test resources, create a lecturer and a room, edit their details, permanently delete a resource referenced only by inactive-course eligibility, and verify that attempts to delete resources referenced by an active course or any Draft Session instead inactivate the resource without changing those references.

**Acceptance Scenarios**:

1. **Given** the planner provides a lecturer name and reference code and a room name, reference code, and positive whole-number capacity, **When** each record is saved, **Then** both records remain available for later resource administration and eligible-resource selection by name and code.
2. **Given** a lecturer or room exists, **When** the planner edits valid identifying details or room capacity, **Then** future planning uses the current values and no existing Draft Session is silently reassigned.
3. **Given** a lecturer or room has no active-course eligibility or Draft Session references, **When** the planner confirms deletion, **Then** eligibility links from inactive courses are removed and the resource and its own availability records are permanently deleted.
4. **Given** a lecturer or room is eligible for one or more active courses, **When** the planner requests deletion, **Then** destructive deletion is prevented, the resource is marked inactive, and the feedback identifies each affected active course.
5. **Given** a lecturer or room is assigned to one or more Draft Sessions, **When** the planner requests deletion, **Then** destructive deletion is prevented, the resource is marked inactive, the sessions remain reviewable, and the feedback identifies the blocking session usage and any affected active courses.
6. **Given** another planner view saved a newer version of a resource, **When** the planner attempts to save or delete a stale version, **Then** the newer record is preserved and the planner is asked to refresh or review the change.
7. **Given** an inactive resource has valid current values and preserved course eligibility relationships, **When** the planner reactivates it, **Then** it returns to active resource choices and each preserved relationship becomes usable where current capacity and other hard rules permit.
8. **Given** an inactive resource has an invalid or duplicate reference code or another invalid current value, **When** the planner attempts reactivation, **Then** reactivation is rejected, the resource remains inactive, and every required correction is identified.

---

### User Story 2 - Record Resource Unavailability (Priority: P2)

A planner records when a lecturer or room cannot be scheduled, using weekly recurring periods for regular commitments and dated periods for one-time exceptions.

**Why this priority**: Eligibility alone is not enough to avoid assigning otherwise suitable resources when they cannot be used.

**Independent Test**: Add recurring and dated unavailable periods to a lecturer and room, inspect their interpreted occurrences, and verify that sessions overlapping those periods are identified while sessions ending exactly when unavailability begins remain available.

**Acceptance Scenarios**:

1. **Given** a lecturer has a recurring unavailable period on Monday from 09:00 to 11:00, **When** the planner reviews resource availability for any applicable Monday, **Then** the lecturer is unavailable during that interval.
2. **Given** a room has a dated unavailable period, **When** a session overlaps that period, **Then** the room is treated as unavailable for the entire session assignment.
3. **Given** recurring and dated unavailable periods overlap, **When** availability is evaluated, **Then** the combined interval is unavailable and neither entry makes any overlapping time available.
4. **Given** an unavailable period has missing boundaries or an end that is not later than its start, **When** the planner attempts to save it, **Then** the period is not saved and every invalid value is identified.
5. **Given** a Draft Session is already assigned to a resource, **When** the planner adds or changes an unavailable period that overlaps the session, **Then** the session is not moved or deleted and validation identifies the new availability conflict.
6. **Given** an unavailable period exists, **When** the planner edits or deletes it, **Then** subsequent generation inputs and validation use the updated availability without changing unrelated resource data.

---

### User Story 3 - Maintain Course Resource Eligibility (Priority: P3)

A planner associates one or more eligible lecturers and one or more eligible rooms with each course and can see the availability and capacity information needed to make those associations meaningful.

**Why this priority**: Multiple eligible resources create the choice set needed by later conflict-aware optimization while keeping resource suitability under planner control.

**Independent Test**: Configure a course with two eligible lecturers and two capacity-sufficient rooms, reject an insufficient-capacity room, remove one still-used eligibility relationship, and verify that the course retains valid alternatives while the existing session assignment remains visible with an eligibility alert.

**Acceptance Scenarios**:

1. **Given** a course and several lecturer and room records exist, **When** the planner selects two distinct lecturers and two distinct capacity-sufficient rooms, **Then** all four eligibility relationships remain visible with the course.
2. **Given** a room capacity is lower than the course cohort size, **When** the planner attempts to add it as an eligible room, **Then** the relationship is rejected and the capacity shortfall is explained.
3. **Given** a currently eligible resource is assigned to an existing Draft Session and the course has another eligible resource of that type, **When** the planner removes the eligibility relationship, **Then** the session keeps its assignment and validation identifies that the assigned resource is no longer eligible.
4. **Given** a course has exactly one eligible lecturer or exactly one eligible room, **When** the planner attempts to remove the last relationship of that type, **Then** the change is rejected and the course retains at least one eligible lecturer and room.
5. **Given** a course has several eligible lecturers and rooms, **When** the planner reviews its resource configuration, **Then** the planner can inspect each resource's current capacity where applicable, unavailable periods, and whether it is assigned to existing sessions for that course.
6. **Given** the course has more than one eligible lecturer or room, **When** the planner reviews its scheduling preferences, **Then** the course shows that contiguous lecturer blocks and reuse of the same room are always-considered soft preferences rather than validity rules, and that hard constraints may require multiple lecturers or rooms.
7. **Given** a cohort-size increase makes one or more eligible rooms too small, **When** the cohort change succeeds, **Then** every insufficient room is removed from affected course eligibility sets, existing Draft Session assignments remain unchanged with capacity and eligibility alerts, and each course left without a room is unavailable for new generation.

---

### User Story 4 - Supply Valid Resource Choices to Scheduling (Priority: P4)

The planner's maintained resource records, eligibility, availability, capacity, and preferences are available to existing generation and validation workflows and to the later conflict-aware optimizer without this slice performing global optimization.

**Why this priority**: Maintained data delivers scheduling value only when downstream workflows can consistently interpret it, while automated global resource selection belongs to FS-010.

**Independent Test**: Configure representative eligible and ineligible resources, unavailable periods, and capacity constraints; then verify that generation inputs expose the complete configuration, every session retains exactly one lecturer and room, and validation reports each hard-rule violation without automatically changing the schedule.

**Acceptance Scenarios**:

1. **Given** a course has multiple eligible lecturers and rooms, **When** its resource constraints are made available for generation, **Then** the complete distinct eligibility sets, current availability, capacities, and soft-preference meanings are available together.
2. **Given** a Draft Session is created by an existing generation workflow or changed through an existing editing workflow, **When** the session is saved, **Then** it references exactly one lecturer and exactly one room.
3. **Given** a Draft Session uses an ineligible resource, overlaps resource unavailability, or exceeds room capacity, **When** the schedule is validated, **Then** each applicable issue is identified without silently moving, deleting, or reassigning the session.
4. **Given** a valid session uses one of several eligible lecturers and rooms, **When** it is validated, **Then** the other eligible resources do not create duplicate assignments or validation issues merely because they were not chosen.
5. **Given** a course predates this feature and has one lecturer and one room, **When** resource eligibility becomes available, **Then** those existing resources form the course's initial eligible sets and all existing Draft Session assignments remain unchanged.

### Edge Cases

- A room capacity is missing, zero, negative, or fractional; the room is not saved and the planner retains the other entered values for correction.
- A room capacity is reduced below the cohort size of an already eligible course; the relationship and existing sessions remain visible, the course is not ready to use that room for new generation, and capacity validation identifies every affected assignment.
- A cohort size is increased above the capacity of one or more eligible rooms; those rooms are automatically removed from affected eligibility sets, while existing session assignments remain unchanged and receive capacity and eligibility alerts.
- Cohort growth removes the last eligible room from a course; the course remains visible but is unavailable for new generation until the planner adds a capacity-sufficient room.
- Two lecturers or rooms have the same display name; they remain separate resources and are distinguished in eligibility, usage, and deletion views by their unique planner-maintained reference codes rather than being silently merged.
- Two reference codes within the same resource catalog differ only by capitalization or surrounding whitespace; they are treated as the same code and the duplicate save is rejected without losing the planner's entered values.
- A resource has no unavailable periods; it is treated as available wherever all other scheduling constraints permit.
- A session only touches the start or end boundary of an unavailable period; touching boundaries do not overlap, while any shared duration does.
- A dated unavailable period spans more than one calendar date; every instant from its start through, but not including, its end is unavailable.
- Two unavailable periods are exact duplicates; the duplicate is rejected. Partially overlapping periods are allowed and interpreted as their combined unavailable time.
- A recurring unavailable period and a dated unavailable period apply at the same time; unavailability wins because dated periods add exceptions and do not reopen recurring unavailable time.
- An eligibility update repeats the same lecturer or room; the course retains one relationship to that resource rather than creating a duplicate.
- Removing an eligibility relationship would leave a course with no eligible lecturer or room; the update is rejected without changing the existing sets.
- A resource is removed from course eligibility while an existing session uses it; the session remains assigned and reviewable but receives an ineligible-resource validation issue.
- A resource becomes unavailable after sessions have been generated; saved sessions remain in place and receive availability validation issues.
- A resource is marked inactive while it is the only eligible lecturer or room for an active course; the course remains visible but unavailable for new generation until the planner associates an active valid replacement, and the retirement result identifies that course.
- A resource is linked only to inactive courses and no Draft Session; a confirmed deletion removes those obsolete eligibility links before deleting the resource, without reactivating or otherwise changing the courses.
- An inactive room is reactivated after its capacity becomes insufficient for a preserved course relationship; the room becomes active, but that relationship remains visibly unusable and is excluded from new generation until capacity is sufficient.
- Availability changes while another planner view is editing the same rule; a stale save does not silently overwrite the newer rule.
- Resource data cannot be refreshed; the planner is warned that eligibility or availability may be stale, and no current selection or saved session is silently changed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide planner-accessible administration for lecturers and rooms, including create, view, edit, and protected-delete actions.
- **FR-002**: A lecturer MUST have a non-empty planner-visible name, a non-empty planner-maintained reference code that is unique among lecturers, and a stable identity that remains distinct even when another lecturer has the same display name.
- **FR-003**: A room MUST have a non-empty planner-visible name, a non-empty planner-maintained reference code that is unique among rooms, a stable identity, and a positive whole-number capacity.
- **FR-004**: Successfully saved resource records and changes MUST remain available across later planner sessions.
- **FR-005**: The system MUST preserve entered values after a resource or availability validation failure so the planner can correct invalid fields without re-entering unaffected information.
- **FR-006**: Permanent deletion of a lecturer or room MUST require explicit planner confirmation.
- **FR-007**: When a lecturer or room requested for deletion has an active-course eligibility relationship or any Draft Session reference, the system MUST prevent destructive deletion, mark the resource inactive, preserve every relationship and session assignment, and identify each affected active course plus the type and count of session references.
- **FR-008**: When a lecturer or room requested for deletion has no active-course eligibility relationship and no Draft Session reference, the system MUST require confirmation, remove any eligibility relationships from inactive courses, and permanently delete the resource and availability records that belong only to it.
- **FR-009**: Automatic cleanup during permitted deletion MUST NOT reactivate, delete, or otherwise alter inactive courses, Draft Sessions, or other resource records beyond removing their obsolete eligibility relationship to the deleted resource.
- **FR-010**: Editing a resource MUST NOT change the lecturer or room identity assigned to any existing Draft Session.
- **FR-011**: The system MUST detect stale resource, availability, and eligibility changes and prevent them from silently overwriting a newer saved change.
- **FR-012**: The planner MUST be able to create, view, edit, and delete recurring weekly and dated unavailable periods for each lecturer and room.
- **FR-013**: A recurring unavailable period MUST specify at least one weekday, a start time, and a later end time, and MUST recur on each selected weekday until changed or removed.
- **FR-014**: A dated unavailable period MUST specify a start date and time and a later end date and time and MUST apply only to that dated interval.
- **FR-015**: A resource MUST be treated as available when no applicable unavailable period overlaps the proposed session and all other scheduling constraints permit use.
- **FR-016**: Any positive-duration overlap between a session and an applicable recurring or dated unavailable period MUST make the resource unavailable for that session; an end boundary equal to a start boundary MUST NOT count as overlap.
- **FR-017**: Exact duplicate unavailable periods for the same resource MUST be rejected; partially overlapping periods MUST be allowed and interpreted as the union of their unavailable time.
- **FR-018**: Dated unavailable periods MUST add to recurring unavailability and MUST NOT cancel or reopen time made unavailable by another rule.
- **FR-019**: The planner MUST be able to associate multiple distinct eligible lecturers and multiple distinct eligible rooms with each course.
- **FR-020**: Every course available for new generation MUST have at least one eligible lecturer and one eligible room, and a planner-initiated eligibility update MUST NOT remove the last resource of either type. Automatic capacity cleanup after cohort growth MAY leave a course without an eligible room, in which case it MUST become unavailable for new generation.
- **FR-021**: A room MUST NOT be newly associated as eligible when its capacity is below the course cohort size; the system MUST state the required and available capacity.
- **FR-022**: If a room capacity edit makes an existing course eligibility relationship insufficient, the relationship MUST remain visible as invalid, the room MUST be excluded as a valid new generation choice for that course, and affected sessions MUST remain unchanged for validation.
- **FR-023**: Removing a resource from a course's eligibility set MUST NOT rewrite or remove any existing Draft Session assignment.
- **FR-024**: A resource outside the current course eligibility set MUST NOT be newly assigned to a Draft Session; an existing assignment that later becomes ineligible MUST remain reviewable and MUST be identified by validation.
- **FR-025**: Every Draft Session MUST reference exactly one lecturer and exactly one room, even when its course has multiple eligible resources.
- **FR-026**: Resource administration, course eligibility, Draft Session assignment, usage, and protected-deletion views MUST show each resource's display name and reference code and expose current room capacity, unavailable periods, course relationships, and Draft Session usage needed to understand resource suitability and identity.
- **FR-027**: Current lecturer and room records, course eligibility sets, room capacities, unavailable periods, and soft-preference semantics MUST be available together to generation and validation workflows after a successful change.
- **FR-028**: Validation MUST identify, as separate applicable issues, an assigned lecturer or room that is not eligible for the course, an assignment that overlaps resource unavailability, and a room whose capacity is below cohort size.
- **FR-029**: Resource, eligibility, capacity, or availability changes MUST NOT automatically move, delete, or reassign existing Draft Sessions.
- **FR-030**: When more than one lecturer is eligible, contiguous blocks of chronologically adjacent sessions within one individual course's Draft Schedule MUST be preferred over repeated alternation.
- **FR-031**: Lecturer-block preference MUST NOT assign lecturer quotas, target unit counts, lecturer rankings, or a requirement to use every eligible lecturer in this slice; it MUST be derived from the eligible lecturer set and interpreted as minimizing lecturer changes where hard constraints allow.
- **FR-032**: When more than one room is eligible, reuse of the same eligible room across a course's sessions MUST be represented as the room preference over unnecessary room changes.
- **FR-033**: Room reuse preference MUST NOT rank eligible rooms or make same-room reuse mandatory; every eligible room that satisfies hard constraints MUST remain an acceptable choice.
- **FR-034**: Availability, eligibility, and capacity MUST take precedence over lecturer-block and room-reuse preferences; preference satisfaction MUST NOT make a hard-rule violation valid.
- **FR-035**: For each existing course with one lecturer and one room when this feature is introduced, the system MUST preserve those relationships as the initial eligible lecturer and room and MUST leave existing Draft Session assignments unchanged.
- **FR-036**: The feature MUST preserve established FS-001 through FS-007 planning, review, editing, validation, multi-course generation, and academic-administration behavior except where this specification explicitly broadens resource administration and resource inputs.
- **FR-037**: This slice MUST NOT perform global conflict-aware optimization, choose resource combinations to maximize scheduled units, administer holidays or exams, grant lecturer access, add authentication, or synchronize with external systems.
- **FR-038**: Every create, edit, delete, availability, and eligibility action MUST provide clear success or actionable failure feedback.
- **FR-039**: An inactive lecturer or room MUST remain visible in administration and historical Draft Session context but MUST be excluded from new course eligibility choices, new session assignments, generation choices, and default active-resource lists; the planner MUST be able to include inactive resources explicitly when reviewing administration.
- **FR-040**: If inactivating a resource leaves an active course without an active eligible lecturer or room, the course MUST remain visible but unavailable for new generation until a valid active replacement is associated, and the retirement result MUST identify the affected course.
- **FR-041**: Lecturer-block and room-reuse preferences MUST always be considered independently for each individual course's Draft Schedule, MUST NOT require planner, course, or global enablement settings, and MUST NOT apply across unrelated courses or historical Draft Schedules.
- **FR-042**: Reference-code uniqueness comparisons MUST ignore capitalization differences and surrounding whitespace within the lecturer catalog and within the room catalog; the same normalized code MAY be used once in each different catalog.
- **FR-043**: When a cohort-size increase makes an eligible room's capacity insufficient, the system MUST automatically remove that room from every affected course's eligibility set, MUST NOT change existing Draft Session assignments, MUST identify those sessions with capacity and ineligibility alerts, and MUST identify every course left unavailable because no eligible room remains.
- **FR-044**: The planner MUST be able to reactivate an inactive lecturer or room only when its current required values and reference-code uniqueness are valid. Reactivation MUST restore the resource to active choices and make preserved course eligibility relationships usable where current capacity and all other hard rules permit, without changing existing Draft Session assignments; relationships that fail current hard rules MUST remain visible but unusable until repaired.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Automated coverage MUST verify valid and invalid resource creation and editing, duplicate display names with distinct reference codes, normalized reference-code uniqueness, inactivation for active-course and Draft Session references, valid and invalid reactivation with relationship restoration, permitted deletion with inactive-course eligibility cleanup, confirmation cancellation, and stale-change protection.
- **TR-003**: Automated coverage MUST verify recurring and dated unavailability, boundary overlap, duplicate and overlapping periods, and downstream validation after availability changes.
- **TR-004**: Automated coverage MUST verify multiple eligible resources, capacity-gated room eligibility, planner-initiated last-eligible-resource protection, cohort-growth cleanup including removal of the last room, exactly one lecturer and room per session, and preservation of existing assignments after eligibility changes.
- **TR-005**: Automated coverage MUST verify migration of existing single resource assignments and continued operation of FS-001 through FS-007 workflows.
- **TR-006**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Lecturer**: A planner-maintained teaching resource with a stable identity, display name, planner-maintained reference code unique among lecturers, active or inactive lifecycle state, unavailable periods, course eligibility relationships, and possible Draft Session assignments.
- **Room**: A planner-maintained location resource with a stable identity, display name, planner-maintained reference code unique among rooms, active or inactive lifecycle state, positive whole-number capacity, unavailable periods, course eligibility relationships, and possible Draft Session assignments.
- **Resource Unavailability Period**: A weekly recurring or dated interval during which exactly one lecturer or room cannot be assigned to an overlapping session.
- **Course Resource Eligibility**: The distinct set of lecturers and rooms the planner permits for a course; at least one of each is required for new generation and eligible rooms must satisfy cohort capacity when associated.
- **Resource Assignment Preference**: The always-considered meaning within one individual course's Draft Schedule that later scheduling should minimize lecturer switches and unnecessary room changes without overriding eligibility, availability, capacity, conflicts, or other hard rules; it contains no enablement setting, lecturer quota, requirement to use every eligible lecturer, or resource ranking in this slice.
- **Draft Session Resource Assignment**: The exactly one lecturer and exactly one room attached to a session; it remains stable when source eligibility or availability changes and is evaluated against current resource rules by validation.
- **Resource Reference**: A course eligibility relationship or Draft Session assignment that protects a lecturer or room from destructive deletion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an unaided acceptance exercise with at least 10 representative planner users or acceptance reviewers familiar with the planner, at least 90% can create a coded lecturer, create a coded capacity-valid room, and associate two eligible lecturers and two eligible rooms with a course within 5 minutes on their first attempt.
- **SC-002**: In the same exercise, at least 90% can add one recurring and one dated unavailable period and correctly identify the resulting unavailable times without assistance within 3 minutes.
- **SC-003**: In 100% of tested deletion attempts involving an active course or Draft Session, destructive deletion is prevented, the resource becomes inactive, and all references remain intact; in 100% of attempts involving only inactive-course eligibility and no Draft Session, confirmed deletion removes those obsolete eligibility links and the resource without changing the inactive courses otherwise.
- **SC-004**: In at least 90% of unaided protected-deletion exercises, participants can identify every blocker type and the next available corrective action within 2 minutes using only the displayed feedback.
- **SC-005**: In 100% of tested session assignments, each session contains exactly one lecturer and one room; adding more eligible resources never creates multiple simultaneous assignments.
- **SC-006**: In 100% of tested resource-rule violations, validation separately identifies ineligible assignments, unavailable-resource overlaps, and insufficient room capacity while leaving saved sessions unchanged.
- **SC-007**: In 100% of tested availability boundaries, positive-duration overlap is treated as unavailable and exactly touching boundaries are treated as non-overlapping.
- **SC-008**: After a successful resource, eligibility, capacity, or availability change, affected planner views and validation use the current saved values within 2 seconds under the documented normal acceptance dataset, without a restart or developer action.
- **SC-009**: The planner can maintain and inspect at least 100 lecturers, 100 rooms, 100 courses, and 1,000 unavailability periods, and 95% of administration views and save outcomes become usable within 2 seconds in the documented reference acceptance environment.
- **SC-010**: All applicable FS-001 through FS-007 acceptance scenarios continue to pass, and 100% of pre-existing courses begin with their prior lecturer and room in their initial eligibility sets without changing any existing Draft Session assignment.
- **SC-011**: In 100% of tested cohort-size increases, every newly insufficient room is removed from all affected course eligibility sets, every existing Draft Session remains assigned and receives applicable capacity and eligibility alerts, and every course left without a room is visibly unavailable for new generation.
- **SC-012**: In 100% of tested reactivation attempts, invalid resources remain inactive with actionable feedback; valid resources return to active choices, preserved eligibility becomes usable only where current hard rules permit, and no existing Draft Session assignment changes.

## Assumptions

- FS-007 academic records and course relationships exist and remain the authoritative dependency for course, cohort, semester, and study-type administration.
- One planner-user role maintains all in-scope resources. Authentication, authorization distinctions, and lecturer self-service remain outside this slice.
- Availability is expressed as unavailability against an otherwise available resource. Recurring weekly and dated unavailable periods combine as a union; this slice does not introduce positive availability overrides, so a dated period cannot reopen recurring unavailable time.
- Recurring unavailability is an ongoing weekly pattern without a separate effective date range. A temporary pattern can be represented through dated unavailable periods and revised when circumstances change.
- Lecturer blocks have no explicit unit allocation, quota, order, or lecturer ranking. The preference is derived from eligibility alone and means minimizing lecturer changes across a course's sessions in chronological order when later scheduling applies it.
- Eligible rooms have no rank. The only room preference in this slice is to minimize unnecessary room changes while allowing any eligible, available, capacity-sufficient room.
- Lecturer-block and room-reuse preferences are always considered separately within each individual course's Draft Schedule. They may be unsatisfied when hard constraints require multiple lecturers or rooms, and they do not span unrelated courses or historical schedules. Configurable switches, weights, and global trade-off decisions are not part of this slice.
- Multiple resources with the same display name are legitimate. Each has a planner-maintained reference code unique within its own resource catalog, compared without regard to capitalization or surrounding whitespace; the same normalized code may appear once among lecturers and once among rooms.
- Active-course eligibility or any Draft Session reference prevents destructive resource deletion and causes the resource to become inactive. Eligibility links from inactive courses do not prevent deletion when no Draft Session references the resource and are removed as part of the confirmed cleanup.
- Inactivation is reversible. Reactivation restores preserved eligibility only where the resource and relationship satisfy current validity rules and never rewrites an existing Draft Session assignment.
- Resource edits affect future choices and current validation but do not silently reassign existing sessions. This slice does not introduce schedule publication or historical-version rules.
- A planner-initiated eligibility update must retain at least one eligible lecturer and one eligible room. Resource retirement or automatic capacity cleanup may leave a course without an active or usable resource, in which case the course remains visible but unavailable for new generation until repaired. Existing single assignments become the initial eligibility sets so the dependency on FS-007 remains valid during transition.
- Capacity is a hard validity rule for generation. Existing manually controlled sessions remain visible with non-blocking validation feedback in accordance with established manual-editing and validation behavior.
- When an FS-007 cohort-size increase makes an eligible room insufficient, the eligibility relationship is cleaned up automatically rather than preserved as invalid; existing Draft Session assignments remain protected for review and validation.
- This slice records and exposes the complete resource choice set and its rules but does not automatically search for the best cross-course assignment; that outcome belongs to FS-010.
