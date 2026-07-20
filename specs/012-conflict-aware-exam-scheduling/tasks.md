# Tasks: FS-012 Conflict-Aware Exam Scheduling

**Input**: Design documents from `specs/012-conflict-aware-exam-scheduling/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/exam-scheduling.openapi.yaml`, `quickstart.md`

**Tests**: Tests are required by the project constitution and MUST be written first and observed failing for the intended missing behavior before the corresponding production task starts.

**Organization**: Tasks are grouped by user story so configuration, generation, and manual management can be implemented and validated as explicit increments. US1 establishes the configuration lifecycle required by US2 and US3; US2 completes the automated P1 outcome; US3 adds the P2 planner-controlled management path.

**Simplicity**: Keep exams separate from teaching drafts, reuse existing resource, holiday, overlap, snapshot, revision, and Schedule-page patterns, and add no dependency, generic repository/solver framework, state library, form framework, exam-type catalog, or unrelated navigation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and does not depend on an incomplete task in the same phase.
- **[Story]**: Maps the task to User Story 1, 2, or 3 from `spec.md`.
- Every task includes the exact repository path it changes or validates.

---

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Isolate the cross-stack work and create reusable feature fixtures without changing production behavior.

- [X] T001 Create and switch the repository at `C:\Codex\planner-resource` to feature branch `codex/fs-012-exam-scheduling` before any production-code task
- [X] T002 [P] Add reusable semester, teaching, resource, holiday, configuration, active-exam, and past-exam builders in `backend/tests/exam_fixtures.py`
- [X] T003 [P] Add typed configuration, exam-session, mixed-outcome, stale-state, and validity-issue fixtures in `client/src/test/examFixtures.ts`

---

## Phase 2: Foundational Persistence (Blocking Prerequisites)

**Purpose**: Add the two revisioned persisted concepts and supported schema upgrade path used by every user story.

**CRITICAL**: Complete this phase before starting any user-story production implementation.

- [X] T004 [P] Write failing clean-create, constraint/index, idempotence, and recognized 0005-to-0006 upgrade/downgrade tests for both exam tables in `backend/tests/db/test_migrations.py`
- [X] T005 [P] Create or update focused FS-008/FS-010/FS-011 regression assertions for eligibility/availability, teaching optimization preservation, and holiday behavior, then run and record the passing pre-change baseline in `backend/tests/services/test_resource_rules.py`, `backend/tests/services/test_semester_optimization.py`, and `backend/tests/services/test_holiday_calendar.py`
- [X] T006 [P] Add `CourseExamConfiguration` and `ExamSession` mappings, checks, indexes, revisioning, relationships, and preserved snapshot columns in `backend/app/models/planning.py`
- [X] T007 [P] Create the additive `0006_conflict_aware_exam_scheduling` upgrade and downgrade in `backend/app/db/migrations/0006_conflict_aware_exam_scheduling.py`
- [X] T008 Advance current-schema detection, sequential 0005-to-0006 startup upgrade, and FS-012 schema error reporting in `backend/app/db/schema.py`

**Checkpoint**: A clean database and a supported FS-011 database both produce the constrained FS-012 schema without changing teaching, resource, or holiday rows.

---

## Phase 3: User Story 1 - Configure Exam Requirements Explicitly (Priority: P1)

**Goal**: Let a planner explicitly enable, validate, update, disable, and freshen one current next-exam configuration while disabled courses and preserved past exams remain untouched.

**Independent Test**: With several past exams and no active exam, save a complete enabled configuration, verify the default seven-to-fourteen-day recommendation and later planner override, retain an anchorless configuration as explicitly enabled but ineligible, reject all invalid or stale inputs, keep a consumed configuration read-only while its active exam exists, and verify a disabled course remains teaching-only.

### Tests for User Story 1 (write and observe failing first)

- [X] T009 [P] [US1] Write service tests for explicit enablement, all field validations, anchorless enabled/ineligible state with null effective recommendations, default/overridden recommendations after an anchor exists, institution-local active/past classification, consumed-configuration read-only behavior, fresh-next configuration, snapshot preservation, revisions, and disabling safeguards in `backend/tests/services/test_exam_scheduling.py`
- [X] T010 [P] [US1] Write API contract tests for `GET /api/exam-planning` and `PUT /api/courses/{course_id}/exam-configuration`, including nullable effective recommendations, active-configuration conflicts, 200/201/404/409/422 envelopes, and atomic multi-field errors, in `backend/tests/api/test_exam_scheduling.py`
- [X] T011 [P] [US1] Write client serialization, nullable-recommendation parsing, response parsing, and structured failure tests for overview/configuration calls in `client/src/api/examScheduling.test.ts`
- [X] T012 [P] [US1] Write accessible editor tests for enable/disable, required values, anchorless guidance, free-text type trimming, derived recommendation, planner overrides, invalid-field feedback, read-only active-exam guidance, busy state, and cancel behavior in `client/src/components/ExamRequirementEditor.test.tsx`
- [X] T013 [P] [US1] Write Schedule-page orchestration tests proving disabled courses show no missing-exam warning, anchorless configurations remain visibly ineligible, and saved configuration refreshes without changing teaching or past-exam state in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 1

- [X] T014 [US1] Define strict Pydantic configuration, nullable effective-recommendation, overview, course-state, lifecycle, resource-reference, issue, eligibility, and structured error schemas matching the OpenAPI aliases in `backend/app/schemas/exam_scheduling.py`
- [X] T015 [US1] Implement the injected `INSTITUTION_TIMEZONE` clock, authoritative optional final-teaching anchor, nullable/default/overridden effective recommendation, active-slot check, anchorless configuration save, consumed-configuration read-only enforcement, freshen/disable lifecycle, revision handling, session snapshot reads, and overview assembly in `backend/app/services/exam_scheduling.py`
- [X] T016 [US1] Expose the overview and configuration operations with atomic 404/409/422 handling in `backend/app/api/exam_scheduling.py`
- [X] T017 [US1] Register the dedicated exam-scheduling router without changing existing route behavior in `backend/app/main.py`
- [X] T018 [P] [US1] Add contract-matching TypeScript configuration, nullable effective-recommendation, overview, session, eligibility, issue, and error types plus overview/save request functions in `client/src/api/examScheduling.ts`
- [X] T019 [US1] Implement the focused accessible enable/configure/disable form with anchorless and active-read-only guidance, current eligible lecturer options, and revision-aware saves in `client/src/components/ExamRequirementEditor.tsx`
- [X] T020 [US1] Load authoritative exam planning state for the selected semester and integrate the requirement editor into the existing Schedule workflow in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: User Story 1 is independently usable and testable; only explicitly enabled, complete, unconsumed configurations with a final teaching anchor are eligible for later placement.

---

## Phase 4: User Story 2 - Generate Valid Exams or Understand Failure (Priority: P1)

**Goal**: Jointly generate one valid active exam or one understandable outcome for every selected enabled course-semester, with no teaching/exam resource conflicts and no stale or invalid save.

**Independent Test**: Prepare feasible and infeasible enabled courses together with disabled and already-active courses, teaching/exam occupancy, holidays, resource unavailability, eligibility, and capacity limits; generate and verify one deterministic scheduled/failed/stale/skipped outcome per prepared course while all pre-existing work remains unchanged.

### Tests for User Story 2 (write and observe failing first)

- [X] T021 [P] [US2] Write optimizer tests for every applicable active Study Type window-start proposal, `AUTOMATIC_START_TIME_UNAVAILABLE`, final-teaching/semester/duration boundaries, eligibility, capacity, full-interval availability, holidays, half-open lecturer/room/cohort conflicts, proposed-exam conflicts, soft recommendation preference, deterministic tie-breaking, and infeasibility evidence in `backend/tests/services/test_exam_optimization.py`
- [X] T022 [P] [US2] Write generation-service tests for anchorless `FINAL_TEACHING_SESSION_MISSING`, missing automatic start proposals, canonical preparation, disabled/active/consumed eligibility, per-course/shared snapshots, mixed partial saves, one-active serialization, exact-result revalidation, stale outcomes, preserved existing sessions, failure aggregation, and solver-without-proof rollback in `backend/tests/services/test_exam_scheduling.py`
- [X] T023 [P] [US2] Write API tests for `POST /api/exams/generation/prepare` and `POST /api/exams/generation`, including anchor/proposal-domain failures, selection bounds, mixed 200 results, 409/422 errors, and no-save 503 behavior, in `backend/tests/api/test_exam_scheduling.py`
- [X] T024 [P] [US2] Write client tests for 1-to-100 unique-course validation, exact preparation-token echoing, anchor/proposal-domain failures, mixed outcomes, structured failures, and network fallback in `client/src/api/examScheduling.test.ts`
- [X] T025 [P] [US2] Write accessible preparation, selection, confirmation, busy-state, stale-retry, and mixed-summary interaction tests in `client/src/components/ExamGenerationPanel.test.tsx`
- [X] T026 [P] [US2] Write summary tests that distinguish scheduled, failed, stale, active-skip, and disabled-skip outcomes and explain `FINAL_TEACHING_SESSION_MISSING`, `AUTOMATIC_START_TIME_UNAVAILABLE`, and other course/configuration-specific blocking evidence in `client/src/components/ExamGenerationResultSummary.test.tsx`
- [X] T027 [P] [US2] Write Schedule-page tests for generation eligibility, authoritative post-save refresh, mixed-result retention, and preservation of the last complete view when refresh fails in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T028 [P] [US2] Write the failing 100-configuration, 500-teaching-session, 100-existing-exam deterministic under-60-second reference test and no-unproven-save assertion before generation production work in `backend/tests/performance/test_exam_scheduling_performance.py`

### Implementation for User Story 2

- [X] T029 [P] [US2] Add preparation, prepared-course, generation-request, summary, outcome, `AUTOMATIC_START_TIME_UNAVAILABLE`, and solver-error schemas matching the contract in `backend/app/schemas/exam_scheduling.py`
- [X] T030 [US2] Build canonical exam candidates from effective dates and every applicable active Study Type Time Window start while applying all fixed hard filters and returning `AUTOMATIC_START_TIME_UNAVAILABLE` when the proposal domain is empty in `backend/app/services/exam_optimization.py`
- [X] T031 [US2] Implement deterministic joint CP-SAT selection that maximizes scheduled exams, then inside-recommendation placements, then canonical date/time/room order, and returns only proven bounded results in `backend/app/services/exam_optimization.py`
- [X] T032 [US2] Implement canonical preparation records and opaque per-course/shared snapshots over configuration, clock date, optional teaching anchor, proposal-domain availability, semester, teaching/exam occupancy, resources, availability, eligibility, capacity, and holidays in `backend/app/services/exam_scheduling.py`
- [X] T033 [US2] Implement transactional generation, semester write-boundary claiming, exact arrangement revalidation, active-slot enforcement, configuration consumption, immutable session snapshots, partial scheduled/failed/stale/skipped outcomes, and no-save timeout handling in `backend/app/services/exam_scheduling.py`
- [X] T034 [US2] Expose preparation and generation endpoints with the specified 200/409/422/503 behavior in `backend/app/api/exam_scheduling.py`
- [X] T035 [P] [US2] Add preparation/generation request functions and typed mixed-result parsing to `client/src/api/examScheduling.ts`
- [X] T036 [US2] Implement understandable per-course mixed outcome, missing-anchor/proposal-domain guidance, and hard-constraint evidence rendering in `client/src/components/ExamGenerationResultSummary.tsx`
- [X] T037 [US2] Implement eligible-course selection, prepare/review/generate controls, stale retry guidance, and operation-state safeguards in `client/src/components/ExamGenerationPanel.tsx`
- [X] T038 [US2] Integrate exam generation and authoritative combined refresh into the selected-semester Schedule workflow in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: The P1 slice outcome is complete: every selected enabled course without an active exam receives one valid saved exam or a clear, configuration-specific non-success outcome.

---

## Phase 5: User Story 3 - Create, Review, Correct, and Delete Exams Safely (Priority: P2)

**Goal**: Make active and past exams distinguishable in the existing review, allow valid manual creation/correction, and delete exactly one confirmed exam with stale-state and preservation safeguards.

**Independent Test**: Manually create an exam, review it beside teaching sessions, accept a valid outside-recommendation override, reject every hard-rule violation, correct active and past exams safely, cancel and confirm consequence-aware deletion, provoke stale submissions, and verify only the selected exam changes and current validity refreshes.

### Tests for User Story 3 (write and observe failing first)

- [X] T039 [P] [US3] Write service tests for manual create/correct/delete, missing-anchor rejection, active and past isolation, recommendation overrides, all hard-rule errors, duplicate-active prevention, revisions and related-input snapshots, cancellation/no-op preservation, deletion consequences, and derived current validity in `backend/tests/services/test_exam_scheduling.py`
- [X] T040 [P] [US3] Write API tests for `POST /api/courses/{course_id}/exam-sessions` and `PATCH`/`DELETE /api/exam-sessions/{exam_id}`, covering 200/201/404/409/422 responses and authoritative refreshed state, in `backend/tests/api/test_exam_scheduling.py`
- [X] T041 [P] [US3] Write regression tests that resource/catalog archive or removal preserves referenced exam history and reports affected current configurations in `backend/tests/services/test_resource_catalog.py` and `backend/tests/services/test_academic_catalog.py`
- [X] T042 [P] [US3] Write client serialization and structured stale/validation error tests for manual create, correction, and confirmed deletion in `client/src/api/examScheduling.test.ts`
- [X] T043 [P] [US3] Write manual editor tests for active/past context, editable placement fields, fixed duration/context, valid outside-window and non-Study-Type-start overrides, aggregated hard errors, stale close/refresh, busy state, and keyboard operation in `client/src/components/ExamManualSessionEditor.test.tsx`
- [X] T044 [P] [US3] Write deletion-dialog tests for exact active/past consequence text, confirmation, cancellation, stale refresh, focus entry/trap/restoration, Escape, and busy-state locking in `client/src/components/ExamDeletionDialog.test.tsx`
- [X] T045 [P] [US3] Write combined-review tests for discriminated Teaching/Exam rows, Active/Past labels, required exam context, hard issues versus soft recommendation notices, shared sorting/filtering, and unchanged teaching behavior in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T046 [P] [US3] Write page orchestration tests for manual mutations, deletion, authoritative refresh, stale-state preservation, and unchanged unrelated sessions in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T047 [US3] Add manual create/update/delete request and deletion-consequence response schemas with revision and related-input token requirements in `backend/app/schemas/exam_scheduling.py`
- [X] T048 [US3] Derive current hard-validity issues for saved exams on authoritative reads, including relevant holiday/resource/session evidence and a separate soft `outsideRecommendedWindow` flag, in `backend/app/services/exam_scheduling.py`
- [X] T049 [US3] Implement atomic manual creation and correction with retained duration/configuration snapshots, final-anchor enforcement, Study Type proposal-domain independence, full hard-rule validation, one-active enforcement, semester serialization, revision checks, and related-input stale detection in `backend/app/services/exam_scheduling.py`
- [X] T050 [US3] Implement exact active/past deletion, consequence selection, confirmation/revision/snapshot enforcement, active-configuration unscheduling, and unrelated-state preservation in `backend/app/services/exam_scheduling.py`
- [X] T051 [P] [US3] Extend existing referenced-record safeguards for exam configurations and history without adding lecturer editing in `backend/app/services/resource_catalog.py` and `backend/app/services/academic_catalog.py`
- [X] T052 [US3] Expose manual create, correction, and deletion endpoints with authoritative state and structured 404/409/422 responses in `backend/app/api/exam_scheduling.py`
- [X] T053 [P] [US3] Add typed manual creation, correction, and confirmed deletion functions to `client/src/api/examScheduling.ts`
- [X] T054 [P] [US3] Implement the accessible revision-aware active/past manual placement editor in `client/src/components/ExamManualSessionEditor.tsx`
- [X] T055 [P] [US3] Implement the accessible consequence-aware single-exam deletion dialog in `client/src/components/ExamDeletionDialog.tsx`
- [X] T056 [US3] Extend the existing review through a discriminated teaching/exam view with visible lifecycle, full exam context, current hard issues, soft recommendation deviation, and shared filters in `client/src/components/DraftSchedulePanel.tsx`
- [X] T057 [US3] Wire manual create/edit/delete actions and authoritative success/stale refresh behavior into `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: All three user stories are independently verifiable, and every saved active or past exam remains planner-reviewable without weakening teaching behavior.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Prove contract fidelity, accessibility, regression-suite health, deterministic performance, and full-stack readiness for the approved slice after all required tests were authored before production behavior.

- [X] T058 Validate all routes, aliases, schemas, statuses, examples, revision tokens, snapshot tokens, and lifecycle/validity separation against `specs/012-conflict-aware-exam-scheduling/contracts/exam-scheduling.openapi.yaml`
- [X] T059 Execute all ten end-to-end, keyboard, 200%-zoom, narrow-layout, stale-state, history, and mixed-generation scenarios and record dated evidence in `specs/012-conflict-aware-exam-scheduling/quickstart.md`
- [X] T060 Run migration, exam service/optimizer/API/performance, and complete backend regression suites specified in `specs/012-conflict-aware-exam-scheduling/plan.md`
- [X] T061 Run client Vitest, ESLint, TypeScript/Vite build, and verify no Schedule/Academic Data navigation regression specified in `specs/012-conflict-aware-exam-scheduling/plan.md`
- [X] T062 Review the final diff against every FS-012 requirement and exclusion, run whitespace/conflict-marker checks, and record completion evidence in `specs/012-conflict-aware-exam-scheduling/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 - Setup**: Starts immediately; T001 precedes all production changes, while T002 and T003 can run in parallel after the branch switch.
- **Phase 2 - Foundational Persistence**: Depends on Phase 1. T004 and the passing pre-change regression baseline T005 are completed first; T006 and T007 may then proceed in parallel; T008 follows T007 and blocks story production work.
- **Phase 3 - US1 Configuration**: Depends on Phase 2 and establishes the current configuration, lifecycle, overview, and client contract required by later stories.
- **Phase 4 - US2 Generation**: Depends on US1 because generation consumes a valid current configuration and authoritative overview state.
- **Phase 5 - US3 Manual Management**: Depends on US1. It may begin alongside US2 after US1 if staffed separately, although final combined-review integration must reconcile both story additions.
- **Phase 6 - Polish**: Depends on every story selected for delivery; full-slice completion requires US1, US2, and US3.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 Configuration -> US2 Generation -> Polish
                                  `-------> US3 Manual Management -> Polish
```

- **US1 (P1)**: First independently testable increment; no dependency on another story after the foundation.
- **US2 (P1)**: Depends on US1 configuration and completes the automatic FS-012 outcome.
- **US3 (P2)**: Depends on US1 configuration; logically independent of the US2 solver, but shares the authoritative review and active-slot invariant.

### Within Each User Story

- Complete and observe the story's automated tests failing before its production tasks.
- Implement schemas and domain behavior before routes and UI integration that expose them.
- Keep server-derived lifecycle, validation, and conflict decisions authoritative; the browser only renders returned state.
- Re-read and revalidate material state inside the serialized write boundary before committing any exam mutation.
- Stop at each checkpoint and run that story's focused backend and client tests.

---

## Parallel Execution Examples

### User Story 1

```text
Parallel test tasks: T009 service | T010 API | T011 client API | T012 editor | T013 page
Parallel implementation after backend tests: T014 backend schemas | T018 client API types/functions
Then: T015 -> T016 -> T017, and T018 -> T019 -> T020
```

### User Story 2

```text
Parallel test tasks: T021 optimizer | T022 service | T023 API | T024 client API | T025 panel | T026 summary | T027 page | T028 performance
Initial parallel work: T029 schemas | T030 candidate construction
Backend dependencies: T030 -> T031; T029 -> T032; T031 + T032 -> T033; T029 + T033 -> T034
Client dependencies: T035 -> T036/T037 -> T038
```

### User Story 3

```text
Parallel test tasks: T039 service | T040 API | T041 catalog safeguards | T042 client API | T043 editor | T044 dialog | T045 review | T046 page
Parallel implementation after tests: T047-T052 backend | T053-T057 client
Independent component work after T053: T054 manual editor | T055 deletion dialog
Integration order: T048/T049/T050/T051 -> T052, and T054/T055 -> T056 -> T057
```

---

## Implementation Strategy

### Practical MVP: Both P1 Stories

1. Complete Phase 1 and Phase 2.
2. Complete US1 and validate explicit configuration independently.
3. Complete US2 and validate mixed conflict-aware generation independently.
4. Stop and demonstrate that enabled courses receive a valid exam or a clear failure while disabled and already-active courses remain unchanged.

US1 alone is a useful configuration increment but does not satisfy the stated FS-012 completion outcome; therefore the practical MVP includes US1 and US2.

### Incremental Delivery

1. **Foundation**: Supported schema and test fixtures.
2. **US1**: Explicit current configuration and active/past-safe lifecycle.
3. **US2**: Deterministic conflict-aware generation and understandable outcomes—P1 MVP complete.
4. **US3**: Unified review, manual correction, and protected deletion—approved slice complete.
5. **Polish**: Contract, dependency regression, accessibility, deterministic performance, and full-suite evidence.

### Scope Guardrails

- Do not add student registration, grading, invigilator rosters, lecturer editing, external exam/room systems, publication workflow, bulk deletion, or a new calendar workspace.
- Do not turn the recommended date range or Study Type windows into manual-placement hard constraints.
- Do not reuse teaching draft persistence or teaching-style non-blocking alerts for exams.
- Do not add a fixed or planner-managed exam-type catalog.
- Do not auto-move or auto-delete an exam that later becomes invalid.

---

## Notes

- `[P]` tasks use different files or independent test surfaces and have no incomplete same-phase dependency.
- Tests precede implementation in every user-story phase as required by Constitution v1.1.0.
- Task descriptions name exact paths and the contract behavior needed to execute them without additional requirements discovery.
- Commit after a verified task or coherent task group; do not commit generated or manual exam behavior before its focused tests pass.
