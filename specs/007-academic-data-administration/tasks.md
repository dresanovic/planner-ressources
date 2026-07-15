---

description: "Dependency-ordered implementation tasks for FS-007 Academic Planning Data Administration"
---

# Tasks: Academic Planning Data Administration

**Input**: Design documents from `specs/007-academic-data-administration/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/academic-administration.openapi.yaml`, `quickstart.md`

**Tests**: Tests are REQUIRED by the constitution wherever automated testing is practical. Create or update each test task before its corresponding production implementation task and confirm the intended test fails before implementing where practical.

**Organization**: Tasks are grouped by user story so each story has an independently testable checkpoint. The recommended delivery order is US1 → US2 → US3 → US4 because later stories reuse the administration shell and persistence foundation while retaining their own acceptance tests.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other ready tasks because it uses different files and has no dependency on their unfinished work
- **[Story]**: Maps the task to a user story from `spec.md`
- Every task includes an exact repository path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Isolate the cross-stack migration work and establish a verified FS-001–FS-006 baseline.

- [X] T001 Create the `codex/fs-007-academic-data-administration` implementation branch, run the pre-change backend/client commands from `specs/007-academic-data-administration/quickstart.md`, and record any baseline failure in `specs/007-academic-data-administration/tasks.md` before changing production code

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared schema, migration, concurrency, and contract primitives required by every user story.

**CRITICAL**: No user-story production implementation begins until T002–T007 are complete and the new foundational tests pass.

- [X] T002 [P] Add failing migration/startup tests for lifecycle fields, revisions, canonical normalized-name uniqueness, collision-safe legacy name-repair states without startup failure, exact-window uniqueness, legacy Course semester repair state, Draft Schedule snapshot backfill, sequential 0001→0002→0003 upgrade, unknown-partial-schema diagnostics, idempotent restart, and SQLite foreign-key enforcement in `backend/tests/db/test_migrations.py`
- [X] T003 [P] Add failing service tests for name normalization and repair, positive whole-number Cohort/Course rules with `minimum <= maximum <= total` and no added upper limit, integer expected-revision conflicts, visible missing-window planning availability, legacy assignment repair, and uniform domain-error metadata in `backend/tests/services/test_academic_catalog.py`
- [X] T004 [P] Add failing client contract tests for paginated envelopes, lifecycle revisions, `nameRepairRequired`, availability reasons, usage blockers, 422 field errors, 409 stale/conflict errors, and retained request data in `client/src/api/academicCatalog.test.ts`
- [X] T005 Implement migration `0003`, catalog lifecycle/revision fields, canonical normalized-name uniqueness for new/repaired rows, collision-safe visible repair state for supported legacy name conflicts without startup failure, Course current-Semester repair, immutable Draft Schedule academic snapshots, protected ORM relationships, sequential startup migration that stops only for unknown unsafe partial schemas, and SQLite foreign-key setup in `backend/app/models/planning.py`, `backend/app/db/migrations/0003_academic_catalog_administration.py`, `backend/app/db/schema.py`, and `backend/app/db/session.py` until T002 passes
- [X] T006 Implement shared academic catalog request/response/error schemas plus numeric validation, normalization/name-repair, revision, visible unavailable-option, and legacy-assignment-repair primitives in `backend/app/schemas/academic_catalog.py` and `backend/app/services/academic_catalog.py` until T003 passes
- [X] T007 Implement shared typed catalog models, paginated response parsing, mutation/error handling, and expected-revision request helpers in `client/src/api/academicCatalog.ts` until T004 passes

**Checkpoint**: Supported databases migrate without data loss, shared contracts compile, and every new catalog mutation can use the same validation/error/revision foundation.

---

## Phase 3: User Story 1 — Build the Academic Planning Catalog (Priority: P1) MVP

**Goal**: Starting without academic records, a planner can create and revisit a valid Semester, Cohort, Study Type with Time Windows, and Course assigned to exactly one Semester; the Course becomes selectable for planning.

**Independent Test**: Create one valid record of every academic type through the UI, connect the Course to its required academic relationships and existing read-only Lecturer/Room options, reload administration, then verify the Course appears only for its assigned Semester in Schedule.

### Tests for User Story 1 (write and fail before implementation)

- [X] T008 [P] [US1] Add failing FastAPI contract tests for paginated list/detail/create of Semesters, Cohorts, Study Types, nested Time Windows, and Courses, including positive whole-number Cohort/Course rules, `minimum <= maximum <= total`, no added upper limit, normalized duplicate rejection, exact-window duplicate rejection, partial-overlap acceptance, required relationship errors, and actionable no-Lecturer/no-Room creation blockers without placeholders in `backend/tests/api/test_academic_catalog.py`
- [X] T009 [P] [US1] Add failing planning-option tests for `semesterId`, active relationship filtering, Course single-semester availability, active Time Windows, otherwise eligible Courses retained with `available=false` and `MISSING_ACTIVE_TIME_WINDOW`, and additive Lecturer/Room options in `backend/tests/api/test_planning_options.py`
- [X] T010 [P] [US1] Add failing page tests for empty catalog states, category navigation, record persistence after remount, creation success/error feedback, and the complete no-academic-seed creation journey in `client/src/pages/AcademicDataPage.test.tsx`
- [X] T011 [P] [US1] Add failing controlled-form tests for required fields, retained values after 422 responses, Course Semester/Cohort/Study Type/read-only Lecturer/Room selectors, and nested Time Window validation in `client/src/components/AcademicRecordEditor.test.tsx`

### Implementation for User Story 1

- [X] T012 [US1] Implement paginated list/detail/create queries and validation for all five academic record types, including normalized uniqueness and exact Time Window uniqueness, in `backend/app/services/academic_catalog.py` until T008 service-facing scenarios pass
- [X] T013 [US1] Implement the Semester, Cohort, Course, Study Type, and nested Time Window list/detail/create endpoints and register the router in `backend/app/api/academic_catalog.py`, `backend/app/schemas/academic_catalog.py`, and `backend/app/main.py` until T008 passes
- [X] T014 [US1] Extend planning options with `semesterId`, availability/reasons, and Lecturer options; filter by active required parents and current Semester while retaining otherwise eligible missing-window Courses as unavailable; and reject invalid Course/Semester pairs at the backend boundary in `backend/app/api/planning_options.py`, `backend/app/schemas/planning_options.py`, `backend/app/services/draft_schedule_repository.py`, and `backend/app/services/multi_course_generation.py` until T009 passes
- [X] T015 [P] [US1] Add typed list/detail/create methods for Semesters, Cohorts, Courses, Study Types, and nested Time Windows plus the additive planning-option fields in `client/src/api/academicCatalog.ts` and `client/src/api/planningOptions.ts`
- [X] T016 [P] [US1] Implement reusable accessible catalog list and controlled create/edit form components, including empty/loading/error states and nested Study Type Time Windows, in `client/src/components/AcademicCatalogList.tsx` and `client/src/components/AcademicRecordEditor.tsx` until T011 passes
- [X] T017 [US1] Implement the Academic Data page, category tabs, list/editor layout, success/error announcements, responsive styling, and lightweight Schedule/Academic Data navigation in `client/src/pages/AcademicDataPage.tsx`, `client/src/App.tsx`, and `client/src/App.css` until T010 passes
- [X] T018 [US1] Run the focused US1 backend/client tests from T008–T011 and complete Quickstart Scenarios 1–2 in `specs/007-academic-data-administration/quickstart.md`, fixing only US1 defects in the files changed by T012–T017

**Checkpoint**: User Story 1 is independently usable as the MVP: academic records can be built through the product and immediately feed the existing planner.

---

## Phase 4: User Story 2 — View and Correct Academic Records (Priority: P2)

**Goal**: A planner can inspect usage, edit current records, reassign a Course, and receive stale/date validation while all academic facts captured by saved schedules remain unchanged.

**Independent Test**: Generate a schedule, edit every captured academic source value, safely reassign its Course, reject an excluding Semester date edit and a stale edit, and verify the old schedule context/validation stays unchanged while future planning uses current data.

### Tests for User Story 2 (write and fail before implementation)

- [X] T019 [P] [US2] Add failing service/API tests for canonical edits, usage summaries, expected-revision conflicts, relationship validation, Semester-date exclusion checks, Course reassignment, legacy Semester repair completion, and legacy normalized-name repair that preserves existing use but requires unique rename before edit/reactivation in `backend/tests/services/test_academic_catalog.py` and `backend/tests/api/test_academic_catalog.py`
- [X] T020 [P] [US2] Add failing repository/API/validation tests proving Draft Schedule snapshots preserve Course name/units/session preferences, Cohort ID/name/size, Study Type ID/name, Semester facts, response filters, room-capacity behavior, and copied constraint-window behavior across source edits in `backend/tests/services/test_draft_schedule_repository.py`, `backend/tests/services/test_draft_schedule_validation.py`, and `backend/tests/api/test_draft_schedule.py`
- [X] T021 [P] [US2] Add failing PATCH/usage/stale-response client tests, including expected revisions, multi-field 422 errors, current-record conflict metadata, and Course reassignment payloads in `client/src/api/academicCatalog.test.ts`
- [X] T022 [P] [US2] Add failing page/editor tests for usage display, edit success, visible legacy Semester/name repair guidance, unique rename enforcement, preserved form values after validation/stale conflict, refresh-and-review behavior, Semester date blockers, active-but-unavailable relationships, and Course reassignment in `client/src/pages/AcademicDataPage.test.tsx` and `client/src/components/AcademicRecordEditor.test.tsx`

### Implementation for User Story 2

- [X] T023 [US2] Implement usage aggregation, atomic revisioned edits, relationship/date validation, Semester saved-session bounds checks, Course reassignment, legacy assignment repair, and visible normalized-name repair completion without disrupting existing planning use in `backend/app/services/academic_catalog.py` until T019 service scenarios pass
- [X] T024 [US2] Implement item PATCH and usage endpoints with canonical 200, structured 404/409/422 responses, and transaction rollback in `backend/app/api/academic_catalog.py` and `backend/app/schemas/academic_catalog.py` until T019 API scenarios pass
- [X] T025 [P] [US2] Capture immutable academic snapshots on Draft Schedule create/replacement and use them for saved response context, filters, cohort capacity, and Study Type validation while retaining source IDs for usage protection in `backend/app/services/draft_schedule_repository.py`, `backend/app/services/draft_schedule_validation.py`, `backend/app/api/draft_schedule.py`, and `backend/app/schemas/draft_schedule.py` until T020 passes
- [X] T026 [US2] Implement typed item PATCH and usage calls with stale/current-record metadata in `client/src/api/academicCatalog.ts` until T021 passes
- [X] T027 [US2] Add record detail/usage presentation, revision-aware editing, visible legacy Semester/name repair guidance and unique-rename completion, retained validation values, stale refresh/review actions, Semester blocker feedback, Course reassignment, and active-but-unavailable status in `client/src/components/AcademicCatalogList.tsx`, `client/src/components/AcademicRecordEditor.tsx`, and `client/src/pages/AcademicDataPage.tsx` until T022 passes
- [X] T028 [US2] Run the focused US2 backend/client tests from T019–T022 and complete Quickstart Scenarios 3–4, 7, and the stale-write portion of Scenario 8 in `specs/007-academic-data-administration/quickstart.md`, fixing only US2 defects in T023–T027 files

**Checkpoint**: User Stories 1 and 2 work independently; editing current catalog data never rewrites saved academic schedule facts.

---

## Phase 5: User Story 3 — Retire or Delete Records Safely (Priority: P3)

**Goal**: A planner can archive/reactivate records without status cascades, permanently delete only unused records, and understand categorized blockers for protected deletion.

**Independent Test**: Delete an unused record, block deletion for every dependent/saved-schedule reference type, archive and reactivate a protected parent, and verify dependent statuses remain unchanged while new-planning availability follows active parents.

### Tests for User Story 3 (write and fail before implementation)

- [X] T029 [P] [US3] Add failing service/API tests for every entity’s dependent and saved-schedule blocker edge, combined blocker responses, unused deletion, stale delete, archive/reactivate, reactivation validation, no ORM cascade, and unchanged dependent statuses in `backend/tests/services/test_academic_catalog.py` and `backend/tests/api/test_academic_catalog.py`
- [X] T030 [P] [US3] Add failing client API tests for usage preflight, archive/reactivate commands, expected-revision delete, 204 success, stale conflict, reactivation conflict, and categorized protected-deletion metadata in `client/src/api/academicCatalog.test.ts`
- [X] T031 [P] [US3] Add failing dialog/page tests for cancel-without-request, focus entry/containment/return, Escape close, unused delete confirmation, separated dependent/saved-schedule blockers, Archive alternative, non-cascade messaging, and active/inactive filtering in `client/src/components/ProtectedDeleteDialog.test.tsx` and `client/src/pages/AcademicDataPage.test.tsx`

### Implementation for User Story 3

- [X] T032 [US3] Implement blocker queries for Semester, Cohort, Course, Study Type, and Time Window; atomic no-usage delete; revisioned archive/reactivate; relationship/name reactivation validation; and non-cascading lifecycle behavior in `backend/app/services/academic_catalog.py` until T029 service scenarios pass
- [X] T033 [US3] Implement DELETE, archive, and reactivate endpoints with canonical success and structured stale/protected/validation outcomes in `backend/app/api/academic_catalog.py` and `backend/app/schemas/academic_catalog.py` until T029 API scenarios pass
- [X] T034 [P] [US3] Implement typed usage preflight, lifecycle command, and permanent-delete methods in `client/src/api/academicCatalog.ts` until T030 passes
- [X] T035 [US3] Implement the accessible protected-delete confirmation/blocker dialog with Archive alternative and focus management in `client/src/components/ProtectedDeleteDialog.tsx` and `client/src/App.css` until the dialog cases in T031 pass
- [X] T036 [US3] Integrate archive/reactivate/delete, active/inactive filters, non-cascading availability feedback, canonical refetch, and last-known-data Retry behavior into `client/src/pages/AcademicDataPage.tsx` and `client/src/components/AcademicCatalogList.tsx` until all T031 cases pass
- [X] T037 [US3] Run the focused US3 backend/client tests from T029–T031 and complete Quickstart Scenarios 5–6 plus the refresh-failure portion of Scenario 8 in `specs/007-academic-data-administration/quickstart.md`, fixing only US3 defects in T032–T036 files

**Checkpoint**: User Stories 1–3 work independently; no destructive or lifecycle action silently invalidates dependent or saved planning data.

---

## Phase 6: User Story 4 — Continue Existing Planning with Updated Options (Priority: P4)

**Goal**: Catalog changes refresh compatible planning choices within the established workflows, invalid prior selections are never silently replaced, and all FS-001–FS-006 behaviors continue to pass with legacy and UI-created data.

**Independent Test**: Change, archive, delete, and reassign catalog records; return to single/batch planning; verify choices refresh and invalid selections require action while saved schedules, constraints, manual edits, overview, and alerts remain usable.

### Tests for User Story 4 (write and fail before implementation)

- [X] T038 [P] [US4] Extend backend planning-option, single-generation, batch-generation, constraint, manual-edit, overview, and validation tests for inactive parents, missing assignment, missing-window Courses retained as unavailable with `MISSING_ACTIVE_TIME_WINDOW`, Course reassignment, both legacy repair states, historical snapshots, and newly UI-created catalog data in `backend/tests/api/test_planning_options.py`, `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_multi_course_generation.py`, `backend/tests/services/test_multi_course_generation.py`, and `backend/tests/services/test_draft_schedule_validation.py`
- [X] T039 [P] [US4] Add failing Schedule page tests for option refetch on view return, Course filtering by assigned Semester, visible missing-window Courses with unavailable reason, preserved valid IDs, retained/flagged invalid prior selection, no automatic substitute, blocked generation until correction, and last-known options on refresh failure in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T040 [P] [US4] Add failing app-navigation tests proving successful Academic Data mutations trigger canonical administration/planning refetch without a router dependency and keyboard navigation returns to Schedule predictably in `client/src/App.test.tsx`

### Implementation for User Story 4

- [X] T041 [P] [US4] Enforce current Course assignment and active academic relationship chains in every single/batch generation and constraint entry point while preserving historical read/edit paths and returning actionable `MISSING_ACTIVE_TIME_WINDOW`/invalid-option errors for visible unavailable Courses in `backend/app/api/draft_schedule.py`, `backend/app/api/multi_course_generation.py`, `backend/app/services/draft_schedule_repository.py`, `backend/app/services/multi_course_generation.py`, and `backend/app/services/draft_schedule_validation.py` until T038 passes
- [X] T042 [US4] Implement shared catalog-change invalidation, refetch-on-Schedule-return, assigned-Semester Course filtering, visible unavailable reasons including missing windows, valid-ID preservation, invalid-selection retention, and blocked generation without substitution in `client/src/App.tsx`, `client/src/pages/CourseSchedulePage.tsx`, and `client/src/api/planningOptions.ts` until T039–T040 pass
- [X] T043 [US4] Run the complete existing backend and client regression suites; fix FS-007-caused defects in their owning files under `backend/app/` and `client/src/`, and modify existing tests only when an approved behavior in `specs/007-academic-data-administration/spec.md` or `specs/007-academic-data-administration/contracts/academic-administration.openapi.yaml` changed, without weakening assertions merely to make the suites pass
- [X] T044 [US4] Complete the Schedule compatibility portions of Quickstart Scenarios 1, 3–5, 8, and 9 in `specs/007-academic-data-administration/quickstart.md`, confirming FS-001–FS-006 behavior with both legacy and UI-created academic records, legacy repair states, and visible missing-window feedback

**Checkpoint**: All four user stories are complete, catalog changes are reflected safely in planning, and FS-001–FS-006 regressions are green.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, accessibility, performance, and verification across the complete slice.

- [X] T045 [P] Document the academic administration endpoints, migration/repair behavior, resource-read-only boundary, and local validation workflow in `backend/README.md` and `client/README.md`
- [X] T046 [P] Add failing seed-script compatibility tests proving seeded Courses receive valid current Semester assignments, satisfy canonical normalized-name and lifecycle rules, and remain usable after migration in `backend/tests/scripts/test_seed_dummy_planning_data.py`
- [X] T047 Update `backend/scripts/seed_dummy_planning_data.py` so seeded Courses receive valid current Semester assignments and remain usable after migration without bypassing canonical normalized-name, name-repair, or lifecycle rules until T046 passes
- [X] T048 Run `python -m pytest` from `backend/` and `npm run test`, `npm run lint`, and `npm run build` from `client/`, recording any unavoidable residual risk in `specs/007-academic-data-administration/tasks.md`
- [X] T049 Execute Quickstart Scenario 10 and the documented 100-record performance protocol in `specs/007-academic-data-administration/quickstart.md`, record the reference environment, raw trials, and SC-007/SC-008 outcomes in `specs/007-academic-data-administration/validation/performance-results.md`; for every reproducible failure, first add or update a failing automated regression test wherever practical, and when automation is genuinely impractical document the specific reason and repeatable manual verification path in `specs/007-academic-data-administration/plan.md` before correcting the owning `client/src/` or `backend/app/` production file
- [ ] T050 Conduct the unaided usability protocol for SC-001, SC-002, and SC-004 with at least 10 representative planner users or acceptance reviewers, record completion times and first-attempt outcomes in `specs/007-academic-data-administration/validation/usability-results.md`, and document whether each 90% threshold passes
- [X] T051 Re-run the constitution and scope check against `specs/007-academic-data-administration/spec.md` and `specs/007-academic-data-administration/plan.md`, inspect `git diff`/`git status`, and confirm no FS-008 resource administration or other out-of-scope behavior entered the implementation

---

## Dependencies & Execution Order

### Phase dependencies

```text
Phase 1 Setup
    ↓
Phase 2 Foundation (blocks all stories)
    ↓
US1 Build Catalog (MVP)
    ↓
US2 View/Edit + Historical Preservation
    ↓
US3 Archive/Delete Safety
    ↓
US4 Existing Planning Compatibility
    ↓
Phase 7 Polish and Full Verification
```

- **Setup** has no dependency.
- **Foundation** depends on the baseline recorded by T001.
- **US1** depends on all foundational tasks and provides the reusable administration shell.
- **US2** depends on US1’s records/endpoints/UI shell and the foundational snapshot columns; it remains independently testable through its edit/history scenario.
- **US3** depends on US1’s shell and shared usage/revision primitives; it can begin after US1, but the recommended sequence completes US2 first because both touch catalog usage/editor files.
- **US4** depends on US1 planning-option creation, US2 snapshot behavior, and US3 lifecycle behavior to exercise the complete refresh/regression boundary.
- **Polish** depends on every story selected for delivery.

### Within each story

1. Write the story’s backend/client tests and confirm they fail for the intended behavior.
2. Implement backend domain/service behavior.
3. Implement HTTP endpoints/contracts.
4. Implement client API and UI behavior.
5. Run focused automated tests and the story’s Quickstart scenarios.
6. Do not mark the story checkpoint complete while a required acceptance scenario is unverified.

## Parallel Opportunities

### Foundation

- T002 migration tests, T003 service tests, and T004 client contract tests can run in parallel.
- After their respective tests fail, backend T005–T006 and client T007 can progress on separate files, with T006 waiting for T005 model names where necessary.

### User Story 1

```text
Parallel test batch: T008 + T009 + T010 + T011
After tests: backend T012–T014 || client T015–T016
Integration: T017 → T018
```

### User Story 2

```text
Parallel test batch: T019 + T020 + T021 + T022
After tests: catalog backend T023–T024 || snapshot backend T025 || client T026
Integration: T027 → T028
```

### User Story 3

```text
Parallel test batch: T029 + T030 + T031
After tests: backend T032–T033 || client API T034
Integration: T035–T036 → T037
```

### User Story 4

```text
Parallel test batch: T038 + T039 + T040
After tests: backend T041 || client T042
Regression/acceptance: T043 → T044
```

## Implementation Strategy

### MVP first

1. Complete T001–T007.
2. Complete T008–T018 for User Story 1.
3. Stop and independently validate the no-academic-seed catalog creation workflow.
4. Demonstrate that the created Course is available only in its assigned Semester.

### Incremental delivery

1. **US1** delivers maintainable catalog creation and planning selection.
2. **US2** adds safe correction, usage context, reassignment, stale protection, and immutable saved facts.
3. **US3** adds reversible retirement and protected permanent deletion.
4. **US4** closes the existing-workflow refresh and regression boundary.
5. Final polish validates accessibility, performance, documentation, and the complete constitution gate.

### Team strategy

- Complete Foundation collaboratively before splitting work.
- Backend and client tests for a story can be assigned in parallel.
- Backend and frontend implementation can proceed in parallel after the story’s contract tests fail, using `contracts/academic-administration.openapi.yaml` as the shared boundary.
- Avoid simultaneous edits to `backend/app/services/academic_catalog.py`, `client/src/pages/AcademicDataPage.tsx`, or their shared test files across different stories; follow the recommended story order for those files.

## Notes

- `[P]` means the task is parallel-safe only after its stated prerequisites are satisfied.
- Course Lecturer/Room selection reuses existing read-only records; Lecturer/Room CRUD, availability, and multiple-resource eligibility remain FS-008 or later.
- Legacy Courses without an inferable current Semester remain visible for planner repair and are excluded from new generation until assigned.
- Saved Draft Schedule academic snapshots must drive both display and academic validation; source IDs remain only for traceability and deletion protection.
- Do not add a router, global cache, form library, background service, audit system, import flow, authentication, or resource-administration scope.
- Commit after a verified task group rather than mixing unfinished stories.
