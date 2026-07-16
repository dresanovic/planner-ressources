# Tasks: FS-009 Manual Session Management

**Input**: Design documents from `specs/009-manual-session-management/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/manual-session-management.openapi.yaml`, `quickstart.md`

**Tests**: Tests are required by the project constitution. Test tasks appear before production implementation tasks in every phase, and each implementation phase ends with focused verification.

**Organization**: Tasks are grouped by user story so manual creation, single-session deletion, and complete-draft clearing remain independently testable. This task list is strictly limited to FS-009 and does not implement FS-008 resource eligibility, optimization, drag/drop, or later calendar-workspace behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same phase because it uses different files or independent test seams.
- **[Story]**: Maps the task to User Story 1, 2, or 3 from `spec.md`.
- Every task names the exact repository file or documentation path it changes or validates.

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Prepare reusable FS-009 fixtures without changing production behavior or adding dependencies.

- [X] T001 [P] Extend repository fixtures with empty, partial, over-scheduled, constrained, and cross-semester course drafts in `backend/tests/services/test_draft_schedule_repository.py`
- [X] T002 [P] Extend API fixtures with capacity-valid/invalid rooms, saved constraints, related-course alerts, and multiple semesters in `backend/tests/api/test_draft_schedule.py`
- [X] T003 [P] Add manual-mutation, selected-course progress, nullable-draft, and stale-error fixtures in `client/src/test/draftScheduleFixtures.ts`

**Checkpoint**: Shared backend and frontend test data can express every FS-009 state without a schema migration.

---

## Phase 2: Foundational Contracts and Interaction Shell

**Purpose**: Establish shared mutation shapes, error handling, and accessible confirmation behavior used by all three stories.

**CRITICAL**: Complete this phase before any user-story production implementation.

### Tests for Shared Foundations (write before implementation)

- [X] T004 [P] Add failing serialization tests for the common mutation result, validation failures, nullable Draft Schedule, and stale conflict response in `backend/tests/api/test_draft_schedule.py`
- [X] T005 [P] Add failing client contract tests for mutation-result parsing, validation errors, network failures, and `STALE_DRAFT` mapping in `client/src/api/draftSchedule.test.ts`
- [X] T006 [P] Add failing accessibility tests for modal labelling, initial focus, focus trapping, Escape cancellation, busy-state controls, and focus restoration in `client/src/components/ScheduleDeletionDialog.test.tsx`

### Shared Implementation

- [X] T007 Implement shared mutation response, progress, failure-code, and stale-conflict schemas in `backend/app/schemas/draft_schedule.py`
- [X] T008 [P] Add shared mutation result, failure, and stale-conflict types plus error parsing in `client/src/api/draftSchedule.ts`
- [X] T009 Implement the reusable accessible confirmation shell with action-specific content slots in `client/src/components/ScheduleDeletionDialog.tsx`

**Checkpoint**: Shared cross-stack contracts and the confirmation shell are ready; no user-story write endpoint is enabled yet.

---

## Phase 3: User Story 1 - Add One Draft Session Manually (Priority: P1) MVP

**Goal**: A planner can add one structurally valid manual Draft Session to an empty or partial course-semester draft and immediately see accurate remaining units and refreshed non-blocking alerts.

**Independent Test**: Select a course-semester with remaining units, create one session with a calculated then optionally overridden end time and a capacity-valid room, and verify the session, remaining units, constraints, and complete-semester alerts after refresh.

### Tests for User Story 1 (write before implementation)

- [X] T010 [P] [US1] Add failing repository tests for derived progress, first-draft snapshot creation, append/revision behavior, concurrent first-draft and append attempts, latest-state remaining-unit and duplicate-date enforcement, lecturer/cohort inheritance, neutral manual window fields, and transaction rollback in `backend/tests/services/test_draft_schedule_repository.py`
- [X] T011 [P] [US1] Add failing API tests for additive planning-option `cohortSize`, `POST /api/courses/{course_id}/draft-schedule/sessions`, mutation results, current-source validation, concurrent creation without over-scheduling, all hard failure codes, non-blocking alerts, unchanged generation/regeneration behavior, and constraint/source preservation in `backend/tests/api/test_planning_options.py` and `backend/tests/api/test_draft_schedule.py`
- [X] T012 [P] [US1] Add failing client tests for additive `cohortSize` planning options and the manual-create API request/result/error contract in `client/src/api/planningOptions.test.ts` and `client/src/api/draftSchedule.test.ts`
- [X] T013 [P] [US1] Add failing unit tests for remaining-unit derivation and default end-time calculation covering one/multiple units, break minutes, valid earlier and later overrides with explicit units remaining authoritative, recalculation after either override, invalid input, and midnight overflow in `client/src/components/manualSessionUtils.test.ts`
- [X] T014 [P] [US1] Add failing page tests for empty/partial progress, form labels, inherited context, capacity-filtered rooms, earlier/later override retention, filter/view preservation, Draft terminology, polite announcements, busy and mutation-failure states, validation errors, successful refresh, and alert updates in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 1

- [X] T015 [P] [US1] Expose current course `cohortSize` through planning-option schemas and mapping in `backend/app/schemas/planning_options.py` and `backend/app/api/planning_options.py`
- [X] T016 [US1] Implement reusable new-draft snapshot construction, scheduled/remaining calculation, hard validation, and transactional manual-session creation that conditionally claims an existing parent revision or resolves a concurrent first-draft insert, then revalidates against the latest saved state before persistence in `backend/app/services/draft_schedule_repository.py`
- [X] T017 [US1] Add the manual-create request/failure schemas, `POST` route, commit/rollback handling, mutation-result mapping, and existing validation-alert serialization in `backend/app/schemas/draft_schedule.py` and `backend/app/api/draft_schedule.py`
- [X] T018 [P] [US1] Add `cohortSize` client typing plus pure progress/end-time helpers that keep explicit units authoritative and reject midnight rollover in `client/src/api/planningOptions.ts` and `client/src/components/manualSessionUtils.ts`
- [X] T019 [US1] Implement the typed manual-create API call and structured `404`/`422`/network error handling in `client/src/api/draftSchedule.ts`
- [X] T020 [US1] Add selected-course scheduled/remaining indicators and the manual-session editor with native labelled inputs, inherited lecturer/cohort, capacity-valid rooms, calculated editable end time, and polite announcements in `client/src/pages/CourseSchedulePage.tsx`
- [X] T021 [US1] Orchestrate manual-create busy/error/success state and complete-semester refresh without resetting filters, and normalize mixed manual/generated overview wording to “Draft” in `client/src/pages/CourseSchedulePage.tsx` and `client/src/components/DraftSchedulePanel.tsx`
- [X] T022 [US1] Run the focused US1 backend/client tests and record creation, hard-validation, remaining-unit, and alert-refresh evidence in `specs/009-manual-session-management/quickstart.md`

**Checkpoint**: User Story 1 is a deployable MVP; manual creation works from empty or partial state without any deletion feature.

---

## Phase 4: User Story 2 - Delete One Draft Session (Priority: P2)

**Goal**: A planner can confirm and delete exactly one generated or manual session, including the last session, with accurate progress, alert refresh, and stale-state protection.

**Independent Test**: Cancel then confirm deletion of one selected session, verify only that session is removed and progress/alerts refresh, repeat for a last session, and prove an outdated parent identity or revision deletes nothing until reconfirmed.

### Tests for User Story 2 (write before implementation)

- [X] T023 [P] [US2] Add failing repository tests for atomic parent identity/revision claim, one-of-many deletion, last-session parent removal, over-scheduled progress, stale rollback, and source/constraint preservation in `backend/tests/services/test_draft_schedule_repository.py`
- [X] T024 [P] [US2] Add failing API tests for `DELETE /api/draft-sessions/{session_id}`, expected parent identity/revision, nullable draft result, refreshed related alerts, and `409 STALE_DRAFT` for a missing confirmed target or changed parent in `backend/tests/api/test_draft_schedule.py`
- [X] T025 [P] [US2] Add failing client API tests for single-delete query parameters, mutation result, and stale-target/network failures in `client/src/api/draftSchedule.test.ts`
- [X] T026 [P] [US2] Add failing dialog tests for single-session date/time/course/semester context, removed units, resulting remainder, last-session consequence, cancel, confirm, stale notice, and destructive button naming in `client/src/components/ScheduleDeletionDialog.test.tsx`
- [X] T027 [P] [US2] Add failing overview/page tests for Delete actions in list and weekly modes, filter preservation, related-alert refresh, last-session empty state, cancelled writes, and refreshed reconfirmation after stale failure in `client/src/components/DraftSchedulePanel.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 2

- [X] T028 [US2] Implement conditional Draft Schedule identity/revision claiming, transactional single-session deletion, surviving-parent revision behavior, last-session ORM parent deletion, and progress recomputation in `backend/app/services/draft_schedule_repository.py`
- [X] T029 [US2] Add the single-session `DELETE` route, expected identity/revision parameters, `409 STALE_DRAFT` mapping for missing or changed confirmed targets, rollback, and mutation-result response in `backend/app/api/draft_schedule.py`
- [X] T030 [P] [US2] Implement the typed single-session delete call with expected identity/revision parameters in `client/src/api/draftSchedule.ts`
- [X] T031 [US2] Add single-session consequence rendering and stale/cancel/confirm behavior to `client/src/components/ScheduleDeletionDialog.tsx`
- [X] T032 [US2] Add contextual Delete controls beside Edit in list and weekly views and emit the selected session plus parent revision snapshot from `client/src/components/DraftSchedulePanel.tsx`
- [X] T033 [US2] Orchestrate confirmation state, mutation busy state, success refresh, stale refresh/message, focus restoration, and required renewed confirmation in `client/src/pages/CourseSchedulePage.tsx`
- [X] T034 [US2] Run the focused US2 backend/client tests and record cancellation, exact-scope deletion, last-session cleanup, over-scheduled progress, alert refresh, and stale-reconfirmation evidence in `specs/009-manual-session-management/quickstart.md`

**Checkpoint**: User Story 2 works independently with pre-existing generated sessions; manual creation is not required to prove single-session deletion.

---

## Phase 5: User Story 3 - Clear One Course-Semester Draft (Priority: P3)

**Goal**: A planner can explicitly clear every session for one course in one semester while preserving every source record, saved generation constraint, other course, and other semester.

**Independent Test**: Cancel then confirm clearing a mixed-origin multi-session draft, verify only the selected course-semester parent and sessions disappear, all course units remain, constraints/source/other drafts survive, alerts refresh, and stale confirmation deletes nothing.

### Tests for User Story 3 (write before implementation)

- [X] T035 [P] [US3] Add failing repository tests for complete ORM parent deletion, no retained empty draft, current progress, cross-course/cross-semester isolation, source/constraint preservation, and stale rollback in `backend/tests/services/test_draft_schedule_repository.py`
- [X] T036 [P] [US3] Add failing API tests for complete-draft `DELETE`, semester plus expected parent identity/revision, nullable result, refreshed alerts, and `409 STALE_DRAFT` for a missing confirmed draft or changed parent in `backend/tests/api/test_draft_schedule.py`
- [X] T037 [P] [US3] Add failing client API tests for complete-draft query parameters, nullable result, and stale-target/network failures in `client/src/api/draftSchedule.test.ts`
- [X] T038 [P] [US3] Add failing dialog/page tests for course/semester/session-count/full-remainder context, preservation copy, cancel, selected-course-only action, success refresh, no-draft state, and stale reconfirmation in `client/src/components/ScheduleDeletionDialog.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T039 [US3] Implement transactional complete course-semester ORM parent deletion with atomic identity/revision claim, source/constraint isolation, and full remaining-unit result in `backend/app/services/draft_schedule_repository.py`
- [X] T040 [US3] Add the course-draft `DELETE` route with semester and expected identity/revision parameters, `409 STALE_DRAFT` mapping for a missing or changed confirmed draft, rollback, and nullable mutation result in `backend/app/api/draft_schedule.py`
- [X] T041 [P] [US3] Implement the typed complete-draft delete call in `client/src/api/draftSchedule.ts`
- [X] T042 [US3] Add complete-draft consequence content to `client/src/components/ScheduleDeletionDialog.tsx` and selected-course clear action, success/stale refresh, and disabled no-draft state to `client/src/pages/CourseSchedulePage.tsx`
- [X] T043 [US3] Run the focused US3 backend/client tests and record cancellation, full clearing, source/constraint preservation, isolation, alert cleanup, and stale-reconfirmation evidence in `specs/009-manual-session-management/quickstart.md`

**Checkpoint**: All three FS-009 user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Prove regression safety, accessibility, performance, documentation, and measurable completion across the complete slice.

- [X] T044 [P] Run the existing and test-first backend regression coverage for generation/regeneration, manual editing, multi-course behavior, constraint revisions, and derived validation alerts in `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_multi_course_generation.py`, and `backend/tests/services/test_draft_schedule_validation.py`, then record results in `specs/009-manual-session-management/quickstart.md`
- [X] T045 [P] Run the existing and test-first frontend regression and accessibility coverage for filter/view preservation, Draft terminology, polite progress announcements, keyboard dialog behavior, and mutation failure states in `client/src/components/ScheduleDeletionDialog.test.tsx`, `client/src/components/DraftSchedulePanel.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx`, then record results in `specs/009-manual-session-management/quickstart.md`
- [X] T046 [P] Document manual-create/delete endpoints, error codes, revision requirements, derived progress, and preserved constraints/source data in `backend/README.md`
- [X] T047 [P] Document the selected-course manual workflow, end-time override, confirmation behavior, stale refresh, and remaining-unit interpretation in `client/README.md`
- [X] T048 Execute all eight end-to-end scenarios and the one-second reference-environment timing, then record results and residual risks in `specs/009-manual-session-management/quickstart.md`
- [ ] T049 Conduct the specified at-least-10-participant unaided usability review for manual creation and deletion-scope comprehension and record anonymized aggregate evidence in `specs/009-manual-session-management/quickstart.md`
- [X] T050 Run full `python -m pytest`, `npm test`, `npm run lint`, and `npm run build` verification and record command outcomes in `specs/009-manual-session-management/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: No dependencies; T001–T003 can run in parallel.
- **Phase 2 — Foundations**: Depends on Phase 1 and blocks production implementation for all stories. T004–T006 are failing tests written in parallel; T007–T009 implement only after their corresponding tests fail.
- **Phase 3 — User Story 1**: Depends on Phase 2 and is the recommended MVP.
- **Phase 4 — User Story 2**: Depends on Phase 2. It can be implemented and tested against existing generated sessions without User Story 1.
- **Phase 5 — User Story 3**: Depends on Phase 2. It can be implemented and tested against an existing generated draft without User Stories 1 or 2, although sequential delivery reduces shared-file conflicts.
- **Phase 6 — Polish**: Depends on every user story selected for delivery; T048–T050 require all three stories.

### User Story Dependency Graph

```text
Phase 1 Setup
      |
Phase 2 Shared foundations
   /      |       \
US1 P1   US2 P2   US3 P3
   \      |       /
 Phase 6 cross-cutting verification
```

### Within Each User Story

- Write the phase's failing repository, API, client, component, and page tests before production changes.
- Implement backend repository behavior before the corresponding FastAPI route.
- Implement typed client calls before page orchestration.
- Refresh the complete semester overview after every successful or stale mutation before asserting remaining units and alerts.
- Finish the phase's focused verification task before moving to the next story.

### Parallel Opportunities

- T001–T003 prepare independent backend service, backend API, and client fixtures.
- T004–T006 cover independent backend contract, client contract, and accessible-dialog seams.
- In US1, T010–T014 can be written in parallel; after they fail, T015 and T016 can proceed in parallel, as can backend work and T018.
- In US2, T023–T027 can be written in parallel; after they fail, backend T028–T029 and client T030–T032 can proceed with coordinated contract ownership.
- In US3, T035–T038 can be written in parallel; after they fail, backend T039–T040 and client T041–T042 can proceed with coordinated contract ownership.
- T044–T045 execute regression suites whose required additions are made test-first in T006 and the user-story test tasks; T046–T047 cover independent documentation files.
- US1, US2, and US3 are behaviorally independent after Phase 2, but parallel implementers must coordinate edits to `draft_schedule_repository.py`, `draft_schedule.py`, `draftSchedule.ts`, `ScheduleDeletionDialog.tsx`, and `CourseSchedulePage.tsx`.

---

## Parallel Example: User Story 1

```text
Task T010: Repository tests in backend/tests/services/test_draft_schedule_repository.py
Task T011: API tests in backend/tests/api/test_draft_schedule.py
Task T012: Client contract tests in client/src/api/planningOptions.test.ts and client/src/api/draftSchedule.test.ts
Task T013: Calculation tests in client/src/components/manualSessionUtils.test.ts
Task T014: Page journey tests in client/src/pages/CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 2

```text
Task T023: Repository deletion/stale tests in backend/tests/services/test_draft_schedule_repository.py
Task T024: Single-delete API tests in backend/tests/api/test_draft_schedule.py
Task T025: Client delete contract tests in client/src/api/draftSchedule.test.ts
Task T026: Single-confirmation tests in client/src/components/ScheduleDeletionDialog.test.tsx
Task T027: Overview/page orchestration tests in DraftSchedulePanel.test.tsx and CourseSchedulePage.test.tsx
```

## Parallel Example: User Story 3

```text
Task T035: Complete-delete repository tests in backend/tests/services/test_draft_schedule_repository.py
Task T036: Complete-delete API tests in backend/tests/api/test_draft_schedule.py
Task T037: Client clear-draft contract tests in client/src/api/draftSchedule.test.ts
Task T038: Full-confirmation/page tests in ScheduleDeletionDialog.test.tsx and CourseSchedulePage.test.tsx
```

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete Phase 1 fixtures.
2. Complete Phase 2 shared contracts and accessible dialog shell.
3. Complete Phase 3 test-first.
4. Stop and validate manual creation independently using T022 and Quickstart Scenarios 1–3.
5. Demonstrate a course moving from all units remaining to partial or complete manual coverage.

### Incremental Delivery

1. Deliver US1 manual creation and remaining-unit feedback.
2. Add US2 single-session deletion, last-session cleanup, and stale reconfirmation.
3. Add US3 complete course-semester clearing and preservation guarantees.
4. Complete Phase 6 regression, performance, usability, and documentation evidence.

### Parallel Team Strategy

1. Complete Setup and Foundations together.
2. Assign US1, US2, and US3 independently only if shared-file ownership is coordinated.
3. Merge by priority order P1 → P2 → P3 and run each story checkpoint after integration.
4. Run Phase 6 only after all selected stories are integrated.

---

## Notes

- No database model, migration, dependency, authentication, background job, or new infrastructure task is required.
- Manual and generated sessions deliberately share the existing Draft Session model; do not add provenance behavior.
- Generation session-size preferences are not manual-creation hard limits; positive whole units and current remaining units are authoritative.
- Deletion confirmation must submit both expected Draft Schedule identity and revision; a read-compare-delete sequence is insufficient.
- Use ORM parent deletion so the existing relationship cascade removes sessions; do not assume database-level `ON DELETE CASCADE`.
- Tests must fail for the intended missing behavior before implementing the corresponding production task wherever practical.
- Preserve unrelated worktree changes and create a feature branch before production implementation unless the constitution's clean solo-work condition for `master` is satisfied.
