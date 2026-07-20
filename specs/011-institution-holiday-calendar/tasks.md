---

description: "Implementation tasks for FS-011 institution-wide holiday calendar and avoidance"
---

# Tasks: Institution-Wide Holiday Calendar and Avoidance

**Input**: Design documents from `specs/011-institution-holiday-calendar/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/holiday-calendar.openapi.yaml`, `quickstart.md`

**Tests**: Automated tests are required and are listed before the corresponding production tasks. Each test task must be written and observed failing for the intended reason before its implementation task begins.

**Scope guardrail**: Implement one current institution-wide calendar of full-day holidays only. Do not add holiday history, import, external providers, multiple calendars, timed closures, standalone review-calendar entries, or automatic movement/deletion of saved sessions.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and has no unmet dependency
- **[Story]**: Maps the task to User Story 1, 2, or 3
- Every task names the exact file or files it changes or produces

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Establish reusable, slice-specific examples without adding production abstractions.

- [X] T001 Create backend builders for current holidays, stale revisions, cross-year dates, and holiday/session collisions in `backend/tests/holiday_fixtures.py`
- [X] T002 [P] Create client fixtures for holiday records, CRUD errors, generation evidence, and review alerts in `client/src/test/holidayFixtures.ts`

---

## Phase 2: Foundational (Blocking Persistence)

**Purpose**: Add the one current holiday entity and schema migration required by every story.

**CRITICAL**: No user-story production work begins until this phase is complete.

### Tests for the foundation (write before implementation)

- [X] T003 Add failing migration and persistence tests for clean installs, upgrades from migration `0004`, required date/name columns, unique dates, positive revisions, revision incrementing, stale mapper update/delete rejection, rollback, and preservation of unrelated planning data in `backend/tests/db/test_migrations.py` and `backend/tests/services/test_holiday_calendar.py`

### Implementation for the foundation

- [X] T004 Add the `InstitutionHoliday` current-state entity with date uniqueness and optimistic revision mapping, without history/import/source fields, in `backend/app/models/planning.py`
- [X] T005 Add migration `0005` for the institution holiday table and its constraints in `backend/app/db/migrations/0005_institution_holidays.py`
- [X] T006 Advance migration discovery and schema-head handling through `0005` in `backend/app/db/schema.py`

**Checkpoint**: The application can persist exactly one current named holiday per calendar date and detect stale revisions.

---

## Phase 3: User Story 1 - Maintain Institution Holiday Calendar (Priority: P1) MVP

**Goal**: Let a planner list holidays across years and create, rename, redate, or explicitly delete the current record for a holiday date.

**Independent Test**: From the Holidays administration area, create dates in two years, reject a duplicate date and blank name, update a record with the current revision, reject a stale update, confirm deletion, and verify the deleted or replaced values leave no historical record.

### Tests for User Story 1 (write before implementation)

- [X] T007 [P] [US1] Add failing service tests for sorted full-list and inclusive relevant-range queries; valid past, future, and leap-day dates; invalid dates; whitespace normalization; blank, 200-character, and 201-character names; duplicate dates; stale updates/deletes; explicit delete confirmation; hard deletion; and a 50-holiday list in `backend/tests/services/test_holiday_calendar.py`
- [X] T008 [P] [US1] Add failing API contract tests for `GET/POST /api/holidays` and `GET/PATCH/DELETE /api/holidays/{holidayId}`, including valid and invalid date/name boundaries, revisions, structured errors, and current-state-only responses, in `backend/tests/api/test_holiday_calendar.py`
- [X] T009 [P] [US1] Add failing client contract tests for holiday queries, mutations, revisions, and error mapping in `client/src/api/holidayCalendar.test.ts`
- [X] T010 [P] [US1] Add failing component tests for accessible add/edit/delete-confirmation flows, inline validation, stale-data recovery, multi-year display, and retry behavior in `client/src/components/HolidayAdministration.test.tsx`
- [X] T011 [P] [US1] Add failing navigation and page tests for the Holidays destination and administration view in `client/src/components/ApplicationNavigation.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx`, and `client/src/App.test.tsx`

### Implementation for User Story 1

- [X] T012 [P] [US1] Define holiday records, create/update/delete inputs, revisions, and structured error responses matching the documented collection and item endpoints in `backend/app/schemas/holiday_calendar.py`
- [X] T013 [US1] Implement sorted full-list and internal relevant-range reads, CRUD validation, duplicate handling, optimistic revision checks, and confirmed hard deletion in `backend/app/services/holiday_calendar.py`
- [X] T014 [US1] Implement the holiday CRUD endpoints to match `contracts/holiday-calendar.openapi.yaml` in `backend/app/api/holiday_calendar.py`
- [X] T015 [US1] Register the holiday calendar router under `/api` in `backend/app/main.py`
- [X] T016 [P] [US1] Implement the typed holiday calendar client and structured error mapping in `client/src/api/holidayCalendar.ts`
- [X] T017 [US1] Implement the accessible current-state holiday list and add/edit/delete-confirmation interactions in `client/src/components/HolidayAdministration.tsx`
- [X] T018 [P] [US1] Add the Holidays destination after Semesters without creating a new top-level workspace in `client/src/components/ApplicationNavigation.tsx`
- [X] T019 [US1] Mount holiday administration and preserve existing academic-data navigation behavior in `client/src/pages/AcademicDataPage.tsx` and `client/src/App.tsx`

**Checkpoint**: User Story 1 is usable and independently testable; this is the smallest administratively useful increment.

---

## Phase 4: User Story 2 - Keep Automatic Generation Off Holidays (Priority: P2)

**Goal**: Treat current institution holidays as hard unavailable dates in single-course, legacy multi-course, and FS-010 conflict-aware generation, while naming relevant holiday evidence in incomplete or failed results.

**Independent Test**: Seed holidays that collide with otherwise valid dates, run each generation mode, and verify no newly saved session uses a holiday; when a holiday contributes to failure or incompleteness, verify the result names its current date and name, and verify a holiday change during generation prevents an invalid save.

### Tests for User Story 2 (write before implementation)

- [X] T020 [P] [US2] Add failing single-course unit tests for successful non-holiday placement, all-or-nothing failure when holidays remove feasibility, mixed failure causes, deduplicated current holiday evidence, and stale snapshot inputs in `backend/tests/services/test_schedule_generation.py`
- [X] T021 [P] [US2] Add failing single-course API tests for successful, failed, and stale-calendar outcomes using server-loaded holidays, including paired non-null holiday date/name evidence, omission of both fields for other failures, and rejection of invalid saves, in `backend/tests/api/test_draft_schedule.py`
- [X] T022 [P] [US2] Add failing legacy multi-course service tests for fully successful, mixed partial-batch, failed-course, and stale outcomes; holiday exclusion; mixed causes; per-course evidence; and deduplication by code/date in `backend/tests/services/test_multi_course_generation.py`
- [X] T023 [P] [US2] Add failing legacy multi-course API tests for complete, mixed partial-batch, failed, and stale-calendar outcomes using server-loaded constraints, paired non-null holiday date/name evidence with both fields omitted otherwise, and no invalid partial save after a concurrent change in `backend/tests/api/test_multi_course_generation.py`
- [X] T024 [P] [US2] Add failing semester-optimizer tests for holiday exclusion, relevant named blocking evidence, and no mutation of existing saved sessions in `backend/tests/services/test_semester_optimization.py`
- [X] T025 [P] [US2] Add failing FS-010 service tests for complete, partial, unchanged, failed, and stale outcomes; the internal union of caller unavailable dates and holidays; named blocking reasons; unchanged request-owned unavailable dates; and snapshot invalidation in `backend/tests/services/test_conflict_aware_generation.py`
- [X] T026 [P] [US2] Add failing FS-010 API tests for complete, partial, unchanged, failed, and stale outcomes using server-authoritative holidays, paired non-null holiday date/name reasons with both fields omitted from other reasons, deduplication, unchanged caller unavailable dates, and save-time revalidation in `backend/tests/api/test_conflict_aware_generation.py`
- [X] T027 [P] [US2] Add failing single-generation client contract tests proving holiday date/name context is present together and non-null for institution-holiday evidence and both fields are absent otherwise in `client/src/api/draftSchedule.test.ts`
- [X] T028 [P] [US2] Add failing batch-generation client contract tests proving per-course holiday date/name evidence is present together and non-null or both fields are absent in `client/src/api/multiCourseDraftGeneration.test.ts`
- [X] T029 [P] [US2] Add failing FS-010 client contract tests proving institution-holiday blocking reasons contain paired non-null date/name evidence while other reasons omit both fields in `client/src/api/conflictAwareGeneration.test.ts`
- [X] T030 [P] [US2] Add failing summary tests that render current holiday names/dates and keep separate holiday dates distinct in `client/src/components/BatchResultSummary.test.tsx`

### Implementation for User Story 2

- [X] T031 [P] [US2] Add paired optional `holidayDate` and `holidayName` context to single-generation failure responses, requiring both non-null fields together or omitting both, in `backend/app/schemas/draft_schedule.py`
- [X] T032 [P] [US2] Add paired per-course institution-holiday date/name evidence, requiring both non-null fields together or omitting both, in `backend/app/schemas/multi_course_generation.py`
- [X] T033 [P] [US2] Add paired `INSTITUTION_HOLIDAY` date/name fields to FS-010 blocking reasons while requiring other reasons to omit both fields in `backend/app/schemas/conflict_aware_generation.py`
- [X] T034 [US2] Implement canonical relevant-range holiday snapshots and fingerprints after the failing generation tests, then apply holiday dates as hard constraints with substantiated, deduplicated evidence in `backend/app/services/holiday_calendar.py` and `backend/app/services/schedule_generation.py`
- [X] T035 [US2] Load a canonical holiday snapshot for single-course generation, revalidate it before save, and preserve invalidated results without saving holiday sessions in `backend/app/api/draft_schedule.py`
- [X] T036 [US2] Apply current holidays and relevant named evidence to each legacy batch item in `backend/app/services/multi_course_generation.py`
- [X] T037 [US2] Load the server-authoritative canonical holiday snapshot for legacy multi-course generation and revalidate it before persisting affected course outcomes in `backend/app/api/multi_course_generation.py`
- [X] T038 [US2] Apply holidays as hard constraints and carry relevant named blocking evidence through semester optimization in `backend/app/services/semester_optimization.py`
- [X] T039 [US2] Union current holidays with FS-010 caller unavailable dates internally and deduplicate blocking reasons by code/date in `backend/app/services/conflict_aware_generation.py`
- [X] T040 [US2] Load and revalidate the canonical holiday snapshot for FS-010 generation before persistence in `backend/app/api/conflict_aware_generation.py`
- [X] T041 [P] [US2] Decode and expose optional single-generation holiday date/name context in `client/src/api/draftSchedule.ts`
- [X] T042 [P] [US2] Decode and expose per-course holiday evidence for legacy batch results in `client/src/api/multiCourseDraftGeneration.ts`
- [X] T043 [P] [US2] Decode structured institution-holiday reasons for FS-010 results in `client/src/api/conflictAwareGeneration.ts`
- [X] T044 [US2] Render holiday failure evidence and use code/date identity so different holiday dates are not collapsed in `client/src/components/BatchResultSummary.tsx`

**Checkpoint**: Every existing automatic generation mode excludes current holidays and explains relevant holiday-caused incompleteness without changing saved sessions.

---

## Phase 5: User Story 3 - See and Refresh Holiday Alerts in Schedule Review (Priority: P3)

**Goal**: Flag existing generated or manual sessions that now fall on a holiday, keep manual saves non-blocking, and refresh derived alerts after holiday or session changes without altering the sessions.

**Independent Test**: Save a manual session on an existing holiday, create or rename a holiday under an existing session, and delete or redate that holiday; verify review alerts appear, update, and disappear using the current holiday name/date while session records, review mode, filters, and selections remain unchanged.

### Tests for User Story 3 (write before implementation)

- [X] T045 [P] [US3] Add failing validation tests for generated/manual session collisions, current holiday names, coexistence with other alerts, unavailable validation context, hard-deleted holidays, and zero session mutation in `backend/tests/services/test_draft_schedule_validation.py`
- [X] T046 [P] [US3] Add failing API tests proving manual holiday sessions still save and schedule responses derive current `INSTITUTION_HOLIDAY` alerts without standalone holiday entries in `backend/tests/api/test_draft_schedule.py`
- [X] T047 [P] [US3] Add failing client contract tests for typed holiday alerts with current date/name and no fabricated related sessions in `client/src/api/draftSchedule.test.ts`
- [X] T048 [P] [US3] Add failing review-panel tests for visible, non-blocking holiday alerts alongside existing alert types and filters in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T049 [P] [US3] Add failing refresh tests proving holiday catalog changes reload selected-semester schedules, existing session create/edit/delete/replace refresh remains intact, and view, filters, selection, and last-known data survive retryable failure in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T050 [P] [US3] Add failing integration tests proving successful holiday create/update/delete actions propagate the catalog revision and trigger review refresh while failed actions do not in `client/src/components/HolidayAdministration.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx`, and `client/src/App.test.tsx`
- [X] T051 [P] [US3] Add a failing performance test that derives holiday alerts for 50 holidays and 500 sessions within two seconds in `backend/tests/performance/test_holiday_calendar_performance.py`

### Implementation for User Story 3

- [X] T052 [US3] Derive `INSTITUTION_HOLIDAY` alerts from current holidays with date/name context, report unavailable validation context instead of declaring sessions safe, and avoid blocking manual saves or mutating sessions in `backend/app/services/draft_schedule_validation.py`
- [X] T053 [US3] Load current holidays for schedule validation and serialize derived holiday alerts while keeping standalone holiday rows out of review responses in `backend/app/api/draft_schedule.py`
- [X] T054 [P] [US3] Add the typed holiday alert code and date/name context to the draft schedule client model in `client/src/api/draftSchedule.ts`
- [X] T055 [US3] Reload selected-semester schedules when the external catalog revision changes while preserving existing session-change refresh, local review state, and last-known data in `client/src/pages/CourseSchedulePage.tsx`
- [X] T056 [US3] Emit the existing catalog-change signal only after successful holiday mutations and connect it to schedule refresh in `client/src/components/HolidayAdministration.tsx`, `client/src/pages/AcademicDataPage.tsx`, and `client/src/App.tsx`

**Checkpoint**: All three stories are independently testable and the full FS-011 completion condition is met.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Demonstrate contract, regression, performance, and usability completion without broadening the slice.

- [X] T057 [P] Validate implemented holiday request/response examples against `specs/011-institution-holiday-calendar/contracts/holiday-calendar.openapi.yaml` and record results in `specs/011-institution-holiday-calendar/validation/contract-validation.md`
- [X] T058 Run the focused and full backend/client automated suites from `specs/011-institution-holiday-calendar/quickstart.md` and record commands and results in `specs/011-institution-holiday-calendar/validation/automated-tests.md`
- [ ] T059 Execute the quickstart CRUD, all-generation-mode, concurrent-change, manual-session alert, refresh, accessibility, and usability scenarios with at least ten representative planners or acceptance reviewers; record participant-level evidence, at least 90% unassisted success for each applicable usability protocol, and the two-second thresholds in `specs/011-institution-holiday-calendar/validation/manual-review.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundation)**: Depends on Phase 1 and blocks production work for all stories.
- **Phase 3 (US1)**: Depends on Phase 2; supplies the planner-facing maintenance flow.
- **Phase 4 (US2)**: Depends on Phase 2 and the internal range-read behavior from T013; canonical generation snapshots are added in T034 only after T020-T026 establish failing behavior, and the story remains testable without the US1 UI.
- **Phase 5 (US3)**: Depends on Phase 2 and the internal range-read behavior from T013. T050 and T056 additionally depend on the US1 mutation UI; its backend validation remains independently testable with fixtures.
- **Phase 6 (Polish)**: Depends on all story phases selected for delivery.

### User Story Dependency Graph

```text
Phase 1 Setup
    |
Phase 2 Foundation
    |
    +--> US1 Calendar maintenance --------+
    |                                     |
    +--> US2 Generation avoidance         +--> Phase 6 validation
    |                                     |
    +--> US3 Derived review alerts --------+
             (refresh integration uses US1 mutations)
```

### Within Each Story

- Complete all listed tests and confirm their intended failure before production implementation.
- Implement shared schemas and services before endpoints or UI consumers.
- Revalidate holiday snapshots before any generated sessions are persisted.
- Complete the independent test at the story checkpoint before advancing.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- In US1, T007-T011 can run in parallel; after backend service/API prerequisites, T016 and T018 can run in parallel.
- In US2, T020-T030 can run in parallel; T031-T033 can run in parallel; client tasks T041-T043 can run in parallel after their contracts stabilize.
- In US3, T045-T051 can run in parallel; T054 can run in parallel with backend implementation after the alert contract is fixed.
- After Phase 2 and T013, US2 backend work and US3 backend validation can proceed in parallel with completion of the US1 interface.

## Parallel Examples

### User Story 1

```text
T007 Service CRUD/concurrency tests in backend/tests/services/test_holiday_calendar.py
T008 Holiday API contract tests in backend/tests/api/test_holiday_calendar.py
T009 Client contract tests in client/src/api/holidayCalendar.test.ts
T010 Administration component tests in client/src/components/HolidayAdministration.test.tsx
T011 Navigation/page tests in their existing client test files
```

### User Story 2

```text
T020 Single-generation service tests
T022 Legacy multi-course service tests
T024 Semester-optimizer tests
T025 FS-010 service tests
T027-T030 Client contract and rendering tests
```

### User Story 3

```text
T045 Validation behavior tests
T046 Schedule API tests
T048 Review-panel tests
T049 External-refresh tests
T051 Performance test
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 and run its independent test.
3. Stop at the US1 checkpoint for the smallest demonstrable maintenance increment.

This MVP is not the completed FS-011 slice: the stated feature outcome additionally requires US2 and US3.

### Full Slice Delivery

1. Deliver US1 current-state calendar maintenance.
2. Deliver US2 hard holiday constraints for every automatic generation mode.
3. Deliver US3 derived alerts and refresh behavior while preserving saved sessions.
4. Complete Phase 6 and verify every success criterion.

## Notes

- `[P]` means different files and no unmet dependency; it does not override test-first order.
- No task retains old holiday names/dates or creates audit/history records; edits replace current state and confirmed deletion removes it.
- No task adds iCalendar/CSV import preparation, provider/source metadata, recurrence, multiple calendars, or timed closures.
- Existing saved sessions are evidence inputs for alerts only and must never be silently moved or deleted.
- Commit after each task or cohesive task group, and run the relevant focused tests before each commit.

