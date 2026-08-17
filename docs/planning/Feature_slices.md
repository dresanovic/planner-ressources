# Feature Slices

## Document purpose

This document is the ground truth for the Resource Planner's product goals, current scope, explicit exclusions, external-system boundaries, development slices, dependencies, and later scope changes. Detailed requirements belong in the corresponding Spec Kit feature directories and must remain consistent with this document.

The earlier roadmap in `docs/planning/Planner_Resource_Feature_Slices_Scope.md` is retained as historical planning input. Where it differs from this document, this document takes precedence.

## Product overview

### Underlying product problem

University planners need to produce workable semester teaching and exam
schedules from changing academic, resource, and availability information.
Without one controlled planning workspace, conflicts, unscheduled work,
publication state, and lecturer input are fragmented across manual exchanges.
Lecturers currently have only a limited accountless review surface and cannot
transfer their complete assigned schedule to Outlook or submit structured
pre-planning unavailable dates without planner re-entry.
Across the existing planner interface, user-facing terminology is also spread
through individual components, calendar dates are frequently shown in the
machine-oriented ISO form, and some alerts expose only a generic category or
failure statement. This makes otherwise valid planning information harder to
interpret and leaves users unsure what happened or what to do next.
The planner application also does not currently identify or authenticate the
people who can reach its planner pages and APIs. Network reachability therefore
permits powerful planning and accountless-link management actions without an
application-level planner access decision.

### Why now

The planner scheduling, administration, publication, calendar workspace,
accountless lecturer-review foundation, and streamlined Schedule navigation are
implemented. Recent use of the Courses overview exposed a cross-application
clarity gap: the visible date format is unfamiliar to the intended European
users, terminology cannot be changed consistently in one place, and alerts such
as `OUTSIDE RECOMMENDED WINDOW` omit the applicable range and next action. The
next selected increment addresses this usability baseline before the remaining
lecturer collaboration extensions.
Subsequent schedule-regeneration testing also exposed a decision gap: an
automatic non-worsening rule can retain a complete but constraint-violating
current schedule instead of offering a valid partial alternative. Planners need
to see that trade-off and own the final atomic replacement decision.
With the scheduling baseline and accountless lecturer-review surface now
implemented, planner access itself is the next selected security boundary: the
application must protect planner work even when no VPN or institutional SSO is
available.

### Product-level success

- Planner users can create and maintain maximally complete semester schedules,
  understand conflicts and gaps, and retain publication control.
- When regeneration produces an alternative to existing teaching schedules,
  the planner can compare current and generated outcomes and explicitly accept
  the complete generated selection or leave the complete current selection
  unchanged.
- A lecturer can use a secure temporary link to see every assigned teaching and
  exam session in one semester revision without seeing another lecturer's data.
- A lecturer can provide session feedback, import a complete static schedule
  into Outlook, and submit whole-day pre-planning unavailability without an
  account.
- Approved lecturer unavailable dates become authoritative planning
  constraints without planner re-entry; rejected dates and lecturer feedback
  never change schedules automatically.
- Planner users can find all lecturer-originated work requiring action in one
  Lecturer coordination destination.
- Every user-facing calendar date follows one European display convention, and
  every known warning or failure gives enough context and recovery guidance for
  the affected user to decide what to do next.
- Selected German domain and workflow terminology can be changed consistently
  for one customer installation through a deployment-supplied override file,
  without rebuilding the application or editing individual screens.
- Only active named planner accounts can reach planner pages and APIs; exactly
  one system administrator manages planner access, while accountless lecturer
  links retain their existing minimum capabilities.

### Product goal

The Resource Planner helps university planner users create, review, correct,
and publish semester teaching and exam schedules while collecting scoped
lecturer input without surrendering planner authority. Its intended outcome is
to maximize scheduled teaching units while avoiding known resource conflicts,
make unavoidable gaps and their causes visible, and keep both planning
decisions and exceptional situations understandable and controllable.

### Initial release goal

The implemented baseline, FS-001 through FS-006, allows a planner user to generate one or several course drafts, configure course-semester constraints, review the semester, edit existing sessions, and inspect non-blocking validation alerts.

The planner-only MVP is complete when it additionally allows the planner to maintain planning data and availability, use multiple eligible resources, add or delete sessions, produce conflict-aware partial or complete semester plans, avoid institution-wide holidays, schedule exams, manage versioned publication states, and operate through a calendar-centered planning workspace.

Accountless lecturer collaboration follows the completed planner-only MVP.
Named planner authentication and administrator-controlled planner access are
the next selected release. Authenticated lecturer access and external data
synchronization remain later releases.

### Target users and actors

- **Planner user**: The primary actor. Earlier specifications use both “admin”
  and “office staff” for this planning authority. A named active planner
  manages planning data, generation, manual corrections, review states, and
  publication but cannot manage other planner accounts.
- **System administrator**: Exactly one active named planner with the additional
  authority to create, disable, reactivate, reset, and transfer planner access.
  The administrator has no broader scheduling authority than another planner.
- **Infrastructure operator**: Supplies the one-time initial bootstrap
  credential and, only when the sole administrator is locked out, a one-time
  administrator-recovery credential. Operating the deployment does not create
  an application account.
- **Lecturer**: An accountless collaboration actor for the current extension. A
  lecturer may inspect assigned sessions, comment, flag impossible sessions,
  export the scoped schedule, and submit whole-day unavailable dates, but
  cannot change a schedule or approve planning constraints.
- **External planning-data provider**: An unknown future system that may supply planning records through a provider-neutral integration.

### Main user outcomes

- Maintain the academic and resource data needed for scheduling without developer intervention.
- Generate complete or maximally complete semester schedules for one or several courses.
- Compare a valid regenerated alternative with the current selected schedules
  and make the final operation-wide replacement decision.
- Avoid lecturer, room, and cohort conflicts while respecting availability and capacity.
- Understand remaining unscheduled units and why they could not be placed.
- Correct schedules manually without losing saved generation constraints.
- Avoid institution-wide public holidays and schedule course exams.
- Review conflicts, remaining work, failures, and schedule states in a filterable calendar workspace.
- Read consistent interface terminology and European-formatted dates, and act
  on warnings or failures without having to interpret internal codes.
- Publish controlled schedule versions while retaining the current published version during later revisions.
- Collect accountless lecturer feedback across all assigned courses in one
  semester revision.
- Let lecturers import their complete assigned schedule into Outlook through a
  static iCalendar file.
- Collect whole-day pre-planning lecturer unavailability for planner approval.
- Protect all planner work with named local accounts and administrator-managed
  access without depending on a VPN or identity provider.
- Later, provide authenticated lecturer access and import or synchronize
  planning data.

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
- Post-generation comparison and planner-controlled atomic replacement when at
  least one selected course already has teaching sessions.
- Institution-wide holiday avoidance.
- Conflict-aware exam generation for explicitly enabled courses.
- Versioned `Draft → Ready for review → Published` lifecycle controlled by the planner.
- A calendar-centered operational workspace based incrementally on the saved UI reference.
- One consistent application navigation for Schedule and Academic Data without duplicate, dead, or overlapping controls.
- Accountless lecturer calendar/list review for all sessions assigned to one
  lecturer in one semester revision, with scoped feedback.
- One Lecturer coordination destination for access links, schedule feedback,
  and availability submissions.
- Static iCalendar export of the complete token-scoped lecturer schedule.
- Planner-issued, single-submission collection of whole-day lecturer
  unavailability with per-date planner approval.
- One shipped German terminology catalog with optional customer-specific
  deployment overrides for selected reusable terms across planner and
  accountless lecturer surfaces.
- European `DD.MM.YYYY` presentation for human-visible calendar dates throughout
  the application, with machine contracts retaining their required standard
  representations.
- Contextual, actionable warning and error messages that identify the affected
  item, explain the applicable condition when known, and state the available
  recovery or next action.
- Named local planner accounts, password authentication, one active
  browser-session-bound session per account, logout and expiry, and server-side
  default denial of planner pages and APIs.
- Exactly one system administrator who can create inactive planner accounts,
  manually share one-time setup or reset access, disable or reactivate accounts,
  and atomically transfer administrator authority.
- One-time startup bootstrap of the first administrator and one-time
  operator-assisted recovery when that administrator is locked out.
- Minimal account lifecycle visibility limited to current status plus creation,
  disablement, and reactivation timestamps.

### Out of scope

- Allowing lecturers to edit schedules directly.
- Requiring lecturer approval before a planner may publish.
- Silently replacing an existing schedule with a worse result.
- Combining independently accepted and rejected courses from one jointly
  optimized multi-course alternative.
- Automatically deleting or moving manually created sessions merely to improve optimization.
- Treating publication as an irreversible final state.
- Provider-specific integration behavior before a provider is selected.
- Automated email delivery or institutional SSO in the confirmed slice sequence.
- VPN-dependent authentication, external identity-provider dependence,
  multifactor authentication, passkeys, self-service forgotten-password flows,
  multiple concurrent planner sessions, session-management UI, general role
  management, detailed authentication audit history, and attribution of
  schedule or academic-data changes to a planner.
- Live calendar subscriptions, Outlook synchronization, or an Outlook API
  integration.
- Partial-day, recurring, or date-range lecturer-submitted availability.
- Persistent lecturer-availability submission drafts or approval/rejection
  history.
- A generic cross-product notification or Action Center.
- Runtime language switching, translation management, an administrator-facing
  label editor, or a full localization platform.
- Full production or room-booking execution outside the planning and publication workflow.

### Possible later scope

- Authenticated lecturer accounts that reuse the accountless collaboration
  workflows under a later-confirmed identity model.
- Provider-neutral import and synchronization of planning data.
- Automated review-email delivery, institutional SSO, and multi-lecturer token-review workflows.
- Live calendar subscriptions or calendar-provider synchronization.
- A generic role-aware Action Center if future authenticated users create a
  demonstrated need for cross-domain queues.
- Provider-specific adapters after an external source and ownership rules are known.

## External systems and integrations

### Current planner-only MVP

No external system is required. Planner users maintain all planning records manually in the product. Existing local or seeded records may support development and migration, but are not the intended long-term data-entry workflow.

### Planner authentication

FS-016 uses self-contained named local planner accounts and does not exchange
identity or credentials with a VPN, institutional SSO, email provider, or other
external system. A VPN may remain an optional deployment layer, but application
access decisions behave identically without it. Setup and reset links are
copied and delivered manually by the system administrator.

### Lecturer review link

FS-015 creates a secure review URL scoped to one lecturer and one semester
revision but does not send email. The planner copies the URL and sends it
through an external communication channel. No email provider integration is
required.

### Lecturer availability link

FS-021 uses a separate planner-issued URL scoped to one active lecturer and one
semester. It permits exactly one whole-day availability submission and does not
require an existing schedule revision or assignment. The fixed 72-hour link is
manually delivered and is not an external-system integration.

### iCalendar file export

FS-020 produces a static `.ics` file for manual import into Outlook. The
product sends no data through an Outlook or calendar-provider API, receives no
calendar data, and cannot revoke or remove a file after download.

### Future planning-data integration

The provider is unknown. FS-017 therefore defines a provider-neutral import or synchronization boundary for lecturers, rooms, cohorts/classes, courses, semesters/planning periods, study types, time windows, holidays, availability, and exam requirements. Data ownership, conflict resolution, authentication, and synchronization direction must be clarified before FS-017 becomes ready for specification.

## UI and supporting material

- Existing React/Vite planner screens and component behavior from FS-001 through FS-006 are the current UI baseline.
- `docs/designs/resource-planner-calendar-screen-reference.png` is the confirmed visual inspiration for the future primary planner workspace.
- The reference shows a navigation rail, remaining-hours/course list, validation summaries, filterable week calendar, schedule cards, and a session detail editor. It is inspiration rather than a pixel-perfect mandate.
- Its elements should be introduced gradually through relevant slices instead of through one disruptive redesign.
- `docs/designs/resource-planner-unified-navigation-ground-truth.png` is the confirmed UX ground truth for the shared application navigation and its relationship to Academic Data screens.
- The navigation reference is authoritative for hierarchy, active-state treatment, and removal of the separate top view switcher; it does not expand the underlying administration workflows or data fields.
- The implemented FS-019 Schedule workspace, FS-015 Lecturer reviews
  destination, `CalendarPlanningWorkspace`, session pane, lecturer
  administration, and resource-availability editor are behavioral references
  for the lecturer extensions.
- `docs/architecture/lecturer-action-surface.md` records the accepted Lecturer
  coordination boundary.
- `docs/architecture/availability-link-validity.md` records the accepted fixed
  72-hour availability-link rule.
- The user-provided Courses overview screenshot from 2026-08-10 is the
  motivating example for I-002: it shows ISO dates and an `Affected record`
  alert containing `OUTSIDE RECOMMENDED WINDOW` without the actual recommended
  period or an available next action.
- No authentication or account-administration mockup is available. FS-016 must
  reuse the existing application visual language for login, setup, and the
  administrator-only `Planner accounts` page.

## Product-level constraints and assumptions

- The implemented planner-only MVP predates authentication. FS-016 changes the
  current product boundary so planner pages and APIs require an active named
  local account.
- Planner authentication is self-contained and must not depend on VPN
  availability, VPN identity, institutional SSO, or email delivery.
- Authorization has only two fixed access levels: planner and exactly one
  system administrator. The only additional administrator authority is planner
  account management.
- One teaching unit is 45 minutes, and the implemented break and preferred-session-size rules remain authoritative unless a later specification explicitly changes them.
- A course may have multiple eligible lecturers and rooms; one Draft Session has exactly one lecturer and one room.
- Multi-lecturer teaching should use contiguous lecturer blocks instead of repeatedly alternating lecturers.
- Reusing the same eligible room is a preference, not a hard rule.
- Planner-created sessions may be saved with visible non-blocking validation alerts, consistent with current manual editing.
- Public holidays use one institution-wide calendar in the planner-only MVP.
- Published schedules are immutable snapshots. Later changes happen in a new draft revision while the current published version remains visible.
- The planner may move a revision to `Ready for review` or `Published` at any time and may publish despite missing or negative lecturer feedback.
- Existing calendar, list, filter, session-detail, lecturer, availability, and
  review components must be reused in access-appropriate modes rather than
  replaced by parallel lecturer-specific implementations.
- Accountless schedule-review and availability tokens grant separate minimum
  capabilities. Backend authorization must enforce the same restrictions shown
  by the UI.
- A downloaded iCalendar file remains under the lecturer's control after token
  expiry or revocation; the product must explain this before download.
- Approved lecturer unavailable dates use the existing planner-controlled
  availability model. Existing conflicting sessions are warned, never moved
  automatically.
- Human-visible calendar dates, including visible date-entry values, use
  zero-padded `DD.MM.YYYY`; API payloads, persistence values,
  sorting/comparison values, non-visible submission values, and standards-based
  exports may retain ISO or another mandated machine format.
- Selected reusable German domain and workflow terms are resolved from one
  effective catalog: shipped German defaults plus one optional customer override
  file supplied during deployment or startup. Ordinary German copy is not
  customer-configurable, and users cannot switch languages or edit terminology.
- A known validation, warning, or operation failure must be presented in plain
  German with the affected record or field, the reason or violated rule when
  known, and a concrete next action. Internal codes, stack traces, secret values,
  and raw infrastructure details are not user-facing explanations.
- The existing FastAPI, SQLAlchemy, React, and Vite technology standards and the project constitution remain binding for later specification and implementation.
- A regenerated alternative is never persisted over existing selected
  schedules before the planner explicitly accepts it. Cancelling or dismissing
  the comparison retains the complete current selection.
- A generated alternative must satisfy every currently active hard scheduling
  constraint. Planner authority permits retaining an older warned schedule; it
  does not permit the generator to offer a newly invalid candidate.

## Slice map

| Order | Slice ID | Slice name | User outcome | Depends on | Status                  |
| ----: | -------- | ---------- | ------------ | ---------- |-------------------------|
| 1 | FS-001 | Single-Course Draft Schedule Generation | Generate a valid draft for one course | None | Implemented             |
| 2 | FS-002 | Review Generated Schedule in Planner UI | Inspect and filter generated sessions | FS-001 | Implemented             |
| 3 | FS-003 | Configurable Generation Constraints and Courses Overview | Control generation windows and review a semester | FS-001, FS-002 | Implemented             |
| 4 | FS-004 | Manual Session Editing | Correct existing generated sessions | FS-003 | Implemented             |
| 5 | FS-005 | Conflict Detection | See non-blocking schedule validation alerts | FS-003, FS-004 | Implemented             |
| 6 | FS-006 | Multi-Course Draft Generation | Generate several course drafts in one operation | FS-003, FS-005 | Implemented             |
| 7 | FS-007 | Academic Planning Data Administration | Maintain academic scheduling inputs in the UI | FS-006 | Implemented             |
| 8 | FS-008 | Resource Eligibility and Availability | Maintain eligible resources and availability | FS-007 | Implemented             |
| 9 | FS-018 | Unified Application Navigation | Move consistently between Schedule and Academic Data | FS-007, FS-008 | Implemented             |
| 10 | FS-009 | Manual Session Creation, Deletion, and Remaining Units | Complete or clear schedules manually | FS-006 | Implemented             |
| 11 | FS-010 | Conflict-Aware Semester Optimization | Maximize conflict-free scheduled units | FS-008, FS-009 | Implemented             |
| 12 | FS-011 | Institution-Wide Holiday Calendar and Avoidance | Prevent generation on public holidays | FS-007, FS-010 | Implemented             |
| 13 | FS-012 | Conflict-Aware Exam Scheduling | Generate exams for enabled courses | FS-008, FS-010, FS-011 | Implemented             |
| 14 | FS-013 | Versioned Review and Publication Lifecycle | Publish controlled schedule revisions | FS-006, FS-012 | Implemented             |
| 15 | FS-014 | Calendar Planning Workspace and Operational Dashboard | Operate the semester from one calendar overview | FS-009 through FS-013, FS-018 | Implemented             |
| 16 | FS-019 | Streamlined Schedule Workspace | Use focused Schedule destinations and in-pane session correction | FS-013, FS-014, FS-018 | Implemented — manual acceptance evidence pending |
| 17 | I-001 | Containerized Application Distribution | Run the complete application as one versioned container image | Implemented application baseline | Implemented |
| 18 | I-002 | Consistent Labels, European Dates, and Actionable Messages | Understand interface wording, dates, warnings, and failures consistently | FS-019 | Partially implemented — implementation, validation, and acceptance follow-ups remain open |
| 19 | I-003 | Unified Teaching Schedule Generation | Generate one or several courses through one conflict-aware workflow | FS-010 through FS-013, FS-019 | Implemented |
| 20 | I-004 | Planner-Controlled Schedule Regeneration Decision | Compare and atomically accept or reject a valid regenerated alternative | I-003, FS-013, FS-019, I-002 | Implemented — manual acceptance evidence pending |
| 21 | FS-015 | Accountless Lecturer Token Review | Review all assigned sessions and provide scoped feedback through the shared calendar workspace | FS-013, FS-014, FS-019 | Implemented — manual/deployment acceptance evidence pending |
| 22 | FS-016 | Authenticated Planner Access and Account Administration | Protect planner work with named accounts and administrator-managed access | I-001, FS-015, FS-019 | Ready for specification |
| 23 | FS-020 | Lecturer iCalendar Export | Import the complete assigned semester schedule into Outlook | FS-015 | Implemented — release acceptance evidence pending |
| 24 | FS-021 | Lecturer Unavailability Submissions | Collect and approve whole-day pre-planning lecturer unavailability | FS-008, FS-015, FS-019 | Ready for specification |
| 25 | FS-022 | Authenticated Lecturer Access | Reuse lecturer collaboration through ongoing authenticated identity | FS-015, FS-016, FS-020, FS-021 | Deferred |
| 26 | FS-017 | Provider-Neutral Planning Data Import and Synchronization | Reduce manual catalog maintenance | FS-007, FS-008 | Proposed — later release |

**Improvement sequence:** `I-001` through `I-004`, with detailed artifacts in their matching `specs/I-.../` directories.

**Recommended next slice:** `FS-016 – Authenticated Planner Access and Account Administration`.

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

- A manually added session defaults Lecturer, Cohort, and Room from the Course, allows the planner to override them from active-record dropdowns for that session only, and may be saved with non-blocking lecturer, room, cohort, or window alerts, consistent with existing editing.
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

Implemented.

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
- Preserve an existing schedule when a candidate would schedule fewer units in
  the implemented automatic-replacement baseline. I-004 supersedes this
  automatic persistence decision with explicit planner comparison and choice.
- Allow equal-unit automatic replacement only when it reduces conflicts or
  improves preference compliance in the implemented baseline; I-004 requires
  planner acceptance before any regenerated alternative replaces existing
  selected schedules.
- Retain explicit same-semester replacement confirmation and stale-data safeguards.
- Expose a future unavailable-date input so holidays can be added without redesigning the optimizer.

#### Out of scope

- Public-holiday data, exam generation, unapproved automatic deletion of existing sessions, and guaranteed mathematical optimality beyond the measurable objective chosen in the specification.

#### Main workflow

The planner selects courses and a semester, reviews replacement implications,
and starts conflict-aware generation. The implemented baseline evaluates
selected courses together against existing schedules and availability, saves
complete or partial improvements, preserves non-improvements, and reports
scheduled and remaining units with reasons. I-004 changes only the final
replacement decision for regenerated alternatives: the planner compares and
accepts the joint result before it is persisted over existing selected work.

#### Business rules

- No generated candidate may introduce a known lecturer, room, or cohort overlap.
- Capacity, semester, and active-window rules remain applicable.
- Existing unselected and manual sessions are constraints, not automatically movable items.
- The primary objective is greatest total scheduled units across the selection.
- Preference improvement never justifies automatically replacing a schedule
  with fewer units. Under I-004, the planner may explicitly accept a valid
  partial alternative after seeing the completeness and constraint trade-off.
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

The planner receives a conflict-aware semester result that maximizes scheduled
units, retains valid partial work, explains gaps, and never silently worsens an
existing course schedule. After I-004, any replacement of existing selected
work additionally requires the planner's explicit post-generation acceptance.

#### Open clarification topics

- Fairness or minimum-allocation guardrails when maximizing total units could starve one course.
- Deterministic tie-break order after units, conflicts, teaching preferences, lecturer continuity, and room continuity.
- Whether a partial plan with zero newly placed units is stored or represented as unchanged/failed.
- Performance target and largest supported globally optimized selection.

#### Specification status

Implemented.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-010: Conflict-Aware Semester Optimization.

Product context: FS-006 generates selected courses independently. The next scheduling outcome must reason globally across a semester and save useful partial work.
Outcome: Maximize scheduled teaching units across selected courses without generating lecturer, room, or cohort overlaps.
Actors: Planner user.
In scope: Global selected-course optimization; existing selected/unselected/manual sessions as fixed occupancy; lecturer/room availability; multiple eligible resources; contiguous lecturer and same-room preferences; complete and partial saved plans; remaining units and reasons; the implemented automatic non-worsening replacement baseline; confirmation/stale protection; future unavailable-date input. I-004 separately owns the post-generation planner decision that supersedes automatic replacement when existing selected schedules are present.
Out of scope: Holiday data, exams, automatic deletion/movement of existing sessions, and unexplained schedule worsening.
Rules: Maximize total scheduled units; generated candidates are conflict-free; in the implemented FS-010 baseline fewer-unit candidates never replace existing schedules; unchanged outcomes preserve data. After I-004, a valid fewer-unit candidate may replace existing selected schedules only through explicit planner acceptance of the complete joint result.
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

Implemented.

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

Implemented.

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

Implemented.

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

Implemented.

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

A planner can share one semester revision with its corresponding lecturer
through a temporary link, and the lecturer can review every assigned teaching
and exam session in the familiar calendar/list workspace and provide scoped
feedback without an account.

#### Rationale for this slice boundary

The implemented secure-link and feedback behavior, the expanded
lecturer-scoped workspace, and the planner's Lecturer coordination surface all
deliver one end-to-end review outcome. Static calendar export and pre-planning
availability collection are independently valuable workflows and remain
FS-020 and FS-021.

#### Primary actors

- Planner user.
- Lecturer reviewing all personal assignments in one semester revision.

#### Preconditions

- FS-013 provides a reviewable schedule revision.
- FS-014 and FS-019 provide the implemented calendar/list workspace, filters,
  session pane, and Schedule navigation to reuse.

#### In scope

- Planner-generated review token bound to exactly one lecturer and one semester
  revision.
- Every teaching and exam session currently assigned to that lecturer across
  all courses in the bound revision.
- A link containing the token that the planner copies and sends manually.
- The implemented one-, two-, or three-day validity choice with three days as
  default, planner-controlled revocation, and replacement issuance.
- Reuse of the planner's calendar and list components in a restricted lecturer
  mode.
- The same applicable course, cohort, room, study-type, session-type,
  lifecycle, and validation filters, while lecturer identity is fixed as
  visible context rather than offered as a selectable filter.
- Selection of a scoped session opens the reused detail pane with feedback
  actions instead of planner edit, create, delete, lifecycle, or generation
  controls.
- Lecturer comments and “this session is not possible” flags, optionally including suggested alternatives in comment text.
- Feedback visibly associated with the relevant schedule revision and session.
- Rename and broaden the planner's existing `Lecturer reviews` destination to
  `Lecturer coordination`, containing access-link management and schedule
  feedback with counts, filters, and direct navigation to affected sessions.
- Planner ability to publish regardless of missing or negative feedback.

#### Out of scope

- One token covering multiple lecturers, automated email delivery, lecturer
  accounts, lecturer schedule editing, mandatory acceptance, feedback as a
  publication gate, iCalendar export, and lecturer availability submissions.

#### Main workflow

The planner opens Lecturer coordination for a Working revision, issues and
copies a link for one assigned lecturer, and sends it manually. The lecturer
opens the link, reviews all personal assignments in calendar or list mode,
filters them, selects a session, and comments or flags it as impossible from
the restricted detail pane. The planner sees the feedback in Lecturer
coordination, opens affected sessions in the planner workspace, and decides
whether to revise or publish.

#### Business rules

- The token grants only the minimum review scope for one lecturer and one
  semester revision, regardless of how many assigned courses are included.
- It is reusable until expiry, revocation, or replacement.
- Expired or revoked tokens expose no schedule data and provide safe feedback.
- Newly assigned sessions enter scope and sessions reassigned away leave scope
  according to the implemented FS-015 projection rules.
- The lecturer cannot alter schedule, resource, publication, or availability
  records.
- Restricted actions must be enforced by backend authorization as well as the
  displayed component mode.
- Silence or objections do not prevent planner publication.
- The review deadline is informational; token expiry is an access-security rule rather than an approval requirement.

#### Data inputs and outputs

Inputs are the reviewable revision, lecturer identity, current assignments,
token lifecycle actions, comments, and impossible-session flags. Outputs are a
scoped review link, a lecturer-only schedule projection, and
revision/session-associated feedback visible to the planner.

#### Integrations

No email integration. The planner uses an external communication channel manually.

#### UI references

- Reuse the implemented FS-014/FS-019 calendar, list, filters, session pane,
  responsive behavior, and accessibility semantics.
- Reuse the implemented FS-015 link-management and feedback components inside
  the renamed Lecturer coordination destination.
- `docs/architecture/lecturer-action-surface.md` defines the accepted
  lecturer-specific coordination boundary.

#### Constraints and assumptions

- The implemented FS-015 security, privacy, expiry, safe-failure, rate-limit,
  and immutable-feedback behavior remains authoritative.
- Component reuse is mandatory, but access-mode composition must not expose
  planner-only controls or data.
- Security and privacy requirements for token generation, storage, expiry, logging, and URL exposure must be explicit in the specification.

#### Dependencies

- FS-013, FS-014, and FS-019.

#### Completion outcome

A lecturer can securely review every personal assignment in one semester
revision through the shared calendar/list experience and provide session
feedback, while the planner can find and act on that feedback without losing
authority.

#### Open clarification topics

- Whether fixed lecturer context is rendered as a read-only field, chip, or
  equivalent accessible context indicator.
- Exact empty-state and filter behavior when every assignment leaves scope.
- Responsive composition of the shared calendar and restricted detail pane.

#### Specification status

Implemented — manual/deployment acceptance evidence pending.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to revise the specification for FS-015: Accountless Lecturer Token Review.

Product context: The Resource Planner already has an implemented secure temporary-link and immutable-feedback baseline for one lecturer and one semester revision. Planner calendar/list workflows, filters, session panes, and focused Schedule navigation are implemented under FS-014 and FS-019. The next outcome is to give accountless lecturers the same understandable schedule-review experience without granting planner authority or building parallel components.
Product-level success: A lecturer sees every and only personal teaching and exam assignment across all courses in the bound revision, can provide session feedback, and the planner can handle that feedback in one Lecturer coordination destination.
Actors: Planner user and one accountless lecturer.
In scope: Preserve the implemented one-lecturer/one-revision token lifecycle, one-to-three-day validity with three-day default, manual delivery, revocation, replacement, privacy, safe-failure, misuse controls, comments, impossible-session flags, immutable attribution, and non-blocking publication. Reuse the FS-014/FS-019 calendar and list components in restricted lecturer mode; expose applicable course, cohort, room, study-type, session-type, lifecycle, and validation filters; show lecturer identity as fixed context rather than a selectable filter; open selected teaching or exam sessions in the reused detail pane with feedback actions only; rename and broaden the planner's Lecturer reviews destination to Lecturer coordination with link management, feedback counts/filters, and navigation to affected sessions.
Out of scope: A token covering multiple lecturers, automated email, lecturer accounts, planner or lecturer schedule mutation through the public link, publication gates, iCalendar export, availability submissions, and a generic Action Center.
Main workflow: The planner issues and manually sends a link from Lecturer coordination. The lecturer reviews all personal assignments in calendar or list mode, filters the projection, selects a session, and comments or flags it as impossible. The planner finds the item in Lecturer coordination, opens the affected session, and decides whether to revise or publish.
Business rules: Scope is one lecturer and one revision across all assigned courses; assignment changes update the projection; expired, revoked, replaced, or unusable links expose no data; feedback is advisory and cannot block publication; planner-only operations are absent from the lecturer mode and denied by the backend.
Data inputs and outputs: Revision, lecturer, current teaching/exam assignments, token lifecycle actions, filters, comments, and impossible-session flags produce a scoped schedule projection and traceable feedback.
External systems and integrations: No email integration; the planner manually sends the URL through an external communication channel.
UI references: Reuse the implemented CalendarPlanningWorkspace, list view, filters, session pane, LecturerReviewManagement behavior, FS-019 Schedule navigation, and docs/architecture/lecturer-action-surface.md.
Dependencies and assumptions: FS-013, FS-014, and FS-019 are implemented. Existing FS-015 security and feedback semantics remain authoritative. Component reuse is mandatory, with access-specific composition and backend enforcement.
Completion outcome: An accountless lecturer can securely review and comment on every personal assignment in the familiar calendar/list workspace, and the planner can manage the resulting feedback through Lecturer coordination.
Known clarification topics: Fixed-context presentation, empty/filter states after assignment changes, and responsive restricted-pane composition.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define user scenarios, functional requirements, edge cases, assumptions, security and accessibility requirements, and measurable success criteria. Preserve the implemented FS-015 baseline and do not introduce unrelated implementation or product scope.
```

### FS-016: Authenticated Planner Access and Account Administration

#### User or business outcome

Only active named planners can reach planner work, and exactly one system
administrator can grant, remove, recover, or transfer that access without
depending on a VPN, institutional SSO, or email delivery.

#### Rationale for this slice boundary

Planner authentication, first-administrator bootstrap, and the minimal account
lifecycle form one end-to-end access-control outcome. Authenticated lecturer
access is independently valuable, depends on additional lecturer workflows,
and is therefore split into deferred FS-022.

#### Primary actors

- Planner user.
- System administrator, who is also a planner.
- Infrastructure operator for initial bootstrap and emergency administrator
  recovery only.
- Accountless lecturer, whose existing token-scoped access must remain intact.

#### Preconditions

- I-001 provides the supported startup and container deployment boundary.
- FS-019 provides the current planner application shell and navigation.
- FS-015 provides the anonymous lecturer-review boundary that authentication
  must preserve.

#### In scope

- Named local planner accounts with a login name, display identity, password,
  active state, and one fixed planner or system-administrator access level.
- Server-side protection of every planner page, planner API read, and planner API
  mutation; anonymous access remains limited to the existing explicit lecturer
  capabilities.
- One-time startup bootstrap credential that can establish the first named
  system administrator only while none exists.
- Exactly one active system administrator with ordinary planner authority plus
  account creation, reset, disablement, reactivation, and administrator
  transfer.
- Administrator creation of an inactive planner and manual delivery of a
  one-time, expiring setup link or code so the planner chooses a password.
- A simple administrator-issued reset-access action that invalidates the old
  password and session and provides a fresh one-time setup link or code; no
  self-service forgotten-password workflow.
- Planner login, logout, and authenticated password change.
- Exactly one active browser-session-bound session per account. Closing the
  browser ends it, a new login replaces it, and inactivity plus absolute
  lifetime limits apply.
- Immediate loss of access after account disablement, password change/reset,
  session replacement, expiry, or operator-assisted administrator recovery.
- Atomic transfer of system-administrator authority to one active planner; the
  prior administrator remains an ordinary planner and the product never has
  zero or multiple active administrators after bootstrap.
- One-time startup recovery credential for an infrastructure operator to let a
  locked-out administrator choose a new password and invalidate the prior
  administrator session.
- One administrator-only `Planner accounts` page showing account identity,
  current state, and creation, disablement, and reactivation timestamps.

#### Out of scope

- Authenticated lecturer accounts or changes to accountless lecturer-review and
  availability behavior.
- Institutional SSO, VPN-derived identity, email delivery, automated identity
  provisioning, multifactor authentication, and passkeys.
- Self-service forgotten-password recovery, administrator visibility or direct
  assignment of another user's password, and permanent bootstrap or recovery
  credentials.
- Multiple concurrent sessions, session lists or device management, general
  roles or permissions, and more than one system administrator.
- Login or password-event history, general security-event auditing, and
  attribution of schedule, publication, or academic-data changes to a planner.

#### Main workflow

On the first deployment, the operator supplies a one-time startup credential.
The first administrator redeems it, chooses a named login and password, and
thereafter signs in like every planner. The administrator creates an inactive
planner, manually shares the generated setup access, and the planner chooses a
password and signs in. The planner performs existing work, changes their own
password when needed, and logs out or is signed out by expiry or session
replacement. The administrator can reset, disable, reactivate, or transfer
access. If the sole administrator is locked out, the operator supplies a
one-time startup recovery credential so that administrator can reset access.

#### Business rules

- Planner authorization is enforced by the backend for every protected read and
  action; hiding navigation or controls is never sufficient.
- Bootstrap works only while no administrator exists and is unusable after the
  first administrator is established.
- Setup and reset access is single-use and expires; successful redemption makes
  the account active and invalidates the setup credential.
- Disabled accounts cannot authenticate or use an existing session.
- Reactivation requires fresh administrator-issued setup access and a new
  password.
- Password change/reset, account disablement, a replacing login, and
  administrator recovery invalidate the account's current session.
- Closing the browser, inactivity expiry, absolute expiry, or logout ends the
  single active session.
- Only the system administrator can manage accounts, and administrator transfer
  changes the extra authority immediately and atomically.
- Accountless lecturer credentials never become planner credentials and retain
  only their existing scoped public capabilities.
- Only current account state plus creation, disablement, and reactivation
  timestamps are exposed; no broader audit history is introduced.

#### Data inputs and outputs

Inputs include the one-time bootstrap or recovery credential, planner login and
display identity, password setup/change values, account lifecycle actions, and
administrator transfer choice. Outputs are active or inactive named planner
accounts, one-time setup/reset access, one current server-side session per
account, current account status and lifecycle timestamps, and clear access or
recovery outcomes.

#### Integrations

None. Authentication is application-owned. A VPN may add network protection but
is neither required nor trusted for identity. Setup and reset access is copied
and delivered manually without an email provider.

#### UI references

No authentication mockup exists. Login, first setup, reset setup, expiry, access
failure, and the administrator-only `Planner accounts` page must reuse the
existing application's visual language, responsive behavior, terminology, and
accessibility patterns.

#### Constraints and assumptions

- Local password authentication and server-side opaque sessions are confirmed.
- Production credential and session exchange must be protected in transit.
- The application remains one FastAPI/React/SQLite deployment and follows the
  project constitution's simplicity requirement.
- Exact password rules, setup/reset validity, inactivity timeout, absolute
  session lifetime, and user-facing wording can be resolved without changing
  the slice boundary.

#### Dependencies

- I-001, FS-015, and FS-019.

#### Completion outcome

An unauthenticated person cannot use the planner application; active named
planners can complete all existing planner workflows; only the sole system
administrator can control planner access; and first setup, ordinary reset, and
administrator recovery work without an external identity or email system while
accountless lecturer access remains unchanged.

#### Open clarification topics

- Exact password acceptance rules and retry limits.
- Exact one-time setup/reset validity period.
- Exact inactivity and absolute session lifetimes.
- Final German labels and safe generic authentication-failure wording.

#### Specification status

Implemented — release acceptance evidence pending.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for the following development
slice.

Slice ID: FS-016
Slice name: Authenticated Planner Access and Account Administration

Product context:
The Resource Planner's scheduling and accountless lecturer-review workflows are
implemented, but anyone who can reach the application can currently use planner
pages and APIs. The application must protect planner work independently of VPN
or institutional SSO while preserving existing minimum-scope lecturer links.

Product-level success:
Only active named planners can use planner functionality; exactly one system
administrator manages planner access; first setup and recovery work without an
identity or email provider; and existing accountless lecturer capabilities
remain unchanged.

User or business outcome:
Protect all planner work with named local accounts and let exactly one system
administrator create, disable, reactivate, reset, recover, and transfer planner
access through a simple workflow.

Primary actors:
Planner user; system administrator who is also a planner; infrastructure
operator for initial bootstrap and emergency administrator recovery;
accountless lecturer whose existing scoped access must remain available.

In scope:
Named local planner accounts; password setup and login; backend default denial
of planner pages and API reads/mutations; explicit preservation of existing
anonymous lecturer capabilities; one-time startup bootstrap of the first named
administrator; exactly one administrator with only the additional planner-
account-management authority; inactive-account creation; manually delivered
one-time expiring setup and reset links/codes; self-service password change;
login and logout; one active browser-session-bound server-side session per
account; replacement of an earlier session by a new login; browser-close,
inactivity, and absolute expiry; disablement and reactivation; atomic
administrator transfer; one-time operator-assisted startup recovery of a
locked-out administrator; and an administrator-only Planner accounts page with
current state plus creation, disablement, and reactivation timestamps.

Out of scope:
Authenticated lecturers; changes to existing lecturer-token behavior; SSO; VPN
identity or dependency; email delivery; automated provisioning; MFA; passkeys;
self-service forgotten-password recovery; administrator access to or direct
assignment of another user's password; permanent bootstrap/recovery secrets;
multiple concurrent sessions; session/device-management UI; broad roles;
multiple administrators; detailed login/password/security audit history; and
planner attribution on schedule, publication, or academic-data mutations.

Main workflow:
The operator supplies a one-time startup credential. While no administrator
exists, the first administrator redeems it and chooses a named login and
password. The administrator then signs in normally, creates an inactive planner,
and manually shares one-time setup access. The planner chooses a password and
uses all existing planner workflows. The administrator may reset, disable,
reactivate, or transfer access. A reset or reactivation uses fresh one-time
access rather than email or a Forgot password workflow. If the sole
administrator is locked out, the operator supplies a one-time startup recovery
credential that permits a password reset and invalidates the prior session.

Business rules:
Backend authorization protects every planner read and action; bootstrap works
only before the first administrator exists; setup/reset access is single-use and
expiring; disabled accounts and invalid sessions expose no planner data; exactly
one active administrator exists after bootstrap; administrator transfer is
atomic; one account has at most one current session; new login, logout,
browser-close, expiry, password change/reset, disablement, and administrator
recovery invalidate the applicable session; lecturers' capability credentials
cannot grant planner access; and visible lifecycle history is limited to account
creation, disablement, and reactivation.

Data inputs and outputs:
Bootstrap/recovery credential, planner identity, password setup/change values,
account actions, and transfer choice produce named account state, one-time
setup/reset access, one current session, lifecycle timestamps, and clear access
or recovery outcomes. Raw passwords and usable credential/session secrets must
never appear in account listings or user-facing diagnostics.

External systems and integrations:
None. Authentication is application-owned. VPN is optional defense in depth,
not a dependency or identity source. Setup/reset access is manually delivered;
there is no email or external identity provider.

UI references:
No authentication mockup exists. Reuse the existing application's visual
language, responsive behavior, terminology, navigation, and accessibility
patterns for login, setup, failure/expiry states, and the administrator-only
Planner accounts page.

Dependencies and assumptions:
I-001, FS-015, and FS-019 are implemented. Local password authentication,
server-side opaque sessions, exactly one administrator, and one active session
per account are confirmed. Production credential/session exchange is protected
in transit. Exact password rules, link validity, session timeouts, and German
wording remain clarification topics.

Completion outcome:
Anonymous users cannot use planner functionality; active planners can complete
all existing planner workflows; only the sole administrator can manage access;
bootstrap and both ordinary and emergency recovery work without external
services; and accountless lecturer access continues unchanged.

Known clarification topics:
Password acceptance and retry rules; setup/reset validity; inactivity and
absolute session lifetimes; and final German authentication wording.

Keep the specification strictly limited to this slice and consistent with
docs/planning/Feature_slices.md. Define independently testable user scenarios,
functional requirements, authorization and privacy requirements, edge cases,
assumptions, accessibility behavior, and measurable success criteria. Do not
introduce authenticated lecturer accounts, external identity integration,
general role management, broad auditing, implementation details, or unrelated
product scope.
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

Implemented.

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

### FS-019: Streamlined Schedule Workspace

#### User or business outcome

A planner can move among focused Calendar, Versions, Exams, and Lecturer
coordination destinations, inspect or correct teaching and exam sessions in a
responsive contextual pane, and reclaim workspace width without losing the
current planning context.

#### Rationale for this slice boundary

This slice reorganizes implemented planner workflows without changing their
domain outcomes. It is recorded separately because focused Schedule
destinations, in-pane correction, and independently collapsible navigation are
one coherent cross-workflow usability outcome and are now a dependency for the
lecturer workspace extensions.

#### Primary actors

- Planner user.

#### Preconditions

- FS-013 provides versioned lifecycle behavior.
- FS-014 provides the calendar workspace and operational summaries.
- FS-018 provides the shared application navigation.

#### In scope

- Schedule as a parent with focused Calendar, Versions, Exams, and Lecturer
  reviews destinations in the implemented workspace.
- Calendar session selection opening teaching or exam detail and established
  editing in an adaptive right-side pane without forcing List mode.
- Compact shared semester/revision/course context across Schedule
  destinations.
- Independent pinning of application navigation and visibility of full
  Planning inputs.
- Preservation of calendar mode, visible period, filters, selection, pane, and
  unsaved-edit safeguards across applicable navigation and responsive states.
- Existing lifecycle, exam, scheduling, validation, and Academic Data behavior
  preserved.

#### Out of scope

- New scheduling, lifecycle, publication, exam, availability, or authorization
  rules.
- New backend endpoints or persistence behavior.
- Lecturer access itself; FS-015 reuses the resulting workspace components.

#### Main workflow

The planner opens a focused Schedule destination, changes shared context,
returns to Calendar, selects a teaching or exam session, inspects or corrects
it in the contextual pane, and optionally collapses navigation or Planning
inputs while all applicable context and unsaved-change protections remain
intact.

#### Business rules

- Navigation-only actions never mutate planning or academic data.
- Planner correction preserves every established scheduling, lifecycle,
  validation, conflict, capacity, holiday, and stale-state rule.
- Only one Schedule child is current.
- Unsaved changes must be explicitly retained or discarded before replacing
  their editing context.

#### Data inputs and outputs

Inputs are current Schedule destination, semester/revision/course context,
calendar state, navigation preferences, selected session, and established edit
values. Outputs are focused workspace and presentation state plus any schedule
change already authorized by an existing workflow.

#### Integrations

None.

#### UI references

- `specs/019-streamline-schedule-workspace` is the implemented specification
  and design-artifact set.
- The implemented `ApplicationNavigation`, `CourseSchedulePage`,
  `CalendarPlanningWorkspace`, and contextual session pane are authoritative
  behavioral references.

#### Constraints and assumptions

- FS-019 is merged and covered by the complete client-side automated suite.
- Manual browser, assistive-technology, and representative-reviewer acceptance
  evidence remains incomplete and must not be reported as passed.

#### Dependencies

- FS-013, FS-014, and FS-018.

#### Completion outcome

The focused Schedule workspace is implemented and reusable, while its remaining
manual acceptance evidence is explicitly tracked rather than inferred.

#### Open clarification topics

- No unresolved product-boundary questions.
- The remaining work is validation evidence under tasks T059 through T061 in
  `specs/019-streamline-schedule-workspace/tasks.md`.

#### Specification status

Implemented — manual acceptance evidence pending.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to recreate or revise the specification for FS-019: Streamlined Schedule Workspace.

Product context: The Resource Planner has implemented calendar planning, versioned publication, exam workflows, and shared application navigation. FS-019 reorganizes these planner workflows into focused Schedule destinations and a responsive in-pane correction experience without changing domain behavior.
Product-level success: Planners can reach Calendar, Versions, Exams, and Lecturer reviews predictably, correct sessions without losing calendar context, and reclaim working width while all existing business rules remain intact.
User or business outcome: Use focused Schedule destinations and an adaptive session pane without forced view changes or lost context.
Primary actors: Planner user.
In scope: Schedule children; compact shared context; teaching/exam detail and correction in the adaptive pane; retained Calendar mode, period, filters, selection, and clean-pane context; unsaved-change protection; independent navigation pinning and Planning-input visibility; established lifecycle and exam workflows in focused destinations.
Out of scope: New backend behavior, scheduling rules, lifecycle states, permissions, lecturer access, or academic-data changes.
Main workflow: Navigate among focused Schedule destinations, return to retained Calendar context, inspect or correct a session in the pane, and control workspace width without accidental data mutation.
Business rules: Navigation does not mutate data; existing domain validation remains authoritative; unsaved edits require an explicit decision; current state and focus remain accessible.
Data inputs and outputs: UI destination, context, pane, preference, and established edit state; no new domain aggregate.
External systems and integrations: None.
UI references: specs/019-streamline-schedule-workspace plus the implemented application navigation, CourseSchedulePage, CalendarPlanningWorkspace, and session pane.
Dependencies and assumptions: FS-013, FS-014, and FS-018. The implementation is merged; manual acceptance tasks T059–T061 remain pending or blocked.
Completion outcome: The streamlined planner workspace remains consistent with its implemented behavior and pending validation is reported accurately.
Known clarification topics: No product-boundary topics; only outstanding manual acceptance evidence.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md and the implemented baseline under specs/019-streamline-schedule-workspace. Do not introduce new domain behavior or claim unperformed validation.
```

### FS-020: Lecturer iCalendar Export

#### User or business outcome

An accountless lecturer can download the complete assigned teaching and exam
schedule for one semester revision as an Outlook-compatible `.ics` file and
import it into a personal calendar.

#### Rationale for this slice boundary

Static calendar transfer is an independently useful integration outcome with
its own privacy, file-format, event-identity, and import behavior. It reuses the
FS-015 lecturer schedule projection but does not change review feedback or
introduce live synchronization.

#### Primary actors

- Accountless lecturer with a valid FS-015 schedule-review token.

#### Preconditions

- The revised FS-015 lecturer workspace provides a valid token-scoped schedule
  projection for one lecturer and one semester revision.

#### In scope

- A download action in the lecturer calendar/list workspace.
- One static `.ics` file containing every teaching and exam session currently
  assigned to the scoped lecturer across all courses in the bound revision.
- Export of the complete lecturer scope regardless of temporary calendar mode,
  visible period, filters, or selected session.
- Outlook as the primary import target while remaining standards-compatible
  with other iCalendar consumers where practical.
- Clear course/session identity, date, start/end time, session type, and
  relevant location/context required to recognize each event.
- Institution-local time-zone representation and stable event identifiers
  suitable for a deterministic export.
- A concise notice that the downloaded file remains outside product control
  after token expiry, revocation, replacement, or revision changes.
- Download only while the FS-015 review token is valid and its scoped schedule
  projection is complete.

#### Out of scope

- A subscribed calendar URL, live feed, refresh, two-way synchronization,
  Outlook or calendar-provider API, planner-side export, filtered/partial
  export, automatic deletion from an imported calendar, feedback/comments,
  internal security data, and planner-only warnings.

#### Main workflow

The lecturer opens a valid schedule-review link, reviews the schedule, chooses
Download calendar, acknowledges the static-file notice, receives one `.ics`
file for the complete scoped revision, and imports it manually into Outlook.

#### Business rules

- Export contains every and only session assigned to the token's lecturer in
  the token's semester revision.
- UI filters never reduce the exported event set.
- A failed or incomplete schedule projection produces no misleading partial
  file.
- Token expiry or revocation prevents future downloads but cannot recall an
  already downloaded file.
- Export never changes schedule, feedback, lifecycle, or calendar-provider
  data.

#### Data inputs and outputs

Inputs are the valid FS-015 token scope and its complete teaching/exam
projection. Output is a static `.ics` file with deterministic calendar and
event metadata.

#### Integrations

Manual file export/import only. Outlook is the primary target, but no Outlook
API, account connection, or data exchange occurs.

#### UI references

- Reuse the FS-015 lecturer calendar/list header and existing action/button
  patterns.
- No separate export application or duplicate schedule view.

#### Constraints and assumptions

- The exported file is a snapshot at download time.
- File possession is outside later token control and must be explained before
  download.
- Standards conformance and Outlook import compatibility must be measurable in
  the later specification.

#### Dependencies

- FS-015.

#### Completion outcome

A lecturer can import one complete, correctly scoped semester-revision
schedule into Outlook without exposing another lecturer's data or requiring a
calendar-provider connection.

#### Open clarification topics

- Exact event summary, description, location, and optional context fields.
- Calendar and file naming.
- Stable event UID construction and expected behavior when a later static file
  is imported again.
- Exact iCalendar time-zone metadata and standards-validation fixtures.

#### Specification status

Ready for specification.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-020: Lecturer iCalendar Export.

Product context: FS-015 gives one accountless lecturer a secure calendar/list projection of every personal teaching and exam assignment across all courses in one semester revision. The lecturer needs a simple way to transfer that complete schedule into Outlook without an account connection or live integration.
Product-level success: A lecturer can import the complete assigned semester-revision schedule into Outlook, with correct recognizable events and no disclosure of another lecturer's data.
User or business outcome: Download one Outlook-compatible static .ics file for the complete token-scoped schedule.
Primary actors: Accountless lecturer using a valid FS-015 schedule-review token.
In scope: Download action in the reused lecturer workspace; complete teaching and exam export across all assigned courses; export independent of current filters, visible period, or selection; recognizable course/session, timing, type, location, and relevant context; institution-local timezone; stable deterministic event identifiers; standards-valid iCalendar output; privacy notice before download; download only from a valid complete FS-015 projection.
Out of scope: Subscription URLs, live refresh, two-way sync, Outlook/calendar APIs, account connection, planner export, filtered export, feedback/comments, internal warnings/security data, and remote deletion of an imported file.
Main workflow: Open valid review link, inspect schedule, choose Download calendar, read the static-file notice, download the .ics, and import it manually into Outlook.
Business rules: Include every and only scoped teaching/exam session; filters never reduce export; incomplete projection produces no partial file; token ending blocks later downloads but cannot recall earlier files; export mutates no product or provider data.
Data inputs and outputs: Valid lecturer/revision token scope and complete schedule projection produce one deterministic .ics file.
External systems and integrations: Manual file exchange with Outlook as primary target; no API or account integration.
UI references: Reuse the FS-015 lecturer workspace and existing action patterns.
Dependencies and assumptions: FS-015 is revised and its projection remains authoritative. The file is a snapshot outside product control after download.
Completion outcome: Outlook can import a complete, correctly scoped lecturer schedule from the downloaded file.
Known clarification topics: Event fields, calendar/file naming, UID strategy and repeat imports, timezone metadata, and conformance fixtures.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define user scenarios, functional requirements, edge cases, privacy behavior, standards and Outlook compatibility, assumptions, and measurable success criteria without prescribing an implementation library.
```

### FS-021: Lecturer Unavailability Submissions

#### User or business outcome

A planner can collect whole-day unavailable dates from an active lecturer
before planning, approve or reject each submitted date, and make only approved
dates authoritative scheduling constraints without manual re-entry.

#### Rationale for this slice boundary

Pre-planning availability collection is separate from post-planning session
feedback and from schedule-review revision scope. It requires a distinct
lecturer-and-semester token, one-time submission, planner decision workflow,
and conversion into the existing FS-008 availability model, while remaining
small enough for one vertical Spec Kit cycle.

#### Primary actors

- Planner user.
- Accountless lecturer submitting personal unavailable dates.

#### Preconditions

- FS-008 provides planner-controlled dated lecturer unavailability and
  unavailability warnings.
- FS-015 provides proven accountless token-security patterns.
- FS-019 and the accepted Lecturer coordination decision provide the planner
  destination and reusable lecturer/workspace components.
- An active lecturer and semester exist; no schedule revision or assigned
  session is required.

#### In scope

- Planner-only issuance of a separate availability link for exactly one active
  lecturer and one semester.
- A fixed validity of 72 consecutive hours, exact displayed expiry, planner
  revocation, and replacement.
- Only one active availability link for the same lecturer and semester;
  replacement ends prior access.
- Strict capability separation from schedule-review tokens.
- Reuse of the lecturer administration/profile and availability components in
  a restricted `My unavailable dates` mode.
- Selection of one or more whole dates within the scoped semester.
- No server-persisted draft; the lecturer makes exactly one submission and the
  successful submission immediately ends link access.
- Each submitted date appears as Pending in Lecturer coordination and can be
  approved or rejected independently.
- Approved dates become existing FS-008 whole-day lecturer-unavailability
  records without planner re-entry.
- Rejected dates are discarded after the decision and do not create
  user-facing decision history.
- A simple pending count/filter and decision actions in Lecturer coordination.
- If approval overlaps an existing session, preserve the session and show the
  existing lecturer-unavailability warning.
- A fresh general one-use link when another or corrected submission is needed.

#### Out of scope

- Partial-day time intervals, recurring weekdays, date ranges, positive
  availability, saved lecturer drafts, edit/delete after submission,
  approval/rejection history, automatic schedule movement, post-planning
  session objections, combined review-and-availability tokens, authenticated
  accounts, email/push notification, and a generic Action Center.

#### Main workflow

Before planning, the planner opens Lecturer coordination, selects an active
lecturer and semester, issues the fixed 72-hour link, copies it, and sends it
manually. The lecturer opens the restricted workspace, selects whole dates
inside the semester, and submits once. The planner sees pending dates in
Lecturer coordination and approves or rejects each. Approved dates immediately
become existing planning unavailability; rejected dates disappear. If another
submission is needed, the planner issues a new link.

#### Business rules

- Only a planner can issue, inspect, revoke, replace, approve, or reject.
- One link is scoped to one lecturer, one semester, and one submission.
- The link ends at the earliest of successful submission, 72-hour expiry,
  revocation, or replacement.
- Unusable links expose no lecturer, semester, availability, or decision data.
- Every submitted date must lie within the scoped semester and duplicate dates
  must not create duplicate unavailability.
- Approval is per date and creates the same authoritative constraint as
  planner-entered FS-008 unavailability.
- Rejection creates no constraint and retains no business history.
- Approved availability never silently moves or deletes an existing session;
  any collision is visible as the established warning.
- After planning exists, lecturers use FS-015 session feedback rather than this
  pre-planning workflow to object to a scheduled date.

#### Data inputs and outputs

Inputs are active lecturer, semester, planner token lifecycle actions, selected
whole dates, and per-date planner decisions. Outputs are a one-use scoped link,
pending date decisions, approved FS-008 unavailability records, and current
pending counts. Rejected dates leave no retained business record.

#### Integrations

No external integration. The planner manually sends the link through an
external communication channel.

#### UI references

- Reuse the implemented lecturer administration/profile and
  `ResourceAvailabilityEditor` concepts in restricted mode.
- Reuse the existing Lecturer reviews destination as the broadened Lecturer
  coordination surface.
- `docs/architecture/lecturer-action-surface.md` and
  `docs/architecture/availability-link-validity.md` are accepted architectural
  context.

#### Constraints and assumptions

- Whole-day lecturer submissions are sufficient for the first release even
  though planner-entered FS-008 availability supports richer intervals.
- Component reuse must not grant public mutation access to planner-controlled
  availability operations.
- Minimal security events may be retained, but they are not user-facing
  approval/rejection history.

#### Dependencies

- FS-008, FS-015, and FS-019.

#### Completion outcome

A planner can collect and decide whole-day lecturer unavailability before
planning, and every approved date becomes a scheduling constraint without
manual re-entry or automatic schedule movement.

#### Open clarification topics

- Exact handling and feedback for a submitted date already covered by existing
  lecturer unavailability.
- Ordering and batch ergonomics for approving/rejecting several dates while
  preserving per-date decisions.
- Safe concurrency behavior when submission, expiry, revocation, replacement,
  or planner decision occurs nearly simultaneously.
- Exact retention period for minimal security events.

#### Specification status

Ready for specification.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-021: Lecturer Unavailability Submissions.

Product context: The planner already maintains dated lecturer unavailability under FS-008, but lecturers need a simple accountless way to submit whole unavailable days before planning. Post-planning objections remain FS-015 session feedback. The planner must retain authority, avoid manual re-entry, and reuse existing lecturer, availability, token-security, and Lecturer coordination components.
Product-level success: Approved lecturer dates become authoritative scheduling constraints without planner re-entry; rejected dates cause no schedule or history; lecturers gain no planner permissions.
User or business outcome: Collect one whole-day availability submission through a temporary link and let the planner approve or reject each date.
Primary actors: Planner user and one accountless lecturer.
In scope: Planner-issued link scoped to one active lecturer and one semester without requiring a revision or assignment; fixed 72-hour expiry; displayed exact expiry; revoke and replace; one active link per pair; one successful submission; separate capability from review links; restricted My unavailable dates workspace reusing lecturer/availability components; one or more whole dates inside the semester; no persisted draft; per-date Pending decisions in Lecturer coordination; individual approval/rejection; approved dates create existing FS-008 unavailability; rejected dates are discarded; pending count/filter; existing-session warning without automatic movement; fresh link for another submission.
Out of scope: Partial days, times, recurrence, date ranges, positive availability, saved drafts, edit/delete after submission, business decision history, automatic schedule movement, session objections, combined tokens, accounts, email/push notification, and a generic Action Center.
Main workflow: Planner issues and manually sends a 72-hour link; lecturer selects whole dates and submits once; planner reviews Pending dates in Lecturer coordination and approves or rejects each; approved dates become FS-008 constraints; another attempt requires a new link.
Business rules: Only planners control link and decision actions; link ends after submission, expiry, revocation, or replacement; unusable links fail safely; dates remain inside the semester; duplicates do not create duplicate constraints; rejection retains no business history; existing collisions produce warnings; later schedule objections use FS-015 feedback.
Data inputs and outputs: Lecturer, semester, token lifecycle, whole dates, and planner decisions produce the scoped link, pending date items, approved FS-008 records, and current pending counts; rejected items are discarded.
External systems and integrations: None; manual link delivery only.
UI references: Reuse lecturer administration/profile, ResourceAvailabilityEditor concepts, Lecturer coordination, and the accepted docs/architecture/lecturer-action-surface.md and docs/architecture/availability-link-validity.md decisions.
Dependencies and assumptions: FS-008, FS-015, and FS-019. Whole days are sufficient; richer planner-entered availability remains unchanged; backend permissions remain authoritative.
Completion outcome: Approved lecturer whole-day unavailability affects subsequent planning without manual re-entry, and no lecturer action directly changes a schedule.
Known clarification topics: Existing-duplicate behavior, per-date batch ergonomics, concurrency at submission/link ending/decision, and minimal security-event retention.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define independently testable scenarios, requirements, security and privacy behavior, edge cases, assumptions, and measurable success criteria without merging the two token capabilities or designing authentication.
```

### FS-022: Authenticated Lecturer Access

#### User or business outcome

A lecturer can later use one ongoing authenticated identity to reach only their
own schedule-review, calendar-export, feedback, and unavailable-date workflows
without receiving a new accountless link for each capability.

#### Rationale for this slice boundary

Authenticated lecturer collaboration is independently valuable but is not
needed to protect planner work. It depends on the accountless lecturer
workflows being complete and on FS-016 establishing the planner authentication
boundary, so it is split from FS-016 and deliberately deferred.

#### Primary actors

- Lecturer.
- System administrator or another later-confirmed lecturer-account operator.
- Planner user handling feedback and availability decisions.

#### Preconditions

- FS-015 provides lecturer schedule review and feedback semantics.
- FS-020 provides static iCalendar export semantics.
- FS-021 provides lecturer unavailable-date submission semantics.
- FS-016 provides protected planner access and an application authentication
  boundary that may inform, but does not predetermine, lecturer identity.

#### In scope

- A later-confirmed ongoing identity and account lifecycle for lecturers.
- Lecturer access limited to personally assigned courses, revisions, teaching
  sessions, exams, feedback, export, and unavailable-date workflows.
- Authenticated reuse of the established lecturer calendar/list workspace,
  feedback, static iCalendar export, and personal unavailable-date behavior.
- Lecturer-appropriate navigation and safe handling of removed assignments or
  deactivated lecturer access.
- Coexistence or migration rules for existing accountless links.

#### Out of scope

- Lecturer schedule editing, publication rights, planner account management,
  access to another lecturer's assignments, or expansion of existing lecturer
  collaboration outcomes.
- Selection of SSO, local passwords, passkeys, MFA, automated provisioning, or
  another identity mechanism before the slice is activated and clarified.

#### Main workflow

After a later identity model is confirmed, a lecturer authenticates, opens the
personal lecturer workspace, reviews assigned teaching and exam sessions,
provides feedback, downloads the complete personal calendar export, and manages
personal unavailable-date submissions within the permissions already defined by
FS-015, FS-020, and FS-021. Planners retain scheduling, availability approval,
and publication authority.

#### Business rules

- A lecturer can read and act only within their own current assignment scope.
- Authentication never grants planner mutation, publication, or account-
  administration authority.
- Assignment removal and account deactivation prevent future unrelated access
  without corrupting required historical attribution.
- Existing accountless capabilities are not removed until explicit coexistence
  or migration behavior is approved.

#### Data inputs and outputs

Inputs include later-confirmed lecturer identity, account status, lecturer
association, current assignments, feedback, export requests, and availability
submissions. Outputs are authenticated lecturer sessions, scoped personal
views/actions, feedback, static exports, and planner-controlled availability
decisions.

#### Integrations

No identity provider is selected. External identity, provisioning, or delivery
integration remains an unresolved later decision.

#### UI references

Reuse the established accountless lecturer workspace and lecturer navigation
patterns. No separate authenticated-lecturer mockup is confirmed.

#### Constraints and assumptions

- This slice must not reopen the business rules of FS-015, FS-020, or FS-021.
- Its identity model and token/account coexistence boundary require a later
  requirements update before specification.

#### Dependencies

- FS-015, FS-016, FS-020, and FS-021.

#### Completion outcome

Once activated, a lecturer can use an ongoing authenticated identity for only
their established collaboration workflows while planner authority and other
lecturers' data remain protected.

#### Open clarification topics

- Identity provider or local credential model, provisioning, recovery, and MFA.
- Who may create or deactivate lecturer access.
- Accountless-token coexistence, migration, and retirement behavior.
- Whether authenticated availability becomes an ongoing workflow or retains
  the one-submission boundary.

#### Specification status

Deferred — identity and coexistence decisions are intentionally unresolved.

#### Ready-to-copy Spec Kit prompt

```text
Use $speckit-specify to create the specification for FS-022: Authenticated
Lecturer Access only after its identity, provisioning, recovery, and
accountless-token coexistence decisions have been confirmed in
docs/planning/Feature_slices.md.

Product context: Accountless lecturer schedule review, feedback, calendar
export, and unavailable-date submission are defined by FS-015, FS-020, and
FS-021. FS-016 separately protects planner work. This deferred slice may later
let lecturers reuse only their established personal workflows through an
ongoing authenticated identity.
Outcome: Give a lecturer ongoing authenticated access to only personally
assigned collaboration data and actions without granting planner authority.
Actors: Lecturer, planner user, and a later-confirmed lecturer-account operator.
In scope: Confirmed lecturer identity/account lifecycle; access limited to
personal assignments; reuse of schedule review, feedback, static export, and
unavailable-date workflows; lecturer navigation; deactivation and assignment-
removal handling; approved token/account coexistence or migration.
Out of scope: Schedule editing, publication, planner account management, other
lecturers' data, new collaboration outcomes, and any unconfirmed identity or
provisioning mechanism.
Rules: Authorization applies to every read and action; lecturers retain only the
permissions established by FS-015, FS-020, and FS-021; deactivation and removed
assignments prevent future unrelated access; accountless links remain until an
explicit migration decision is approved.
Dependencies: FS-015, FS-016, FS-020, and FS-021 plus confirmed identity and
coexistence decisions.
Completion: An authenticated lecturer can safely reuse the established personal
collaboration workflows without receiving planner authority or seeing another
lecturer's data.
Clarification topics: Identity method, provisioning, recovery, MFA, account
operator, token coexistence/migration, and authenticated availability behavior.

Keep the specification strictly limited to this slice and consistent with
docs/planning/Feature_slices.md. Do not start specification while the listed
product-level identity and coexistence decisions remain unresolved, and do not
introduce implementation details or expand lecturer authority.
```

### I-001: Containerized Application Distribution

#### User or business outcome

A deployment operator can pull and run one versioned application image through
one port while preserving planning data outside the replaceable container.

#### Scope and relationship to earlier slices

- Package the existing frontend and backend as one non-root application image.
- Provide persistent SQLite storage, health checks, versioned release tags,
  multi-architecture publication, backup guidance, and simple deployment files.
- Preserve all existing scheduling behavior; this improvement changes
  distribution rather than product workflows.

#### Dependencies

- The implemented application baseline.

#### Specification status

Implemented. Detailed artifacts are in
`specs/I-001-containerized-distribution/`.

### I-002: Consistent Labels, European Dates, and Actionable Messages

#### User or business outcome

Planner users and lecturers can understand the same terminology, calendar dates,
warnings, and failures consistently throughout the application and can tell what
to do next when the system reports a problem.

#### Rationale for this slice boundary

Controlled labels, European date presentation, and actionable messages are
separate presentation concerns but deliver one cross-workflow usability outcome:
the application communicates planning information clearly and consistently.
They share the same application-wide inventory and regression boundary and are
small enough to specify together without changing scheduling behavior.

#### Primary actors

- Planner user.
- Lecturer using an accountless review or availability surface.

#### Preconditions

- FS-019 provides the current planner navigation, Schedule workspace, session
  details, and correction surfaces that form the principal UI baseline.
- Existing domain validations and machine-readable API error contracts remain
  available as the source conditions for user-facing messages.

#### In scope

- One complete shipped German default catalog for selected reusable domain and
  workflow terms, plus one optional customer override file supplied during
  deployment or startup.
- Stable context-specific identifiers and complete values for singular, plural,
  navigation, heading, field, and table contexts, without automatic German
  inflection or token substitution into ordinary copy.
- A complete inventory and migration of the selected configurable terminology
  across current planner and accountless lecturer surfaces.
- Zero-padded `DD.MM.YYYY` presentation for every human-visible calendar date,
  including lists, calendars, detail panes, summaries, dialogs, notices,
  generated user-facing text, and date entry presentation.
- Consistent European formatting of date ranges without changing their meaning.
- Contextual messages for validation warnings, field errors, failed operations,
  stale data, connectivity failures, and unexpected service failures.
- Each known message identifying the failed or affected action, record or field;
  explaining the cause, violated rule, or relevant values when known; and
  stating a concrete recovery or next action.
- Warning language that clearly distinguishes non-blocking conditions from
  failures and states whether the current record remains saved or usable.
- Separate presentation of multiple actionable problems rather than an
  undifferentiated combined sentence.
- Safe fallback messages for genuinely unknown failures that name the attempted
  action, preserve user-entered work where possible, and offer retry or refresh
  guidance without exposing sensitive or internal diagnostic data.

#### Out of scope

- Non-German application languages, runtime locale switching, translation
  workflows, automatic pluralization or inflection, remote translation services,
  and runtime terminology administration.
- Customer configuration of ordinary German sentences, instructions, notices,
  confirmations, or complete warning and error message templates.
- Renaming stored academic records or values entered by users.
- Changing domain rules, warning severity, save/block behavior, API semantics,
  database date representation, or ordering/comparison logic.
- Translating technical interchange formats such as API payloads, iCalendar
  content, URLs, logs, or source-level test fixtures into display format.
- A generic notification center, support-ticket workflow, or exposure of stack
  traces, internal exception text, bearer values, or secrets.

#### Main workflow

A user opens any planner or accountless lecturer screen and sees German
application copy plus selected terminology resolved from the shipped defaults
and optional customer overrides. All calendar dates are presented as
`DD.MM.YYYY`. When a known warning or failure occurs, the German message names
the affected action or record, includes the relevant rule or values,
distinguishes whether the condition blocks the action, and provides a direct
safe action or points precisely to the existing control.

For the motivating Courses overview case, an outside-recommended-window warning
must identify the course or exam, show the scheduled date and actual recommended
start and end dates in European format, state that the condition is non-blocking,
and explain how the planner can edit the date or retain the intentional override.

#### Business rules

- `DD.MM.YYYY` means a two-digit day, two-digit month, and four-digit year, for
  example `11.09.2026`.
- Date formatting must not shift the calendar day because of timezone
  conversion. Existing institution-local time behavior remains authoritative.
- Machine-readable dates remain machine-readable at storage and integration
  boundaries; conversion occurs only where a date becomes user-facing.
- A raw internal error code may support diagnostics but cannot be the only or
  primary explanation shown to the user.
- Known messages follow the sequence: what happened, what item or field is
  affected, why it happened or which values/rule apply, and what the user can do
  next.
- Messages must not promise recovery actions the current screen does not offer.
- When an exact cause is unavailable, the message must not invent one; it names
  the attempted action and offers the safest available retry, refresh, or
  preservation guidance.
- Customer terminology overrides take effect on the installation's next startup
  without an application rebuild and do not alter user data.
- Omitted overrides use shipped German defaults. Empty, unreadable, unknown, or
  unresolved overrides must be detected before an affected interface is served
  and must never render as an empty label or raw catalog key.
- Date fields always display and accept `DD.MM.YYYY`; an accessible calendar
  picker may supplement the field but may not replace it with a
  browser-dependent visible format.

#### Data inputs and outputs

Inputs are shipped German terminology defaults, optional customer override
values, machine-readable calendar dates, domain validation details, affected
record and field context, attempted actions, and recoverability information.
Outputs are consistent customer-specific German terminology,
European-formatted display dates, and safe actionable German messages. No new
business record or external data exchange is introduced.

#### Integrations

None. Existing APIs and standards-based exports retain their established date
and error contracts unless a later specification explicitly changes them.

#### UI references

- The existing React/Vite planner and accountless lecturer surfaces are the
  coverage baseline.
- The user-provided Courses overview screenshot from 2026-08-10 demonstrates
  the two principal defects: ISO dates such as `2026-09-11` and the context-poor
  `KI Grundlagen · OUTSIDE RECOMMENDED WINDOW` warning.
- Existing visual hierarchy and interaction patterns remain unchanged except
  where additional message detail requires readable wrapping or grouping.

#### Constraints and assumptions

- The application language is German. The deliberately small terminology
  catalog is not a complete internationalization system.
- Customer configuration is an optional deployment/startup override file over
  shipped German defaults, not an in-application editor or runtime switch.
- Each grammatical or UI context has its own complete catalog value; no
  inflection engine or sentence token substitution is required.
- The European standard applies to calendar dates, not to changing the existing
  24-hour clock, duration, number, or timezone rules.
- Date controls always display and accept `DD.MM.YYYY` while preserving valid
  machine values submitted to existing APIs. An accessible calendar picker may
  supplement this field behavior.
- The work covers all current user-facing surfaces, including less frequent
  dialogs and failure states, not only the Courses overview screenshot.

#### Dependencies

- FS-019.
- Existing domain error codes and validation detail from the implemented slices.

#### Completion outcome

A representative user can move across planner and accountless lecturer
workflows without encountering an ISO-formatted human date or a migrated static
configurable term outside the effective German catalog, and can use every tested
known warning or failure to identify the affected context and the next available
action. The
outside-recommended-window case explicitly shows the scheduled date,
recommended range, non-blocking status, and correction or retention options.

#### Open clarification topics

None. Implementation-level file structure and key naming remain planning
decisions within the confirmed deployment override and context-specific value
rules.

#### Specification status

Partially implemented — implementation, validation, and acceptance follow-ups
remain open.
The initiative's detailed Spec Kit artifacts use the exact directory
`specs/I-002/`.

#### Original Spec Kit prompt

```text
Use $speckit-specify to create the specification for the following development
slice. Store all generated specification artifacts in the exact initiative
directory specs/I-002/; do not create a differently named feature directory.

Slice ID: I-002
Slice name: Consistent Labels, European Dates, and Actionable Messages

Product context:
The Resource Planner's current planner and accountless lecturer interfaces use
static wording distributed across components, frequently expose ISO calendar
dates, and sometimes show only generic categories or failures. The user-provided
Courses overview screenshot demonstrates `2026-09-11` and `KI Grundlagen ·
OUTSIDE RECOMMENDED WINDOW` without the recommended range or next action.

Product-level success:
Users see consistent terminology, every human-visible calendar date follows the
European `DD.MM.YYYY` convention, and known warnings or failures explain the
affected context, cause or rule, blocking status, and next available action.

User or business outcome:
Planner users and lecturers can understand dates, warnings, failures, and
interface terminology consistently throughout the application and know what to
do next when a problem is reported.

Primary actors:
Planner user; lecturer using an accountless review or availability surface.

In scope:
German-only application copy; one shipped German default catalog for selected
reusable domain/workflow terminology; one optional customer override file
supplied during deployment or startup; complete context-specific values without
automatic inflection; planner and accountless lecturer terminology inventory;
`DD.MM.YYYY` display and entry for all human-visible calendar dates and ranges;
precise contextual German messages with direct safe recovery actions or precise
directions to existing controls; separate problem rendering; safe unknown-error
fallbacks; and regression coverage. The outside-recommended-window message must
show the affected course or exam, scheduled date, recommended start/end dates,
non-blocking status, and edit-or-retain guidance.

Out of scope:
Non-German application languages, runtime locale switching, translation or
terminology administration, automatic inflection, configuration of ordinary
German sentences or complete message templates, renaming user-entered records,
changes to business rules or severity, API and database date representation,
standards-based export formatting, notification centers, support workflows, or
disclosure of internal diagnostics and secrets.

Main workflow:
The user opens any current application surface and sees German copy,
customer-configured terminology, and European dates. When a known problem
occurs, the German message states what happened, the affected item or field, the
reason or relevant values, whether the action is blocked, and a direct safe
action or precise direction to the existing correction, retry, refresh, or
intentional-retain control.

Business rules:
`DD.MM.YYYY` is zero-padded and is always displayed and accepted by date fields;
formatting must not shift calendar days; machine boundaries retain required
formats; raw codes are never the primary explanation; messages do not invent
causes or unavailable recovery actions; omitted overrides use German defaults;
invalid overrides are caught before serving the interface; terminology changes
apply on next startup without rebuilding or changing user data.

Data inputs and outputs:
German terminology defaults, optional customer overrides, machine dates,
validation details, affected record/field context, attempted actions, and
recovery information become consistent German terminology, display dates, and
safe actionable German messages. No new business records are introduced.

External systems and integrations:
None. Existing APIs, persistence, and standards-based exports retain their
contracts.

UI references:
Existing React/Vite planner and accountless lecturer surfaces are the full
coverage baseline. The user-provided Courses overview screenshot from 2026-08-10
is the motivating example.

Dependencies and assumptions:
Depends on FS-019 and existing domain validation details. German is the only
application language. The terminology catalog and optional deployment override
are deliberately small. Existing 24-hour time, duration, and timezone rules
remain unchanged.

Completion outcome:
Current user-facing surfaces contain no ISO-formatted human calendar dates or
selected configurable terms outside the effective German catalog, and tested
known warnings/failures provide actionable German context. The motivating
warning includes its scheduled date, recommended range, non-blocking status, and
correction/retention guidance.

Known clarification topics:
None. File structure and key naming remain planning decisions within the
confirmed deployment override and context-specific value rules.

Keep the specification strictly limited to this slice and consistent with
docs/planning/Feature_slices.md. Define independently testable scenarios,
functional requirements, accessibility behavior, edge cases, assumptions, and
measurable success criteria without implementation details or scope expansion.
```

### I-003: Unified Teaching Schedule Generation

#### User or business outcome

A planner generates one or several selected courses through one conflict-aware
teaching workflow that protects unselected teaching sessions and active exams.

#### Scope and relationship to earlier slices

- Use one generation workflow and one placement decision process for one to
  twenty selected courses.
- Use active constraints, holidays, resources, unselected teaching sessions,
  and active exams as authoritative generation inputs.
- Retire the legacy single-course and independent batch generation operations.
- Provide precise lecturer, room, and cohort warnings and an aligned responsive
  teaching list.
- Supersede the supported generation behavior from FS-001, FS-006, and FS-010
  without renumbering or removing those historical baseline slices.

#### Dependencies

- FS-010 through FS-013 and FS-019.

#### Specification status

Implemented with validation and acceptance follow-ups open. Detailed artifacts
are in `specs/I-003-unified-schedule-generation/`.

### I-004: Planner-Controlled Schedule Regeneration Decision

#### User or business outcome

A planner can compare the complete current selection with a valid jointly
regenerated alternative and make the final atomic decision to accept the new
plan or retain everything currently saved.

#### Rationale for this slice boundary

The implemented optimizer's automatic non-worsening rule treats scheduled-unit
coverage as the dominant replacement criterion. That can preserve a complete
but constraint-violating current schedule when a valid partial alternative is
operationally preferable. Candidate generation and planner replacement
authority form one independently valuable decision workflow without changing
manual editing, publication, or the underlying hard-constraint definitions.

#### Primary actors

- Planner user.

#### Preconditions

- I-003 provides unified conflict-aware teaching generation, holiday avoidance,
  exam occupancy, and understandable partial outcomes.
- FS-013 provides the active Working revision and stale-write protection.
- FS-019 provides the Schedule workspace and generation controls.
- I-002 provides actionable German message conventions.

#### In scope

- Use the same unified conflict-aware generator for a selection of one or
  several courses.
- Treat all current active course constraints, study-type time windows, course
  date boundaries, semester boundaries, holidays, resource eligibility and
  availability, room capacity, unselected teaching sessions, and active exams
  as authoritative hard generation inputs.
- Never offer a generated alternative containing a hard-constraint violation,
  including a lecturer, room, or cohort overlap.
- When at least one selected course has existing teaching sessions, keep the
  generated alternative uncommitted and show one post-generation comparison
  before replacing anything.
- Explain why a planner decision is required and compare current versus
  generated results for the complete selection, including per-course scheduled
  and required teaching units, complete or partial status, remaining units and
  reasons, and current hard-constraint warnings resolved by the alternative.
- Show the same comparison even when the generated result appears objectively
  better, so the replacement rule and planner control remain consistent.
- Offer exactly the decision actions `Neu erzeugten Stundenplan übernehmen`
  and `Abbrechen`. No written justification or separate keep-current button is
  required.
- Make `Abbrechen`, dialog dismissal, or leaving the unresolved comparison
  discard the complete generated alternative and leave the complete current
  selection unchanged.
- Make acceptance replace existing schedules and create schedules for
  previously unplanned courses in the selected set as one atomic operation.
- Permit explicit acceptance of a valid partial alternative with fewer
  scheduled units than the current schedule when the planner judges resolved
  violations more important than completeness.
- Revalidate revision and relevant planning state before acceptance; stale
  state prevents replacement and directs the planner to regenerate.
- When none of the selected courses has an existing teaching schedule, retain
  the established direct-save generation behavior because there is no current
  alternative to compare.
- When no valid generated alternative can be produced, preserve the current
  selection and report the blocking reasons without presenting a misleading
  replacement choice.

#### Out of scope

- Per-course accept/reject choices inside one jointly optimized operation.
- Combining current sessions from rejected courses with generated sessions
  from accepted courses.
- Offering or accepting a newly generated candidate with hard conflicts.
- Requiring a comment, reason, approval signature, or decision-history entry.
- Automatically repairing, deleting, or moving the retained current schedule
  after cancellation.
- Changing manual session-editing permissions, lifecycle transitions, or
  publication authority.

#### Main workflow

The planner selects one or several courses and starts generation. The system
optimizes the complete selection against active constraints and fixed semester
occupancy without changing saved sessions. If existing selected sessions are
present and a valid alternative is available, a simple comparison explains the
coverage and constraint trade-off. The planner chooses `Neu erzeugten
Stundenplan übernehmen` to atomically replace the complete selected result, or
chooses `Abbrechen` or dismisses the dialog to discard the candidate and keep
the complete current result.

#### Business rules

- The planner, not an automatic coverage or preference tie-break, makes every
  replacement decision after a regenerated alternative exists.
- One multi-course solve produces one indivisible acceptance decision.
- Acceptance is all-or-nothing across the selected course set.
- Cancellation is non-mutating and implies retention of the current schedules.
- Generated validity is not negotiable: planner choice can retain an older
  warned schedule but cannot authorize a newly invalid candidate.
- Completeness and validity are separate comparison dimensions. Fewer scheduled
  units do not disqualify a valid candidate from explicit planner acceptance.
- The comparison must not label either result simply as better when the result
  has competing advantages; it presents concrete counts, warnings, and effects.
- Existing selected manual sessions are part of the current result and are
  replaced only if the planner accepts the complete generated alternative; the
  comparison must state that consequence.
- A stale candidate never replaces newer schedule or constraint state.

#### Data inputs and outputs

Inputs are the selected courses, active Working revision, current selected and
unselected teaching sessions, active exams, holidays, current course and
study-type constraints, resources and availability, and the planner's binary
decision. Outputs are either one atomically persisted generated selection or
the unchanged current selection, plus an understandable generation/comparison
summary. A cancelled candidate creates no schedule or decision-history record.

#### Integrations

None.

#### UI references

- Reuse the implemented `Stundenpläne erzeugen` selection and generation
  surface in `CourseSchedulePage`.
- Replace the pre-generation replacement implication as the authoritative
  decision point with one simple post-generation comparison dialog.
- Reuse the precise conflict and actionable-message conventions established by
  I-002; do not introduce another schedule-generation workflow.

#### Constraints and assumptions

- Consistent operation-wide acceptance is deliberately preferred over
  per-course decisions because independently mixing a joint optimizer's output
  can invalidate its conflict guarantees.
- Showing the dialog for every regeneration with existing selected sessions is
  deliberately preferred over conditional dialog rules.
- The planner needs decision evidence, not a mandatory textual justification.
- The generated alternative remains provisional until acceptance and must not
  become visible as the saved Working revision in other views.

#### Dependencies

- I-003, FS-013, FS-019, and I-002.

#### Completion outcome

A planner can intentionally retain a complete but warned current plan or accept
a valid partial regenerated plan after seeing the concrete trade-off, and a
multi-course decision can never leave a partially applied or newly conflicting
schedule.

#### Open clarification topics

None. Candidate transport and temporary representation are implementation
decisions as long as provisional data is not persisted as the current Working
revision before acceptance.

#### Specification status

Implemented — manual acceptance evidence pending.

#### Original Spec Kit prompt

```text
Use $speckit-specify to create the specification for I-004: Planner-Controlled Schedule Regeneration Decision.

Product context: The conflict-aware optimizer currently applies an automatic non-worsening replacement rule. A complete current schedule with hard-constraint warnings can therefore be retained instead of a valid partial alternative. The planner must see the trade-off and make the final decision without weakening generated-schedule validity or multi-course conflict guarantees.
Product-level success: Whenever regeneration proposes replacing existing selected teaching sessions, the planner compares the complete current selection with one valid jointly generated alternative and atomically accepts the new result or leaves all current work unchanged.
User or business outcome: Give the planner final authority over whether a valid regenerated alternative replaces existing selected schedules.
Primary actors: Planner user.
In scope: The unified one-course/multi-course conflict-aware generator; every current active course, study-type, semester, holiday, resource, capacity, availability, fixed unselected teaching-session, and active-exam constraint; hard-valid generated candidates only; provisional generation when at least one selected course has existing sessions; one post-generation operation-wide and per-course comparison of scheduled/required units, complete/partial status, remaining reasons, and resolved current violations; the same dialog for every such regeneration; exactly `Neu erzeugten Stundenplan übernehmen` and `Abbrechen`; dismissal as cancellation; atomic acceptance across existing and previously unplanned selected courses; explicit acceptance of a valid fewer-unit result; stale-state rejection; direct save when no selected course has an existing schedule; preservation plus reasons when no valid candidate exists.
Out of scope: Per-course choices within one solve; mixing accepted generated and rejected current course results; generated hard conflicts; mandatory comments or decision history; automatic repair after cancellation; manual-editing, lifecycle, or publication changes.
Main workflow: Select courses and generate without mutating saved sessions. If current selected sessions and a valid candidate exist, compare both complete outcomes. Accept the generated selection atomically or cancel/dismiss to discard it and retain everything current.
Business rules: The planner makes every replacement decision; a joint solve has one indivisible decision; cancellation never mutates; generated candidates always satisfy active hard constraints; an older warned plan may be retained; a valid partial candidate remains selectable even with fewer units; comparisons present facts rather than declaring a winner; accepting replaces selected manual sessions too; stale candidates cannot commit.
Data inputs and outputs: Selected courses, Working revision, current semester teaching and exam occupancy, holidays, active constraints, resources, availability, and the binary planner choice produce either one atomically saved generated selection or no schedule change, with an actionable comparison/result summary.
External systems and integrations: None.
UI references: Reuse `Stundenpläne erzeugen` in CourseSchedulePage and I-002 actionable German message patterns. The simple post-generation comparison is the authoritative replacement decision; do not build another generator.
Dependencies and assumptions: I-003, FS-013, FS-019, and I-002. Operation-wide acceptance and an always-shown comparison for regeneration with existing selected sessions are confirmed. No written justification is required.
Completion outcome: A planner can choose between a complete warned current plan and a valid partial alternative without any partial multi-course application, silent replacement, or generated hard conflict.
Known clarification topics: None. Candidate transport and temporary representation remain implementation decisions, provided provisional data is not exposed as the saved Working revision.

Keep the specification strictly limited to this slice and consistent with docs/planning/Feature_slices.md. Define independently testable scenarios, functional requirements, edge cases, atomicity and stale-state behavior, accessibility expectations, and measurable success criteria without choosing an algorithm or persistence mechanism.
```

## Deferred scope

- **Automated email delivery**: FS-015 and FS-021 deliberately use
  planner-copied links; an email provider is not yet selected or required.
- **Institutional SSO and automated provisioning**: Deferred until authenticated collaboration is validated and an identity provider is known.
- **Authenticated lecturer access (FS-022)**: Ongoing lecturer identity remains
  desirable but is deferred until FS-020 and FS-021 are complete and identity,
  provisioning, recovery, and accountless-token coexistence are confirmed.
- **Multi-lecturer token scope**: Each accountless link intentionally represents
  one lecturer even though FS-015 includes all of that lecturer's assigned
  courses. Combined multi-lecturer access may be reconsidered only through a
  later scope update.
- **Live calendar subscription or synchronization**: FS-020 is a static file
  export. Calendar feeds, provider APIs, refresh, and two-way synchronization
  remain later possibilities without a confirmed need.
- **Richer lecturer-submitted availability**: Partial-day times, recurring
  weekdays, and date ranges remain excluded from FS-021; planners retain the
  richer FS-008 administration workflow.
- **Generic Action Center**: Lecturer-originated work is consolidated in
  Lecturer coordination. A cross-product, role-aware queue is deferred until
  authenticated roles demonstrate a need beyond existing calendar operational
  summaries.
- **Full internationalization and runtime terminology administration**: I-002
  keeps the application German and allows only deployment-time overrides of
  selected terminology. Additional languages, locale selection, translation
  workflows, and administrator-edited wording remain deferred until there is a
  confirmed user or operational need.
- **Multiple campus or regional holiday calendars**: The planner-only MVP uses one institution-wide calendar.
- **Provider-specific integration adapters**: Deferred until a provider-neutral contract and actual provider are known.
- **Automatic lecturer-driven schedule changes**: Lecturers remain advisory reviewers; planner users alone change schedules.
- **Mandatory approval gates**: Lecturer acceptance is not required for publication.
- **Automated destructive optimization of existing sessions**: Existing and manually controlled sessions are never silently deleted or moved.
- **Student registration, grading, and downstream operational room booking**: These remain outside the confirmed Resource Planner boundary.

## Product-level open assumptions

- The historical planner-only MVP was implemented without authentication;
  FS-016 now owns the selected transition to required named planner access.
- Current lecturer collaboration remains accountless and capability-scoped;
  FS-022 cannot advance from Deferred until its identity and coexistence model
  is confirmed.
- A downloaded FS-020 calendar file remains outside product control and may
  continue to expose the exported schedule after link expiry or revocation.
- Planner-entered or planner-approved availability remains authoritative until
  FS-017 defines ownership for synchronized fields.
- Optimization fairness and deterministic candidate tie-breaking can be
  clarified within FS-010 without changing its global-maximization boundary;
  I-004 owns the later planner-controlled persistence decision.

## Change history

| Date | Change type | Affected slices | Summary | Rationale |
| ---- | ----------- | --------------- | ------- | --------- |
| 2026-08-14 | Split slice, new deferred slice, reordered slice, product-scope and authentication-boundary change | FS-016, FS-022, FS-020, FS-021, FS-017 | Narrowed FS-016 to self-contained named planner authentication with exactly one account administrator, one active session per account, one-time startup bootstrap and recovery, manually delivered setup/reset access, and minimal account lifecycle visibility; moved authenticated lecturer access to new deferred FS-022; made FS-016 the recommended next slice. | Protect powerful planner work without depending on VPN, SSO, or email while keeping the first implementation simple and preserving existing accountless lecturer capabilities. |
| 2026-08-14 | Identifier and status reconciliation | I-001 through I-004, FS-001, FS-006, FS-010 | Added the missing I-001 and I-003 map entries, corrected the former FS-022 and FS-023 labels to I-002 and I-004, aligned direct dependencies, and reconciled statuses with remaining validation work. | Make the slice map mirror the improvement specification directories while retaining earlier FS slices as historical baselines. |
| 2026-08-12 | New improvement and product-level scheduling decision change | I-004, FS-010 | Added a post-generation comparison that lets the planner atomically accept one valid joint regenerated result or cancel to retain the complete current selection; documented that this supersedes FS-010's automatic non-worsening persistence rule without weakening hard-constraint validation. | A complete current schedule can contain active-window or other hard-constraint warnings while a valid partial alternative is operationally preferable; completeness alone must not silently decide the replacement, and per-course acceptance would break joint conflict guarantees. |
| 2026-08-10 | New, specified, and clarified improvement; product-level usability scope change; reordered slice | I-002, FS-015, FS-020, FS-021, FS-016, FS-017 | Added and clarified German application wording with deployment-time customer terminology overrides, European date display and entry, and actionable German messages as the selected initiative, with detailed artifacts in `specs/I-002/`; shifted the remaining not-yet-specified slices later without changing their IDs or dependencies. | Resolve demonstrated cross-workflow comprehension problems before extending more workflows, while keeping runtime language switching, full translation management, machine contracts, and business rules outside the slice. |
| 2026-07-31 | Product-level scope change, updated slice, new slices, scope reconciliation, reordered later slice | FS-015, FS-016, FS-019, FS-020, FS-021 | Added the missing implemented FS-019 workspace with its pending manual acceptance status; broadened FS-015 into the shared lecturer calendar/list and Lecturer coordination experience; added static iCalendar export and whole-day lecturer unavailability submissions; made FS-016 reuse the completed accountless workflows. | Complete the accountless lecturer collaboration loop through reused components before introducing authentication, while preserving planner authority and separating review, export, and pre-planning availability into coherent vertical outcomes. |
| 2026-07-31 | Status correction | FS-009–FS-012, FS-014, FS-018 | Aligned detailed-section statuses with the existing implemented statuses in the slice map. | Remove pre-existing internal contradictions without changing the confirmed slice outcomes. |
| 2026-07-23 | Status update | FS-013, FS-014 | Marked FS-013 implemented and advanced FS-014 to Ready for specification as the recommended next slice. | Reflect completion of the versioned publication lifecycle and open the calendar workspace for specification. |
| 2026-07-14 | Ground-truth creation | FS-001–FS-017 | Reconstructed implemented FS-001–FS-006 and replaced the old roadmap with a validated planner-MVP and later-release slice map. | Preserve implemented behavior while defining conflict-aware planning, manual administration, exams, publication, calendar operations, lecturer review, identity, and future integration as coherent vertical slices. |
| 2026-07-16 | New slice, reordered slice, updated slice | FS-007, FS-014, FS-018 | Added unified application navigation as the recommended next slice, recorded the approved UX ground truth, and made the later calendar workspace reuse that navigation. | Separate the confirmed cross-workflow navigation outcome from implemented academic administration and remove the navigation ambiguity from FS-014. |
| 2026-07-16 | Reordered slice, status correction | FS-008, FS-018 | Recorded FS-008 as implemented, placed FS-018 after the completed FS-008 baseline, and added FS-008 as an FS-018 dependency. | Reflect completed resource administration work and the Lecturer and Room destinations that unified navigation must preserve. |
