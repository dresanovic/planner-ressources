# Tasks: Manual Session Editing

**Input**: Design documents from `/specs/004-manual-session-editing/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update test tasks before production implementation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup (Shared Test Fixtures And Types)

**Purpose**: Prepare shared fixture data and type seams used by multiple manual-editing stories.

- [ ] T001 [P] Add backend fixture helpers for generated Draft Sessions with editable semester, cohort, and room capacity scenarios in backend/tests/api/test_draft_schedule.py
- [ ] T002 [P] Add repository fixture helpers for manual Draft Session edit scenarios in backend/tests/services/test_draft_schedule_repository.py
- [ ] T003 [P] Add frontend fixture data for editable Draft Sessions, rooms with capacities, and overview schedules in client/src/test/draftScheduleFixtures.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared contracts and room option data required before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add manual edit request and failure response schemas for Draft Session updates in backend/app/schemas/draft_schedule.py
- [ ] T005 Add room option response schema with capacity and rooms list to planning options schemas in backend/app/schemas/planning_options.py
- [ ] T006 Add shared client types for Draft Session edit payloads, edit failures, and room options in client/src/api/draftSchedule.ts and client/src/api/planningOptions.ts
- [ ] T007 Add repository function stubs and validation error types for updating Draft Sessions in backend/app/services/draft_schedule_repository.py
- [ ] T008 Extend planning options tests to expect room options with capacity metadata in backend/tests/api/test_draft_schedule.py

**Checkpoint**: Shared contracts, fixture seams, and room option types are ready for story work.

---

## Phase 3: User Story 1 - Edit Session Time And Length (Priority: P1) MVP

**Goal**: Office staff can edit an existing generated Draft Session's date, start time, and end time, with end time controlling derived session length.

**Independent Test**: Open a generated Draft Session from the Courses overview, change date/start/end time, save it, and confirm the updated session appears with the new time range in list and weekly modes.

### Tests for User Story 1 (write before implementation)

- [ ] T009 [P] [US1] Add repository tests for valid date/start/end time edit persistence and unchanged cancel/failure state in backend/tests/services/test_draft_schedule_repository.py
- [ ] T010 [US1] Add repository tests for out-of-semester dates, end-before-start time ranges, and duplicate dates in backend/tests/services/test_draft_schedule_repository.py
- [ ] T011 [P] [US1] Add API contract tests for PATCH /api/draft-sessions/{sessionId} success and invalid date/time failures in backend/tests/api/test_draft_schedule.py
- [ ] T012 [P] [US1] Add frontend component tests for opening edit controls, showing current date/start/end/derived length, canceling, and saving time edits in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 1

- [ ] T013 [US1] Implement date/start/end time validation and persistence in update Draft Session repository function in backend/app/services/draft_schedule_repository.py
- [ ] T014 [US1] Add PATCH /api/draft-sessions/{sessionId} route with 200/404/422 handling in backend/app/api/draft_schedule.py
- [ ] T015 [US1] Add updateDraftSession client API function and typed edit failure handling in client/src/api/draftSchedule.ts
- [ ] T016 [US1] Add edit state, date/start/end inputs, derived length display, save, and cancel behavior to Courses overview sessions in client/src/components/DraftSchedulePanel.tsx
- [ ] T017 [US1] Wire manual time edit save handling and overview schedule replacement in client/src/pages/CourseSchedulePage.tsx
- [ ] T018 [US1] Style manual edit controls, validation messages, and compact in-row edit actions in client/src/App.css

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - Change Session Room (Priority: P2)

**Goal**: Office staff can change a Draft Session room to another room with sufficient capacity, and insufficient-capacity room edits are blocked.

**Independent Test**: Open a generated Draft Session, choose a replacement room with enough capacity, save it, verify room filter behavior, then try a room below cohort size and confirm the edit is rejected.

### Tests for User Story 2 (write before implementation)

- [ ] T019 [P] [US2] Add repository tests for successful room replacement, missing room rejection, insufficient room capacity rejection, and occupied-room non-rejection in backend/tests/services/test_draft_schedule_repository.py
- [ ] T020 [P] [US2] Add API tests for room edit success, insufficient capacity 422, missing room 404, and no occupancy conflict warning in backend/tests/api/test_draft_schedule.py
- [ ] T021 [P] [US2] Add frontend tests for room selector options, capacity messaging, save behavior, and room filter changes after edit in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 2

- [ ] T022 [US2] Load all rooms and include room option capacity metadata in GET /api/planning-options in backend/app/api/planning_options.py
- [ ] T023 [US2] Implement room capacity validation and replacement room persistence in backend/app/services/draft_schedule_repository.py
- [ ] T024 [US2] Map insufficient room capacity and missing room edit failures in PATCH /api/draft-sessions/{sessionId} in backend/app/api/draft_schedule.py
- [ ] T025 [US2] Parse room options with capacity in client/src/api/planningOptions.ts
- [ ] T026 [US2] Add room selector, capacity-aware room option display, and room edit submission to client/src/components/DraftSchedulePanel.tsx
- [ ] T027 [US2] Pass planning option room data into the Courses overview edit controls from client/src/pages/CourseSchedulePage.tsx
- [ ] T028 [US2] Style room selector and capacity error states in client/src/App.css

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Preserve Manual Edits During Review (Priority: P3)

**Goal**: Saved manual edits remain visible across overview filters, list/weekly view modes, page reload/reopen of the same semester, and existing regeneration replacement behavior remains intact.

**Independent Test**: Save a manual edit, change filters and view modes, reload the selected semester overview, and confirm saved values remain until regeneration replaces that course's draft schedule.

### Tests for User Story 3 (write before implementation)

- [ ] T029 [P] [US3] Add API tests that semester-scoped GET /api/draft-schedules returns saved manual edit values after reload in backend/tests/api/test_draft_schedule.py
- [ ] T030 [P] [US3] Add backend tests that regeneration replacement removes prior manually edited Draft Sessions according to existing behavior in backend/tests/api/test_draft_schedule.py
- [ ] T031 [P] [US3] Add frontend component tests for edited sessions across filters, list/weekly mode switching, no false optimistic save on failure, and semester overview reload in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 3

- [ ] T032 [US3] Ensure updated Draft Schedule responses sort edited sessions by updated date/start time in backend/app/api/draft_schedule.py
- [ ] T033 [US3] Ensure semester-scoped draft schedule listing returns saved manual edit values and refreshed room context in backend/app/services/draft_schedule_repository.py
- [ ] T034 [US3] Update review filtering helpers to use edited session room/date/time values consistently in client/src/components/scheduleReviewUtils.ts
- [ ] T035 [US3] Preserve edited schedule state across filters, list/weekly mode switching, save failures, and overview reloads in client/src/components/DraftSchedulePanel.tsx
- [ ] T036 [US3] Ensure page-level semester overview reload keeps saved manual edits and continues to refresh after regeneration in client/src/pages/CourseSchedulePage.tsx

**Checkpoint**: All Slice 4 user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation alignment, and scope checks across the slice.

- [ ] T037 [P] Update backend README with manual Draft Session edit endpoint, validation rules, and deferred occupancy checks in backend/README.md
- [ ] T038 [P] Update client README with manual editing workflow, room capacity rule, and out-of-scope conflict warnings in client/README.md
- [ ] T039 Run backend verification from quickstart in backend/tests/services/test_draft_schedule_repository.py and backend/tests/api/test_draft_schedule.py
- [ ] T040 Run frontend verification commands from quickstart using npm run test, npm run lint, and npm run build in client/package.json
- [ ] T041 Execute the manual smoke scenario and negative scenarios from specs/004-manual-session-editing/quickstart.md
- [ ] T042 Confirm no conflict warnings, public holiday warnings, exam scheduling, dashboard summaries, multi-course generation, session creation/deletion/splitting/merging, or source planning-record edit controls are present in client/src/components/DraftSchedulePanel.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP.
- **Phase 4 US2**: Depends on Phase 2 and can be developed after US1 for the shared edit form, but remains independently testable with room-only changes.
- **Phase 5 US3**: Depends on Phase 2 and should follow US1/US2 so persistence can be verified across completed edit behaviors.
- **Phase 6 Polish**: Depends on all selected user stories being complete.

### User Story Dependencies

- **US1 Edit Session Time And Length**: Independent after foundation; recommended MVP.
- **US2 Change Session Room**: Independent after foundation but reuses the edit surface from US1 when implemented sequentially.
- **US3 Preserve Manual Edits During Review**: Independent validation of persistence and overview behavior, but most useful after US1 and US2 are implemented.

### Within Each User Story

- Write tests before production changes where practical.
- Repository/API tests before backend implementation.
- Frontend component tests before UI wiring.
- Backend repository validation before API route integration.
- Client API types before component save wiring.
- Component behavior before CSS polish.

## Parallel Opportunities

- T001, T002, and T003 can run in parallel during setup.
- T004, T005, T006, T007, and T008 can run in parallel after setup if schema/interface edits are coordinated.
- T009, T011, and T012 can run in parallel for US1; T009 and T010 share a file and should be coordinated.
- T019, T020, and T021 can run in parallel for US2.
- T029 and T031 can run in parallel for US3; T029 and T030 share a file and should be coordinated.
- T037 and T038 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T011 [US1] Add API contract tests for PATCH /api/draft-sessions/{sessionId} success and invalid date/time failures in backend/tests/api/test_draft_schedule.py"
Task: "T012 [US1] Add frontend component tests for opening edit controls, showing current date/start/end/derived length, canceling, and saving time edits in client/src/components/DraftSchedulePanel.test.tsx"
Task: "T015 [US1] Add updateDraftSession client API function and typed edit failure handling in client/src/api/draftSchedule.ts"
```

## Parallel Example: User Story 2

```bash
Task: "T019 [US2] Add repository tests for successful room replacement, missing room rejection, insufficient room capacity rejection, and occupied-room non-rejection in backend/tests/services/test_draft_schedule_repository.py"
Task: "T020 [US2] Add API tests for room edit success, insufficient capacity 422, missing room 404, and no occupancy conflict warning in backend/tests/api/test_draft_schedule.py"
Task: "T021 [US2] Add frontend tests for room selector options, capacity messaging, save behavior, and room filter changes after edit in client/src/components/DraftSchedulePanel.test.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "T029 [US3] Add API tests that semester-scoped GET /api/draft-schedules returns saved manual edit values after reload in backend/tests/api/test_draft_schedule.py"
Task: "T031 [US3] Add frontend component tests for edited sessions across filters, list/weekly mode switching, no false optimistic save on failure, and semester overview reload in client/src/components/DraftSchedulePanel.test.tsx"
Task: "T034 [US3] Update review filtering helpers to use edited session room/date/time values consistently in client/src/components/scheduleReviewUtils.ts"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational contracts and stubs.
3. Complete Phase 3 US1 tests and implementation.
4. Validate that date/start/end edits save, reject invalid inputs, cancel cleanly, and display correctly in list and weekly modes.
5. Stop and demo the MVP before adding room replacement.

### Incremental Delivery

1. Deliver US1 for manual date/start/end editing.
2. Add US2 for room replacement with capacity enforcement.
3. Add US3 for review persistence, reload behavior, and regeneration replacement verification.
4. Run full quickstart verification after each story and again after polish.

### Parallel Team Strategy

After Phase 2, backend repository/API tests can be prepared while frontend component tests and API typing are prepared by another developer. Coordinate edits to `client/src/components/DraftSchedulePanel.tsx`, `client/src/pages/CourseSchedulePage.tsx`, and `backend/app/services/draft_schedule_repository.py`.

## Notes

- [P] tasks touch different files or are independent enough to run in parallel.
- [US1], [US2], and [US3] labels map directly to the prioritized user stories in spec.md.
- Verify tests fail before implementing where practical.
- Do not introduce conflict detection, room occupancy warnings, generation-window validation, teaching-window validation, public holiday handling, exam scheduling, dashboards, multi-course generation, multiple eligible rooms per course, session creation/deletion/splitting/merging, or source planning-record editing in this slice.
- Use the API shapes in specs/004-manual-session-editing/contracts/openapi.yaml as the cross-stack contract.
