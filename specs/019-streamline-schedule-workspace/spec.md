# Feature Specification: FS-019 Streamlined Schedule Workspace

**Working Branch**: `master`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Improve Schedule usability by moving schedule versions and exam generation out of the vertically stacked calendar page into dedicated destinations under Schedule, opening teaching and exam details and editing in a right-side pane without forcing List view, and allowing the large application navigation and contextual planning inputs to be collapsed independently."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-27

- Q: Where should planners change semester, revision, and course context after Schedule is divided into Calendar, Versions, and Exams? → A: All destinations use a compact shared context header; Calendar additionally provides the collapsible full Planning inputs pane.
- Q: How should the session pane affect the Calendar layout? → A: Dock beside Calendar when space permits, use a right overlay at constrained widths, and use a temporary full-screen panel on narrow screens.
- Q: Which session types should use the new contextual pane for editing? → A: Teaching and exam sessions both use the pane for detail and editing.
- Q: When a clean session pane is open and the planner visits Versions or Exams, what should happen when they return to Calendar? → A: Restore the selected session and reopen its pane when the session and revision are still available.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect and Edit Without Leaving the Calendar (Priority: P1)

A planner selects a teaching or exam session in the calendar, reviews its
details in a right-side contextual pane, and edits an editable session in that
same pane while the calendar remains in its current mode and context.

**Why this priority**: Session correction is a frequent planning task. Forcing
the planner into List mode breaks spatial orientation and makes a local change
feel like navigation to a different workflow.

**Independent Test**: Open an editable working revision in Week mode, select a
teaching session, enter edit mode in the contextual pane, change and save a
valid value, and verify that Week mode, the visible period, filters, revision,
and selected session context remain intact while the calendar reflects the
saved change.

**Acceptance Scenarios**:

1. **Given** a teaching session is visible in Week, Day, or Month mode, **When** the planner selects it, **Then** a right-side pane opens with the session detail required by FS-014 and the calendar remains in the same mode, period, revision, and filter context.
2. **Given** an editable teaching session is open in the pane, **When** the planner chooses Edit session, **Then** the pane presents the established editable values and Save and Cancel actions without opening or switching to List mode.
3. **Given** the planner enters valid changes in the pane, **When** Save succeeds, **Then** the saved calendar item and affected summaries refresh in place, the pane returns to current detail, and no unrelated calendar context is reset.
4. **Given** the planner changes editable values, **When** Cancel is chosen, **Then** saved schedule data remains unchanged and the pane returns to the current saved detail.
5. **Given** the pane contains unsaved changes, **When** the planner attempts to close it, select another session, or leave Calendar, **Then** the planner can keep editing or explicitly discard the unsaved changes before the context changes.
6. **Given** the current Published revision is selected, **When** the planner opens a teaching or exam session, **Then** the pane provides complete read-only detail and explains why editing is unavailable.
7. **Given** the planner opens an exam session, **When** its detail or established correction action is used, **Then** all exam detail and editing remain in the same pane rather than opening a separate editor, while preserving every exam validity, recommendation, capacity, lifecycle, confirmation, and stale-state rule established by FS-012 through FS-014.
8. **Given** the available width changes while a clean or edited session is open, **When** the pane changes among docked, right-overlay, and narrow full-screen presentations, **Then** the selected session, entered values, validation feedback, and unsaved-change state are preserved.

---

### User Story 2 - Navigate Focused Schedule Areas (Priority: P1)

A planner expands Schedule in the primary navigation and moves directly among
Calendar, Versions, and Exams without scrolling through unrelated work on one
long page.

**Why this priority**: Calendar planning, lifecycle governance, and exam
preparation are distinct tasks. A clear Schedule hierarchy reduces page length
and makes each workflow easier to find.

**Independent Test**: Starting from each Schedule child destination, use the
primary navigation to open the other two destinations and verify that each
shows only its intended workspace while retaining the applicable selected
semester and revision context.

**Acceptance Scenarios**:

1. **Given** the planner opens Schedule without a child destination already selected, **When** Schedule loads, **Then** Calendar is the current child destination.
2. **Given** the primary navigation is available, **When** the planner expands Schedule, **Then** Calendar, Versions, and Exams appear as its ordered child destinations and exactly one current destination is identified.
3. **Given** Calendar is current, **When** the planner opens Versions or Exams, **Then** the corresponding focused workspace replaces Calendar in the main content area rather than appearing beneath it.
4. **Given** the planner leaves Calendar with a clean session pane open, **When** they return during the same application use and the prior semester, revision, and session remain available, **Then** the prior calendar mode, visible period, filters, selected session, and open pane are restored.
5. **Given** the planner moves among Calendar, Versions, and Exams, **When** navigation completes, **Then** a compact shared context header identifies and permits changes to the semester and any revision or course context meaningful to the current destination, context changes remain consistent across Schedule children, and no schedule or academic data changes solely because of navigation.
6. **Given** Academic Data is present in primary navigation, **When** Schedule gains child destinations, **Then** the established Academic Data hierarchy and destinations remain reachable and unmodified.

---

### User Story 3 - Reclaim Workspace Width (Priority: P2)

A planner can unpin the persistent application navigation and independently
hide or show contextual Planning inputs so the calendar and its contextual pane
have enough working space.

**Why this priority**: The current persistent navigation and Planning inputs
consume a large portion of the page before a session detail pane is opened.
Independent controls let planners choose the context they need without losing
access to either area.

**Independent Test**: At a supported wide viewport, unpin and reopen the primary
navigation, hide and restore Planning inputs, open a session pane, and verify
that each control changes only its own surface while the current Schedule
destination and planning context remain unchanged.

**Acceptance Scenarios**:

1. **Given** the wide persistent navigation is pinned, **When** the planner chooses Unpin navigation, **Then** the expanded persistent panel is removed from the main layout, main content gains usable width, and a compact labeled control remains available to reopen it.
2. **Given** the navigation is unpinned, **When** the planner reopens it and chooses Pin navigation, **Then** the persistent navigation returns without changing the current destination or planning context.
3. **Given** the planner changes the pinned state, **When** the application is revisited on the same device, **Then** the most recently chosen pinned state is restored where that presentation is supported.
4. **Given** the full Planning inputs pane is visible in Calendar, **When** the planner hides it, **Then** only that full contextual inputs area is removed from the working layout, the compact shared context header remains available, and a clearly labeled control remains available to restore the full pane.
5. **Given** either the primary navigation or Planning inputs changes visibility, **When** the other surface is inspected, **Then** its visibility state is unchanged.
6. **Given** the viewport uses the established narrow navigation presentation, **When** the planner opens or closes navigation, **Then** it behaves as a temporary panel and does not expose an inapplicable pin control.

---

### User Story 4 - Manage Versions in a Dedicated Workspace (Priority: P2)

A planner opens Versions for the selected semester and manages the active
working revision, current publication, lifecycle actions, and revision history
without the lifecycle surface being stretched by unrelated Calendar content or
Planning inputs.

**Why this priority**: Lifecycle state is essential, but its controls and
history compete with day-to-day calendar planning when placed in the same
vertical stack.

**Independent Test**: Prepare a semester with a working revision, a current
publication, and historical lifecycle events; open Versions; execute and cancel
representative permitted lifecycle actions; and verify that all FS-013
semantics remain intact in the focused workspace.

**Acceptance Scenarios**:

1. **Given** a selected semester has a working revision and a current publication, **When** Versions opens, **Then** both designations, stable revision identities, lifecycle states, and available actions are visible without Calendar or exam-generation content.
2. **Given** a revision has lifecycle history, **When** the planner inspects that revision, **Then** its ordered history is readable on demand without forcing every event detail to occupy permanent page height.
3. **Given** a lifecycle action is permitted by FS-013, **When** the planner completes it from Versions, **Then** the selected semester's lifecycle state refreshes consistently and no schedule content is changed beyond the established action.
4. **Given** no lifecycle revision exists, **When** Versions opens, **Then** the established Start Draft state and action are presented without an empty oversized lifecycle container.
5. **Given** a lifecycle action is stale, rejected, or fails, **When** feedback appears, **Then** existing revision and publication state is preserved and the planner can review the refreshed current state.

---

### User Story 5 - Prepare Exams in a Dedicated Workspace (Priority: P2)

A planner opens Exams for the selected semester, distinguishes courses eligible
for exam preparation from courses that are not eligible, configures or reviews
requirements, selects eligible courses, and prepares exams without scrolling
past the calendar or revision history.

**Why this priority**: Exam preparation is a substantial semester task with its
own selection, eligibility, constraints, and confirmation flow. A dedicated
workspace makes its available work and next action easier to understand.

**Independent Test**: Open Exams for a semester containing eligible courses,
courses with active exams, and courses blocked for another reason; configure an
eligible course, select one or more eligible courses, prepare exams, cancel or
confirm the established flow, and verify accurate selection and result
feedback.

**Acceptance Scenarios**:

1. **Given** the selected semester contains courses in several exam eligibility states, **When** Exams opens, **Then** eligible courses are presented before unavailable courses by default and every unavailable course has a specific reason available.
2. **Given** one or more eligible courses are selected, **When** the planner reviews the workspace, **Then** the selected count, applicable generation constraints, and Prepare exams action remain available without scrolling to the end of the course list.
3. **Given** no eligible course is selected, **When** the workspace is shown, **Then** the preparation action is unavailable and the reason is understandable without relying only on a disabled visual style.
4. **Given** the planner prepares or generates exams, **When** the established confirmation and result flow completes, **Then** successes and failures are associated with their courses and all FS-012 scheduling, snapshot, partial-result, and stale-state rules remain unchanged.
5. **Given** a course already has an active exam, **When** the planner reviews it in Exams, **Then** the course cannot be selected for another active exam, its reason remains available, and it appears in the unavailable-course group rather than interrupting the eligible-course list.

### Edge Cases

- The selected semester or revision is removed or becomes unavailable while the
  planner is moving among Calendar, Versions, and Exams.
- The selected session is deleted, no longer matches active filters, or moves
  outside the visible period after a successful edit.
- A session becomes read-only because the selected lifecycle context changes
  while its edit pane is open.
- A save succeeds but a subsequent workspace refresh is delayed or fails.
- A stale or invalid save fails after the planner has entered changes; the pane
  must not imply success or silently discard the entered correction.
- The planner attempts to open another session, change Schedule destination,
  close the pane, or collapse a surface while unsaved session changes exist.
- The originating calendar item is no longer available when focus should be
  restored after closing the pane.
- Navigation is unpinned at a wide size and the viewport then changes to the
  narrow temporary-panel presentation or returns to wide presentation.
- Planning inputs are hidden while a course or semester becomes unavailable.
- A semester has no schedule revision, only a Published revision, or both a
  Working and Current Published revision.
- A semester has no exam-enabled courses, no eligible courses, or more courses
  than can be shown without internal scrolling or filtering.
- Exam eligibility changes while the planner has courses selected.
- Long course, cohort, lecturer, room, revision, or validation labels must not
  hide the pane close, edit, save, cancel, navigation, or preparation controls.
- At supported narrow widths or 200% text zoom, the right-side pane must adapt
  without making its content or the control that closes it unreachable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The primary navigation MUST present Schedule as a parent containing the ordered child destinations Calendar, Versions, and Exams.
- **FR-002**: Calendar MUST be the default Schedule child when no Schedule child is already current.
- **FR-003**: Exactly one Schedule child destination MUST be identified as current whenever Schedule content is shown.
- **FR-004**: Calendar MUST present calendar planning and operational summary content without permanently stacking complete Versions or Exams workspaces beneath it.
- **FR-005**: Versions MUST present the applicable lifecycle designations, actions, and history without Calendar or exam-generation content.
- **FR-006**: Exams MUST present applicable exam requirement, eligibility, selection, preparation, and result content without Calendar or complete revision-history content.
- **FR-007**: Adding Schedule children MUST preserve the established Academic Data hierarchy, destinations, and current-state behavior.
- **FR-008**: Navigation among Schedule children MUST NOT create, change, publish, abandon, restore, generate, or delete scheduling or academic data solely because navigation occurred.
- **FR-009**: Every Schedule child MUST present a compact shared context header that identifies the selected semester and any revision or course context meaningful to that destination, permits changes to that meaningful context, and propagates those changes consistently across Schedule children.
- **FR-010**: Returning to Calendar during the same application use MUST restore the prior calendar mode, visible period, active filters, selected session, and clean open pane when their referenced semester, revision, and session remain available.
- **FR-011**: If preserved context is no longer available, the destination MUST present a clear current state and a direct recovery choice rather than displaying mixed or stale context.
- **FR-012**: Deliberate List mode MUST remain available under Calendar with the behavior required by FS-014, but no session selection or edit action initiated in Week, Day, or Month mode may force List mode.
- **FR-013**: Selecting a teaching or exam session in Week, Day, or Month mode MUST open its contextual detail in a pane that docks beside Calendar when both remain usable, overlays Calendar from the right when horizontal space is constrained, and becomes a temporary full-screen panel on the established narrow presentation.
- **FR-014**: Opening the session pane MUST preserve the current Calendar mode, visible period, filters, semester, revision, and scroll position.
- **FR-015**: The pane MUST identify the selected session's kind, course, date, time, resources, revision context, lifecycle context, and current warnings required by FS-012 through FS-014.
- **FR-016**: For both teaching and exam sessions, the pane MUST expose an Edit session action only when the selected session and revision are editable under established scheduling and lifecycle rules.
- **FR-017**: For both teaching and exam sessions, activating Edit session MUST replace or extend the pane's detail with the established editable session values and MUST keep Save and Cancel in the pane rather than opening a separate editor.
- **FR-018**: Saving from the pane MUST apply all established validation, conflict, capacity, holiday, snapshot, stale-state, and revision-editability rules without weakening or duplicating those rules.
- **FR-019**: After a successful save, Calendar MUST refresh the changed item and affected operational context without requiring the planner to reopen the semester or switch modes.
- **FR-020**: After a successful save, the pane MUST show the current saved session detail or an explicit completed state associated with that session.
- **FR-021**: Cancelling an edit MUST leave saved schedule data unchanged and return the pane to the selected session's current saved detail.
- **FR-022**: A failed or validation-rejected save MUST leave saved schedule data unchanged, retain the planner's entered values in edit mode, and show actionable feedback in the pane. If refreshed state shows that the target no longer exists or is no longer editable, the pane MUST leave edit mode, show or identify the accurate current state, and explain why the entered values cannot be applied.
- **FR-023**: The pane MUST protect unsaved changes when the planner attempts to close it, choose another session, change destination, or otherwise replace the editing context.
- **FR-024**: Closing a clean pane MUST restore focus to the originating calendar item when it remains available, or to a predictable Calendar result location when it does not.
- **FR-025**: When a selected session disappears or becomes non-editable after refresh, the pane MUST close or transition to accurate current detail and communicate the change without leaving focus on hidden content.
- **FR-026**: On supported wide layouts, planners MUST be able to unpin and pin the persistent primary navigation through clearly labeled controls.
- **FR-027**: Unpinning navigation MUST remove the expanded persistent panel from the main layout, reclaim main-content width, and leave a compact labeled control that reopens navigation.
- **FR-028**: The most recently chosen wide-layout navigation pin state MUST be restored when the application is revisited on the same device.
- **FR-029**: On the established narrow navigation presentation, navigation MUST remain a temporary dismissible panel and MUST NOT offer a pin control that has no effect.
- **FR-030**: Calendar MUST provide the full Planning inputs pane and allow planners to hide and show it independently from primary navigation; Versions and Exams MUST use the compact shared context header without displaying the full Planning inputs pane.
- **FR-031**: Changing primary-navigation visibility MUST NOT change Planning-input visibility, and changing Planning-input visibility MUST NOT change primary-navigation visibility.
- **FR-032**: Hiding or showing either left-side surface MUST preserve current destination, semester, revision, course, calendar, session, and unsaved-edit context.
- **FR-033**: Versions MUST show the active working revision and current publication, when present, with stable identity, state, designation, and available lifecycle actions required by FS-013.
- **FR-034**: Versions MUST provide complete ordered lifecycle history while allowing detailed event history to be inspected without requiring all event detail to remain expanded.
- **FR-035**: Versions MUST present meaningful no-revision, working-only, published-only, and working-plus-published states, and its content area MUST NOT expand solely to equal the height of another Schedule surface.
- **FR-036**: Exams MUST present selectable courses before courses unavailable for exam preparation by default and MUST make a specific reason available for each unavailable course.
- **FR-037**: Exams MUST keep the current selected-course count, applicable constraints, and preparation action available without requiring the planner to scroll to the end of the course list.
- **FR-038**: Exams MUST prevent ineligible courses from being selected while preserving all exam configuration, active-exam, recommendation, generation, partial-result, confirmation, and stale-state rules established by FS-012.
- **FR-039**: Unavailable courses MUST be grouped separately from eligible courses by default so repeated unavailability explanations do not interrupt eligible-course selection or hide the primary preparation action.
- **FR-040**: Current destination, navigation expansion, pin state, Planning-input visibility, pane state, edit state, and read-only state MUST be communicated by text or semantics and MUST NOT rely only on color.
- **FR-041**: Every new navigation, pin, visibility, pane, edit, save, cancel, close, and preparation control MUST be operable by keyboard with visible focus.
- **FR-042**: Opening and closing temporary navigation or a narrow-layout session pane MUST manage focus predictably, prevent interaction with obscured content where applicable, and support Escape dismissal when no unsaved-change decision is required.
- **FR-043**: Changes caused by saving, cancelling, stale-state recovery, disappearing selection, or eligibility refresh MUST be communicated without requiring the planner to infer the result only from visual movement.
- **FR-044**: At supported narrow widths and up to 200% text zoom, every Schedule destination and required control MUST remain reachable without panels or controls obscuring one another.
- **FR-045**: This feature MUST preserve existing scheduling, lifecycle, publication, exam, conflict, capacity, holiday, validation, and academic-data business rules.
- **FR-046**: This feature MUST NOT add a new schedule lifecycle state, exam eligibility rule, scheduling constraint, approval role, permission model, or independently publishable course schedule.
- **FR-047**: This feature MUST NOT remove deliberate Calendar List mode or the existing ability to inspect historical, working, and current-published context where earlier specifications require it.
- **FR-048**: This feature MUST update the user-facing navigation and session-correction contracts from FS-014 and FS-018 only where this specification explicitly requires focused Schedule children, unpinned navigation, or in-pane editing.
- **FR-049**: Changing among docked, right-overlay, and narrow full-screen pane presentations MUST preserve the selected session, entered edit values, validation feedback, and unsaved-change state.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Existing backend behavior MUST continue to be verified with FastAPI-compatible tests, normally using `pytest`, wherever the changed user flow exercises saved scheduling, lifecycle, or exam behavior.
- **TR-003**: Frontend behavior MUST be verified through React/Vite-appropriate build, lint, component, and UI checks covering the changed Schedule workflows.
- **TR-004**: Automated coverage MUST verify Schedule child navigation, current-destination semantics, default Calendar selection, context preservation, and the absence of Versions and Exams as permanent Calendar stack content.
- **TR-005**: Automated coverage MUST verify session-pane opening, detail, edit, save, cancel, failure, stale-state, unsaved-change protection, no forced List-mode switch, and focus restoration.
- **TR-006**: Automated coverage MUST verify independent primary-navigation pin state and Planning-input visibility, same-device pin-state restoration, and transitions between wide and narrow presentations.
- **TR-007**: Automated coverage MUST verify focused Versions and Exams empty, normal, unavailable, success, failure, and stale states while preserving FS-012 and FS-013 rules.
- **TR-008**: Keyboard, assistive-technology, narrow-width, and 200%-text-zoom acceptance paths MUST be manually verified where automated checks cannot establish actual usability.
- **TR-009**: Regression coverage MUST verify that deliberate Calendar List mode, Academic Data navigation, schedule editing, lifecycle actions, and exam preparation retain their established domain behavior.
- **TR-010**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Schedule Destination**: One of Calendar, Versions, or Exams under the Schedule navigation parent, with a label, hierarchy position, current state, and applicable retained planning context.
- **Schedule Workspace Context**: The planner's shared semester, revision, and course context presented through the compact context header, plus Calendar mode, visible period, filters, and selected session where applicable.
- **Session Pane State**: The transient detail or edit state for one selected teaching or exam session, including its originating Calendar location, whether unsaved changes exist, and whether a clean pane should reopen when the planner returns to Calendar.
- **Navigation Preference**: The planner's same-device preference for whether wide primary navigation is pinned or unpinned.
- **Planning Inputs Visibility**: The independently controlled visible or hidden state of contextual Planning inputs.
- **Revision Workspace Context**: The active working, current-published, or historical revision identity and lifecycle information presented in Versions.
- **Exam Preparation Context**: The selected semester's course eligibility, selected courses, requirements, constraints, preparation state, and generation results presented in Exams.

### Scope Boundaries and Relationships

- FS-012 remains authoritative for exam requirements, eligibility, scheduling,
  generation, correction, snapshots, partial results, and stale-state behavior.
  FS-019 changes exam detail and correction placement to the shared Calendar
  pane but does not change any exam rule or outcome.
- FS-013 remains authoritative for revision states, lifecycle transitions,
  publication immutability, history, and stale lifecycle actions.
- FS-014 remains authoritative for Calendar content, modes, filtering,
  operational summaries, and detail data. FS-019 changes the placement of detail
  and correction actions and prohibits an automatic switch to List mode.
- FS-018 remains authoritative for the single primary navigation and Academic
  Data hierarchy. FS-019 changes Schedule from one leaf destination into a
  parent with three child destinations and adds wide-layout pinning.
- This feature reorganizes and clarifies existing planner workflows. It does not
  create new scheduling, lifecycle, publication, exam, or academic-data rules.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After locating a session in Week, Day, or Month mode, planners can open its edit controls in no more than two intentional actions without entering List mode.
- **SC-002**: In 100% of acceptance cases, opening, editing, cancelling, or successfully saving through the session pane preserves Calendar mode, semester, revision, visible period, and active filters unless the saved change itself makes the selected item leave the visible result.
- **SC-003**: In an unaided usability review with at least 10 representative planners or acceptance reviewers, at least 90% can correct a teaching session and confirm the updated calendar item on their first attempt without guidance or an unintended view change.
- **SC-004**: In 100% of inspected Calendar states, complete Versions and Exams workspaces are absent from the Calendar content stack and remain reachable through no more than two primary-navigation actions.
- **SC-005**: At least 90% of representative planners in an unaided review can find Calendar, revision history, and exam preparation on their first attempt.
- **SC-006**: In 100% of supported wide-layout acceptance cases, a planner can unpin and restore primary navigation and independently hide and restore Planning inputs without losing current Schedule or edit context.
- **SC-007**: In 100% of keyboard acceptance paths, planners can reach every Schedule child, open and close applicable panels, inspect and edit a session, save or cancel, and continue in Calendar without focus loss.
- **SC-008**: In 100% of acceptance checks at supported narrow widths and 200% text zoom, current location and all required navigation, pane, lifecycle, exam, save, cancel, and close controls remain reachable and unobscured.
- **SC-009**: In 100% of lifecycle and exam regression cases, moving the workflows into focused destinations produces the same permitted outcomes, rejected outcomes, confirmations, and stale-state protections as the authoritative prior specifications.
- **SC-010**: In 100% of navigation-only acceptance cases, changing destination, expansion, pinning, or visibility causes no scheduling or academic-data mutation.

## Assumptions

- The users are the existing planner or office-staff audience with established
  authority to view and modify working schedules; this feature adds no new roles
  or permissions.
- Calendar is the default Schedule child because it is the primary operational
  workspace.
- Calendar, Versions, and Exams use one compact shared context header. It always
  identifies the selected semester and includes revision or course controls
  only where they are meaningful to the current destination. Calendar also
  provides the collapsible full Planning inputs pane.
- Calendar mode, visible period, filters, and current planning context are
  retained for the duration of the current application use. A clean selected
  session pane is also restored on return to Calendar when its semester,
  revision, and session remain available. The wide-navigation pinned preference
  is retained when the same device revisits the application.
- Planning inputs visibility is a workspace choice independent from primary
  navigation. Longer-term persistence of Planning-input visibility is not
  required.
- Session detail and editing use an adaptive pane: it is docked beside Calendar
  when both remain usable, overlays Calendar from the right at constrained
  widths, and becomes a temporary full-screen panel on the established narrow
  presentation. Presentation changes retain the same content, actions,
  selected session, entered values, validation feedback, and unsaved-change
  protection.
- The existing session, lifecycle, and exam operations remain the source of
  truth; this feature changes how planners reach and use them.
