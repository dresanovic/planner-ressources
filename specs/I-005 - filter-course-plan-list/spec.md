# Feature Specification: I-005 — Filterable Course Lists for Generation and Administration

**Working Branch**: `master` (specification-only update; unrelated working changes present)

**Created**: 2026-11-03

**Status**: Implemented — automated verification passed; user acceptance PASS on 2026-11-03

**Input**: User description: "Specify cohort-based course discovery in generation and Academic Data, preserving explicit selection and existing safeguards." Specification work explicitly authorized by "start the I-005" on 2026-11-03.

**Product authority**: [I-005 in Feature_slices.md](../../docs/planning/Feature_slices.md#i-005-filterable-course-lists-for-generation-and-administration). Dependencies: FS-007, FS-019, and I-003; preserve I-004. The directory is explicitly named `specs/I-005 - filter-course-plan-list` at the user's request.

## Clarifications

### Session 2026-11-03

- Q: When you leave a course list and return within the same semester, should its previous cohort filter be restored? → A: Restore during the current session; reset on semester change or page reload (Option B). Each list remembers its filter independently.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find and select a cohort's courses for generation (Priority: P1)

As a planner preparing a semester, I can narrow `Planung > Kalender > Plan erzeugen > Stundenpläne erzeugen` to a cohort, identify its courses, and explicitly select them without consulting another tab.

**Why this priority**: First-plan preparation required finding eleven Master courses among 94 courses in semester 2027 S. Cohort discovery removes that manual scan.

**Independent Test**: With the representative 94-course catalog, choose `MA IT & Wirtschaftsinformatik – 2. Semester`, inspect the eleven matches, select them individually, and review the selection before using existing generation.

**Acceptance Scenarios**:

1. **Given** semester 2027 S contains 94 courses, exactly eleven in the target cohort, **When** the planner filters the generation list by that cohort, **Then** exactly those eleven appear with identifiable semester/cohort context, and filtering selects none of them automatically.
2. **Given** those eleven matches and an empty selection, **When** the planner explicitly selects each course, **Then** the total is eleven distinct courses and generation uses exactly those IDs under existing eligibility rules.
3. **Given** similarly named courses in different cohorts or with different available references, **When** the planner inspects the list, **Then** names, cohort identities, and available distinguishing references identify the intended course within this workflow.
4. **Given** a matching course is unavailable for generation, **When** the filter is applied, **Then** it does not become eligible and the existing unavailability explanation is preserved.

---

### User Story 2 - Find a cohort's courses in Academic Data (Priority: P1)

As a planner, I can narrow `Stammdaten > Lehrveranstaltungen` to the applicable semester and cohort and open an existing course action directly.

**Why this priority**: Both flat lists were identified as the same discovery problem. Administration needs the same direct cohort discovery.

**Independent Test**: Establish semester 2027 S in Academic Data, choose the target cohort, verify its eleven courses with equivalent status visibility, and open one course's existing edit action without changing data merely by filtering.

**Acceptance Scenarios**:

1. **Given** courses from multiple semesters and cohorts, **When** the planner chooses 2027 S and the target cohort, **Then** only courses belonging to both appear and the active context is identifiable.
2. **Given** a filtered course, **When** the planner opens an existing detail/edit action, **Then** that exact record opens through the established workflow with unchanged permissions and validation.
3. **Given** an existing active/inactive status restriction, **When** cohort filtering is applied, **Then** both restrictions apply without archiving, reactivating, editing, or deleting courses.
4. **Given** separate generation and administration list contexts, **When** one list's cohort filter changes, **Then** the other list and calendar-session filters remain unchanged.

---

### User Story 3 - Understand the complete selection through filtering (Priority: P1)

As a planner, I can select courses across cohorts and still understand the complete generation selection, including courses hidden by a filter.

**Why this priority**: Visibility must never silently determine generation input or obscure the extent of a replacement decision.

**Independent Test**: Select two courses in cohort A, switch to B, select one more, and verify a total of three with two hidden. Review all identities, reveal A, deselect one, and verify generation receives exactly the remaining two IDs.

**Acceptance Scenarios**:

1. **Given** two selected courses in A, **When** filtering changes to B, **Then** selected IDs remain identical, the total stays two, and both are identified as hidden by the filter.
2. **Given** two hidden selected courses, **When** a visible third course is explicitly selected, **Then** the total becomes three and every selected course/cohort identity can be reviewed before generation.
3. **Given** twenty selected courses, some hidden, **When** the planner attempts another selection, **Then** the complete-set limit applies with an understandable reason; permitted deselection remains available.
4. **Given** hidden selected courses, **When** the cohort filter is reset, **Then** they reappear selected without any selected-ID change.
5. **Given** visible and hidden selections, **When** the existing clear-selection action is explicitly invoked, **Then** all selected IDs are removed and the cohort filter stays unchanged.
6. **Given** a hidden selected course with saved teaching sessions, **When** generation starts, **Then** it remains in the joint selection and existing I-004 comparison and atomic accept/cancel safeguards cover the complete selected set.
7. **Given** zero selections or a selected course that has become missing, unavailable, or stale, **When** generation is attempted, **Then** existing validation prevents invalid input without silently dropping or substituting selected IDs.

---

### User Story 4 - Recover from empty results and operate accessibly (Priority: P2)

As a planner, I can understand no-match results, reset filtering, and complete discovery using keyboard or assistive technology within existing layouts.

**Why this priority**: Filtering must remain understandable and recoverable in both the narrow planning panel and administration view.

**Independent Test**: In each surface, use only the keyboard to choose a cohort with no matches, identify context and feedback, reset, and select/open a course. Repeat with a screen reader, narrow viewport, and enlarged text.

**Acceptance Scenarios**:

1. **Given** courses exist but the cohort has no matches, **When** filtering completes, **Then** feedback identifies no matches and active context, provides a reachable reset, and leaves any generation selection intact and reviewable.
2. **Given** an empty semester, **When** the list opens or the filter resets, **Then** it explains the empty semester rather than implying that an empty selection can generate.
3. **Given** keyboard-only operation, **When** filtering, inspecting, selecting/deselecting, reviewing hidden selections, and resetting, **Then** every action is reachable with visible focus, no trap, and meaningful focus after result changes.
4. **Given** screen-reader operation, **When** filter or selection changes, **Then** the label/value, result count or no-match state, and total/hidden selection information are perceivable without relying on color or position.
5. **Given** long course/cohort names, **When** used at 320 CSS pixels wide or 200% text enlargement, **Then** identifying information and controls remain obtainable without clipped actions or two-dimensional scrolling caused by this feature.
6. **Given** an active cohort filter, **When** it is reset, **Then** the applicable list returns without changing semester, administration status restrictions, course/schedule data, or generation selection.
7. **Given** different cohort choices in the generation and administration lists, **When** the planner leaves either list and returns during the same session without changing its semester scope, **Then** that list restores its own previous cohort filter and shows the restored active context; restoring a filter does not restore or alter generation selection.
8. **Given** a remembered cohort filter, **When** the planner changes that list's semester scope or reloads the page, **Then** the cohort choice resets to unfiltered and a later return does not revive the previous choice. Explicit cohort-filter reset likewise replaces the remembered choice with the unfiltered state.

### Edge Cases

- Identical course names across cohorts/semesters: match actual relationships and use available references to distinguish records.
- A cohort has no courses in the semester, or all matches are excluded by administration status: report zero matches without silently broadening scope.
- A course lacks a usable cohort relationship: keep it discoverable in the applicable unfiltered list without assigning it arbitrarily; existing eligibility rules still apply.
- All selected courses are hidden, even with zero visible matches: retain the total and reviewable identities; visible emptiness does not make a valid explicit selection empty.
- Selection totals of zero, one, twenty, or an externally invalid total above twenty: retain existing validation irrespective of visibility. Repeated selection must not duplicate IDs.
- A selected course is deleted, archived, reassigned, or becomes ineligible: filters do not repair selection silently; existing validation/stale handling blocks invalid input with an explanation.
- A cohort choice disappears during refresh: explain unavailable context and allow reset without relabeling another cohort as the old one or changing selected IDs.
- Loading/retrieval failure: distinguish it from successful no-match results, preserve existing recovery behavior, and do not interpret unavailable data as a selection change.
- Semester change is a context transition, not a cohort-filter change: reset the cohort filter and retain the existing generation behavior that clears selection on semester change, with visible new context and count.
- Navigating away and back within the same session and unchanged semester scope restores each list's own cohort choice. A semester-scope change, page reload, or explicit filter reset discards that remembered choice; revisiting an earlier semester must not revive it. Filter memory does not extend the existing lifetime of generation selection.
- Filtering with a course editor open: do not save, discard, or switch its record even if it disappears from matches; existing explicit save/cancel/navigation rules remain authoritative.
- Filtering during preparation or generation: do not alter the operation's captured selection. Later explicit selection or semester changes remain subject to existing preparation and stale-state safeguards.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both named surfaces MUST offer direct course-list filtering by one cohort and an unfiltered cohort state, without needing a second page or browser tab to identify courses.
- **FR-002**: Matching MUST use actual course/cohort relationships within the applicable semester scope. Generation MUST use its existing selected semester. Academic Data MUST allow an explicit semester scope while retaining access to its existing all-semester catalog.
- **FR-003**: Each list MUST identify active semester scope, chosen cohort or unfiltered state, and matching-result count. With equivalent semester and existing status visibility, both surfaces MUST agree on cohort membership; generation eligibility remains separately authoritative.
- **FR-004**: Entries MUST identify course and cohort, expose available course reference/code information needed to distinguish similar names, and identify semester when spanning semesters. Existing status and action availability information MUST be preserved.
- **FR-005**: Each list MUST offer an explicit cohort-filter reset restoring courses within the current semester/status scope. Reset MUST NOT clear selection, change semester/status restrictions, or mutate data. Reset and clear-selection MUST have distinguishable labels and effects.
- **FR-006**: Lists MUST distinguish no matches, an empty underlying semester/catalog, loading, and retrieval failure. No-match feedback MUST identify active context and a reset path; failure MUST NOT appear as successful zero results.
- **FR-007**: Applying, changing, or resetting cohort filtering MUST change visibility only. It MUST NOT add, remove, duplicate, or substitute selected IDs, mutate academic/schedule records, start generation, or automatically open a course action.
- **FR-008**: Generation input MUST come from the complete explicit selection, including hidden selected courses, rather than visible matches. Existing individual select/deselect and clear-selection actions MUST remain available under existing workflow permissions.
- **FR-009**: Generation MUST show total selected courses and the number hidden by the cohort filter, even with zero matches. Before generation, the planner MUST be able to review every selected course's identity and cohort within that workflow and reveal a hidden course for explicit deselection without losing selection.
- **FR-010**: The existing one-to-twenty-distinct-course limit MUST apply to the complete selection. Filtering MUST NOT bypass limits or eligibility or prevent permitted deselection. Empty, duplicate, missing, oversized, cross-semester, or unavailable input MUST retain existing validation without silent substitution or partial submission.
- **FR-011**: Filtering MUST preserve existing preparation, revision/editability, eligibility, conflict, and stale-state safeguards. Hidden selected courses with saved sessions MUST trigger the same I-004 provisional comparison and operation-wide accept/cancel rules as visible courses. Filters MUST NOT alter a prepared/running operation's captured selection.
- **FR-012**: Academic Data MUST preserve existing detail/edit and lifecycle actions for the exact record with unchanged validation and authorization. Filtering MUST NOT save, cancel, or switch an open edit or apply it to every visible course.
- **FR-013**: Generation-list, administration-list, and calendar-session filters MUST be independent. Changing one list's cohort filter MUST NOT silently change another surface's context or selection.
- **FR-014**: Each list MUST independently remember its cohort choice during the current page session and unchanged semester scope, including return from a course action or navigation away and back. First use without a remembered choice MUST start unfiltered. A semester-scope change, page reload, or explicit cohort-filter reset MUST discard that list's remembered cohort choice and start unfiltered; returning to an earlier semester MUST NOT revive the discarded choice. Restoration MUST display the active filter context and MUST NOT restore or alter generation selection. Existing generation-selection clearing on semester change MUST remain unchanged; cohort filtering itself MUST never clear selection.
- **FR-015**: Filtering, reset, result inspection, permitted selection actions, hidden-selection review, and existing course actions MUST be keyboard-operable with accessible names, visible focus, logical focus order, and no trap. Result updates MUST NOT unexpectedly move focus; if a focused result disappears, focus MUST remain at a meaningful control in that workflow.
- **FR-016**: Assistive technology MUST expose active context/filter, result/no-match state, course/cohort identities, checked/disabled states and existing reasons, and total/hidden selection counts. Result and selection changes MUST be perceivable without color alone.
- **FR-017**: Both experiences MUST remain usable in their existing layouts at 320 CSS pixels wide and at 200% text enlargement, with full identifying text obtainable and no clipped/unreachable controls or feature-induced two-dimensional scrolling.

### Test Requirements *(mandatory)*

This specification explicitly requests test-first delivery under `.specify/memory/constitution.md`. These are requirements for later implementation, not authorization to begin it.

- **TR-001**: Create or update automated tests before production changes wherever practical for every story, including membership by distinct identity, semester boundaries, existing status visibility, reset, no-match, loading/failure, and independent contexts. Verify independent filter restoration after navigation and reset on semester change, page reload, and explicit filter reset, including no revival when returning to an earlier semester and no changes to generation selection from restoration.
- **TR-002**: Use a representative 94-course 2027 S dataset with exactly eleven courses in `MA IT & Wirtschaftsinformatik – 2. Semester`. Include other cohorts/semesters, similar names, and unavailable records; historical counts are not permanent catalog restrictions.
- **TR-003**: Verify selection invariance across filter changes/reset, total/hidden review, explicit deselection/clear-selection, zero/one/twenty/oversized boundaries, and exact submitted IDs. Verify I-004 comparison and atomic decisions with hidden selections and no silent reduction of invalid/stale input.
- **TR-004**: Verify unchanged academic permissions and generation safeguards at existing integration boundaries. If backend behavior changes, add test-first coverage in `backend/tests/`; otherwise run relevant existing regressions without inventing new backend scope. The plan MUST identify actual frontend, backend, and shared-contract impacts and concrete checks.
- **TR-005**: Verify keyboard/screen-reader operation, focus after filtering, no-match recovery, and selection announcements. Manually verify long labels, narrow panels, 320 CSS-pixel width, and 200% text enlargement. Document practical automated-test exceptions and manual verification paths in the plan.
- **TR-006**: Maintain traceability: Story 1 covers FR-001–004, FR-007–008, and FR-010; Story 2 covers FR-001–004 and FR-012–013; Story 3 covers FR-005 and FR-007–011; Story 4 covers FR-005–006 and FR-014–017. Context-transition and refresh edge cases additionally verify FR-011–014. The plan MUST provide checks for every requirement and measurable outcome.

### Key Entities

- **Course**: Existing academic course with stable identity, name, available reference, semester/cohort relationships, status, and existing eligibility.
- **Cohort**: Existing academic grouping with stable identity and recognizable name; determines course membership.
- **Semester context**: Generation's selected semester or Academic Data's explicit semester/all-semester scope; limits the list without changing assignments.
- **Course-list filter context**: One surface's cohort choice/unfiltered state within semester and existing status scope; controls visibility only.
- **Generation selection**: Distinct explicitly selected course IDs, with total, visible, and hidden membership independent of cohort filtering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In each surface, choosing the target cohort narrows the representative 94-course 2027 S list to exactly eleven courses without external lookup, another browser tab, or inspection of all 94 rows.
- **SC-002**: In every tested cohort-change/reset sequence within a semester, 100% of selected IDs remain unchanged unless explicitly selected/deselected. Generation receives exactly the complete selected set, including hidden items.
- **SC-003**: In all tested mixed-cohort, all-hidden, and zero-match cases, total/hidden counts are correct and every selected course is reviewable before generation; filtering cannot add a twenty-first selection.
- **SC-004**: Using only the keyboard, a planner can isolate and individually select the eleven generation courses, isolate/open a target administration course action, and recover from zero matches in both surfaces. A screen reader exposes all required context and selection information.
- **SC-005**: In a representative acceptance walkthrough, the planner correctly identifies active semester/cohort, every course that will be generated including hidden selections, and reset versus clear-selection effects on the first attempt without assistance or another tab.
- **SC-006**: With 94 applicable courses, at least 95% of twenty measured cohort changes per surface show the updated matches and count within one second after the choice once the catalog has loaded. Initial retrieval retains existing loading/failure behavior.
- **SC-007**: Filter-only acceptance checks produce zero academic/schedule mutations and zero automatic generation runs. Existing invalid-selection, stale-state, and I-004 replacement checks pass equally for visible and hidden selections.
- **SC-008**: At 320 CSS pixels wide and at 200% text enlargement, every filtering, reset, selection-review, and matching-course action remains operable in both surfaces without lost identifying information or feature-induced two-dimensional scrolling.
- **SC-009**: In every tested navigation round trip during the same session and unchanged semester scope, each list restores its own cohort choice without changing generation selection. In every tested semester-change, page-reload, and explicit-reset case, the cohort state is unfiltered and discarded choices do not reappear on later navigation.

## Assumptions

- Scope is cohort discovery in both lists, including necessary semester context. FS-007 supplies academic records/actions, FS-019 layouts/navigation, and I-003 unified generation; I-004 remains authoritative for replacement.
- Additional filters/search by name/code, study type, lecturer, or room; grouped/tree layouts; and select-all-visible actions remain deferred proposals. Displaying an available course code does not introduce code search.
- One cohort at a time is sufficient. Cross-cohort selection uses successive filter changes and explicit selection; multi-cohort filtering is not required.
- Confirmed persistence: each list remembers its cohort filter independently during the current page session and unchanged semester scope, including navigation away and back. Semester-scope change, page reload, and explicit filter reset discard the remembered choice. No persistence across reloads or cross-surface synchronization is required; filter memory does not change generation-selection lifecycle rules.
- Academic Data initially offers all-semester visibility and explicit semester scope for this task. Returning during the same session follows the confirmed cohort-filter restoration rule within unchanged semester scope. Cohort reset retains chosen semester and existing status scope. Its scope changes do not change generation's semester.
- Generation already clears selection on semester change; this remains a separate context rule. Selection invariance applies to cohort-filter changes/reset within a semester, without redesigning existing navigation or semester lifecycle behavior.
- Existing records supply cohort/semester relationships. Filtering does not create or repair academic data. The eleven-of-94 example is an acceptance dataset, not a production count constraint.
- Screenshots and the 03.11.2026 walkthrough are recorded references in Feature_slices.md, not independently inspected attachments in this session. Existing list behavior was consulted for context; no new layout is prescribed.
- Out of scope: scheduling/optimization rules, generation-limit changes, automatic generation/batching, academic-data mutation through filters, calendar-session filter redesign, authorization/revision/publication changes, external integration, and unrelated list redesign. This invocation produces specification artifacts only; planning, tasks, and implementation are later phases.
