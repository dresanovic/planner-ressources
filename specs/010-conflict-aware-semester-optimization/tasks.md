# Tasks: FS-010 Conflict-Aware Semester Optimization

**Input**: Design documents from `specs/010-conflict-aware-semester-optimization/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/conflict-aware-optimization.openapi.yaml`, `quickstart.md`

**Tests**: Tests are required by the constitution and FS-010 TR-001 through TR-010. Every automated test task precedes the corresponding production task, and failing behavior must be confirmed before implementation where practical.

**Organization**: Tasks are grouped by user story. US1 provides the complete-result MVP; US2 adds optimal partial results and reasons; US3 adds non-worsening replacement and stale protection; US4 completes mixed-operation review and refresh behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and does not depend on an incomplete task.
- **[Story]**: Maps the task to the corresponding specification user story.
- Every task names the exact file it creates or changes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish safe delivery scope and the one justified runtime dependency.

- [X] T001 Create and switch to `codex/fs-010-semester-optimization`, then update the Working Branch fields in `specs/010-conflict-aware-semester-optimization/spec.md` and `specs/010-conflict-aware-semester-optimization/plan.md`
- [X] T002 Add pinned `ortools==9.15.6755` and its resolved runtime requirements to `backend/requirements.txt`, install them, and verify the CP-SAT Python import
- [X] T003 [P] Create canonical course, semester, resource, window, fixed-session, and expected-optimum fixture builders in `backend/tests/optimization_fixtures.py`
- [X] T004 [P] Create preparation, outcome, reason, and mixed-result client fixtures in `client/src/test/optimizationFixtures.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create reusable test evidence and the bounded reference workload before any user-story production implementation.

**CRITICAL**: No production user-story task begins until these test foundations exist.

- [X] T005 Create the documented 20-course, 600-requested-unit, 500-fixed-session fixture and initially failing 30/60-second acceptance test in `backend/tests/performance/test_semester_optimization_performance.py`
- [X] T006 [P] Create shared expected optimization status, reason-code, summary-field, and error-envelope fixtures for later API contract tests in `backend/tests/contract_fixtures.py`
- [X] T007 [P] Create the validation evidence index with sections for all twelve quickstart scenarios plus the SC-006/SC-007 usability protocol in `specs/010-conflict-aware-semester-optimization/validation/README.md`

**Checkpoint**: Dependency, fixtures, contract validation, and performance acceptance baseline exist; story tests can now be written.

---

## Phase 3: User Story 1 - Generate the Best Conflict-Free Semester Result (Priority: P1) MVP

**Goal**: Optimize first-time selected courses together, prove maximum scheduled units, obey every hard rule/fixed occupancy/unavailable date, assign eligible resources, and save a complete deterministic result.

**Independent Test**: Prepare first-time courses with competing time/resource choices, including a request-order counterexample, optimize them, and verify the saved result is proven optimal, conflict-free, hard-rule compliant, deterministic, and independent of selection order.

### Tests for User Story 1 (write and confirm failures first)

- [X] T008 [P] [US1] Add candidate-generation tests for semester/planning dates, allowed-window starts, valid session sizes, one session per course/date, unavailable dates, resource eligibility/availability/capacity, and fixed occupancy in `backend/tests/services/test_semester_optimization.py`
- [X] T009 [US1] Add solver tests for the request-order counterexample, maximum total units, Lecturer continuity, Room continuity, Lecturer/Room/Cohort no-overlap, eligible resource assignment, `OPTIMAL`-only acceptance, canonical final rank, and 20-run determinism in `backend/tests/services/test_semester_optimization.py`
- [X] T010 [P] [US1] Add preparation, canonical snapshot, first-time solve, exact-result validation, atomic save, established default-constraint saving, custom-constraint/source-record preservation, and no-save solver failure tests in `backend/tests/services/test_conflict_aware_generation.py`
- [X] T011 [P] [US1] Add `/optimization/prepare` and `/optimization/generate` API tests for 1â€“20 distinct courses, malformed selection, unavailable-date canonical deduplication, complete results, `optimalForPreparedSnapshot`, and `503 OPTIMAL_RESULT_NOT_PROVEN` in `backend/tests/api/test_conflict_aware_generation.py`
- [X] T012 [P] [US1] Add request/response parsing, network failure, validation failure, and solver failure tests in `client/src/api/conflictAwareGeneration.test.ts`
- [X] T013 [P] [US1] Add optimized selection limit, labels, disabled/loading state, complete-outcome rendering, and complete-result page-flow tests in `client/src/components/MultiCourseGenerationPanel.test.tsx`, `client/src/components/BatchResultSummary.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 1

- [X] T014 [P] [US1] Define optimization request, preparation, snapshot, summary, outcome, reason, and error schemas matching the OpenAPI contract in `backend/app/schemas/conflict_aware_generation.py`
- [X] T015 [US1] Implement immutable solver-domain inputs, canonical time conversion, finite temporal candidate generation, hard-rule filtering, fixed-occupancy filtering, and reason evidence collection in `backend/app/services/semester_optimization.py`
- [X] T016 [US1] Implement CP-SAT temporal/resource variables, optional intervals, per-course/date limits, unit bounds, and Lecturer/Room/Cohort no-overlap constraints in `backend/app/services/semester_optimization.py`
- [X] T017 [US1] Implement staged total-unit, Lecturer-continuity, Room-continuity, and canonical-rank optimization for first-time courses plus `OPTIMAL` enforcement, overall deadline handling, solution hints, single-worker/fixed-seed configuration, and deterministic result extraction in `backend/app/services/semester_optimization.py`
- [X] T018 [US1] Implement complete semester/course/resource/constraint/draft loading, canonical preparation fingerprints, and first-time-course preparation in `backend/app/services/conflict_aware_generation.py`
- [X] T019 [US1] Implement first-time orchestration that solves, revalidates exact sessions against current state, saves each complete Draft Schedule through the existing repository, preserves source records/custom constraints, saves exact active defaults only for successful courses with no constraint set, and rolls back unproven/invalid operations in `backend/app/services/conflict_aware_generation.py`
- [X] T020 [US1] Add prepare/generate routes, request validation, 404/422/503/500 mapping, transaction commit/rollback, and router registration in `backend/app/api/conflict_aware_generation.py` and `backend/app/main.py`
- [X] T021 [P] [US1] Implement typed preparation/generation calls and error parsing in `client/src/api/conflictAwareGeneration.ts`
- [X] T022 [US1] Update the existing multi-course picker to expose â€œOptimize selected courses,â€ enforce the 1â€“20 optimized limit, and retain selection during loading/errors in `client/src/components/MultiCourseGenerationPanel.tsx`
- [X] T023 [US1] Integrate prepare, no-replacement optimization, in-progress state, error display, complete-outcome rendering, and successful semester reload into `client/src/pages/CourseSchedulePage.tsx` and `client/src/components/BatchResultSummary.tsx`
- [X] T024 [US1] Run the focused US1 backend/client tests and quickstart scenarios 1â€“3 and 7, then record expected-optimum, Lecturer/Room continuity, hard-rule, unavailable-date deduplication, constraint/source preservation, and 20-run determinism evidence in `specs/010-conflict-aware-semester-optimization/validation/user-story-1-results.md`

**Checkpoint**: US1 is independently usable for first-time course sets and proves/saves the maximum complete conflict-free result.

---

## Phase 4: User Story 2 - Keep and Understand a Useful Partial Plan (Priority: P2)

**Goal**: Save the greatest permitted partial result when completion is impossible and report accurate remaining units with substantiated blocking-reason categories, including zero-placement unchanged outcomes.

**Independent Test**: Optimize an intentionally infeasible first-time selection and verify the independently established maximum partial total is saved, every incomplete course reports saved scheduled/remaining units and applicable reasons, and zero placement creates no empty Draft Schedule.

### Tests for User Story 2 (write and confirm failures first)

- [X] T025 [P] [US2] Add solver tests for optional partial unit combinations, minimum/maximum session sizes, globally competing courses, zero placement, no fairness minimum, and maximum partial totals in `backend/tests/services/test_semester_optimization.py`
- [X] T026 [US2] Add candidate-evidence tests for every blocking-reason code and unsupported unique-cause avoidance in `backend/tests/services/test_semester_optimization.py`
- [X] T027 [P] [US2] Add service/API tests for improved partial, unchanged no-draft zero placement, accurate saved progress, no empty parent, and reason serialization in `backend/tests/services/test_conflict_aware_generation.py` and `backend/tests/api/test_conflict_aware_generation.py`
- [X] T028 [P] [US2] Add partial/unchanged outcome, scheduled/remaining unit, multiple-reason, and zero-placement presentation tests in `client/src/components/BatchResultSummary.test.tsx`

### Implementation for User Story 2

- [X] T029 [US2] Extend the CP-SAT course model to choose zero or more valid session sizes up to course total units while preserving the strict global total-unit objective in `backend/app/services/semester_optimization.py`
- [X] T030 [US2] Implement substantiated blocking-reason aggregation for eligibility, capacity, availability, occupied resources/cohort, unavailable dates, planning windows, course constraints, and selected-course competition in `backend/app/services/semester_optimization.py`
- [X] T031 [US2] Map proven partial/no-placement results to `improved_partial` or `unchanged`, derive progress from saved state, avoid empty Draft Schedules, and serialize stable reasons in `backend/app/services/conflict_aware_generation.py`
- [X] T032 [US2] Extend outcome/summary API schemas with scheduled units, remaining units, improvement facts, and blocking reasons in `backend/app/schemas/conflict_aware_generation.py`
- [X] T033 [US2] Add the five-status result types, improvement fields, and blocking-reason types to `client/src/api/conflictAwareGeneration.ts`
- [X] T034 [US2] Render improved-partial/unchanged status, scheduled and remaining units, improvements, and all reason categories in `client/src/components/BatchResultSummary.tsx`
- [X] T035 [US2] Preserve the selected planning context and refresh saved partial schedules/alerts after result receipt in `client/src/pages/CourseSchedulePage.tsx`
- [X] T036 [US2] Run the focused US2 tests and quickstart scenario 4, then record independently established partial totals, zero-placement behavior, progress, and reason evidence in `specs/010-conflict-aware-semester-optimization/validation/user-story-2-results.md`

**Checkpoint**: US2 independently demonstrates useful proven partial work and understandable remaining-unit evidence without weakening US1.

---

## Phase 5: User Story 3 - Prevent Schedule Regression During Replacement (Priority: P3)

**Goal**: Confirm replacement scope, retain whole current-draft alternatives, apply every clarified comparison tier, reject regressions, detect material stale inputs, and save only exact unaffected results without silent re-optimization.

**Independent Test**: Prepare selected courses with current/manual drafts and exercise cancellation, fewer units, equal non-improvement, equal strict improvement, higher units, every comparison tier, material stale inputs, and unaffected exact-result saving.

### Tests for User Story 3 (write and confirm failures first)

- [X] T037 [P] [US3] Add solver tests for whole current-draft alternatives, actual scheduled-unit baselines including over-scheduled drafts, fewer-unit rejection, conflict-pair/type counting, complete-draft preservation, and integration with the US1 continuity/canonical tiers in `backend/tests/services/test_semester_optimization.py`
- [X] T038 [P] [US3] Add service tests for replacement preparation, fingerprint changes across every material input category, stale-course preservation, exact unaffected-result validation, no silent re-solve, nested rollback, cross-semester isolation, custom-constraint/source-record preservation, and successful-only default-constraint saving in `backend/tests/services/test_conflict_aware_generation.py`
- [X] T039 [P] [US3] Add API tests for replacement-required `409`, cancellation/no request, confirmed worse/equal/better outcomes, mixed stale success, prepared-snapshot proof scope, refreshed preparation, and no-save operation failure in `backend/tests/api/test_conflict_aware_generation.py`
- [X] T040 [P] [US3] Extend replacement dialog tests for affected courses, manual-edit warning, cancel, confirm, changed-preparation retry, keyboard focus, and announced outcomes in `client/src/components/ReplacementConfirmationDialog.test.tsx`
- [X] T041 [P] [US3] Add page-flow tests for confirmed replacement, unchanged regression, stale result, fresh retry, and preservation of newer state in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T042 [US3] Add whole retained-current alternatives using actual scheduled-unit baselines, existing conflict relationship variables, complete-draft preservation count, and their staged locks around the already-implemented US1 continuity/canonical tiers in `backend/app/services/semester_optimization.py`
- [X] T043 [US3] Implement canonical unavailable-date deduplication and per-course/shared snapshot tokens covering Draft Schedules, semester occupancy, Courses/Cohorts, eligibility, resources, availability, active periods, allowed windows, constraints, and canonical unavailable dates in `backend/app/services/conflict_aware_generation.py`
- [X] T044 [US3] Implement preparation comparison, post-solve material-input reload, stale impact classification, prepared-snapshot proof reporting, and exact unaffected-result validation against refreshed occupancy without re-optimization or a refreshed-state global-optimality claim in `backend/app/services/conflict_aware_generation.py`
- [X] T045 [US3] Implement non-worsening/equal-improvement decisions and per-course nested atomic replacement with current-draft preservation on stale, failed, or non-improving outcomes in `backend/app/services/conflict_aware_generation.py`
- [X] T046 [US3] Enforce replacement confirmation and preparation identity at the HTTP boundary and return planner-readable stale/comparison outcomes in `backend/app/api/conflict_aware_generation.py`
- [X] T047 [US3] Update preparation and generation client requests to echo shared/course snapshot tokens and confirmed replacement scope in `client/src/api/conflictAwareGeneration.ts`
- [X] T048 [US3] Reuse and adapt the replacement confirmation dialog for optimized affected-course/manual-edit scope, cancellation, focus restoration, and renewed confirmation in `client/src/components/ReplacementConfirmationDialog.tsx`
- [X] T049 [US3] Integrate confirmation, stale-state refresh, exact failed/stale retry preparation, and preservation messaging into `client/src/pages/CourseSchedulePage.tsx`
- [X] T050 [US3] Run the focused US3 tests and quickstart scenarios 5, 6, and 8â€“9, then record actual-unit non-worsening, comparison-tier, cancellation, constraint/source preservation, stale proof scope, unaffected-save, rollback, and no-silent-reoptimization evidence in `specs/010-conflict-aware-semester-optimization/validation/user-story-3-results.md`

**Checkpoint**: US3 makes optimization safe for reviewed current schedules and concurrent planning changes.

---

## Phase 6: User Story 4 - Review One Coordinated Operation (Priority: P4)

**Goal**: Present one saved-state summary that classifies every selected course exactly once, supports fresh retry, and refreshes the complete semester overview and validation alerts.

**Independent Test**: Run one operation constructed to produce complete, improved partial, unchanged, failed, and stale outcomes; verify counts, progress, reasons, saved schedules, retry targets, and refreshed alerts against final persisted state.

### Tests for User Story 4 (write and confirm failures first)

- [X] T051 [P] [US4] Add service/API tests for all five outcomes in one operation, exact-once ordered classification, summary arithmetic, final saved-state progress, elapsed time, `optimalForPreparedSnapshot`, and absence of a refreshed-state global-optimality claim in `backend/tests/services/test_conflict_aware_generation.py` and `backend/tests/api/test_conflict_aware_generation.py`
- [X] T052 [P] [US4] Add client API tests for mixed summary parsing and failed/stale retry selection in `client/src/api/conflictAwareGeneration.test.ts`
- [X] T053 [P] [US4] Add summary component tests for all classifications, counts, progress, improvements, reasons, operation errors, and accessible retry controls in `client/src/components/BatchResultSummary.test.tsx`
- [X] T054 [P] [US4] Add page tests for complete-semester reload, related-alert refresh, no speculative state, fresh failed/stale retry, filters, and no-manual-reload behavior in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 4

- [X] T055 [US4] Re-read committed schedules and derive exact-once ordered course outcomes plus internally consistent summary counts/units/timing and prepared-snapshot proof scope from final saved state in `backend/app/services/conflict_aware_generation.py`
- [X] T056 [US4] Finalize mixed result and operation-failure response mapping in `backend/app/api/conflict_aware_generation.py`
- [X] T057 [US4] Finalize mixed summary and retry-target types/parsing in `client/src/api/conflictAwareGeneration.ts`
- [X] T058 [US4] Implement accessible five-status counts, per-course progress/reasons/improvements, prepared-snapshot proof wording, operation failures, and retry failed/stale controls in `client/src/components/BatchResultSummary.tsx`
- [X] T059 [US4] Reload the complete semester overview/alerts after save or stale response, preserve review filters, and initiate fresh retry preparation in `client/src/pages/CourseSchedulePage.tsx`
- [X] T060 [US4] Run the focused US4 tests and quickstart scenario 11, then record mixed-outcome, prepared-snapshot proof wording, summary, retry, overview-refresh, and alert-refresh evidence in `specs/010-conflict-aware-semester-optimization/validation/user-story-4-results.md`

**Checkpoint**: All four user stories are independently testable and the complete optimized workflow is reviewable from saved state.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Prove bounded performance, regressions, documentation, and final constitutional compliance across the complete slice.

- [X] T061 Tune candidate pruning, model construction, staged solve hints, and deadline budgeting only as required by the already-written performance test in `backend/app/services/semester_optimization.py`
- [X] T062 [P] Add regression coverage that existing single-course generation, independent FS-006 batch generation, FS-008 resource rules, FS-009 manual mutations, validation alerts, and other-semester schedules remain unchanged in `backend/tests/services/test_schedule_generation.py`, `backend/tests/services/test_multi_course_generation.py`, `backend/tests/api/test_multi_course_generation.py`, and `backend/tests/api/test_draft_schedule.py`
- [X] T063 [P] Add client regression coverage for existing single-course planning, manual session management, review filters, and independent batch behavior in `client/src/pages/CourseSchedulePage.test.tsx` and `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T064 Document the optimized workflow, 20-course bound, unavailable-date deduplication, actual-unit replacement protection, prepared-snapshot proof wording, constraint preservation, solver/no-save failure behavior, and development commands in `backend/README.md` and `client/README.md`
- [X] T065 Run the reference performance protocol repeatedly and record hardware, fixture seed, versions, stage statuses, raw timings, 30-second percentile, and 60-second maximum evidence in `specs/010-conflict-aware-semester-optimization/validation/performance-results.md`
- [X] T066 Run all twelve scenarios in `specs/010-conflict-aware-semester-optimization/quickstart.md` and record consolidated acceptance results in `specs/010-conflict-aware-semester-optimization/validation/quickstart-results.md`
- [X] T067 Run `python -m pytest` from `backend/`, then `npm test`, `npm run lint`, and `npm run build` from `client/`, and record command outputs plus residual risks in `specs/010-conflict-aware-semester-optimization/validation/final-results.md`
- [ ] T068 Conduct the SC-006/SC-007 protocol with at least 10 representative planners or acceptance reviewers and record anonymized prompts, timings, outcome/reason identification, replacement understanding, improved-partial versus unchanged accuracy, failures, and aggregate percentages in `specs/010-conflict-aware-semester-optimization/validation/usability-results.md`
- [ ] T069 Recheck the constitution, Simplicity Check, cross-stack contract, no-migration decision, exact FS-010 scope, all acceptance evidence, and absence of excluded background/holiday/exam/fairness behavior; document the final audit in `specs/010-conflict-aware-semester-optimization/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 â€” Setup**: Starts immediately. T001 must complete before production edits; T002 enables solver tests; T003 and T004 can run in parallel.
- **Phase 2 â€” Foundational**: Depends on Phase 1. T005â€“T007 create required test/contract/evidence foundations and block user-story implementation.
- **Phase 3 â€” US1**: Depends on Phase 2 and delivers the MVP solver/API/UI path for first-time complete results.
- **Phase 4 â€” US2**: Depends on the US1 solver and orchestration boundaries; extends them with partial choice and explanation behavior.
- **Phase 5 â€” US3**: Depends on US1; may proceed alongside US2 after the common US1 boundary is stable, but T050 validates both comparison and partial preservation together.
- **Phase 6 â€” US4**: Depends on US1â€“US3 outcome semantics so one mixed saved-state summary can be verified.
- **Phase 7 â€” Polish**: Depends on every desired story. Performance tuning must respond to T005 rather than introduce unmeasured complexity, and T068 supplies the required SC-006/SC-007 usability evidence before the T069 final audit.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP)
                           |---> US2
                           `---> US3
                                  \
                          US2 -----+---> US4 -> Polish
```

### Within Each User Story

1. Write all listed automated tests and confirm the intended failures.
2. Implement domain/model behavior before orchestration.
3. Implement orchestration before HTTP/UI exposure.
4. Implement client API before component/page integration.
5. Run focused tests and record independent acceptance evidence before advancing.

### Parallel Opportunities

- T003 and T004 can run in parallel after T002 is not required for either fixture file.
- T005, T006, and T007 can run in parallel once Setup completes.
- Within each story, backend service, backend API, client API, and client component test tasks marked `[P]` can be written in parallel.
- After US1 stabilizes the shared boundary, US2 explanation work and US3 replacement/stale work can proceed in parallel in separate test files, but production edits to `semester_optimization.py`, `conflict_aware_generation.py`, and `CourseSchedulePage.tsx` must be serialized.
- T062 and T063 can run in parallel; documentation and evidence tasks can proceed after their relevant verification completes.

---

## Parallel Example: User Story 1

```text
T008 then T009: backend/tests/services/test_semester_optimization.py (same file; serialize)
T010: backend/tests/services/test_conflict_aware_generation.py
T011: backend/tests/api/test_conflict_aware_generation.py
T012: client/src/api/conflictAwareGeneration.test.ts
T013: client/src/components/MultiCourseGenerationPanel.test.tsx and client/src/pages/CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 2

```text
T025 then T026: backend/tests/services/test_semester_optimization.py (same file; serialize)
T027: backend service/API partial-result tests
T028: client/src/components/BatchResultSummary.test.tsx
```

## Parallel Example: User Story 3

```text
T037: backend solver comparison tests
T038: backend orchestration stale/replacement tests
T039: backend API confirmation tests
T040: client replacement dialog tests
T041: client page stale/retry tests
```

## Parallel Example: User Story 4

```text
T051: backend mixed-outcome tests
T052: client API mixed-result tests
T053: client summary tests
T054: client page refresh/retry tests
```

---

## Implementation Strategy

### MVP First â€” User Story 1

1. Complete Setup and Foundational phases.
2. Complete US1 tests before production tasks.
3. Deliver proven complete optimization for first-time course sets.
4. Stop and validate US1 with independently established optima, hard constraints, unavailable dates, and deterministic repeats.

### Incremental Delivery

1. **US1**: Proven complete conflict-free optimization and save.
2. **US2**: Proven partial results, zero-placement behavior, progress, and reasons.
3. **US3**: Replacement confirmation, non-worsening comparison, stale safety, and exact unaffected saves.
4. **US4**: Mixed saved-state summaries, refresh, and fresh retry.
5. **Polish**: Reference performance, all regressions, full quickstart, and constitutional audit.

### Parallel Team Strategy

After Setup/Foundation and US1:

- Solver-focused work can advance US2 candidate/reason behavior.
- Transaction-focused work can advance US3 snapshots/revalidation.
- Client work can prepare story tests against the committed OpenAPI contract.
- Serialize changes where stories share the same production file and integrate only after each story's focused tests pass.

---

## Notes

- `[P]` means file-level parallelism only; do not parallel-edit shared production files.
- No task adds a database migration, persisted optimization operation, background queue, algorithm selector, fairness weighting, holiday CRUD, exam scheduling, or arbitrary start-time grid.
- `FEASIBLE` or `UNKNOWN` solver output is never persisted; only all-stage `OPTIMAL` results may save.
- Existing user changes in `docs/planning/Feature_slices.md` remain outside this task list unless a later explicit scope update requests them.
- Commit only after relevant focused tests pass; run the complete verification suite before final commit.
