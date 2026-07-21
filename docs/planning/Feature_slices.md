# Feature Slices

## Document purpose

This document is the ground truth for the Resource Planner's product goals, current scope, explicit exclusions, external-system boundaries, development slices, dependencies, and later scope changes. Detailed requirements belong in the corresponding Spec Kit feature directories and must remain consistent with this document.

The earlier roadmap in `docs/planning/Planner_Resource_Feature_Slices_Scope.md` is retained as historical planning input. Where it differs from this document, this document takes precedence.

## Product overview

### Product goal

The Resource Planner helps university planner users create, review, correct, and publish semester teaching and exam schedules. Its intended outcome is to maximize scheduled teaching units while avoiding known resource conflicts, make unavoidable gaps and their causes visible, and keep the planner in control of exceptional and changing situations.

### Initial release goal

The implemented baseline, FS-001 through FS-006, allows a planner user to generate one or several course drafts, configure course-semester constraints, review the semester, edit existing sessions, and inspect non-blocking validation alerts.

The planner-only MVP is complete when it additionally allows the planner to maintain planning data and availability, use multiple eligible resources, add or delete sessions, produce conflict-aware partial or complete semester plans, avoid institution-wide holidays, schedule exams, manage versioned publication states, and operate through a calendar-centered planning workspace.

Lecturer collaboration, authenticated role separation, and external data synchronization are later releases and are not prerequisites for the planner-only MVP.

### Target users and actors

- **Planner user**: The primary actor. Earlier specifications use both “admin” and “office staff”; both terms mean this same planner-user role. The planner manages planning data, generation, manual corrections, review states, and publication.
- **Lecturer**: A later-release reviewer. A lecturer may inspect assigned sessions, comment, and flag impossible sessions, but cannot change a schedule.
- **External planning-data provider**: An unknown future system that may supply planning records through a provider-neutral integration.

### Main user outcomes

- Maintain the academic and resource data needed for scheduling without developer intervention.
- Generate complete or maximally complete semester schedules for one or several courses.
- Avoid lecturer, room, and cohort conflicts while respecting availability and capacity.
- Understand remaining unscheduled units and why they could not be placed.
- Correct schedules manually without losing saved generation constraints.
- Avoid institution-wide public holidays and schedule course exams.
- Review conflicts, remaining work, failures, and schedule states in a filterable calendar workspace.
- Publish controlled schedule versions while retaining the current published version during later revisions.
- Later, collect lecturer feedback and import or synchronize planning data.

## Product scope

### In scope

- Planner-controlled course and multi-course draft generation by semester.
- Course-semester generation constraints and default teaching windows.
- Semester-wide list and calendar review with filters.
- Manual editing of existing Draft Sessions and non-blocking validation alerts.
- Manual administration of academic records, resources, availability, holidays, and exam requirements.
- Multiple eligible lecturers and rooms per course, with assignment preferences.
- Manual Draft Session creation and deletion, complete course-schedule deletion, and remaining-unit tracking.
- Global conflict-aware generation that maximizes scheduled units across the selected courses.
- Persisted partial plans with understandable unscheduled-unit reasons.
- Institution-wide holiday avoidance.
- Conflict-aware exam generation for explicitly enabled courses.
- Versioned `Draft → Ready for review → Published` lifecycle controlled by the planner.
- A calendar-centered operational workspace based incrementally on the saved UI reference.
- One consistent application navigation for Schedule and Academic Data without duplicate, dead, or overlapping controls.

### Out of scope

- Allowing lecturers to edit schedules directly.
- Requiring lecturer approval before a planner may publish.
- Silently replacing an existing schedule with a worse result.
- Automatically deleting or moving manually created sessions merely to improve optimization.
- Treating publication as an irreversible final state.
- Provider-specific integration behavior before a provider is selected.
- Automated email delivery or institutional SSO in the confirmed slice sequence.
- Full production or room-booking execution outside the planning and publication workflow.

### Possible later scope

- Accountless lecturer review through a time-limited link.
- Authenticated planner and lecturer accounts with role-based access.
- Provider-neutral import and synchronization of planning data.
- Automated review-email delivery, institutional SSO, and multi-lecturer token-review workflows.
- Provider-specific adapters after an external source and ownership rules are known.

## External systems and integrations

### Current planner-only MVP

No external system is required. Planner users maintain all planning records manually in the product. Existing local or seeded records may support development and migration, but are not the intended long-term data-entry workflow.

### Lecturer review link

FS-015 creates a secure review URL but does not send email. The planner copies the URL and sends it through an external communication channel. No email provider integration is required.

### Future planning-data integration

The provider is unknown. FS-017 therefore defines a provider-neutral import or synchronization boundary for lecturers, rooms, cohorts/classes, courses, semesters/planning periods, study types, time windows, holidays, availability, and exam requirements. Data ownership, conflict resolution, authentication, and synchronization direction must be clarified before FS-017 becomes ready for specification.

## UI and supporting material

- Existing React/Vite planner screens and component behavior from FS-001 through FS-006 are the current UI baseline.
- `docs/designs/resource-planner-calendar-screen-reference.png` is the confirmed visual inspiration for the future primary planner workspace.
- The reference shows a navigation rail, remaining-hours/course list, validation summaries, filterable week calendar, schedule cards, and a session detail editor. It is inspiration rather than a pixel-perfect mandate.
- Its elements should be introduced gradually through relevant slices instead of through one disruptive redesign.
- `docs/designs/resource-planner-unified-navigation-ground-truth.png` is the confirmed UX ground truth for the shared application navigation and its relationship to Academic Data screens.
- The navigation reference is authoritative for hierarchy, active-state treatment, and removal of the separate top view switcher; it does not expand the underlying administration workflows or data fields.

## Product-level constraints and assumptions

- The planner-only MVP remains a planner-user product and does not require authentication or role separation.
- One teaching unit is 45 minutes, and the implemented break and preferred-session-size rules remain authoritative unless a later specification explicitly changes them.
- A course may have multiple eligible lecturers and rooms; one Draft Session has exactly one lecturer and one room.
- Multi-lecturer teaching should use contiguous lecturer blocks instead of repeatedly alternating lecturers.
- Reusing the same eligible room is a preference, not a hard rule.
- Planner-created sessions may be saved with visible non-blocking validation alerts, consistent with current manual editing.
- Public holidays use one institution-wide calendar in the planner-only MVP.
- Published schedules are immutable snapshots. Later changes happen in a new draft revision while the current published version remains visible.
- The planner may move a revision to `Ready for review` or `Published` at any time and may publish despite missing or negative lecturer feedback.
- The existing FastAPI, SQLAlchemy, React, and Vite technology standards and the project constitution remain binding for later specification and implementation.

## Slice map

| Order | Slice ID | Slice name | User outcome | Depends on | Status |
| ----: | -------- | ---------- | ------------ | ---------- | ------ |
| 1 | FS-001 | Single-Course Draft Schedule Generation | Generate a valid draft for one course | None | Implemented |
| 2 | FS-002 | Review Generated Schedule in Planner UI | Inspect and filter generated sessions | FS-001 | Implemented |
| 3 | FS-003 | Configurable Generation Constraints and Courses Overview | Control generation windows and review a semester | FS-001, FS-002 | Implemented |
| 4 | FS-004 | Manual Session Editing | Correct existing generated sessions | FS-003 | Implemented |
| 5 | FS-005 | Conflict Detection | See non-blocking schedule validation alerts | FS-003, FS-004 | Implemented |
| 6 | FS-006 | Multi-Course Draft Generation | Generate several course drafts in one operation | FS-003, FS-005 | Implemented |
| 7 | FS-007 | Academic Planning Data Administration | Maintain academic scheduling inputs in the UI | FS-006 | Implemented |
| 8 | FS-008 | Resource Eligibility and Availability | Maintain eligible resources and availability | FS-007 | Implemented |
| 9 | FS-018 | Unified Application Navigation | Move consistently between Schedule and Academic Data | FS-007, FS-008 | Implemented |
| 10 | FS-009 | Manual Session Creation, Deletion, and Remaining Units | Complete or clear schedules manually | FS-006 | Implemented |
| 11 | FS-010 | Conflict-Aware Semester Optimization | Maximize conflict-free scheduled units | FS-008, FS-009 | Implemented |
| 12 | FS-011 | Institution-Wide Holiday Calendar and Avoidance | Prevent generation on public holidays | FS-007, FS-010 | Implemented |
| 13 | FS-012 | Conflict-Aware Exam Scheduling | Generate exams for enabled courses | FS-008, FS-010, FS-011 | Implemented |
| 14 | FS-013 | Versioned Review and Publication Lifecycle | Publish controlled schedule revisions | FS-006, FS-012 | Implemented — validation follow-ups open |
| 15 | FS-014 | Calendar Planning Workspace and Operational Dashboard | Operate the semester from one calendar overview | FS-009 through FS-013, FS-018 | Proposed |
| 16 | FS-015 | Accountless Lecturer Token Review | Collect scoped lecturer feedback by secure link | FS-013 | Proposed — later release |
| 17 | FS-016 | Authenticated Lecturer Access and Role Management | Provide ongoing role-restricted collaboration | FS-015 | Proposed — later release |
| 18 | FS-017 | Provider-Neutral Planning Data Import and Synchronization | Reduce manual catalog maintenance | FS-007, FS-008 | Proposed — later release |

**Recommended first slice:** `FS-013 – Versioned Review and Publication Lifecycle`

## Development slices

### FS-001: Single-Course Draft Schedule Generation

#### User or business outcome

A planner user can explicitly generate a complete draft teaching schedule for one course and receive understandable reasons when a valid complete schedule cannot be produced.

#### Rationale for this slice boundary

This slice proves the core scheduling value using one course, lecturer, room, cohort, semester, and study type before broader review or multi-course coordination is introduced.

#### Primary actors

- Planner user.

#### Preconditions

- Course, lecturer, room, cohort, semester, study type, and allowed time windows exist.

#### In scope

- Explicit generation for one course.
- Unit distribution using 45-minute units, 10-minute inter-unit breaks, and lecturer session-size preferences.
- Placement inside semester and Study Type Time Windows, once per week where possible.
- Room-capacity validation, complete-plan behavior, replacement of the course's prior draft, and understandable failures.

#### Out of scope

- Calendar review, manual editing, cross-course conflict handling, holidays, exams, multi-course generation, or multiple eligible resources.

#### Main workflow

The planner selects the planning inputs and triggers generation. The system validates the request, distributes all units, places sessions in permitted windows, and either saves the complete draft or reports why no complete valid draft can be created.

#### Business rules

- One unit is 45 minutes; 10-minute breaks contribute to session duration.
- Use the lecturer's maximum preferred session size by default while respecting the allowed range.
- No more than one session for the course occurs on the same day.
- A failed attempt must not leave a partial replacement.

#### Data inputs and outputs

Inputs include course units, lecturer preferences, room capacity, cohort size, semester dates, study type, and time windows. Output is a Draft Schedule with Draft Sessions or a complete set of detected generation errors.

#### Integrations

None.

#### UI references

The implemented single-course generation controls are the reference.

#### Constraints and assumptions

Planning records already exist. This slice reflects the implemented baseline in `specs/001-draft-course-schedule`.

#### Dependencies

None.

#### Completion outcome

A complete valid one-course draft can be generated and retrieved, while invalid or impossible requests leave no partial schedule.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise the specification for FS-001: Single-Course Draft Schedule Generation.

Product context: A university planner user needs a reliable first scheduling workflow.
Outcome: Generate a complete draft for one course or explain why it cannot be generated.
In scope: One course, lecturer, room, cohort, semester, and study type; 45-minute units; 10-minute breaks; preferred session-size distribution; semester and Study Type Time Windows; room capacity; complete-plan persistence; understandable failures.
Out of scope: Review UI, manual editing, conflicts, holidays, exams, multi-course generation, and multiple eligible resources.
Completion: A valid complete draft is saved and an impossible attempt creates no partial plan.

Keep the specification consistent with docs/planning/Feature_slices.md and the implemented baseline under specs/001-draft-course-schedule. Do not introduce implementation details or expand scope.
```

### FS-002: Review Generated Schedule in Planner UI

#### User or business outcome

A planner user can inspect generated Draft Sessions in chronological list and weekly calendar-style views and filter the visible schedule context.

#### Rationale for this slice boundary

Review is independently useful after generation and is separate from changing or validating the draft.

#### Primary actors

- Planner user.

#### Preconditions

- FS-001 has generated a Draft Schedule.

#### In scope

- Generated-session details with course, cohort, lecturer, room, and study-type context.
- List and weekly views, filters, empty states, and no-results feedback.

#### Out of scope

- Editing, conflict alerts, multi-course generation, holidays, exams, or dashboards.

#### Main workflow

The planner opens a generated schedule, switches review modes, and narrows visible sessions using available context filters.

#### Business rules

- Review controls do not change saved schedule data.
- Filters affect visibility only.

#### Data inputs and outputs

Input is the current generated Draft Schedule and display context. Output is a filtered visual representation; no planning data is mutated.

#### Integrations

None.

#### UI references

The implemented list and weekly review surfaces are the reference.

#### Constraints and assumptions

This slice reflects `specs/002-review-generated-schedule`; FS-003 later broadens the review context to the selected semester.

#### Dependencies

- FS-001.

#### Completion outcome

The planner can understand when and where generated sessions occur without editing them.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented, later refined by FS-003.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise FS-002: Review Generated Schedule in Planner UI.

Outcome: Let a planner inspect a generated one-course schedule in list and weekly views and filter by course, cohort, lecturer, room, and study type.
In scope: Read-only schedule context, view switching, filters, empty/no-result states.
Out of scope: Editing, validation alerts, multi-course generation, holidays, exams, and dashboards.
Dependency: FS-001.

Keep the specification consistent with docs/planning/Feature_slices.md and specs/002-review-generated-schedule. Do not introduce implementation details.
```

### FS-003: Configurable Generation Constraints and Courses Overview

#### User or business outcome

A planner can control when a selected course may be generated and review all generated course plans for the selected semester independently of the focused planning input.

#### Rationale for this slice boundary

Course-semester constraints and semester-wide review together make the generator practically controllable while keeping generation focused on one course.

#### Primary actors

- Planner user.

#### Preconditions

- FS-001 and FS-002.

#### In scope

- Default or custom planning period inside the semester.
- One or more weekly teaching windows.
- Saved course-semester constraints after successful generation and clearing back to defaults.
- Semester-wide Courses overview with filters derived from all generated plans.

#### Out of scope

- Manual editing, conflict detection, multi-course generation, holidays, exams, dashboards, or multiple eligible resources.

#### Main workflow

The planner selects a course and semester, loads defaults or saved constraints, optionally edits them, generates the course, and reviews all generated schedules in the selected semester.

#### Business rules

- Custom periods stay within the semester.
- Failed generation does not overwrite saved constraints.
- Generation controls remain separate from review filters.

#### Data inputs and outputs

Inputs are course-semester planning periods and weekly windows. Outputs are saved active constraints and a semester-scoped collection of Draft Schedules.

#### Integrations

None.

#### UI references

The implemented planning sidebar and central Courses overview are the reference.

#### Constraints and assumptions

This slice reflects `specs/003-configurable-generation-constraints`.

#### Dependencies

- FS-001 and FS-002.

#### Completion outcome

The planner controls course generation windows and can review every generated plan in the selected semester.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise FS-003: Configurable Generation Constraints and Courses Overview.

Outcome: Configure course-semester generation periods and weekly windows, persist successful custom constraints, restore defaults, and review all generated schedules in the selected semester.
In scope: Default/custom constraints, validation, save/clear behavior, semester Courses overview, overview filters independent from the focused course.
Out of scope: Editing, conflicts, multi-course generation, holidays, exams, dashboards, and multiple eligible resources.
Dependencies: FS-001 and FS-002.

Keep the specification consistent with docs/planning/Feature_slices.md and specs/003-configurable-generation-constraints. Do not introduce implementation details.
```

### FS-004: Manual Session Editing

#### User or business outcome

A planner can correct the date, time, length, or room of an existing Draft Session and retain that correction during later review.

#### Rationale for this slice boundary

Editing existing generated sessions provides focused correction value without introducing session creation, deletion, or conflict resolution.

#### Primary actors

- Planner user.

#### Preconditions

- FS-003 and an existing Draft Session.

#### In scope

- Edit an existing session's date, start time, end time, and room.
- Preserve valid edits across filters, view modes, and later visits.
- Reject invalid time order, out-of-semester or duplicate course-session dates, missing rooms, and insufficient room capacity.

#### Out of scope

- Creating or deleting sessions, source-record editing, conflict blocking, holidays, exams, or multi-course generation.

#### Main workflow

The planner opens a session, changes allowed fields, and saves or cancels. Valid changes persist; invalid changes leave the session unchanged and return understandable feedback.

#### Business rules

- Cancel leaves the session unchanged.
- Editing changes draft data, not saved generation constraints.
- Otherwise valid edits may create conditions that later appear as non-blocking alerts.

#### Data inputs and outputs

Inputs are revised date/time/room values. Output is the updated parent schedule and derived session length.

#### Integrations

None.

#### UI references

The implemented Draft Session editor is the reference.

#### Constraints and assumptions

This slice reflects `specs/004-manual-session-editing`.

#### Dependencies

- FS-003.

#### Completion outcome

Valid manual corrections remain visible and invalid or canceled edits do not alter saved data.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise FS-004: Manual Session Editing.

Outcome: Let a planner edit an existing Draft Session's date, start/end time, length, and room while preserving valid changes across review interactions.
In scope: Focused edit/cancel workflow and existing validation rules.
Out of scope: Session creation/deletion, source planning records, conflict blocking, holidays, exams, and multi-course generation.
Dependency: FS-003.

Keep the specification consistent with docs/planning/Feature_slices.md and specs/004-manual-session-editing. Do not introduce implementation details.
```

### FS-005: Conflict Detection

#### User or business outcome

A planner can identify unsafe or inconsistent Draft Sessions across the selected semester without being prevented from continuing planning work.

#### Rationale for this slice boundary

Detection and explanation are useful before automated avoidance and remain distinct from optimization or automatic correction.

#### Primary actors

- Planner user.

#### Preconditions

- FS-003 and FS-004.

#### In scope

- Lecturer, room, and cohort overlap alerts across semester schedules.
- Room-capacity, active generation-constraint, and Study Type Time Window alerts.
- Related-session context, multiple alerts per session, and refresh after generation or editing.

#### Out of scope

- Blocking saves, automatic correction, conflict-aware generation, holidays, exams, dashboards, or multiple eligible resources.

#### Main workflow

The planner reviews semester schedules and sees current alert indicators and explanations. Alerts update after saved schedule changes and remain attached during filtering and view switching.

#### Business rules

- Back-to-back sessions do not overlap.
- Alerts do not block generation or otherwise valid manual edits.
- Missing reference data produces an explicit validation-data issue.

#### Data inputs and outputs

Inputs are semester Draft Sessions and active planning reference data. Outputs are derived per-session validation alerts.

#### Integrations

None.

#### UI references

The implemented alert rendering in list and weekly views is the reference.

#### Constraints and assumptions

This slice reflects `specs/005-conflict-detection`.

#### Dependencies

- FS-003 and FS-004.

#### Completion outcome

Every supported validation issue is visible and understandable without changing save behavior.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise FS-005: Conflict Detection.

Outcome: Display non-blocking lecturer, room, cohort, capacity, and active-window alerts across all Draft Sessions in the selected semester.
In scope: Detection, related-session explanations, refresh after generation/editing, filtering/view persistence, missing-reference alerts.
Out of scope: Blocking, automatic resolution, conflict-aware generation, holidays, exams, dashboards, and multiple eligible resources.
Dependencies: FS-003 and FS-004.

Keep the specification consistent with docs/planning/Feature_slices.md and specs/005-conflict-detection. Do not introduce implementation details.
```

### FS-006: Multi-Course Draft Generation

#### User or business outcome

A planner can generate drafts for several explicitly selected courses in one semester, understand per-course outcomes, retry failures, and safely confirm replacements.

#### Rationale for this slice boundary

This slice scales the established independent course generator without introducing cross-course optimization.

#### Primary actors

- Planner user.

#### Preconditions

- FS-003 and FS-005.

#### In scope

- Initial operations for 2–50 distinct courses and failed-only retries for 1–50 courses.
- Per-course saved constraints or defaults, ordered outcomes, partial success, and understandable failures.
- Same-semester replacement discovery and confirmation, stale-data protection, atomic unexpected-failure behavior, and cross-semester retention.
- Refreshed semester overview and alerts; preserved single-course workflow.

#### Out of scope

- Conflict-aware placement, holidays, exams, multiple eligible resources, persistent batch history, dashboards, or background execution.

#### Main workflow

The planner selects a semester and courses, prepares the operation, confirms identified replacements, executes generation, reviews ordered outcomes, and may retry failed courses only.

#### Business rules

- Each course is generated independently.
- Expected course failures do not block valid courses and do not change failed-course data.
- Unexpected operation-wide failure rolls back the complete attempt.
- Current-session results need not persist after reload.

#### Data inputs and outputs

Inputs are selected course IDs, semester, immutable preparation snapshots, and replacement confirmation. Outputs are per-course results, summary counts, and saved successful schedules.

#### Integrations

None.

#### UI references

The implemented One course/Several courses modes, confirmation dialog, result summary, and retry workflow are the reference.

#### Constraints and assumptions

This slice reflects `specs/006-multi-course-draft-generation` and is recorded as implemented.

#### Dependencies

- FS-003 and FS-005.

#### Completion outcome

Several courses can be generated safely in one foreground operation while failed or stale courses retain their prior data.

#### Open clarification topics

None for the implemented boundary.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise FS-006: Multi-Course Draft Generation.

Outcome: Generate 2–50 selected course drafts for one semester, allow failed-only retry, preserve failed courses, confirm same-semester replacements, and refresh the semester overview.
In scope: Preparation/execution, per-course constraints, ordered outcomes, partial success, replacement and stale-data safeguards, cross-semester retention, operation rollback, transient results.
Out of scope: Conflict-aware placement, holidays, exams, multiple eligible resources, dashboards, persistent history, and background work.
Dependencies: FS-003 and FS-005.

Keep the specification consistent with docs/planning/Feature_slices.md and specs/006-multi-course-draft-generation. Do not introduce implementation details.
```

### FS-007: Academic Planning Data Administration

#### User or business outcome

A planner can create and maintain the academic records needed by the planner without relying on seeded data, developer intervention, or an external integration.

#### Rationale for this slice boundary

Manual academic-data ownership is the first prerequisite for the confirmed planner-only MVP. It is separated from resource availability because academic structure and scheduling-resource eligibility have different workflows and business rules.

#### Primary actors

- Planner user.

#### Preconditions

- The FS-001 through FS-006 planner baseline is available.

#### In scope

- Full create, view, edit, and delete workflows for semesters/planning periods, cohorts/classes, courses, study types, and Study Type Time Windows.
- Relationships required by the implemented generator, including course units, cohort, study type, and semester-relevant planning context.
- Clear validation and dependency feedback.
- Prevention of deletion when a record is referenced by a saved schedule or another record that must remain valid.
- Planning-option refresh so changes become available to existing generation and review workflows.

#### Out of scope

- Lecturer and room availability, multiple eligible resources, public holidays, exams, external import/synchronization, and provider-specific identifiers.

#### Main workflow

The planner opens academic administration, creates or updates the records required for a semester, sees validation and usage context, and deletes only records that are not protected by existing relationships or saved schedules. The updated records become selectable in the planner.

#### Business rules

- Referenced records must not be deleted silently or by cascade when that would invalidate saved planning data.
- Validation must explain what prevents deletion and what must be changed first.
- Editing source records must not silently rewrite historical or published schedule facts.
- Existing records and schedules must remain usable after the administration capability is introduced.

#### Data inputs and outputs

Inputs include semester dates, cohort identity and size, course identity and units, study-type definitions, and weekly time windows. Outputs are durable academic records and updated planning options.

#### Integrations

None. Manual product-owned administration is required for this release.

#### UI references

- Existing planning selectors provide terminology and display context.
- `docs/designs/resource-planner-calendar-screen-reference.png` shows possible navigation entries for classes, courses, and planning periods; it is inspiration only.

#### Constraints and assumptions

- The planner-only MVP has one planner-user role and does not require authentication.
- Detailed archive behavior, duplicate detection, and historical-label rules may be clarified without changing the slice boundary.

#### Dependencies

- FS-006.

#### Completion outcome

A planner can prepare and maintain the academic input catalog for scheduling entirely through the UI, while protected data cannot be destructively removed.

#### Open clarification topics

- Whether records that cannot be deleted should support an inactive/archive state.
- Exact uniqueness rules and editing effects for records already copied into draft versus published schedules.
- Whether course-semester eligibility requires an explicit record or is inferred from available course data.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for the following development slice.

Slice ID: FS-007
Slice name: Academic Planning Data Administration

Product context:
The implemented Resource Planner can generate and review schedules, but its academic input records are not yet fully maintainable by planner users. The planner-only MVP must work without developer-seeded data or an external source.

User or business outcome:
A planner user can maintain the academic records required for scheduling through the product UI.

Primary actors:
Planner user.

In scope:
Create, view, edit, and delete semesters/planning periods, cohorts/classes, courses, study types, and Study Type Time Windows; validate required relationships; prevent deletion when records are referenced by saved schedules or required dependent records; refresh existing planning options without breaking FS-001 through FS-006.

Out of scope:
Lecturer/room availability, multiple eligible resources, holidays, exams, authentication, lecturer access, and external import or synchronization.

Main workflow:
The planner maintains academic records, receives clear validation and protected-deletion feedback, and then uses those records in the existing generation and review workflows.

Business rules:
Referenced records must not be destructively deleted; editing source records must not silently rewrite saved historical schedule facts; existing data remains usable.

Data inputs and outputs:
Semester dates, cohort identity/size, course identity/units, study-type definitions, and weekly windows become durable selectable planning records.

External systems and integrations:
None; manual administration is authoritative for this release.

UI references:
Existing planner selectors and docs/designs/resource-planner-calendar-screen-reference.png as gradual visual inspiration.

Dependencies and assumptions:
FS-001 through FS-006 are implemented. One planner-user role is sufficient.

Completion outcome:
The academic scheduling catalog can be managed safely through the UI without developer intervention.

Known clarification topics:
Archive/inactive behavior, uniqueness rules, historical-label behavior, and explicit versus inferred course-semester eligibility.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define user scenarios, functional requirements, edge cases, assumptions, and measurable success criteria. Do not introduce implementation details or expand product scope.
```

### FS-008: Resource Eligibility and Availability

#### User or business outcome

A planner can maintain lecturers, rooms, their unavailable periods, and the eligible resources for each course so later generation can make realistic resource choices.

#### Rationale for this slice boundary

Resource choice and availability form one planner-facing outcome and one coherent input boundary for conflict-aware scheduling. They are separated from the optimizer so the data and preferences are independently usable and testable.

#### Primary actors

- Planner user.

#### Preconditions

- FS-007 academic records exist.

#### In scope

- Full create, view, edit, and protected-delete workflows for lecturers and rooms.
- Room capacity and lecturer/room availability periods.
- Multiple eligible lecturers and multiple eligible rooms per course.
- One lecturer and one room assignment per Draft Session.
- Preference data for contiguous lecturer blocks and reuse of the same room.
- Availability and eligibility visibility when configuring a course.

#### Out of scope

- Global optimization, holiday calendars, exams, lecturer authentication, direct lecturer maintenance of availability, and external synchronization.

#### Main workflow

The planner maintains lecturer and room records, records unavailable periods, assigns eligible resources to courses, and defines or confirms scheduling preferences. Existing schedules remain reviewable even if source eligibility changes.

#### Business rules

- Referenced lecturers or rooms cannot be destructively deleted.
- Room capacity remains a hard validity rule.
- Each Draft Session uses exactly one lecturer and one room.
- When several lecturers teach a course, contiguous lecturer blocks are preferred over repeated alternation.
- Reusing one eligible room is preferred but not required when another eligible room enables more scheduling.

#### Data inputs and outputs

Inputs include resource identity, room capacity, unavailable intervals, course eligibility, and preference configuration. Outputs are durable resource and availability records available to generation and validation.

#### Integrations

None in the planner-only MVP.

#### UI references

The Professors and Rooms navigation concepts in the saved calendar reference are inspiration. Existing planning selectors establish current terminology.

#### Constraints and assumptions

- Availability may contain recurring or dated periods; the exact supported forms may be clarified in the specification.
- Source-record changes must not silently mutate published schedule revisions.

#### Dependencies

- FS-007.

#### Completion outcome

The planner can express who and what may be scheduled for a course and when those resources are unavailable.

#### Open clarification topics

- Recurring versus date-specific availability and exception precedence.
- Whether lecturer blocks have explicit unit targets or are optimized from eligibility alone.
- Whether room preference can be ranked beyond “same room where possible.”

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise the specification for FS-008: Resource Eligibility and Availability.

Product context: Planner users must manually maintain scheduling resources before conflict-aware optimization can choose among them.
Outcome: Maintain lecturers, rooms, capacity, availability, and multiple eligible lecturers/rooms per course.
Actors: Planner user.
In scope: Lecturer/room CRUD with protected deletion; room capacity; recurring or dated availability; course eligibility; exactly one lecturer and room per session; contiguous lecturer-block and same-room preferences.
Out of scope: Global optimization, holidays, exams, lecturer access, authentication, and external synchronization.
Workflow: Maintain resources and availability, associate eligible resources with courses, and make the result available to generation and validation.
Rules: Referenced resources cannot be destructively deleted; capacity is hard; contiguous lecturer blocks and room reuse are preferences.
Dependencies: FS-007.
Completion: Courses have planner-maintained eligible resources and availability suitable for later optimization.
Clarification topics: Availability recurrence/precedence, lecturer block allocation, and any room-preference ranking.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without implementation details.
```

### FS-009: Manual Session Creation, Deletion, and Remaining Units

#### User or business outcome

A planner can add an individual Draft Session, delete one session, or clear one course's complete draft, while immediately seeing how many course units remain unscheduled.

#### Rationale for this slice boundary

These controls complete the manual planning loop and provide the explicit escape hatch needed when existing sessions prevent a better generated plan. They remain separate from automated optimization.

#### Primary actors

- Planner user.

#### Preconditions

- FS-006 and an available course-semester planning context.

#### In scope

- Add one Draft Session manually to a course-semester draft.
- Delete one generated or manually created Draft Session.
- Delete the complete Draft Schedule and all generated or manually edited/created sessions for one course in one semester.
- Preserve the course-semester's saved generation constraints after deletion.
- Recalculate remaining units immediately after additions or deletions.
- Show all course units as remaining when the complete draft is deleted.
- Confirmation and understandable consequences for destructive actions.

#### Out of scope

- Bulk semester deletion, automatic generation, splitting/merging sessions, source-course deletion, and automatic conflict repair.

#### Main workflow

The planner selects one course schedule and either adds a validly formed session, deletes one session, or explicitly clears the course schedule. The planner sees changed remaining units and refreshed validation alerts.

#### Business rules

- A manually added session may be saved with non-blocking lecturer, room, cohort, or window alerts, consistent with existing editing.
- Existing hard structural validation such as semester bounds, valid time order, existing references, and room capacity remains applicable.
- Deleting schedule data never deletes saved generation constraints or source planning records.
- Only one course or one session is affected by each explicit deletion action.

#### Data inputs and outputs

Inputs are course, date, time, units or duration, lecturer, room, and deletion targets. Outputs are the revised Draft Schedule, remaining-unit count, and refreshed alerts.

#### Integrations

None.

#### UI references

The session detail panel, delete action, remaining-hours indicators, and calendar interactions in the saved design reference are inspiration; drag/drop is not required by this slice.

#### Constraints and assumptions

- “Slot” is normalized to the existing domain term “Draft Session.”
- Detailed confirmation copy and whether an empty Draft Schedule record remains may be clarified later.

#### Dependencies

- FS-006.

#### Completion outcome

The planner can manually complete, reduce, or clear one course draft without losing its saved generation constraints and always sees the resulting remaining units.

#### Open clarification topics

- Whether manual creation uses explicit units, duration, or both when they disagree.
- Whether an empty schedule remains as a partial draft or is represented only by the course's remaining-unit state.
- Exact confirmation thresholds for one-session deletion versus complete-course deletion.

#### Specification status

Proposed.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-009: Manual Session Creation, Deletion, and Remaining Units.

Outcome: Let a planner add one Draft Session, delete one session, or delete one course-semester draft and immediately understand remaining units.
Actors: Planner user.
In scope: Manual session creation; deletion of one generated/manual session; explicit deletion of all sessions for one course in one semester; preserved generation constraints; immediate remaining-unit and alert refresh; understandable confirmation.
Out of scope: Bulk semester deletion, generation/optimization, splitting/merging, source-record deletion, and automatic conflict repair.
Rules: Manual sessions may retain non-blocking alerts; structural validity and capacity remain hard; deleting sessions never deletes source data or saved constraints; complete deletion makes all course units remaining.
Dependencies: FS-006.
UI reference: Existing editor plus the gradual interaction concepts in docs/designs/resource-planner-calendar-screen-reference.png; drag/drop is not required.
Completion: One course draft can be manually completed, reduced, or cleared with accurate remaining-unit feedback.
Clarification topics: Units versus duration input, representation of an empty draft, and confirmation details.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without implementation details.
```

### FS-010: Conflict-Aware Semester Optimization

#### User or business outcome

A planner can generate the greatest achievable number of teaching units across selected courses without creating known lecturer, room, or cohort overlaps, while retaining and explaining a valid partial result when completion is impossible.

#### Rationale for this slice boundary

This is the primary next scheduling outcome and replaces request-order-only independent generation with global semester reasoning. Holiday and exam constraints remain separate additions to the same availability boundary.

#### Primary actors

- Planner user.

#### Preconditions

- FS-008 provides eligible resources and availability.
- FS-009 provides remaining-unit and recovery behavior.
- Existing semester schedules and manual edits are available as occupied planning facts.

#### In scope

- Optimize across the complete selected course set rather than processing each course independently.
- Consider every existing semester Draft Session, including manually edited or created sessions and schedules outside the selection.
- Avoid lecturer, room, and cohort overlaps and resource unavailability during generation.
- Choose among eligible lecturers and rooms while applying contiguous-lecturer and same-room preferences.
- Maximize the total number of scheduled units across the selected courses.
- Save valid partial plans when complete plans are impossible.
- Report remaining units and understandable blocking reasons by course.
- Preserve an existing schedule when a candidate would schedule fewer units.
- Allow equal-unit replacement only when it reduces conflicts or improves preference compliance; otherwise keep the current schedule.
- Retain explicit same-semester replacement confirmation and stale-data safeguards.
- Expose a future unavailable-date input so holidays can be added without redesigning the optimizer.

#### Out of scope

- Public-holiday data, exam generation, unapproved automatic deletion of existing sessions, and guaranteed mathematical optimality beyond the measurable objective chosen in the specification.

#### Main workflow

The planner selects courses and a semester, reviews replacement implications, and starts conflict-aware generation. The system evaluates selected courses together against existing schedules and availability, saves complete or partial improvements, preserves non-improvements, and reports scheduled and remaining units with reasons.

#### Business rules

- No generated candidate may introduce a known lecturer, room, or cohort overlap.
- Capacity, semester, and active-window rules remain applicable.
- Existing unselected and manual sessions are constraints, not automatically movable items.
- The primary objective is greatest total scheduled units across the selection.
- Preference improvement never justifies scheduling fewer units.
- Course results must distinguish complete, improved partial, unchanged, and failed/stale outcomes.

#### Data inputs and outputs

Inputs include selected courses, current semester sessions, constraints, availability, eligible resources, revisions, and replacement confirmation. Outputs include saved complete or partial schedules, resource assignments, remaining units, reasons, and an operation summary.

#### Integrations

None.

#### UI references

Existing multi-course preparation/results and the remaining-hours concepts in the saved design reference.

#### Constraints and assumptions

- Public holidays are deliberately later, but unavailable dates must fit the scheduling boundary.
- The exact optimization/tie-breaking strategy is an implementation concern only after requirements define deterministic observable priorities and performance expectations.

#### Dependencies

- FS-008 and FS-009.

#### Completion outcome

The planner receives a conflict-aware semester result that maximizes scheduled units, retains valid partial work, explains gaps, and never silently worsens an existing course schedule.

#### Open clarification topics

- Fairness or minimum-allocation guardrails when maximizing total units could starve one course.
- Deterministic tie-break order after units, conflicts, teaching preferences, lecturer continuity, and room continuity.
- Whether a partial plan with zero newly placed units is stored or represented as unchanged/failed.
- Performance target and largest supported globally optimized selection.

#### Specification status

Proposed.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-010: Conflict-Aware Semester Optimization.

Product context: FS-006 generates selected courses independently. The next scheduling outcome must reason globally across a semester and save useful partial work.
Outcome: Maximize scheduled teaching units across selected courses without generating lecturer, room, or cohort overlaps.
Actors: Planner user.
In scope: Global selected-course optimization; existing selected/unselected/manual sessions as fixed occupancy; lecturer/room availability; multiple eligible resources; contiguous lecturer and same-room preferences; complete and partial saved plans; remaining units and reasons; non-worsening replacement; equal-unit replacement only for a better arrangement; confirmation/stale protection; future unavailable-date input.
Out of scope: Holiday data, exams, automatic deletion/movement of existing sessions, and unexplained schedule worsening.
Rules: Maximize total scheduled units; generated candidates are conflict-free; fewer-unit candidates never replace existing schedules; unchanged outcomes preserve data.
Dependencies: FS-008 and FS-009.
Completion: The planner gets a measurable conflict-aware result, understandable gaps, and no silent regression of existing plans.
Clarification topics: Fairness guardrails, deterministic tie-breaking, zero-placement representation, and performance/selection limits.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without choosing an algorithm or other implementation details.
```

### FS-011: Institution-Wide Holiday Calendar and Avoidance

#### User or business outcome

A planner can maintain one institution-wide public-holiday calendar and prevent generated teaching sessions from being placed on those dates.

#### Rationale for this slice boundary

Holiday administration and avoidance are a coherent real-world scheduling outcome that extends the optimizer's unavailable-date boundary without mixing in exam behavior or external calendar integration.

#### Primary actors

- Planner user.

#### Preconditions

- FS-007 provides manual administration patterns.
- FS-010 accepts unavailable dates as scheduling constraints.

#### In scope

- Create, view, edit, and confirmed-delete institution-wide holiday dates with readable names; edits and deletion retain no prior holiday history.
- Make holidays unavailable to single-course, multi-course, conflict-aware, and later exam generation.
- Show holiday alerts where an existing or manually added session falls on a holiday; standalone review-calendar display remains for FS-014.
- Recalculate relevant alerts after holiday changes without silently moving saved sessions.

#### Out of scope

- Multiple campus or regional calendars, automatic holiday-provider import, religious/personal leave calendars, timed or half-day closures, or automatic movement of existing sessions.

#### Main workflow

The planner maintains holiday dates. Future generation excludes them. Existing affected sessions remain saved and become visibly flagged for planner action.

#### Business rules

- One calendar applies institution-wide.
- A holiday is a hard unavailable date for automatic generation.
- Adding or editing a holiday never silently deletes or relocates existing sessions.
- Editing a holiday replaces its current date/name and confirmed deletion removes it without retaining holiday history; saved sessions remain unchanged.

#### Data inputs and outputs

Inputs are holiday date and name. Outputs are durable unavailable dates and current validation context.

#### Integrations

None. Provider-based holiday import is later scope under FS-017.

#### UI references

The primary calendar workspace should visibly distinguish holidays when FS-014 is delivered; an administration view is required in this slice.

#### Constraints and assumptions

- Institution-wide dates are sufficient for the planner-only MVP.

#### Dependencies

- FS-007 and FS-010.

#### Completion outcome

New generated teaching sessions do not land on maintained public holidays, and existing holiday collisions are visible rather than silently changed.

#### Resolved clarification decisions

- Half-day and timed closures remain later scope.
- Changed or removed holiday values are not retained as history.
- Existing review surfaces show alerts only on affected sessions; standalone holiday display remains for FS-014.
- When holiday exclusion contributes to incomplete or failed generation, the result identifies each substantiated relevant holiday by name and date.

#### Specification status

Proposed.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-011: Institution-Wide Holiday Calendar and Avoidance.

Outcome: Let a planner maintain one institution-wide holiday calendar and prevent automatic scheduling on holiday dates.
In scope: Current-state holiday date/name CRUD without retained history; unavailable-date use by existing generation modes and FS-010; holiday alerts for existing or manual sessions; alert refresh after changes; named holiday explanations for incomplete or failed generation.
Out of scope: Campus/region-specific calendars, external holiday providers, timed closures, and automatic movement/deletion of saved sessions.
Rules: Holidays are hard constraints for new generation; existing sessions are flagged, not silently changed.
Dependencies: FS-007 and FS-010.
Completion: Maintained holidays are excluded from generation and visible in review.
Resolved clarifications: Timed closures are deferred; changed/deleted holiday values are not retained; existing review shows affected-session alerts only; substantiated holiday-related generation gaps identify holiday name and date.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without implementation details.
```

### FS-012: Conflict-Aware Exam Scheduling

#### User or business outcome

A planner can configure and generate exams for courses that explicitly require them, with suitable resources and without conflicts with teaching sessions or other exams.

#### Rationale for this slice boundary

Exams are a separate academic scheduling outcome with their own requirements and timing, but they reuse the established availability and conflict-aware planning boundaries.

#### Primary actors

- Planner user.

#### Preconditions

- FS-008 resource eligibility and availability.
- FS-010 conflict-aware scheduling.
- FS-011 holiday avoidance.

#### In scope

- Mark a course as requiring an exam.
- Configure duration, permitted date range, required room capacity, exam type, responsible lecturer, and a course-configurable default delay after the last teaching session.
- Generate exams only for explicitly enabled courses.
- Avoid conflicts with teaching sessions and exams sharing lecturer, room, or cohort.
- Respect resource availability, room capacity, and institution-wide holidays.
- Review and manually correct exam sessions within the same planner context while keeping them distinguishable from teaching sessions.
- Report understandable failures when an exam cannot be placed.

#### Out of scope

- Student-level exam registration, invigilator rosters beyond the responsible lecturer, exam grading, automated publication to an external examination system, or lecturer editing.

#### Main workflow

The planner enables and configures an exam requirement for a course, starts exam generation, reviews the proposed exam with its conflict context, and adjusts it using planner-authorized schedule controls where necessary.

#### Business rules

- Courses without an explicit exam requirement receive no generated exam.
- The default timing rule is configurable per course; the initial default may be at least one week after the final teaching session.
- The permitted date range is authoritative and must be reconciled with the configured delay.
- Exams must not overlap teaching or exam sessions for the same lecturer, room, or cohort.
- Capacity, resource availability, and holidays are hard generation constraints.

#### Data inputs and outputs

Inputs include course exam-enabled state, duration, date range, delay, capacity, type, lecturer, cohort, and eligible rooms. Output is a distinguishable exam session or an understandable failure.

#### Integrations

None.

#### UI references

The “Exam Session” concept and session editor in the saved design reference are inspiration, not an exact field mandate.

#### Constraints and assumptions

- One exam requirement per course is sufficient unless specification clarification identifies a required multi-exam case.
- The same planner user controls teaching and exam planning.

#### Dependencies

- FS-008, FS-010, and FS-011.

#### Completion outcome

Every explicitly exam-enabled course can receive a valid generated exam or a clear explanation of why no valid exam placement exists.

#### Open clarification topics

- Whether a course may require more than one exam or exam component.
- Precedence when the configured delay conflicts with the permitted date range.
- Whether manual exam creation/deletion exactly reuses FS-009 or needs exam-specific safeguards.

#### Specification status

Proposed.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-012: Conflict-Aware Exam Scheduling.

Outcome: Generate and manage exams only for explicitly enabled courses, without teaching/exam resource conflicts.
Actors: Planner user.
In scope: Exam-required flag; duration; permitted date range; required room capacity; exam type; responsible lecturer; configurable per-course delay after the last teaching session; conflict-aware placement; resource availability; holidays; review and planner correction; understandable failures.
Out of scope: Student registrations, grading, external exam systems, broad invigilator management, and lecturer editing.
Rules: No exam without explicit configuration; date range and delay must be valid; lecturer/room/cohort teaching and exam conflicts are prohibited; capacity, availability, and holidays are hard constraints.
Dependencies: FS-008, FS-010, and FS-011.
Completion: Enabled courses receive a valid exam or a clear failure reason.
Clarification topics: Multiple exams per course, delay/date-range precedence, and exam-specific manual safeguards.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without implementation details.
```

### FS-013: Versioned Review and Publication Lifecycle

#### User or business outcome

A planner can distinguish working drafts from review-ready and published schedules, publish deliberately, and revise a published plan without removing the currently published version prematurely.

#### Rationale for this slice boundary

Publication state and revision continuity form a single planner-control outcome. Lecturer feedback uses this lifecycle later but is not required to deliver planner-controlled versioning.

#### Primary actors

- Planner user.

#### Preconditions

- FS-012 completes the planner's teaching and exam schedule content.

#### In scope

- Schedule lifecycle states `Draft`, `Ready for review`, and `Published`.
- Planner-controlled state transitions, including direct publication when desired.
- An immutable published revision that remains visible while the planner creates and edits a new draft revision.
- Replacement of the current published version only when the new revision is explicitly published.
- Visibility of current state, revision identity, publication time, and current-versus-working revision.
- Preservation of comments/feedback associations with the revision they concern when later collaboration is added.

#### Out of scope

- Mandatory approvals, lecturer authentication or feedback, automatic publishing, external publication systems, and an organizational approval chain.

#### Main workflow

The planner works on a draft, optionally marks it ready for review, and publishes it when appropriate. If changes are needed later, the planner creates or opens a new draft revision while users continue to see the current published revision, then explicitly publishes the replacement.

#### Business rules

- Only the planner controls transitions in the planner-only MVP.
- `Ready for review` is informative and does not restrict the planner.
- Published revisions are immutable snapshots; they are never edited in place.
- The planner may publish despite missing or negative later lecturer feedback.
- Creating or abandoning a draft revision does not remove the current published version.

#### Data inputs and outputs

Inputs are schedule revisions and explicit transition actions. Outputs are durable lifecycle state, revision history, one current published revision where present, and at most one controlled working revision per semester.

#### Integrations

None.

#### UI references

Lifecycle badges and filters should be introduced gradually into the current review UI and later calendar workspace.

#### Constraints and assumptions

- The planner-only MVP does not require authentication.
- Audit depth beyond revision/state history may be clarified later.

#### Dependencies

- FS-006 and FS-012.

#### Completion outcome

The planner can publish a stable schedule, revise it safely, and replace it only through an explicit later publication.

#### Clarification decisions

- Publication and revision identity are semester-wide; course views project the selected semester revision.
- A semester has at most one active working revision.
- Complete revision/state event history is retained, while historical schedule bodies load on demand.
- Abandonment captures the working content; restoration reuses the same revision only when no other working revision exists.

#### Specification status

Implemented — the exact reference-scale/query-bound proof, broader file-backed concurrency matrix, literal 200% manual pass, and moderated planner study remain validation follow-ups.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-013: Versioned Review and Publication Lifecycle.

Outcome: Give planner users controlled Draft → Ready for review → Published schedule states and safe post-publication revision.
In scope: Planner-controlled transitions; optional ready-for-review state; direct publication; immutable published snapshots; new working revision while the current published version remains visible; explicit replacement publication; revision/state visibility and history.
Out of scope: Mandatory approvals, lecturer access, authentication, automatic publication, external publication systems, and editing published data in place.
Rules: Planner retains full control; ready-for-review is informative; abandoned drafts do not remove the published version; later feedback never blocks publication.
Dependencies: FS-006 and FS-012.
Completion: A published schedule stays stable until an explicitly published new revision replaces it.
Clarification topics: Course versus semester publication scope, concurrent draft rules, history depth, and abandon/restore behavior.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, and measurable success criteria without implementation details.
```

### FS-014: Calendar Planning Workspace and Operational Dashboard

#### User or business outcome

A planner can operate the selected semester from one filterable calendar-centered workspace that makes scheduled sessions, remaining work, conflicts, failures, and lifecycle state immediately actionable.

#### Rationale for this slice boundary

The workspace consolidates information produced by earlier slices after its underlying data is available. Individual visual concepts may appear earlier, but this slice delivers the coherent operational outcome.

#### Primary actors

- Planner user.

#### Preconditions

- FS-009 through FS-013 provide remaining units, conflict-aware outcomes, holidays, exams, and lifecycle states.

#### In scope

- Primary semester calendar with practical day/week/month navigation as validated by the later specification.
- Filters for relevant course, cohort/class, lecturer, room, study type, session type, lifecycle state, and validation status.
- Visible teaching and exam sessions with warnings and concise capacity/resource context.
- Operational summaries for unscheduled units/hours, course conflicts, room-capacity issues, generation failures, and schedules needing review.
- Selection of a session to inspect and use existing planner-authorized editing, creation, or deletion workflows.
- Course-level remaining-unit context and alert-driven filtering.
- Responsive empty, loading, partial-data, and failure states.
- Gradual migration from the existing Courses overview without removing required current behavior.

#### Out of scope

- Pixel-perfect reproduction of the reference image, lecturer access, new scheduling algorithms, external data synchronization, and drag/drop or resize unless explicitly justified during specification.

#### Main workflow

The planner selects a semester, sees its operational state in the calendar, filters or follows an alert/remaining-unit indicator to affected courses and sessions, inspects details, invokes existing correction actions, and immediately sees refreshed results.

#### Business rules

- Dashboard counts and calendar items must derive from the same current schedule revision context.
- Filters must not hide or mutate underlying schedules.
- Alerts and remaining-unit totals must remain traceable to affected courses or sessions.
- Published and working revisions must be visually distinguishable.

#### Data inputs and outputs

Inputs are semester schedules, teaching/exam sessions, resource context, alerts, remaining units, failures, holidays, and lifecycle states. Output is an interactive operational view; corrections are delegated to established workflows.

#### Integrations

None.

#### UI references

- `docs/designs/resource-planner-calendar-screen-reference.png` is the primary visual inspiration.
- `docs/designs/resource-planner-unified-navigation-ground-truth.png` defines the shared application navigation delivered by FS-018 and reused by this workspace.
- Existing Courses overview, list/week views, filters, result summaries, alerts, and editor remain behavioral references.

#### Constraints and assumptions

- The reference's elements are introduced gradually and adapted to the product's real terminology and workflows.
- The workspace must reuse FS-018 navigation rather than introduce another global navigation model.
- Accessibility, responsive behavior, and workable performance for the supported semester scale must be measurable in the specification.

#### Dependencies

- FS-009 through FS-013 and FS-018.

#### Completion outcome

The planner can understand and act on the complete semester planning state from one coherent calendar workspace.

#### Open clarification topics

- Required calendar modes and whether drag/drop/resize is included now or later.
- Exact dashboard aggregation definitions and the meaning of “needs review.”

#### Specification status

Proposed.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-014: Calendar Planning Workspace and Operational Dashboard.

Outcome: Give planner users one calendar-centered semester workspace for schedules, remaining units, alerts, failures, and lifecycle state.
In scope: Calendar navigation; filters by planning/resource/session/state context; teaching and exam cards; alerts; unscheduled units/hours; conflicts; capacity issues; failures; schedules needing review; traceable summary-to-item navigation; session detail and existing correction actions; current/published revision distinction; responsive and failure states.
Out of scope: A pixel-perfect clone, lecturer access, new optimization, external synchronization, and unconfirmed drag/drop/resize behavior.
Rules: Calendar and summaries use the same revision context; filters do not mutate data; every metric is traceable to affected records.
Dependencies: FS-009 through FS-013 and FS-018.
UI reference: docs/designs/resource-planner-calendar-screen-reference.png for the calendar workspace, docs/designs/resource-planner-unified-navigation-ground-truth.png for shared application navigation, plus the existing Courses overview behavior. Introduce the reference elements gradually.
Completion: A planner can understand and act on the complete semester state from one workspace.
Clarification topics: Calendar modes, drag/drop scope, aggregation definitions, and “needs review.”

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, requirements, edge cases, assumptions, accessibility expectations, and measurable success criteria without implementation details.
```

### FS-015: Accountless Lecturer Token Review

#### User or business outcome

A planner can generate a temporary course-schedule review link for the corresponding lecturer, and the lecturer can provide scoped feedback without an account.

#### Rationale for this slice boundary

Accountless review delivers the common one-course/one-lecturer collaboration outcome before the product introduces full authentication and role management.

#### Primary actors

- Planner user.
- Lecturer reviewing one course schedule.

#### Preconditions

- FS-013 provides a reviewable schedule revision.

#### In scope

- Planner-generated review token for one course schedule revision and its one corresponding lecturer.
- A link containing the token that the planner copies and sends manually.
- Token reuse for three days, planner-controlled revocation, and replacement issuance.
- Read-only schedule review for the scoped course.
- Lecturer comments and “this session is not possible” flags, optionally including suggested alternatives in comment text.
- Feedback visibly associated with the relevant schedule revision and session.
- Planner ability to publish regardless of missing or negative feedback.

#### Out of scope

- Multi-lecturer course review, automated email delivery, lecturer accounts, lecturer schedule editing, mandatory acceptance, and feedback as a publication gate.

#### Main workflow

The planner prepares a course schedule for review, generates and copies a three-day link, and sends it manually. The lecturer opens it, reviews assigned course sessions, and may comment or flag impossible sessions. The planner reviews feedback and decides whether to revise or publish.

#### Business rules

- The token grants only the minimum review scope for one course schedule and lecturer.
- It is reusable until expiry, revocation, or replacement.
- Expired or revoked tokens expose no schedule data and provide safe feedback.
- The lecturer cannot alter schedule records.
- Silence or objections do not prevent planner publication.
- The review deadline is informational; token expiry is an access-security rule rather than an approval requirement.

#### Data inputs and outputs

Inputs are reviewable revision, course, lecturer identity, token lifecycle actions, comments, and impossible-session flags. Outputs are a scoped review link and revision-associated feedback.

#### Integrations

No email integration. The planner uses an external communication channel manually.

#### UI references

The lecturer view should reuse readable calendar/list concepts but expose only scoped review and feedback controls.

#### Constraints and assumptions

- The dominant use case is one course schedule with one lecturer.
- Security and privacy requirements for token generation, storage, expiry, logging, and URL exposure must be explicit in the specification.

#### Dependencies

- FS-013.

#### Completion outcome

A lecturer can securely review and comment on one course schedule for up to three days without an account, while the planner retains complete authority.

#### Open clarification topics

- Whether replacement immediately revokes every earlier token.
- Whether the planner may configure an expiry shorter than three days.
- Rate limits, feedback identity display, and comment retention after revision replacement.

#### Specification status

Proposed — later release.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-015: Accountless Lecturer Token Review.

Outcome: Let a planner share one course schedule with its corresponding lecturer through a secure temporary link and receive comments/flags without an account.
Actors: Planner user and one lecturer.
In scope: Token scoped to one course schedule revision and lecturer; planner copy action; manual sending; reusable three-day access; revoke and replace; read-only review; comments; impossible-session flags; revision/session association; planner publication regardless of feedback.
Out of scope: Multi-lecturer token review, automated email, accounts, schedule editing, mandatory acceptance, and publication blocking.
Rules: Expired/revoked tokens expose no data; the token has minimum scope; feedback is advisory; deadline information is not an approval gate.
Dependency: FS-013.
Completion: A lecturer can securely review and comment for three days while the planner retains control.
Clarification topics: Replacement revocation, configurable shorter expiry, rate limits, identity display, and retention.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Include explicit security, privacy, expiry, misuse, and measurable acceptance requirements without prescribing implementation.
```

### FS-016: Authenticated Lecturer Access and Role Management

#### User or business outcome

Planner users and lecturers can use ongoing authenticated access with permissions appropriate to their responsibilities.

#### Rationale for this slice boundary

Persistent identity and authorization are a distinct later-release outcome. They are intentionally deferred so the planner-only MVP and simpler accountless review can be validated first.

#### Primary actors

- Planner user.
- Lecturer.
- Planner user acting as account administrator in the first version.

#### Preconditions

- FS-015 has established lecturer review behavior and feedback semantics.

#### In scope

- Authenticated planner and lecturer accounts.
- Manual account creation, maintenance, deactivation, and role assignment by authorized planner users.
- Planner access to the complete institution planning scope.
- Lecturer access only to courses, schedule revisions, and sessions assigned to that lecturer.
- Authenticated reuse of lecturer comment and impossible-session feedback behavior.
- Safe handling of removed assignments and deactivated accounts.

#### Out of scope

- Institutional SSO, automated identity provisioning, broad organizational roles, lecturer schedule editing, and changing planner publication authority.

#### Main workflow

An authorized planner manages accounts. Users authenticate and receive role-appropriate navigation and data. Lecturers review only assigned schedules and submit advisory feedback; planners retain full planning and publication control.

#### Business rules

- Authorization is enforced on every protected action and data read, not only through hidden UI controls.
- Lecturers never gain schedule mutation or publication rights.
- Deactivation prevents new access without destroying historical feedback attribution.
- Assignment changes must not expose unrelated schedule data.

#### Data inputs and outputs

Inputs include account identity, role, status, lecturer association, and course/session assignments. Outputs are authenticated sessions, authorized views/actions, and attributable feedback.

#### Integrations

No external identity provider. Institutional SSO is possible later scope.

#### UI references

Planner administration and a restricted lecturer review area; detailed identity UI has no confirmed mockup.

#### Constraints and assumptions

- Account-security, session-management, password/recovery, audit, and privacy requirements require focused clarification before this slice is ready.

#### Dependencies

- FS-015.

#### Completion outcome

Authenticated users can safely perform only their role-authorized workflows, and lecturers see only their assigned planning context.

#### Open clarification topics

- Credential creation, password reset, multifactor requirements, session lifetime, and account-recovery process.
- Whether planner administration requires a distinct administrator permission.
- Migration or coexistence rules for token review after accounts exist.

#### Specification status

Proposed — later release.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-016: Authenticated Lecturer Access and Role Management.

Outcome: Provide authenticated planner and lecturer access with least-privilege permissions.
In scope: Manually managed accounts; role/status maintenance; planner-wide access; lecturer access only to assigned courses/sessions/revisions; authenticated advisory feedback; deactivation and historical attribution.
Out of scope: SSO, automated provisioning, lecturer schedule editing, lecturer publication rights, and broad organization-role design.
Rules: Authorization applies to every protected read/action; deactivation preserves history; assignment changes must not leak data; planners retain full workflow control.
Dependency: FS-015.
Completion: Planner and lecturer users can perform only permitted workflows and lecturers see only assigned context.
Clarification topics: Credentials, password reset, MFA, session lifetime, recovery, administrator permission, and token/account coexistence.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Include explicit authentication, authorization, privacy, misuse, audit, and measurable security requirements without choosing implementation details prematurely.
```

### FS-017: Provider-Neutral Planning Data Import and Synchronization

#### User or business outcome

A planner can reduce repetitive manual data maintenance by importing or synchronizing planning records from a future external source without surrendering safe planner control.

#### Rationale for this slice boundary

Integration follows the complete manual workflows so the product has a stable domain boundary. Provider-neutral behavior is separated from any future provider-specific adapter.

#### Primary actors

- Planner user.
- External planning-data provider.

#### Preconditions

- FS-007 and FS-008 define manually maintainable records and relationships.
- An external provider, access method, data ownership model, and synchronization direction have been selected before the slice becomes ready.

#### In scope

- Provider-neutral import or synchronization of the planning records confirmed for the selected provider.
- Preview, validation, matching, create/update/skip outcomes, and understandable per-record errors.
- Protection of saved and published schedules from destructive source changes.
- Repeatable imports and traceable source identifiers where available.
- Clear ownership and manual-override behavior based on later clarification.

#### Out of scope

- A specific provider adapter before selection, silent destructive synchronization, automatic publication, arbitrary external-system workflow execution, and identity/SSO integration.

#### Main workflow

The planner starts or reviews an import/synchronization run, previews proposed changes and conflicts, confirms allowed changes, and receives a durable summary. Invalid or unsafe records are skipped with actionable reasons while existing schedules remain protected.

#### Business rules

- Imported data must pass the same domain validation as manually entered data.
- Repeating the same source data must not create uncontrolled duplicates.
- External deletion or absence must not silently delete records referenced by saved or published schedules.
- Ownership, conflict resolution, and manual overrides must be explicit before implementation.

#### Data inputs and outputs

Potential inputs include lecturers, rooms, availability, cohorts/classes, courses, semesters/planning periods, study types/time windows, holidays, and exam requirements. Outputs are validated changes, stable matching information, and an import/synchronization summary.

#### Integrations

Unknown provider. The later specification must document data direction, authentication, rate/access limits, source ownership, and whether import, scheduled synchronization, or both are required.

#### UI references

No confirmed integration mockup. The planner needs preview, conflict, progress, and result states consistent with existing product language.

#### Constraints and assumptions

- Manual administration remains available.
- This slice cannot become `Ready for specification` until the provider and ownership decisions are known.

#### Dependencies

- FS-007 and FS-008.

#### Completion outcome

Selected external planning data can be introduced repeatably and safely, with planner-visible validation and no silent damage to existing schedule history.

#### Open clarification topics

- Provider, protocol, authentication, data direction, frequency, ownership, conflict resolution, deletion semantics, record matching, volume, and audit/retention requirements.

#### Specification status

Proposed — later release; blocked from readiness by integration decisions.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-017: Provider-Neutral Planning Data Import and Synchronization only after the external provider and ownership rules have been confirmed.

Outcome: Reduce manual maintenance by safely importing or synchronizing selected planning records.
Actors: Planner user and the selected external planning-data provider.
In scope: Confirmed record types; preview; validation; matching; create/update/skip outcomes; repeatability; source identifiers; per-record errors; protected schedules; explicit ownership and manual override behavior.
Out of scope: Unselected provider adapters, silent destructive synchronization, automatic publication, identity/SSO, and arbitrary external workflows.
Rules: Imported data follows the same domain validation; repeated source data avoids duplicates; source deletion never silently destroys referenced records; ownership/conflict rules must be explicit.
Dependencies: FS-007 and FS-008 plus confirmed provider decisions.
Completion: External data enters the planner repeatably and safely with a traceable outcome.
Clarification topics: Provider, protocol, authentication, direction, frequency, ownership, conflicts, deletion, matching, volume, and retention.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Do not proceed while product-level integration questions remain unresolved, and do not prescribe implementation before requirements are confirmed.
```

### FS-018: Unified Application Navigation

#### User or business outcome

A planner can move consistently between Schedule and Academic Data through one familiar navigation hierarchy without redundant, non-working, or overlapping controls.

#### Rationale for this slice boundary

Shared navigation is an independently visible cross-workflow outcome. It builds on the implemented Schedule and Academic Data views without reopening their scheduling or administration behavior, and it establishes the shell that the later calendar workspace must reuse.

#### Primary actors

- Planner user.

#### Preconditions

- FS-007 and FS-008 provide the implemented Schedule and Academic Data views and administration categories, including Lecturers and Rooms.

#### In scope

- One persistent left sidebar shared by Schedule and Academic Data.
- Schedule and Academic Data as the only top-level destinations.
- An expandable Academic Data parent containing Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms.
- Clear active states for the current top-level destination and Academic Data child.
- Removal of the separate fixed Schedule/Academic Data switcher and non-working Schedule sidebar links.
- Header controls that remain fully visible and operable without navigation overlap at supported viewport sizes.
- Keyboard-operable expansion and selection, visible focus, and semantic expanded/current state communication.
- Responsive navigation behavior that preserves access to every destination.

#### Out of scope

- New Dashboard functionality, new administration categories, changes to scheduling or catalog business behavior, a redesign of the calendar workspace, authentication, and a broader URL-routing or deep-linking redesign.

#### Main workflow

The planner opens Schedule, uses the persistent sidebar to expand Academic Data, selects an administration category, sees both parent and child context, completes the existing task, and returns to Schedule without encountering a second navigation model or covered header control.

#### Business rules

- The product exposes one primary application navigation model.
- Academic Data shows exactly the confirmed child destinations in the confirmed order.
- When an Academic Data child is active, that child and its parent context remain visible.
- Unavailable placeholder destinations are not shown as working navigation.
- Current location and focus are communicated by more than color alone.

#### Data inputs and outputs

Inputs are the current view, selected Academic Data category, and expansion state. Output is visible navigation and location state; no academic or scheduling domain data is created or changed by this slice.

#### Integrations

None.

#### UI references

- `docs/designs/resource-planner-unified-navigation-ground-truth.png` is the authoritative UX reference for navigation hierarchy, active states, spacing, and removal of the top switcher.
- Existing Schedule and Academic Data screens remain behavioral references for their underlying workflows.

#### Constraints and assumptions

- The existing visual language, terminology, and planner-only role remain authoritative.
- The approved image governs the navigation and shell; its illustrative table rows and form contents do not add new administration requirements.
- Accessibility and responsive behavior must be measurable in the specification.

#### Dependencies

- FS-007 and FS-008.

#### Completion outcome

The planner can reach Schedule and every Academic Data category from one consistent, accessible sidebar, with no dead duplicate destinations and no top-right control overlap.

#### Open clarification topics

- Whether Academic Data remains expanded after switching back to Schedule.
- The exact narrow-screen presentation, such as a drawer or another compact pattern.

#### Specification status

Ready for specification.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-018: Unified Application Navigation.

Product context: The Resource Planner has implemented Schedule and Academic Data views, but currently uses competing sidebars plus a fixed top view switcher that overlaps page-header controls. FS-018 replaces those navigation models without changing the underlying scheduling or administration workflows.
Outcome: Let a planner move consistently between Schedule and Academic Data through one familiar, accessible navigation hierarchy.
Actor: Planner user.
In scope: One persistent left sidebar; Schedule and Academic Data as top-level destinations; expandable Academic Data children in this order: Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, Rooms; clear parent/child active states; removal of the fixed top switcher and non-working Schedule links; unobstructed header controls; keyboard operation; visible focus; semantic expanded/current states; responsive access to all destinations.
Out of scope: Dashboard functionality, new categories, scheduling or catalog business changes, calendar-workspace redesign, authentication, and broader URL-routing or deep-linking redesign.
Rules: Expose one primary navigation model; keep active Academic Data parent/child context visible; do not present unavailable destinations as working navigation; communicate location and focus by more than color.
Data: Current view, selected category, and expansion state only; no domain-data behavior changes.
Integrations: None.
Dependencies: FS-007 and FS-008.
UI reference: docs/designs/resource-planner-unified-navigation-ground-truth.png is authoritative for the navigation hierarchy and shell. Existing screens remain behavioral references, and illustrative mock data does not expand scope.
Completion: Schedule and every Academic Data category are reachable from one consistent sidebar, with no dead duplicate destinations and no header overlap.
Clarification topics: Expansion persistence when returning to Schedule and the exact narrow-screen presentation.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define scenarios, functional requirements, accessibility behavior, responsive states, edge cases, assumptions, and measurable success criteria without implementation details.
```

## Deferred scope

- **Automated email delivery**: FS-015 deliberately uses planner-copied links; an email provider is not yet selected or required.
- **Institutional SSO and automated provisioning**: Deferred until authenticated collaboration is validated and an identity provider is known.
- **Multi-lecturer token review**: The accountless workflow covers the dominant one-course/one-lecturer case. Multi-lecturer review may be handled through FS-016 or a later scope update.
- **Multiple campus or regional holiday calendars**: The planner-only MVP uses one institution-wide calendar.
- **Provider-specific integration adapters**: Deferred until a provider-neutral contract and actual provider are known.
- **Automatic lecturer-driven schedule changes**: Lecturers remain advisory reviewers; planner users alone change schedules.
- **Mandatory approval gates**: Lecturer acceptance is not required for publication.
- **Automated destructive optimization of existing sessions**: Existing and manually controlled sessions are never silently deleted or moved.
- **Student registration, grading, and downstream operational room booking**: These remain outside the confirmed Resource Planner boundary.

## Product-level open assumptions

- The planner-only MVP may operate without authentication because it is restricted to planner users in its initial environment.
- One exam requirement per course is assumed until FS-012 clarification establishes otherwise.
- A single current published revision should remain visible while a replacement draft is prepared; exact course-versus-semester revision granularity remains for FS-013 clarification.
- Planner-maintained data remains authoritative until FS-017 defines ownership for synchronized fields.
- Optimization fairness and deterministic tie-breaking can be clarified within FS-010 without changing its global-maximization boundary.

## Change history

| Date | Change type | Affected slices | Summary | Rationale |
| ---- | ----------- | --------------- | ------- | --------- |
| 2026-07-14 | Ground-truth creation | FS-001–FS-017 | Reconstructed implemented FS-001–FS-006 and replaced the old roadmap with a validated planner-MVP and later-release slice map. | Preserve implemented behavior while defining conflict-aware planning, manual administration, exams, publication, calendar operations, lecturer review, identity, and future integration as coherent vertical slices. |
| 2026-07-16 | New slice, reordered slice, updated slice | FS-007, FS-014, FS-018 | Added unified application navigation as the recommended next slice, recorded the approved UX ground truth, and made the later calendar workspace reuse that navigation. | Separate the confirmed cross-workflow navigation outcome from implemented academic administration and remove the navigation ambiguity from FS-014. |
| 2026-07-16 | Reordered slice, status correction | FS-008, FS-018 | Recorded FS-008 as implemented, placed FS-018 after the completed FS-008 baseline, and added FS-008 as an FS-018 dependency. | Reflect completed resource administration work and the Lecturer and Room destinations that unified navigation must preserve. |
