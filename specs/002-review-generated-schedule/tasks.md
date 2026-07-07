# Tasks: Review Generated Schedule In Planner UI

**Input**: Design documents from `/specs/002-review-generated-schedule/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/draft-schedule-review.md, quickstart.md

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update test tasks before production implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare verification and shared frontend test support without changing feature behavior.

- [ ] T001 [P] Add a `test` script and Vitest/jsdom dev dependencies for client behavior tests in `client/package.json`
- [ ] T002 [P] Create frontend test setup file `client/src/test/setup.ts`
- [ ] T003 [P] Document Slice 2 verification commands in `client/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared contracts and helpers that every story uses.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Add review context and filterable session fields to Pydantic response schemas in `backend/app/schemas/draft_schedule.py`
- [ ] T005 [P] Add Draft Schedule review TypeScript types for context, filters, and view mode in `client/src/api/draftSchedule.ts`
- [ ] T006 [P] Create pure schedule review helper stubs for filtering and weekly grouping in `client/src/components/scheduleReviewUtils.ts`
- [ ] T007 [P] Add shared test fixtures for enriched Draft Schedule responses in `client/src/test/draftScheduleFixtures.ts`

**Checkpoint**: Shared contracts and frontend helper seams are ready for story work.

---

## Phase 3: User Story 1 - Inspect Generated Sessions In A Review View (Priority: P1) MVP

**Goal**: Office staff can open the current selected course schedule and see generated sessions with date, time, units, course, Cohort, lecturer, room, and study type context.

**Independent Test**: Open a course with generated Draft Sessions and confirm the review view shows every generated session chronologically with the required planning context and a clear empty state when no schedule exists.

### Tests for User Story 1 (write before implementation)

- [ ] T008 [P] [US1] Add backend API contract assertions for enriched schedule context and filterable session IDs in `backend/tests/api/test_draft_schedule.py`
- [ ] T009 [P] [US1] Add frontend component test for chronological list rendering and required context labels in `client/src/components/DraftSchedulePanel.test.tsx`
- [ ] T010 [P] [US1] Add frontend component test for no-schedule empty state in `client/src/components/DraftSchedulePanel.test.tsx`
- [ ] T011 [P] [US1] Add frontend component test for a generated schedule with zero sessions in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 1

- [ ] T012 [US1] Load Course relationships needed for review context in `backend/app/services/draft_schedule_repository.py`
- [ ] T013 [US1] Populate enriched Draft Schedule response context and session IDs in `backend/app/api/draft_schedule.py`
- [ ] T014 [US1] Update client API parsing types for enriched schedule responses in `client/src/api/draftSchedule.ts`
- [ ] T015 [US1] Load the current generated draft schedule on page open using `getDraftSchedule` and handle loading/not-found states in `client/src/pages/CourseSchedulePage.tsx`
- [ ] T016 [US1] Replace hard-coded mock session context with enriched schedule context in `client/src/pages/CourseSchedulePage.tsx`
- [ ] T017 [US1] Render chronological list review with date, time, units, course, Cohort, lecturer, room, and study type in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T018 [US1] Render a distinct empty state when a generated Draft Schedule exists but contains zero sessions in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T019 [US1] Style the richer list review and empty states in `client/src/App.css`

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - Switch Between Weekly And List Review Modes (Priority: P2)

**Goal**: Office staff can switch between list mode and a simple weekly calendar-style review without changing generated data or losing the visible session set.

**Independent Test**: Open a generated schedule, switch between list and weekly modes, and confirm both modes show the same visible sessions while preserving active filters.

### Tests for User Story 2 (write before implementation)

- [ ] T020 [P] [US2] Add unit tests for weekly grouping by week and day in `client/src/components/scheduleReviewUtils.test.ts`
- [ ] T021 [P] [US2] Add frontend component test for switching list and weekly modes in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 2

- [ ] T022 [US2] Implement weekly grouping helpers in `client/src/components/scheduleReviewUtils.ts`
- [ ] T023 [US2] Add view mode state and segmented list/weekly controls in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T024 [US2] Render weekly calendar-style grouped sessions in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T025 [US2] Style list/weekly mode controls and weekly grouped layout in `client/src/App.css`

**Checkpoint**: User Stories 1 and 2 work independently.

---

## Phase 5: User Story 3 - Filter Visible Draft Sessions (Priority: P3)

**Goal**: Office staff can filter visible Draft Sessions by current course, Cohort, lecturer, room, and study type, with match-all behavior and a clear no-results state.

**Independent Test**: Use schedule data with distinguishable context values, apply each supported filter and multiple filters together, and confirm only matching sessions remain visible.

### Tests for User Story 3 (write before implementation)

- [ ] T026 [P] [US3] Add unit tests for match-all filter behavior and clear-filter behavior in `client/src/components/scheduleReviewUtils.test.ts`
- [ ] T027 [P] [US3] Add frontend component test for filter controls and no-results state in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 3

- [ ] T028 [US3] Implement schedule filter helpers in `client/src/components/scheduleReviewUtils.ts`
- [ ] T029 [US3] Add filter state and clear-filter behavior in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T030 [US3] Render course, Cohort, lecturer, room, and study type filter controls in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T031 [US3] Apply filtered sessions consistently to list and weekly modes in `client/src/components/DraftSchedulePanel.tsx`
- [ ] T032 [US3] Add no-results state styling and filter control styling in `client/src/App.css`

**Checkpoint**: All Slice 2 user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation alignment, and cleanup across the slice.

- [ ] T033 [P] Update backend draft schedule API documentation with enriched review response in `backend/README.md`
- [ ] T034 [P] Update client draft schedule page documentation with list/weekly/filter review behavior in `client/README.md`
- [ ] T035 Run backend verification with `python -m pytest` from `backend/`
- [ ] T036 Run frontend verification with `npm run lint`, `npm run test`, and `npm run build` from `client/`
- [ ] T037 Execute the manual review scenario from `specs/002-review-generated-schedule/quickstart.md`
- [ ] T038 Confirm no manual session edit controls, conflict warnings, holiday warnings, exam controls, dashboard summaries, or multi-course review controls are present in `client/src/components/DraftSchedulePanel.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; may be implemented after US1 to reuse the review display.
- **User Story 3 (Phase 5)**: Depends on Foundational; should follow US1 and US2 so filters can apply to both views.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1**: No dependency on other stories after Foundational.
- **US2**: Reuses the schedule display from US1 but remains independently testable with fixture data.
- **US3**: Reuses the view modes from US1/US2 but remains independently testable through pure filter helpers and UI tests.

### Within Each User Story

- Tests must be written before implementation where practical.
- Backend contract tests before backend response changes.
- Frontend helper/component tests before UI changes.
- Shared helper logic before component integration.
- CSS after markup/state behavior exists.

---

## Parallel Opportunities

- T001, T002, and T003 can run in parallel.
- T004, T005, T006, and T007 can run in parallel after setup.
- T008, T009, T010, and T011 can run in parallel for US1.
- T020 and T021 can run in parallel for US2.
- T026 and T027 can run in parallel for US3.
- T033 and T034 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "T008 [US1] Add backend API contract assertions in backend/tests/api/test_draft_schedule.py"
Task: "T009 [US1] Add frontend component test in client/src/components/DraftSchedulePanel.test.tsx"
Task: "T010 [US1] Add frontend empty-state component test in client/src/components/DraftSchedulePanel.test.tsx"
Task: "T011 [US1] Add frontend zero-session component test in client/src/components/DraftSchedulePanel.test.tsx"
```

---

## Parallel Example: User Story 2

```bash
Task: "T020 [US2] Add weekly grouping unit tests in client/src/components/scheduleReviewUtils.test.ts"
Task: "T021 [US2] Add mode switching component test in client/src/components/DraftSchedulePanel.test.tsx"
```

---

## Parallel Example: User Story 3

```bash
Task: "T026 [US3] Add match-all filter unit tests in client/src/components/scheduleReviewUtils.test.ts"
Task: "T027 [US3] Add filter controls component test in client/src/components/DraftSchedulePanel.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational contracts and helper seams.
3. Complete Phase 3 User Story 1.
4. Stop and validate: backend API response includes context, frontend list review shows all required context, and no-schedule plus zero-session empty states work.

### Incremental Delivery

1. Deliver US1 for inspectable generated sessions.
2. Add US2 for weekly/list mode switching.
3. Add US3 for filters and no-results behavior.
4. Run the full quickstart and verification commands.

### Parallel Team Strategy

After Phase 2, one developer can own backend contract enrichment for US1 while another prepares frontend helper tests and components. US2 and US3 can proceed in parallel only after the shared helper contracts are stable.

---

## Notes

- [P] tasks touch different files or are independent enough to run in parallel.
- [US1], [US2], and [US3] map directly to the prioritized user stories in `spec.md`.
- The MVP is User Story 1 only.
- Keep Slice 2 scoped to the current selected course schedule.
- Do not add manual editing, conflict detection, public holiday handling, exam scheduling, planning dashboard summaries, or semester-wide multi-course review.
