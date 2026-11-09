# Tasks: Dated Windows, Copying and Intensive-Week Scheduling

**Input**: `specs/I-009-dated-intensive-windows/` spec, plan, research, data-model, contracts/interfaces and quickstart.
**Slice**: I-009. **Tests**: explicitly requested by TR-001–009 and constitution; write/run failing tests before their production tasks. This is a future execution list; Goal 2 does not execute it.
**Organization**: story phases in spec order, P1 before P2. No task is complete merely because artifacts exist.

## Format and paths

`- [ ] Tnnn [P?] [USn?] action with exact path`. Paths are repository-relative, `backend/app/`, `backend/tests/`, `client/`; [P] permits only indicated independent tasks within an already-ready test batch. Existing modules are extended; named new test/migration/evidence files are intentionally new. Run backend commands from backend and frontend commands from client. No delivery Git operations are authorized.

## Phase 1: Setup

- [X] T001 After explicit plan/task approval and human-started Goal 3, record baseline/status and existing user changes in `specs/I-009-dated-intensive-windows/validation.md`, create dedicated `codex/021-dated-intensive-windows` branch from the recovered tree without discarding changes, and bind the execution to the approved spec/plan/tasks; no commit/push/merge (constitution V, TR-001/009).
- [X] T002 Verify existing Python 3.12/Node 24 environments and locked dependencies from `backend/requirements.txt` and `client/package-lock.json`; record exact commands/versions and unavailable checks in `specs/I-009-dated-intensive-windows/validation.md`, without upgrading dependencies (TR-008).
- [X] T003 Prepare disposable weekly/dated/course/fixed-teaching/exam test fixtures in new `backend/tests/fixtures/dated_intensive_windows.py`, covering two forms, known instructional intervals and independent small alternatives; never use the live planner DB (TR-002–006/009).

## Phase 2: Foundational

**Purpose**: Freeze cross-stack expectations and fixture semantics; no generic infrastructure work.

- [X] T004 Add shared wire fixture cases to new `backend/tests/fixtures/dated_intensive_contracts.json` and `client/src/test/datedIntensiveContracts.json` from `specs/I-009-dated-intensive-windows/contracts/interfaces.md` for weekly compatibility, dated/null-weekday, German errors, rational intensive facts and proof directions; record a test assertion that both fixture sets agree in new `backend/tests/api/test_dated_intensive_windows.py` before production changes (TR-008).

**Checkpoint**: fixtures/expected contracts ready. Story tests must still fail for the intended missing behavior, not import/fixture errors.

## Phase 3: US1 — Open One Specific Teaching Date (P1, first useful increment)

**Goal**: Maintain dated windows and generate/validate exact-date teaching safely alongside unchanged weekly records.
**Independent test**: Add one Monday to Fri/Sat form, reload/edit/delete, generate only on that exact additional date/form; preserve weekly IDs and saved work. Dated-only courses are selectable. Include initial freshness/current-warning protection before exposing new records.

### Tests first

- [X] T005 [P] [US1] Write failing predecessor/fresh migration tests in `backend/tests/db/test_migrations.py` for preserved IDs/revisions/owners/activity/order and incoming FK/saved/historical references, equivalent checks/partial unique indexes, inactive duplicates, rollback and partial-schema rejection (FR-003/005/011/012, TR-002).
- [X] T006 [P] [US1] Write failing catalog/service and HTTP contract tests in `backend/tests/services/test_academic_catalog.py`, `backend/tests/api/test_academic_catalog.py` and `backend/tests/api/test_dated_intensive_windows.py` for kind/date/marker, all fields, aggregate German parsing/field errors, active form changes, duplicates/races, overlap vs adjacency, usage/protected deletion, archive/reactivation/stale writes and legacy weekly input; use T004 fixtures (FR-001–007/011/012, TR-002/008).
- [X] T007 [P] [US1] Write failing shared permission/availability/preparation tests in new `backend/tests/services/test_dated_intensive_windows.py` and existing `backend/tests/services/test_draft_schedule_validation.py`, `backend/tests/services/test_semester_optimization.py`, `backend/tests/services/test_calendar_workspace.py`, `backend/tests/services/test_schedule_lifecycle.py`, `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_calendar_workspace.py` and `backend/tests/api/test_schedule_lifecycle.py` for exact date/year/form, six independent days/Sunday/out-of-period, dated-only minimum occurrence, no stitching, narrower constraints, all inherited hard rules, manual severity, marker/date/form/activity freshness and zero session mutation. Assert dated generation before the US1 checkpoint, mixed-kind stable ordering and retained-session validation; cover direct constraint response, Calendar profile serialization/reconstruction, lifecycle loading/new snapshot capture with kind/date/marker, old captured-weekly fallback and unchanged historical bytes. Also write failing mixed weekly/dated and dated-only exam proposal/availability regressions in `backend/tests/services/test_exam_scheduling.py`, `backend/tests/services/test_exam_optimization.py` and `backend/tests/api/test_exam_scheduling.py`: dated rows never become weekly exam proposals, cannot cause None/int sorting and do not satisfy weekly-start eligibility (FR-002/003/013–016/025/027/031, TR-005/006/009).
- [X] T008 [P] [US1] Write failing date/marker/list/client contract/editor tests in `client/src/api/academicCatalog.test.ts`, `client/src/api/planningOptions.test.ts`, `client/src/components/AcademicRecordEditor.test.tsx`, `client/src/components/DraftSchedulePanel.test.tsx` and `client/src/pages/AcademicDataPage.test.tsx` for discriminated types, German full-date entry, default-off marker, ordering, retained error input and minimum keyboard labels/focus; derived-window display distinguishes weekly from full-date dated records/marker and safely renders legacy captured weekly values without nullable-weekday indexing (FR-001/003/004/006/007/013/030, TR-007/008).

### Production after intended failures

- [X] T009 [US1] Extend model, migration and sequential initializer in `backend/app/models/planning.py`, new `backend/app/db/migrations/0013_dated_teaching_windows.py` and `backend/app/db/schema.py` with D1–D10 verbatim constraints: “`id` remains the existing primary key; edits and migration preserve identity.” “`study_type_id` is exactly one required existing active form on create/edit/reactivate.” “`kind` is required, either `weekly` or `dated`, and immutable on edit/copy.” “`weekday` is an integer 0–6 for weekly and null for dated.” “`date` is a full valid calendar date including year for dated and null for weekly.” “`start_time` and `end_time` are required same-day times; end_time is later than start_time; midnight spanning is rejected.” “`is_intensive` is Boolean, false for weekly, defaults false for new dated records and is editable only for dated records.” “`sort_order` retains its existing integer value on migration/copy.” “`is_active` retains existing Boolean lifecycle behavior; inactive entries participate in duplicate identity.” “`revision` is a positive optimistic integer; mutation requires matching expectedRevision and increments revision.” Enforce kind-specific uniqueness independent of marker/activity, preserve FK/history and initialize new/predecessor schemas equivalently; service-only constraints remain in T010 (FR-001–005/007/012).
- [X] T010 [US1] Extend schema/service/routes in `backend/app/schemas/academic_catalog.py`, `backend/app/services/academic_catalog.py` and `backend/app/api/academic_catalog.py` for T009 field validation, owner-changing edit/kind lock, legacy weekly requests, aggregate German 422 field envelopes, race-safe duplicate/stale 409 rollback, overlapNotice, usage/count blockers, archive/reactivation and no cascades into sessions; preserve current authentication/CSRF (FR-001–007/011/012/016).
- [X] T011 [US1] Extend `backend/app/services/schedule_generation.py` normalized opportunities/shared applicability and `backend/app/services/draft_schedule_repository.py` loading for exact-date/weekday/form/active matching, single full-interval containment and narrow restrictions; update usable occurrence availability in `backend/app/services/academic_catalog.py` and `backend/app/services/conflict_aware_generation.py` without weekly fallback or changed hard rules. Explicitly update `backend/app/services/semester_optimization.py` candidate applicability/date filtering, mixed-kind stable sorting and retained-session containment now so dated generation works before T015; retain existing unmarked preference/tie order. Intensive candidate-boundary/scoring work stays in US2 T020/T021 (FR-002/013–015).
- [X] T012 [US1] Propagate kind/date/marker through `backend/app/api/planning_options.py`, `backend/app/schemas/planning_options.py`, `backend/app/schemas/draft_schedule.py`, `backend/app/schemas/conflict_aware_generation.py`, `backend/app/services/conflict_aware_generation.py`, `client/src/api/academicCatalog.ts`, `client/src/api/planningOptions.ts`, `client/src/api/draftSchedule.ts` and `client/src/api/conflictAwareGeneration.ts`; handle nullable weekday explicitly. Update direct producers/loaders in `backend/app/api/draft_schedule.py`, `backend/app/services/calendar_workspace.py` and `backend/app/services/schedule_lifecycle.py`: propagate kind/date/marker through constraints, current Calendar profiles/reconstruction, lifecycle current-window loading and new snapshot captures; default missing discriminator/date/marker only in old captured-weekly values without rewriting existing captures. Current Calendar/List/detail validation must receive full dated facts (FR-003/013/023/027, TR-008).
- [X] T013 [US1] Integrate shared permission in `backend/app/services/draft_schedule_validation.py` and initial date/marker/form/activity/revision fingerprints plus exact-candidate revalidation in `backend/app/services/conflict_aware_generation.py`; maintain manual warning severity, non-mutating window maintenance and immutable historical evidence. In `backend/app/services/exam_scheduling.py`, restrict automatic start proposals and active-start eligibility to active weekly windows; dated-only forms retain existing no-weekly-start unavailability and mixed rows cannot reach weekday sorting as null. Do not change manual exam behavior or add dated exam policy (FR-013–016/025/027/031).
- [X] T014 [US1] Extend `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/AcademicCatalogList.tsx` and `client/src/pages/AcademicDataPage.tsx` with kind selection/locked edit, required active form/date/hours, dated default-off marker, German date/errors/overlap, explicit weekly/dated groups in specified order and basic labelled keyboard/focus behavior; trigger immediate catalog invalidation on acknowledged mutations before reload. Extend read-only derived-window display in `client/src/components/DraftSchedulePanel.tsx` with weekly/dated labels, full German date/marker, safe nullable-weekday handling and captured-weekly fallback (FR-001/003/004/006/007/013/023/030).
- [X] T015 [US1] Verify `.venv/Scripts/python.exe -m pytest tests/db/test_migrations.py tests/services/test_academic_catalog.py tests/services/test_dated_intensive_windows.py tests/services/test_draft_schedule_validation.py tests/api/test_academic_catalog.py tests/api/test_dated_intensive_windows.py tests/services/test_semester_optimization.py tests/services/test_calendar_workspace.py tests/services/test_schedule_lifecycle.py tests/api/test_draft_schedule.py tests/api/test_calendar_workspace.py tests/api/test_schedule_lifecycle.py tests/services/test_exam_scheduling.py tests/services/test_exam_optimization.py tests/api/test_exam_scheduling.py` and `npm test -- src/components/DraftSchedulePanel.test.tsx src/api/academicCatalog.test.ts src/api/planningOptions.test.ts src/components/AcademicRecordEditor.test.tsx src/pages/AcademicDataPage.test.tsx`; record US1 outcomes in `specs/I-009-dated-intensive-windows/validation.md` (SC-001/006, TR-001/002/005/008).

## Phase 4: US2 — Use Intensive Opportunities (P1)

**Goal**: Optimize total LE, exact intensive LE and same-cohort daily variety, preserving all hard rules and lower preference order.
**Independent test**: Known feasible alternatives prove priorities, exact boundaries, fixed teaching contribution, single-LV fallback, multi-day LV and unchanged no-marker output. Test synchronous core and installed worker paths.

### Tests first

- [X] T016 [P] [US2] Write independent exhaustive small-alternative oracle tests in new `backend/tests/services/test_intensive_objectives.py` and extend `backend/tests/services/test_semester_optimization.py` for both sacrifice prohibitions, same/different cohorts, fixed teaching/exams, cross-date ties, single-LV/multi-day cases, no-marker stable output and tight packing/interior marker-aligned/positive-overlap start completeness; exact accounting includes 90 minutes=2 LE once and 30 minutes=2/3 LE excluding breaks/source identity (FR-017–022, SC-003–005, TR-003/004).
- [X] T017 [P] [US2] Write failing facts/proof/worker/acceptance tests in `backend/tests/api/test_dated_intensive_windows.py`, `backend/tests/services/test_conflict_aware_generation.py`, `backend/tests/services/test_optimization_worker.py` and `backend/tests/services/test_optimization_operations.py` for max directions, staged conditional/unattempted proof, integer ticks, current/generated association, detached picklability, deadline/cancellation and exact apply reproduction (FR-025/026/028/029, TR-006/008/009).
- [X] T018 [P] [US2] Write failing shared facts/proof/component tests in `client/src/api/conflictAwareGeneration.test.ts`, `client/src/components/BatchResultSummary.test.tsx`, new `client/src/components/OptimizationProofFacts.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx` for exact rational values, per-cohort counts, separately identified current/generated sides, correct German priority and truthful proof statuses/LE conversion (FR-028/029, TR-007/008).

### Production

- [X] T019 [US2] Add exact marked-union/instructional intersection helpers to `backend/app/services/schedule_generation.py`; extend detached `OptimizationCourse`/fixed teaching values in `backend/app/services/semester_optimization.py` and loading in `backend/app/services/conflict_aware_generation.py` with each fixed course's units/form/marked context; exclude exams from variety and fixed coverage from selected totals (FR-018–020).
- [X] T020 [US2] Extend candidate-start event closure and generation in `backend/app/services/semester_optimization.py` with marker/instruction/break boundary alignments and positive-overlap representatives at inherited microsecond precision, including packing closure, while preserving legacy seeds/ranks when unmarked; use oracle evidence to prove no intensive/variety optimum is omitted (FR-014/017–022).
- [X] T021 [US2] Implement sequential intensive_teaching_time/max then daily_variety/max after total_units in `backend/app/services/semester_optimization.py`, with exact bounded integer coefficients, unique LV/cohort/date presence, max(0,K−1), fixed constants, earlier-stage equality locks and unchanged remaining objective/sub-order/tiebreak; preserve hard rules, one LV session/date and installed timeout/conditional behavior (FR-015/017–022/029).
- [X] T022 [US2] Extend objective keys/direction/condition validation and result/comparison serializers in `backend/app/schemas/conflict_aware_generation.py` and `backend/app/services/conflict_aware_generation.py` with exact intensiveFacts and scope identity for each actual arrangement; include fixed context in fingerprints and do not infer preference proof from coverage (FR-025/028/029).
- [X] T023 [US2] Propagate detached facts/checkpoints/progress/proof and independent exact validation through `backend/app/services/optimization_worker.py` and `backend/app/services/optimization_operations.py`; preserve one deadline, no worker ORM/writes, explicit existing acceptance, atomic at-most-once application and no new I-006 dependency (FR-026/029/031).
- [X] T024 [US2] Extend shared facts/proof types and installed operation handling in `client/src/api/conflictAwareGeneration.ts`, `client/src/hooks/useOptimizationOperation.ts` and `client/src/test/optimizationFixtures.ts`; consume matching scopes and add no acceptance bypass or dependence on I-007/I-008 (FR-026/028/029).
- [X] T025 [US2] Show actual saved/provisional and current/generated intensive facts separately in `client/src/components/BatchResultSummary.tsx`, `client/src/components/OptimizationProofFacts.tsx` and `client/src/pages/CourseSchedulePage.tsx`; convert exact ticks to LE and explain German priority/single-LV validity/no placement guarantee while retaining legacy no-marker flow (FR-028/029).
- [X] T026 [US2] Run `.venv/Scripts/python.exe -m pytest tests/services/test_intensive_objectives.py tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py tests/services/test_optimization_worker.py tests/services/test_optimization_operations.py tests/api/test_dated_intensive_windows.py` and `npm test -- src/api/conflictAwareGeneration.test.ts src/components/BatchResultSummary.test.tsx src/components/OptimizationProofFacts.test.tsx src/pages/CourseSchedulePage.test.tsx`; rerun US1 checks and record independent-oracle/results evidence in `specs/I-009-dated-intensive-windows/validation.md` (SC-003–005, TR-001/003/004/008/009).

## Phase 5: US3 — Consistent Alerts and Saved Work (P1)

**Goal**: Refresh current context safely after every window mutation and preserve I-004 operations/history.
**Independent test**: Saved Monday alert appears/disappears without session change, marker edit stales candidate only, failure labels non-current, stale/cancelled/repeated/interrupted acceptance preserves atomic state.

### Tests first

- [X] T027 [P] [US3] Extend backend freshness/hard-rule/lifecycle/atomicity matrices in `backend/tests/services/test_dated_intensive_windows.py`, `backend/tests/services/test_conflict_aware_generation_concurrency.py`, `backend/tests/services/test_optimization_operations.py` and `backend/tests/services/test_schedule_lifecycle.py`, `backend/tests/services/test_calendar_workspace.py`, `backend/tests/api/test_calendar_workspace.py` and `backend/tests/api/test_schedule_lifecycle.py` for every relevant window/fixed-context change, direct save/submit/final acceptance, manual severity, active exams, published/history immutability and reject/cancel/failure/retry/interruption preservation (FR-015/016/023–027, TR-005/006/009).
- [X] T028 [P] [US3] Write failing refresh integration tests in `client/src/App.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx` for acknowledgement before failed list reload, options/Calendar/List/detail failure/retry, revisited views, marker-only invalidation, out-of-order responses, filters/selections/editor preservation and obsolete comparison prevention (FR-023–025, TR-006).

### Production

- [X] T029 [US3] Complete snapshot/fixed-context/date/marker freshness and atomic apply/lifecycle integration in `backend/app/services/conflict_aware_generation.py`, `backend/app/services/optimization_operations.py`, `backend/app/services/draft_schedule_repository.py` and `backend/app/services/draft_schedule_validation.py`, `backend/app/services/calendar_workspace.py` and `backend/app/services/schedule_lifecycle.py` against T027; preserve window-change non-mutation, manual warnings and captured historical evidence (FR-023–027).
- [X] T030 [US3] Complete acknowledged-mutation invalidation for create/edit/delete/archive/reactivate, even if catalog reload fails, in `client/src/pages/AcademicDataPage.tsx` and `client/src/App.tsx`; retain input/filter state and report save success separately from refresh failure (FR-023/024).
- [X] T031 [US3] Complete catalog-revision-bound current options/derived windows/Calendar/List/detail refresh, obsolete preview clearing, out-of-order response guards and unavailable/retry UI in `client/src/pages/CourseSchedulePage.tsx` and `client/src/hooks/useOptimizationOperation.ts`; keep historical renderers captured and preserve unrelated state (FR-023–027).
- [X] T032 [US3] Run `.venv/Scripts/python.exe -m pytest tests/services/test_dated_intensive_windows.py tests/services/test_conflict_aware_generation_concurrency.py tests/services/test_optimization_operations.py tests/services/test_schedule_lifecycle.py tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py tests/api/test_schedule_lifecycle.py` and `npm test -- src/App.test.tsx src/pages/AcademicDataPage.test.tsx src/pages/CourseSchedulePage.test.tsx src/hooks/useOptimizationOperation.test.tsx`; rerun prior-story checks and record session/history fingerprints and atomicity outcomes in `specs/I-009-dated-intensive-windows/validation.md` (SC-006–008, TR-001/006/009).

## Phase 6: US4 — Independent Copies (P2)

**Goal**: Prefill an unsaved copy and explicitly create one independent record.
**Independent test**: Copy weekly/marked dated records, cancel/save, change/delete source while editor open and edit/delete peers independently. Zero writes on open/cancel; one record on success.

- [X] T033 [P] [US4] Write failing API/service independence tests in `backend/tests/api/test_dated_intensive_windows.py` and `backend/tests/services/test_academic_catalog.py` for ordinary create from copied values, marker-only duplicate, source changed/deleted, target archived, concurrent creates and zero cascading/planning effects; no copy endpoint or ancestry relation (FR-008–012/016, TR-002).
- [X] T034 [P] [US4] Write failing copy/prefill/cancel/focus/double-submit/error-retention tests in `client/src/components/AcademicRecordEditor.test.tsx`, `client/src/components/AcademicCatalogList.test.tsx` and `client/src/pages/AcademicDataPage.test.tsx` for weekly and marked dated values, changed source and independent saved edits/deletes (FR-008–010/030, TR-002/007).
- [X] T035 [US4] Add creation/edit/copy mode and one-time captured values in `client/src/components/AcademicRecordEditor.tsx`: retain kind, prefill form/date-or-weekday/hours/marker/sortOrder, focus form on copy, preserve input on invalid save, disable repeat in-flight submit and return focus on cancel/dismiss (FR-008–010/030).
- [X] T036 [US4] Add Kopieren actions/unsaved presentation/ordinary POST integration in `client/src/components/AcademicCatalogList.tsx` and `client/src/pages/AcademicDataPage.tsx`; strip source ID/revision/link, create exactly one independent record, snapshot values against later source changes, retain current duplicate/form validation and non-mutating cancel (FR-008–010/016).
- [X] T037 [US4] Run `.venv/Scripts/python.exe -m pytest tests/api/test_dated_intensive_windows.py tests/services/test_academic_catalog.py` and `npm test -- src/components/AcademicRecordEditor.test.tsx src/components/AcademicCatalogList.test.tsx src/pages/AcademicDataPage.test.tsx`; record source/copy/session identity preservation and rerun prior-story suites in `specs/I-009-dated-intensive-windows/validation.md` (SC-002, TR-001/002/007).

## Phase 7: US5 — Understand and Operate Accessibly (P2)

**Goal**: Complete German, keyboard/AT and responsive presentation across administration/results.
**Independent test**: All required flows work by keyboard, full dates/marker/errors/counts are readable at 320 CSS px/200%, and timed unaided reviewer exercise meets SC-009.

- [X] T038 [US5] Write failing ordering/first-invalid focus/return/containment/announcements/label/proof-association tests in `client/src/components/AcademicRecordEditor.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx`, `client/src/components/OptimizationProofFacts.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx`; assert all detected German errors and non-color-only facts while retaining existing flows (FR-004/006/028–030, TR-007).
- [X] T039 [US5] Complete default-focus/first-invalid/return/containment, associated errors, keyboard actions and announcements in `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/AcademicCatalogList.tsx` and `client/src/pages/AcademicDataPage.tsx`; preserve explicit ordered groups and full date/marker/form display (FR-004/006/030).
- [X] T040 [US5] Complete German result facts/priority/fallback and correct proof status/condition/direction presentation in `client/src/components/BatchResultSummary.tsx`, `client/src/components/OptimizationProofFacts.tsx` and `client/src/pages/CourseSchedulePage.tsx`, exposing per-cohort/date counts for actual current/generated sides and no false optimality (FR-028–030).
- [X] T041 [US5] Adjust `client/src/App.css` for readable/reachable dates/marker/errors/controls/result facts at 320 CSS px and 200% text enlargement with visible focus and non-color-only states, preserving existing responsive tables/modals (FR-030).
- [ ] T042 [US5] Run `npm test -- src/components/AcademicRecordEditor.test.tsx src/pages/AcademicDataPage.test.tsx src/components/OptimizationProofFacts.test.tsx src/pages/CourseSchedulePage.test.tsx`; execute real-browser keyboard/AT/320px/200% and five-reviewer unaided acceptance in `specs/I-009-dated-intensive-windows/quickstart.md`, recording versions, all times/explanations and failures in `specs/I-009-dated-intensive-windows/validation.md`; at least 4/5 finish within five minutes and all five explain total LE priority/single-LV validity (SC-009/010, TR-007).

## Phase 8: Polish and Cross-Cutting Verification

- [X] T043 Verify shared backend/client wire fixture equality and contracts with `.venv/Scripts/python.exe -m pytest tests/api/test_dated_intensive_windows.py tests/api/test_academic_catalog.py tests/api/test_conflict_aware_generation.py tests/api/test_optimization_operations.py` and `npm test -- src/api/academicCatalog.test.ts src/api/planningOptions.test.ts src/api/conflictAwareGeneration.test.ts`; record results in `specs/I-009-dated-intensive-windows/validation.md` (TR-008).
- [ ] T044 Run `.venv/Scripts/python.exe -m pytest tests` from backend and record complete regressions, migration and manual/exam/lifecycle protections in `specs/I-009-dated-intensive-windows/validation.md` (TR-005/006/008/009).
- [X] T045 Run `npm test`, `npx tsc -b`, `npm run build`, `npm run lint` from client; record each outcome and any unavailable verification in `specs/I-009-dated-intensive-windows/validation.md` (TR-008).
- [X] T046 Run `.venv/Scripts/python.exe -m pytest tests/performance/test_semester_optimization_performance.py tests/performance/test_academic_catalog_performance.py`; execute SC-008's real-browser twenty sequential changes on 100 windows/20 courses/100 sessions per `specs/I-009-dated-intensive-windows/quickstart.md`, recording each save-ack-to-current-view latency, environment, maximum, refresh failures/retries and unchanged session fingerprints in `specs/I-009-dated-intensive-windows/validation.md`; every affected mounted view must refresh within two seconds (SC-008, TR-009).
- [X] T047 Run `.venv/Scripts/python.exe -m pytest tests/services/test_optimization_worker.py tests/services/test_optimization_operations.py tests/services/test_conflict_aware_generation.py tests/services/test_semester_optimization.py tests/services/test_schedule_lifecycle.py` against core synchronous I-003/I-004 invocation without operation-service requirement and installed worker/proof invocation; use fixtures/configuration in those files, never remove installed production features, and record unchanged acceptance/proof/deadline/no-marker boundaries and no I-007/I-008 dependency in `specs/I-009-dated-intensive-windows/validation.md` (FR-026/029/031, TR-009).
- [ ] T048 Review current diff/scope and acceptance traceability, reconcile actual commands/environment limitations in `specs/I-009-dated-intensive-windows/quickstart.md` and `specs/I-009-dated-intensive-windows/validation.md`; retain FR-031 exclusions, report missing manual evidence, preserve reviewer checklist ownership and stop for the process's independent implementation-convergence/human handover gates without commit/push/merge (TR-001–009).

## Dependencies and Execution Order

Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → US5 → Phase 8. This deliberate serial story order avoids edits to shared modules colliding. US1 includes minimum current-validation/freshness safety; later US3 is not permission to ship unsafe US1. Within each phase, tests must be authored/run and show intended failure before production tasks, then production follows listed order and story verification closes the increment. Preserve all previously verified behavior.

T005–T008, T016–T018, T027–T028 and T033–T034 may execute concurrently within their own ready test batch because their file sets are disjoint. T004 precedes contract consumers. All production edits are serialized; different story phases are not concurrent. US1 T007/T008 include the newly affected solver, exam, Calendar/lifecycle and derived-panel tests; these must show intended failure before T011–T014. T009 → T010 → T011 → T012 → T013 → T014; T019 → T020 → T021 → T022 → T023 → T024 → T025. Final verification follows final changes; rerun affected checks if those changes invalidate earlier evidence.

## Parallel Examples by Story

| Story | Ready independent test work |
| --- | --- |
| US1 | T005 migration tests alongside T006 catalog, T007 permission and T008 client tests |
| US2 | T016 oracle alongside T017 backend proof/worker and T018 client facts tests |
| US3 | T027 backend protection alongside T028 client refresh tests |
| US4 | T033 backend copy independence alongside T034 client copy tests |
| US5 | No concurrent edits: T038 spans shared UI tests; execute T039–T042 serially |

## Requirement Traceability

| Requirement | Principal tasks |
| --- | --- |
| FR-001 | T005/006/008–014 |
| FR-002 | T007/011/015 |
| FR-003 | T005/009/012 |
| FR-004 | T006/008/010/014/038/039 |
| FR-005 | T005/006/009/010 |
| FR-006 | T008/014/038/039 |
| FR-007 | T006/008/009/014 |
| FR-008–010 | T033–037 |
| FR-011–012 | T005/006/009/010/033 |
| FR-013–014 | T007/011–013/020 |
| FR-015–016 | T007/010/013/027/029/033/036 |
| FR-017–022 | T016/019–021/026 |
| FR-023–024 | T014/027–032/046 |
| FR-025 | T007/013/017/022/027–032 |
| FR-026–027 | T013/017/023/024/027/029/032/047 |
| FR-028–029 | T017/018/022–026/038/040/047 |
| FR-030 | T008/014/034/035/038–042 |
| FR-031 | T001/023/047/048 |
| SC-001 | T007/015 |
| SC-002 | T033–037 |
| SC-003–005 | T016–026 |
| SC-006–007 | T007/015/027–032/044 |
| SC-008 | T028/030–032/046 |
| SC-009–010 | T038–042 |
| TR-001–009 | Test-first phases; T001–004/015/026/032/037/042–048 |

## Implementation Strategy

First useful increment is US1: dated administration and exact-date permission with its safety gates. It is a demonstration checkpoint, not completion of I-009. Then verify US2 intensive optimization, US3 full current-context protection and P2 US4/US5. All five stories and cross-cutting evidence are needed for full-slice completion. Manual-only exceptions in plan require real browser/AT/user evidence; absent evidence is not a pass. No task adds an unrelated dependency/service or changes approved scope. Stop for human direction when a requirement/architecture change is needed. Goal 2 ends at plan/task approval, before executing any checkbox.

## Phase 9: Convergence

- [X] T049 Correct duplicate-window feedback in `client/src/components/AcademicRecordEditor.tsx` with failing regression tests in `client/src/components/AcademicRecordEditor.test.tsx` and `client/src/pages/AcademicDataPage.test.tsx`: distinguish `DUPLICATE_TIME_WINDOW` from stale-revision responses, explain the existing same-form/kind/date-or-weekday/hours conflict in German (including inactive/marker-only duplicates), retain unsaved create/edit/copy values and permit correction or cancellation without another write; preserve genuine stale-refresh guidance per FR-005, US4/AC4, T034-T036 (partial).
- [X] T050 Complete the independent exhaustive intensive-objective oracle matrix in `backend/tests/services/test_intensive_objectives.py` and `backend/tests/services/test_semester_optimization.py`: compare actual feasible shared-resource/cohort tightly packed alternatives with interior marked boundaries and discrete positive-overlap representatives, prove variety cannot sacrifice intensive coverage at equal total coverage, and verify equal-score cross-date arrangements use established lower preferences/stable ties without an added intensive-date distribution preference; do not derive oracle alternatives or scores from production candidate/scoring helpers, and correct any exposed in-scope implementation gap before recording results in `specs/I-009-dated-intensive-windows/validation.md` per FR-017-FR-022, SC-003-SC-005, TR-003, T016/T020 (missing).
- [X] T051 Complete dated/fixed-teaching freshness acceptance regressions in `backend/tests/services/test_conflict_aware_generation.py`, `backend/tests/services/test_optimization_operations.py` and the applicable concurrency tests: after candidate creation, change date, hours, form, activity and marker (including preference-only changes that leave teaching valid), and change the applicable marked context of fixed unselected teaching; verify synchronous explicit acceptance and installed operation finalization reject stale evidence, preserve all prior selected/unselected/manual/exam facts and write no partial result or saved receipt. Cover prepared submission and candidate acceptance boundaries separately, retain existing cancellation/retry/atomicity checks and record evidence in `specs/I-009-dated-intensive-windows/validation.md` per FR-025-FR-027, TR-006, T017/T027 (missing).
- [ ] T052 Complete the remaining real accessibility acceptance in `specs/I-009-dated-intensive-windows/quickstart.md` and record actual browser/assistive-technology versions, observations and failures in `specs/I-009-dated-intensive-windows/validation.md`: cover required create/copy/edit/cancel flows and focus/error/outcome announcements with actual AT, and inspect administration plus affected saved/provisional/current/generated result facts at 320 CSS pixels and genuine 200% text enlargement. Existing headless copy/delete and administration screenshot evidence is partial; retain unavailable status until these observations occur and correct any demonstrated in-scope failures per FR-030, SC-010, US5/AC3-AC7, TR-007, T042 (partial).
- [ ] T053 Obtain the five actual representative-planner/acceptance-reviewer unaided exercises defined in `specs/I-009-dated-intensive-windows/quickstart.md`; record anonymized individual times, independence/non-recurrence explanations and result-fact comprehension in `specs/I-009-dated-intensive-windows/validation.md`, with at least four completing within five minutes and all five identifying total-LE priority and permitted single-LV days. Keep this human-only acceptance open while reviewers are unavailable; do not simulate reviewers or waive the threshold per SC-009, T042 (partial).

## Phase 10: Code-review corrections

- [X] T054 Add failing `CourseSchedulePage.test.tsx` regressions before corrective production changes for failed course/semester constraint loads, blocked save/reset with retained same-selection date edits, retry/revisit recovery, unavailable focused-course generation, and delayed former-selection load/save/reset responses (FR-023–026, US3/AC10–12).
- [X] T055 Scope constraint readiness/errors to course, semester and catalog/retry context in `client/src/pages/CourseSchedulePage.tsx`; guard editor mutations and delayed responses, preserve same-selection input, and omit unavailable focused-course constraint loading from workspace readiness (FR-023–026).
- [X] T056 Run the corrected full frontend suite, TypeScript, ESLint and Vite build using the documented Node 24 runtime; perform a read-only follow-up code review and record exact outcomes and remaining feature-wide acceptance limitations in `validation.md`. Do not mark outstanding backend/manual acceptance tasks complete based on these frontend corrections.

## Phase 11: Candidate, recovery and precision review corrections

- [X] T057 Add failing independent lecturer/room recurring/dated availability-boundary optimum regressions, then complete intensive candidate seeds without changing unmarked behavior (FR-017–022).
- [X] T058 Add failing authenticated constraint read/broaden/reset and frontend recovery regressions, then separate maintenance eligibility from generation availability and refresh availability after maintenance (US3/AC13).
- [X] T059 Add failing exact draft/calendar/edit and teaching-editor/end-arithmetic regressions, then preserve precise clocks through those paths (US3/AC14).
- [X] T060 Run affected backend tests and full frontend/type/lint/build checks, review the corrections read-only, and record actual results without completing unrelated outstanding acceptance gates.

## Phase 12: Completion-aware first search and report interpretation

- [X] T061 Record detached baseline first-incumbent coverage and serial reference-stage timing; add failing completion-aware first-candidate and report-interpretation regressions before production edits.
- [X] T062 Add bounded advisory completion hints for the demonstrated preferred-size remainder case, retaining all hard constraints/objective priorities/native fallback/deadline behavior and unchanged lecturer semantics.
- [X] T063 Explain measured versus proven objective values and the composite schedule-shape penalty in the existing proof surface, without a new diagnostics feature or contract.
- [X] T064 Run targeted and broader regression verification, serial before/after observations, and read-only code review; record exact outcomes and limitations without claiming full release/manual acceptance.
