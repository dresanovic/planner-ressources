# Tasks: FS-022 Consistent Labels, European Dates, and Actionable Messages

**Input**: Design documents from `specs/I-002/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Tests are required by the specification and constitution. Within every story phase, complete the listed tests first and confirm that they fail for the intended missing behavior before changing production code wherever practical.

**Organization**: Tasks are grouped by the three prioritized user stories. The strict date formatter is foundational because the P1 motivating warning and all P2 presentation share it. Every task remains limited to the approved German terminology, European date, and actionable-message slice.

**Delivery prerequisite**: Before T001, isolate implementation on `codex/I-002-consistent-presentation` or an equivalent clean worktree. Preserve the unrelated changes already present on `master`; do not reset, delete, or absorb them into this slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can be executed in parallel after its stated phase dependencies because it uses different files and does not depend on another incomplete task in the same parallel group.
- **[US1]**, **[US2]**, **[US3]**: Maps the task to the corresponding prioritized story in `spec.md`.
- Every checklist item names the exact files it creates or changes.

## Phase 1: Setup and Evidence Baseline

**Purpose**: Isolate the broad customer-facing change, record the starting state, and turn the approved surface inventory into an implementation control before production edits.

- [X] T001 Create `specs/I-002/validation/baseline.md` and record the isolated branch/worktree, preserved pre-existing changes, Python/Node versions, and results or pre-existing failures from `python -m pytest backend/tests` run at the repository root plus `npm test`, `npm run lint`, and `npm run build` run from `client/`
- [X] T002 [P] Create `specs/I-002/validation/surface-migration.md` from `specs/I-002/contracts/surface-inventory.md` with one row per terminology occurrence group, human date display/entry, known problem state, owning mapper, planned test, and machine-boundary exclusion

---

## Phase 2: Foundational Shared Date Boundary

**Purpose**: Provide the one strict date-only/timestamp boundary required by both the P1 outside-window message and the P2 application-wide date migration.

**CRITICAL**: Complete this phase before any user-story implementation. The formatter is directly consumed by US1 and US2 and establishes the presentation boundary used by the final integrated verification; the recommended priority order remains US1, US2, then US3.

- [X] T003 Add failing strict formatter/parser tests for ISO-to-`DD.MM.YYYY` round trips, ranges with missing endpoints, impossible/incomplete dates, leap/century/year boundaries, Vienna timestamp/DST behavior, and institution-local today in `client/src/utils/datePresentation.test.ts`
- [X] T004 Implement pure `formatCalendarDate`, `formatCalendarDateRange`, `parseEuropeanDate`, strict ISO validation/arithmetic, zoned timestamp formatting, and institution-local today without date-only `Date` construction in `client/src/utils/datePresentation.ts` until T003 passes

**Checkpoint**: The shared formatter is deterministic, timezone-safe for date-only values, and leaves machine ISO values untouched.

---

## Phase 3: User Story 1 - Understand and Act on Reported Problems (Priority: P1) MVP

**Goal**: Planner users and accountless lecturers receive precise German warning/error items with affected context, known cause/rule/values, truthful blocking and saved-input state, and a safe next action; multiple problems remain separate and sensitive diagnostics never appear.

**Independent Test**: Trigger the motivating outside-window warning plus representative field validation, stale update, connectivity failure, permission failure, failed safe read, ambiguous mutation, unexpected failure, and multi-problem response. Verify exact available context/action, accessible semantics, retained input, and diagnostic non-disclosure without enabling US2's general date-field migration or US3's configurable terminology.

### Tests for User Story 1 (write and fail first)

- [X] T005 [P] [US1] Add failing pure mapping tests for blocking/warning tone, field context, stale/connectivity/permission/unexpected categories, ambiguous mutation guidance, safe Retry availability, and raw exception/secret suppression in `client/src/utils/userProblems.test.ts`
- [X] T006 [P] [US1] Add failing component tests for distinct repeated problems, one blocking alert announcement, polite non-blocking warning semantics, native keyboard actions, field description IDs, and long-content wrapping hooks in `client/src/components/ActionableProblemList.test.tsx`
- [ ] T007 [P] [US1] Add failing exact German outside-window tests covering course/exam identity, scheduled and recommended European dates, non-blocking/saved status, adjacent `Bearbeiten` guidance, intentional retention, and no raw validity code, plus DraftSchedulePanel field-error IDs, `aria-invalid`, `aria-describedby`, first-invalid focus, and preserved input in `client/src/components/DraftSchedulePanel.test.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, and `client/src/components/SessionPane.test.tsx`
- [ ] T008 [P] [US1] Add failing scheduling-operation tests for field association, stale data, failed reads, connectivity, ambiguous mutation outcome, preserved drafts, unexpected fallback, separate batch issues, and contextual publication conditions in `client/src/pages/CourseSchedulePage.test.tsx`, `client/src/components/ExamGenerationPanel.test.tsx`, `client/src/components/ExamRequirementEditor.test.tsx`, `client/src/components/ExamManualSessionEditor.test.tsx`, `client/src/components/TeachingSessionEditor.test.tsx`, `client/src/components/MultiCourseGenerationPanel.test.tsx`, `client/src/components/BatchResultSummary.test.tsx`, and `client/src/components/PublicationConfirmationDialog.test.tsx`
- [ ] T009 [P] [US1] Add failing academic/resource administration tests for contextual field association, permission, stale, connectivity, unknown failures, and protected-delete blockers without direct `reason.message`, joined errors, or invented recovery in `client/src/pages/AcademicDataPage.test.tsx`, `client/src/components/AcademicRecordEditor.test.tsx`, `client/src/components/HolidayAdministration.test.tsx`, `client/src/components/ResourceAdministration.test.tsx`, `client/src/components/ResourceAvailabilityEditor.test.tsx`, `client/src/components/CourseResourceEligibilityEditor.test.tsx`, and `client/src/components/ProtectedDeleteDialog.test.tsx`
- [X] T010 [P] [US1] Add failing backend tests for allowlisted contextual German accountless findings, unchanged public finding shape/category/refs, unknown-safe fallback, and non-disclosure of raw internal findings in `backend/tests/services/test_lecturer_review.py` and `backend/tests/api/test_lecturer_review.py`
- [ ] T011 [P] [US1] Add failing accountless/planner lecturer tests for contextual findings, truthful read-only feedback/review guidance, safe retry, multiple items, and bearer/fragment/diagnostic non-disclosure in `client/src/pages/LecturerReviewPage.test.tsx` and `client/src/components/LecturerReviewManagement.test.tsx`

### Implementation for User Story 1

- [X] T012 [US1] Implement the minimal `UserProblem` model and domain-neutral safe fallback/category helpers without a global code/action registry in `client/src/utils/userProblems.ts` until T005 passes
- [X] T013 [US1] Implement accessible separate blocking/warning problem lists and caller-supplied safe actions in `client/src/components/ActionableProblemList.tsx` until T006 passes
- [X] T014 [US1] Replace raw finding labels and implement the contextual outside-window mapping/rendering in `client/src/utils/calendarFindingLabel.ts`, `client/src/components/DraftSchedulePanel.tsx`, `client/src/components/CalendarPlanningWorkspace.tsx`, and `client/src/components/SessionPane.tsx` using `client/src/utils/datePresentation.ts` until T007 passes
- [ ] T015 [US1] Map scheduling, exam, lifecycle, batch, and publication-condition validation/stale/connectivity/permission/unexpected results to separate caller-context problems in `client/src/pages/CourseSchedulePage.tsx`, `client/src/components/ExamGenerationPanel.tsx`, `client/src/components/ExamRequirementEditor.tsx`, `client/src/components/ExamManualSessionEditor.tsx`, `client/src/components/TeachingSessionEditor.tsx`, `client/src/components/MultiCourseGenerationPanel.tsx`, `client/src/components/BatchResultSummary.tsx`, `client/src/components/ExamGenerationResultSummary.tsx`, and `client/src/components/PublicationConfirmationDialog.tsx` until T008 passes
- [ ] T016 [US1] Map academic, holiday, resource, availability, eligibility, and protected-delete blocker failures to contextual German problems while retaining entered values and safe existing callbacks in `client/src/pages/AcademicDataPage.tsx`, `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/HolidayAdministration.tsx`, `client/src/components/ResourceEditor.tsx`, `client/src/components/ResourceAvailabilityEditor.tsx`, `client/src/components/CourseResourceEligibilityEditor.tsx`, and `client/src/components/ProtectedDeleteDialog.tsx` until T009 passes
- [X] T017 [P] [US1] Generate allowlisted contextual German public finding messages from public-visible course/session data and validated safe supporting values without changing response shape in `backend/app/services/lecturer_review.py` until T010 passes
- [ ] T018 [US1] Render accountless and lecturer-management findings through truthful German problem items and current safe Retry/feedback/review controls in `client/src/pages/LecturerReviewPage.tsx` and `client/src/components/LecturerReviewManagement.tsx` until T011 passes
- [ ] T019 [US1] Complete inventory-driven programmatic field-error association, stable message IDs, `aria-invalid`, `aria-describedby`, submit-time first-invalid focus, and preserved-input behavior in `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/ExamRequirementEditor.tsx`, `client/src/components/HolidayAdministration.tsx`, `client/src/components/ResourceEditor.tsx`, `client/src/components/ResourceAvailabilityEditor.tsx`, `client/src/components/CourseResourceEligibilityEditor.tsx`, `client/src/components/TeachingSessionEditor.tsx`, `client/src/components/ExamManualSessionEditor.tsx`, `client/src/components/MultiCourseGenerationPanel.tsx`, `client/src/components/DraftSchedulePanel.tsx`, and `client/src/pages/CourseSchedulePage.tsx`
- [X] T020 [US1] Add non-color-only severity, visible-focus, long-name/message wrapping, action layout, and 320px/200%-zoom-safe problem styles in `client/src/App.css`
- [X] T021 [US1] Run `python -m pytest backend/tests/services/test_lecturer_review.py backend/tests/api/test_lecturer_review.py` from the repository root and `npm test -- src/utils/userProblems.test.ts src/components/ActionableProblemList.test.tsx src/components/DraftSchedulePanel.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/SessionPane.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/ExamGenerationPanel.test.tsx src/components/ExamRequirementEditor.test.tsx src/components/ExamManualSessionEditor.test.tsx src/components/TeachingSessionEditor.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/components/BatchResultSummary.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/pages/AcademicDataPage.test.tsx src/components/AcademicRecordEditor.test.tsx src/components/HolidayAdministration.test.tsx src/components/ResourceAdministration.test.tsx src/components/ResourceAvailabilityEditor.test.tsx src/components/CourseResourceEligibilityEditor.test.tsx src/components/ProtectedDeleteDialog.test.tsx src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx` from `client/`, then record failing-first evidence, final results, covered acceptance cases, and residual manual checks in `specs/I-002/validation/us1-actionable-problems.md`

**Checkpoint**: User Story 1 is independently demonstrable as the MVP, including the complete motivating warning and safe accessible recovery behavior.

---

## Phase 4: User Story 2 - Read and Enter European Calendar Dates (Priority: P2)

**Goal**: Every human-visible calendar date/range/timestamp and every visible date-entry value uses exact `DD.MM.YYYY` without changing its day or any machine-facing ISO contract.

**Independent Test**: Review every date row in `contracts/surface-inventory.md`, enter valid/invalid/boundary dates by pointer and keyboard, and compare existing request payloads, sorting, persistence, URLs, and exports. All visible/accessibility dates must be European and all machine boundaries unchanged.

### Tests for User Story 2 (write and fail first)

- [ ] T022 [P] [US2] Add failing `EuropeanDateField` tests for initial/external ISO sync, typing/paste, required/optional empty values, invalid/incomplete/impossible dates, min/max, stale-value suppression, submit-time error association/focus, keyboard use, and reset in `client/src/components/EuropeanDateField.test.tsx`
- [ ] T023 [P] [US2] Add failing calendar/list/detail tests for European dates and ranges in visible text, headings, accessible names, warnings, recommendation/final-teaching details, leap/year/DST boundaries, and no day shift in `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/ScheduleOccurrenceList.test.tsx`, `client/src/components/SessionPane.test.tsx`, and `client/src/components/calendarWorkspaceUtils.test.ts`
- [ ] T024 [P] [US2] Add failing schedule/exam entry and display tests for generation/manual/session/recommendation dates, invalid focus, range rules, and unchanged ISO callbacks in `client/src/components/DraftSchedulePanel.test.tsx`, `client/src/pages/CourseSchedulePage.test.tsx`, `client/src/components/TeachingSessionEditor.test.tsx`, `client/src/components/ExamManualSessionEditor.test.tsx`, `client/src/components/ExamRequirementEditor.test.tsx`, and `client/src/components/MultiCourseGenerationPanel.test.tsx`
- [ ] T025 [P] [US2] Add failing academic/holiday/resource date-entry tests for European visible values, strict correction, min/max/ranges, and unchanged ISO submissions in `client/src/components/AcademicRecordEditor.test.tsx`, `client/src/components/HolidayAdministration.test.tsx`, and `client/src/components/ResourceAvailabilityEditor.test.tsx`
- [ ] T026 [P] [US2] Add failing remaining-display tests for German/Vienna timestamps and European dates in lecturer review/management, lifecycle, deletion dialogs, batch results, availability labels, and schedule review summaries in `client/src/pages/LecturerReviewPage.test.tsx`, `client/src/components/LecturerReviewManagement.test.tsx`, `client/src/components/ScheduleLifecyclePanel.test.tsx`, `client/src/components/ExamDeletionDialog.test.tsx`, `client/src/components/ScheduleDeletionDialog.test.tsx`, `client/src/components/BatchResultSummary.test.tsx`, and `client/src/components/scheduleReviewUtils.test.ts`
- [ ] T027 [P] [US2] Extend machine-boundary regressions so display/input conversion leaves API payloads, snapshots, ISO ordering, and public lecturer transport unchanged in `client/src/api/calendarWorkspace.test.ts`, `client/src/api/draftSchedule.test.ts`, `client/src/api/examScheduling.test.ts`, `client/src/api/lecturerReview.test.ts`, `client/src/pages/CourseSchedulePage.snapshot.test.ts`, `backend/tests/api/test_calendar_workspace.py`, and `backend/tests/api/test_lecturer_review.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement the controlled accessible text-based `DD.MM.YYYY` field with persistent `TT.MM.JJJJ` help, strict validity, ISO/null output, stable hint/error IDs, and no caret mask or picker in `client/src/components/EuropeanDateField.tsx` until T022 passes
- [X] T029 [P] [US2] Migrate academic semester, holiday, and resource-availability date entry/display to `EuropeanDateField` and shared formatters in `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/HolidayAdministration.tsx`, and `client/src/components/ResourceAvailabilityEditor.tsx` until T025 passes
- [X] T030 [P] [US2] Migrate draft generation, manual teaching entry, course scheduling summaries, teaching editor, and comma-separated unavailable dates to strict European presentation with ISO callbacks in `client/src/components/DraftSchedulePanel.tsx`, `client/src/pages/CourseSchedulePage.tsx`, `client/src/components/TeachingSessionEditor.tsx`, and `client/src/components/MultiCourseGenerationPanel.tsx` until T024 passes
- [X] T031 [P] [US2] Migrate calendar anchor, headers, ranges, rows, detail/accessibility labels, and occurrence lists to shared formatters while retaining ISO comparison/navigation values in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/ScheduleOccurrenceList.tsx`, and `client/src/components/SessionPane.tsx` until T023 passes
- [X] T032 [P] [US2] Migrate exam entry, recommended/final-teaching ranges, and deletion confirmation dates to shared European presentation with unchanged ISO payloads in `client/src/components/ExamManualSessionEditor.tsx`, `client/src/components/ExamRequirementEditor.tsx`, and `client/src/components/ExamDeletionDialog.tsx`
- [X] T033 [P] [US2] Migrate remaining lecturer, lifecycle, schedule-deletion, batch, availability-label, calendar-validator, and review-summary dates/timestamps to explicit European/Vienna helpers in `client/src/pages/LecturerReviewPage.tsx`, `client/src/components/LecturerReviewManagement.tsx`, `client/src/components/ScheduleLifecyclePanel.tsx`, `client/src/components/ScheduleDeletionDialog.tsx`, `client/src/components/BatchResultSummary.tsx`, `client/src/utils/resourceAvailability.ts`, `client/src/api/calendarWorkspace.ts`, `client/src/components/calendarWorkspaceUtils.ts`, and `client/src/components/scheduleReviewUtils.ts` until T026 and T027 pass
- [X] T034 [US2] Run `npm test -- src/utils/datePresentation.test.ts src/components/EuropeanDateField.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/ScheduleOccurrenceList.test.tsx src/components/SessionPane.test.tsx src/components/calendarWorkspaceUtils.test.ts src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/TeachingSessionEditor.test.tsx src/components/ExamManualSessionEditor.test.tsx src/components/ExamRequirementEditor.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/components/AcademicRecordEditor.test.tsx src/components/HolidayAdministration.test.tsx src/components/ResourceAvailabilityEditor.test.tsx src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx src/components/ScheduleLifecyclePanel.test.tsx src/components/ExamDeletionDialog.test.tsx src/components/ScheduleDeletionDialog.test.tsx src/components/BatchResultSummary.test.tsx src/components/scheduleReviewUtils.test.ts src/api/calendarWorkspace.test.ts src/api/draftSchedule.test.ts src/api/examScheduling.test.ts src/api/lecturerReview.test.ts src/pages/CourseSchedulePage.snapshot.test.ts` from `client/` and `python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_lecturer_review.py` from the repository root, then record every inventory row, submitted ISO example, boundary result, technical ISO exclusion, and residual browser check in `specs/I-002/validation/us2-european-dates.md`

**Checkpoint**: User Story 2 is independently complete: all approved human date locations and entries use the European convention and machine contracts remain unchanged.

---

## Phase 5: User Story 3 - Configure Customer-Specific German Terminology (Priority: P3)

**Goal**: One optional startup file overrides selected context-specific German terms across both applications without rebuild or data changes; invalid configuration blocks startup, while ordinary application copy remains fixed German.

**Independent Test**: Start the same build with no override, a valid partial override, and every invalid override class. Confirm exact-set bootstrap, consistent representative replacements across planner/accountless surfaces, omitted-key defaults, unchanged record values/fixed prose, and no blank/raw key.

### Tests for User Story 3 (write and fail first)

- [X] T035 [P] [US3] Add failing loader and contract-parity tests proving the exact property set in `specs/I-002/contracts/terminology-overrides.schema.json` equals the complete nonblank backend defaults, then cover absent override, valid Unicode subset merge, omitted fallback, duplicate/malformed/wrong-root/unknown/blank/non-string/control-character rejection, configured missing/unreadable files, immutable result, and value-safe diagnostics in `backend/tests/services/test_terminology.py`
- [X] T036 [P] [US3] Add failing startup and public endpoint tests for invalid-config startup failure, exact full response, `Cache-Control: no-store`, public access without credentials, middleware classification, immutable application-state serving with no database query, and no secret/source leakage in `backend/tests/test_main.py` and `backend/tests/api/test_ui_terminology.py`
- [X] T037 [P] [US3] Add failing client tests proving its expected keys equal `specs/I-002/contracts/terminology-overrides.schema.json`, exact validation and set-once access, deterministic default initialization for direct component tests, isolated override/bootstrap state, no raw-key fallback, exactly one API-base fetch per bootstrap attempt, no interaction refetch, one additional fetch per explicit Retry, omitted credentials, fixed German failure UI, no partial render, and lecturer-fragment removal before the first request in `client/src/config/terminology.test.ts`, `client/src/main.test.tsx`, and `client/src/test/setup.ts`
- [ ] T038 [US3] After T037 establishes deterministic terminology test initialization, add failing shell/academic integration tests proving context-specific Course/Lecturer/Cohort/Room/Schedule/Academic Data overrides, stable navigation IDs, omitted defaults, fixed German prose, long labels, and unchanged stored names in `client/src/App.test.tsx`, `client/src/components/ApplicationNavigation.test.tsx`, `client/src/pages/AcademicDataPage.test.tsx`, and `client/src/components/AcademicRecordEditor.test.tsx`
- [ ] T039 [US3] After T037 establishes deterministic terminology test initialization, add failing resource/administration integration tests for catalog-backed field/table/heading contexts, German protected-delete copy, and unchanged domain IDs/record values in `client/src/components/ResourceAdministration.test.tsx`, `client/src/components/CourseResourceEligibilityEditor.test.tsx`, `client/src/components/HolidayAdministration.test.tsx`, and `client/src/components/ProtectedDeleteDialog.test.tsx`
- [ ] T040 [US3] After T037 establishes deterministic terminology test initialization, add failing schedule/exam integration tests for catalog-backed Course/Lecturer/Cohort/Room/Schedule contexts, fixed German sentences including publication conditions, and no label-driven filtering/routing in `client/src/pages/CourseSchedulePage.test.tsx`, `client/src/components/DraftSchedulePanel.test.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/SessionPane.test.tsx`, `client/src/components/ExamGenerationPanel.test.tsx`, and `client/src/components/PublicationConfirmationDialog.test.tsx`
- [ ] T041 [US3] After T037 establishes deterministic terminology test initialization, add failing planner/accountless lecturer integration tests for the same effective overridden terms, omitted defaults, fixed German copy, long values, and unchanged dynamic course/lecturer/room names in `client/src/pages/LecturerReviewPage.test.tsx` and `client/src/components/LecturerReviewManagement.test.tsx`

### Implementation for User Story 3

- [X] T042 [US3] Add the exact German default map in `backend/app/config/terminology.de.json` and implement strict duplicate-aware JSON loading, validation, partial merge, safe diagnostics, immutability, and `CUSTOMER_TERMINOLOGY_FILE` handling in `backend/app/terminology.py` until T035 passes
- [X] T043 [US3] Add the full effective-catalog response schema and public no-store route, initialize catalog state before FastAPI lifespan yield, and classify the route as public in `backend/app/schemas/ui_terminology.py`, `backend/app/api/ui_terminology.py`, and `backend/app/main.py` until T036 passes
- [X] T044 [US3] Implement exact typed catalog validation/access, API-base bootstrap fetch without credentials, pre-request lecturer-fragment removal, delayed dynamic imports, and fixed German failure/Retry rendering in `client/src/config/terminology.ts` and `client/src/main.tsx` until T037 passes
- [ ] T045 [P] [US3] Set German document metadata and migrate shell/navigation/academic fixed copy plus selected context labels without using display values as IDs in `client/index.html`, `client/src/App.tsx`, `client/src/components/ApplicationNavigation.tsx`, `client/src/pages/AcademicDataPage.tsx`, `client/src/components/AcademicCatalogList.tsx`, and `client/src/components/AcademicRecordEditor.tsx` until T038 passes
- [ ] T046 [P] [US3] Migrate resource/eligibility/availability/holiday list, heading, field, dialog, empty-state, and action copy to fixed German plus exact Lecturer/Room/Course/Cohort catalog contexts in `client/src/components/ResourceCatalogList.tsx`, `client/src/components/ResourceEditor.tsx`, `client/src/components/ResourceAvailabilityEditor.tsx`, `client/src/components/CourseResourceEligibilityEditor.tsx`, `client/src/components/HolidayAdministration.tsx`, `client/src/components/ResourceRemovalDialog.tsx`, and `client/src/components/ProtectedDeleteDialog.tsx` until T039 passes
- [ ] T047 [P] [US3] Migrate schedule/calendar/exam/lifecycle list, heading, field, dialog, summary, empty-state, accessible-name, and action copy to fixed German plus exact Course/Lecturer/Cohort/Room/Schedule catalog contexts in `client/src/pages/CourseSchedulePage.tsx`, `client/src/components/ScheduleContextHeader.tsx`, `client/src/components/DraftSchedulePanel.tsx`, `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/ScheduleOccurrenceList.tsx`, `client/src/components/SessionPane.tsx`, `client/src/components/TeachingSessionEditor.tsx`, `client/src/components/MultiCourseGenerationPanel.tsx`, `client/src/components/BatchResultSummary.tsx`, `client/src/components/ExamGenerationPanel.tsx`, `client/src/components/ExamGenerationResultSummary.tsx`, `client/src/components/ExamManualSessionEditor.tsx`, `client/src/components/ExamRequirementEditor.tsx`, `client/src/components/ScheduleLifecyclePanel.tsx`, `client/src/components/AbandonRevisionDialog.tsx`, `client/src/components/DiscardChangesDialog.tsx`, `client/src/components/PublicationConfirmationDialog.tsx`, `client/src/components/ReplacementConfirmationDialog.tsx`, `client/src/components/ScheduleDeletionDialog.tsx`, and `client/src/components/ExamDeletionDialog.tsx` until T040 passes
- [ ] T048 [P] [US3] Migrate accountless lecturer and planner coordination fixed copy plus exact Course/Lecturer/Room/Schedule catalog contexts while preserving dynamic record names and secret-safe behavior in `client/src/pages/LecturerReviewPage.tsx` and `client/src/components/LecturerReviewManagement.tsx` until T041 passes
- [X] T049 [US3] Document and expose the optional read-only `/config/terminology-overrides.json` deployment path and `CUSTOMER_TERMINOLOGY_FILE` environment setting without making the mount mandatory in `compose.yaml`, `.env.example`, and `infrastructure/docker/README.md`

**Checkpoint**: User Story 3 is independently complete: one immutable German catalog is startup-selected, strictly validated, consistently consumed, and deployment-documented without a rebuild or user-data change.

---

## Phase 6: Polish, Inventory Closure, and Acceptance Evidence

**Purpose**: Prove the application-wide coverage, machine/privacy regressions, real-browser accessibility, deployment behavior, and measurable usability outcome after all selected stories are complete.

- [ ] T050 Re-run boundary-aware searches for raw `reason.message`, backend `message`, joined errors, raw-code labels, native date inputs, browser-locale dates, human ISO dates, and selected literal terminology; do not complete the task while an in-scope violation remains, and classify only justified machine/fixed-copy exclusions with implementation/test links in `specs/I-002/validation/surface-migration.md`
- [X] T051 Run every focused and complete pytest/Vitest/lint/build command from `specs/I-002/quickstart.md`, compare with the T001 baseline, and record command, exit status, date-contract/export/privacy/domain regressions, and unresolved risk in `specs/I-002/validation/automated-verification.md`
- [ ] T052 [P] Validate the same built container with no override, a valid partial read-only override, and every invalid configuration class; record startup/readiness, effective response, no-rebuild evidence, safe logs, and unchanged database data in `specs/I-002/validation/deployment-verification.md`
- [ ] T053 [P] Execute the pointer, keyboard, latest-stable Edge/Chrome/Firefox on Windows, 320px, 200%-zoom, long-text, accessibility-tree, and NVDA/Firefox scenarios from `specs/I-002/quickstart.md` and record exact versions, focus/announcement results, screenshots, and defects in `specs/I-002/validation/manual-accessibility.md`
- [ ] T054 [P] Run the uncoached outside-window comprehension exercise with at least 10 representative planners/designated reviewers and record actual completion times and whether at least 9 of 10 meet SC-006 in `specs/I-002/validation/usability.md`
- [ ] T055 Resolve every in-scope defect recorded by T050-T054, record each exact production/test path and the affected automated/manual checks rerun to passing in `specs/I-002/validation/remediation.md`, and leave any genuinely unresolved item open rather than proceeding to release readiness
- [ ] T056 Reconcile all FR/TR/SC evidence, record any justified manual-only coverage, and update FS-022 status/history only when every required outcome is genuinely met in `specs/I-002/validation/release-readiness.md` and `docs/planning/Feature_slices.md`

---

## Dependencies & Execution Order

### Phase dependencies

1. **Phase 1 Setup** has no code dependency and must preserve the pre-existing worktree state.
2. **Phase 2 Foundation** depends on the setup baseline and blocks US1/US2 because both render dates in user-facing messages or surfaces.
3. **US1 (Phase 3)** depends on Phase 2 and is the recommended MVP.
4. **US2 (Phase 4)** depends on Phase 2. It is behaviorally independently testable, but should follow US1 in one worktree because several schedule/lecturer files overlap.
5. **US3 (Phase 5)** depends on Phase 2 under the shared foundational gate. In the recommended single-worktree execution it follows US2 because its German-copy/catalog migration touches most of the same components.
6. **Phase 6 Polish** depends on every story selected for release. T055 depends on the automated, deployment, accessibility, and usability findings from T050-T054; T056 depends on their documented remediation or a genuinely recorded blocker.

### User story dependency graph

```text
Phase 1 Setup
    |
    `--> Phase 2 Shared Date Boundary --> US1 Actionable Problems (MVP)
                                     |--> US2 European Dates
                                     `--> US3 Terminology

US1 + US2 + US3 --> Phase 6 Full inventory and acceptance
```

US1, US2, and US3 have separate independent test criteria. The sequencing recommendation is driven by overlapping files and priority, not a hidden product dependency.

### Within each user story

- Complete every test task in the story before its corresponding production task and capture the intended failing result where practical.
- Implement the smallest core model/helper before renderers and surface integrations.
- Preserve existing API/domain identifiers before migrating presentation.
- Run focused story verification and update the story evidence before crossing its checkpoint.
- Never mark a manual or representative-user result complete without actual evidence.

## Parallel Opportunities

### Setup and foundation

- T002 can prepare the inventory matrix while T001 records the isolated baseline.
- T003 is the sole test-first prerequisite for T004.

### User Story 1

- T005-T011 can run in parallel because they cover separate pure, component, scheduling, administration, backend, and lecturer test files.
- After their tests exist, T012 and T017 can run in parallel; T013 follows T012, while the backend public projection remains independent.
- T014-T016 and T018 can be divided by their non-overlapping surface groups after T012-T013; T019 then closes shared field associations.

### User Story 2

- T022-T027 can run in parallel across component, surface, and contract test files, coordinating only where a listed test file overlaps.
- After T028, T029-T033 can run in parallel by academic/resource, schedule, calendar, exam, and lecturer/lifecycle file group.

### User Story 3

- T035-T037 can run in parallel across backend loader/API and client bootstrap tests. After T037 establishes the shared terminology test initialization, T038-T041 can run in parallel across shell/academic, resource, schedule, and lecturer integration tests.
- T042 and the client-side preparation for T044 can proceed in parallel after their tests; T043 follows T042's server access contract.
- After T044, T045-T048 can run in parallel by shell/academic, resource, schedule/exam, and lecturer surface group.

### Final validation

- T052-T054 can run in parallel after T050-T051 establish a green automated candidate. T055 waits for all findings and closes them; T056 then performs the release-readiness decision.

## Parallel Execution Examples

### User Story 1 test batch

```text
T005: client/src/utils/userProblems.test.ts
T006: client/src/components/ActionableProblemList.test.tsx
T007-T009: separate planner surface test groups
T010: backend/tests/services/test_lecturer_review.py and backend/tests/api/test_lecturer_review.py
T011: lecturer client tests
```

### User Story 2 migration batch after T028

```text
T029: academic/holiday/resource dates
T030: draft/course/teaching/multi-course dates
T031: calendar/occurrence/session dates
T032: exam dates
T033: lecturer/lifecycle/utility dates
```

### User Story 3 migration batch after T044

```text
T045: shell/navigation/academic terminology and German copy
T046: resource/eligibility/holiday terminology and German copy
T047: schedule/calendar/exam terminology and German copy
T048: accountless/planner lecturer terminology and German copy
```

## Implementation Strategy

### MVP first: User Story 1

1. Complete Phase 1 without disturbing existing changes.
2. Complete the strict shared date boundary in Phase 2.
3. Complete T005-T021 for actionable German problems.
4. Stop and validate US1 independently, including the motivating warning, privacy, multiple issues, field associations, and safe recovery.
5. Demonstrate or release this increment only if partial deployment is acceptable; it intentionally does not claim full application date or customer-terminology completion.

### Incremental delivery

1. **MVP**: Actionable Problems gives immediate comprehension/recovery value.
2. **Increment 2**: European Dates completes display and entry consistency while retaining ISO boundaries.
3. **Increment 3**: Customer Terminology completes German fixed copy and startup-selected context labels.
4. **Acceptance**: Inventory, full regression, deployment, accessibility, and real-user evidence close the slice.

### Simplicity guardrails

- Add no package dependency, i18n framework, React catalog context, date picker/mask, universal error envelope, action registry, automatic mutation retry, diagnostic reference system, database setting, or administration UI.
- Keep domain-specific message facts near their owning pages/components; share only the small problem value/renderer and proven date/terminology boundaries.
- Keep ISO and stable domain IDs at machine/logic boundaries; convert only when rendering or accepting human input.
- If implementation discovers missing facts or a required contract change, update `specs/I-002/spec.md` and `specs/I-002/plan.md` before changing production behavior.

## Notes

- `[P]` marks a safe parallel opportunity, not a requirement to parallelize.
- Existing current tests may be updated in the same task as the listed new assertions, but production changes still follow the failing test.
- Commit after each task or coherent task group only after its relevant tests pass.
- Full slice acceptance requires actual T052-T054 evidence; unavailable participants or assistive-technology access must be reported as a blocker, never replaced with fabricated results.

## Phase 7: Convergence

- [ ] T057 Complete catalog-backed Course/Lecturer/Cohort/Room/Schedule/Academic Data contexts and fixed German copy across every remaining planner, resource, exam, lifecycle, protected-delete, accountless lecturer, and lecturer-management surface named by `contracts/surface-inventory.md`; preserve stable IDs, routing values, and dynamic record names per FR-004, FR-009, and SC-001 (partial)
- [ ] T058 Replace remaining joined errors, raw backend condition/blocker messages, raw-code-derived primary labels, and generic English failures with separate domain-local German `UserProblem` items that name the action and affected context, state known cause/rule/blocking/saved status, and expose only truthful available recovery in `ExamRequirementEditor.tsx`, `PublicationConfirmationDialog.tsx`, `ProtectedDeleteDialog.tsx`, `CourseSchedulePage.tsx`, and every remaining inventoried problem path per FR-018–FR-025, FR-031–FR-034, and SC-005 (partial)
- [ ] T059 Add attempted-continuation validation and first-invalid focus for every button-driven form using `EuropeanDateField`, then add stable field error IDs, `aria-invalid`, `aria-describedby`, distinct multiple field problems, and preserved-draft behavior across the forms listed in T019 per FR-027–FR-030, SC-004, and SC-007 (partial)
- [ ] T060 Add representative customer-override integration tests across shell/navigation, academic/resource administration, schedule/calendar/exam, accountless lecturer, and lecturer-management surfaces, proving long Unicode labels propagate on next bootstrap while stable IDs, filters, routes, dynamic names, and fixed prose remain unchanged per TR-003 and SC-001 (partial)
- [ ] T061 Complete the date/message/terminology verification matrix with paste, reset, keyboard-only, min/max/range, submit-focus, leap/year/DST, unchanged ISO payload/snapshot/export/public-transport tests and a repeatable source audit; update every row of `validation/surface-migration.md` with exact evidence and justified machine/fixed-copy exclusions per TR-002, TR-004–TR-007, and SC-003–SC-005 (partial)
