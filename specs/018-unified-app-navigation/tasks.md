# Tasks: FS-018 Unified Application Navigation

**Input**: Design documents from `specs/018-unified-app-navigation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/application-navigation.md`, `quickstart.md`

**Tests**: Tests are required by the project constitution and FS-018 TR-001 through TR-009. Each automatable story behavior has a failing test task before the corresponding production task; visual layout and rendered contrast are covered by the bounded browser acceptance matrix.

**Organization**: Tasks are grouped by user story so the hierarchy MVP, location context, keyboard accessibility, and narrow-screen access can be implemented and verified incrementally.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its stated prerequisites because it changes a different file or produces independent evidence
- **[Story]**: Maps a task to one specification user story
- Every task names the exact file it creates or changes

## Phase 1: Setup and Baseline

**Purpose**: Isolate the customer-facing implementation and preserve evidence of the known-good client baseline.

- [ ] T001 Record the isolated implementation branch/worktree, pre-existing change boundaries, locked client versions, and the passing 22-test focused baseline command in `specs/018-unified-app-navigation/validation/pre-implementation.md`

---

## Phase 2: Foundational Page-Shell Extraction

**Purpose**: Make the two existing workflows content-only and make Academic Data category selection controllable by the future application shell without changing domain behavior.

**CRITICAL**: Complete this phase before any user-story implementation. Write and observe each focused test fail before its paired production change.

- [ ] T002 [P] Add failing characterization tests for externally selected Academic Data categories, category-transition editor/resource cleanup, existing category loading, and absence of page-local category navigation in `client/src/pages/AcademicDataPage.test.tsx`
- [ ] T003 [P] Define the shared Academic Data category type/fixed metadata in `client/src/components/ApplicationNavigation.tsx`, then make `AcademicDataPage` consume that type as controlled selection, preserve current category-transition cleanup/loading, and return content/dialogs without its own shell/sidebar in `client/src/pages/AcademicDataPage.tsx` (depends on T002)
- [ ] T004 [P] Add failing characterization tests proving the Schedule workflow renders without Dashboard/Courses/Cohorts/Rooms/Schedule hash navigation and retains existing scheduling behavior in `client/src/pages/CourseSchedulePage.test.tsx`
- [ ] T005 [P] Return the existing Schedule workbench/dialog content without its page-owned application shell or dead hash-link sidebar in `client/src/pages/CourseSchedulePage.tsx` (depends on T004)

**Checkpoint**: Both workflows are content-only, Academic Data can be driven by a shared category value, and their focused page tests pass without backend/API changes.

---

## Phase 3: User Story 1 — Navigate Through One Application Hierarchy (Priority: P1) MVP

**Goal**: Replace all competing navigation with one application-owned hierarchy that reaches Schedule and the seven ordered Academic Data categories.

**Independent Test**: Start on Schedule, use only the shared navigation to expand Academic Data, visit Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms in order, and return to Schedule; verify the fixed switcher, dead links, duplicate navigation, and unavailable placeholders are absent.

### Tests for User Story 1 (write before implementation)

- [ ] T006 [P] [US1] Create failing component tests for the single primary-navigation landmark, Schedule leaf, disclosure-only Academic Data parent, exact seven-child label/order contract, expansion without navigation, child selection, and omission of unavailable children in `client/src/components/ApplicationNavigation.test.tsx`
- [ ] T007 [P] [US1] Replace the fixed-switcher test with failing application integration tests for initial Schedule content, all eight reachable leaf destinations, correct controlled Academic Data category content, Schedule remaining mounted, catalog-revision refresh, and absence of duplicate/dead navigation in `client/src/App.test.tsx`

### Implementation for User Story 1

- [ ] T008 [US1] Extend the foundational Academic Data metadata into the basic shared hierarchy with Schedule selection, disclosure-only Academic Data expansion, child selection, availability filtering, and one primary-navigation landmark in `client/src/components/ApplicationNavigation.tsx` (depends on T003, T006)
- [ ] T009 [US1] Make `App` own current view, selected Academic Data category, and expansion state; render one application shell/navigation around the content-only pages; retain the mounted Schedule/catalog-revision behavior; and remove the fixed top switcher in `client/src/App.tsx` (depends on T003, T005, T007, T008)
- [ ] T010 [US1] Replace `.view-navigation` and page-local shell/sidebar styling with the authoritative persistent wide two-column application shell and ordered child hierarchy while preserving existing workbench/header/content styles in `client/src/App.css` (depends on T009)
- [ ] T011 [US1] Run the focused US1 component, application, and page suites and record the command output plus hierarchy/dead-link assertions in `specs/018-unified-app-navigation/validation/us1-single-hierarchy.md`

**Checkpoint**: User Story 1 is a demonstrable MVP—one wide sidebar reaches all eight leaves and no competing or dead primary navigation remains.

---

## Phase 4: User Story 2 — Understand Current Location (Priority: P2)

**Goal**: Keep exactly one current leaf plus visible Academic Data parent/child context, with expansion persistence and non-color location indicators.

**Independent Test**: Open Schedule and every Academic Data category; verify the correct sole semantic current leaf, active Academic Data parent, visible current child, initial/retained expansion behavior, collapse refusal for an active child, and stable repeated-current selection.

### Tests for User Story 2 (write before implementation)

- [ ] T012 [P] [US2] Add failing tests for sole `aria-current` leaf semantics, Academic Data active-parent/expanded semantics, initial collapsed Schedule state, forced expansion and collapse refusal for an active child, and focus fallback when a permitted collapse hides children in `client/src/components/ApplicationNavigation.test.tsx`
- [ ] T013 [P] [US2] Add failing integration tests for selected-category and expansion persistence across Schedule round trips, automatic expansion on Academic child selection, and no state/domain-request reset when the current leaf is selected again in `client/src/App.test.tsx`

### Implementation for User Story 2

- [ ] T014 [US2] Implement sole-current-leaf semantics, active-parent state, forced expansion for Academic content, permitted Schedule-only collapse, and disclosure focus fallback in `client/src/components/ApplicationNavigation.tsx` (depends on T012)
- [ ] T015 [US2] Implement retained permitted expansion/category state and repeated-current-leaf no-op behavior in `client/src/App.tsx` (depends on T013, T014)
- [ ] T016 [US2] Add distinct active-parent, current-leaf, expanded-child-rail, and non-color marker treatments that remain distinguishable from hover and preserve the ground-truth hierarchy in `client/src/App.css` (depends on T014)
- [ ] T017 [US2] Run the focused US2 semantic/state suites and record current-leaf counts, expanded-state assertions, round-trip persistence, and repeated-selection results in `specs/018-unified-app-navigation/validation/us2-location-context.md`

**Checkpoint**: User Stories 1 and 2 independently pass; every view exposes one unambiguous current leaf and Academic Data retains visible parent/child context.

---

## Phase 5: User Story 3 — Navigate with a Keyboard and Assistive Technology (Priority: P2)

**Goal**: Operate the complete hierarchy without a pointer and provide predictable focus, semantic expansion/current states, and destination focus handoff.

**Independent Test**: Traverse and activate every visible navigation control by keyboard, expand/collapse Academic Data, select a different destination, inspect the navigation/current/expanded semantics, and confirm visible focus never enters hidden content or disappears.

### Tests for User Story 3 (write before implementation)

- [ ] T018 [P] [US3] Add failing keyboard tests for native disclosure/leaf activation, logical forward/reverse traversal, exclusion of collapsed children, focus movement to Academic Data before child collapse, and no hidden focused item in `client/src/components/ApplicationNavigation.test.tsx`
- [ ] T019 [P] [US3] Add failing application tests for focus moving to the shared content start after a different leaf selection, no content jump for repeated-current selection, and valid focus after Schedule/Academic content changes in `client/src/App.test.tsx`

### Implementation for User Story 3

- [ ] T020 [US3] Complete keyboard-safe disclosure and child visibility focus handling using native controls and direct focus management in `client/src/components/ApplicationNavigation.tsx` (depends on T018)
- [ ] T021 [US3] Add the programmatically focusable current-content target and actual-destination-change focus handoff without remounting Schedule or resetting page state in `client/src/App.tsx` (depends on T019, T020)
- [ ] T022 [US3] Add a focus indicator visually distinct from current/active states and capable of the specified 3:1 adjacent-color contrast in all hierarchy states in `client/src/App.css` (depends on T020)
- [ ] T023 [US3] Run the focused keyboard/assistive-technology suites and record traversal, semantic-tree, destination-handoff, hidden-focus, and repeated-selection results in `specs/018-unified-app-navigation/validation/us3-keyboard-accessibility.md`

**Checkpoint**: User Stories 1–3 pass with complete keyboard access, correct semantic state, and predictable focus behavior in the wide presentation.

---

## Phase 6: User Story 4 — Reach Every Destination on a Narrow Screen (Priority: P3)

**Goal**: Present the same hierarchy as a temporary narrow overlay with contained focus, complete dismissal behavior, preserved state, and unobstructed page controls.

**Independent Test**: At and below 820px, open the panel, reach all eight leaves, cycle focus in both directions, dismiss with Escape and explicit close, select a destination, cross repeatedly to wide presentation, and verify state/focus plus all page-header controls remain valid.

### Tests for User Story 4 (write before implementation)

- [ ] T024 [P] [US4] Add failing narrow-panel tests for the labeled opener, named modal panel, initial focus, Tab/Shift+Tab containment, Escape/explicit-close restoration, leaf-selection dismissal, current-leaf dismissal, and resize-to-wide cleanup in `client/src/components/ApplicationNavigation.test.tsx`
- [ ] T025 [P] [US4] Add failing application integration tests for background interaction blocking while open, content focus after narrow leaf selection, and destination/category/expansion preservation across mocked 820px responsive transitions in `client/src/App.test.tsx`

### Implementation for User Story 4

- [ ] T026 [US4] Implement the narrow opener/panel, modal naming, opener restoration, direct focus loop, Escape/close/selection dismissal, and existing-820px media-transition cleanup in `client/src/components/ApplicationNavigation.tsx` (depends on T024)
- [ ] T027 [US4] Integrate temporary-panel open state with application content interaction blocking and destination focus handoff while preserving shared navigation state in `client/src/App.tsx` (depends on T025, T026)
- [ ] T028 [US4] Implement the 820px-and-below fixed overlay/backdrop, hidden-when-closed sidebar, visible narrow opener, scrollable 320px-safe hierarchy, header/control reflow, and removal of the former stacked-sidebar behavior in `client/src/App.css` (depends on T026, T027)
- [ ] T029 [US4] Run the focused responsive component/application suites and record panel semantics, focus containment/restoration, background blocking, selection dismissal, and repeated breakpoint-transition results in `specs/018-unified-app-navigation/validation/us4-responsive-access.md`

**Checkpoint**: All four user stories independently pass; wide and narrow presentations expose one consistent hierarchy and preserve state/focus without header overlap.

---

## Phase 7: Polish, Documentation, and Cross-Cutting Verification

**Purpose**: Complete visual, usability, regression, documentation, scope, and constitution evidence across the delivered slice.

- [ ] T030 [P] Update navigation, responsive access, keyboard behavior, and the unchanged backend/API boundary while removing obsolete fixed-switcher/sidebar wording in `client/README.md`
- [ ] T031 [P] Execute all six `quickstart.md` browser scenarios at wide, 820px, 320px, and 200% text zoom; measure 3:1 focus contrast; inspect accessibility semantics; verify long Schedule and Academic Data headers; and record screenshots/results in `specs/018-unified-app-navigation/validation/navigation-acceptance.md`
- [ ] T032 [P] Conduct the SC-003/SC-004 unaided review with at least 10 representative planners or acceptance reviewers and record first-attempt navigation plus five-second location-identification outcomes in `specs/018-unified-app-navigation/validation/usability-review.md`
- [ ] T033 Run `npm test -- src/components/ApplicationNavigation.test.tsx src/App.test.tsx`, both focused page suites, and the complete `npm test` command from `client/`, then record passing counts and FS-007/FS-008 regression evidence in `specs/018-unified-app-navigation/validation/client-test-results.md`
- [ ] T034 Run `npm run lint` and `npm run build` from `client/` and record commands, versions, durations, warnings, and final outcomes in `specs/018-unified-app-navigation/validation/client-quality-results.md`
- [ ] T035 Compare the final diff with `spec.md`, `plan.md`, `contracts/application-navigation.md`, the authoritative image, and the Simplicity Check; confirm no backend/API/domain/routing/dependency changes or unavailable destinations were introduced; and record the final constitution/scope review in `specs/018-unified-app-navigation/validation/final-review.md` (depends on T030–T034)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: No dependency; complete before production changes.
- **Phase 2 — Foundation**: Depends on T001 and blocks every user story. T002/T003 and T004/T005 are independent page tracks.
- **Phase 3 — US1**: Depends on Phase 2 and creates the shared hierarchy/application shell used by later stories.
- **Phase 4 — US2**: Depends on US1's hierarchy; location context remains independently testable.
- **Phase 5 — US3**: Depends on US1's hierarchy but can be developed in parallel with US2 by separate owners only if same-file coordination is explicit; keyboard behavior remains independently testable.
- **Phase 6 — US4**: Depends on US1 plus the state semantics from US2 and focus behavior from US3.
- **Phase 7 — Polish**: Depends on all selected user stories; T030–T032 can proceed in parallel before the final automated/quality/scope evidence T033–T035.

### User Story Dependencies

```text
Foundation
    |
    v
US1: Single hierarchy (MVP)
    |\
    | +--> US2: Location context
    | +--> US3: Keyboard/accessibility
    |          \
    +-----------+--> US4: Narrow responsive access
```

- **US1 (P1)**: Starts after Foundation and has no dependency on another story.
- **US2 (P2)**: Uses the US1 hierarchy but can be demonstrated independently by opening each leaf and inspecting current/parent/expansion state.
- **US3 (P2)**: Uses the US1 hierarchy but can be demonstrated independently with keyboard-only traversal and focus/semantic inspection.
- **US4 (P3)**: Uses the US1 hierarchy, US2 state rules, and US3 focus rules to expose the same contract in a temporary panel.

### Within Each User Story

- Write the story's failing automated tests before its production tasks and confirm the intended failure.
- Implement component behavior before wiring application-level state/focus that consumes it.
- Complete CSS only after the corresponding semantic/interaction state exists.
- Run and record focused story verification before crossing the phase checkpoint.
- Do not change backend files, HTTP contracts, domain records, routing, dependencies, or unrelated page content.

### Parallel Opportunities

- In Foundation, T002/T003 (Academic Data) can run independently of T004/T005 (Schedule), with each production task following its own test.
- In US1, T006 and T007 can be written in parallel because they target component and application integration files.
- In US2, T012 and T013 can be written in parallel for the same reason.
- In US3, T018 and T019 can be written in parallel for the same reason.
- In US4, T024 and T025 can be written in parallel for the same reason.
- After all stories, T030 documentation, T031 browser acceptance, and T032 usability review produce separate files and can run in parallel.

---

## Parallel Example: User Story 1

```text
Task T006: Create failing hierarchy/disclosure contract tests in client/src/components/ApplicationNavigation.test.tsx
Task T007: Create failing cross-view application integration tests in client/src/App.test.tsx
```

## Parallel Example: User Story 2

```text
Task T012: Create failing current/active/expansion component tests in client/src/components/ApplicationNavigation.test.tsx
Task T013: Create failing persistence/no-op integration tests in client/src/App.test.tsx
```

## Parallel Example: User Story 3

```text
Task T018: Create failing keyboard/disclosure focus tests in client/src/components/ApplicationNavigation.test.tsx
Task T019: Create failing destination content-focus tests in client/src/App.test.tsx
```

## Parallel Example: User Story 4

```text
Task T024: Create failing narrow modal/focus/resize tests in client/src/components/ApplicationNavigation.test.tsx
Task T025: Create failing background-blocking/state-preservation tests in client/src/App.test.tsx
```

---

## Implementation Strategy

### MVP First — User Story 1

1. Complete Setup and the two Foundation page tracks.
2. Write US1 component and application tests and confirm they fail for the missing shared hierarchy.
3. Implement the single application shell, disclosure hierarchy, controlled category, and wide layout.
4. Stop at T011 and validate that all eight leaves work without duplicate/dead navigation.
5. Demo the independently useful wide-navigation MVP before adding location/accessibility refinements.

### Incremental Delivery

1. **Foundation**: Existing pages become content-only with protected workflow behavior.
2. **US1**: One hierarchy reaches every existing destination—MVP.
3. **US2**: Current parent/child context and expansion persistence become unambiguous.
4. **US3**: Keyboard and assistive-technology behavior complete wide accessibility.
5. **US4**: The same contract becomes available through the narrow temporary panel.
6. **Polish**: Run the full matrix, usability review, regression suite, lint/build, and scope gate.

### Parallel Team Strategy

1. One owner completes T001.
2. Two owners can complete the Academic Data and Schedule Foundation tracks independently.
3. After Foundation, pair component-test/implementation ownership with App integration-test/implementation ownership, coordinating the two shared files at each story checkpoint.
4. US2 and US3 may be prepared in parallel but should integrate sequentially to avoid conflicting edits to `ApplicationNavigation.tsx`, `App.tsx`, and their tests.
5. Run US4 after both state and focus contracts are stable; parallelize final documentation, browser evidence, and usability evidence.

---

## Notes

- Tasks marked [P] change different files or produce independent evidence once their explicit prerequisites are satisfied.
- Story labels map directly to the four user stories in `spec.md`.
- No backend, migration, API-contract, router, state-library, persistence, Dashboard, or new-category task belongs to FS-018.
- The only new production abstraction is `ApplicationNavigation`, justified in `plan.md` by the shared wide/narrow hierarchy and focus contract.
- Preserve pre-existing user changes and stop if implementation overlaps them unexpectedly.
- Commit only after relevant focused and complete verification passes; use a feature branch for this customer-facing shell change.
