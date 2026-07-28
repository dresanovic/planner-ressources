# Tasks: FS-019 Streamlined Schedule Workspace

**Input**: Design documents from `specs/019-streamline-schedule-workspace/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/schedule-workspace-ui.md`, `quickstart.md`

**Tests**: Tests are required by the project constitution and FS-019 TR-001 through TR-010. Every automatable behavior has a failing-test task before its production task. Real layout, zoom, focus containment, and assistive-technology behavior use the bounded manual matrix in `quickstart.md`.

**Organization**: Tasks are grouped by user story so in-pane correction, focused Schedule destinations, reclaimed workspace width, lifecycle governance, and exam preparation can be implemented and verified incrementally.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its stated prerequisites because it changes different files or produces independent evidence
- **[Story]**: Maps a task to one specification user story
- Every task names the exact file or repository path it creates or changes

## Phase 1: Setup and Baseline

**Purpose**: Isolate the customer-facing implementation and preserve the known starting point without overwriting unrelated work.

- [X] T001 Inspect and classify every existing change under `C:\Codex\planner-resource`; if all changes belong to FS-019, create or switch to `codex/019-streamline-schedule-workspace` before production edits, otherwise create a clean isolated worktree and transfer only FS-019 artifacts; do not discard, reset, or overwrite existing changes, and record the chosen boundary, locked versions, clean-production starting state, and focused baseline results in `specs/019-streamline-schedule-workspace/validation/pre-implementation.md`

---

## Phase 2: Foundational Calendar State Integrity

**Purpose**: Remove the blanket Calendar remount and establish accurate same-context reconciliation before any story relies on pane or destination restoration.

**CRITICAL**: Complete this phase before user-story implementation. Write and observe each focused test fail before its paired production change.

- [X] T002 [P] Add failing tests proving mode, anchor, filters, drilldown, and a valid selected occurrence survive a same-semester/revision workspace refresh while removed filter/session references are reconciled and announced in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T003 [P] Add failing page integration tests proving a coherent refresh does not remount Calendar state, a genuine semester replacement does reset it, and refreshed display/edit records cannot mix revision identities in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T004 Remove the `workspaceToken`-keyed content remount, retain stable Calendar view state, reconcile unavailable filters/occurrences explicitly, and provide deterministic result-focus fallback in `client/src/components/CalendarPlanningWorkspace.tsx` (depends on T002)
- [X] T005 Preserve the semester-scoped hard reset while supplying coherent stable revision/session data and recovery announcements to Calendar in `client/src/pages/CourseSchedulePage.tsx` (depends on T003, T004)

**Checkpoint**: Same-context data refreshes no longer erase Calendar interaction state, while invalid semester/revision/session references recover accurately.

---

## Phase 3: User Story 1 - Inspect and Edit Without Leaving the Calendar (Priority: P1) MVP

**Goal**: Open teaching or exam detail and correction in one adaptive right-side pane without switching Calendar mode or losing spatial/filter context.

**Independent Test**: In an editable Working revision, select teaching and exam occurrences from Week, Day, and Month, edit and save valid values, cancel, exercise validation/stale/read-only states, and verify mode, visible period, filters, revision, selected session, and pane context remain intact without entering List mode or a separate exam dialog.

### Tests for User Story 1 (write before implementation)

- [X] T006 [P] [US1] Add failing tests for pane detail/edit modes, teaching and exam content, Keep editing/Discard behavior, clean and dirty Escape, save/cancel/error status, origin focus, result fallback, and narrow focus containment in `client/src/components/SessionPane.test.tsx` and `client/src/components/DiscardChangesDialog.test.tsx`
- [X] T007 [P] [US1] Add failing parity tests proving extracted teaching fields, eligible lecturer/room mapping, payloads, validation feedback, and deliberate List editing remain unchanged in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T008 [P] [US1] Add failing tests for controlled exam draft/baseline values, dirty callbacks, pane-friendly composition, payloads, validation/server-error retention, and create/manual-placement regression in `client/src/components/ExamManualSessionEditor.test.tsx`
- [X] T009 [P] [US1] Replace the forced-List handoff expectation with failing tests for controlled teaching/exam selection, no mode switch, complete read-only detail, edit requests reachable in exactly two intentional actions, same-mode refresh, Calendar scroll-position preservation across open/edit/cancel/save/close, disappearing selection, and origin/fallback focus in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T010 [P] [US1] Add failing page tests for canonical `teaching:{id}` and `exam:{id}` resolution, in-pane save/cancel/failure/stale handling, coherent post-save Calendar/summary refresh, saved-but-refresh-failed status, shared course stability, and context-change dirty protection in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T011 [P] [US1] Add failing application tests proving a dirty pane blocks Schedule-to-Academic navigation until Keep editing or Discard commits and that current navigation/focus does not move while blocked in `client/src/App.test.tsx`

### Implementation for User Story 1

- [X] T012 [P] [US1] Extract the established teaching edit view-model mapper and reusable date/time/lecturer/room form into `client/src/components/sessionEditModel.ts` and `client/src/components/TeachingSessionEditor.tsx`, then rewire deliberate List editing without changing behavior in `client/src/components/DraftSchedulePanel.tsx` (depends on T007)
- [X] T013 [P] [US1] Add controlled draft, baseline/dirty reporting, retained feedback, and pane-friendly heading/action composition while preserving create/manual placement in `client/src/components/ExamManualSessionEditor.tsx` (depends on T008)
- [X] T014 [P] [US1] Implement the reusable safe-default Keep editing / Discard changes decision with Escape-as-keep and deterministic focus restoration in `client/src/components/DiscardChangesDialog.tsx` (depends on T006)
- [X] T015 [US1] Implement one `closed | detail | editing` teaching/exam pane with established detail fields, domain-specific editor composition, derived dirty state, status/error announcements, origin focus, and docked/overlay/narrow semantics in `client/src/components/SessionPane.tsx` (depends on T006, T012-T014)
- [X] T016 [US1] Make occurrence selection controlled, remove the teaching-to-List handoff and Calendar exam-dialog handoff, preserve deliberate List mode and the active Calendar scroll container without unexpected focus scrolling, and integrate one pane beside the current Calendar projection in `client/src/components/CalendarPlanningWorkspace.tsx` (depends on T004, T009, T015)
- [X] T017 [US1] Lift canonical pane state, origin/baseline/draft/error state, occurrence record resolution, and the single pending close/select/semester/revision/course/Schedule-child/Academic-destination intent union and discard dialog into `client/src/pages/CourseSchedulePage.tsx`; expose an approved-navigation callback so no second pending intent can exist in `App` (depends on T010, T014, T016)
- [X] T018 [US1] Integrate top-level Schedule-to-Academic navigation as a request to `CourseSchedulePage` and commit only its approved callback so semantic current state and focus change after approval without storing or rendering a second dirty decision in `client/src/App.tsx` (depends on T011, T017)
- [X] T019 [US1] Route teaching and exam corrections through their existing API mutations followed by coherent Calendar/summary refresh, distinguish mutation success from refresh failure, retain failed/stale drafts unless authoritative data proves them invalid, and remove the separate Calendar exam modal in `client/src/pages/CourseSchedulePage.tsx` (depends on T010, T013, T017)
- [X] T020 [US1] Add a container-aware Calendar/pane shell that docks at a Calendar pane container width of at least 70rem above an 820px viewport, uses a right overlay below 70rem above that viewport boundary, becomes a full-screen dialog at 820px or below, and preserves reachable sticky actions, long-label wrapping, and hidden-content/focus behavior in `client/src/App.css` (depends on T015-T019)
- [X] T021 [US1] Run the focused pane, Calendar, editor, page, and application suites and record failing-first evidence, the exactly-two-action edit path, Calendar scroll-position assertions, and teaching/exam save/cancel/failure/stale/no-List results in `specs/019-streamline-schedule-workspace/validation/us1-session-pane.md`

**Checkpoint**: User Story 1 is a demonstrable MVP: both session kinds can be inspected and corrected without leaving Calendar context, and every context-replacing action protects dirty work.

---

## Phase 4: User Story 2 - Navigate Focused Schedule Areas (Priority: P1)

**Goal**: Reach Calendar, Versions, and Exams as ordered Schedule children, expose only one focused workspace, and retain the applicable shared and clean Calendar context.

**Independent Test**: Start from each Schedule child, navigate to the other two, change meaningful semester/revision/course context, and verify the selected workspace replaces the others while Calendar mode, period, filters, valid clean selection/pane, and Academic Data behavior survive the round trip.

### Tests for User Story 2 (write before implementation)

- [X] T022 [P] [US2] Add failing component tests for Schedule as an expanded/active disclosure parent, ordered Calendar/Versions/Exams children, default and sole current child semantics, child selection within no more than two primary-navigation actions while Schedule is current, current-child no-op, unchanged Academic Data hierarchy, and narrow Schedule-child selection dismissal/current semantics in `client/src/components/ApplicationNavigation.test.tsx`
- [X] T023 [P] [US2] Add failing application tests for default Calendar, all three reachable children, retained selected child, mounted Schedule behavior, request/commit dirty navigation, content-focus handoff, and no navigation-induced API mutation in `client/src/App.test.tsx`
- [X] T024 [P] [US2] Add failing controlled-header tests for always-present semester plus destination-meaningful revision/course controls, unavailable-context recovery, labels, keyboard operation, and non-color current context in `client/src/components/ScheduleContextHeader.test.tsx`
- [X] T025 [P] [US2] Add failing page tests for mutually exclusive exposed Calendar/Versions/Exams regions, no vertically stacked lifecycle/exam content, shared-context propagation, hidden-region focus exclusion, and clean Calendar/pane restoration or invalid-reference recovery in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 2

- [X] T026 [US2] Extend the one primary navigation hierarchy with controlled Schedule expansion, ordered children, sole-current semantics, current-child no-op behavior, and unchanged Academic Data disclosure behavior in `client/src/components/ApplicationNavigation.tsx` (depends on T022)
- [X] T027 [US2] Make `App` own `calendar | versions | exams`, default Calendar, child-navigation requests committed only through the existing page approval handshake, mounted Schedule content, and destination-focus handoff without adding routing, a global store, or a second pending intent in `client/src/App.tsx` (depends on T017, T018, T023, T026)
- [X] T028 [P] [US2] Implement the controlled compact semester/revision/course context surface and explicit unavailable-context recovery in `client/src/components/ScheduleContextHeader.tsx` (depends on T024)
- [X] T029 [US2] Accept the controlled destination, route requested child changes through the single pending-intent owner, render the shared context header, and place Calendar, lifecycle, and exam compositions in mounted but mutually hidden/inert workspace wrappers from the one existing data owner in `client/src/pages/CourseSchedulePage.tsx` (depends on T017, T025, T027, T028)
- [X] T030 [US2] Reconcile retained clean Calendar mode/period/filters/selection/pane/scroll position before restoration, focus the committed workspace start, and prevent hidden workspace controls from retaining focus in `client/src/pages/CourseSchedulePage.tsx` and `client/src/components/CalendarPlanningWorkspace.tsx` (depends on T016, T017, T025, T029)
- [X] T031 [US2] Add Schedule parent/child hierarchy, compact context header, current workspace heading, mutually hidden wrapper, and focused content sizing styles in `client/src/App.css` (depends on T026-T030)
- [X] T032 [US2] Run the focused navigation, application, context-header, Calendar, and page suites and record default/current semantics, three-child round trips within the two-action limit, context propagation, clean restoration, hidden-region exclusion, and no-mutation evidence in `specs/019-streamline-schedule-workspace/validation/us2-focused-schedule.md`

**Checkpoint**: Both P1 stories pass: session correction stays in Calendar and the three focused Schedule destinations are reachable with consistent context.

---

## Phase 5: User Story 3 - Reclaim Workspace Width (Priority: P2)

**Goal**: Independently unpin wide application navigation and hide Calendar Planning inputs without losing destination, context, pane, or edit state.

**Independent Test**: At a wide viewport, unpin/reopen/pin navigation, hide/show Planning inputs, reload on the same device, and cross narrow/wide presentations while verifying each control changes only its own surface and preserves Schedule and edit context.

### Tests for User Story 3 (write before implementation)

- [X] T033 [P] [US3] Add failing component tests for wide-only Pin/Unpin controls, the labeled unpinned opener, a wide temporary modal left overlay with backdrop/focus containment/Escape-close restoration/background inert state, pin-to-persistent conversion, narrow omission of pin controls, retained hierarchy/current state, and breakpoint cleanup in `client/src/components/ApplicationNavigation.test.tsx`
- [X] T034 [P] [US3] Add failing application tests for default/valid/invalid/throwing localStorage reads and writes, persisted wide pin restoration, narrow transitions retaining the stored choice, reclaimed shell state, and unchanged destination/pane context in `client/src/App.test.tsx`
- [X] T035 [P] [US3] Add failing page tests for independently hidden/shown Planning inputs, retained compact header, nonpersistence, and preservation of course/semester/revision/Calendar/pane/dirty state in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T036 [US3] Separate controlled wide pin/open behavior from the existing narrow temporary-panel state; implement the wide unpinned opener as a temporary modal left overlay with backdrop, focus containment, Escape/close restoration, background blocking, and Pin-to-persistent conversion; and omit pin actions at the established narrow presentation in `client/src/components/ApplicationNavigation.tsx` (depends on T033)
- [X] T037 [US3] Add exception-safe `resource-planner.navigation.pinned.v1` read/write helpers, default-pinned behavior, independent navigation pinned/open state, and shell data/class state without persisting any workspace value in `client/src/App.tsx` (depends on T034, T036)
- [X] T038 [US3] Add nonpersisted Planning-input visibility state and labeled hide/show controls that leave the shared header and pane/edit state untouched in `client/src/pages/CourseSchedulePage.tsx` (depends on T035)
- [X] T039 [US3] Implement pinned/unpinned wide shell columns, compact opener placement, wide temporary-overlay/backdrop/inert presentation, independent Planning-input collapse, responsive transitions, and width reclamation without pane remount in `client/src/App.css` (depends on T037, T038)
- [X] T040 [US3] Run the focused navigation, application, and page suites and record storage fallback, same-device restoration, wide temporary-overlay modal/focus/background behavior, narrow pin omission, pin-to-persistent conversion, responsive transitions, independent surface visibility, reclaimed layout state, and retained edit-context evidence in `specs/019-streamline-schedule-workspace/validation/us3-reclaim-width.md`

**Checkpoint**: Navigation and Planning inputs can be controlled independently, and only the valid wide pin preference persists.

---

## Phase 6: User Story 4 - Manage Versions in a Dedicated Workspace (Priority: P2)

**Goal**: Manage Working and Current Published revisions, lifecycle actions, and complete ordered history in a focused, content-sized Versions workspace.

**Independent Test**: Open Versions for no-revision, Working-only, Published-only, and combined states; disclose history on demand; complete/cancel permitted actions; and exercise stale/rejected/failure refresh while Calendar and Exams remain absent.

### Tests for User Story 4 (write before implementation)

- [X] T041 [P] [US4] Add failing tests for no-revision, Working-only, Published-only, combined designations, stable identities, permitted actions, complete ordered history disclosure, collapsed-by-default details, stale/rejected/failure refresh, and content-sized semantics in `client/src/components/ScheduleLifecyclePanel.test.tsx`
- [X] T042 [P] [US4] Add failing page tests for the focused Versions composition, Start Draft, review/publish/abandon/restore confirmation wiring, lifecycle feedback ownership, shared semester/revision context, and absence of exposed Calendar/Exams content in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 4

- [X] T043 [US4] Present Working and Current Published summaries, empty-state action, stable revision identities, and complete per-revision ordered event history through on-demand disclosure while retaining all existing lifecycle callbacks in `client/src/components/ScheduleLifecyclePanel.tsx` (depends on T041)
- [X] T044 [US4] Move lifecycle composition, pending confirmations, refresh/error feedback, and no-revision recovery into the focused Versions region without changing existing API handlers in `client/src/pages/CourseSchedulePage.tsx` (depends on T042, T043)
- [X] T045 [US4] Add content-sized Versions cards, nonstretching layout, readable designation/action hierarchy, and accessible history-disclosure styles in `client/src/App.css` (depends on T043, T044)
- [X] T046 [US4] Run the focused lifecycle panel/page suites and record empty/working/published/both, disclosure ordering, action parity, stale/rejected/failure, and no-stacked-content evidence in `specs/019-streamline-schedule-workspace/validation/us4-versions.md`

**Checkpoint**: Versions independently preserves every FS-013 lifecycle outcome while removing its oversized permanent Calendar placement.

---

## Phase 7: User Story 5 - Prepare Exams in a Dedicated Workspace (Priority: P2)

**Goal**: Configure requirements, distinguish eligible from unavailable courses, retain visible selection/action context, and prepare exams in a focused workspace.

**Independent Test**: Use a semester with eligible, active-exam, and otherwise unavailable courses; review/configure requirements, select eligible courses, prepare exams, and verify grouped reasons, selected count/action visibility, confirmation, partial result, and stale behavior without Calendar or complete Versions content.

### Tests for User Story 5 (write before implementation)

- [X] T047 [P] [US5] Add failing tests for authoritative `generationEligibility.eligible` selectability, eligible-first/unavailable grouping, exact unavailability reasons, selection pruning after refresh, selected count/action context outside the list, empty-selection explanation, and prepare/result parity in `client/src/components/ExamGenerationPanel.test.tsx`
- [X] T048 [P] [US5] Add failing tests for focused requirement review/edit, active-exam read-only behavior, recommendation/override validation, responsible lecturer, save/cancel feedback, and selected-course context callbacks in `client/src/components/ExamRequirementEditor.test.tsx`
- [X] T049 [P] [US5] Add failing page tests for the dedicated Exams composition, selected requirement course, manual placement, constraints, prepare/confirmation/generate, per-course partial results, stale refresh, active-exam exclusion, mounted selection retention, and absence of exposed Calendar/complete Versions content in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 5

- [X] T050 [US5] Determine selectability from the authoritative eligibility boolean, render eligible and unavailable groups with exact reasons, prune invalid selections with an announcement, and keep selected count/constraints/action context outside the scrolling list in `client/src/components/ExamGenerationPanel.tsx` (depends on T047)
- [X] T051 [P] [US5] Adapt requirement review/edit composition to controlled selected-course context and focused Exams feedback without changing exam requirement payloads or rules in `client/src/components/ExamRequirementEditor.tsx` (depends on T048)
- [X] T052 [US5] Compose requirements, manual placement, constraints, eligibility selection, preparation confirmation, generation, and per-course results in the mounted focused Exams region using existing state/API handlers in `client/src/pages/CourseSchedulePage.tsx` (depends on T049-T051)
- [X] T053 [US5] Add eligible/unavailable group hierarchy, internally scrolling course list, sticky/reachable action context, empty-state explanation, long-label wrapping, and narrow/zoom-safe Exams styles in `client/src/App.css` (depends on T050-T052)
- [X] T054 [US5] Run the focused exam requirement/generation/page suites and record grouping/selectability, reasons, selection pruning, action visibility, requirement/manual placement, confirmation/partial-result/stale, and no-stacked-content evidence in `specs/019-streamline-schedule-workspace/validation/us5-exams.md`

**Checkpoint**: Exams independently preserves every FS-012 rule and result while making available work and the next action immediately understandable.

---

## Phase 8: Polish, Documentation, and Cross-Cutting Verification

**Purpose**: Complete regression, responsive/accessibility, usability, documentation, and final constitution/scope evidence across the delivered slice.

- [X] T055 [P] Update Schedule navigation, focused workspaces, pane editing, pinning, Planning-input visibility, responsive behavior, and the unchanged backend/API boundary in `client/README.md`
- [X] T056 [P] Run the targeted and complete backend pytest commands from `quickstart.md` and record versions, commands, passing counts, durations, warnings, and unchanged calendar/draft/exam/lifecycle contract evidence in `specs/019-streamline-schedule-workspace/validation/backend-regression.md`
- [X] T057 Run every focused client command and complete `npm test` from `quickstart.md`, then record failing-first references, passing counts, durations, warnings, and deliberate List/Academic Data regression evidence in `specs/019-streamline-schedule-workspace/validation/client-test-results.md`
- [X] T058 Run `npm run lint` and `npm run build` from `client/` and record versions, commands, durations, warnings, and outcomes in `specs/019-streamline-schedule-workspace/validation/client-quality-results.md`
- [ ] T059 [P] **BLOCKED (manual acceptance remainder)** Execute all ten `quickstart.md` browser scenarios across wide pinned and the wide unpinned temporary modal overlay, the 70rem docked/overlay container boundary, the 820px full-screen boundary, 320px, and 200% zoom; record Calendar scroll position before and after pane open/edit/cancel/save/close, verify the two-action session-edit and Schedule-destination limits plus keyboard/focus/inert/long-label behavior with NVDA and Firefox, and record versions, screenshots, announcements, focus restoration, action counts, and outcomes in `specs/019-streamline-schedule-workspace/validation/schedule-workspace-acceptance.md`
- [ ] T060 [P] **BLOCKED (external reviewers unavailable)** Conduct the SC-003/SC-005 review with at least 10 product-owner-provided representative planners or designated acceptance reviewers and record anonymized roles, protocol, first-attempt correction/navigation results, aggregate percentages, and pass/fail outcome in `specs/019-streamline-schedule-workspace/validation/usability-review.md`; mark the task blocked rather than fabricating results if reviewers are unavailable
- [ ] T061 **BLOCKED by T059-T060** Compare the final diff and verification evidence with `specs/019-streamline-schedule-workspace/spec.md`, `specs/019-streamline-schedule-workspace/plan.md`, `specs/019-streamline-schedule-workspace/data-model.md`, and `specs/019-streamline-schedule-workspace/contracts/schedule-workspace-ui.md`; confirm every FR/TR/SC is covered, no backend/API/router/dependency/domain-rule expansion occurred, all constitution gates still pass, and record the final result in `specs/019-streamline-schedule-workspace/validation/final-review.md` (depends on T055-T060)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 - Setup**: No dependency; complete before production edits.
- **Phase 2 - Foundation**: Depends on T001 and blocks every story because Calendar refresh currently destroys state required by US1 and US2.
- **Phase 3 - US1**: Depends on Foundation and delivers the recommended MVP.
- **Phase 4 - US2**: Its navigation/context tests can be prepared after Foundation, but T027-T030 explicitly depend on US1's single pending-intent and pane-restoration contract.
- **Phase 5 - US3**: Depends on US1 and US2 because it must preserve their pane, destination, and shell state while reclaiming width.
- **Phase 6 - US4**: Depends on US2's focused workspace shell, but not on US3.
- **Phase 7 - US5**: Depends on US2's focused workspace shell, but not on US3 or US4.
- **Phase 8 - Polish**: Depends on all selected stories. Independent documentation, backend regression, browser acceptance, and usability evidence may run in parallel before final review.

### User Story Dependencies

```text
Setup
  |
  v
Calendar state foundation
  |\
  | +--> US1: In-pane teaching/exam correction (MVP)
  | |       \
  | +--------+--> US2: Focused Schedule destinations
  |                  |\
  |                  | +--> US3: Reclaim workspace width
  |                  | +--> US4: Focused Versions
  |                  | `--> US5: Focused Exams
  |                  |
  `------------------'
```

- **US1 (P1)**: Starts after Foundation and is independently demonstrable on the existing Calendar destination.
- **US2 (P1)**: Starts after Foundation; its hierarchy/composition work is independently testable, while final dirty/clean pane transitions integrate with US1.
- **US3 (P2)**: Uses US1 pane state and US2 shell/destination state, but is independently verified through pin/input visibility behavior.
- **US4 (P2)**: Uses only the US2 focused workspace shell and remains independently verifiable through lifecycle states/actions.
- **US5 (P2)**: Uses only the US2 focused workspace shell and remains independently verifiable through exam eligibility/preparation states.

### Within Each User Story

- Write the story's failing automated tests and confirm the intended failure before its production tasks.
- Implement extracted field/view-model seams before components that consume them.
- Implement component semantics and state before application/page integration.
- Integrate production behavior before CSS presentation.
- Run focused tests and record story evidence before crossing the checkpoint.
- Do not alter FastAPI production files, HTTP schemas, persistence models, lifecycle states, exam eligibility rules, scheduling validation, routing, or runtime dependencies.

### Parallel Opportunities

- In Foundation, T002 and T003 can be written in parallel in separate test files.
- In US1, T006-T011 are separate test tracks; T012-T014 are separate production files after their tests.
- In US2, T022-T025 are separate test tracks; T022 covers only Schedule child/current semantics at narrow sizes, while temporary navigation focus/backdrop behavior remains in T033; T028 can proceed independently after T024 while navigation work proceeds.
- In US3, T033-T035 are separate test tracks.
- US4 and US5 can run in parallel after US2 because they primarily change separate lifecycle and exam components; coordinate their small integrations in `CourseSchedulePage.tsx` and `App.css`.
- In Polish, T055, T056, T059, and T060 produce independent files/evidence.

---

## Parallel Example: User Story 1

```text
Task T006: Create failing pane/dirty-dialog tests in client/src/components/SessionPane.test.tsx and client/src/components/DiscardChangesDialog.test.tsx
Task T007: Create failing teaching editor/List parity tests in client/src/components/DraftSchedulePanel.test.tsx
Task T008: Create failing controlled exam editor tests in client/src/components/ExamManualSessionEditor.test.tsx
Task T009: Create failing no-List/selection/focus tests in client/src/components/CalendarPlanningWorkspace.test.tsx
Task T010: Create failing pane orchestration/save/stale tests in client/src/pages/CourseSchedulePage.test.tsx
Task T011: Create failing dirty top-level navigation tests in client/src/App.test.tsx
```

## Parallel Example: User Story 2

```text
Task T022: Create failing Schedule hierarchy tests in client/src/components/ApplicationNavigation.test.tsx
Task T023: Create failing destination/application integration tests in client/src/App.test.tsx
Task T024: Create failing context-header tests in client/src/components/ScheduleContextHeader.test.tsx
Task T025: Create failing focused-workspace/restoration tests in client/src/pages/CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 3

```text
Task T033: Create failing wide pin/narrow navigation tests in client/src/components/ApplicationNavigation.test.tsx
Task T034: Create failing pin persistence/shell tests in client/src/App.test.tsx
Task T035: Create failing Planning-input independence tests in client/src/pages/CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 4

```text
Task T041: Create failing lifecycle states/history/action tests in client/src/components/ScheduleLifecyclePanel.test.tsx
Task T042: Create failing focused Versions integration tests in client/src/pages/CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 5

```text
Task T047: Create failing eligibility/grouping/action tests in client/src/components/ExamGenerationPanel.test.tsx
Task T048: Create failing requirement-context tests in client/src/components/ExamRequirementEditor.test.tsx
Task T049: Create failing focused Exams integration tests in client/src/pages/CourseSchedulePage.test.tsx
```

---

## Implementation Strategy

### MVP First - User Story 1

1. Complete Setup and the Calendar state foundation.
2. Write and confirm all US1 failing tests.
3. Extract/reuse the established teaching and exam editors.
4. Implement the one controlled adaptive pane and dirty-intent guard.
5. Stop at T021 and independently validate teaching/exam correction without List-mode or Calendar-context loss.
6. Demo the pane MVP before changing the broader Schedule information architecture.

### Incremental Delivery

1. **Foundation**: Calendar state survives coherent refresh and invalid references reconcile accurately.
2. **US1**: Teaching and exam detail/edit stay in Calendar - MVP.
3. **US2**: Calendar, Versions, and Exams become focused Schedule destinations.
4. **US3**: Wide navigation and Planning inputs reclaim width independently.
5. **US4**: Lifecycle governance becomes a focused, content-sized workspace.
6. **US5**: Exam preparation becomes eligibility-first with persistent action context.
7. **Polish**: Run complete regression, responsive/accessibility, usability, and scope gates.

### Parallel Team Strategy

1. One owner completes T001 and the Foundation checkpoint.
2. After Foundation, pane/editor work for US1 and navigation/context tests for US2 may be prepared in parallel, but integrate US1 before US2's final dirty/clean pane transitions.
3. After US2, separate owners can implement US4 and US5 in parallel; one owner coordinates the shared `CourseSchedulePage.tsx` and `App.css` integrations.
4. Implement US3 once pane and navigation state are stable so pin/visibility changes can prove they preserve both.
5. Parallelize documentation, backend regression, manual browser/AT evidence, and external usability evidence before the final review.

---

## Notes

- Tasks marked [P] change different files or produce independent evidence once explicit prerequisites are satisfied.
- Story labels map directly to the five user stories in `spec.md`.
- `CourseSchedulePage` remains the single schedule data/mutation owner; do not create per-destination service owners.
- The new shared production seams are limited to `ScheduleContextHeader`, `SessionPane`, `DiscardChangesDialog`, `TeachingSessionEditor`, and `sessionEditModel`, each justified by current multi-destination or multi-editor use in `plan.md`.
- Only `resource-planner.navigation.pinned.v1` may be newly persisted; never persist pane drafts, filters, workspace context, destination, or Planning-input visibility.
- No backend production, migration, HTTP contract, router, state-library, generic session API, lifecycle-rule, eligibility-rule, or unrelated design-system task belongs to FS-019.
- Preserve pre-existing user changes and stop if implementation overlaps them unexpectedly.
- Commit only after relevant focused and complete verification passes; use the isolated feature branch for this customer-facing change.
