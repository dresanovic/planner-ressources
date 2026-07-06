# Tasks: Draft Course Schedule

**Input**: Design documents from `/specs/001-draft-course-schedule/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/draft-schedule.openapi.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Test tasks appear before production implementation tasks in each phase.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the minimal project structure and dependency declarations needed for the feature.

- [ ] T001 Add SQLAlchemy and Alembic dependencies to backend/requirements.txt
- [ ] T002 [P] Create backend package directories and __init__.py files in backend/app/api/, backend/app/db/, backend/app/models/, backend/app/schemas/, backend/app/services/
- [ ] T003 [P] Create backend test directories and __init__.py files in backend/tests/api/ and backend/tests/services/
- [ ] T004 [P] Create frontend feature directories in client/src/api/, client/src/components/, and client/src/pages/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared persistence, schemas, and seedable domain structure required before user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Create database engine/session configuration for SQLite in backend/app/db/session.py
- [ ] T006 Create SQLAlchemy declarative base metadata in backend/app/db/base.py
- [ ] T007 Define planning SQLAlchemy models for Course, Lecturer, Cohort, Room, Semester, StudyType, StudyTypeTimeWindow, DraftSchedule, and DraftSession in backend/app/models/planning.py
- [ ] T008 Create Alembic configuration and initial migration for planning tables in backend/app/db/migrations/
- [ ] T009 Create shared Pydantic schemas for draft sessions, draft schedules, generation requests, and generation failures in backend/app/schemas/draft_schedule.py
- [ ] T010 Create repository module skeleton and planning input loader placeholders in backend/app/services/draft_schedule_repository.py
- [ ] T011 Create placeholder draft schedule API router in backend/app/api/draft_schedule.py and register it in backend/app/main.py

**Checkpoint**: Foundation ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Generate a Complete Draft Schedule (Priority: P1) MVP

**Goal**: Admin can trigger generation for one valid course and receive a complete draft schedule whose sessions cover all required units.

**Independent Test**: Provide valid planning inputs, trigger generation, and confirm sessions cover all required units, use preferred session sizing, and replace previous generated drafts.

### Tests for User Story 1 (write before implementation)

- [ ] T012 [P] [US1] Add service tests for splitting 20 units into five 4-unit sessions and 18 units into 4,4,4,3,3 in backend/tests/services/test_schedule_generation.py
- [ ] T013 [US1] Add service tests for 45-minute units, 10-minute breaks, generated end times, and total scheduled units in backend/tests/services/test_schedule_generation.py
- [ ] T014 [P] [US1] Add API tests for successful POST /api/courses/{courseId}/draft-schedule/generate and GET /api/courses/{courseId}/draft-schedule in backend/tests/api/test_draft_schedule.py
- [ ] T015 [P] [US1] Add API test that a second successful generation replaces previous generated draft sessions in backend/tests/api/test_draft_schedule.py
- [ ] T016 [US1] Add repository test that successful regeneration replaces prior draft sessions in backend/tests/services/test_draft_schedule_repository.py
- [ ] T017 [US1] Add frontend component fixture or build-verified mock state for displaying generated sessions in client/src/components/DraftSchedulePanel.tsx

### Implementation for User Story 1

- [ ] T018 [US1] Implement unit distribution and session duration helpers in backend/app/services/schedule_generation.py
- [ ] T019 [US1] Implement default once-per-week generation using the selected Study Type Time Window in backend/app/services/schedule_generation.py
- [ ] T020 [US1] Implement successful draft persistence and replacement of previous generated drafts in backend/app/services/draft_schedule_repository.py
- [ ] T021 [US1] Implement POST /api/courses/{courseId}/draft-schedule/generate success path in the placeholder router in backend/app/api/draft_schedule.py
- [ ] T022 [US1] Implement GET /api/courses/{courseId}/draft-schedule readback path in backend/app/api/draft_schedule.py
- [ ] T023 [P] [US1] Implement typed client functions for generate and readback requests in client/src/api/draftSchedule.ts
- [ ] T024 [US1] Implement DraftSchedulePanel session display and generate action wiring in client/src/components/DraftSchedulePanel.tsx
- [ ] T025 [US1] Mount the draft schedule page in client/src/pages/CourseSchedulePage.tsx and client/src/App.tsx

**Checkpoint**: MVP complete. US1 can be validated independently with a valid single-course generation case.

---

## Phase 4: User Story 2 - Respect Study Type Time Windows (Priority: P2)

**Goal**: Generated sessions occur only inside Study Type Time Windows, use the admin-selected preferred window where possible, and fall back to other allowed windows when needed.

**Independent Test**: Define multiple windows, generate a schedule, and confirm every session fits an allowed window, selected-window preference is honored where possible, and multiple sessions in one week never share the same day.

### Tests for User Story 2 (write before implementation)

- [ ] T026 [P] [US2] Add service tests for selected-window preference and fallback to another allowed window in backend/tests/services/test_schedule_generation.py
- [ ] T027 [US2] Add service tests for multiple sessions in one week with at most one generated session per day in backend/tests/services/test_schedule_generation.py
- [ ] T028 [P] [US2] Add API test that generated sessions never exceed allowed Study Type Time Windows in backend/tests/api/test_draft_schedule.py

### Implementation for User Story 2

- [ ] T029 [US2] Implement allowed-window placement validation and fallback-window selection in backend/app/services/schedule_generation.py
- [ ] T030 [US2] Implement insufficient-weeks fallback to multiple sessions per week with one-session-per-day enforcement in backend/app/services/schedule_generation.py
- [ ] T031 [US2] Include selectedTimeWindowId and session timeWindowId consistently in API responses in backend/app/api/draft_schedule.py
- [ ] T032 [US2] Display each generated session's date, time range, units, and window reference in client/src/components/DraftSchedulePanel.tsx

**Checkpoint**: US1 and US2 both work independently and preserve all time-window constraints.

---

## Phase 5: User Story 3 - Block Invalid Generation Requests (Priority: P3)

**Goal**: Admin receives all detected failure reasons and no partial draft is created when generation is invalid or impossible.

**Independent Test**: Provide invalid capacity, invalid session preferences, and impossible scheduling inputs, then confirm no draft sessions are created and all detected reasons are returned.

### Tests for User Story 3 (write before implementation)

- [ ] T033 [P] [US3] Add service tests for insufficient room capacity and invalid session preference failures in backend/tests/services/test_schedule_generation.py
- [ ] T034 [US3] Add service tests for no fitting time window and insufficient semester capacity failures in backend/tests/services/test_schedule_generation.py
- [ ] T035 [P] [US3] Add API test that multiple detected failure reasons are returned together with no partial draft creation in backend/tests/api/test_draft_schedule.py
- [ ] T036 [US3] Add frontend component fixture or build-verified mock state for rendering all generation failure reasons in client/src/components/DraftSchedulePanel.tsx

### Implementation for User Story 3

- [ ] T037 [US3] Implement failure reason accumulation for capacity, preference, no-window, and insufficient-capacity cases in backend/app/services/schedule_generation.py
- [ ] T038 [US3] Ensure failed generation does not create or replace draft records in backend/app/services/draft_schedule_repository.py
- [ ] T039 [US3] Return 422 GenerationFailureResponse with all detected errors in backend/app/api/draft_schedule.py
- [ ] T040 [US3] Render all returned generation failure messages in client/src/components/DraftSchedulePanel.tsx

**Checkpoint**: All user stories are independently functional and invalid generation requests are safely blocked.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation alignment, and cleanup across stories.

- [ ] T041 [P] Update backend setup notes for SQLite, SQLAlchemy, and Alembic usage in backend/README.md
- [ ] T042 [P] Update frontend usage notes for the draft schedule page in client/README.md
- [ ] T043 Run backend pytest verification from quickstart in backend/
- [ ] T044 Run frontend lint and build verification from quickstart in client/
- [ ] T045 Verify and record that the valid single-course generation scenario completes in under 1 minute in specs/001-draft-course-schedule/quickstart.md
- [ ] T046 Review specs/001-draft-course-schedule/quickstart.md against implemented behavior and update it if implementation changed approved behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2; MVP scope.
- **Phase 4 US2**: Depends on Phase 2 and can be developed after or alongside US1, but final verification should include US1 behavior.
- **Phase 5 US3**: Depends on Phase 2 and can be developed after or alongside US1/US2, but final verification should confirm no regression to successful generation.
- **Phase 6 Polish**: Depends on all selected user stories being complete.

### User Story Dependencies

- **US1 Generate a Complete Draft Schedule**: Independent after foundation; recommended MVP.
- **US2 Respect Study Type Time Windows**: Independent after foundation but shares `schedule_generation.py` with US1.
- **US3 Block Invalid Generation Requests**: Independent after foundation but shares service, repository, API, and UI files with US1/US2.

### Within Each User Story

- Write tests before implementation where practical.
- Service tests before service implementation.
- API tests before endpoint implementation.
- Client verification before or alongside UI implementation.
- Service logic before API endpoints.
- API client functions before UI wiring.

## Parallel Opportunities

- T002, T003, and T004 can run in parallel during setup.
- T012, T014, T015, T016, and T017 can be started in parallel for US1, but T012 and T013 share the same test file and should be coordinated.
- T026, T027, and T028 can run in parallel for US2, with coordination on shared test files.
- T033, T034, T035, and T036 can run in parallel for US3, with coordination on shared test files.
- T041 and T042 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T014 [US1] Add API tests for successful POST /api/courses/{courseId}/draft-schedule/generate and GET /api/courses/{courseId}/draft-schedule in backend/tests/api/test_draft_schedule.py"
Task: "T017 [US1] Add frontend component fixture or build-verified mock state for displaying generated sessions in client/src/components/DraftSchedulePanel.tsx"
Task: "T023 [US1] Implement typed client functions for generate and readback requests in client/src/api/draftSchedule.ts"
```

## Parallel Example: User Story 2

```bash
Task: "T026 [US2] Add service tests for selected-window preference and fallback to another allowed window in backend/tests/services/test_schedule_generation.py"
Task: "T028 [US2] Add API test that generated sessions never exceed allowed Study Type Time Windows in backend/tests/api/test_draft_schedule.py"
Task: "T032 [US2] Display each generated session's date, time range, units, and window reference in client/src/components/DraftSchedulePanel.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "T033 [US3] Add service tests for insufficient room capacity and invalid session preference failures in backend/tests/services/test_schedule_generation.py"
Task: "T035 [US3] Add API test that multiple detected failure reasons are returned together with no partial draft creation in backend/tests/api/test_draft_schedule.py"
Task: "T036 [US3] Add frontend component fixture or build-verified mock state for rendering all generation failure reasons in client/src/components/DraftSchedulePanel.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 US1 tests and implementation.
4. Run backend pytest plus frontend lint/build checks.
5. Stop and validate the MVP before adding US2 or US3 behavior.

### Incremental Delivery

1. Deliver US1 to prove complete draft generation and replacement.
2. Add US2 to strengthen time-window placement behavior.
3. Add US3 to harden invalid-input handling and failure feedback.
4. Run quickstart validation after each story.

### Notes

- Keep public holiday avoidance, exams, multi-course optimization, multiple lecturers, multiple rooms, cross-course conflicts, drag/drop editing, and calendar polish out of these tasks.
- If an automated frontend test runner is added during implementation, document that dependency in the implementation notes and keep it scoped to the draft schedule panel.
- Verify failing tests before production changes where practical.
