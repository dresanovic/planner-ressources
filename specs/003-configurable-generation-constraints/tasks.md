# Tasks: Configurable Generation Constraints

**Input**: Design documents from `/specs/003-configurable-generation-constraints/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update test tasks before production implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared test fixtures and client types used by multiple stories.

- [X] T001 [P] Add backend fixture helpers for course-semester constraint scenarios in backend/tests/api/test_draft_schedule.py
- [X] T002 [P] Add frontend test data factories for generation constraints in client/src/components/DraftSchedulePanel.test.tsx
- [X] T003 [P] Add shared TypeScript types for planning periods and allowed teaching windows in client/src/api/draftSchedule.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared backend data structures and validation primitives that MUST be complete before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add GenerationConstraintSet and GenerationConstraintWindow models plus DraftSession traceability fields in backend/app/models/planning.py
- [X] T005 Add generation constraint request/response schemas and new failure codes in backend/app/schemas/draft_schedule.py
- [X] T006 Update schedule-generation dataclasses to accept planning period and allowed window inputs in backend/app/services/schedule_generation.py
- [X] T007 Add repository function stubs for loading, saving, and clearing course-semester constraints in backend/app/services/draft_schedule_repository.py
- [X] T008 Update frontend API function signatures for constraint loading, clearing, and generation payloads in client/src/api/draftSchedule.ts

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Generate With Default Constraints (Priority: P1) MVP

**Goal**: Office staff can generate using semester and study type defaults, and saved course-semester constraints reload when present.

**Independent Test**: Select a course and semester with no saved custom constraints, generate without editing constraints, and confirm sessions use the semester date range and study type windows; then seed saved constraints and confirm they reload for the same course-semester.

### Tests for User Story 1 (write before implementation)

- [X] T009 [P] [US1] Add backend API tests for default constraint loading and saved constraint reload in backend/tests/api/test_draft_schedule.py
- [X] T010 [P] [US1] Add backend service tests for default planning period and default study type windows in backend/tests/services/test_schedule_generation.py
- [X] T011 [P] [US1] Add frontend test for default generation constraint display distinct from review filters in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 1

- [X] T012 [US1] Implement active default constraint loading for selected course and semester in backend/app/services/draft_schedule_repository.py
- [X] T013 [US1] Add GET `/api/courses/{course_id}/generation-constraints` endpoint in backend/app/api/draft_schedule.py
- [X] T014 [US1] Update schedule generation to use submitted planning period and allowed windows instead of selectedTimeWindowId in backend/app/services/schedule_generation.py
- [X] T015 [US1] Update draft schedule replacement and response mapping for optional timeWindowId and constraintWindowIndex in backend/app/services/draft_schedule_repository.py
- [X] T016 [US1] Update draft schedule API request handling to accept planningPeriod and allowedTeachingWindows in backend/app/api/draft_schedule.py
- [X] T017 [US1] Implement client API calls for reading generation constraints and generating with active constraints in client/src/api/draftSchedule.ts
- [X] T018 [US1] Render generation constraint controls with default period and windows in client/src/components/DraftSchedulePanel.tsx
- [X] T019 [US1] Wire course and semester changes to load active generation constraints in client/src/pages/CourseSchedulePage.tsx
- [X] T020 [US1] Preserve Slice 2 review filters as review-only controls separate from generation constraints in client/src/components/DraftSchedulePanel.tsx

**Checkpoint**: User Story 1 should be fully functional and independently testable as the MVP.

---

## Phase 4: User Story 2 - Override The Planning Period (Priority: P2)

**Goal**: Office staff can set, use, save, reload, and clear a custom planning period within the selected semester.

**Independent Test**: Enter a custom start/end date inside the semester, generate, verify all sessions stay within the custom period, revisit the same course-semester to see the saved period, and clear the full saved constraint set back to semester and study type defaults.

### Tests for User Story 2 (write before implementation)

- [X] T021 [P] [US2] Add backend API tests for custom planning period validation, save-after-success, failed-attempt preservation, and full constraint-set clear behavior in backend/tests/api/test_draft_schedule.py
- [X] T022 [P] [US2] Add backend repository tests for saving, replacing, reloading, and deleting full course-semester constraint sets in backend/tests/services/test_draft_schedule_repository.py
- [X] T023 [P] [US2] Add frontend tests for editing planning period, sending it to generation, and clearing the full constraint set in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 2

- [X] T024 [US2] Implement planning period validation against selected semester dates in backend/app/services/schedule_generation.py
- [X] T025 [US2] Implement save-after-success and failed-generation preservation for planning periods in backend/app/services/draft_schedule_repository.py
- [X] T026 [US2] Add DELETE `/api/courses/{course_id}/generation-constraints` support for clearing the full saved course-semester constraint set in backend/app/api/draft_schedule.py
- [X] T027 [US2] Return INVALID_PLANNING_PERIOD errors for reversed or out-of-semester dates in backend/app/api/draft_schedule.py
- [X] T028 [US2] Add planning period date inputs and full constraint-set reset behavior to generation constraints UI in client/src/components/DraftSchedulePanel.tsx
- [X] T029 [US2] Wire clear-custom-constraints client call and local default reset behavior in client/src/api/draftSchedule.ts
- [X] T030 [US2] Integrate planning period state ownership across selected course and semester changes in client/src/pages/CourseSchedulePage.tsx

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Configure Allowed Weekly Teaching Windows (Priority: P3)

**Goal**: Office staff can define one or more weekly teaching windows, use them for generation, persist them after success, and clear the full saved constraint set back to semester and study type defaults.

**Independent Test**: Add Monday 08:00-12:00 and Wednesday 09:00-13:00 windows, generate, verify all sessions fit those windows, revisit the same course-semester to see saved windows, and clear the full saved constraint set back to semester and study type defaults.

### Tests for User Story 3 (write before implementation)

- [X] T031 [P] [US3] Add backend service tests for multiple allowed windows, invalid windows, missing windows, and custom-window placement in backend/tests/services/test_schedule_generation.py
- [X] T032 [P] [US3] Add backend API tests for custom window save/reload/full-set clear and 422 failures without partial draft schedules in backend/tests/api/test_draft_schedule.py
- [X] T033 [P] [US3] Add frontend tests for adding, removing, validating, and submitting weekly teaching windows in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 3

- [X] T034 [US3] Implement multiple allowed window ordering and placement logic in backend/app/services/schedule_generation.py
- [X] T035 [US3] Implement custom window persistence with optional source_time_window_id in backend/app/services/draft_schedule_repository.py
- [X] T036 [US3] Return INVALID_TEACHING_WINDOW and MISSING_TEACHING_WINDOW failures for bad or empty window sets in backend/app/api/draft_schedule.py
- [X] T037 [US3] Add weekday/start/end custom window controls with add/remove actions and full constraint-set reset behavior in client/src/components/DraftSchedulePanel.tsx
- [X] T038 [US3] Update generation request construction to send all active allowedTeachingWindows in client/src/pages/CourseSchedulePage.tsx
- [X] T039 [US3] Update client draft session typing and display to tolerate nullable timeWindowId and use constraintWindowIndex in client/src/api/draftSchedule.ts

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification, cleanup, and documentation checks across all stories.

- [X] T040 [P] Update backend README generation examples for planningPeriod and allowedTeachingWindows in backend/README.md
- [X] T041 [P] Update client README planner workflow notes for generation constraints versus review filters in client/README.md
- [X] T042 Run backend verification from quickstart in backend/tests/services/test_schedule_generation.py backend/tests/services/test_draft_schedule_repository.py backend/tests/api/test_draft_schedule.py
- [X] T043 Run frontend verification commands for Vitest, lint, and build in client/package.json
- [X] T044 Review generated behavior against quickstart smoke scenario in specs/003-configurable-generation-constraints/quickstart.md
- [X] T045 Remove obsolete selectedTimeWindowId-only assumptions from backend/app/schemas/draft_schedule.py client/src/api/draftSchedule.ts client/src/pages/CourseSchedulePage.tsx
- [X] T046 [P] Add regression test that changing generation constraints without triggering generation leaves existing Draft Sessions unchanged in client/src/components/DraftSchedulePanel.test.tsx
- [X] T047 [P] Record manual review evidence that at least 90% of sampled office staff or reviewers identify generation constraint controls as future-generation inputs, not review filters, in specs/003-configurable-generation-constraints/quickstart.md

---

## Phase 7: Courses Overview Layout & Semester Scope

**Purpose**: Keep generation controls with the planning input selection and make the central review surface useful across all generated plans in the selected semester.

- [X] T048 [P] Add backend API test for listing generated draft schedules by selected semester in backend/tests/api/test_draft_schedule.py
- [X] T049 [P] Add frontend tests for Courses overview title, compact all-plan filters, and left planning input independence in client/src/components/DraftSchedulePanel.test.tsx
- [X] T050 Add repository query for generated draft schedules by semester in backend/app/services/draft_schedule_repository.py
- [X] T051 Add GET `/api/draft-schedules?semesterId=` endpoint in backend/app/api/draft_schedule.py
- [X] T052 Add client API call for semester-scoped draft schedules in client/src/api/draftSchedule.ts
- [X] T053 Move generation constraints and Generate action into the planning input sidebar in client/src/pages/CourseSchedulePage.tsx
- [X] T054 Convert DraftSchedulePanel into the central Courses overview over all selected-semester schedules in client/src/components/DraftSchedulePanel.tsx
- [X] T055 Update layout styling for sidebar generation controls and compact one-row overview filters in client/src/App.css
- [X] T056 Run backend and frontend verification commands from specs/003-configurable-generation-constraints/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; this is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and may reuse US1 constraint loading/generation flow.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and may reuse US1/US2 constraint state and persistence flow.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Generate With Default Constraints**: No dependency on US2 or US3 after Foundational; delivers the MVP.
- **US2 Override The Planning Period**: Can be built after Foundational but is simplest after US1 establishes active constraint loading.
- **US3 Configure Allowed Weekly Teaching Windows**: Can be built after Foundational but is simplest after US1 establishes active constraint loading and generation payloads.

### Within Each User Story

- Tests must be written before implementation where practical.
- Backend service and API behavior should be implemented before frontend integration.
- Frontend API types should be updated before UI wiring.
- Each story checkpoint should pass its independent test before moving to the next priority.

### Parallel Opportunities

- T001, T002, and T003 can run in parallel.
- T004, T005, T006, and T008 can run in parallel, with T007 following the model/schema shape from T004/T005.
- Test tasks within each user story can run in parallel because they target service/API/frontend test files.
- US2 and US3 can proceed in parallel after US1 if changes to `DraftSchedulePanel.tsx` and `CourseSchedulePage.tsx` are coordinated.
- T040 and T041 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "T009 [US1] Add backend API tests for default constraint loading and saved constraint reload in backend/tests/api/test_draft_schedule.py"
Task: "T010 [US1] Add backend service tests for default planning period and default study type windows in backend/tests/services/test_schedule_generation.py"
Task: "T011 [US1] Add frontend test for default generation constraint display distinct from review filters in client/src/components/DraftSchedulePanel.test.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T021 [US2] Add backend API tests for custom planning period validation, save-after-success, failed-attempt preservation, and full constraint-set clear behavior in backend/tests/api/test_draft_schedule.py"
Task: "T022 [US2] Add backend repository tests for saving, replacing, reloading, and deleting full course-semester constraint sets in backend/tests/services/test_draft_schedule_repository.py"
Task: "T023 [US2] Add frontend tests for editing planning period, sending it to generation, and clearing the full constraint set in client/src/components/DraftSchedulePanel.test.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "T031 [US3] Add backend service tests for multiple allowed windows, invalid windows, missing windows, and custom-window placement in backend/tests/services/test_schedule_generation.py"
Task: "T032 [US3] Add backend API tests for custom window save/reload/full-set clear and 422 failures without partial draft schedules in backend/tests/api/test_draft_schedule.py"
Task: "T033 [US3] Add frontend tests for adding, removing, validating, and submitting weekly teaching windows in client/src/components/DraftSchedulePanel.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate default constraint loading, generation, saved reload, and review-filter separation.
5. Demo the default-generation workflow before adding custom planning period and custom windows.

### Incremental Delivery

1. Complete Setup and Foundational tasks.
2. Add US1 default constraints and saved reload; test independently.
3. Add US2 custom planning period override and durable clearing; test independently.
4. Add US3 custom weekly windows; test independently.
5. Run polish and full quickstart verification.

### Parallel Team Strategy

With multiple developers:

1. Pair on foundational model/schema/generator contract tasks.
2. After Foundational, assign backend service/API tests separately from frontend component tests.
3. Coordinate any simultaneous edits to `client/src/components/DraftSchedulePanel.tsx`, `client/src/pages/CourseSchedulePage.tsx`, and `backend/app/services/schedule_generation.py`.
4. Integrate stories in priority order: US1, then US2, then US3.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [US1], [US2], and [US3] labels map to the user stories in `spec.md`.
- Verify tests fail before implementing where practical.
- Do not introduce manual session editing, conflict detection, multi-course generation, holiday avoidance, exam scheduling, dashboards, validation alerts, or multiple lecturer/room behavior in this slice.
- Use the API shapes in `specs/003-configurable-generation-constraints/contracts/openapi.yaml` as the cross-stack contract.
