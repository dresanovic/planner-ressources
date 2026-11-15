---
description: "Dependency-ordered implementation and verification tasks for I-014"
---

# Tasks: I-014 Time-Grid Calendar with Teaching Window Context

**Input**: Design documents in `specs/I-014-time-grid-calender/`: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/interfaces.md](contracts/interfaces.md), [quickstart.md](quickstart.md).

**Prerequisites**: Reviewed specification and plan; constitution 1.2.0 applies. This file schedules implementation; generation of this file does not start it.

**Tests**: Required explicitly by TR-001–006 and the constitution. Write new-behavior tests before production and establish their intended failures. Existing-invariant characterization tests may already pass; record them honestly rather than manufacture failures. Run focused checks after each change. Manual exceptions are exactly those recorded in the plan: real geometry, contrast, AT, genuine enlargement and human comprehension cannot be proven by jsdom alone.

**Organization**: Four story phases in spec priority order. UI keyboard operation and textual facts accompany every increment; US4 completes cross-mode verification. Checkboxes track verified work. T044, T045 and T049 remain open for the explicitly pending observed acceptance matrix; see validation.md.

## Format and Path Conventions

Use `- [ ] Tnnn [P?] [USn?] description with path`. `[P]` denotes independent work in different files within the currently unblocked test batch, not permission to bypass dependencies. Paths are repository-relative. Production stays under `backend/app/` and `client/src/`; tests under `backend/tests/` and colocated client tests. No new project, calendar dependency, endpoint, migration, snapshot format, permission rule or generation/validation algorithm is required.

## Phase 1: Setup

**Purpose**: Establish an isolated, reproducible implementation context using the existing project.

- [X] T001 Record current Git branch/status and existing user changes, then create or use `codex/i-014-time-grid-calendar` before production work without committing/discarding unrelated changes; initialize `specs/I-014-time-grid-calender/validation.md` with the actual branch/revision, scope and pending evidence.
- [X] T002 Check installed compatible Python/Node and locked dependencies against `backend/requirements.txt`, `client/package-lock.json` and `infrastructure/docker/Dockerfile`; use existing environments, install locked dependencies only if missing, and record versions plus a verified disposable database path in `specs/I-014-time-grid-calender/validation.md` following `specs/I-014-time-grid-calender/quickstart.md`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared acceptance fixtures only; no speculative infrastructure. Complete this phase before story work.

- [X] T003 [P] Extend `backend/tests/calendar_workspace_fixtures.py` with reusable I-014 fixture builders for the June 2027 semester, calendar A Saturday 08:00–16:00, Höber, Angelika 26.06.2027 12:15–17:20, in-window/gap/boundary/wholly-outside sessions, zero-session course, calendar B 10:00–18:00, weekly/dated/intensive sources and legacy/current Published variants; use existing test database/auth conventions and existing save/warning semantics.
- [X] T004 [P] Extend `client/src/test/calendarWorkspaceFixtures.ts` with corresponding explicit response fixtures matching `specs/I-014-time-grid-calender/contracts/interfaces.md`, including missing/malformed context, duplicate calendar names with different identities, overlaps and Month dates with 0/1/5/20 entries; preserve old fixtures for adapter compatibility and avoid sharing production layout/precedence calculations as test oracles.

**Checkpoint**: Both fixture sets express the same source facts; no production business behavior has changed.

## Phase 3: User Story 1 - See Sessions Against Permitted Hours (Priority: P1) — MVP

**Goal**: One-calendar Day/Week comparisons with proportional actual time, gaps, readable window context and the complete 80-minute overrun.

**Independent Test**: In Day and Week, inspect the supplied 26.06.2027 session and its 08:00–16:00 window, an in-window 90-minute session, an empty two-hour gap, wholly outside/boundary sessions and concurrent blocks. Exact times and full blocks remain reachable from 00:00–24:00 without opening a warning list.

### Tests first

- [X] T005 [P] [US1] Add service tests in `backend/tests/services/test_calendar_workspace.py` for per-course source contexts including zero-session courses, all semester dates plus outside occurrence dates, bounded date applicability, unchanged old fields/findings and zero saved-record changes after reads; assert the supplied overrun facts without changing existing validation decisions.
- [X] T006 [P] [US1] Add API contract tests in `backend/tests/api/test_calendar_workspace.py` for the additive authenticated workspace response, nullable calendar identity, profile/window/day field shapes, known-empty versus unavailable contexts, no-revision response and unchanged revision/error/auth behavior; assert the existing route rather than add a new endpoint.
- [X] T007 [P] [US1] Add decoder tests in `client/src/api/calendarWorkspace.test.ts` for new fields, unique course/context and local window references, enum/null/date/time constraints, missing-context compatibility, and isolation of malformed teaching-window sections while core sessions remain readable.
- [X] T008 [P] [US1] Create `client/src/components/calendarTimeGridLayout.test.ts` for Day/Week empty-date enumeration, exact minute offsets/72 px-hour scale, preserved break-inclusive interval geometry, stable start/end/ref ordering, endpoint adjacency, lowest-free lanes for three identical/connected overlaps and explanatory outside intervals tied to existing findings; unknown context must yield no invented duration.
- [X] T009 [P] [US1] Create `client/src/components/CalendarTimeGrid.test.tsx` for exact interval placement metadata, full-day reachability, earliest-content/08:00 initial positioning, empty permitted gaps, distinct sessions/windows/unknown states, non-color legend/text, non-hover access and selection callbacks without drag/resize writes; cover exams without applicable teaching-window rules and conditional supported midnight continuations.
- [X] T010 [US1] Run the new checks before production with `.venv/Scripts/python.exe -m pytest tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py` from `backend/` and `npm test -- src/api/calendarWorkspace.test.ts src/components/calendarTimeGridLayout.test.ts src/components/CalendarTimeGrid.test.tsx` from `client/`; record intended failures and passing invariant baselines in `specs/I-014-time-grid-calender/validation.md`.

### Implementation

- [X] T011 [US1] Define additive response models in `backend/app/schemas/calendar_workspace.py` per the contract: course `cohortCalendarRef` is nullable; context `courseRef` is "Exactly one existing workspace course; includes zero-session courses"; calendar identity is "missing identity remains nullable, never guessed from label"; `availability` is "`available`, `unavailable` or `not_applicable`"; `basis` is "`current_working`, `captured_published` or `unavailable`"; `reason` is "Nullable explanation for missing/non-applicable context"; `isCustom`/`sourceRevision` are "nullable when source is unavailable"; planning bounds are "nullable if unavailable". Keep existing required fields and semantics intact.
- [X] T012 [US1] Project source profiles in `backend/app/services/calendar_workspace.py` into per-course contexts before the existing token hash, reusing the exact existing profile construction and unchanged `window_applies`/period comparisons; implement SourceWindow constraints "context-local `windowRef`, nullable `sourceTimeWindowId`, `kind` (`weekly`/`dated`), nullable `weekday`/`date`" with marker/hours/sort order, and day constraints "ISO `date`, `applicableWindowRefs`, and `periodStatus` (`within_period`/`outside_period`)". "Cover every semester date plus occurrence dates outside it"; outside-period refs are empty, source records remain inspectable, and old capture kind/marker defaults stay weekly/false. Reuse the existing route and add no writes or rule changes.
- [X] T013 [US1] Extend `client/src/api/calendarWorkspace.ts` with matching optional-compatible context/course types and bounded section validation: context/window refs are unique in scope and all day refs resolve; "Empty references with available context mean known no applicable teaching hours on that date" and "Missing date coverage is unknown/outside supplied coverage, never permission inferred by the browser". Preserve sound core data on new-section failure and leave existing core failure behavior intact.
- [X] T014 [US1] Implement `client/src/components/calendarTimeGridLayout.ts` pure hourly helpers with constraints "stable sort is start, end, occurrence ref" and "Assign the lowest free lane within each overlap-connected group; intervals meeting only at endpoints can reuse a lane"; use supplied intervals/resolved dates, preserve actual durations and source boundaries, and explain the 80-minute outside portion only as presentation of known facts/existing findings. A paint union must never imply single-window validity or a zero-overrun proof for a non-stitchable finding.
- [X] T015 [US1] Implement `client/src/components/CalendarTimeGrid.tsx` with labeled native sections/buttons and full 24-hour canvases, selectable side-by-side blocks, supplied window backgrounds, hour/date/calendar labels, textual source/hour/finding explanations and unknown/non-applicable states; preserve occurrence identity and select the established detail callback, with no catalog fetch, permission inference, mutation, drag/drop or resizing.
- [X] T016 [US1] Add scoped hourly styles in `client/src/App.css`: initial 72 CSS pixels/hour and 1,728-pixel canvas, border-box proportional blocks without duration-inflating min-height, different permitted/outside colors plus patterns/labels, readable blocks over both, visible focus, sticky identity labels and labeled-scroll-compatible dimensions; ensure short blocks retain accessible full text outside cramped geometry.
- [X] T017 [US1] Integrate Day/Week surfaces into `client/src/components/CalendarPlanningWorkspace.tsx`, passing explicit anchor/range including all seven weekdays, current filtered occurrences and context while retaining existing state/actions/List/summary ownership; keep zero-session selected calendar windows, prompt when no calendar is identifiable and preserve holidays above the timed canvas. Keep unsupported malformed intervals under existing error behavior.
- [X] T018 [US1] Rerun US1 targeted backend/client checks from T010 and measure Day/Week geometry in an actual browser following `specs/I-014-time-grid-calender/quickstart.md`; record the 366-pixel reference block, 96-pixel outside portion at the initial scale, empty gaps, early/late access, overlap selection and existing detail behavior in `specs/I-014-time-grid-calender/validation.md`, with SC-001 pass/fail and limitations.

**Checkpoint**: US1 provides a useful hourly comparison MVP independently of Month. It is not completion of the full I-014 scope.

## Phase 4: User Story 2 - Understand Which Window Applies (Priority: P1)

**Goal**: Correct source/provenance and unambiguous grouping across multiple calendars, differing course profiles and unavailable context.

**Independent Test**: Compare A/B on the same date, a dated-only intensive opportunity and a differing effective course profile; switch Working/Published and fail window refresh. Every state agrees with authoritative existing results; another calendar never extends a session's permission.

### Tests first

- [X] T019 [P] [US2] Extend `backend/tests/services/test_calendar_workspace.py` with dated-intensive suppression of recurring windows, dated non-recurrence, overlapping/adjacent separate sources, course-profile differences, duplicate calendar labels/IDs, captured Published provenance, missing legacy profile/identity, current-validation label preservation and hours/marker/basis/status token coverage without snapshot mutation.
- [X] T020 [P] [US2] Extend `backend/tests/api/test_calendar_workspace.py` for per-course context uniqueness, partial section availability across mixed known/unknown profiles, known-empty arrays, calendar source references from captured identity and unavailable legacy context without live fallback; assert unchanged findings/severity and read-only response behavior.
- [X] T021 [P] [US2] Extend `client/src/components/CalendarPlanningWorkspace.test.tsx` for A/B separation, calendar labels plus differing course-profile subgroups, no guessed merging of duplicate/unknown identities, explicitly selected empty calendars versus no-context prompt, profile source disclosure alongside the custom pane, delayed/retried window failures and no mixed revision data or overwritten unsaved input.
- [X] T022 [P] [US2] Extend restricted-adapter tests in `client/src/components/calendarWorkspaceUtils.test.ts` and `client/src/pages/LecturerReviewPage.test.tsx` to cover absent planner context, assigned-session-only rendering and zero planner-context fetches or planner actions; public review endpoints remain unchanged.
- [X] T023 [US2] Run `.venv/Scripts/python.exe -m pytest tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py tests/services/test_dated_intensive_windows.py tests/services/test_schedule_lifecycle.py` from `backend/` and `npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/pages/LecturerReviewPage.test.tsx` from `client/`; record intended new failures or already-passing characterization results in `specs/I-014-time-grid-calender/validation.md` before related enhancements.

### Implementation

- [X] T024 [US2] Complete any failing provenance/partial-status/token cases in `backend/app/services/calendar_workspace.py`: use current Working profiles and captured Published profiles/identity only, preserve `selectedRevision.validationBasis: current`, default legacy missing metadata to unavailable with reason, and hash the new response facts using the unchanged existing algorithm; never repair business rules or join live windows into missing captured evidence.
- [X] T025 [US2] Complete context-state handling in `client/src/api/calendarWorkspace.ts` and restricted adaptation in `client/src/components/calendarWorkspaceUtils.ts`: absent/malformed sections remain unavailable with retry reason, sound sessions survive, planner-only data is not fetched in restricted mode, and stale/unknown context never becomes available through fallback.
- [X] T026 [US2] Add stable calendar/profile grouping to `client/src/components/calendarTimeGridLayout.ts` and `client/src/components/CalendarTimeGrid.tsx` under the model constraint "Legacy unknown identity remains separately labeled per course; identical names are never merged by guesswork"; use the same scale for groups and label course-specific subgroups when effective contexts differ, without computing window precedence in the browser.
- [X] T027 [US2] Complete inline source/context disclosure, revision/last-known/retry states and custom-pane adjacency in `client/src/components/CalendarPlanningWorkspace.tsx` and the existing `SessionPane.tsx` modal boundary; disclose supplied kind/date/weekday/hours/intensive marker and provenance, retaining distinct source boundaries and selected context without changing established filters, editor protection or correction authority.
- [X] T028 [US2] Rerun T023 plus `npm test -- src/api/calendarWorkspace.test.ts src/components/CalendarTimeGrid.test.tsx` from `client/`, inspect all US2 cases in a browser, and record SC-002 outcome, zero-write/snapshot comparisons and token behavior in `specs/I-014-time-grid-calender/validation.md`; preserve separate unknown/outdated/no-hours/non-applicable labels.

**Checkpoint**: Correct multi-calendar and revision context is independently testable using Day/Week; Month is not needed to establish US2 correctness.

## Phase 5: User Story 3 - Survey a Month and Open Existing Actions (Priority: P2)

**Goal**: Complete compact Month overview with exact overflow and retained date/session/correction/List navigation.

**Independent Test**: A month with empty dates, partial hours and 0/1/5/20 sessions per date shows all dates and entries; overflow counts are exact, hidden findings remain signaled, dates open Day and entries open established detail while filters/revision/List parity persist.

### Tests first

- [X] T029 [P] [US3] Extend `client/src/components/calendarTimeGridLayout.test.ts` with complete Monday-based Month weeks, adjacent-month/year/leap-date labels, chronological tied-start ordering, exact hidden counts and the model constraint "Count affected occurrences once even if they have several window findings"; unrelated validation findings must not create window-specific affected counts.
- [X] T030 [P] [US3] Create `client/src/components/CalendarMonthGrid.test.tsx` for empty day cells, compact actual start/end/title, "first three entries by default", exact `+2`/`+17` overflow for 5/20 entries, expansion/collapse reachability, hidden affected-entry cues and calendar-specific partial/no-hours/unknown/non-applicable disclosure with full accessible names.
- [X] T031 [P] [US3] Extend `client/src/pages/CourseSchedulePage.test.tsx` for Month date-to-Day/session-to-pane callbacks, previous/next/Today/direct-date navigation, filtered identity parity with List, existing edit/save/cancel/unsaved-input confirmation and immutable Published detail; verify calendar navigation/filtering performs no mutation request.
- [X] T032 [US3] Run `npm test -- src/components/calendarTimeGridLayout.test.ts src/components/CalendarMonthGrid.test.tsx src/pages/CourseSchedulePage.test.tsx` from `client/` and record intended failures/current invariant passes in `specs/I-014-time-grid-calender/validation.md` before Month production changes.

### Implementation

- [X] T033 [US3] Implement complete Month date enumeration and stable entry/window-finding count projections in `client/src/components/calendarTimeGridLayout.ts`, retaining existing logical mode range/filter semantics and labeling padding outside supplied coverage instead of deriving permission for it.
- [X] T034 [US3] Implement `client/src/components/CalendarMonthGrid.tsx` with compact timed entries, calendar-specific context disclosure and local expanded-date state; enforce "first three entries by default", exact hidden counts and affected-occurrence counts even when every affected entry is in overflow. Expansion is inline and keeps focus; date activation opens Day and entries select the original occurrence.
- [X] T035 [US3] Add scoped Month styles to `client/src/App.css` for seven-column complete weeks, clearly labeled adjacent-month/empty dates, readable timed entries and persistent overflow/context cues; distinguish partial hours from all-day permission and keep compact entries separate from hourly block styling.
- [X] T036 [US3] Integrate Month callbacks and disclosures in `client/src/components/CalendarPlanningWorkspace.tsx`, using existing date/filter/revision/selection ownership and `client/src/pages/CourseSchedulePage.tsx` pane callbacks where necessary; retain established List, guarded navigation, correction refresh and published immutability without persisting new view state.
- [X] T037 [US3] Rerun T032 plus `npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts` from `client/`; execute Month/List/correction scenarios in `specs/I-014-time-grid-calender/quickstart.md` and record SC-003, view-only zero-write SC-006 results and unchanged existing action semantics in `specs/I-014-time-grid-calender/validation.md`.

**Checkpoint**: All three calendar modes and retained List work through established actions; the crowded-month journey can be demonstrated without relying on hourly layout tests.

## Phase 6: User Story 4 - Compare Hours Accessibly (Priority: P2)

**Goal**: Equivalent usable window/session information across keyboard, assistive technology, removed color, narrow width and enlarged text.

**Independent Test**: Complete the overrun and crowded-month flows using keyboard only; identify date/calendar/source/hour/finding text without color or hover, then repeat at 320 CSS pixels and genuine 200% enlargement with actual assistive-technology observations.

### Tests first

- [X] T038 [P] [US4] Extend `client/src/components/CalendarTimeGrid.test.tsx` for chronological DOM reading order independent of visual lanes, full date/calendar/session/window accessible labels, decorative backgrounds without duplicate announcements, native activation and labeled keyboard-scroll regions without unsupported ARIA grid behavior.
- [X] T039 [P] [US4] Extend `client/src/components/CalendarMonthGrid.test.tsx` for keyboard source disclosure, exact hidden-entry/finding announcements, expansion focus preservation, non-hover full text and date/session activation across empty/crowded cells.
- [X] T040 [P] [US4] Extend `client/src/components/CalendarPlanningWorkspace.test.tsx` and `client/src/pages/CourseSchedulePage.test.tsx` for logical focus return after pane/disclosure close, disappeared-session fallback, unsaved editor preservation across narrow pane presentation and keyboard-operable mode/date/filter/actions with required information available in calendar itself.
- [X] T041 [US4] Run `npm test -- src/components/CalendarTimeGrid.test.tsx src/components/CalendarMonthGrid.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/pages/CourseSchedulePage.test.tsx` from `client/`; record any newly exposed failures in `specs/I-014-time-grid-calender/validation.md` before fixes, retaining existing passing accessibility tests.

### Implementation and acceptance

- [X] T042 [US4] Complete keyboard semantics, source labels, announcements and logical focus restoration in `client/src/components/CalendarTimeGrid.tsx`, `client/src/components/CalendarMonthGrid.tsx` and `client/src/components/CalendarPlanningWorkspace.tsx`; retain native Tab/Shift+Tab, Enter/Space and scroll keys, no hover-only information and no added composite-grid shortcut system. Rerun T041 after fixes.
- [X] T043 [US4] Complete responsive/text-enlargement/focus/contrast presentation in `client/src/App.css` for 320 CSS pixels and 200% text enlargement, retaining access to all modes/date/calendar labels, dense overlaps and native scroll areas without overlapping surrounding controls or changing actual block duration.
- [ ] T044 [US4] Run actual browser keyboard, removed-color, wide/narrow/200%-text and assistive-technology scenarios from `specs/I-014-time-grid-calender/quickstart.md`; save screenshots/measurements under `specs/I-014-time-grid-calender/verification/` and record browser/AT versions, contrast/read-order/focus observations and SC-005 outcomes in `specs/I-014-time-grid-calender/validation.md`. Explicitly retain missing observations as pending acceptance.
- [ ] T045 [US4] Conduct the five-representative-planner SC-004 trial from `specs/I-014-time-grid-calender/quickstart.md` and record anonymized per-case times/answers in `specs/I-014-time-grid-calender/validation.md`; at least four must identify overrun/duration, in-window session, empty permitted gap and correct calendar within 30 seconds per case without first opening a warning list. Missing participants or failed criteria remain unresolved acceptance, never agent-inferred passes.

**Checkpoint**: Automated accessibility assertions supplement actual browser/AT/human evidence; pending manual evidence is visible and does not imply full acceptance.

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Complete the concrete regression/contract gates and reconcile actual evidence; no unrelated optimization, refactoring or security project.

- [X] T046 [P] From `backend/`, run `.venv/Scripts/python.exe -m pytest tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py tests/services/test_dated_intensive_windows.py tests/services/test_draft_schedule_validation.py tests/services/test_schedule_lifecycle.py`, then `.venv/Scripts/python.exe -m pytest tests/performance/test_calendar_workspace_performance.py`, then `.venv/Scripts/python.exe -m pytest tests`; record exit codes/results and unchanged scheduling/validation/availability/snapshot outcomes in `specs/I-014-time-grid-calender/verification/backend-results.md`.
- [X] T047 [P] From `client/`, run `npm test -- src/api/calendarWorkspace.test.ts src/components/calendarTimeGridLayout.test.ts src/components/CalendarTimeGrid.test.tsx src/components/CalendarMonthGrid.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/pages/CourseSchedulePage.test.tsx src/pages/LecturerReviewPage.test.tsx`, then `npm test`, `npm run build` (includes TypeScript), and `npm run lint`; record exit codes/results in `specs/I-014-time-grid-calender/verification/client-results.md`.
- [X] T048 Compare serialized backend responses and frontend fixture expectations against `specs/I-014-time-grid-calender/contracts/interfaces.md`, covering every enum/null/reference/date invariant and source/provenance case; inspect the production diff for prohibited business logic/persistence/public-review access changes, run `git diff --check` from root, and record the cross-stack/scope result in `specs/I-014-time-grid-calender/validation.md` without modifying unrelated user work.
- [ ] T049 Complete remaining end-to-end `specs/I-014-time-grid-calender/quickstart.md` scenarios against the isolated database, including all calendar modes/List, stale/partial failure/retry, viewing zero-write fingerprints and existing correction/publication rules; record SC-001–006 coverage and any remaining failures in `specs/I-014-time-grid-calender/validation.md`, reusing T018/T028/T037/T044/T045 evidence rather than rerunning unchanged checks without cause.
- [X] T050 Reconcile implemented facts and any discovered corrections into `specs/I-014-time-grid-calender/spec.md`, `specs/I-014-time-grid-calender/plan.md`, `specs/I-014-time-grid-calender/contracts/interfaces.md` and `specs/I-014-time-grid-calender/quickstart.md`; scope/behavior changes must update the spec before related production edits, and the built-in `specs/I-014-time-grid-calender/checklists/requirements.md` stays reviewer-owned quality evidence rather than an implementation checkbox target.
- [X] T051 Finalize `specs/I-014-time-grid-calender/validation.md` with actual branch/revision/diff identity, backend/client/contract results, manual/human evidence and residual limitations; mark tasks in `specs/I-014-time-grid-calender/tasks.md` complete only when their required evidence exists, leaving failed or unavailable acceptance tasks unchecked and reporting them without claiming full delivery.

## Dependencies & Execution Order

```text
T001 -> T002 -> (T003 || T004)
  -> US1: T005–T009 tests -> T010 red evidence -> T011–T017 -> T018 verification
  -> US2: T019–T022 tests -> T023 red evidence -> T024–T027 -> T028 verification
  -> US3: T029–T031 tests -> T032 red evidence -> T033–T036 -> T037 verification
  -> US4: T038–T040 tests -> T041 red evidence -> T042–T043 -> T044/T045 acceptance
  -> T046 || T047 -> T048 -> T049 -> T050 -> T051
```

### Phase and task dependencies

- Phase 1 precedes shared fixtures; Phase 2 blocks all story implementation. Fixtures do not replace the story-specific tests.
- US1 starts without another story. Schema T011 precedes projection T012; decoder T013 and layout T014 precede surface T015; styles T016 and integration T017 follow their new surface. Each production change depends on its relevant tests plus red-evidence task.
- US2 reuses US1's context contract/hourly surface, then independently proves multi-calendar and provenance correctness. T024/T025 precede grouped integration T026/T027. Existing authoritative dated precedence is consumed unchanged even before US2's expanded cases.
- US3 reuses the established context/selection interface; it can be tested as a compact Month increment, but follows US2 in this plan to avoid editing the same workspace/style/helper files concurrently. T033 precedes T034; T035/T036 follow component creation.
- US4 completes end-to-end accessibility across all three modes. Baseline keyboard/non-color facts must not be deferred from earlier stories. T042/T043 follow the relevant failing checks; T044 depends on these fixes. T045 requires a usable integrated build and actual participants, not browser automation.
- Final automation T046/T047 can run once production changes are stable even if human/AT observations are pending. Pending T044/T045 does not prevent collecting regressions, but prevents claiming their acceptance outcomes or checking their tasks off. T048 depends on both final automated result sets. T049 reuses completed observations and records gaps; T051 may finalize an honest incomplete report while unavailable tasks remain unchecked.
- Same-file edits are sequential, including all edits to `validation.md`. Parallel result tasks T046/T047 use different result files, merged by the later reconciliation tasks. If later corrections change production, rerun affected tests and final gates before claiming completion.

### Parallel opportunities and examples

Parallelism below is an execution option, not a requirement to spawn agents.

| Phase/story | Example independent batch | Barrier |
| --- | --- | --- |
| Foundation | T003 backend fixtures and T004 client fixtures | T001–T002 complete |
| US1 | T005 service tests, T006 API tests, T007 decoder tests, T008 layout tests, T009 surface tests | Fixtures complete; all precede T010 |
| US2 | T019 service tests, T020 API tests, T021 workspace tests, T022 adapter/restricted page tests | US1 verified; all precede T023 |
| US3 | T029 layout tests, T030 Month tests, T031 page workflow tests | US2 verified; all precede T032 |
| US4 | T038 hourly semantics tests, T039 Month tests, T040 workspace/page focus tests | US3 verified; all precede T041 |
| Final checks | T046 backend results and T047 client results | Production stable; disjoint evidence files |

## Implementation Strategy

### MVP first

Complete T001–T018 to demonstrate US1: Day/Week show actual timing, empty permitted gaps and the complete supplied 80-minute overrun using authoritative read-only window facts. Preserve established detail and baseline accessible text from this first increment. Verify the MVP before broadening presentation; it does not replace the confirmed Month/multiple-calendar/accessibility scope.

### Incremental delivery

Proceed US1 -> US2 -> US3 -> US4, verifying each independently. Keep new schema/data projection minimal and current backend rules untouched. No deployment, commit or publication is implied by task generation. After the final production change, complete the concrete backend/client/contract gates and observed acceptance. Record missing checks explicitly rather than reducing scope or inventing evidence.

## Coverage and Review Notes

| Requirement group | Main tasks and evidence |
| --- | --- |
| FR-001–004: modes, time geometry, scroll, overlaps | T008–T018, T029–T037, T044 |
| FR-005–009: accessible permission context, correct sources/calendars, complete sessions/gaps | T005–T018, T019–T028, T038–T044 |
| FR-010–012: compact Month/overflow/navigation | T029–T037, T039–T044 |
| FR-013–015: revision/filter/action preservation and no writes | T005–T007, T012–T013, T019–T028, T031–T037, T048–T049 |
| FR-016–018: keyboard/textual/responsive | Baseline T009/T015–T017/T030/T034; completion T038–T045 |
| FR-019–020: failure states and presentation-only boundaries | T007/T013, T019–T028, T046–T049 |
| TR-001–006: test-first, visual/manual and cross-stack gates | Red-evidence T010/T023/T032/T041; story checks and T044–T051 |
| SC-001–003 | T018, T028, T037 plus integrated T049 |
| SC-004–005 | T044–T045 with actual observations/participants |
| SC-006 | No-write characterization and T037/T046/T048–T049 |

Task count: 51 total — Setup 2, Foundation 2, US1 14, US2 10, US3 9, US4 8, final verification/reconciliation 6. No specification-quality checkbox denotes implementation completion. No extension configuration exists at generation time; before/after-task hooks are absent.

## Phase 8: Convergence

- [X] T052 Add failing regression cases in `client/src/components/CalendarPlanningWorkspace.test.tsx` for an explicitly selected calendar with known windows and zero sessions after room, session-type or validation filtering, then update context-course selection in `client/src/components/CalendarPlanningWorkspace.tsx` so Day/Week/Month retain that calendar's known per-profile windows independently of the occurrence projection; preserve session/List filter parity and avoid borrowing another calendar's permission. Run `npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/components/CalendarTimeGrid.test.tsx src/components/CalendarMonthGrid.test.tsx` from `client/`, plus relevant build/lint gates, and record the result in `specs/I-014-time-grid-calender/validation.md` per FR-014, T017, T021, T026 and T036 (partial)
- [ ] T053 Complete the outstanding T044 actual assistive-technology, genuine 200% text-enlargement and removed-color walkthroughs from `specs/I-014-time-grid-calender/quickstart.md`, including keyboard/focus/read-order/contrast observations across the required modes and dense cases; retain relevant existing observations, record actual browser/AT versions and results in `specs/I-014-time-grid-calender/validation.md`, and save supporting evidence under `specs/I-014-time-grid-calender/verification/`; leave unavailable observations explicitly unresolved per SC-005, TR-005 and T044 (partial)
- [ ] T054 Conduct the outstanding five-representative-planner trial and record anonymized per-case times and answers in `specs/I-014-time-grid-calender/validation.md`, checking that at least four identify the overrun/duration, in-window session, empty permitted gap and applicable calendar within 30 seconds per case without first opening a warning list; do not substitute agent judgments or automated checks for participants per SC-004 and T045 (missing)
- [ ] T055 Complete the remaining isolated-database end-to-end acceptance matrix after the convergence correction and observed trials, reusing valid existing evidence while covering unresolved stale/partial-context retry, mode/List/filter parity, correction/publication protections and view-only zero-write results; reconcile actual SC-001-006 outcomes and remaining limitations in `specs/I-014-time-grid-calender/validation.md` without claiming full acceptance while evidence is missing per SC-006 and T049 (partial)

## Phase 9: Convergence

- [ ] T056 Complete the unresolved actual assistive-technology, genuine 200% text-enlargement and removed-color walkthroughs from T044/T053 across the required calendar modes and dense cases; record actual browser/AT versions, keyboard/focus/read-order/contrast results in `specs/I-014-time-grid-calender/validation.md` and supporting observations under `specs/I-014-time-grid-calender/verification/`, retaining unavailable checks as unresolved rather than inferring acceptance from DOM tests per TR-005, SC-005 and US4/AC1–4 (partial)
- [ ] T057 Conduct the outstanding five-representative-planner trial from T045/T054 and record anonymized per-case answers and elapsed times in `specs/I-014-time-grid-calender/validation.md`; verify at least four participants identify the overrun/duration, in-window session, empty permitted gap and applicable calendar within 30 seconds per case without first opening a warning list, and retain failed or unavailable participant evidence explicitly per SC-004 (missing)
- [ ] T058 Complete the remaining isolated-database end-to-end acceptance and reconciliation from T049/T055 after the pending observations, reusing valid evidence for mode/List/filter parity, stale/partial-context retry, correction/publication protections and view-only zero-write fingerprints; record actual SC-001–006 outcomes and residual limitations in `specs/I-014-time-grid-calender/validation.md` without claiming full acceptance while evidence remains missing per SC-006 and T049/T055 (partial)

## User-requested calendar simplification — 15.11.2026

- [X] T056 Replace empty-calendar presentation expectations with regressions for empty dates, Month cohort labels and date-local populated columns; remove the duplicated Day/Week overview and Month window placeholders. Keep all dates visible, using one empty column when no cohort has matching sessions. Supersedes T052's empty-calendar window-display requirement.
- [X] T057 Add checkbox cohort subsets to the shared projection, combined with lecturer and other filters; retain selection across modes, reconcile refreshed facets, and support All/reset and Escape. Test cohort identity separately even when calendars/profiles are shared.
- [X] T058 Run focused regressions, client suite, build, lint and scoped code review. Broader observed acceptance tasks remain separate; see verification/calendar-simplification-review.md.
