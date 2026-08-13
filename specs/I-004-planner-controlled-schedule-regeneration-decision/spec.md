# Feature Specification: Planner-Controlled Schedule Regeneration Decision

**Working Branch**: `HEAD (delegated worktree)`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "Create FS-023 so a planner can compare one valid, provisional, jointly regenerated teaching-schedule alternative with the complete current selected result and atomically accept the generated result or retain all saved schedules."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare a Provisional Regenerated Alternative (Priority: P1)

A planner selects one or several courses, at least one of which already has a
saved teaching schedule, and starts generation. The system produces one valid
alternative for the complete selection without changing saved schedules, then
shows the planner the current and generated results side by side before any
replacement can occur.

**Why this priority**: The planner needs evidence and final authority whenever
generation could replace existing work. Without a provisional comparison, a
coverage rule could silently retain or replace the wrong operational trade-off.

**Independent Test**: Select a course whose complete current schedule has an
active hard-constraint warning, generate a valid partial alternative with fewer
scheduled units, and verify that the saved Working revision remains unchanged
while a comparison shows coverage, completeness, remaining reasons, and the
warning resolved by the candidate.

**Acceptance Scenarios**:

1. **Given** at least one selected course has saved teaching sessions, **When** a valid joint alternative is generated, **Then** no selected schedule is changed and one post-generation comparison is shown for the complete selection.
2. **Given** the generated alternative schedules fewer teaching units than the current result but satisfies all active hard constraints, **When** the comparison is shown, **Then** the alternative remains available for explicit acceptance and its partial status, remaining units, and reasons are visible.
3. **Given** the generated alternative appears complete and resolves every shown current warning, **When** generation finishes, **Then** the comparison is still shown and no automatic replacement occurs.
4. **Given** selected saved sessions include planner-created or planner-edited sessions, **When** the comparison is shown, **Then** it clearly states that accepting the generated alternative replaces those selected sessions as part of the complete result.

---

### User Story 2 - Make One Atomic Decision for the Selection (Priority: P1)

The planner makes one indivisible choice for every course in the joint result.
Accepting applies the complete generated selection; cancelling or dismissing
discards the complete candidate and retains everything currently saved.

**Why this priority**: Per-course mixing would break the joint solver's conflict
guarantees and could leave a multi-course operation only partly applied.

**Independent Test**: Select one course with an existing schedule and one
previously unplanned course, generate a joint candidate, and separately exercise
acceptance, cancellation, and dismissal. Verify that acceptance saves both
course results together and that either cancellation path saves neither.

**Acceptance Scenarios**:

1. **Given** a valid comparison for several selected courses, **When** the planner chooses `Neu erzeugten Stundenplan übernehmen`, **Then** the complete generated result replaces or creates all selected course schedules as one successful operation.
2. **Given** a valid comparison for several selected courses, **When** the planner chooses `Abbrechen`, **Then** the complete candidate is discarded and every current selected and unselected schedule remains unchanged.
3. **Given** a valid comparison remains unresolved, **When** the planner dismisses it or leaves it, **Then** dismissal is treated as cancellation, the complete candidate is discarded, and all saved schedules remain unchanged.
4. **Given** applying any part of an accepted joint result cannot complete, **When** acceptance is attempted, **Then** none of the generated result is saved and the complete current selection is retained.
5. **Given** a mixed selection contains courses with and without existing teaching schedules, **When** the planner accepts or cancels, **Then** the same one decision applies to every course in that selection with no per-course accept or reject choice.

---

### User Story 3 - Prevent Invalid or Stale Replacement (Priority: P1)

The planner may choose between a warned current schedule and a valid generated
alternative, but cannot authorize a candidate that violates current planning
rules or was generated from obsolete planning state.

**Why this priority**: Planner control must not weaken conflict safety or allow a
candidate to overwrite newer schedules, constraints, or resource facts.

**Independent Test**: Generate a valid comparison, change a selected schedule or
another captured planning input, and attempt acceptance. Verify that no schedule
changes, the candidate cannot be committed, and the planner is told to generate
a new alternative.

**Acceptance Scenarios**:

1. **Given** any candidate would violate an active hard constraint, fixed teaching or exam occupancy, a holiday, availability, capacity, or lecturer, room, or cohort conflict rule, **When** generation concludes, **Then** that candidate is not offered for acceptance.
2. **Given** a valid candidate is awaiting a decision, **When** relevant revision, schedule, constraint, holiday, course, semester, resource, eligibility, availability, capacity, or active-exam state changes, **Then** acceptance is rejected without mutation and the planner is directed to regenerate.
3. **Given** the current saved schedule contains a warning, **When** the planner cancels a valid generated alternative, **Then** the current schedule is retained without automatic repair, deletion, or movement.
4. **Given** no valid generated alternative can be produced, **When** generation ends, **Then** all saved schedules remain unchanged, blocking reasons are shown, and no replacement decision is presented.

---

### User Story 4 - Preserve Direct Save for New Selections (Priority: P2)

A planner generating schedules only for courses without saved teaching sessions
continues to receive the established direct-save outcome because there is no
current selected schedule to replace.

**Why this priority**: Planner approval is required for replacement, not for the
first valid saved result, so the existing streamlined new-schedule workflow
should remain intact.

**Independent Test**: Select only courses with no saved teaching sessions,
generate a valid complete or partial joint result, and verify that it is saved
directly without showing the replacement comparison.

**Acceptance Scenarios**:

1. **Given** none of the selected courses has a saved teaching schedule, **When** a valid joint result is generated, **Then** the result is saved directly under the established generation rules and no replacement comparison is shown.
2. **Given** none of the selected courses has a saved teaching schedule and no valid result can be produced, **When** generation ends, **Then** no schedule is created and the planner receives actionable blocking reasons.

### Edge Cases

- Exactly one selected course has an existing schedule while every other
  selected course is previously unplanned; the complete selection still has one
  provisional candidate and one decision.
- Existing selected schedules include manual additions, deletions, edits,
  complete courses, partial courses, over-scheduled courses, or current
  hard-constraint warnings.
- The candidate has fewer total or per-course scheduled units than the current
  selection, including zero newly placed units for one selected course, but is
  otherwise a valid joint result.
- The candidate has equal coverage but different resource assignments or
  resolves current warnings; the same factual comparison is still required.
- The planner activates the accept action more than once or the comparison
  closes while acceptance is in progress; at most one complete result may be
  committed.
- A selected or unselected teaching session, active exam, holiday, availability,
  resource assignment, capacity, constraint, course, semester, or Working
  revision changes after candidate generation but before acceptance.
- The active Working revision becomes non-editable or is no longer active while
  the comparison is open.
- The comparison contains long course names, several blocking reasons, or both
  complete and partial course outcomes; each fact remains associated with the
  correct course and current/generated side.
- The comparison is dismissed with the keyboard, a close control, or navigation
  away from the unresolved decision; each path has cancellation semantics.
- No valid candidate is proven within the established generation deadline; the
  current selection remains unchanged and no empty or misleading comparison is
  shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use the established unified conflict-aware teaching-schedule generator for selections of one to twenty courses; this feature MUST NOT introduce a separate generation workflow.
- **FR-002**: The system MUST determine before generation whether at least one selected course has saved teaching sessions in the active Working revision.
- **FR-003**: When at least one selected course has saved teaching sessions, generation MUST produce at most one provisional joint candidate for the complete selected course set without creating, replacing, deleting, or moving any saved teaching session.
- **FR-004**: A provisional candidate MUST NOT appear as the saved Working revision or as current schedule data in other views before successful planner acceptance.
- **FR-005**: Every offered candidate MUST satisfy all active course and study-type time constraints, course and semester date boundaries, holidays, resource eligibility and availability, room capacity, fixed unselected teaching and active-exam occupancy, same-course active-exam teaching boundaries, and lecturer, room, and cohort non-overlap rules.
- **FR-006**: A candidate containing any known hard-constraint violation MUST NOT be offered for acceptance, even if the current selected schedule contains the same or other violations.
- **FR-007**: When a valid candidate exists and at least one selected course has saved teaching sessions, the system MUST always show one post-generation comparison before any replacement, including when the candidate has greater or equal coverage and no apparent disadvantage.
- **FR-008**: The comparison MUST explain that a planner decision is required and MUST identify the selected course set governed by that one decision.
- **FR-009**: The comparison MUST present current and generated totals for scheduled and required teaching units and MUST distinguish complete and partial results for the complete selection.
- **FR-010**: For every selected course, the comparison MUST present current and generated scheduled units, required units, complete or partial status, remaining units, and substantiated remaining or blocking reasons.
- **FR-011**: The comparison MUST identify substantiated current hard-constraint warnings that the generated candidate resolves, while clearly distinguishing warnings on retained current schedules from candidate validity.
- **FR-012**: The comparison MUST present concrete facts and trade-offs without declaring either the current or generated result categorically better.
- **FR-013**: When selected saved sessions include manual additions or edits, the comparison MUST state that acceptance replaces those selected sessions as part of the complete joint result.
- **FR-014**: The unresolved comparison MUST offer exactly the decision actions `Neu erzeugten Stundenplan übernehmen` and `Abbrechen`; a standard dismissal control MAY also be available but MUST have cancellation semantics.
- **FR-015**: Choosing `Neu erzeugten Stundenplan übernehmen` MUST accept the complete joint candidate for every selected course, including both replacements for courses with saved sessions and newly created schedules for previously unplanned selected courses.
- **FR-016**: The system MUST NOT offer per-course accept or reject choices or combine retained current results from some selected courses with generated results from others.
- **FR-017**: The planner MUST be permitted to accept a valid partial candidate with fewer scheduled units than the current selection or than an individual current selected schedule.
- **FR-018**: Choosing `Abbrechen`, dismissing the comparison, or leaving the unresolved comparison MUST discard the complete candidate and leave all saved schedules and other planning records unchanged.
- **FR-019**: Cancellation or dismissal MUST NOT automatically repair, delete, move, or revalidate by mutation any retained current session.
- **FR-020**: Acceptance MUST persist the complete selected-course candidate atomically; if any part cannot be applied, no part MAY be applied and the complete saved selection MUST remain unchanged.
- **FR-021**: An accepted candidate MUST be applied at most once, even if acceptance is repeated or interrupted.
- **FR-022**: Immediately before acceptance, the system MUST revalidate the active Working revision and every relevant planning input on which candidate validity or comparison facts depend.
- **FR-023**: A candidate MUST become stale when relevant revision, selected or protected teaching, active-exam, constraint, holiday, course, semester, resource, eligibility, availability, capacity, or lifecycle state changes after candidate generation.
- **FR-024**: A stale candidate MUST NOT replace any saved schedule; the planner MUST receive an actionable explanation that current state changed and a new alternative must be generated.
- **FR-025**: Generation, comparison, and acceptance MUST be available only for the active editable Working revision, consistent with the established schedule lifecycle.
- **FR-026**: When no valid candidate is produced, the system MUST preserve all saved schedules, report substantiated course-specific blocking reasons, and MUST NOT present a replacement choice.
- **FR-027**: When none of the selected courses has saved teaching sessions, the system MUST preserve established direct-save generation for a valid complete or partial joint result and MUST NOT show the replacement comparison.
- **FR-028**: A cancelled, dismissed, failed, invalid, timed-out, unproven, stale, or unsuccessfully applied candidate MUST create no schedule change, planner-decision record, or mandatory written-reason record.
- **FR-029**: The planner MUST NOT be required to enter a comment, justification, signature, or other written reason to accept or cancel a candidate.
- **FR-030**: Generation result and comparison messages MUST use the established actionable German wording conventions and MUST distinguish what happened, why it happened, and what the planner can do next.
- **FR-031**: The comparison MUST expose a programmatically determinable title, current-versus-generated structure, course associations, statuses, warnings, and decision controls so assistive technology can convey the same decision evidence available visually.
- **FR-032**: The comparison MUST be fully operable by keyboard, MUST place focus within the decision surface when it opens, MUST keep focus from moving behind the unresolved decision, and MUST return focus to a logical generation control when it closes.
- **FR-033**: Status, completeness, warnings, resolved violations, and current-versus-generated distinctions MUST NOT rely on color alone.
- **FR-034**: If comparison content exceeds the available viewport or text is enlarged to 200%, all facts and both decision actions MUST remain reachable without loss of course or side association.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Generation acceptance tests MUST verify hard-valid candidates against active constraints, fixed teaching and exam occupancy, holidays, eligibility, availability, capacity, and lecturer, room, and cohort conflict rules for both one-course and multi-course selections.
- **TR-003**: State-transition tests MUST verify that candidate generation is non-mutating, acceptance is atomic and at-most-once, and cancellation, dismissal, failure, invalidity, timeout, unproven results, staleness, and unsuccessful application preserve all saved planning state.
- **TR-004**: Mixed-selection tests MUST verify that courses with and without existing schedules are accepted or cancelled together and that no per-course mixture can be committed.
- **TR-005**: Comparison tests MUST verify operation-wide and per-course current/generated facts, explicit manual-session replacement consequences, valid fewer-unit candidate availability, exact decision labels, factual wording, and actionable failure or stale guidance.
- **TR-006**: Freshness tests MUST change each relevant captured planning-state category after candidate generation and verify that acceptance is rejected without mutation.
- **TR-007**: Direct-save regression tests MUST verify that selections containing no existing teaching schedule continue to save valid complete or partial results without a replacement comparison.
- **TR-008**: Accessibility tests and manual review MUST verify keyboard-only completion, logical focus placement and return, assistive-technology names and relationships, non-color status communication, and readable content at 200% text zoom.
- **TR-009**: Regression coverage MUST verify that manual schedule editing, exam scheduling, revision lifecycle, publication, and unrelated Schedule workspace behavior remain unchanged.
- **TR-010**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Current Selected Result**: The complete saved teaching-schedule state for all selected courses in the active Working revision, including scheduled and required units, complete or partial status, manual sessions, remaining units, and current warnings.
- **Provisional Joint Candidate**: One valid, uncommitted generated alternative for the complete selected course set, including course-level outcomes and the planning-state basis used to establish validity and freshness.
- **Course Comparison Outcome**: The current and generated coverage, status, remaining units, reasons, and resolved current warnings for one selected course within the operation-wide comparison.
- **Regeneration Comparison**: The complete current-versus-generated decision evidence for one selected course set, including aggregate facts, course outcomes, replacement consequences, and the two planner actions.
- **Planner Regeneration Decision**: The one atomic choice to accept the complete joint candidate or cancel it; it is an interaction outcome, not a required retained history record.
- **Candidate Freshness Evidence**: The relevant Working revision and planning-state identity against which acceptance is revalidated so an obsolete candidate cannot replace newer work.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance cases where at least one selected course has saved teaching sessions, generation changes zero saved sessions before the comparison is accepted.
- **SC-002**: In 100% of valid regeneration cases involving existing selected schedules, the planner sees one comparison containing aggregate and per-course current/generated coverage, completeness, remaining reasons, and resolved current warnings before replacement is possible.
- **SC-003**: In 100% of accepted multi-course and mixed-selection cases, either the complete generated result is saved for every selected course or no selected course changes.
- **SC-004**: In 100% of cancellation, dismissal, navigation-away, failure, invalid, timed-out, unproven, stale, or unsuccessful-acceptance cases, all saved schedules and unrelated planning records remain unchanged.
- **SC-005**: Across all acceptance datasets, every offered generated alternative has zero known active hard-constraint violations and zero lecturer, room, or cohort overlaps with selected teaching, fixed unselected teaching, or active exams.
- **SC-006**: In 100% of stale-state acceptance cases, the candidate is rejected before mutation and the planner is told to regenerate from current state.
- **SC-007**: In 100% of selections with no existing teaching schedule, a valid complete or partial result follows direct-save behavior without presenting a replacement comparison.
- **SC-008**: In an unaided usability review with at least five representative planner users, at least 90% can identify the coverage and validity trade-off and complete their intended accept-or-cancel decision in under two minutes on the first attempt.
- **SC-009**: In 100% of keyboard and 200%-text-zoom acceptance checks, planners can reach, understand, and activate both decisions while retaining the association between each fact, its course, and the current or generated result.
- **SC-010**: For the established supported workload of one to twenty selected courses, at least 95% of representative generation attempts present a valid comparison, save a direct result, or show an actionable no-result outcome within thirty seconds.

## Assumptions

- The planner audience and authorization model remain unchanged. Only the active
  editable Working revision may be generated, compared, or replaced.
- A course has an existing teaching schedule when it has at least one saved
  teaching session in the selected active Working revision.
- Required and scheduled teaching units retain the definitions established by
  unified schedule generation, so current and generated values are directly
  comparable.
- Active exams, as defined by unified schedule generation, remain fixed
  occupancy and may bound teaching for their course; past exams remain stored
  and unchanged but are not newly brought into scope by this feature.
- Current hard-constraint warnings may remain on planner-retained manual work.
  They are decision evidence, not permission to generate an invalid candidate.
- Direct-save behavior for selections without existing teaching schedules
  includes valid partial results under the established generation rules.
- Candidate transport, temporary storage, and expiration mechanics are planning
  decisions, provided candidates remain provisional, cannot be exposed as the
  saved Working revision, and cannot be accepted after relevant state changes.
- FS-010 through FS-013 provide conflict-aware generation, holidays, exam
  occupancy, partial outcomes, Working-revision lifecycle, and stale-write
  protection. FS-019 provides the Schedule workspace and generation controls;
  FS-022 provides actionable German wording conventions.
- Per-course decisions, mixed current/generated application, changes to manual
  editing or publication authority, mandatory decision comments or history,
  and automatic repair after cancellation remain outside this feature.
