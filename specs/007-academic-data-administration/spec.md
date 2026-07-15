# Feature Specification: Academic Planning Data Administration

**Working Branch**: `master`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Create FS-007: Academic Planning Data Administration so a planner user can safely create, view, edit, delete, archive, and reuse the academic records required by existing scheduling workflows without developer-seeded data or external synchronization."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-15

- Q: What planner-facing value determines uniqueness for semesters, cohorts, courses, and study types? → A: The normalized name is unique within each record category; the same name may be used in a different category.
- Q: What happens when edited semester dates would place saved sessions outside the semester? → A: Block the edit if any saved session would fall outside the new dates.
- Q: Which academic values remain unchanged when their source records are edited after a schedule is saved? → A: The saved schedule retains all captured names, units, cohort identity and size, and study type values; future planning uses current source records.
- Q: What happens to dependent record statuses when a semester, cohort, or study type is archived? → A: Dependent statuses do not change; dependents remain visible but are unavailable for new planning while a required parent is inactive.
- Q: How is a course made available for a semester? → A: Each course is explicitly assigned to exactly one current semester; saved schedules from earlier semester assignments remain usable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build the Academic Planning Catalog (Priority: P1)

A planner creates semesters or planning periods, cohorts or classes, study types and their weekly time windows, and courses assigned to semesters so the records needed to plan a semester are available without developer intervention.

**Why this priority**: A complete, valid academic catalog is the prerequisite for using the existing schedule generation and review workflows without seeded data.

**Independent Test**: Starting with no academic records, create one valid record of each type, connect the course to its cohort and study type, assign it to the semester, and verify that the resulting combination is selectable for planning.

**Acceptance Scenarios**:

1. **Given** no academic records exist, **When** the planner creates a valid semester, cohort, study type, weekly time window, and course assigned to the semester, **Then** every record and relationship remains available after leaving and returning to administration.
2. **Given** a course has valid units, cohort, study type, and one active assigned semester, **When** the planner opens the existing planning workflow for that semester, **Then** the course is available as a compatible planning option.
3. **Given** a course is assigned to a different semester, **When** the planner views the selected semester's course options, **Then** the course is not offered for new planning in that semester.
4. **Given** a required value or relationship is missing or invalid, **When** the planner attempts to save the record, **Then** the record is not saved and the feedback identifies each value or relationship that must be corrected.
5. **Given** an equivalent unique identity already exists in the same catalog, **When** the planner attempts to create or rename another record to that identity, **Then** the conflicting record is not saved and the existing conflict is explained.
6. **Given** a migrated course has no safely inferable current semester, **When** the planner opens administration, **Then** the course and its saved schedules remain visible, the course is identified as requiring a semester assignment, and it cannot be used for new planning until the planner assigns one.
7. **Given** existing records contain normalized-name conflicts, **When** administration becomes available, **Then** the application remains usable, each conflict is identified for planner repair, and no new or reactivated record may introduce or preserve an unresolved duplicate identity.

---

### User Story 2 - View and Correct Academic Records (Priority: P2)

A planner can find academic records, inspect their scheduling relationships and current usage, and correct editable details while preserving the facts already stored in saved schedules.

**Why this priority**: Academic data changes over time, and planners need to correct it safely without turning routine maintenance into developer work or changing schedule history unexpectedly.

**Independent Test**: Edit the label, size, units, dates, and relationships of representative records, verify the updated values are used for future planning choices, and verify a previously saved schedule still displays the facts captured when it was saved.

**Acceptance Scenarios**:

1. **Given** academic records exist, **When** the planner opens a catalog view, **Then** the planner can view each record's identifying details, active status, required relationships, and whether it is used by dependent records or saved schedules.
2. **Given** a record is not otherwise invalidated by the change, **When** the planner edits and saves it, **Then** the updated current value appears in administration and in subsequent applicable planning selections.
3. **Given** a saved schedule contains academic facts captured from source records, **When** the planner edits a source name, course units, cohort identity or size, or study type, **Then** the saved schedule retains every captured value while future planning uses the current source values.
4. **Given** an edit would make a required relationship invalid, **When** the planner attempts to save it, **Then** the edit is rejected and the planner is told which dependent relationship prevents the change.
5. **Given** an academic record is linked to several other records or saved schedules, **When** the planner inspects its usage, **Then** the feedback distinguishes dependent catalog records from saved schedule usage.
6. **Given** a semester has saved sessions, **When** the planner attempts to change its dates so that any saved session would fall outside the new interval, **Then** the edit is rejected, the existing semester and sessions remain unchanged, and the conflicting session usage is explained.
7. **Given** a course has a current semester assignment and saved schedules from that or an earlier assignment, **When** the planner reassigns the course to another semester, **Then** the saved schedules remain unchanged and the course becomes available for new planning only in the newly assigned semester.

---

### User Story 3 - Retire or Delete Records Safely (Priority: P3)

A planner can remove unused records, make referenced records inactive when they should no longer be used for new planning, and reactivate inactive records when appropriate. Destructive actions never invalidate required relationships or saved schedules.

**Why this priority**: Catalog maintenance must prevent accidental loss while still letting planners keep obsolete options out of new planning workflows.

**Independent Test**: Delete an unused record, attempt to delete records referenced by a dependent record and by a saved schedule, archive a protected record, and verify historical use remains readable while the inactive record is excluded from new selections.

**Acceptance Scenarios**:

1. **Given** a record has no dependent records and is not referenced by a saved schedule, **When** the planner confirms deletion, **Then** the record is deleted and no longer appears in administration or planning options.
2. **Given** a record is required by another academic record, **When** the planner attempts deletion, **Then** deletion is prevented and the feedback identifies the type and number of blocking dependents and the action needed first.
3. **Given** a record is referenced by a saved schedule, **When** the planner attempts deletion, **Then** deletion is prevented without altering the schedule and the feedback explains that saved schedule history protects the record.
4. **Given** a protected record is no longer intended for new planning, **When** the planner marks it inactive, **Then** it remains visible in administration and historical schedule context but is unavailable for new planning selections.
5. **Given** an inactive record and all of its required relationships are valid, **When** the planner reactivates it, **Then** it becomes available again wherever its semester assignment and relationships permit.
6. **Given** one or more courses are assigned to a semester, **When** the planner attempts to delete the semester, **Then** deletion is prevented until every course is reassigned or otherwise safely removed, and saved schedule usage continues to protect historical data.
7. **Given** a semester, cohort, or study type has active dependent records, **When** the planner marks the parent inactive, **Then** dependent statuses remain unchanged, the dependents remain visible, and they are unavailable for new planning until every required parent is active again.

---

### User Story 4 - Continue Existing Planning with Updated Options (Priority: P4)

After maintaining the catalog, a planner can continue using the established single-course and multi-course generation, constraint, editing, overview, and validation-alert workflows with refreshed, compatible choices.

**Why this priority**: Administration provides value only if its records are immediately and safely usable by FS-001 through FS-006 without regressing existing work.

**Independent Test**: Change catalog records, return to each affected existing workflow, and verify current assigned options refresh while saved schedules and unrelated selections remain usable.

**Acceptance Scenarios**:

1. **Given** the planner creates or activates a valid course assigned to an active semester, **When** the planner returns to an existing planning selector for that semester, **Then** the new option is available without developer intervention.
2. **Given** the planner archives or deletes an option, **When** planning choices refresh, **Then** it is not available for new selection and an existing saved schedule that used it remains reviewable.
3. **Given** a currently selected option becomes invalid or inactive during administration, **When** the planner returns to planning, **Then** the interface does not silently substitute another option and clearly requires a valid current choice before a new generation action.
4. **Given** academic records and saved schedules existed before FS-007, **When** administration becomes available, **Then** those records and schedules remain usable and their previously valid planning relationships are preserved.
5. **Given** catalog maintenance does not affect a saved schedule, **When** the planner reviews or edits that schedule through an existing workflow, **Then** the established FS-001 through FS-006 behavior remains available.
6. **Given** a Course otherwise qualifies for the selected Semester but its Study Type has no active usable Time Window, **When** planning options refresh, **Then** the Course remains visible with an unavailable status and missing-window reason, and generation is blocked with actionable feedback until a valid window exists.

### Edge Cases

- A semester end date precedes its start date, or edited dates would exclude one or more saved sessions; saving is rejected with date- or session-specific feedback and the existing semester remains unchanged.
- A cohort size or course unit value is absent, zero, negative, or fractional; saving is rejected without losing the entered correction context. This slice imposes no additional upper product limit.
- A Study Type Time Window has no weekday, has an end that is not after its start, or exactly duplicates another window for the same study type; saving is rejected with the conflicting value identified.
- Two names differ only by capitalization or surrounding whitespace; they are treated as the same name for duplicate detection.
- A planner changes a record's identity to collide with another record; the original record remains unchanged after the failed save.
- A planner reassigns a course to another semester; its saved schedules in earlier semesters remain reviewable, while the course becomes available for new planning only in its new assigned semester.
- Existing data contains saved schedules for one course in multiple semesters; every schedule remains usable, but the course has only one current semester assignment for new planning.
- A migrated course has no safely inferable current semester; it remains visible for planner repair and its saved schedules remain usable, but it is unavailable for new planning until assigned.
- Existing records collide after capitalization and surrounding-whitespace normalization; startup and existing use continue, the conflicts are visibly marked for repair, and the planner must rename them uniquely before successful update or reactivation.
- A course's cohort or study type is inactive; the course remains inspectable, but it is not offered for new planning until all required relationships are active and valid.
- An inactive parent is reactivated while another required parent remains inactive; dependent records keep their own status and remain unavailable for new planning until all required parents are active.
- A study type has no active valid weekly time window; it remains maintainable, but courses using it cannot start generation that depends on a default window and receive actionable feedback.
- A semester reaches its end date; it does not become inactive automatically, because lifecycle changes are planner-controlled.
- A record is archived and another record is created with the same normalized name; creation is blocked because inactive records remain part of their record category.
- Two planner views are open and one saves a newer change before the other saves; the later stale save must not silently overwrite the newer record.
- The planner cancels a delete confirmation; the record, its status, its relationships, and all saved schedules remain unchanged.
- A catalog refresh cannot be completed; the planner is told that current options may be unavailable and no existing selection or saved schedule is silently changed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide planner-accessible administration for semesters or planning periods, cohorts or classes, courses, study types, and Study Type Time Windows.
- **FR-002**: The planner MUST be able to create, view, edit, and request deletion of every academic record type in scope.
- **FR-003**: The system MUST retain successfully saved academic records so they remain available across later planner sessions.
- **FR-004**: A semester MUST have a name that is unique among semesters, a start date, and an end date that is not earlier than its start date.
- **FR-005**: A cohort MUST have a name that is unique among cohorts and a positive whole-number size; FS-007 MUST NOT impose an additional upper product limit.
- **FR-006**: A study type MUST have a name that is unique among study types.
- **FR-007**: A Study Type Time Window MUST belong to exactly one study type and specify a weekday, start time, and later end time.
- **FR-008**: The system MUST reject an exact duplicate weekday/start/end time window for the same study type.
- **FR-009**: Every newly created or successfully updated course MUST have a name that is unique among courses, positive whole-number total, minimum-session, and maximum-session units, exactly one cohort, exactly one study type, and exactly one current assigned semester. Minimum-session units MUST NOT exceed maximum-session or total units, and maximum-session units MUST NOT exceed total units; FS-007 MUST NOT impose an additional upper product limit.
- **FR-010**: The system MUST make a course available for new planning only in its one current assigned semester; semester availability MUST NOT be inferred from the existence of other active semesters.
- **FR-011**: The planner MUST be able to reassign a course from one semester to another without creating a second simultaneous current semester assignment.
- **FR-012**: The system MUST require all mandatory values and relationships before saving a record and MUST identify every detected correction needed in understandable planner language.
- **FR-013**: Identity uniqueness comparisons MUST ignore capitalization differences and surrounding whitespace within each record type's catalog.
- **FR-014**: The system MUST preserve the planner's entered values after a validation failure so corrections can be made without re-entering unaffected information.
- **FR-015**: The system MUST let the planner inspect a record's current active status and the presence of dependent academic records and saved schedule usage before a destructive action.
- **FR-016**: The system MUST require explicit planner confirmation before permanently deleting an academic record.
- **FR-017**: The system MUST permanently delete a record only when it has no required dependent academic records and no saved schedule reference.
- **FR-018**: The system MUST NOT cascade a deletion when doing so would delete or invalidate a required dependent record or any saved schedule fact.
- **FR-019**: When deletion is blocked, the system MUST distinguish saved schedule references from dependent academic records, state the type and count of blockers, and explain the prerequisite action where one is available.
- **FR-020**: The planner MUST be able to mark any protected academic record inactive instead of deleting it and to reactivate it when its required values, relationships, and uniqueness remain valid.
- **FR-021**: Inactive records MUST remain visible and identifiable in administration and saved schedule context but MUST be excluded from new planning choices.
- **FR-022**: A course MUST be available for new planning only when the course, its one assigned semester, cohort, and study type are active and valid.
- **FR-023**: A missing active Study Type Time Window MUST keep an otherwise eligible course visible in planning with an unavailable status and a missing-window reason, prevent generation that depends on that default, and produce actionable feedback; it MUST NOT cause the system to invent a window.
- **FR-024**: Editing a source academic record MUST NOT rewrite any course name, course units, Semester relationship, Cohort identity or size, Study Type identity, or other in-scope academic fact already captured by a saved schedule. FS-007 MUST NOT redefine the established historical handling of Lecturer or Room assignments.
- **FR-025**: New planning and newly saved schedule facts MUST use the current valid names, course units, Semester relationship, Cohort identity and size, and Study Type identity at the time the new planning action is performed. Lecturer and Room handling MUST continue to follow the established FS-001 through FS-006 behavior.
- **FR-026**: The system MUST reject an edit that would leave a required dependent relationship invalid and MUST identify the blocking relationship.
- **FR-027**: The system MUST prevent deletion of a semester while any course is currently assigned to it or any saved schedule references it, and MUST identify both kinds of blocking usage.
- **FR-028**: Reassigning a course to another semester MUST leave every saved schedule from an earlier assignment unchanged and MUST make the course available for new planning only in its newly assigned semester.
- **FR-029**: Academic catalog changes MUST refresh affected current planning options without silently changing unrelated selections or saved schedules.
- **FR-030**: If a previously selected planning option is no longer assigned to the selected semester, active, or valid, the system MUST identify the invalid selection and require the planner to choose a valid option before a new generation action.
- **FR-031**: Academic records and saved schedules that existed before this feature MUST remain usable; a course available for new planning MUST have only one current semester assignment, while saved schedules in any earlier semesters remain reviewable and editable through established workflows.
- **FR-032**: The system MUST preserve the existing FS-001 through FS-006 single-course generation, multi-course generation, constraint configuration, schedule review, manual session editing, and non-blocking validation-alert workflows.
- **FR-033**: The system MUST detect a stale edit or destructive request and prevent it from silently overwriting a more recent change.
- **FR-034**: The system MUST provide clear success or failure feedback for every create, edit, archive, reactivate, semester-reassignment, and delete action.
- **FR-035**: The feature MUST NOT administer lecturer or room availability, multiple eligible resources, holidays, exams, authentication, lecturer access, or external import and synchronization.
- **FR-036**: The system MUST reject a semester date edit when any saved session would fall before the proposed start date or after the proposed end date, identify the blocking saved-session usage, and leave the semester and schedules unchanged.
- **FR-037**: Archiving or reactivating a semester, cohort, or study type MUST NOT automatically change any dependent record's active status; dependents MUST remain visible and MUST be excluded from new planning whenever a required parent is inactive.
- **FR-038**: A migrated course for which no current semester can be determined safely MAY temporarily have no current assignment; it MUST remain visible and assignable in administration, retain all saved schedule usage, be identified as requiring repair, and be unavailable for new planning. It MUST NOT remain unassigned after a successful create or edit.
- **FR-039**: Existing normalized-name conflicts MUST NOT prevent application startup or make existing records and schedules unusable. Each conflict MUST be visible and require a unique rename before that record can be successfully edited or reactivated, and the system MUST reject every new conflict.
- **FR-040**: Course administration MUST include name, total units, minimum and maximum session units, one Semester, one Cohort, one Study Type, and the existing single Lecturer and Room assignments. Lecturer and Room choices MUST be read-only options in this slice; if either option type is unavailable, Course creation MUST be blocked with actionable feedback and MUST NOT invent a placeholder resource.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Backend behavior MUST be verified with FastAPI-compatible tests, normally using `pytest`.
- **TR-003**: Frontend behavior MUST be verified through React/Vite-appropriate checks, such as build, lint, component, or UI tests.
- **TR-004**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.
- **TR-005**: Automated coverage MUST verify valid and invalid creation, every protected-deletion reason, archive/reactivation behavior, uniqueness rules, single-semester course assignment and reassignment, and saved-schedule historical preservation.
- **TR-006**: Automated coverage MUST verify that FS-001 through FS-006 planning options and workflows continue to operate with existing and newly maintained academic records.

### Key Entities

- **Semester / Planning Period**: A dated academic planning interval with a name unique among semesters and an active or inactive lifecycle state.
- **Cohort / Class**: A student group with a name unique among cohorts, a size, lifecycle state, and relationships to courses and saved schedule facts.
- **Course**: A teaching subject with a name unique among courses, total and session-unit values, one cohort, one study type, the existing single Lecturer and Room assignments, lifecycle state, exactly one current assigned semester for new planning after creation or successful edit, and potential saved schedule usage in current or earlier semesters.
- **Study Type**: A mode or pattern of study with a name unique among study types that owns default weekly time windows and may be required by courses.
- **Study Type Time Window**: One allowed default weekly interval identified by its study type, weekday, start time, and end time.
- **Saved Schedule Reference**: Durable evidence that a schedule captured in-scope academic facts, including names, course units, Semester assignment, Cohort identity and size, and Study Type identity; it protects referenced source records from destructive removal without preventing a course's current Semester from being reassigned. Lecturer and Room historical handling remains governed by the established workflows outside this slice's preservation boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an unaided acceptance exercise with at least 10 representative planner users or acceptance reviewers familiar with the current planner, at least 90% can create a complete valid semester, cohort, study type with a time window, and course assigned to that semester within 5 minutes on their first attempt.
- **SC-002**: In the same exercise, at least 90% can identify and correct all deliberately invalid required values and relationships on their first attempt using only the displayed feedback.
- **SC-003**: In 100% of tested deletion attempts involving a dependent academic record or saved schedule, deletion is prevented and no dependent or historical data changes.
- **SC-004**: In at least 90% of unaided protected-deletion exercises, participants can identify why deletion is blocked and either locate the prerequisite dependent record or choose the inactive alternative within 2 minutes.
- **SC-005**: In 100% of tested source-edit cases, previously saved schedule facts and labels remain unchanged while subsequent planning choices use the current valid source values.
- **SC-006**: In 100% of tested assignment combinations, a course is available for generation only in its one current assigned semester when all required records and relationships, including an active usable Study Type Time Window, are valid; a course that is visible but unavailable is clearly identified as unavailable, and saved schedules from earlier assignments remain usable.
- **SC-007**: After a successful catalog change, affected planning choices show the current valid option set within 2 seconds under the documented normal acceptance dataset, without requiring a restart or developer action.
- **SC-008**: A planner can maintain at least 100 records of each in-scope catalog type, and 95% of administration views and save outcomes become usable within 2 seconds in the documented reference acceptance environment.
- **SC-009**: All existing FS-001 through FS-006 acceptance scenarios continue to pass with both pre-existing academic data and records created through administration.
- **SC-010**: In 100% of tested stale-edit cases, the newer saved record remains unchanged and the planner receives feedback that a refresh or review is required.

## Assumptions

- One planner-user role has access to all in-scope administration; authentication and finer-grained permissions remain outside this slice.
- Manual administration is authoritative for this release; no provider-specific identifiers or ownership rules are required.
- Records that cannot be safely deleted support a planner-controlled inactive state. Inactivity is reversible and is not triggered automatically by dates or non-use.
- Inactive status does not cascade through relationships. A dependent record retains its own status but cannot be used for new planning while any required parent is inactive.
- Names are unique within their own record category, compared without regard to capitalization or surrounding whitespace. The same normalized name may be used in a different record category.
- Exact duplicate Study Type Time Windows are invalid; partially overlapping windows are not treated as duplicates in this slice and continue to follow existing planning behavior.
- Saved schedules retain the in-scope academic facts captured when they were saved, including names, course units, Semester assignment, Cohort identity and size, and Study Type identity. Editing an in-scope academic source record affects future planning only and does not revise those saved facts. This slice does not change or extend the established historical treatment of Lecturer or Room assignments.
- Every course is explicitly assigned to exactly one current semester for new planning. Reassignment changes future availability but never rewrites or removes saved schedules from earlier semester assignments.
- Existing academic records and saved schedules remain usable when administration is introduced. If a course has saved schedules in multiple semesters, those schedules remain available while only one semester is treated as the course's current assignment for new planning.
- Cohort size and Course total/minimum/maximum unit values use positive whole numbers. Minimum-session units cannot exceed maximum-session or total units, and maximum-session units cannot exceed total units. This slice defines no additional upper product limit.
- Existing Lecturer and Room records are selectable read-only dependencies for Course administration. Their CRUD, availability, and multiple-resource eligibility remain out of scope, and no placeholder resource is created when an option is missing.
- Deleting a time window is allowed only when its removal does not leave a required dependent relationship invalid; courses whose study type has no active usable window receive existing generation validation rather than an invented default.
- Permanent deletion is intended for unused erroneous or duplicate-free setup data; archiving is the normal way to retire data that has been used.
