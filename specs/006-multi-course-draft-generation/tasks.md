# Tasks: Multi-Course Draft Generation

**Input**: Design documents from `/specs/006-multi-course-draft-generation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update test tasks before production implementation tasks and confirm the new tests fail for the intended reason before implementing each story.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared course-semester, revision, and transaction foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on an incomplete task
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup (Shared Fixtures And Baseline)

**Purpose**: Prepare reusable multi-course test data and preserve evidence of the existing Slice 1-5 baseline before production changes.

- [X] T001 [P] Create reusable backend test builders for two semesters, multiple courses, saved/default constraints, existing drafts, and manual edits in backend/tests/multi_course_fixtures.py
- [X] T002 [P] Extend frontend fixture builders with multiple courses, semester-scoped schedules, draft revisions, replacement snapshots, and batch outcomes in client/src/test/draftScheduleFixtures.ts
- [X] T003 Run the existing backend and frontend regression suites and record any pre-existing failures in specs/006-multi-course-draft-generation/quickstart.md

---

## Phase 2: Foundational (Blocking Course-Semester, Revision, And Transaction Work)

**Purpose**: Make Draft Schedules safe to retain by course and semester and establish transaction ownership and optimistic revisions required by every batch story.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for the shared foundation (write before implementation)

- [X] T004 [P] Add migration tests for preserved existing rows, revision backfill, same-course schedules in different semesters, and duplicate course-semester rejection in backend/tests/db/test_migrations.py
- [X] T005 [P] Add repository tests for semester-specific Draft Schedule reads/replacements, cross-semester retention, draft revision increments, constraint revision increments, and unchanged saved-constraint revisions in backend/tests/services/test_draft_schedule_repository.py
- [X] T006 Add repository transaction tests proving schedule and constraint mutations flush without committing and can be rolled back as one unit in backend/tests/services/test_draft_schedule_repository.py
- [X] T007 [P] Add single-course API regression tests for explicit semester reads, atomic generation persistence, manual-edit revision increments, and preservation of another semester's draft in backend/tests/api/test_draft_schedule.py
- [X] T008 [P] Add client API tests for semester-explicit single-course Draft Schedule reads and revision parsing in client/src/api/draftSchedule.test.ts

### Implementation for the shared foundation

- [X] T009 [P] Add DraftSchedule and GenerationConstraintSet revision fields plus course-semester Draft Schedule uniqueness to backend/app/models/planning.py
- [X] T010 Implement the SQLite-compatible revision and course-semester uniqueness migration with downgrade support in backend/app/db/migrations/0002_course_semester_drafts.py
- [X] T011 Refactor Draft Schedule and constraint repository reads, replacements, clears, saves, and manual edits to be semester-specific, revision-aware, and flush-only in backend/app/services/draft_schedule_repository.py
- [X] T012 Add Draft Schedule revision serialization and require semesterId on the single-course read contract in backend/app/schemas/draft_schedule.py and backend/app/api/draft_schedule.py
- [X] T013 Move single-course generation, constraint clearing, and manual-edit commit/rollback ownership to the API boundary in backend/app/api/draft_schedule.py
- [X] T014 Update single-course client reads and response types for semesterId and revision without changing the existing generation/edit workflow in client/src/api/draftSchedule.ts

**Checkpoint**: Existing single-course generation and manual editing are transaction-safe, Draft Schedules coexist by course and semester, and optimistic revisions are available to batch work.

---

## Phase 3: User Story 1 - Generate Several Course Drafts (Priority: P1) MVP

**Goal**: Office staff select 2-50 distinct courses for one semester, generate each independently with its own saved constraints or defaults, and receive one successful outcome per course when all inputs are valid.

**Independent Test**: Select two courses without same-semester drafts, give one saved custom constraints and leave the other on Study Type/semester defaults, generate both, and verify the result and semester overview contain two independently generated schedules using the correct per-course inputs.

### Tests for User Story 1 (write before implementation)

- [X] T015 [P] [US1] Add orchestration tests for initial 2-50 selection validation, duplicate rejection, nonexistent-semester rejection, request-order preservation, and canonical unavailable-course preparation in backend/tests/services/test_multi_course_generation.py
- [X] T016 [US1] Add orchestration tests proving every course loads only its own saved constraints or defaults, the batch service accepts no shared constraint set, and an all-success execution persists exact ordered outcomes in backend/tests/services/test_multi_course_generation.py
- [X] T017 [P] [US1] Add API contract tests for POST /api/draft-schedules/batch/prepare validation and canonical prepared snapshots in backend/tests/api/test_multi_course_generation.py
- [X] T018 [US1] Add API contract tests for all-success POST /api/draft-schedules/batch/generate summary counts, ordered outcomes, saved schedules, and active constraints in backend/tests/api/test_multi_course_generation.py
- [X] T019 [P] [US1] Add client API tests for prepare/generate request serialization, typed response parsing, and 2-50 initial limits in client/src/api/multiCourseDraftGeneration.test.ts
- [X] T020 [P] [US1] Add page tests for separate One course/Several courses modes, checkbox selection, selected count, clear selection, 2-50 validation, focused-editor isolation, and all-success display in client/src/pages/CourseSchedulePage.test.tsx
- [X] T021 [US1] Add test-first 50-course API timing and bounded-read regressions using file-backed SQLite, asserting complete ordered outcomes within 10 seconds and query/repository-call counts that avoid per-course database loading in backend/tests/services/test_multi_course_generation.py and backend/tests/api/test_multi_course_generation.py

### Implementation for User Story 1

- [X] T022 [P] [US1] Define batch operation, preparation, prepared-course, execution, summary, outcome, and request-failure schemas from the OpenAPI contract in backend/app/schemas/multi_course_generation.py
- [X] T023 [US1] Implement read-only preparation validation and bounded bulk loading of canonical courses, same-semester draft snapshots, constraints, and planning inputs in backend/app/services/multi_course_generation.py
- [X] T024 [US1] Implement all-success candidate generation from the preloaded per-course input map using each course's saved constraints or normalized defaults and the existing pure generator in backend/app/services/multi_course_generation.py
- [X] T025 [US1] Expose preparation and generation endpoints with initial selection validation in backend/app/api/multi_course_generation.py
- [X] T026 [US1] Register the multi-course router without changing existing routes in backend/app/main.py
- [X] T027 [P] [US1] Implement typed prepare/generate API functions and user-safe request error mapping in client/src/api/multiCourseDraftGeneration.ts
- [X] T028 [P] [US1] Build the Several courses mode, checkbox picker, selected-count/limit feedback, clear action, and per-course-constraint explanation in client/src/components/MultiCourseGenerationPanel.tsx
- [X] T029 [US1] Integrate separate single/batch selections and the all-success batch action into client/src/pages/CourseSchedulePage.tsx
- [X] T030 [US1] Style the batch mode, scrollable course picker, selection feedback, and responsive controls in client/src/App.css

**Checkpoint**: User Story 1 is independently functional as the MVP for valid, first-time course selections.

---

## Phase 4: User Story 2 - Handle Partial Success And Retry Failures (Priority: P2)

**Goal**: Expected failures remain course-local, successful courses persist, failed data stays unchanged, and office staff can retry only the 1-50 failed courses while unexpected failures roll back the whole attempt.

**Independent Test**: Generate one valid course with one invalid course, verify only the valid course changes, inspect understandable per-course reasons, correct the failure, and retry that course alone without regenerating the success.

### Tests for User Story 2 (write before implementation)

- [X] T031 [P] [US2] Add orchestration tests for partial success, all expected failures, courses unavailable before or after preparation, complete failed-course data preservation, exact summary invariants, and non-blocking overlaps in backend/tests/services/test_multi_course_generation.py
- [X] T032 [US2] Add orchestration tests for 1-50 failed-only retry, stale constraint snapshots, per-course savepoint rollback, and injected unexpected failure rolling back the outer transaction in backend/tests/services/test_multi_course_generation.py
- [X] T033 [P] [US2] Add API tests for understandable failure codes/reasons, exactly one outcome per request item, retry size rules, all-failed responses, and operation-wide 500 responses without false successes in backend/tests/api/test_multi_course_generation.py
- [X] T034 [P] [US2] Add client API tests for course failures, malformed/oversized retry rejection, and operation-wide failure parsing in client/src/api/multiCourseDraftGeneration.test.ts
- [X] T035 [P] [US2] Add page tests for partial/all-failed summaries, every failure reason, failed-only one-course retry, successful-course exclusion, operation-wide errors, double-submit prevention, and current-session-only result retention in client/src/pages/CourseSchedulePage.test.tsx

### Implementation for User Story 2

- [X] T036 [US2] Extend orchestration with course-level failure mapping, unavailable-course outcomes, immutable constraint snapshots, nested savepoints, and one outer commit/rollback boundary in backend/app/services/multi_course_generation.py
- [X] T037 [US2] Map expected course failures to normal results and unexpected exceptions to BATCH_OPERATION_FAILED without uncommitted outcomes in backend/app/api/multi_course_generation.py
- [X] T038 [P] [US2] Build aggregate counts, ordered success/failure rows, all failure reasons, and Retry failed courses action in client/src/components/BatchResultSummary.tsx
- [X] T039 [US2] Integrate failed-only retry, fresh retry preparation, transient result state, operation-wide error state, and scoped preparation/execution loading into client/src/pages/CourseSchedulePage.tsx
- [X] T040 [US2] Style result summaries, outcome statuses, failure details, retry controls, and operation-wide errors in client/src/App.css

**Checkpoint**: User Stories 1 and 2 support all-success, partial-success, all-expected-failure, retry, and atomic unexpected-failure behavior.

---

## Phase 5: User Story 3 - Safely Replace Existing Semester Drafts (Priority: P3)

**Goal**: Same-semester replacement targets and manual-edit loss are identified before execution, cancellation writes nothing, confirmation replaces only successful targets, and stale drafts preserve newer data.

**Independent Test**: Prepare a mixture of same-semester replacement and first-time courses, cancel and verify no changes, then confirm and verify successful same-semester replacement while another-semester schedule remains unchanged.

### Tests for User Story 3 (write before implementation)

- [X] T041 [P] [US3] Add service tests for same-semester-only replacement discovery, draft ID/revision snapshots, no-draft-to-new-draft staleness, changed-draft staleness, current confirmation on retry, and cross-semester retention in backend/tests/services/test_multi_course_generation.py
- [X] T042 [P] [US3] Add API tests for replacementCourseIds, missing-confirmation 409 responses, malformed prepared snapshots, confirmed replacement, stale draft outcomes, and other-semester preservation in backend/tests/api/test_multi_course_generation.py
- [X] T043 [P] [US3] Add page tests for replacement identification, manual-edit warning, cancel-without-execution, immutable confirmed snapshots, one execution submission, and fresh confirmation on stale retry in client/src/pages/CourseSchedulePage.test.tsx

### Implementation for User Story 3

- [X] T044 [US3] Implement expected Draft Schedule ID/revision comparison and conditional same-semester replacement with STALE_DRAFT_SCHEDULE outcomes in backend/app/services/multi_course_generation.py
- [X] T045 [US3] Enforce replacement confirmation and prepared-snapshot consistency before execution in backend/app/api/multi_course_generation.py
- [X] T046 [P] [US3] Build the replacement list, manual-edit loss warning, confirm action, and cancel action in client/src/components/ReplacementConfirmationDialog.tsx
- [X] T047 [US3] Integrate immutable preparation snapshots, confirmation/cancellation, stale-result retry preparation, and no-write cancellation into client/src/pages/CourseSchedulePage.tsx
- [X] T048 [US3] Style the replacement dialog, replacement-course list, warning, and confirmation actions in client/src/App.css

**Checkpoint**: User Stories 1-3 safely handle first-time generation, expected failures, retry, confirmation, stale writes, and cross-semester retention.

---

## Phase 6: User Story 4 - Review The Semester After Generation (Priority: P4)

**Goal**: Every normal batch result refreshes the complete selected-semester overview once, keeps Slice 5 conflicts non-blocking and visible, and leaves the single-course workflow intact.

**Independent Test**: Generate independently placed courses that overlap by lecturer, room, or Cohort and verify the refreshed overview shows new and pre-existing schedules with alerts while both batch outcomes remain successful.

### Tests for User Story 4 (write before implementation)

- [X] T049 [P] [US4] Add API regression tests that a post-batch semester overview contains generated and pre-existing drafts with recalculated lecturer, room, and Cohort alerts while batch outcomes stay successful in backend/tests/api/test_multi_course_generation.py
- [X] T050 [P] [US4] Add page tests for one overview refresh after every normal result, retained last-known overview/result on refresh failure, refresh retry, filter/edit reset after success, and result-semester restoration before retry in client/src/pages/CourseSchedulePage.test.tsx
- [X] T051 [P] [US4] Extend component regressions for externally resetting overview filters/open edits while preserving alert rendering and manual editing in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 4

- [X] T052 [US4] Coordinate normal-result overview refresh, refresh retry, result-semester restoration, scoped async states, and successful-refresh interaction reset in client/src/pages/CourseSchedulePage.tsx
- [X] T053 [US4] Add a page-controlled reset seam for filters and open session edits without changing review, alert, or manual-edit behavior in client/src/components/DraftSchedulePanel.tsx
- [X] T054 [US4] Style busy-but-mounted overview and refresh-failure recovery states in client/src/App.css

**Checkpoint**: All four Slice 6 stories are independently testable and the full batch-to-review workflow is complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final performance, documentation, regression, usability, and scope verification across Slice 6.

- [X] T055 [P] Document batch preparation/execution, partial success, transaction behavior, stale failures, and semester-scoped single-course reads in backend/README.md
- [X] T056 [P] Document Several courses selection, replacement confirmation, failure retry, transient results, and overview refresh behavior in client/README.md
- [X] T057 Run the focused backend verification commands and record results in specs/006-multi-course-draft-generation/quickstart.md
- [X] T058 Run npm run test, npm run lint, and npm run build and record results in specs/006-multi-course-draft-generation/quickstart.md
- [ ] T059 Execute and record the at-least-10-participant unaided usability protocol, including the two-minute named-semester/course selection and generation-start timing, the comprehension and failed-only retry pass rates, the three-run reference-environment performance median, and the remaining all-success, partial/retry, cancellation, cross-semester, stale-data, alert, transient-state, and rollback scenarios in specs/006-multi-course-draft-generation/quickstart.md
- [X] T060 Review the complete Slice 6 git diff for conflict-aware placement, automatic conflict resolution, persistent batch history, background processing, holiday/exam behavior, dashboards, eligibility administration, multiple lecturer/room behavior, or session CRUD expansion and record the scope-audit result in specs/006-multi-course-draft-generation/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks every user story because all stories require course-semester identity, revisions, and boundary-owned transactions.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP.
- **Phase 4 US2**: Depends on Phase 2; it extends the US1 orchestration/result seams with partial success and retry.
- **Phase 5 US3**: Depends on Phase 2; it can be developed alongside US2 after the preparation/execution contracts from US1 exist.
- **Phase 6 US4**: Depends on the normal batch result from US1 and is most useful after US2/US3 outcomes are available.
- **Phase 7 Polish**: Depends on all selected user stories being complete.

### User Story Dependencies

- **US1 Generate Several Course Drafts (P1)**: Independent after the shared foundation; recommended MVP.
- **US2 Handle Partial Success And Retry Failures (P2)**: Independently testable with mixed-validity courses after the US1 batch contract/service seam exists.
- **US3 Safely Replace Existing Semester Drafts (P3)**: Independently testable with replacement fixtures after the US1 preparation seam exists; may proceed in parallel with US2 while coordinating shared service/API files.
- **US4 Review The Semester After Generation (P4)**: Independently testable with a normal batch result and existing Slice 5 overview/alert behavior; integrates the earlier stories into the review loop.

### Within Each User Story

- Write and run the story's tests before its production tasks; confirm failures reflect missing Slice 6 behavior.
- Define/extend schemas before service and route integration.
- Keep candidate generation side-effect free before persistence work.
- Complete service behavior before API route integration.
- Complete client API behavior before page/component integration.
- Finish the independent test before moving to the next priority.

## Parallel Opportunities

- T001 and T002 can run in parallel during setup.
- T004, T005, T007, and T008 can run in parallel as foundation tests; T009 can proceed separately once expected model behavior is understood.
- T015, T017, T019, and T020 can run in parallel for US1; coordinate T015/T016/T021 and T017/T018 because each group shares a file.
- T031, T033, T034, and T035 can run in parallel for US2; T031/T032 share a service-test file.
- T041, T042, and T043 can run in parallel for US3; service, API, and UI work can then proceed in parallel where files do not overlap.
- T049, T050, and T051 can run in parallel for US4.
- T055 and T056 can run in parallel during polish.

## Parallel Example: User Story 1

```text
Task: "T015 [US1] Add orchestration selection/constraint-isolation tests in backend/tests/services/test_multi_course_generation.py"
Task: "T017 [US1] Add preparation API contract tests in backend/tests/api/test_multi_course_generation.py"
Task: "T019 [US1] Add batch client API tests in client/src/api/multiCourseDraftGeneration.test.ts"
Task: "T020 [US1] Add several-courses page tests in client/src/pages/CourseSchedulePage.test.tsx"
```

## Parallel Example: User Story 2

```text
Task: "T031 [US2] Add partial/all-failure preservation tests in backend/tests/services/test_multi_course_generation.py"
Task: "T033 [US2] Add per-course and operation-wide API failure tests in backend/tests/api/test_multi_course_generation.py"
Task: "T034 [US2] Add client failure parsing tests in client/src/api/multiCourseDraftGeneration.test.ts"
Task: "T035 [US2] Add result/retry page tests in client/src/pages/CourseSchedulePage.test.tsx"
```

## Parallel Example: User Story 3

```text
Task: "T041 [US3] Add replacement/stale/cross-semester service tests in backend/tests/services/test_multi_course_generation.py"
Task: "T042 [US3] Add confirmation and stale API tests in backend/tests/api/test_multi_course_generation.py"
Task: "T043 [US3] Add confirmation/cancellation page tests in client/src/pages/CourseSchedulePage.test.tsx"
```

## Parallel Example: User Story 4

```text
Task: "T049 [US4] Add post-batch overview/alert API regressions in backend/tests/api/test_multi_course_generation.py"
Task: "T050 [US4] Add overview refresh/recovery page tests in client/src/pages/CourseSchedulePage.test.tsx"
Task: "T051 [US4] Add overview interaction-reset component regressions in client/src/components/DraftSchedulePanel.test.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup and capture the Slice 1-5 baseline.
2. Complete Phase 2 course-semester, revision, and transaction foundation.
3. Complete Phase 3 US1 tests before implementation.
4. Validate two valid first-time courses independently use saved/default constraints and produce one outcome each.
5. Stop and demo the MVP before adding failure, replacement, and review refinements.

### Incremental Delivery

1. Deliver US1 for valid multi-course selection and generation.
2. Add US2 for partial/all failure, preservation, atomic rollback, and failed-only retry.
3. Add US3 for replacement confirmation, cancellation, stale-data safety, and cross-semester retention.
4. Add US4 for complete overview refresh, non-blocking alerts, and single-course regression safety.
5. Run the focused quickstart after every story and the full quickstart during polish.

### Parallel Team Strategy

After Phase 2, service tests, API tests, and frontend tests can be prepared concurrently. US2 and US3 may proceed in parallel after US1 establishes the contracts, but edits to `backend/app/services/multi_course_generation.py`, `backend/app/api/multi_course_generation.py`, `client/src/pages/CourseSchedulePage.tsx`, and `client/src/App.css` must be coordinated.

## Notes

- [P] tasks touch different files or have no dependency on incomplete work.
- [US1]-[US4] labels map directly to the prioritized user stories in spec.md.
- Keep the existing pure placement algorithm in backend/app/services/schedule_generation.py unchanged.
- Generate each course without considering other courses' occupancy; overlaps remain Slice 5 non-blocking alerts.
- Do not persist batch operations, summaries, retry sets, or conflict alerts.
- Use prepared Draft Schedule revisions and active constraint snapshots as concurrency preconditions.
- Use one outer transaction plus per-course savepoints; expected course failures are partial, unexpected failures are atomic.
- Preserve the focused single-course editor and never use its unsaved values as batch inputs.
- Use specs/006-multi-course-draft-generation/contracts/openapi.yaml as the cross-stack contract.
