# Tasks: Planner-Controlled Schedule Regeneration Decision

**Input**: Design documents from `specs/I-004-planner-controlled-schedule-regeneration-decision/`

**Tests**: Required by the project constitution and feature plan. Add failing tests before the corresponding production changes.

**Scope guard**: Extend the existing unified generator with a stateless post-generation approval pause. Do not add candidate persistence, a database migration, expiry/cleanup, a background job, decision history, or a backend cancel operation.

## Phase 1: Setup

**Purpose**: Establish an isolated implementation baseline and prepare reusable test data for the new response modes and mixed selections without changing application behavior.

- [ ] T001 Before any test or production edit, verify implementation is on an isolated feature branch/worktree with no unrelated changes in planned files, record the branch and baseline status in `specs/I-004-planner-controlled-schedule-regeneration-decision/quickstart.md`, then add reusable fixtures for direct-saved results, decision-required previews, comparison facts, mixed selections, and prepared evidence in `backend/tests/optimization_fixtures.py` and `client/src/test/optimizationFixtures.ts`

---

## Phase 2: Foundational

**Purpose**: Establish the shared deterministic identity and lifecycle freshness evidence used by preview and acceptance.

- [ ] T002 Add failing tests for canonical candidate fingerprints and active Working-revision state/row-version freshness in `backend/tests/services/test_conflict_aware_generation.py`
- [ ] T003 Implement canonical ordered candidate fingerprinting and include active Working-revision state and row version in shared snapshot evidence in `backend/app/services/conflict_aware_generation.py`

**Checkpoint**: Preview and acceptance can share one deterministic candidate identity and reject lifecycle changes.

---

## Phase 3: User Story 1 - Compare a Provisional Regenerated Alternative (Priority: P1)

**Goal**: When any selected course already has saved sessions, generate one hard-valid joint alternative without saving it and show a factual current-versus-generated comparison.

**Independent Test**: Select a course whose current complete schedule has an active hard-constraint warning, generate a valid partial alternative with fewer units, and verify that saved schedules/outcomes remain unchanged while aggregate and per-course coverage, remaining reasons, and resolved warnings are shown.

### Tests for User Story 1

- [ ] T004 [P] [US1] Add failing optimizer tests proving generated-only replacement mode cannot retain selected current sessions, permits a valid lower-unit partial result and a zero-session course within a non-empty joint result, and rejects an all-zero result in `backend/tests/services/test_semester_optimization.py`
- [ ] T005 [P] [US1] Add failing service/API tests for non-mutating preview generation, hard-validity, comparison facts, resolved warnings, prepared evidence, fingerprint output, and removal of the pre-generation confirmation gate, plus workflow-level performance cases for preview, direct-save, and actionable no-result outcomes against the 95%-within-30-seconds criterion in `backend/tests/services/test_conflict_aware_generation.py`, `backend/tests/api/test_conflict_aware_generation.py`, and `backend/tests/performance/test_semester_optimization_performance.py`
- [ ] T006 [P] [US1] Add failing client tests for discriminated preview responses, post-generation dialog timing, exact current/generated facts, valid lower-coverage selection, replacement consequences, exact German actions, and accessible focus/zoom structure in `client/src/api/conflictAwareGeneration.test.ts`, `client/src/components/ReplacementConfirmationDialog.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 1

- [ ] T007 [US1] Add generated-only replacement mode to the unified optimizer, disabling current-session retention and the non-worsening unit floor while preserving every active hard constraint and fixed occupancy rule in `backend/app/services/semester_optimization.py`
- [ ] T008 [US1] Split generation from persistence for replacement selections, build aggregate/per-course comparison facts from the exact snapshot and candidate, suppress provisional PlanningOutcome writes, and preserve no-result diagnostics in `backend/app/services/conflict_aware_generation.py` and `backend/app/services/draft_schedule_validation.py`
- [ ] T009 [US1] Replace `replacementConfirmed` with discriminated direct-saved/decision-required generate contracts and expose the non-mutating preview branch in `backend/app/schemas/conflict_aware_generation.py` and `backend/app/api/conflict_aware_generation.py`
- [ ] T010 [US1] Model the discriminated generate response and evolve the existing confirmation dialog into the accessible factual comparison, including responsive current/generated sections and only the approved actions in `client/src/api/conflictAwareGeneration.ts`, `client/src/components/ReplacementConfirmationDialog.tsx`, and `client/src/App.css`
- [ ] T011 [US1] Move replacement handling from pre-generation confirmation to post-generation preview state without inserting the candidate into saved schedules in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: Replacement selections produce a visible, non-mutating, hard-valid comparison; no approval action is implemented yet.

---

## Phase 4: User Story 2 - Make One Atomic Decision for the Selection (Priority: P1)

**Goal**: Accept or discard the complete joint candidate as one decision for every selected course.

**Independent Test**: Generate a mixed planned/unplanned selection, then verify acceptance saves every selected result together while button, Escape, close, and navigation cancellation save nothing and issue no backend cancellation request.

### Tests for User Story 2

- [ ] T012 [P] [US2] Add failing one-course and multi-course backend acceptance tests that verify active course/study-type windows, course/semester boundaries, holidays, eligibility, availability, capacity, fixed teaching, active exams, same-course exam boundaries, and lecturer/room/cohort non-overlap, together with exact-fingerprint acceptance, mixed-selection atomic save, valid lower-coverage acceptance, zero-session clear/no-empty-draft behavior, successful-only PlanningOutcome retention, rollback, and repeated acceptance rejection in `backend/tests/services/test_conflict_aware_generation.py` and `backend/tests/api/test_conflict_aware_generation.py`
- [ ] T013 [P] [US2] Add failing simultaneous-accept tests proving at most one request commits and the losing request changes nothing in `backend/tests/services/test_conflict_aware_generation_concurrency.py`
- [ ] T014 [P] [US2] Add failing client tests proving accept is sent once, both actions disable in flight, success refreshes authoritative schedules, and button/Escape/close/navigation cancellation clears the whole local candidate without an API call in `client/src/api/conflictAwareGeneration.test.ts`, `client/src/components/ReplacementConfirmationDialog.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 2

- [ ] T015 [US2] Implement deterministic re-solve and fingerprint verification followed by one existing atomic save plan for all selected courses, including explicit zero-session delete/no-op handling, rollback, and successful outcome retention in `backend/app/services/conflict_aware_generation.py` and `backend/app/services/draft_schedule_repository.py`
- [ ] T016 [US2] Add the accept request/response schema and `POST /optimization/accept` route with no client-supplied sessions, per-course choice, written reason, or cancel endpoint in `backend/app/schemas/conflict_aware_generation.py` and `backend/app/api/conflict_aware_generation.py`
- [ ] T017 [US2] Add the accept API call and wire atomic accept, busy-state protection, refresh-after-success, and local-only discard semantics into the comparison workflow in `client/src/api/conflictAwareGeneration.ts`, `client/src/components/ReplacementConfirmationDialog.tsx`, and `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: The complete mixed selection is accepted once or discarded without mutation; no partial decision path exists.

---

## Phase 5: User Story 3 - Prevent Invalid or Stale Replacement (Priority: P1)

**Goal**: Refuse acceptance when the planning snapshot or reproduced candidate differs from what the planner compared.

**Independent Test**: Generate a comparison, change each captured input category or force a fingerprint mismatch, and verify acceptance changes no schedule, closes the unusable preview, preserves the selection, and directs regeneration.

### Tests for User Story 3

- [ ] T018 [P] [US3] Add failing parameterized tests for lifecycle, selected draft/session, protected teaching, active exam, course/constraint, holiday/unavailable-date, resource/availability/eligibility/capacity staleness, fingerprint mismatch, and past-exam non-staleness in `backend/tests/services/test_conflict_aware_generation.py` and `backend/tests/api/test_conflict_aware_generation.py`
- [ ] T019 [P] [US3] Add failing client tests for stale/non-reproducible acceptance responses clearing preview evidence, preserving course selection, avoiding automatic retry, and presenting actionable German regeneration guidance in `client/src/api/conflictAwareGeneration.test.ts` and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [ ] T020 [US3] Revalidate all shared/per-course I-003 snapshot evidence and the active Working revision immediately before persistence, reject non-reproduced fingerprints, and return non-mutating stale/non-reproducible errors in `backend/app/services/conflict_aware_generation.py` and `backend/app/api/conflict_aware_generation.py`
- [ ] T021 [US3] Map stale and fingerprint-mismatch responses to candidate disposal, retained selection, and explicit regenerate guidance without retrying acceptance in `client/src/api/conflictAwareGeneration.ts` and `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: Only the exact still-current result the planner saw can be committed.

---

## Phase 6: User Story 4 - Preserve Direct Save for New Selections (Priority: P2)

**Goal**: Keep the established direct-save behavior when no selected course has saved teaching sessions.

**Independent Test**: Generate complete, partial, and no-result cases for wholly unplanned selections; valid results save directly with no comparison, while no-result saves nothing and reports blockers.

### Tests for User Story 4

- [ ] T022 [P] [US4] Add failing backend regression tests for authoritative saved-session detection, direct atomic save of complete/partial wholly unplanned selections, and non-mutating all-zero/no-result diagnostics in `backend/tests/services/test_conflict_aware_generation.py` and `backend/tests/api/test_conflict_aware_generation.py`
- [ ] T023 [P] [US4] Add failing client regression tests proving direct-saved responses bypass the comparison and retain the established saved-result/no-result presentation in `client/src/api/conflictAwareGeneration.test.ts` and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 4

- [ ] T024 [US4] Preserve the existing solve-and-save branch and saved-result UI for selections with no saved sessions while routing only replacement selections through preview/accept in `backend/app/services/conflict_aware_generation.py`, `backend/app/api/conflict_aware_generation.py`, and `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: Existing generation remains unchanged for wholly unplanned selections.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify the narrow change across the unified initiative and capture final evidence.

- [ ] T025 Run the focused backend service/API/concurrency tests, the workflow-level 95%-within-30-seconds performance test, focused client API/dialog/page tests, complete backend/client suites, lint, and build; record results and any required command adjustments in `specs/I-004-planner-controlled-schedule-regeneration-decision/quickstart.md`
- [ ] T026 Coordinate with the FS-023 product owner to perform the quickstart mixed-selection, cancellation, stale, atomicity, direct-save, keyboard, narrow-layout, 200%-zoom, and five-planner usability checks; treat the SC-008 threshold as a release-readiness gate and record only anonymized evidence in `specs/I-004-planner-controlled-schedule-regeneration-decision/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on T001 and blocks replacement stories.
- **US1 (Phase 3)**: Depends on Phase 2 and creates the provisional comparison.
- **US2 (Phase 4)**: Depends on US1 because acceptance consumes its preview evidence and fingerprint.
- **US3 (Phase 5)**: Depends on US2 because it protects the accept operation.
- **US4 (Phase 6)**: Depends on the shared generation branching introduced by US1; it is otherwise independently testable.
- **Polish (Phase 7)**: Depends on all implemented stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 -> US2 -> US3
                         `-----> US4
US1 + US2 + US3 + US4 -> Polish
```

### Within Each Story

1. Add and observe the failing tests.
2. Implement optimizer/service behavior.
3. Implement schemas/routes and client API contracts.
4. Integrate the dialog/page behavior.
5. Run the story's independent test before moving on.

### Parallel Opportunities

- T004, T005, and T006 can run in parallel after Phase 2.
- T012, T013, and T014 can run in parallel after US1.
- T018 and T019 can run in parallel after US2.
- T022 and T023 can run in parallel after the generation branch exists.
- Backend and client focused verification within T025 can run in parallel.

---

## Parallel Example: User Story 1

```text
Task T004: Optimizer generated-only and partial-result tests
Task T005: Backend non-mutating preview and comparison tests
Task T006: Client contract, dialog, and page tests
```

## Parallel Example: User Story 2

```text
Task T012: Backend atomic acceptance tests
Task T013: Concurrent acceptance tests
Task T014: Client accept and discard tests
```

## Implementation Strategy

### Recommended Product MVP

Complete Phases 1-4 (US1 and US2). US1 alone is independently demonstrable as a non-mutating comparison, but US1 plus US2 delivers the usable planner decision loop.

### Incremental Delivery

1. Deliver the non-mutating comparison (US1).
2. Add one atomic accept/local discard decision (US2).
3. Harden acceptance against stale or non-reproduced results (US3).
4. Prove the unchanged direct-save path (US4).
5. Run full regression, accessibility, responsiveness, performance, and usability validation.

### Simplicity Guardrail

If implementation appears to require a candidate table, token expiry, cleanup job, backend cancel route, signed client session payload, second generator, or decision-history model, stop and reconcile the work with `plan.md`; none is part of FS-023.
