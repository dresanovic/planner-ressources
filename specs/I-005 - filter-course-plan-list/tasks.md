# Tasks: I-005 — Filterable Course Lists for Generation and Administration

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/course-list-contract.md, quickstart.md in this feature directory.
**Tests**: Required by TR-001–006 and the constitution. Write story tests and observe the intended failure before production changes; later verification tasks require green results. All boxes are intentionally unchecked: this document prepares implementation, it does not perform it.
**Format**: `- [ ] Tnnn [P?] [USn?] action with repository-relative path`. Paths with spaces are quoted in commands. No backend production tasks or dependencies are needed for the selected design.

## Phase 1: Setup

**Purpose**: Preserve unrelated work and establish actual baseline commands.

- [X] T001 Review `specs/I-005 - filter-course-plan-list/plan.md` and current git status; create/use a `codex/i-005-filter-course-plan-list` implementation branch or isolated worktree before any production edits, without resetting, committing or discarding unrelated backend work. Record chosen branch/worktree and baseline status in `specs/I-005 - filter-course-plan-list/quickstart.md`.
- [X] T002 Verify installed locked environments using `client/package-lock.json` and `backend/requirements.txt`; run `npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/AcademicDataPage.test.tsx src/App.test.tsx src/api/conflictAwareGeneration.test.ts` from root and the backend regression command in quickstart.md from backend. Record baseline results in `specs/I-005 - filter-course-plan-list/quickstart.md`; install existing locked dependencies only if missing.

## Phase 2: Foundational

**Purpose**: A shared acceptance dataset, with no new production infrastructure.

- [X] T003 Add `client/src/test/fixtures/courseLists.ts` exporting consistent existing CourseOption/CourseRecord-shaped catalogs: 94 courses in 2027 S, exactly eleven target-cohort members, other semester/cohort, empty-match cohort, duplicate labels, unavailable course, null-semester legacy record outside the 94, and enough optional additional records for a multi-page administration case. Preserve these model constraints: `semester is nullable`; `cohortId is nullable; null means all cohorts`; `semesterId is nullable; null means all semesters`; `valid generation selection contains 1–20 distinct course IDs`. Do not alter production schemas or require stored course codes.

**Checkpoint**: Fixture imports/typechecks in each new story test; production state machinery stays story-local.

## Phase 3: User Story 1 — Generation discovery (Priority: P1; MVP)

**Goal**: Isolate eleven courses and explicitly select them within the existing generation workflow.
**Independent test**: Eleven-of-94 membership by cohort ID with no implicit selection; explicit eleven-course selection prepares exactly those IDs.

### Tests first

- [X] T004 [P] [US1] Extend `client/src/components/MultiCourseGenerationPanel.test.tsx` with shared catalog tests for cohort-ID matching, eleven-of-94 count, duplicate labels, reset without selection changes, unavailable reasons/new-selection prevention and exact individual toggles. Filter state constraint: `cohortId is nullable; null means all cohorts`. Cover basic total/hidden selection safety immediately so the MVP never silently drops selected IDs (FR-001–005, FR-007–010; SC-001–003).
- [X] T005 [P] [US1] Extend `client/src/pages/CourseSchedulePage.test.tsx` with selected-semester boundaries, target-cohort selection preparing the complete explicit eleven IDs, no API mutations or generation on filtering, and cancelled versus committed guarded semester changes. Verify no edit/revision guard is bypassed (FR-002, FR-007–008, FR-011; SC-001, SC-007).

### Implementation and verification

- [X] T006 [US1] After T004/T005 fail for intended behavior, add controlled cohort choice, labelled filter/reset, matching count, course/cohort identity and available distinguishing ID fallback in `client/src/components/MultiCourseGenerationPanel.tsx`. Derive visible courses from full input, preserve complete selected IDs/count and existing 20-total cap, disable newly unavailable selections with reasons while permitting existing selection removal when allowed. Do not add search/grouping/bulk selection (FR-001–005, FR-007–010).
- [X] T007 [US1] Own generation cohort choice above the conditional panel in `client/src/pages/CourseSchedulePage.tsx`, pass complete semesterCourses and semester identity, reset cohort only inside committed semester transition, and leave startBatch/prepare payload construction and captured evidence unchanged (FR-002, FR-008, FR-011, FR-014).
- [X] T008 [US1] In `client/src/components/MultiCourseGenerationPanel.tsx`, expose a minimal complete-selection review and hidden count from the first increment, including missing selected IDs with explicit unavailable identity fallback; keep reset separate from clear-selection and never intersect IDs with visible results (FR-005, FR-007–010).
- [X] T009 [US1] Run `npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/api/conflictAwareGeneration.test.ts` from root and record passing MVP evidence in `specs/I-005 - filter-course-plan-list/quickstart.md` before continuing.

## Phase 4: User Story 2 — Administration discovery (Priority: P1)

**Goal**: Scope Academic Data to semester/cohort and open an exact existing course action.
**Independent test**: Isolate the eleven courses; status intersects semester/cohort, all pages are considered, existing edit target/value remains unchanged.

### Tests first

- [X] T010 [P] [US2] Extend `client/src/pages/AcademicDataPage.test.tsx` for eleven-of-94 matching, all-semester/null-semester access, status intersection, matches beyond page one, exact record actions, metadata distinctions, no filter-triggered mutation, and preservation of open editor unsaved values/options. Include `semester is nullable` and `semesterId is nullable; null means all semesters` cases (FR-001–004, FR-007, FR-012; SC-001, SC-007).
- [X] T011 [P] [US2] Extend `client/src/App.test.tsx` with mocked controlled admin filter props to verify independent admin semester/cohort state survives page unmount/remount and category round trips, resets on scope change/reload, and never changes generation or calendar filters. Use `cohortId is nullable; null means all cohorts` (FR-013–014; SC-009).

### Implementation and verification

- [X] T012 [US2] After T010/T011 fail, add App-owned administration semester/cohort state and ordinary callbacks in `client/src/App.tsx`, pass them into AcademicDataPage, retain semester scope for same-context restoration, clear cohort on scope change and initialize on fresh mount without browser storage or per-semester cache (FR-013–014).
- [X] T013 [US2] Add labelled semester/cohort controls and local full-catalog display predicates to `client/src/pages/AcademicDataPage.tsx`; retain existing status retrieval, complete pagination, null-semester all-scope visibility, exact actions and editor state. Do not use filtering to change selected/editorGeneration/values or lifecycle state (FR-001–005, FR-007, FR-012–013).
- [X] T014 [US2] Add a narrow optional course identity/metadata renderer to `client/src/components/AcademicCatalogList.tsx`, supply course/cohort/semester metadata from `client/src/pages/AcademicDataPage.tsx`, and preserve existing non-course callers and exact action handlers (FR-004, FR-012).
- [X] T015 [US2] Run `npm --prefix client test -- src/pages/AcademicDataPage.test.tsx src/App.test.tsx` from root and record green administration discovery/editor/pagination evidence in `specs/I-005 - filter-course-plan-list/quickstart.md`.

## Phase 5: User Story 3 — Complete selection safety (Priority: P1)

**Goal**: Review every explicit selected course even when hidden; preserve whole-set validity and I-004 decisions.
**Independent test**: Two courses from A plus one from B remain exactly three selected; reveal/deselect yields the exact remaining input; a hidden saved course still requires the joint replacement decision.

### Tests first

- [X] T016 [P] [US3] Extend `client/src/components/MultiCourseGenerationPanel.test.tsx` for cross-cohort selection, all-hidden/zero-match review, reset versus clear-selection, duplicate identity/toggle safety, 0/1/20/externally oversized boundaries, missing/unavailable selected identity review and permitted removal. Enforce `valid generation selection contains 1–20 distinct course IDs` across all hidden/visible items (FR-005, FR-007–010; SC-002–003).
- [X] T017 [P] [US3] Extend `client/src/pages/CourseSchedulePage.test.tsx` with hidden selected saved-course preparation, complete request IDs, I-004 comparison/accept/cancel/stale cases, unavailable/missing selection rejection without pruning, non-editable revision and filtering during preparation/comparison without changing captured evidence (FR-008–011; SC-002, SC-007).

### Implementation and verification

- [X] T018 [US3] After T016/T017 fail, complete selected-course identity/cohort review, hidden counts, reveal/reset path and invalid/missing-item explanations in `client/src/components/MultiCourseGenerationPanel.tsx`; keep selected identity distinct from visibility and never auto-select or silently drop missing IDs (FR-005, FR-007–010).
- [X] T019 [US3] In `client/src/pages/CourseSchedulePage.tsx`, retain last-known display identity for selected records where available or provide explicit course-ID/unavailable fallback to the review. Preserve existing whole-set validation and captured operation handlers; metadata refresh must not alter selected IDs, snapshot tokens or candidate fingerprint (FR-009–011).
- [X] T020 [US3] Verify `client/src/api/conflictAwareGeneration.ts` remains contract-compatible using `client/src/api/conflictAwareGeneration.test.ts` and request assertions in `client/src/pages/CourseSchedulePage.test.tsx`; add regression assertions first if a gap exists, without redesigning the API. Whole-set 1–20 validation, hidden saved-course decisions and atomic/stale behavior must remain authoritative (FR-010–011).
- [X] T021 [US3] Run `npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/api/conflictAwareGeneration.test.ts` from root and record full selection/I-004 regression evidence in `specs/I-005 - filter-course-plan-list/quickstart.md`.

## Phase 6: User Story 4 — Recovery, lifetime and accessibility (Priority: P2)

**Goal**: Understand empty/failure states, retain/reset independent filter memory correctly and operate with keyboard/assistive technology in existing layouts.
**Independent test**: Navigate away/back in both lists, then semester round trips/reset/reload; perform zero-match recovery, selection review and exact course action using keyboard and screen reader.

### Tests first

- [X] T022 [P] [US4] Extend `client/src/pages/AcademicDataPage.test.tsx` for underlying empty versus no matches/loading/failure, disappeared selected cohort/semester context without broadening, filter/reset preservation of editor values, accessible controls and result messages (FR-005–006, FR-012, FR-015–016).
- [X] T023 [P] [US4] Extend `client/src/components/MultiCourseGenerationPanel.test.tsx` for empty/no-match and unavailable context, zero-match hidden review, accessible names, disabled reasons, live totals, keyboard operation and meaningful focus when a result disappears (FR-005–006, FR-009, FR-015–016; SC-004).
- [X] T024 [P] [US4] Extend `client/src/App.test.tsx` and then `client/src/pages/CourseSchedulePage.test.tsx` for independent restoration across surface/pane/category transitions, explicit reset memory, reload/fresh mount, cancelled/committed semester changes, no revival of discarded choices, and no selection restoration/change from filter restoration. Also test parent-owned generation planning-option retrieval: pending initial load, initial failure before a panel exists, successful empty data, failed refresh retaining IDs/identity without successful no-match feedback or generation, and successful recovery. Coordinate sequential edits within these files (FR-006, FR-011, FR-013–014; SC-007, SC-009).

### Implementation and verification

- [X] T025 [US4] After T022–T024 fail, implement distinguishable successful-empty/no-match/loading/error and disappeared-choice feedback in `client/src/pages/AcademicDataPage.tsx`, `client/src/pages/CourseSchedulePage.tsx` and `client/src/components/MultiCourseGenerationPanel.tsx`. Handle initial and refresh planning-option outcomes at the parent page, pass freshness when the panel exists, and block generation on failed freshness until existing reload/recovery succeeds, preserving last known selection/editor and explicit reset/scope recovery rather than substituting or silently broadening (FR-005–006, FR-007, FR-012).
- [X] T026 [US4] Complete accessible German labels via existing terminology, semantic checked/disabled feedback and live result/selection status in `client/src/components/MultiCourseGenerationPanel.tsx` and `client/src/pages/AcademicDataPage.tsx`; maintain predictable focus when results disappear without stealing focus during ordinary filtering (FR-015–016).
- [X] T027 [US4] Refine controlled lifetime/reset integration as needed in `client/src/App.tsx`, `client/src/pages/CourseSchedulePage.tsx` and `client/src/pages/AcademicDataPage.tsx` to pass T024, with no storage, cross-surface synchronization or per-semester choice caches (FR-013–014).
- [X] T028 [US4] Scope wrapping, focus indicators, long identity text and reachable control/review layout adjustments in `client/src/App.css` to the two course-list surfaces; preserve other catalog and calendar layouts at 320 CSS pixels and 200% text enlargement (FR-017; SC-008).
- [X] T029 [US4] Run `npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/AcademicDataPage.test.tsx src/pages/CourseSchedulePage.test.tsx src/App.test.tsx` from root and record accessible semantics/state/focus evidence in `specs/I-005 - filter-course-plan-list/quickstart.md`.

## Phase 7: Polish and cross-cutting verification

- [X] T030 Execute the manual keyboard/screen-reader, no-match recovery, long-label, 320 CSS-pixel and 200% text checks for both lists in `specs/I-005 - filter-course-plan-list/quickstart.md`; record actual browser/assistive technology and results. These rendered outcomes cannot be proven by jsdom alone (FR-015–017; SC-004, SC-008).
- [X] T031 Measure twenty loaded-catalog cohort changes per surface and run the planner comprehension walkthrough defined in `specs/I-005 - filter-course-plan-list/quickstart.md`: at least nineteen of twenty visible updates per surface within one second; planner identifies context, full selection and reset/clear effects on first attempt without assistance (SC-005–006).
- [X] T032 Run `npm --prefix client test`, `npm --prefix client run build`, and `npm --prefix client run lint` from root; record outputs and resolve introduced failures in `specs/I-005 - filter-course-plan-list/quickstart.md` before commit (TR-004–006).
- [X] T033 From backend run `.venv/Scripts/python.exe -m pytest tests/api/test_planning_options.py tests/api/test_academic_catalog.py tests/services/test_academic_catalog.py tests/api/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation_concurrency.py`; record contract/atomicity/stale-state regression results in `specs/I-005 - filter-course-plan-list/quickstart.md`. No backend implementation is authorized by this task (FR-010–012; SC-007).
- [X] T034 Audit FR-001–017, TR-001–006 and SC-001–009 against recorded implementation evidence in `specs/I-005 - filter-course-plan-list/quickstart.md`; reconcile final spec/plan/tasks and update only the I-005 delivery status in `docs/planning/Feature_slices.md` when actual evidence warrants it. Preserve unrelated files and reviewer-owned checklist markers.

## Dependencies and execution order

- T001 → T002 → T003. Tests may then start; no new production setup is required.
- US1: T004 and T005 may run concurrently, then T006 → T007 → T008 → T009.
- US2 can start independently after T003; T010 and T011 may run concurrently, then T012 → T013 → T014 → T015. Default solo delivery order is US1 then US2 because both are P1 and touch separate discovery surfaces.
- US3 extends US1's generation UI; start after T009. T016/T017 may run concurrently, then T018 → T019 → T020 → T021. US2 is not a prerequisite for its independent safety demonstration.
- US4 follows integrated US1–US3 to verify the combined experience. T022–T024 may run concurrently across distinct files after earlier story edits are finished; implementation T025–T028 is sequential, then T029.
- T030–T034 follow all story checkpoints. Do not mark any future task complete based on this planning workflow.

## Parallel examples by story

- US1: T004 (panel test file) alongside T005 (page test file); both must fail before T006.
- US2: T010 (administration tests) alongside T011 (App tests); both must fail before T012.
- US3: T016 (panel tests) alongside T017 (page tests); both must fail before T018.
- US4: T022 (administration tests), T023 (panel tests), T024 (App and schedule page tests) have non-overlapping files within that wave. Never overlap T024 with earlier tasks editing those files.
- No production parallel markers: integration edits share existing files; sequential changes are simpler.

## Implementation strategy

Demonstrate US1 as the first useful increment with complete-selection preservation and minimal hidden review already present. US2 independently delivers administration discovery. US3 strengthens adversarial/full-set review and I-004 coverage, without postponing basic safety from the MVP. US4 completes recovery, lifetime and accessibility checks across the integrated surfaces. The full feature is done only after every story and final verification, not merely after the generation MVP.

## Requirement coverage index

| Requirement | Tasks |
| --- | --- |
| FR-001 | T004, T006, T010, T013 |
| FR-002 | T005, T007, T010, T013 |
| FR-003 | T004, T006, T010, T013 |
| FR-004 | T004, T006, T010, T014 |
| FR-005 | T004, T008, T016, T018, T022, T025 |
| FR-006 | T022, T023, T024, T025 |
| FR-007 | T005, T006, T010, T013, T016, T025 |
| FR-008 | T005, T007, T016, T017 |
| FR-009 | T008, T016, T018, T019, T023 |
| FR-010 | T004, T006, T016, T017, T020, T033 |
| FR-011 | T005, T007, T017, T019, T020, T024, T025, T033 |
| FR-012 | T010, T013, T014, T022, T025, T033 |
| FR-013 | T011, T012, T024, T027 |
| FR-014 | T007, T011, T012, T024, T027 |
| FR-015 | T022, T023, T026, T030 |
| FR-016 | T022, T023, T026, T030 |
| FR-017 | T028, T030 |
| TR-001 | T004–T029 tests-before-production ordering |
| TR-002 | T003, T004, T010 |
| TR-003 | T016–T021 |
| TR-004 | T002, T020, T032, T033 |
| TR-005 | T022–T030 |
| TR-006 | T034 and this index |
| SC-001 | T003–T015 |
| SC-002 | T016–T021 |
| SC-003 | T016, T018, T021 |
| SC-004 | T022, T023, T026, T030 |
| SC-005 | T031 |
| SC-006 | T031 |
| SC-007 | T005, T010, T017, T020, T033 |
| SC-008 | T028, T030 |
| SC-009 | T011, T024, T027, T029 |

## Notes

Backend behavior, HTTP payloads, authorization and academic mutations stay unchanged. Update this plan and add test-first contract work before any discovered necessary boundary change. Manual exceptions are limited to actual rendering, assistive speech and planner comprehension; automated logic and semantics are still test-first. Exact validation commands and expected outcomes are in quickstart.md. Tasks are immediately actionable, not implementation results.



## Phase 8: Convergence

- [X] T035 Guard failed-course retry against pending/failed planning-option freshness in `client/src/pages/CourseSchedulePage.tsx`, with a failing retry-path regression first, per FR-006 and FR-011 (partial)
- [X] T036 Limit new catalog layout classes to the courses category in `client/src/pages/AcademicDataPage.tsx` per T028 and plan: scoped course-list layout (unrequested)
- [X] T037 Replace the no-op hidden-selection cancellation assertion with an actual required cancel action and prove hidden-selection accept/stale behavior in `client/src/pages/CourseSchedulePage.test.tsx` per TR-003 and T017 (partial)
- [X] T038 Complete and record actual rendered/keyboard/screen-reader checks, twenty browser-timed changes per surface and the real planner walkthrough in `specs/I-005 - filter-course-plan-list/quickstart.md` per T030–T031, SC-004–006 and SC-008 (partial)


## Phase 9: Convergence

- [X] T039 Finish independent screen-reader speech, full text enlargement and real planner comprehension evidence remaining from T030–T031/T038 in `specs/I-005 - filter-course-plan-list/quickstart.md` per SC-004, SC-005 and SC-008 (partial)
- [X] T040 Prevent course-editor fields from overflowing the 320-pixel administration surface using course-scoped CSS in `client/src/App.css`, and recheck actual rendering per FR-017 and SC-008 (partial)


## Phase 10: Convergence

- [X] T041 Record the remaining independent screen-reader speech, actual full text enlargement/authenticated layout and real planner first-attempt comprehension results in `specs/I-005 - filter-course-plan-list/quickstart.md`, completing acceptance obligations T030/T031/T038/T039 per TR-005 and SC-004/SC-005/SC-008 (partial)
