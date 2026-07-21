# Feature Specification: FS-013 Versioned Review and Publication Lifecycle

**Working Branch**: `codex/fs-012-exam-scheduling`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Give planner users controlled Draft → Ready for review → Published schedule states and safe post-publication revision."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish a Stable Semester Schedule (Priority: P1)

A planner deliberately publishes the current working revision of a semester schedule. The published revision includes the semester's teaching and exam schedule, receives a stable revision identity and publication time, and cannot be edited in place. Moving through Ready for review is optional: the planner may publish directly from Draft.

**Why this priority**: Deliberate publication and a stable published result are the central business outcome of this slice.

**Independent Test**: Prepare one semester with a working Draft revision containing teaching and exam sessions, publish it directly, and verify that the published schedule is identifiable, remains unchanged when later planning data changes, and rejects every attempted in-place schedule edit.

**Acceptance Scenarios**:

1. **Given** a semester has a Draft working revision and no published revision, **When** the planner explicitly publishes the Draft, **Then** that revision becomes the one current Published revision with a stable revision identity and publication time.
2. **Given** a semester has a revision marked Ready for review, **When** the planner explicitly publishes it, **Then** publication succeeds without any approval or feedback prerequisite.
3. **Given** a Draft working revision was never marked Ready for review, **When** the planner explicitly publishes it, **Then** publication succeeds directly without creating a separate review gate.
4. **Given** a working revision has known missing schedule content or non-blocking validation alerts, **When** the planner requests publication, **Then** the planner sees those known conditions and may still explicitly confirm publication.
5. **Given** a revision is Published, **When** any action attempts to add, change, or remove one of its teaching or exam sessions, **Then** the action is rejected and the published snapshot remains unchanged.
6. **Given** a revision is Published, **When** related course, lecturer, room, cohort, exam, or other planning records later change, **Then** the published snapshot continues to present the schedule content and identifying context captured at publication.

---

### User Story 2 - Revise Without Disturbing the Published Schedule (Priority: P1)

After publication, a planner creates a new working revision from the current published schedule and changes that working copy while the existing published revision remains the visible current publication. Only explicit publication of the new revision replaces the prior publication.

**Why this priority**: Safe post-publication revision prevents incomplete or abandoned work from disrupting the schedule people currently rely on.

**Independent Test**: Publish one semester revision, create and edit a successor working revision, abandon or retain it without publishing, and verify that the original remains current; then restore or prepare a working revision and explicitly publish it to verify a single deliberate replacement.

**Acceptance Scenarios**:

1. **Given** a semester has a current Published revision and no active working revision, **When** the planner starts a new revision, **Then** a new Draft is created from the published snapshot and the current Published revision remains unchanged and visible.
2. **Given** a semester has a current Published revision and an edited Draft or Ready for review revision, **When** the planner views the semester's published schedule, **Then** the existing Published revision remains the current publication and working changes do not appear in it.
3. **Given** a working successor to a Published revision, **When** the planner explicitly publishes the successor, **Then** the successor becomes the single current Published revision and the former publication becomes an immutable superseded revision.
4. **Given** a replacement publication is requested, **When** the request cannot complete or is stale because relevant revision state changed, **Then** the prior Published revision remains current, the working revision is not partially published, and the planner is told to review the current state.
5. **Given** a published semester is being viewed through a course-specific view, **When** the planner selects that course, **Then** the displayed content comes from the semester's current Published revision rather than a separately published course version.

---

### User Story 3 - Use an Informative Review-Ready State (Priority: P2)

A planner may mark the one active working revision Ready for review to communicate its status, return it to Draft, continue editing it, or publish it. The state supplies information only and never transfers control away from the planner.

**Why this priority**: The optional state supports an understandable review workflow while preserving the planner-only MVP and direct publication.

**Independent Test**: Move one working revision between Draft and Ready for review, edit it in each state, publish from each state in separate cases, and verify that no approval, lecturer access, or feedback condition blocks the planner.

**Acceptance Scenarios**:

1. **Given** an active Draft revision, **When** the planner marks it Ready for review, **Then** its current state and transition time become visible without creating an approval requirement.
2. **Given** an active Ready for review revision, **When** the planner continues editing schedule content, **Then** the edits are allowed and its revision identity and Ready for review state are retained until the planner explicitly changes that state.
3. **Given** an active Ready for review revision, **When** the planner returns it to Draft, **Then** it becomes Draft with all saved schedule content retained.
4. **Given** missing, pending, or negative feedback may later be associated with a revision, **When** the planner publishes that revision, **Then** the feedback status does not prevent publication.
5. **Given** a Published, superseded, or abandoned revision, **When** the planner attempts to mark it Ready for review, **Then** the transition is rejected and its state and content remain unchanged.

---

### User Story 4 - Abandon, Restore, and Inspect Revision History (Priority: P2)

A planner can abandon an active unpublished revision without affecting the current publication, restore that revision when no other working revision exists, and inspect the complete ordered revision and lifecycle history for the semester.

**Why this priority**: Safe abandonment prevents obsolete work from remaining active, while restoration and visible history protect planner effort and explain which revision is current.

**Independent Test**: Create a working revision after publication, move it through Ready for review, abandon it, inspect its history alongside the current publication, restore it, and verify that its content and identity are retained and its state becomes Draft.

**Acceptance Scenarios**:

1. **Given** an active Draft or Ready for review revision and a current Published revision, **When** the planner abandons the working revision, **Then** the working revision becomes abandoned and the Published revision remains current and unchanged.
2. **Given** an abandoned revision and no active working revision for the semester, **When** the planner restores it, **Then** the same revision returns to Draft with its saved content and revision identity retained.
3. **Given** an abandoned revision and another active working revision for the same semester, **When** the planner attempts restoration, **Then** restoration is rejected, both revisions remain unchanged, and the planner is told that only one working revision may be active.
4. **Given** a semester with draft, ready, abandoned, published, and superseded lifecycle events, **When** the planner opens revision history, **Then** every revision appears in a stable order with its identity, current status, origin revision where applicable, relevant lifecycle times, and current-versus-working designation.
5. **Given** an abandoned revision, **When** the planner leaves it abandoned indefinitely or starts a different working revision, **Then** it remains in history but does not become current, published, or editable.

### Edge Cases

- A semester with no working or published revision exposes an explicit **Start Draft** action. Until that action succeeds, publication and scheduled-occurrence mutations are unavailable; the created Draft adopts the semester's current saved schedule content, including an empty schedule.
- A semester may have no current publication before its first publication, but once a current publication exists it remains current until a replacement publication completes.
- Two near-simultaneous attempts to start or restore working revisions must not result in more than one active Draft or Ready for review revision for the same semester.
- Two near-simultaneous publication attempts must not result in multiple current Published revisions or a period in which an existing current publication is lost.
- Repeating a completed state-transition request must not create duplicate revisions, duplicate history events, or a second current publication.
- A stale editor, state control, abandon prompt, restore action, or publication confirmation must not overwrite a newer revision state or published schedule.
- Abandoning a working revision with unsaved changes affects only its saved state; unsaved changes are not treated as part of revision history.
- Restoring an abandoned revision retains its prior state events and adds a restoration event; it does not erase the fact that it was abandoned.
- Publishing a restored revision replaces the current publication only after the planner explicitly publishes it.
- A superseded revision remains reviewable as history but can never become current again directly; further work begins in a Draft revision.
- Later feedback referring to an older revision remains attributable to that revision and does not alter the lifecycle state of another revision.
- Revision history must distinguish revisions even if their schedule contents are identical.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The publication lifecycle MUST apply to the complete teaching and exam schedule for one semester; this slice MUST NOT create independently publishable course revisions.
- **FR-002**: A semester schedule revision MUST have exactly one current lifecycle state: Draft, Ready for review, Published, superseded, or abandoned.
- **FR-003**: Draft and Ready for review MUST be the only active working states, and a semester MUST have at most one active working revision at a time. When a semester has no lifecycle revision and no current publication, the planner MUST be able to explicitly establish its initial Draft from the semester's current saved schedule content, including an empty schedule.
- **FR-004**: Ready for review MUST be optional and informative; it MUST NOT create an approval, feedback, or waiting prerequisite for any planner action.
- **FR-005**: The planner MUST be able to move the active working revision from Draft to Ready for review and from Ready for review back to Draft without losing its saved schedule content or revision identity.
- **FR-006**: The planner MUST be able to edit the active working revision in either Draft or Ready for review state, subject only to the schedule-editing rules established by earlier slices; editing MUST NOT change its lifecycle state automatically.
- **FR-007**: The planner MUST be able to publish directly from Draft or publish from Ready for review through an explicit publication action.
- **FR-008**: Before publication, the planner MUST be shown the selected semester, revision identity, current lifecycle state, whether the action will create the first publication or replace an existing publication, and any known incomplete schedule content or non-blocking validation alerts.
- **FR-009**: Known incomplete schedule content, non-blocking validation alerts, and any missing, pending, or negative later feedback MUST NOT prevent the planner from explicitly publishing.
- **FR-010**: Completing publication MUST give the revision a stable publication time and make it the one current Published revision for its semester.
- **FR-011**: Once Published, a revision's teaching sessions, exam sessions, schedule relationships, and planner-visible identifying context captured at publication MUST be immutable.
- **FR-012**: An attempted in-place edit, deletion, state reversal, or direct restoration of a Published or superseded revision MUST be rejected without changing any revision.
- **FR-013**: Changes to planning records made after publication MUST NOT alter the content or identifying context shown in an existing Published or superseded snapshot.
- **FR-014**: When a semester has a current Published revision, the planner MUST be able to create a new Draft derived from that published snapshot if no active working revision already exists.
- **FR-015**: Creating, editing, marking ready, returning to Draft, or abandoning a working revision MUST NOT change, hide, or remove the current Published revision.
- **FR-016**: Publishing a successor MUST make it the single current Published revision and MUST mark the former current publication superseded only as part of the same completed replacement outcome. In the ordered lifecycle history for that replacement, the former publication's supersession event MUST immediately precede the successor's publication event.
- **FR-017**: A failed, cancelled, invalid, duplicate, or stale publication MUST leave every saved revision unchanged and MUST leave the existing current Published revision unchanged when one exists.
- **FR-018**: A semester that has acquired a current Published revision MUST retain exactly one current Published revision until another revision is explicitly and successfully published as its replacement.
- **FR-019**: Course-specific schedule views MUST derive their published content and publication identity from the applicable semester-wide Published revision.
- **FR-020**: The planner MUST be able to abandon the active Draft or Ready for review revision through an explicit action that identifies the affected semester and revision.
- **FR-021**: Abandoning a working revision MUST retain that revision and its saved content in history, make it non-editable, and leave any current Published revision unchanged.
- **FR-022**: The planner MUST be able to restore an abandoned revision only when the semester has no active working revision; restoration MUST return the same revision to Draft with its saved content and identity retained.
- **FR-023**: Restoration attempted while another working revision is active MUST be rejected without changing either revision.
- **FR-024**: Superseded revisions MUST remain immutable history and MUST NOT be restored directly to a working or current-published state; the planner MUST start a new Draft to revise their schedule content.
- **FR-025**: Every revision MUST have a stable identity that is unique within its semester and a stable ordering relative to the semester's other revisions.
- **FR-026**: Revision history MUST retain every created revision and record each completed lifecycle transition in order, including creation, Ready for review, return to Draft, publication, supersession, abandonment, and restoration where applicable.
- **FR-027**: For every revision, history MUST expose its stable identity, semester, current state, origin revision where applicable, creation time, relevant state-transition times, publication time where applicable, and whether it is the current publication or active working revision.
- **FR-028**: History MUST preserve a revision's stable identity so that later feedback can remain associated with the revision it concerns, without implementing feedback collection in this slice.
- **FR-029**: State, revision identity, and current-versus-working designation MUST be visible wherever the planner selects, edits, publishes, or compares the published and working schedule context.
- **FR-030**: Any action based on revision state that changed after the planner opened its control or confirmation MUST be rejected as stale, preserve the current revision and publication state, and present the refreshed state before retry.
- **FR-031**: Repeating a completed transition request MUST NOT create a duplicate revision, duplicate lifecycle event, or additional current Published revision.
- **FR-032**: This feature MUST NOT add mandatory approvals, lecturer access or feedback collection, authentication, automatic publication, external publication delivery, organizational approval chains, field-by-field schedule edit audit, or editing of published data in place.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each implemented user story where automated testing is practical.
- **TR-002**: Lifecycle coverage MUST verify every allowed and rejected transition, direct Draft publication, optional Ready for review, editing in both working states, and publication despite known non-blocking conditions.
- **TR-003**: Snapshot coverage MUST verify that every form of teaching, exam, relationship, and identifying-context change leaves Published and superseded revisions unchanged.
- **TR-004**: Replacement coverage MUST verify first publication, successful explicit replacement, cancelled and failed publication, stale publication, repeated requests, and simultaneous attempts while preserving exactly one current publication.
- **TR-005**: Working-revision coverage MUST verify the one-active-working-revision rule across creation, abandonment, restoration, simultaneous attempts, and stale actions.
- **TR-006**: History coverage MUST verify stable identity and ordering, every defined lifecycle event, origin relationships, lifecycle times, current-versus-working designation, complete retention, and future revision association.
- **TR-007**: Scope coverage MUST verify that course-specific views use the semester publication and that no independent course publication, approval, authentication, lecturer feedback, automatic delivery, or published-data editing behavior is introduced.
- **TR-008**: Any exception to automated test-first work MUST document the reason and manual verification path in the implementation plan.

### Key Entities

- **Semester Schedule Revision**: One version of the complete teaching and exam schedule for a semester. It has a stable identity and order, one lifecycle state, an optional origin revision, lifecycle times, and schedule content appropriate to that revision.
- **Working Revision**: The semester's single active mutable revision, in Draft or Ready for review state. It may be edited, published, or abandoned by the planner.
- **Published Snapshot**: An immutable revision that was explicitly published. It retains the schedule content and identifying context captured at publication regardless of later working or planning-data changes.
- **Current Publication**: The single Published snapshot presently designated for a semester. Once established, it remains current until an explicit replacement publication completes.
- **Superseded Revision**: A prior Published snapshot that was replaced by a later explicit publication. It remains immutable and visible in history.
- **Abandoned Revision**: An unpublished working revision removed from active work without deletion. It remains in history and may be restored to Draft only when no other working revision is active.
- **Lifecycle Event**: A completed revision creation or state transition, including its type and time, used to explain the ordered history without recording every schedule field edit.

## Dependencies

- **Required — FS-006: Multi-Course Draft Generation** supplies the multi-course semester schedule boundary and existing planner-controlled draft behavior.
- **Required — FS-012: Conflict-Aware Exam Scheduling** supplies the exam schedule content included with teaching sessions in a semester revision.
- Existing review, manual editing, validation, session management, optimization, resource, and holiday behavior remains governed by its originating slices. FS-013 versions and publishes their resulting schedule content without redefining those workflows.
- FS-014 may later present lifecycle information in the calendar workspace, and FS-015 may later associate lecturer feedback with stable revision identities. Neither downstream slice is delivered here.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance cases, a semester with a current publication continues to show the exact same Published snapshot while a successor is created, edited, marked ready, returned to Draft, abandoned, restored, cancelled, or fails publication.
- **SC-002**: In 100% of completed publication cases, the semester has exactly one current Published revision with a visible stable identity and publication time; no acceptance case produces zero or multiple current publications after the first publication.
- **SC-003**: In 100% of post-publication change cases, the published teaching sessions, exam sessions, schedule relationships, and captured identifying context remain unchanged until an explicit replacement publication completes.
- **SC-004**: A planner can mark a Draft Ready for review, return it to Draft, or publish it directly with one explicit lifecycle action per transition and without supplying approval or feedback.
- **SC-005**: Before every publication, the planner can identify the semester, selected revision, current state, replacement consequence, and all known incomplete or non-blocking schedule conditions from the publication decision context.
- **SC-006**: In 100% of acceptance cases involving abandonment or restoration, no published snapshot changes, no revision content is lost, and the semester never has more than one active working revision.
- **SC-007**: Revision history accounts for 100% of created revisions and completed lifecycle transitions in stable order, with no duplicate identity or lifecycle event after repeated requests.
- **SC-008**: In a moderated acceptance test with at least 10 representative planner users following the same prepared-semester script, at least 90% of participants, rounded up to the next whole participant, can identify the current publication, active working revision, and most recent lifecycle event within 30 seconds without assistance.
- **SC-009**: In the same moderated acceptance test and participant cohort used for SC-008, at least 90% of participants, rounded up to the next whole participant, complete both direct first publication and safe replacement publication on their first attempt without mistaking a working revision for the current publication.
- **SC-010**: All applicable teaching and exam scheduling acceptance scenarios from FS-006 and FS-012 continue to pass when performed in the active working revision.

## Assumptions

- Publication scope is the complete semester schedule, including all course teaching sessions and exams in that semester. Course-specific views are projections of the same semester revision, not independently publishable units.
- A semester has at most one active working revision, in either Draft or Ready for review state. This avoids competing unpublished versions while still retaining all abandoned and published history.
- The complete revision and lifecycle history is retained for the life of the semester planning record. This slice does not define deletion or archival of revision history.
- History records revision creation and lifecycle transitions, not a field-by-field audit of every schedule edit.
- Abandonment is reversible for an unpublished revision. Restoration reactivates the same revision as Draft only if no other working revision is active; it does not erase earlier history.
- Published and superseded revisions cannot be restored directly. Reusing their content begins a new Draft so the historical snapshot remains immutable.
- Ready for review does not freeze content. The planner may edit in that state, return it to Draft, or publish it.
- The initial planner-only environment has one planner-user role and does not require actor identity in lifecycle history. Authentication and attributable user audit are outside this slice.
- Publication is an internal schedule lifecycle designation. Sending, exporting, synchronizing, or otherwise delivering the schedule to an external publication system is outside this slice.
- Known schedule incompleteness and validation alerts remain non-blocking in keeping with planner control. The planner receives visible decision context and explicitly chooses whether to publish.
- Later lecturer feedback will refer to stable revision identities, but FS-013 neither collects nor evaluates that feedback.
- Lifecycle timestamps represent unambiguous instants. Planner-facing history and publication times are interpreted in the institution's local timezone, assumed for this slice to be Europe/Vienna, and display an explicit timezone indication.
