# Tasks: Unified Teaching Schedule Generation

**Input**: Design documents from
`specs/I-003-unified-schedule-generation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, and `quickstart.md`

**Tests**: Tests are required by the specification and constitution. In every
story, write the listed tests first and confirm that the new assertions fail for
the intended reason before changing production code.

**Organization**: Tasks are grouped by user story so each slice can be completed
and verified independently. Task descriptions name the concrete files and the
observable behavior to implement.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and does not
  depend on an incomplete task in the same phase
- **[Story]**: Maps the task to a user story in `spec.md`
- Every task includes an exact repository path

## Phase 1: Setup and Baseline

**Purpose**: Isolate the broad customer-facing change and prepare reusable test
data without changing application behavior.

- [X] T001 Create or switch to `codex/I-003-unified-schedule-generation` (or an equivalent isolated worktree) for `C:/Codex/planner-resource`, preserve all pre-existing user changes, run `python -m pytest backend/tests` from the repository root, then run `npm test`, `npm run lint`, and `npm run build` from `C:/Codex/planner-resource/client`, and record every pre-existing failure before changing feature files
- [X] T002 [P] Extend `backend/tests/optimization_fixtures.py` with deterministic helpers for protected unselected teaching, active and past exams, shared lecturer/room/cohort occupancy, exact-boundary intervals, and selected-course exam deadlines
- [X] T003 Add or update baseline regression coverage before production implementation for manual teaching management, exam generation/manual management, lifecycle/publication immutability, resources, Academic Data, and Calendar modes in `backend/tests/services/test_exam_scheduling.py`, `backend/tests/services/test_schedule_lifecycle.py`, `backend/tests/api/test_calendar_workspace.py`, `client/src/pages/CourseSchedulePage.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, and `client/src/components/ResourceAdministration.test.tsx`; then run those three backend files with `python -m pytest` and those four client files with `npm test --` before production implementation

---

## Phase 2: Foundational Effective-Constraint Source

**Purpose**: Establish the one effective constraint representation shared by
generation, immediate constraint editing, lifecycle projections, and the client.

**CRITICAL**: Complete this phase before any user-story implementation.

### Tests for the foundation (write first)

- [X] T004 [P] Add failing repository tests in `backend/tests/services/test_draft_schedule_repository.py` proving semester-date inheritance, semester-bounded saved dates, live current `StudyTypeTimeWindow` derivation, and ignored legacy `GenerationConstraintWindow` copies
- [X] T005 [P] Add failing projection tests in `backend/tests/services/test_calendar_workspace.py` and `backend/tests/services/test_schedule_lifecycle.py` proving study-type/window changes immediately alter effective constraints and current validation without moving existing sessions

### Foundation implementation

- [X] T006 [P] Extend the effective constraint response with study-type identity and read-only mapped-window evidence in `backend/app/schemas/draft_schedule.py`
- [X] T007 Change effective constraint loading to use `GenerationConstraintSet` only for dates and always derive weekly windows from the current active study type mappings in `backend/app/services/draft_schedule_repository.py`
- [X] T008 Update constraint consumers to ignore copied course window rows and revalidate from current study-type mappings in `backend/app/services/calendar_workspace.py` and `backend/app/services/schedule_lifecycle.py`
- [X] T009 Run `python -m pytest backend/tests/services/test_draft_schedule_repository.py backend/tests/services/test_calendar_workspace.py backend/tests/services/test_schedule_lifecycle.py backend/tests/services/test_academic_catalog.py backend/tests/api/test_academic_catalog.py` from `C:/Codex/planner-resource`, correcting only foundation-scope defects in the files changed by T006-T008

**Checkpoint**: Every consumer sees the same effective dates and study-type
windows; no course-specific weekly-window override remains authoritative.

---

## Phase 3: User Story 1 - Generate a Conflict-Safe Teaching Plan (Priority: P1) MVP

**Goal**: Use the existing optimizer as the sole placement engine and generate a
permitted result for one to twenty selected courses without conflicts against
selected teaching, unselected teaching, or active exams.

**Independent Test**: With Matematik 1 protected teaching, an active Data
Visualization exam, and a past exam, regenerate only Data Visualization and
verify that every saved session avoids protected lecturer/room/cohort occupancy,
ends no later than its active exam begins, permits exact adjacency, ignores the
past exam, and leaves all protected records unchanged.

### Tests for User Story 1 (write first)

- [X] T010 [P] [US1] Add failing solver tests for active-exam fixed occupancy, same-course `latest_teaching_end`, exact-boundary adjacency, selected-course mutual conflicts, deterministic tie ordering, and best proven partial coverage in `backend/tests/services/test_semester_optimization.py`
- [X] T011 [P] [US1] Add failing service tests for loading every active semester exam, excluding past exams from occupancy/deadlines/tokens, preserving lecturer/room/cohort reason codes with protected source evidence, enforcing the active-exam boundary, returning `STUDY_TYPE_WINDOW_UNAVAILABLE` when current mapped windows cannot host the minimum session, and preserving state on stale/timeout/unproven results in `backend/tests/services/test_conflict_aware_generation.py`
- [X] T012 [P] [US1] Add failing API tests for one-to-twenty unique same-semester selections, empty/duplicate/oversized/cross-semester/unavailable rejection, one-course parity, replacement confirmation, per-course outcomes, and no mutation on failure in `backend/tests/api/test_conflict_aware_generation.py`
- [X] T013 [P] [US1] Extend `backend/tests/performance/test_semester_optimization_performance.py` with active-exam protected occurrences and the documented one-unmeasured-warm-up plus twenty sequential fresh-input measured-run protocol, asserting all twenty finish within sixty seconds and at least nineteen within thirty while recording environment and per-run evidence

### Implementation for User Story 1

- [X] T014 [P] [US1] Extend normalized fixed occupancy and optimizer course input with source kind and optional latest teaching end, enforce half-open lecturer/room/cohort overlap and active-exam deadline rules, and retain deterministic/non-worsening objectives in `backend/app/services/semester_optimization.py`
- [X] T015 [P] [US1] Add `ACTIVE_EXAM_BOUNDARY` and `STUDY_TYPE_WINDOW_UNAVAILABLE` blocking reason values, optional protected `sourceKind`/`sourceId` evidence, and prepared effective-constraint fields in `backend/app/schemas/conflict_aware_generation.py`
- [X] T016 [US1] Load active exams using `institution_today()`, build protected occupancy and selected-course deadlines, retain lecturer/room/cohort reason codes with `active_exam` source evidence, reject missing or too-short current study-type windows precisely, include only active exams in freshness evidence, and preserve atomic proven-result saving in `backend/app/services/conflict_aware_generation.py`
- [X] T017 [US1] Enforce unified selection validation and expose extended prepared/outcome contracts, including precise study-type-window unavailability and protected source evidence, without a one-course special case in `backend/app/api/conflict_aware_generation.py`
- [X] T018 [US1] Run the focused US1 service, API, solver, and performance tests from `specs/I-003-unified-schedule-generation/quickstart.md` and confirm exams and unselected schedules are unchanged in all failure paths

**Checkpoint**: User Story 1 is independently functional through the unified
backend endpoints for both one and many selected courses.

---

## Phase 4: User Story 2 - Configure and Replace Plans Safely (Priority: P1)

**Goal**: Save/reset course-semester date overrides immediately, revalidate the
current schedule without moving it, and ensure generation reads but never
mutates or rolls back active constraints.

**Independent Test**: Save a date override for a course with an existing draft,
verify immediate warnings and live study-type windows, then cancel, fail, and
stale a prepared replacement and confirm the override remains active while the
draft, manual edits, and exams remain unchanged.

### Tests for User Story 2 (write first)

- [X] T019 [P] [US2] Add failing date-only persistence tests for create/update/idempotent save, optimistic revision conflict, reset to semester dates, cross-semester isolation, semester-bound validation, and legacy child-window cleanup in `backend/tests/services/test_draft_schedule_repository.py`
- [X] T020 [P] [US2] Add failing API contract tests for lifecycle-checked `PUT` and `DELETE` constraint operations, including `GENERATION_CONSTRAINT_OVERRIDE_NOT_FOUND` without mutation when reset has no saved override, stale-revision rejection, successful matching-revision reset, refreshed draft alerts, invalid input, and zero automatic session movement in `backend/tests/api/test_draft_schedule.py`
- [X] T021 [P] [US2] Add failing generation state-transition tests for constraint/date/window/resource/holiday/teaching/active-exam/revision staleness, past-exam non-staleness, cancellation, timeout, unproven solve, and constraint preservation in `backend/tests/services/test_conflict_aware_generation.py`
- [X] T022 [P] [US2] Add failing client contract tests for effective constraint reads and immediate save/reset payloads and responses, including the exact typed DraftSchedule/validation-alert mutation response and reset missing/stale/success cases, in `client/src/api/draftSchedule.test.ts`
- [X] T023 [P] [US2] Add failing focused-course editor tests for inherited/custom dates, explicit save/reset, validation, dirty/saving generation guard, read-only study-type windows, and refreshed authoritative warnings in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 2

- [X] T024 [P] [US2] Add date-only save request and mutation response schemas, including expected constraint revision and the exact authoritative `DraftScheduleResponse` with validation alerts, in `backend/app/schemas/draft_schedule.py`
- [X] T025 [US2] Replace copied-window persistence with immediate date-only insert/update/reset operations, optimistic revision checks, semester validation, idempotency, and legacy child cleanup in `backend/app/services/draft_schedule_repository.py`
- [X] T026 [US2] Implement active-working-revision `PUT` and response-returning `DELETE` constraint handlers in `backend/app/api/draft_schedule.py`, returning `GENERATION_CONSTRAINT_OVERRIDE_NOT_FOUND` without mutation when no override exists, rejecting a stale expected revision, and committing a matching-revision reset before refreshing validation
- [X] T027 [US2] Remove every constraint save/update/delete from the optimizer generation transaction and make date, study-type, and mapped-window revisions participate in stale checking in `backend/app/services/conflict_aware_generation.py`
- [X] T028 [US2] Ensure study-type or mapped-window mutations trigger current schedule revalidation and invalidate prepared input without moving sessions in `backend/app/services/academic_catalog.py`, `backend/app/services/calendar_workspace.py`, and `backend/app/services/schedule_lifecycle.py`
- [X] T029 [P] [US2] Implement typed effective constraint read/save/reset calls and remove writable weekly-window inputs from `client/src/api/draftSchedule.ts`
- [X] T030 [US2] Convert `GenerationConstraintEditor` into a focused course date-only editor with explicit save/reset, dirty-state reporting, and read-only study-type windows in `client/src/components/DraftSchedulePanel.tsx`
- [X] T031 [US2] Wire immediate constraint activation, authoritative draft refresh, and stale prepared-state clearing into `client/src/pages/CourseSchedulePage.tsx`, then run all focused US2 tests from `specs/I-003-unified-schedule-generation/quickstart.md`

**Checkpoint**: User Story 2 is independently verifiable without initiating a
successful generation; saved planning intent is current and failure-safe.

---

## Phase 5: User Story 3 - Use One Understandable Generation Workflow (Priority: P2)

**Goal**: Present one course-selection and generation journey and immediately
retire all weaker single-course and independent batch operations.

**Independent Test**: Select one course and then several courses in Calendar
Planning and verify both use the same prepare/confirmation/generate controls and
outcomes; directly call each legacy operation and verify structured 410 guidance
with no service call or persisted mutation.

### Tests for User Story 3 (write first)

- [X] T032 [P] [US3] Replace legacy-operation success expectations with failing 410 contract/no-service-call/no-mutation tests for single generate and batch prepare/generate in `backend/tests/api/test_draft_schedule.py` and `backend/tests/api/test_multi_course_generation.py`
- [X] T033 [P] [US3] Add failing client API tests for the extended unified preparation/result contract, every explicit OptimizationSummary field, protected source evidence, and stale/replacement responses in `client/src/api/conflictAwareGeneration.test.ts`
- [X] T034 [P] [US3] Add failing UI tests proving one selection count, one action for one-to-twenty courses, focused constraint review, replacement course names, per-course outcomes, and absence of single/batch mode controls in `client/src/components/MultiCourseGenerationPanel.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T035 [US3] Replace the legacy single generate and independent batch prepare/generate handlers with a shared structured HTTP 410 response containing `GENERATION_ENDPOINT_RETIRED` and the supported paths in `backend/app/api/draft_schedule.py` and `backend/app/api/multi_course_generation.py`
- [X] T036 [US3] Remove the now-unreachable independent batch service/schemas and legacy single-course `generate_schedule` implementation plus their obsolete service tests after verifying no supported callers remain in `backend/app/services/multi_course_generation.py`, `backend/app/schemas/multi_course_generation.py`, `backend/app/services/schedule_generation.py`, `backend/tests/services/test_multi_course_generation.py`, and `backend/tests/services/test_schedule_generation.py`
- [X] T037 [P] [US3] Extend unified preparation/result client types and delete retired generation calls and their obsolete client tests from `client/src/api/conflictAwareGeneration.ts`, `client/src/api/draftSchedule.ts`, `client/src/api/multiCourseDraftGeneration.ts`, and `client/src/api/multiCourseDraftGeneration.test.ts`
- [X] T038 [US3] Evolve `MultiCourseGenerationPanel` directly into the sole one-to-twenty course generation surface with preparation, explicit replacement, stale recovery, and course-specific outcomes in `client/src/components/MultiCourseGenerationPanel.tsx`
- [X] T039 [US3] Remove parallel single/batch mode state, handlers, and controls and route every supported teaching-generation action through the unified panel in `client/src/pages/CourseSchedulePage.tsx`, then run the focused US3 backend and client contract suites

**Checkpoint**: User Story 3 is independently verifiable from the UI and by
direct API calls; no supported path executes a second generator.

---

## Phase 6: User Story 4 - Understand Every Conflict Warning (Priority: P2)

**Goal**: Make every lecturer, room, and cohort overlap warning visibly distinct,
precise, deduplicated per category, and removable after authoritative refresh.

**Independent Test**: Create two overlapping sessions sharing room and cohort but
not lecturer; verify exactly one Room conflict and one Cohort conflict with named
resources and related course/date/interval, then resolve one category and verify
only that warning disappears after refresh.

### Tests for User Story 4 (write first)

- [X] T040 [P] [US4] Add failing validation tests for one alert per affected/related session pair and shared category, three distinct overlap codes, complete related evidence, and missing-context behavior in `backend/tests/services/test_draft_schedule_validation.py`
- [X] T041 [P] [US4] Add failing component tests for localized lecturer/room/cohort titles, resource-specific explanations, related course/date/interval, multiple categories for one pair, deduplication, and resolved-warning removal in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 4

- [X] T042 [US4] Deduplicate overlap alerts by affected session, related session, and conflict code while preserving resource and related-occurrence evidence in `backend/app/services/draft_schedule_validation.py`
- [X] T043 [US4] Add a direct code-specific conflict presentation mapper and render distinct lecturer, room, and cohort titles/details instead of generic repeated wording in `client/src/components/DraftSchedulePanel.tsx`
- [X] T044 [US4] Replace cached alerts after generation, constraint save/reset, manual edit, or deletion with authoritative refreshed schedule data in `client/src/pages/CourseSchedulePage.tsx` and verify the focused US4 suites pass

**Checkpoint**: User Story 4 is independently testable with manually overlapping
sessions and no generator execution.

---

## Phase 7: User Story 5 - Review an Aligned and Responsive List (Priority: P2)

**Goal**: Keep all teaching values under the correct field at wide, narrow, and
200% zoom presentations, regardless of warning count or label length.

**Independent Test**: Render List rows with zero, one, and several warnings and
long labels; verify the nine-field order at wide width, explicit labels at narrow
width, and reachable warnings/actions at 200% zoom.

### Tests for User Story 5 (write first)

- [X] T045 [P] [US5] Add failing DOM/layout-contract tests for the exact Date/Time/Duration/Course/Cohort/Lecturer/Room/Study type/Actions order, warnings contained in Date, explicit narrow labels, long text, and action reachability in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T046 [P] [US5] Add a failing CSS/source regression asserting generic occurrence grid rules are scoped and cannot override teaching rows in `client/src/pages/CourseSchedulePage.snapshot.test.ts`

### Implementation for User Story 5

- [X] T047 [US5] Add the dedicated teaching header/row class, stable nine-field markup, warning containment, and explicit narrow field labels in `client/src/components/DraftSchedulePanel.tsx`
- [X] T048 [US5] Define one shared teaching grid template, scope generic `.schedule-occurrence-row` styles to their owning list, and add narrow/zoom wrapping rules in `client/src/App.css`
- [ ] T049 [US5] Perform and record the teaching List matrix at 1280, 820, and 320 CSS pixels at 100% browser zoom and a 1280-pixel viewport at 200% browser zoom, covering zero/one/multiple warnings and long labels as documented in `specs/I-003-unified-schedule-generation/quickstart.md`, correcting only List association/accessibility defects in `client/src/components/DraftSchedulePanel.tsx` and `client/src/App.css`

**Checkpoint**: All five user stories are independently functional and their
combined Calendar experience satisfies the clarified workflow.

---

## Phase 8: Polish and Cross-Cutting Verification

**Purpose**: Reconcile documentation, prove unaffected behavior, and collect the
final functional, performance, and presentation evidence.

- [X] T050 [P] Update `docs/architecture/unified-teaching-schedule-generation.md` so active-exam boundaries, immediate date activation, study-type-owned windows, and 410 legacy retirement agree with `specs/I-003-unified-schedule-generation/spec.md`
- [X] T051 Run the complete backend suite `python -m pytest backend/tests` from `C:/Codex/planner-resource` and resolve only I-003 regressions in the files named by preceding tasks
- [X] T052 Run focused client tests followed by `npm test`, `npm run lint`, and `npm run build` from `C:/Codex/planner-resource/client` and resolve only I-003 regressions in the files named by preceding tasks
- [ ] T053 Execute the fresh-data Matematik 1/Data Visualization generation, constraint activation, legacy retirement, and warning scenarios in `specs/I-003-unified-schedule-generation/quickstart.md`, reference the completed T049 List evidence instead of repeating its viewport/zoom matrix, and record combined pass/fail evidence plus any justified manual-only limitation in that file
- [X] T054 Execute the documented one-warm-up/twenty-measured-run reference performance protocol in `backend/tests/performance/test_semester_optimization_performance.py`, record environment and all durations/outcomes in `specs/I-003-unified-schedule-generation/quickstart.md`, and pass only when all twenty end by sixty seconds and at least nineteen end by thirty seconds
- [ ] T055 Conduct the SC-006 unaided usability review with at least ten representative semester planners, use the same prepared scenario without procedural coaching, require selection plus focused-constraint review plus unified preparation for first-attempt success, verify at least 90% first-attempt success, and record anonymized outcomes in `specs/I-003-unified-schedule-generation/quickstart.md`

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: Starts immediately. T001 and test-first regression task
  T003 must complete before production implementation; T002 may be prepared
  independently after the isolated branch/worktree exists.
- **Phase 2 (Foundation)**: Depends on Phase 1 and blocks every user story.
- **US1 and US2 (P1)**: Both depend on Phase 2. Their test authoring can proceed
  in parallel, but implementation is safest in order US1 then US2 because US2
  extends the same freshness service with constraint mutation behavior.
- **US3 (P2)**: Depends on the unified US1 endpoint and US2 effective-constraint
  contract; it removes the alternate paths only after their replacement is ready.
- **US4 (P2)**: Depends only on Phase 2 for backend validation data and may proceed
  beside US1/US2; its final authoritative-refresh integration T044 follows US2.
- **US5 (P2)**: Depends only on the existing List component and can proceed beside
  backend work; final combined review follows US4 warning markup.
- **Polish**: Depends on every story selected for release.

### User story completion order

```text
Setup -> Foundation -> US1 -> US2 -> US3
                       |      |
                       |      `----> US4 ----> US5
                       `------------> US5
All selected stories ----------------> Polish
```

- **US1** delivers the conflict-safe backend MVP and is independently testable
  through the unified API.
- **US2** delivers immediate constraint ownership/preservation and is independently
  testable without a successful solve.
- **US3** makes the unified backend the only supported user/API workflow.
- **US4** is independently testable using manually created conflicting sessions.
- **US5** is independently testable using static schedule fixtures and responsive
  presentation review.

### Within each story

- Complete all listed tests and observe the intended failures before production
  tasks in that story.
- Implement data/value changes before services, services before endpoints, and
  endpoints before page integration.
- Run the story checkpoint before starting a dependent story.
- Commit after a verified logical group; do not mix unrelated dirty-worktree files.

## Parallel Execution Examples

### User Story 1

```text
Parallel test work: T010 (solver), T011 (service), T012 (API), T013 (performance)
Parallel implementation after tests: T014 (optimizer) and T015 (schema)
Then: T016 -> T017 -> T018
```

### User Story 2

```text
Parallel test work: T019 (repository), T020 (API), T021 (staleness), T022 (client API), T023 (component)
Parallel implementation after tests: T024 (schema) and T029 (client API)
Then: T025 -> T026 -> T027/T028 -> T030 -> T031
```

### User Story 3

```text
Parallel test work: T032 (retired API), T033 (unified client API), T034 (UI)
After tests: T035 -> T036 and T037; then T038 -> T039
```

### User Story 4

```text
Parallel test work: T040 (backend validation) and T041 (client rendering)
After tests: T042 and T043; then T044
```

### User Story 5

```text
Parallel test work: T045 (DOM contract) and T046 (CSS/source regression)
After tests: T047 -> T048 -> T049
```

## Implementation Strategy

### MVP first

1. Complete Setup and Foundation.
2. Complete US1 through T018.
3. Stop and verify conflict safety for both one and many selected courses.
4. Treat this as the technical MVP; do not expose it as the final user workflow
   until US2 immediate constraints and US3 legacy retirement are complete.

### First releasable increment

1. Complete Setup, Foundation, US1, and US2.
2. Complete US3 so the safe engine is the only supported workflow.
3. Run the combined backend/client tests before enabling the feature.

### Incremental completion

1. Add US4 precise warnings and verify manual conflict review.
2. Add US5 stable List layout and verify responsive/zoom behavior.
3. Complete Phase 8 regression, performance, documentation, and manual evidence.

## Notes

- No task adds a database table, migration, dependency, generator strategy,
  algorithm selector, editable course weekly windows, exam movement, or automatic
  repair of unselected schedules.
- `GenerationConstraintWindow` remains compatibility data only; this feature
  ignores and clears it but does not add a physical-removal migration.
- A change limited to a past exam must not stale a preparation.
- Exact interval adjacency is permitted because overlap requires positive duration.
- If implementation discovers a requirement change, update `spec.md` before
  changing production code and regenerate/reconcile this task list.
