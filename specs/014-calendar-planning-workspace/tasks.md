# Tasks: FS-014 Calendar Planning Workspace and Operational Dashboard

**Input**: Design documents from
`/specs/014-calendar-planning-workspace/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), and [quickstart.md](quickstart.md)

**Tests**: Tests are required by the specification and constitution. Create or
update each test task before its corresponding production task, confirm the
intended failure where practical, and keep earlier-slice regression tests
passing.

**Organization**: Tasks are grouped by user story. The existing Courses
overview becomes the unified Schedule workspace's only List mode; these tasks
preserve that implementation and its behavior until parity is proven.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on another incomplete task in the same group.
- **[Story]**: Maps the task to a user story in `spec.md`.
- Every task names the exact file or files it changes or validates.

## Phase 1: Setup

**Purpose**: Establish the isolated delivery boundary and reusable deterministic
fixtures without adding dependencies.

- [X] T001 Create and switch to `codex/fs-014-calendar-workspace`, then record the verified branch/baseline assumption in `specs/014-calendar-planning-workspace/plan.md`
- [X] T002 [P] Create the deterministic 100-course/500-occurrence/50-holiday backend fixture and smaller story variants in `backend/tests/calendar_workspace_fixtures.py`
- [X] T003 [P] Create matching typed client workspace, no-revision, partial, failure, and Published/Working fixtures in `client/src/test/calendarWorkspaceFixtures.ts`

**Checkpoint**: Implementation is isolated and all later tests can use
deterministic feature fixtures.

---

## Phase 2: Foundational — Outcome Retention and Shared Validation

**Purpose**: Add the cross-story persistence and validation inputs required for
accurate reloadable operational state.

**CRITICAL**: Complete this phase before any user-story production behavior.

### Foundational tests — write and confirm failure first

- [X] T004 [P] Add fresh-install, 0007-upgrade, foreign-key, uniqueness, and no-fabricated-backfill tests for migration 0008 in `backend/tests/db/test_migrations.py`
- [X] T005 [P] Add insert, same-key newer upsert, cross-key isolation, stale-revision rejection, successor non-inheritance, and reload tests in `backend/tests/services/test_planning_outcome_retention.py`
- [X] T006 [P] Add reliable-completion versus request/cancel/operation-level-failure retention tests for single-course generation in `backend/tests/api/test_draft_schedule.py`
- [X] T007 [P] Add per-course result retention and same-kind supersession tests for multi-course generation in `backend/tests/api/test_multi_course_generation.py`
- [X] T008 [P] Add successful, improved-partial, unchanged, failed, and stale per-course retention tests for semester optimization in `backend/tests/api/test_conflict_aware_generation.py`
- [X] T009 [P] Add completed exam-generation outcome retention and rollback/stale-context tests in `backend/tests/api/test_exam_scheduling.py`
- [X] T010 [P] Add snapshot-v2 capture, immutable read, v1 compatibility, and missing-constraint availability tests in `backend/tests/services/test_schedule_lifecycle.py`
- [X] T011 [P] Add common live-row and Published-snapshot evaluator parity tests, including exclusion of Working occurrences from Published validation, in `backend/tests/services/test_draft_schedule_validation.py`

### Foundational implementation

- [X] T012 Create migration 0008 with the `planning_outcomes` table, indexes, foreign keys, classification/operation checks, and unique revision-course-kind key in `backend/app/db/migrations/0008_calendar_workspace_outcomes.py`
- [X] T013 Register the 0008 schema and add the `PlanningOutcome` SQLAlchemy model/relationships in `backend/app/db/schema.py` and `backend/app/models/planning.py`
- [X] T014 Implement transactional latest-applicable-outcome insert/upsert/read behavior and stale-revision safeguards in `backend/app/services/planning_outcomes.py`
- [X] T015 Integrate reliable single-course completed results with the retention helper in `backend/app/api/draft_schedule.py` and `backend/app/services/schedule_generation.py`
- [X] T016 [P] Integrate reliable multi-course per-course completed results with the retention helper in `backend/app/api/multi_course_generation.py` and `backend/app/services/multi_course_generation.py`
- [X] T017 [P] Integrate semester-optimization per-course classifications with the retention helper in `backend/app/api/conflict_aware_generation.py`, `backend/app/services/conflict_aware_generation.py`, and `backend/app/services/semester_optimization.py`
- [X] T018 [P] Integrate reliable exam-generation per-course completed results with the retention helper in `backend/app/api/exam_scheduling.py`, `backend/app/services/exam_scheduling.py`, and `backend/app/services/exam_optimization.py`
- [X] T019 Extend new publication snapshots to schema v2 with captured course constraint context while preserving immutable v1 reads in `backend/app/schemas/schedule_lifecycle.py` and `backend/app/services/schedule_lifecycle.py`
- [X] T020 Extract typed pure validation records/evaluators and adapt both live Working rows and Published snapshot occurrences without changing rule meanings in `backend/app/services/draft_schedule_validation.py`

**Checkpoint**: Reliable latest outcomes survive reloads, new publications
capture sufficient validation context, legacy publications remain readable, and
Working/Published validation uses one tested rule source.

---

## Phase 3: User Story 1 — Understand the Semester at a Glance (Priority: P1) MVP

**Goal**: Show one clearly identified Working or Current Published semester
context with its teaching/exam occurrences, remaining work, current findings,
retained outcomes, lifecycle state, and operational summaries.

**Independent Test**: Load no-revision, Working-only, Published-only, and
coexisting contexts and verify that one coherent response and screen contains
the correct revision identity, records, summaries, availability, and Published
current-validation overlay without cross-revision data.

### Tests for User Story 1 — write and confirm failure first

- [X] T021 [P] [US1] Add service tests for default revision selection, a no-revision response with empty revision-owned data/facets and no-revision not-applicable summaries, captured Published course totals, current Published validation, canonical metric applicability/value rules, needs-review reasons, and not-applicable/unavailable/partial-known/available planning-outcome coverage with zero allowed only for complete coverage in `backend/tests/services/test_calendar_workspace.py`
- [X] T022 [P] [US1] Add OpenAPI-shaped endpoint tests for distinct loaded/no-revision variants, required numeric fields for available/partial metrics, forbidden numeric fields and required reasons for unavailable/not-applicable metrics, empty no-revision records/facets, no-revision summary scope, named metric fields, category-specific finding details, typed references, workspace token, and rejection of mixed Working/Published identities in `backend/tests/api/test_calendar_workspace.py`
- [X] T023 [P] [US1] Add discriminated loaded/no-revision response parsing, required-field, typed occurrence, four-state metric, forbidden metric-shape, and problem-response tests in `client/src/api/calendarWorkspace.test.ts`
- [X] T024 [P] [US1] Add UI tests for revision/semester labels, teaching/exam distinction, five summary states, holiday context, no-revision action, and Published read-only explanation in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T025 [P] [US1] Add Schedule-page tests for Working-default, Published-fallback, no-revision, and coherent initial integration in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 1

- [X] T026 [P] [US1] Define distinct loaded/no-revision response variants, occurrence, finding, retained-outcome, five conditionally shaped named summaries, four-state availability, planning-outcome coverage, loaded/empty facets, and problem schemas from the OpenAPI contract in `backend/app/schemas/calendar_workspace.py`
- [X] T027 [US1] Implement selected-context loading, an empty no-revision response with no-revision not-applicable summaries, canonical typed references, metric-specific applicability/value rules, remaining-unit/minute calculations, conflict/capacity/failure/needs-review aggregation, section availability, and workspace token creation in `backend/app/services/calendar_workspace.py`
- [X] T028 [US1] Expose `GET /api/semesters/{semester_id}/calendar-workspace` with default/explicit revision handling and 404/409/422 failures in `backend/app/api/calendar_workspace.py`
- [X] T029 [US1] Register the calendar workspace router without adding a new application destination in `backend/app/main.py`
- [X] T030 [P] [US1] Implement discriminated loaded/no-revision TypeScript contract types, conditional metric validation, and fetch handling in `client/src/api/calendarWorkspace.ts`
- [X] T031 [P] [US1] Extend captured-versus-live schedule normalization for the workspace without mutating snapshots in `client/src/pages/scheduleSnapshot.ts`
- [X] T032 [US1] Build the semantic at-a-glance workspace shell, persistent context header, Week default surface, occurrence cards, holiday context, and operational summary cards in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T033 [US1] Make `CourseSchedulePage` own selected workspace revision, coherent load state, response token, and integration with the existing lifecycle and correction components in `client/src/pages/CourseSchedulePage.tsx`
- [X] T034 [US1] Add the initial calendar-centered wide layout, non-color teaching/exam/warning treatment, summary availability treatment, and persistent revision context styles in `client/src/App.css`

**Checkpoint**: The planner can understand the complete selected semester state
from one coherent MVP workspace; no navigation/filter/drilldown expansion is
required to prove this story.

---

## Phase 4: User Story 2 — Navigate and Filter the Calendar (Priority: P1)

**Goal**: Provide Week, Day, Month, and the adapted existing List mode with
date navigation and non-mutating intersected filters that preserve semester and
revision context.

**Independent Test**: Navigate all modes and date periods, apply every filter
alone and in combination, clear them, and prove the visible records/summaries
change without a mutation request or loss of the selected context; verify List
is the existing Courses overview behavior rather than a duplicate.

### Tests for User Story 2 — write and confirm failure first

- [X] T035 [P] [US2] Add UTC-safe ISO date, semester-boundary, Week/Day/Month range, current-period behavior for today inside/before/after the semester, List-mode non-applicability, and previous/next navigation tests in `client/src/components/calendarWorkspaceUtils.test.ts`
- [X] T036 [US2] Add intersection, unscheduled-course, room/remaining-work, exam-only, validation, lifecycle, no-match, and clear-filter projection tests in `client/src/components/calendarWorkspaceUtils.test.ts`
- [X] T037 [P] [US2] Add mode preservation, date controls, announced nearest-boundary substitution, List current-period non-applicability without repositioning, out-of-semester dates, teaching/exam cards, active-filter communication, and no-mutation UI tests in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T038 [P] [US2] Add explicit parity tests for existing filters, List and Weekly review outcomes, alerts, summaries, selection, and editor paths in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T039 [P] [US2] Add page-level tests proving mode/filter/date state survives revision-safe rendering and List uses the adapted overview exactly once in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 2

- [X] T040 [US2] Implement UTC-safe ISO calendar ranges, today-or-nearest-semester-boundary current-period resolution, List-mode non-applicability, previous/next navigation, filter intersections, facet selection, and visible-record projection in `client/src/components/calendarWorkspaceUtils.ts`
- [X] T041 [US2] Implement Week, Day, and Month grids, carry the existing Weekly review outcomes/alerts into Week, add previous/next/current/date controls with announced nearest-boundary substitution, mark current period not applicable in List, add outside-semester treatment and dense-date continuation, and preserve context in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T042 [US2] Add course, cohort, lecturer, room, study type, session type, lifecycle, and validation filter controls with visible active state and complete clear action in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T043 [US2] Adapt the existing Courses overview in `DraftSchedulePanel` as the workspace's single List branch while preserving its required review, alert, summary, selection, and editor behavior, and keep the separate legacy host usable throughout parity validation in `client/src/components/DraftSchedulePanel.tsx`
- [X] T044 [US2] Promote mode, date, filters, drilldown, and selected-record state to the shared Schedule workspace and render the adapted List once in `client/src/pages/CourseSchedulePage.tsx`
- [X] T045 [US2] Add accessible calendar grids, mode/date/filter layouts, active-filter chips, outside-semester treatment, and dense-date continuation styling without importing reference-image-only controls in `client/src/App.css`

**Checkpoint**: All four modes and filters work from one response, and the
existing overview—not a replacement—is the only List mode.

---

## Phase 5: User Story 3 — Trace Summaries and Alerts to Affected Records (Priority: P1)

**Goal**: Reconcile every operational value to all and only its contributing
courses, occurrences, findings, or outcomes and navigate to each contributor
without changing revision context.

**Independent Test**: Activate each metric in prepared mixed data, compare the
displayed contributor set with an independent expected set, reach dated and
undated contributors, and clear the drilldown back to the prior workspace
context.

### Tests for User Story 3 — write and confirm failure first

- [X] T046 [P] [US3] Add canonical conflict-pair/type, capacity-occurrence, retained-failure record count, eligible/covered course coverage, per-metric not-applicable versus available-zero universes, unavailable/partial source coverage, remaining-work, multi-reason needs-review, and complete category-specific contributor-detail tests in `backend/tests/services/test_calendar_workspace.py`
- [X] T047 [P] [US3] Add filtered-summary reconciliation, hidden conflict-partner linkage, room-filter semantics, and distinct-course reason tests in `client/src/components/calendarWorkspaceUtils.test.ts`
- [X] T048 [P] [US3] Add summary activation, scope announcement, exact contributor list, full reason display, clear drilldown, and zero/unavailable non-activation tests in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T049 [P] [US3] Add off-period dated-target navigation and undated course/outcome List-detail navigation tests in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T050 [US3] Complete canonical finding identities and category-specific contributor detail payloads for conflicts, capacity, failures, remaining work, and needs review in `backend/app/services/calendar_workspace.py`
- [X] T051 [US3] Implement the conflict, capacity, holiday, exam-validity, and other category-specific contributor-detail schemas required by the OpenAPI trace contract in `backend/app/schemas/calendar_workspace.py`
- [X] T052 [US3] Implement filtered metric projections and contributor reconciliation over canonical response references in `client/src/components/calendarWorkspaceUtils.ts`
- [X] T053 [US3] Implement actionable summary cards, complete/filtered scope labels, contributor regions, reason details, related-conflict links, and clear-drilldown behavior in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T054 [US3] Implement trace routing that moves dated targets into view and sends undated courses/outcomes to the adapted List/detail context without fabricating dates in `client/src/pages/CourseSchedulePage.tsx`
- [X] T055 [US3] Add deterministic drilldown entry/exit focus and contributor relationship styling/semantics in `client/src/App.css` and `client/src/components/CalendarPlanningWorkspace.tsx`

**Checkpoint**: Every metric is auditable and actionable within the selected
revision, including off-screen and undated contributors.

---

## Phase 6: User Story 4 — Inspect and Correct a Session Through Existing Workflows (Priority: P2)

**Goal**: Expose complete teaching/exam detail and invoke only the established
Working correction paths, then refresh the whole workspace coherently.

**Independent Test**: Inspect representative teaching and exam occurrences in
Working and Published, complete/cancel/fail/stale each applicable established
action, and verify action availability, unchanged rules, coherent refresh, and
predictable focus.

### Tests for User Story 4 — write and confirm failure first

- [X] T056 [P] [US4] Add teaching/exam detail-field, current-warning, revision-context, Published-read-only, and focus-entry/return tests in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T057 [P] [US4] Add existing edit/delete/manual-create/planning/exam action handoff, success refresh, cancel, failure, and stale-result tests in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T058 [P] [US4] Extend regression tests for unchanged manual editor, deletion, and alert behavior when invoked from List/calendar context in `client/src/components/DraftSchedulePanel.test.tsx`, `client/src/components/ScheduleDeletionDialog.test.tsx`, and `client/src/components/ExamManualSessionEditor.test.tsx`

### Implementation for User Story 4

- [X] T059 [P] [US4] Normalize all FS-009 teaching detail and FS-012 exam validity/recommendation fields for live and captured occurrences in `client/src/pages/scheduleSnapshot.ts`
- [X] T060 [US4] Implement labelled teaching/exam detail with all current findings and Working-versus-Published action explanation in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T061 [US4] Connect detail actions to the existing manual creation, editing, deletion, planning, exam, and lifecycle handlers without duplicating validation rules in `client/src/pages/CourseSchedulePage.tsx`
- [X] T062 [US4] Refresh calendar records, summaries, warnings, remaining units, revision identity, and action availability atomically after a successful existing action in `client/src/pages/CourseSchedulePage.tsx`
- [X] T063 [US4] Preserve workspace state and established feedback after cancel/failure/stale results, and move focus predictably when an edited/deleted record disappears, in `client/src/pages/CourseSchedulePage.tsx`
- [X] T064 [US4] Add detail-region, read-only explanation, action-group, warning, and visible-focus styling in `client/src/App.css`

**Checkpoint**: Awareness becomes action through existing workflows only; the
calendar introduces no second mutation rule set.

---

## Phase 7: User Story 5 — Compare Working and Published Operational Context (Priority: P2)

**Goal**: Make Working and Current Published identity, content, lifecycle
meaning, validation basis, and action availability unmistakable while leaving
history and transitions with FS-013.

**Independent Test**: Publish, create/edit a successor, mark it Ready for
review, switch repeatedly, and verify stable identity, distinct content,
current Published validation, read-only behavior, and established lifecycle
history/action paths.

### Tests for User Story 5 — write and confirm failure first

- [X] T065 [P] [US5] Add explicit Working/Published selection, historical-revision rejection, changed-context conflict, and Published-only validation isolation tests in `backend/tests/api/test_calendar_workspace.py`
- [X] T066 [P] [US5] Add atomic repeated-switch, Draft/Ready wording, changed/added/removed occurrence, action-availability, and stale-response rejection tests in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T067 [P] [US5] Add stable revision identity, active Working/current-publication designation, Ready-not-approved wording, and existing history/action tests in `client/src/components/ScheduleLifecyclePanel.test.tsx`

### Implementation for User Story 5

- [X] T068 [US5] Enforce permitted explicit revision selection, historical rejection, read-only Published context, and conflict response when context changes mid-read in `backend/app/services/calendar_workspace.py` and `backend/app/api/calendar_workspace.py`
- [X] T069 [US5] Implement atomic context switching, response-token stale-result rejection, selection reset/preservation rules, and full state replacement in `client/src/pages/CourseSchedulePage.tsx`
- [X] T070 [US5] Present stable revision number/state/designation, Ready-for-review semantics, current-validation labeling, and established history/lifecycle entry points in `client/src/components/ScheduleLifecyclePanel.tsx` and `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T071 [US5] Add persistent non-color Working/Current Published, Draft/Ready/Published, read-only, and current-validation styles in `client/src/App.css`

**Checkpoint**: The planner cannot mistake unpublished work for the current
publication, and FS-013 remains the lifecycle authority.

---

## Phase 8: User Story 6 — Continue Safely Through Responsive and Failure States (Priority: P3)

**Goal**: Keep the complete workspace operable by keyboard and assistive
technology at narrow/zoomed sizes and through loading, partial, initial-failure,
refresh-failure, retry, and recovery states.

**Independent Test**: Complete the primary workflow at 320 CSS pixels and 200%
zoom with keyboard/screen reader, then exercise every empty/failure/retry path
and verify no false zero, mixed context, hidden action, covered FS-018
navigation, or focus loss.

### Tests for User Story 6 — write and confirm failure first

- [X] T072 [P] [US6] Add service tests for every metric's no-applicable-record, no-verifiable-source, partially verified, available-zero, and available-nonzero state; planning-failure eligible/covered course coverage; exclusion of unavailable contributions; and coherent recovery in `backend/tests/services/test_calendar_workspace.py`
- [X] T073 [P] [US6] Add client parsing tests for partial availability, initial error, conflict, retryable failure, and last-known metadata in `client/src/api/calendarWorkspace.test.ts`
- [X] T074 [P] [US6] Add distinct no-semester/no-revision/no-session/no-issue/no-match/loading/partial/initial-failure/refresh-failure/recovery UI tests, including no-revision Start Draft rendering and not-applicable/unavailable/partial/available metric presentation, in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T075 [US6] Add semantic names/relationships, live announcements, keyboard mode/filter/summary/detail operation, simultaneous-session discovery, and focus tests in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T076 [P] [US6] Add pending-context race, last-known refresh failure, retry, recovery, and no-cross-context page tests in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 6

- [X] T077 [US6] Return section-level available/partial/unavailable coverage without false totals and preserve one coherent response boundary in `backend/app/services/calendar_workspace.py`
- [X] T078 [P] [US6] Preserve structured retryable problem and partial-section information in `client/src/api/calendarWorkspace.ts`
- [X] T079 [US6] Implement intended-context loading, atomic request replacement, last-known refresh state, retry, recovery, and request-race rejection in `client/src/pages/CourseSchedulePage.tsx`
- [X] T080 [US6] Implement all distinct empty/loading/partial/failure/recovery presentations, status announcements, and retry controls in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T081 [US6] Implement wide and sequential narrow layouts, 320 CSS-pixel/200%-zoom behavior, unobstructed FS-018 navigation, 4.5:1 text and 3:1 essential non-text contrast, and reduced-motion-safe focus styling in `client/src/App.css`
- [ ] T082 [US6] Execute keyboard, supported screen-reader/browser, simultaneous-session, contrast, 320 CSS-pixel, 200% zoom, dense-date, and FS-018 navigation checks and record environments/results in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`

**Checkpoint**: Every required record and action remains reachable and
truthfully represented across responsive and failure states.

---

## Phase 9: Polish and Cross-Cutting Verification

**Purpose**: Prove scale, regression, scope, documentation, visual alignment,
and human success criteria after all desired story phases.

- [X] T083 [P] Add deterministic 20-run initial-load and workspace-service timing assertions at the approved reference scale in `backend/tests/performance/test_calendar_workspace_performance.py`
- [X] T084 [P] Add or extend regression assertions that FS-018 navigation retains one Schedule destination and remains current/keyboard-operable in `client/src/components/ApplicationNavigation.test.tsx` and `client/src/App.test.tsx`
- [X] T085 Update outcome persistence, snapshot-v2 compatibility, workspace behavior, and local validation instructions in `backend/app/db/migrations/README.md` and `client/README.md`
- [X] T086 Run all focused migration/service/API tests from `specs/014-calendar-planning-workspace/quickstart.md` and record command/results in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T087 Run `python -m pytest backend/tests`, resolve only FS-014-related regressions in the files named by failing tests, and record the final result in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T088 Run focused client tests, `npm run test`, `npm run lint`, and `npm run build` from `client/package.json`, resolve FS-014-related failures, and record results in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T089 Run the 20-iteration API/browser performance protocol and record server versus browser measurements against SC-010–SC-012 in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T090 Compare the implemented wide/narrow workspace with `docs/designs/resource-planner-calendar-screen-reference.png` and navigation with `docs/designs/resource-planner-unified-navigation-ground-truth.png`, documenting gradual adoption and deliberate scope/accessibility deviations in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T091 Verify the absence of a second list, Dashboard destination, drag/drop/resize/duplicate/split/merge, automatic repair, new optimization, lecturer access, external sync, and independent course publication, and record the audit in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T092 Conduct SC-004–SC-006 with at least 10 actual representative planners/designated reviewers and record anonymized outcomes—or explicitly retain them as pending—in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [X] T093 Complete every applicable scenario in `specs/014-calendar-planning-workspace/quickstart.md`, reconcile the evidence with `specs/014-calendar-planning-workspace/spec.md`, and record final pass/pending/fail status in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`
- [ ] T094 After T038, T082, T084, T088, T090, T092, and T093 complete, record the List/Weekly behavior, accessibility, navigation, visual, regression, and acceptance parity decision in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`; if any required evidence is pending or failing, retain the separate legacy host
- [ ] T095 When T094 records complete parity, remove only the separate legacy Courses overview host/mode switch while retaining the adapted shared List implementation in `client/src/components/DraftSchedulePanel.tsx` and `client/src/pages/CourseSchedulePage.tsx`
- [ ] T096 After T095, rerun focused List/Week tests, `npm run test`, `npm run lint`, `npm run build`, keyboard smoke checks, and narrow-layout checks from `client/package.json`, and record results in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 — Setup**: Starts immediately.
- **Phase 2 — Foundational**: Depends on Phase 1 and blocks all user-story
  production work.
- **Phase 3 — US1**: Depends on Phase 2 and creates the coherent MVP workspace.
- **Phase 4 — US2**: Depends on the US1 workspace shell and can run in parallel
  with US3 after US1.
- **Phase 5 — US3**: Depends on US1 canonical summaries and can run in parallel
  with US2 after US1.
- **Phase 6 — US4**: Depends on US1 detail selection; its trace-entry behavior
  integrates with US3 when both are selected for delivery.
- **Phase 7 — US5**: Depends on US1 revision loading and may run in parallel
  with US2–US4 after US1.
- **Phase 8 — US6**: Depends on the workspace flows selected for release so
  responsive/failure/accessibility validation covers the delivered whole.
- **Phase 9 — Polish**: Depends on all stories selected for final release.

### User-story completion order

```text
Setup -> Foundation -> US1 (MVP)
                         |-> US2 --|
                         |-> US3 --|-> US6 -> Polish
                         |-> US4 --|
                         `-> US5 --|
```

- **US1 (P1)** is independently demonstrable as the at-a-glance MVP.
- **US2 (P1)** independently proves navigation/filter/List parity on the US1
  response.
- **US3 (P1)** independently proves aggregate-to-contributor traceability on
  the US1 response.
- **US4 (P2)** independently proves existing action handoff and refresh from a
  selected occurrence.
- **US5 (P2)** independently proves Working/Published comparison and lifecycle
  semantics.
- **US6 (P3)** independently proves responsive, accessible, and failure-safe
  operation over the selected release surface.

### Within each phase

1. Complete test tasks and confirm their intended failures where practical.
2. Complete data/schema behavior before services that consume it.
3. Complete services before API/UI integration.
4. Complete UI behavior before manual evidence.
5. Pass the phase's independent test before starting a dependent phase.

## Parallel Opportunities

### Setup

After T001, T002 and T003 can run together.

### Foundation

T004–T011 can be authored in parallel in their named test files. After T012–T014
establish persistence, T015–T018 can integrate the four operation families in
parallel. T019 and T020 are sequential after their tests but independent of
each other.

### User Story 1

```text
Parallel tests: T021, T022, T023, T024, T025
Parallel contract/client groundwork after tests: T026, T030, T031
Then: T027 -> T028 -> T029, and T032 -> T033 -> T034
```

### User Story 2

```text
Parallel first tests: T035, T037, T038, T039
Same-file follow-up after T035: T036
Then: T040
Parallel presentation work: T041, T043
Then: T042 -> T044 -> T045
```

### User Story 3

```text
Parallel tests: T046, T047, T048, T049
Backend: T050 -> T051
Client: T052 -> T053 -> T054 -> T055
```

### User Story 4

```text
Parallel tests: T056, T057, T058
Parallel groundwork: T059 and T060 after their tests
Then: T061 -> T062 -> T063 -> T064
```

### User Story 5

```text
Parallel tests: T065, T066, T067
Backend: T068
Client: T069 -> T070 -> T071
```

### User Story 6

```text
Parallel first tests: T072, T073, T074, T076
Same-file follow-up after T074: T075
Parallel backend/client groundwork: T077 and T078
Then: T079 -> T080 -> T081 -> T082
```

### Cross-story staffing after the MVP

After US1 passes independently, separate contributors can implement US2, US3,
US4, and US5 concurrently because their production tasks are separated by the
named files/behaviors. Coordinate changes to
`CalendarPlanningWorkspace.tsx`, `CourseSchedulePage.tsx`, and `App.css` through
the explicit task order rather than editing those files concurrently.

## Implementation Strategy

### MVP first

1. Complete Setup.
2. Complete Foundational persistence and validation.
3. Complete US1.
4. Stop and run the US1 independent test.
5. Demonstrate one coherent at-a-glance semester workspace before expanding
   interaction breadth.

### Incremental delivery

1. **US1**: coherent semester state and summaries.
2. **US2 + US3**: calendar navigation/filtering/List parity and metric
   traceability; these P1 stories may proceed in parallel.
3. **US4 + US5**: existing correction handoff and Working/Published comparison.
4. **US6**: harden the completed workspace for responsive, accessible, and
   failure-safe use.
5. **Polish**: full regression, performance, visual/reference, scope, and
   moderated evidence.

### Guardrails

- Do not delete or rebuild the existing Courses overview. Adapt it, prove parity,
  keep its separate host usable while evidence is pending, and only then remove
  the separate legacy presentation boundary through T094–T096.
- Do not implement visual-reference controls that are outside the specification.
- Do not add runtime dependencies or architectural layers excluded by
  `plan.md`.
- Do not report manual or moderated criteria as passed without actual evidence.
- Stop at any checkpoint to validate the independently testable story.

## Phase 10: Convergence

- [X] T097 Extend the exam occurrence contract, backend workspace assembly, client types, and session detail with required capacity, assigned-room current capacity, lifecycle context, and focused contract/UI tests in `specs/014-calendar-planning-workspace/contracts/calendar-workspace.openapi.yaml`, `backend/app/schemas/calendar_workspace.py`, `backend/app/services/calendar_workspace.py`, `backend/tests/api/test_calendar_workspace.py`, `backend/tests/services/test_calendar_workspace.py`, `client/src/api/calendarWorkspace.ts`, `client/src/api/calendarWorkspace.test.ts`, `client/src/components/CalendarPlanningWorkspace.tsx`, and `client/src/components/CalendarPlanningWorkspace.test.tsx` per FR-017 and US4/AC2 (partial)
- [X] T098 Preserve an open existing List correction workflow across calendar mode, date, filter, selection, and drilldown changes, or invoke that workflow's established unsaved-change confirmation before unmounting it, with regression tests in `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/DraftSchedulePanel.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx` per FR-049 and the session-correction edge case (contradicts)
- [X] T099 Reconcile selected-session disappearance after edit, deletion, filtering, or coherent refresh by moving focus to a deterministic nearby result or result-set heading and announcing the changed result, with component/page regression coverage in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/pages/CourseSchedulePage.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx` per AR-002 and US6/AC2 (partial)
- [X] T100 Add an understandable per-date total and keyboard-operable continuation path for dense Month dates without clipping or omitting simultaneous sessions, with responsive styling and tests in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, and `client/src/App.css` per RS-003 and the dense-calendar edge case (partial)
- [X] T101 Complete runtime validation of the discriminated calendar-workspace response, including semester and revision identity, workspace token, contexts, section status, every collection and typed reference, facets, metric scopes, and structured problems, with malformed-response coverage in `client/src/api/calendarWorkspace.ts` and `client/src/api/calendarWorkspace.test.ts` per plan: discriminated response contract and TR-008 (partial)
- [X] T102 Complete backend test matrices for all four planning-outcome retention integrations, snapshot-v1/v2 compatibility, revision selection and isolation, Published current validation, metric availability and exact aggregation, and contributor reconciliation in `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_multi_course_generation.py`, `backend/tests/api/test_conflict_aware_generation.py`, `backend/tests/api/test_exam_scheduling.py`, `backend/tests/services/test_schedule_lifecycle.py`, `backend/tests/services/test_calendar_workspace.py`, and `backend/tests/api/test_calendar_workspace.py` per TR-002, TR-005, and TR-011 (partial)
- [X] T103 Complete client test matrices for Week/Day/Month/List navigation, every independent and intersected filter, exact trace/drilldown restoration, teaching/exam action handoff, cancel/failure/stale preservation, coherent request races and recovery, and single-List parity in `client/src/components/calendarWorkspaceUtils.test.ts`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/DraftSchedulePanel.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx`, remediating only failures within FS-014 scope, per TR-003, TR-004, TR-006, TR-007, TR-008, TR-011, and TR-012 (partial)
- [X] T104 Announce successful retry and coherent refresh recovery without unexpected focus movement, clear obsolete failure messaging, and add state-transition tests in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/pages/CourseSchedulePage.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx` per AR-009 and RS-009 (partial)
- [ ] T105 Complete keyboard, supported screen-reader/browser, simultaneous-session, measured contrast, 320-CSS-pixel, 200%-zoom, dense-date, and unobstructed FS-018 navigation validation, remediate FS-014 findings in `client/src/App.css` and workspace components, and record environments and results in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md` per AR-001 through AR-011 and SC-007 through SC-009 (partial)
- [X] T106 Run the required 20-iteration API/browser initial-load, calendar interaction, revision-switch, and successful post-action refresh performance protocol at the reference scale and record percentile/timeout evidence in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`, extending `backend/tests/performance/test_calendar_workspace_performance.py` or client performance instrumentation only where repeatable evidence requires it, per SC-010 through SC-012 (missing)
- [ ] T107 Conduct the moderated acceptance review with at least 10 representative planners or designated reviewers, complete and reconcile every applicable quickstart scenario, record anonymized SC-004 through SC-006 results and the final List/Weekly parity decision in `specs/014-calendar-planning-workspace/checklists/workspace-validation.md`, and remove a separate legacy current-overview host only if all FR-057 parity gates pass while retaining FS-013 historical review per SC-004 through SC-006 and FR-057 (partial)

## Phase 11: Convergence

- [X] T108 Derive one canonical planning-eligible course universe for complete and filtered planning-outcome coverage, exclude visible but ineligible course contexts from the coverage denominator without hiding them from other workspace concerns, and add backend/client tests for eligible-only, ineligible-only, and mixed filtered scopes in `backend/app/services/calendar_workspace.py`, `backend/app/schemas/calendar_workspace.py`, `backend/tests/services/test_calendar_workspace.py`, `client/src/api/calendarWorkspace.ts`, `client/src/components/CalendarPlanningWorkspace.tsx`, and their focused tests per FR-037 and TR-005 (partial)
- [X] T109 Add page-level integration tests for repeated Working/Current Published switching, Draft/Ready same-revision transitions, changed/added/removed occurrences, out-of-order workspace responses, action availability, and calendar-originated teaching edit/delete and exam edit/delete handoff through success, cancel, failure, and stale outcomes; remediate only exposed FS-014 state-coherence defects in `client/src/pages/CourseSchedulePage.tsx`, `client/src/pages/CourseSchedulePage.test.tsx`, and focused workspace tests per US1/AC4, US4/AC3–AC6, US5/AC2, TR-002, TR-007, and TR-008 (partial)
- [X] T110 Enforce the complete discriminated runtime response contract by requiring every named section-status entry, reconciling the selected revision with its matching available context, validating nested exam validity/recommendation fields and all category-specific finding details, and checking conditionally shaped metric values and coverage invariants with malformed-response tests in `client/src/api/calendarWorkspace.ts` and `client/src/api/calendarWorkspace.test.ts` per plan: discriminated response contract and TR-008 (partial)
- [X] T111 Complete traceability tests for dated contributors outside the visible period and undated course, planning-outcome, and validation-finding contributors, including exact List target focus, related conflict linkage, revision preservation, and restoration after clearing drilldown; remediate only exposed FS-014 routing defects in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/DraftSchedulePanel.tsx`, `client/src/components/DraftSchedulePanel.test.tsx`, and `client/src/pages/CourseSchedulePage.test.tsx` per FR-042 through FR-045 and TR-006 (partial)

## Phase 12: Convergence

- [X] T112 Reconcile the validation-status projection and available facets so “No current issue” excludes scheduled and unscheduled course contexts affected by retained failed or stale outcomes while planning-failure and stale-outcome filters continue to include exactly their affected course contexts; replace the contradictory expectation and add independent/intersection coverage in `backend/app/services/calendar_workspace.py`, `backend/tests/services/test_calendar_workspace.py`, `client/src/components/calendarWorkspaceUtils.ts`, and `client/src/components/calendarWorkspaceUtils.test.ts` per FR-023 and TR-004 (contradicts)
- [X] T113 Route the complete Clear filters action through the same drilldown teardown used by Clear drilldown so either path restores the pre-drilldown calendar mode and date anchor while preserving the selected semester, revision, and unrelated context; add direct restoration tests in `client/src/components/CalendarPlanningWorkspace.tsx` and `client/src/components/CalendarPlanningWorkspace.test.tsx` per FR-024, FR-043, and US3/AC6 (contradicts)
- [X] T114 Move focus deterministically into an opened summary drilldown and return it to the initiating summary or a predictable nearby result when the drilldown closes through either clear path, with visible-focus styling and keyboard regression coverage in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/CalendarPlanningWorkspace.test.tsx`, and `client/src/App.css` per AR-002 and US6/AC2 (partial)
