# Tasks: FS-008 Resource Eligibility and Availability

**Input**: Design documents from `specs/008-resource-eligibility-availability/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/resource-eligibility-availability.openapi.yaml`, `quickstart.md`

**Tests**: Tests are required by the project constitution. Every user-story phase starts with automated tests that must be written and observed failing before the corresponding production tasks where practical.

**Organization**: Tasks are grouped by user story and ordered so each completed phase has an independent acceptance path. Exact paths are repository-relative.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May run in parallel with other tasks at that point because it changes different files and does not depend on unfinished work.
- **[Story]**: Maps the task to a user story from `spec.md`.
- Tasks without a story label belong to shared setup, foundations, or final verification.

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Isolate implementation work and create shared test data without changing production behavior.

- [ ] T001 Create a `codex/fs-008-resource-eligibility` implementation branch, run the current backend/client baseline commands, and record commit, commands, and outcomes in `specs/008-resource-eligibility-availability/validation/baseline-results.md`
- [ ] T002 [P] Add reusable Lecturer, Room, Course eligibility, and unavailability factories that preserve existing FS-001–FS-007 fixtures in `backend/tests/resource_fixtures.py`
- [ ] T003 [P] Add typed duplicate-name, active/inactive, availability, eligibility, and removal-outcome fixtures in `client/src/test/resourceFixtures.ts`

---

## Phase 2: Foundational (Blocking Schema and Migration)

**Purpose**: Establish the final relational model and safe upgrade path used by every story.

**CRITICAL**: Complete this phase before user-story production work.

### Tests first

- [ ] T004 Add failing clean-create and FS-007-to-FS-008 migration tests for normalized codes, eligibility backfill, scalar Course resource removal, unavailability constraints, and unchanged DraftSession assignments in `backend/tests/db/test_migrations.py`
- [ ] T005 [P] Add failing seed compatibility tests for editable deterministic resource codes, one initial eligible Lecturer and Room per Course, and idempotent reseeding in `backend/tests/scripts/test_seed_dummy_planning_data.py`
- [ ] T006 [P] Add the failing 100-Lecturer/100-Room/100-Course/1,000-period performance acceptance dataset and automated timing coverage in `backend/tests/performance/test_resource_catalog_performance.py`

### Shared implementation

- [ ] T007 Define revisioned Lecturer, Room, CourseEligibleLecturer, CourseEligibleRoom, ResourceUnavailabilityPeriod, and ResourceUnavailabilityWeekday models and relationships in `backend/app/models/planning.py`
- [ ] T008 Implement sequential migration 0004 with code backfill, eligibility backfill, unavailability tables/checks, scalar Course resource removal, and DraftSession preservation in `backend/app/db/migrations/0004_resource_eligibility_availability.py`
- [ ] T009 Update empty-database detection, sequential FS-007 upgrade, current-schema verification, and unknown-partial-schema diagnostics in `backend/app/db/schema.py`
- [ ] T010 Update seeded resources and Courses to use codes and authoritative eligibility sets without creating duplicates in `backend/scripts/seed_dummy_planning_data.py`
- [ ] T011 Run the failing-then-passing migration and seed tests and record schema invariants in `specs/008-resource-eligibility-availability/validation/foundation-results.md`

**Checkpoint**: Clean databases and upgraded FS-007 databases expose the FS-008 model while preserving every saved session assignment.

---

## Phase 3: User Story 1 - Maintain Scheduling Resources Safely (Priority: P1) MVP

**Goal**: Let a planner create, find, edit, retire, delete, and reactivate coded Lecturer and Room records with protected history and recoverable stale writes.

**Independent Test**: Create same-named resources with distinct codes, edit them, permanently delete an unprotected resource, retire a protected resource with active-Course/session details, reject a stale change, and reactivate a valid inactive resource without changing DraftSessions.

### Tests for User Story 1 (write and observe failing first)

- [ ] T012 [P] [US1] Add failing service tests for resource validation, normalized code uniqueness, duplicate display names, revisions, list filters/search, capacity impacts, retirement dispositions, cleanup, and reactivation in `backend/tests/services/test_resource_catalog.py`
- [ ] T013 [P] [US1] Add failing contract/API tests for Lecturer and Room list/detail/create/update/usage/DELETE/reactivate paths and structured 404/409/422 errors in `backend/tests/api/test_resource_catalog.py`
- [ ] T014 [P] [US1] Add failing typed client tests for active-default queries, name/code search, expected revisions, stale metadata, and deleted/inactivated/reactivated results in `client/src/api/resourceCatalog.test.ts`
- [ ] T015 [P] [US1] Add failing component tests for `Name · CODE`, Room capacity, inactive filtering, retained invalid input, keyboard/focus-managed removal outcomes, and confirmation cancel/close paths that issue no deletion request and leave resource state unchanged in `client/src/components/ResourceAdministration.test.tsx`
- [ ] T016 [P] [US1] Add failing page tests for Lecturer/Room navigation, active-default results, explicit inactive discovery, stale review, retirement messages, reactivation refresh, and refresh-failure warnings that retain the selected resource and last-known content without changing saved data in `client/src/pages/AcademicDataPage.test.tsx`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Define typed Lecturer/Room DTOs, mutation bodies, usage assessments, removal outcomes, reactivation results, and error envelopes in `backend/app/schemas/resource_catalog.py`
- [ ] T018 [US1] Implement resource validation, normalized code handling, pagination/search, revisioned create/edit, usage assessment, and Room capacity impact queries in `backend/app/services/resource_catalog.py`
- [ ] T019 [US1] Implement transactional delete-or-inactivate behavior, inactive-Course link cleanup, DraftSession preservation, and valid reactivation with relationship usability in `backend/app/services/resource_catalog.py`
- [ ] T020 [US1] Expose Lecturer/Room CRUD, usage, confirmed removal, and reactivation routes and register the router in `backend/app/api/resource_catalog.py` and `backend/app/main.py`
- [ ] T021 [P] [US1] Implement typed resource list/detail/mutation/usage/removal/reactivation requests and recoverable API errors in `client/src/api/resourceCatalog.ts`
- [ ] T022 [P] [US1] Implement coded active/inactive resource lists and controlled Lecturer/Room editors in `client/src/components/ResourceCatalogList.tsx` and `client/src/components/ResourceEditor.tsx`
- [ ] T023 [P] [US1] Implement a focus-managed outcome-driven dialog that shows active Courses, session usage, inactive-link cleanup, and the server disposition in `client/src/components/ResourceRemovalDialog.tsx`
- [ ] T024 [US1] Add Lecturer and Room categories, active/all/inactive filters, name/code search, detail loading, stale review, retirement, reactivation orchestration, and actionable refresh-failure warnings that retain the selected resource and last-known content in `client/src/pages/AcademicDataPage.tsx`
- [ ] T025 [US1] Add responsive resource administration, status, consequence, stale-review, and accessible feedback styles without a new UI dependency in `client/src/App.css`
- [ ] T026 [US1] Run all US1 tests and the quickstart duplicate-code and lifecycle scenarios, then record independent acceptance evidence in `specs/008-resource-eligibility-availability/validation/user-story-1-results.md`

**Checkpoint**: User Story 1 works independently as the MVP resource catalog and protected lifecycle workflow.

---

## Phase 4: User Story 2 - Record Resource Unavailability (Priority: P2)

**Goal**: Let a planner maintain recurring weekly and dated unavailable periods for each Lecturer and Room and interpret overlaps consistently.

**Independent Test**: Add recurring and dated rules, reject invalid and exact-duplicate rules, allow partial overlap, verify half-open boundaries, reject a stale edit, and observe new validation without moving an existing session.

### Tests for User Story 2 (write and observe failing first)

- [ ] T027 [P] [US2] Add failing pure-rule tests for recurring weekday expansion, dated multi-day intervals, union behavior, exact duplicates, and half-open overlap boundaries in `backend/tests/services/test_resource_rules.py`
- [ ] T028 [P] [US2] Add failing service/API tests for nested recurring/dated CRUD, kind-specific validation, owner integrity, revisions, duplicates, and deletion plus downstream validation and Draft Schedule API/schema response tests proving availability changes produce serializable `LECTURER_UNAVAILABLE` and `ROOM_UNAVAILABLE` alerts without moving or modifying existing DraftSessions in `backend/tests/services/test_resource_catalog.py`, `backend/tests/api/test_resource_catalog.py`, `backend/tests/services/test_draft_schedule_validation.py`, and `backend/tests/api/test_draft_schedule.py`
- [ ] T029 [P] [US2] Add failing client tests for discriminated recurring/dated payloads, canonical period responses, expected revisions, and field errors in `client/src/api/resourceCatalog.test.ts`
- [ ] T030 [P] [US2] Add failing component tests for weekday fieldsets, dated ranges, controlled-form retention, chronological display, duplicate feedback, and stale review in `client/src/components/ResourceAvailabilityEditor.test.tsx`

### Implementation for User Story 2

- [ ] T031 [US2] Implement canonical recurring/dated validation, duplicate signatures, weekday expansion, union lookup, and half-open overlap helpers in `backend/app/services/resource_rules.py`
- [ ] T032 [US2] Implement revisioned unavailability list/create/update/delete transactions and owner checks, resource-unavailability alerts and no-mutation validation behavior, and the `LECTURER_UNAVAILABLE` and `ROOM_UNAVAILABLE` `ValidationAlertCode` values in `backend/app/services/resource_catalog.py`, `backend/app/services/draft_schedule_validation.py`, and `backend/app/schemas/draft_schedule.py`
- [ ] T033 [US2] Add discriminated unavailability schemas and nested resource routes matching the OpenAPI contract in `backend/app/schemas/resource_catalog.py` and `backend/app/api/resource_catalog.py`
- [ ] T034 [P] [US2] Add typed unavailability methods and discriminated DTOs to `client/src/api/resourceCatalog.ts`
- [ ] T035 [US2] Implement recurring and dated controlled forms, canonical lists, delete confirmation, stale recovery, and announced outcomes in `client/src/components/ResourceAvailabilityEditor.tsx`
- [ ] T036 [US2] Integrate resource-owned unavailable periods into the selected Lecturer/Room detail workflow, announce availability refresh failures, and retain the selected resource and last-known content during refresh in `client/src/pages/AcademicDataPage.tsx`
- [ ] T037 [US2] Run all focused US2 tests and quickstart Scenarios 4 and 11, then record recurring, dated, overlap-boundary, duplicate-period, stale-write, validation, refresh-failure, and no-mutation evidence in `specs/008-resource-eligibility-availability/validation/user-story-2-results.md`

**Checkpoint**: User Story 2 can be tested against one maintained resource without Course eligibility or scheduling allocation.

---

## Phase 5: User Story 3 - Maintain Course Resource Eligibility (Priority: P3)

**Goal**: Let a planner atomically maintain multiple eligible Lecturers and Rooms per Course, understand capacity/usability, and apply clarified capacity cleanup.

**Independent Test**: Save two Lecturers and Rooms, reject invalid additions and final-resource removal, preserve a used assignment after relationship removal, verify Room-shrink versus Cohort-growth behavior, and recover from a stale aggregate update.

### Tests for User Story 3 (write and observe failing first)

- [ ] T038 [P] [US3] Add failing service tests for atomic set replacement, duplicate IDs, inactive additions, last-resource guards, computed usability, stale Course revisions, and preserved invalid relationships in `backend/tests/services/test_resource_catalog.py`
- [ ] T039 [P] [US3] Add failing API contract tests for GET/PUT Course resource eligibility, canonical candidates, fixed preference metadata, and all-or-nothing errors in `backend/tests/api/test_resource_catalog.py`
- [ ] T040 [P] [US3] Add failing Cohort-growth and Room-shrink tests for asymmetric relationship cleanup, Course revision increments, impact summaries, and unchanged DraftSessions plus DraftSession validation and API/schema response tests for planner-removed eligibility, cohort-growth cleanup, insufficient capacity, serializable separate and combined `LECTURER_INELIGIBLE`, `ROOM_INELIGIBLE`, and applicable `ROOM_CAPACITY` alerts, and unchanged assignments in `backend/tests/services/test_academic_catalog.py`, `backend/tests/api/test_academic_catalog.py`, `backend/tests/services/test_draft_schedule_validation.py`, and `backend/tests/api/test_draft_schedule.py`
- [ ] T041 [P] [US3] Add failing planning-readiness tests for no active eligible Lecturer, no usable eligible Room, coded candidate sets, and visible unavailable Courses in `backend/tests/api/test_planning_options.py`
- [ ] T042 [P] [US3] Add failing client API tests for atomic eligibility payloads, capacity/usability reasons, fixed preferences, stale revisions, and Cohort capacity effects in `client/src/api/resourceCatalog.test.ts` and `client/src/api/academicCatalog.test.ts`
- [ ] T043 [P] [US3] Add failing component tests for searchable coded checkbox groups, disabled invalid additions, visible preserved invalid relationships, final-resource feedback, and read-only preference guidance in `client/src/components/CourseResourceEligibilityEditor.test.tsx`
- [ ] T044 [P] [US3] Add failing Course administration page tests for eligibility save/cancel, cohort-size cleanup messaging, current configuration refresh, eligibility refresh-failure warnings that preserve the selected Course and current checkbox state, and input preservation in `client/src/pages/AcademicDataPage.test.tsx`

### Implementation for User Story 3

- [ ] T045 [US3] Implement CourseResourceConfiguration queries, computed candidate usability, atomic replacement, last-resource protection, Course revision changes, current Lecturer/Room eligibility validation with assignment-preservation behavior, and the `LECTURER_INELIGIBLE` and `ROOM_INELIGIBLE` `ValidationAlertCode` values in `backend/app/services/resource_catalog.py`, `backend/app/services/draft_schedule_validation.py`, and `backend/app/schemas/draft_schedule.py`
- [ ] T046 [US3] Add Course eligibility and candidate schemas plus GET/PUT routes under the existing academic Course boundary in `backend/app/schemas/resource_catalog.py` and `backend/app/api/resource_catalog.py`
- [ ] T047 [US3] Replace scalar Course resource handling with eligibility-set creation/editing and current readiness checks in `backend/app/services/academic_catalog.py` and `backend/app/schemas/academic_catalog.py`
- [ ] T048 [US3] Implement Cohort-growth automatic insufficient-Room removal, affected Course revision increments, capacity impact results, Room-shrink preservation, and validation-visible capacity/ineligibility outcomes in `backend/app/services/academic_catalog.py`, `backend/app/api/academic_catalog.py`, and `backend/app/services/draft_schedule_validation.py`
- [ ] T049 [US3] Return coded eligible sets, usability reasons, and no-resource readiness reasons from planning options in `backend/app/api/planning_options.py` and `backend/app/schemas/planning_options.py`
- [ ] T050 [P] [US3] Implement eligibility and Cohort-capacity typed requests/results in `client/src/api/resourceCatalog.ts`, `client/src/api/academicCatalog.ts`, and `client/src/api/planningOptions.ts`
- [ ] T051 [US3] Implement the atomic Course eligibility editor and integrate it with Course administration, capacity-impact feedback, actionable refresh-failure warnings, retained Course selection, retained eligibility checkbox state, and preserved unsaved input in `client/src/components/CourseResourceEligibilityEditor.tsx`, `client/src/components/AcademicRecordEditor.tsx`, and `client/src/pages/AcademicDataPage.tsx`
- [ ] T052 [US3] Run all focused US3 tests and quickstart Scenarios 5, 6, and 11, then record multiple-eligibility, capacity, last-resource, cohort-growth, stale-update, assignment-preservation, eligibility-alert, refresh-failure, and no-mutation evidence in `specs/008-resource-eligibility-availability/validation/user-story-3-results.md`

**Checkpoint**: User Story 3 provides complete planner-maintained choice sets without depending on generation optimization.

---

## Phase 6: User Story 4 - Supply Valid Resource Choices to Scheduling (Priority: P4)

**Goal**: Consume eligibility, availability, capacity, and fixed preferences in course-local generation, manual editing, planning options, and non-blocking validation while preserving the FS-010 boundary.

**Independent Test**: Generate a Course requiring resource changes, verify deterministic minimal switching and exactly one Lecturer/Room per session, validate every independent resource issue without mutation, edit assignments through existing session editing, and confirm multi-Course generation remains independent rather than globally optimized.

### Tests for User Story 4 (write and observe failing first)

- [ ] T053 [P] [US4] Add failing deterministic assignment tests for feasible candidate filtering, hard-rule precedence, minimum Lecturer/Room transitions, stable code/ID tie-breaks, and no cross-Course scoring in `backend/tests/services/test_resource_rules.py`
- [ ] T054 [P] [US4] Add failing single- and multi-Course generation tests for eligibility sets, availability, capacity, exactly-one assignments, partial resource feasibility, and preserved independent Course behavior in `backend/tests/services/test_schedule_generation.py` and `backend/tests/services/test_multi_course_generation.py`
- [ ] T055 [P] [US4] Add failing validation integration tests for simultaneous eligibility, availability, and capacity alerts, per-session coded identity, and no mutation in `backend/tests/services/test_draft_schedule_validation.py`
- [ ] T056 [P] [US4] Add failing DraftSession API tests for Lecturer plus Room edits, changed invalid assignments, unchanged legacy-invalid assignments, and refreshed parent schedules in `backend/tests/api/test_draft_schedule.py`
- [ ] T057 [P] [US4] Add failing planning and generation API regression tests for coded resource sets, fixed preferences, current readiness, and unchanged FS-001–FS-007 routes in `backend/tests/api/test_planning_options.py`, `backend/tests/api/test_multi_course_generation.py`, and `backend/tests/api/test_draft_schedule.py`
- [ ] T058 [P] [US4] Add failing client contract tests for per-session Lecturer/Room identity, new validation codes, eligible edit choices, and planning resource extensions in `client/src/api/draftSchedule.test.ts` and `client/src/api/planningOptions.test.ts`
- [ ] T059 [P] [US4] Add failing schedule component tests for multiple Lecturer/Room assignments, coded labels, eligible edit controls, simultaneous alerts, and unchanged session preservation in `client/src/components/DraftSchedulePanel.test.tsx`

### Implementation for User Story 4

- [ ] T060 [US4] Implement feasible candidate construction and deterministic dynamic programming that minimizes within-Course Lecturer and Room transitions in `backend/app/services/resource_rules.py`
- [ ] T061 [US4] Refactor temporal generation to require feasible active eligible available resources and emit exactly-one assignments without cross-Course optimization in `backend/app/services/schedule_generation.py`
- [ ] T062 [US4] Integrate authoritative eligibility and per-session resource context into independent batch generation and persistence in `backend/app/services/multi_course_generation.py` and `backend/app/services/draft_schedule_repository.py`
- [ ] T063 [US4] Compose the eligibility, availability, and capacity validation rules delivered by US2 and US3, preserve all simultaneous alerts, and add per-session resource names/codes in `backend/app/services/draft_schedule_validation.py`
- [ ] T064 [US4] Extend DraftSession schemas and PATCH behavior for Lecturer and Room assignment changes while preserving unchanged invalid assignments and established manual-alert behavior in `backend/app/schemas/draft_schedule.py`, `backend/app/api/draft_schedule.py`, and `backend/app/services/draft_schedule_repository.py`
- [ ] T065 [US4] Expose the complete coded resource configuration, fixed preference metadata, and per-session assignment context in `backend/app/schemas/planning_options.py`, `backend/app/api/planning_options.py`, and `backend/app/schemas/draft_schedule.py`
- [ ] T066 [P] [US4] Update typed planning and DraftSchedule clients for eligible sets, per-session resource codes, Lecturer editing, and new alert codes in `client/src/api/planningOptions.ts` and `client/src/api/draftSchedule.ts`
- [ ] T067 [US4] Update schedule summaries, filters, session rows, and edit controls to render and change exactly one eligible Lecturer and Room while preserving simultaneous alerts in `client/src/components/DraftSchedulePanel.tsx` and `client/src/components/scheduleReviewUtils.ts`
- [ ] T068 [US4] Run focused US4 generation/editing/validation tests and quickstart scenarios 7–8, then record the FS-010 boundary and independent acceptance evidence in `specs/008-resource-eligibility-availability/validation/user-story-4-results.md`

**Checkpoint**: All four user stories operate together, and resource choices are ready for later global optimization without implementing it.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Complete documentation, performance/usability evidence, full regression, and delivery checks across all stories.

- [ ] T069 [P] Update backend and client operating documentation for coded resources, eligibility, availability, lifecycle, routes, and no-global-optimization scope in `backend/README.md` and `client/README.md`
- [ ] T070 Execute the automated performance suite and quickstart performance protocol, then record raw SC-008/SC-009 measurements and environment details in `specs/008-resource-eligibility-availability/validation/performance-results.md`
- [ ] T071 Execute the 10-participant SC-001/SC-002/SC-004 usability protocol and record non-identifying results in `specs/008-resource-eligibility-availability/validation/usability-results.md`
- [ ] T072 Run the complete backend test suite and record command, duration, failures, and final passing result in `specs/008-resource-eligibility-availability/validation/backend-regression-results.md`
- [ ] T073 Run client tests, lint, and production build and record command, duration, failures, accessibility checks, and final passing results in `specs/008-resource-eligibility-availability/validation/client-regression-results.md`
- [ ] T074 Execute every applicable scenario in `specs/008-resource-eligibility-availability/quickstart.md`, compare implementation with `specs/008-resource-eligibility-availability/contracts/resource-eligibility-availability.openapi.yaml`, and record final scope/completion evidence in `specs/008-resource-eligibility-availability/validation/final-results.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: No dependencies; start immediately.
- **Phase 2 — Foundation**: Depends on Setup and blocks every user story.
- **Phase 3 — US1**: Depends on Foundation; establishes resource identities and lifecycle.
- **Phase 4 — US2**: Depends on US1 because unavailable periods belong to maintained resources.
- **Phase 5 — US3**: Depends on US1 because Course eligibility selects maintained resources; it can run in parallel with US2.
- **Phase 6 — US4**: Depends on both US2 and US3 because scheduling consumes availability and eligibility.
- **Phase 7 — Polish**: Depends on all desired user stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 ──┬──> US2 ──┐
                             └──> US3 ──┴──> US4 -> Polish
```

### Within Each User Story

1. Write the phase's tests and observe the intended failures.
2. Implement models/rules before services, services before routes, and routes before page integration.
3. Keep backend and client contract changes synchronized with the OpenAPI artifact.
4. Run the focused story tests and independent acceptance checkpoint before advancing.

### Parallel Opportunities

- Setup fixtures T002 and T003 can proceed in parallel after T001.
- Foundational migration tests T004, seed tests T005, and performance acceptance tests T006 touch different files.
- Each story's backend service/API tests and client API/component/page tests marked `[P]` can be authored concurrently.
- In US1, backend schemas/services/routes and client API/components can progress in parallel after tests exist.
- US2 and US3 may progress concurrently after US1, but both modify `backend/tests/services/test_draft_schedule_validation.py`, `backend/tests/api/test_draft_schedule.py`, `backend/app/services/draft_schedule_validation.py`, `backend/app/schemas/draft_schedule.py`, resource catalog services, and `client/src/pages/AcademicDataPage.tsx`; deliberately partition or serialize changes to these shared files before integration.
- Documentation T069 can proceed in parallel with final evidence preparation after the desired user stories are complete.

---

## Parallel Example: User Story 1

```text
Parallel test stream A: T012 then T013 — backend service and HTTP lifecycle tests
Parallel test stream B: T014 then T015 then T016 — client API, component, and page tests
Parallel implementation stream A: T017 then T018 then T019 then T020 — backend contract through routes
Parallel implementation stream B: T021 then T022/T023 then T024/T025 — typed client through page integration
```

## Parallel Example: User Story 2

```text
Parallel test stream A: T027/T028 — overlap rules and availability transactions
Parallel test stream B: T029/T030 — client contract and controlled-form behavior
Parallel implementation stream A: T031 then T032/T033 — rules through HTTP
Parallel implementation stream B: T034 then T035/T036 — client API through resource detail
Focused acceptance evidence: T037
```

## Parallel Example: User Story 3

```text
Parallel backend tests: T038/T039/T040/T041
Parallel client tests: T042/T043/T044
Backend implementation: T045/T046 then T047/T048/T049
Client implementation: T050 then T051
Focused acceptance evidence: T052
```

## Parallel Example: User Story 4

```text
Parallel backend tests: T053/T054/T055/T056/T057
Parallel client tests: T058/T059
Backend implementation: T060 then T061/T062/T063/T064/T065
Client implementation: T066 then T067
```

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete Setup and Foundation.
2. Complete US1 tests before US1 production code.
3. Deliver coded Lecturer/Room administration, protected retirement/deletion, and reactivation.
4. Stop and validate `validation/user-story-1-results.md` before expanding scope.

### Incremental Delivery

1. **MVP**: Setup + Foundation + US1.
2. **Availability increment**: US2 adds resource-owned recurring/dated unavailability.
3. **Eligibility increment**: US3 adds atomic Course choice sets and capacity cleanup; may be developed beside US2.
4. **Scheduling integration**: US4 consumes both inputs course-locally and preserves the FS-010 boundary.
5. **Release evidence**: Polish phase completes performance, usability, full regression, and contract/quickstart verification.

### Parallel Team Strategy

After Foundation and US1:

- Developer A can implement US2 availability.
- Developer B can implement US3 eligibility and capacity effects.
- Developer C can prepare US4 failing allocator/validation/client tests without implementing against incomplete inputs.
- Merge and verify shared validation tests, Draft Schedule schemas/services, resource catalog services, and Academic Data page changes deliberately before US4 integration; do not run overlapping edits to the same shared file without coordination.

## Notes

- `[P]` means different primary files and no dependency on unfinished work at that point.
- Every task includes an exact repository-relative path and a traceable story label where required.
- Keep DraftSession Lecturer/Room assignments unchanged during migration and source-data changes.
- Do not add preference switches, ranks, quotas, positive availability overrides, cross-Course solving, or any other FS-010 behavior.
- Update the specification and plan before production code if implementation reveals a changed requirement.
- Commit after each task or cohesive test-first group and run the relevant focused tests before the checkpoint.
