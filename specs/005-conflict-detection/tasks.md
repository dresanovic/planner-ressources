# Tasks: Conflict Detection

**Input**: Design documents from `/specs/005-conflict-detection/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update test tasks before production implementation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on incomplete tasks
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup (Shared Fixtures And Type Seams)

**Purpose**: Prepare shared fixture data and test seams used by multiple conflict-detection stories.

- [X] T001 [P] Add backend fixture helpers for multi-course selected-semester Draft Schedules with overlapping lecturer, room, and Cohort scenarios in backend/tests/services/test_draft_schedule_validation.py
- [X] T002 [P] Add backend API fixture helpers for validation-alert response scenarios in backend/tests/api/test_draft_schedule.py
- [X] T003 [P] Add frontend fixture data for Draft Sessions with validationAlerts, relatedSessions, multiple alerts, and hidden-related-session filter scenarios in client/src/test/draftScheduleFixtures.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared alert contracts and service seams required before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add ValidationAlertCode, RelatedSessionResponse, and ValidationAlertResponse schemas to backend/app/schemas/draft_schedule.py
- [X] T005 Add validationAlerts to DraftSessionResponse in backend/app/schemas/draft_schedule.py
- [X] T006 Add ValidationAlert and RelatedSession client types plus validationAlerts on DraftSession in client/src/api/draftSchedule.ts
- [X] T007 Create draft schedule validation service dataclasses and function stubs in backend/app/services/draft_schedule_validation.py
- [X] T008 Update draft schedule API response mapping seams to accept per-session validation alerts in backend/app/api/draft_schedule.py
- [X] T009 Add shared alert rendering helper or component seam for session alerts in client/src/components/DraftSchedulePanel.tsx

**Checkpoint**: Shared alert contracts, fixture seams, and validation service seams are ready for story work.

---

## Phase 3: User Story 1 - See Overlap Conflicts In Semester Overview (Priority: P1) MVP

**Goal**: Office staff can see lecturer, room, and Cohort overlap alerts across all generated plans in the selected semester Courses overview.

**Independent Test**: Prepare generated Draft Sessions in the same selected semester with overlapping lecturer, room, and Cohort assignments, open the Courses overview, and confirm all affected sessions show clear alerts with every related conflicting session available in the selected semester.

### Tests for User Story 1 (write before implementation)

- [X] T010 [P] [US1] Add validation service tests for lecturer, room, and Cohort overlap alerts on all affected sessions in backend/tests/services/test_draft_schedule_validation.py
- [X] T011 [P] [US1] Add validation service tests for back-to-back non-overlap, no self-conflict, and multi-session relatedSessions behavior in backend/tests/services/test_draft_schedule_validation.py
- [X] T012 [P] [US1] Add API tests that GET /api/draft-schedules?semesterId= returns validationAlerts with relatedSessions for cross-course overlaps in backend/tests/api/test_draft_schedule.py
- [X] T013 [P] [US1] Add API tests that GET /api/courses/{courseId}/draft-schedule returns validationAlerts for the generated course schedule in backend/tests/api/test_draft_schedule.py
- [X] T014 [P] [US1] Add frontend component tests that list-mode overlap alert indicators expose alert reasons and related session details within two interactions in client/src/components/DraftSchedulePanel.test.tsx
- [X] T015 [P] [US1] Add frontend component tests for overlap alerts remaining visible when filters hide related conflicting sessions in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 1

- [X] T016 [US1] Implement positive-duration interval overlap detection helpers in backend/app/services/draft_schedule_validation.py
- [X] T017 [US1] Implement lecturer, room, and Cohort overlap alert generation with all available relatedSessions in backend/app/services/draft_schedule_validation.py
- [X] T018 [US1] Integrate selected-semester validation alert computation into GET /api/draft-schedules?semesterId= response mapping in backend/app/api/draft_schedule.py
- [X] T019 [US1] Serialize overlap validationAlerts and relatedSessions on DraftSessionResponse in backend/app/api/draft_schedule.py
- [X] T020 [US1] Parse overlap validationAlerts in client/src/api/draftSchedule.ts
- [X] T021 [US1] Render list-mode validation alert indicators, reasons, and related session details in client/src/components/DraftSchedulePanel.tsx
- [X] T022 [US1] Style validation alert indicators and related-session details in client/src/App.css

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - See Capacity And Window Violations (Priority: P2)

**Goal**: Office staff can see room capacity, currently active generation-constraint, and Study Type Time Window violation alerts on affected Draft Sessions.

**Independent Test**: Prepare Draft Sessions with a room below Cohort capacity, a session outside currently active generation constraints, and a session outside the Study Type Time Window, then confirm each affected session displays the correct alert reason and multiple issues can appear together.

### Tests for User Story 2 (write before implementation)

- [X] T023 [P] [US2] Add validation service tests for room capacity alerts, missing room/cohort validation-data issues, and non-blocking alert output in backend/tests/services/test_draft_schedule_validation.py
- [X] T024 [P] [US2] Add validation service tests for currently active generation-constraint date/window violations and default-constraint fallback in backend/tests/services/test_draft_schedule_validation.py
- [X] T025 [P] [US2] Add validation service tests for Study Type Time Window violations and sessions with multiple alert codes in backend/tests/services/test_draft_schedule_validation.py
- [X] T026 [P] [US2] Add API tests that validationAlerts include ROOM_CAPACITY, GENERATION_CONSTRAINT_VIOLATION, STUDY_TYPE_WINDOW_VIOLATION, and VALIDATION_DATA_MISSING codes in backend/tests/api/test_draft_schedule.py
- [X] T027 [P] [US2] Add frontend component tests for capacity/window alert display and multiple alert reasons on one session in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 2

- [X] T028 [US2] Load or pass room, Cohort, active generation-constraint, and Study Type Time Window context needed by validation in backend/app/services/draft_schedule_repository.py
- [X] T029 [US2] Implement ROOM_CAPACITY and VALIDATION_DATA_MISSING alert generation in backend/app/services/draft_schedule_validation.py
- [X] T030 [US2] Implement currently active generation-constraint planning-period and allowed-window violation checks in backend/app/services/draft_schedule_validation.py
- [X] T031 [US2] Implement Study Type Time Window violation checks in backend/app/services/draft_schedule_validation.py
- [X] T032 [US2] Include capacity and window validation alerts in all DraftSessionResponse mappings in backend/app/api/draft_schedule.py
- [X] T033 [US2] Render multiple validation alert reasons for one session in client/src/components/DraftSchedulePanel.tsx
- [X] T034 [US2] Style multi-alert and validation-data issue states in client/src/App.css

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Refresh Alerts After Generation And Manual Edits (Priority: P3)

**Goal**: Validation alerts update after generation, regeneration, and saved manual edits without blocking generation or otherwise valid manual edit saves.

**Independent Test**: Generate a draft schedule, observe alerts, manually edit a session to create or resolve a conflict, save the edit, and confirm the Courses overview shows the updated alert state while the edit itself remains saveable when otherwise valid.

### Tests for User Story 3 (write before implementation)

- [X] T035 [P] [US3] Add API tests that POST /api/courses/{courseId}/draft-schedule/generate returns non-blocking validationAlerts when generated sessions conflict in backend/tests/api/test_draft_schedule.py
- [X] T036 [P] [US3] Add API tests that PATCH /api/draft-sessions/{sessionId} returns refreshed validationAlerts after edits create and resolve alerts in backend/tests/api/test_draft_schedule.py
- [X] T037 [P] [US3] Add backend tests that regeneration replacement removes alerts for replaced Draft Sessions in backend/tests/services/test_draft_schedule_validation.py
- [X] T038 [P] [US3] Add frontend component tests that alert state updates after onUpdateSession creates or resolves alerts in client/src/components/DraftSchedulePanel.test.tsx
- [X] T039 [P] [US3] Add frontend component tests that weekly mode shows the same validationAlerts as list mode in client/src/components/DraftSchedulePanel.test.tsx

### Implementation for User Story 3

- [X] T040 [US3] Ensure generation response validation uses the refreshed selected-semester schedule set after replacement in backend/app/api/draft_schedule.py
- [X] T041 [US3] Ensure manual edit response validation uses the refreshed selected-semester schedule set after save in backend/app/api/draft_schedule.py
- [X] T042 [US3] Ensure regenerated course schedules no longer contribute replaced-session validation alerts in backend/app/services/draft_schedule_validation.py
- [X] T043 [US3] Preserve validationAlerts during page-level schedule replacement after generation and manual edit saves in client/src/pages/CourseSchedulePage.tsx
- [X] T044 [US3] Render validation alerts in weekly review cards in client/src/components/DraftSchedulePanel.tsx
- [X] T045 [US3] Style weekly-mode validation alerts in client/src/App.css

**Checkpoint**: All Slice 5 user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation alignment, and scope checks across the slice.

- [X] T046 [P] Update backend README with validation alert response fields, non-blocking behavior, and current-generation-constraint rule in backend/README.md
- [X] T047 [P] Update client README with Courses overview validation alert behavior and non-blocking edit/generation workflow in client/README.md
- [X] T048 Run backend verification from quickstart in backend/tests/services/test_draft_schedule_validation.py, backend/tests/services/test_draft_schedule_repository.py, and backend/tests/api/test_draft_schedule.py
- [X] T049 Run frontend verification commands from quickstart using npm run test, npm run lint, and npm run build in client/package.json
- [ ] T050 Execute manual smoke, manual edit refresh, capacity/window, and non-blocking scenarios from specs/005-conflict-detection/quickstart.md
- [X] T051 Confirm no automatic conflict resolution, conflict-aware generation, public holiday warnings, exam scheduling, dashboard summaries, multi-course generation, session creation/deletion/splitting/merging, or multiple lecturer/room behavior is present in client/src/components/DraftSchedulePanel.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP.
- **Phase 4 US2**: Depends on Phase 2, and can be developed after US1 to reuse alert rendering and response mapping.
- **Phase 5 US3**: Depends on Phase 2, and should follow US1/US2 so refresh behavior covers all alert types.
- **Phase 6 Polish**: Depends on all selected user stories being complete.

### User Story Dependencies

- **US1 See Overlap Conflicts In Semester Overview**: Independent after foundation; recommended MVP.
- **US2 See Capacity And Window Violations**: Independent after foundation but reuses the validation alert contract and UI display from US1 when implemented sequentially.
- **US3 Refresh Alerts After Generation And Manual Edits**: Independent validation of refresh and non-blocking behavior, but most useful after US1 and US2 alert categories are implemented.

### Within Each User Story

- Write tests before production changes where practical.
- Backend validation service tests before validation service implementation.
- API tests before response mapping integration.
- Frontend component tests before UI rendering and styling.
- Shared schema and client types before endpoint/UI integration.
- Story complete before moving to the next priority.

## Parallel Opportunities

- T001, T002, and T003 can run in parallel during setup.
- T004, T006, T007, and T009 can run in parallel after setup if schema/interface changes are coordinated.
- T010, T012, T013, T014, and T015 can run in parallel for US1; T010 and T011 share a file and should be coordinated.
- T023, T026, and T027 can run in parallel for US2; T023, T024, and T025 share a file and should be coordinated.
- T035, T037, T038, and T039 can run in parallel for US3; T035 and T036 share a file and should be coordinated.
- T046 and T047 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T010 [US1] Add validation service tests for lecturer, room, and Cohort overlap alerts on all affected sessions in backend/tests/services/test_draft_schedule_validation.py"
Task: "T012 [US1] Add API tests that GET /api/draft-schedules?semesterId= returns validationAlerts with relatedSessions for cross-course overlaps in backend/tests/api/test_draft_schedule.py"
Task: "T014 [US1] Add frontend component tests that list-mode overlap alert indicators expose alert reasons and related session details within two interactions in client/src/components/DraftSchedulePanel.test.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T023 [US2] Add validation service tests for room capacity alerts, missing room/cohort validation-data issues, and non-blocking alert output in backend/tests/services/test_draft_schedule_validation.py"
Task: "T026 [US2] Add API tests that validationAlerts include ROOM_CAPACITY, GENERATION_CONSTRAINT_VIOLATION, STUDY_TYPE_WINDOW_VIOLATION, and VALIDATION_DATA_MISSING codes in backend/tests/api/test_draft_schedule.py"
Task: "T027 [US2] Add frontend component tests for capacity/window alert display and multiple alert reasons on one session in client/src/components/DraftSchedulePanel.test.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "T035 [US3] Add API tests that POST /api/courses/{courseId}/draft-schedule/generate returns non-blocking validationAlerts when generated sessions conflict in backend/tests/api/test_draft_schedule.py"
Task: "T037 [US3] Add backend tests that regeneration replacement removes alerts for replaced Draft Sessions in backend/tests/services/test_draft_schedule_validation.py"
Task: "T038 [US3] Add frontend component tests that alert state updates after onUpdateSession creates or resolves alerts in client/src/components/DraftSchedulePanel.test.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational alert contracts and validation service seams.
3. Complete Phase 3 US1 tests and implementation.
4. Validate that lecturer, room, and Cohort overlap alerts appear on all affected selected-semester sessions and identify every related conflicting session.
5. Stop and demo the MVP before adding capacity/window violations.

### Incremental Delivery

1. Deliver US1 for overlap detection and list-mode alert display.
2. Add US2 for room capacity, current generation-constraint, Study Type Time Window, and missing-data alerts.
3. Add US3 for generation/manual-edit refresh behavior, weekly-mode parity, and non-blocking workflow checks.
4. Run full quickstart verification after each story and again after polish.

### Parallel Team Strategy

After Phase 2, backend validation service tests can be prepared while API contract tests and frontend component tests are prepared by another developer. Coordinate edits to `backend/app/api/draft_schedule.py`, `backend/app/schemas/draft_schedule.py`, `client/src/api/draftSchedule.ts`, `client/src/components/DraftSchedulePanel.tsx`, and `client/src/App.css`.

## Notes

- [P] tasks touch different files or are independent enough to run in parallel.
- [US1], [US2], and [US3] labels map directly to the prioritized user stories in spec.md.
- Verify tests fail before implementing where practical.
- Do not persist validation alerts; derive them from selected-semester schedule and planning data at read time.
- Use currently active course-semester generation constraints for generation-window alerts.
- Each overlap alert must identify every related conflicting session available in the selected semester.
- Alerts are non-blocking: generation and otherwise valid manual edits must remain saveable when alerts exist.
- Do not introduce automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summaries, multi-course generation, multiple lecturers/rooms per course, session creation/deletion/splitting/merging, or source planning-record editing in this slice.
- Use the API shapes in specs/005-conflict-detection/contracts/openapi.yaml as the cross-stack contract.
