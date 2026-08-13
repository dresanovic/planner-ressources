# Quickstart Validation: Planner-Controlled Schedule Regeneration Decision

## Purpose

Use this guide after implementation to prove the FS-023 workflow end to end. It
validates provisional generation, factual comparison, atomic acceptance,
non-mutating cancellation, stale/one-time protection, direct save, accessibility,
and regression boundaries. It does not replace the automated test suites.

Relevant design artifacts:

- [Implementation plan](plan.md)
- [Data model](data-model.md)
- [API contract](contracts/planner-regeneration.openapi.yaml)
- [UI contract](contracts/planner-regeneration-ui.md)

## Prerequisites

- Implementation and validation run from an isolated FS-023 feature
  branch/worktree with no unrelated changes in files named by `tasks.md`.
  Record the branch name, commit, and baseline `git status --short` before TDD
  work begins.
- Python 3.12 with `backend/requirements-dev.txt` installed.
- Node/npm with `client/package.json` dependencies installed.
- A disposable SQLite database or equivalent isolated test database.
- An active editable Working revision for a semester.
- Representative planner data containing:
  - at least two selected courses;
  - one selected course with saved teaching sessions, including a manual edit;
  - one selected course with no teaching schedule;
  - one unselected saved teaching schedule as fixed occupancy;
  - an active exam and a past exam;
  - institution holidays, availability, capacity, and eligible resources;
  - a current selected schedule with a known active constraint warning for the
    lower-coverage comparison scenario.

Do not run destructive acceptance scenarios against production planning data.

## 1. Run focused automated checks first

From the repository root:

```powershell
python -m pytest backend/tests/services/test_semester_optimization.py backend/tests/services/test_conflict_aware_generation.py
python -m pytest backend/tests/api/test_conflict_aware_generation.py backend/tests/services/test_conflict_aware_generation_concurrency.py
python -m pytest backend/tests/performance/test_semester_optimization_performance.py
```

From `client/`:

```powershell
npm test -- src/api/conflictAwareGeneration.test.ts src/components/ReplacementConfirmationDialog.test.tsx src/components/BatchResultSummary.test.tsx src/pages/CourseSchedulePage.test.tsx
npm run lint
npm run build
```

Expected: every command succeeds. The tests must include failing-first evidence
for the new behavior before production changes are made. The performance test
must measure the workflow-level preview, direct-save, and actionable no-result
paths, not only the optimizer function, and at least 95% of representative
one-to-twenty-course runs must finish within thirty seconds.

## 2. Provisional mixed-selection generation

1. Open the active Working revision in Schedule Planning.
2. Select the course with saved/manual sessions and the previously unplanned
   course.
3. Capture current schedule identities, revisions, session values, and current
   PlanningOutcome rows.
4. Start generation.

Expected:

- No pre-generation replacement dialog appears.
- A post-generation comparison opens only after one hard-valid joint alternative
  exists.
- Database/current schedule reads still return exactly the captured schedules,
  revisions, sessions, and outcomes.
- The comparison shows complete-selection and per-course current/generated
  required, scheduled, remaining, and complete/partial facts.
- Resolved current warnings and generated remaining reasons appear on the correct
  course/side.
- The comparison states that accepting replaces all selected saved sessions,
  including planner-created/edited work.
- The only decision actions are `Neu erzeugten Stundenplan übernehmen` and
  `Abbrechen`; no per-course choice or reason field is present.

## 3. Accept a valid lower-coverage partial alternative

Use a dataset where the current warned schedule has more teaching units than the
hard-valid generated alternative.

1. Generate the provisional alternative.
2. Confirm the generated side is marked partial and its remaining reasons are
   visible.
3. Choose `Neu erzeugten Stundenplan übernehmen`.

Expected:

- The lower-coverage valid candidate is selectable.
- Every selected existing/new/zero-session course result commits together.
- No generated lecturer, room, or cohort overlap exists against selected
  teaching, unselected teaching, or active exams.
- All other hard rules remain satisfied, including holidays, dates/windows,
  availability, capacity, eligibility, and same-course active-exam boundary.
- Manual/current selected sessions were replaced only after acceptance.
- The accepted result matches the preview fingerprint exactly.
- Reusing the old prepared evidence is rejected because saved draft revisions
  changed.
- Established saved generation outcomes describe the accepted schedules but no
  accept/reason/decision-history record exists.

## 4. Cancel and dismiss without mutation

Repeat provisional generation from a clean baseline for each path:

- choose `Abbrechen`;
- press Escape;
- use the accessible close control;
- navigate away from the unresolved comparison.

Expected for every path:

- The complete unsaved preview and fingerprint are removed from client state.
- No backend cancellation or cleanup request is sent because preview stored no
  server state.
- All selected and unselected schedules, revisions, constraints, exams, and
  PlanningOutcomes remain unchanged.
- Current warnings remain; no automatic repair, movement, or deletion occurs.

## 5. Reject every stale input category

Generate a fresh comparison, then change one relevant input before acceptance.
Repeat for:

- active Working revision state or row version;
- selected draft/session identity or revision;
- unselected protected teaching occupancy;
- active exam occupancy or same-course exam boundary;
- course, semester, study-type window, or date constraint;
- holiday or planner unavailable date;
- lecturer/room eligibility, activity, availability, or assignment facts;
- cohort or room capacity.

Expected in each run:

- Acceptance returns an actionable stale response and directs regeneration.
- No course result is partially saved.
- The old prepared evidence/fingerprint is removed from client state.
- Changing only a past exam follows established I-003 semantics and does not by
  itself make the candidate stale.

## 6. Prove atomicity and at-most-once behavior

Automated concurrency tests are authoritative; supplement them manually if the
environment supports concurrent requests.

1. Make persistence fail after at least one selected replacement is attempted.
2. Verify the transaction rolls back every selected schedule and outcome.
3. Send two simultaneous acceptance requests for one prepared preview.
4. Send the acceptance request again after a successful commit.

Expected:

- A persistence failure saves no selected course; the client preview remains
  usable only while its prepared snapshot is still fresh.
- Exactly one concurrent request can commit.
- Later requests fail freshness validation because draft revisions changed and
  change nothing.
- Refreshing schedules after a lost success response reveals the accepted result.

## 7. Verify direct save and no-result paths

### Wholly unplanned selection

Select only courses with no saved teaching sessions and generate a valid complete
or partial result.

Expected: the result saves directly through the existing workflow and no
comparison preview appears.

### No valid non-empty alternative

Use constraints that permit no generated session for the complete selection.

Expected: no preview or empty draft is created, current schedules remain
unchanged, and course-specific actionable blocking reasons appear.

## 8. Verify accessibility and responsive presentation

Perform keyboard-only review at normal zoom and at 200% text zoom:

1. Open the comparison from the generation control.
2. Confirm focus enters the dialog and background controls cannot be reached.
3. Tab and Shift+Tab through all enabled controls.
4. Inspect long course names and multiple reasons at a narrow supported viewport.
5. Cancel, reopen, and accept.

Expected:

- Dialog title, description, course groups, current/generated sides, statuses,
  warnings, and actions have programmatic associations.
- Focus wraps within the dialog and returns logically when it closes.
- Escape cancels unless acceptance is in flight.
- Course and side association remains clear without color and when facts stack.
- No horizontal page overflow hides content; both actions remain reachable.

The FS-023 product owner owns recruitment and evidence collection for the SC-008
review with at least five representative planner users. At least 90% must
identify the validity/coverage trade-off and complete their intended decision
unaided in under two minutes on the first attempt. Record anonymized task
completion, duration, errors, and result only; do not add product decision
history. Automated implementation may complete before this review, but FS-023
is not release-ready until the threshold passes.

## 9. Run complete regression suites

From the repository root:

```powershell
python -m pytest backend/tests
```

From `client/`:

```powershell
npm test
npm run lint
npm run build
```

Expected: manual teaching management, exam scheduling, lifecycle/publication,
Calendar workspace, resources, academic data, conflict warnings, and wholly
unplanned direct generation remain green.

## Evidence record

Implementation baseline:

- branch: `codex/I-004-planner-controlled-schedule-regeneration-decision`;
- base commit: `bbc6d6e`;
- implementation started from a clean isolated checkout of the feature branch;
- baseline status contained only the approved `.specify/feature.json` pointer and
  untracked FS-023 specification artifacts;
  no unrelated production-file changes were present.

Before commit, record:

- branch and commit under test;
- database engine used for transaction/concurrency checks;
- backend/client command results;
- concurrency outcome;
- reference generation durations and workload size;
- keyboard/zoom/browser combinations;
- usability-review participant count, pass rate, and median time;
- any unrun check with exact reason, affected requirement/success criterion, and
  residual risk.

## Automated implementation evidence — 2026-08-12

- Branch/base: `codex/I-004-planner-controlled-schedule-regeneration-decision`
  at `bbc6d6e`.
- Database: disposable in-memory and file-backed SQLite; the file-backed
  simultaneous-accept test committed exactly one request and rejected the
  competing request as stale.
- Focused backend service/API/concurrency suite after final no-result diagnostics:
  92 passed.
- Acceptance concurrency suite: 1 passed.
- Workflow performance cases for direct save, replacement preview, and
  actionable no-result: 3 passed; each used 20 fresh measured runs across
  repeated 1-, 5-, 10-, 15-, and 20-course workloads, and at least 19/20 runs
  completed within 30 seconds. Together with the 20-course optimizer reference,
  the corrected performance suite passed 4 tests in 269.70 seconds.
- Complete backend suite: 470 passed in 239.70 seconds. Existing deprecation
  warnings remain unrelated to FS-023.
- Complete client suite: 383 passed; focused page suite after the final
  navigation-discard and no-result guidance adjustments: 53 passed.
- Review-correction client API/page suite: 63 passed.
- Consolidated-branch verification after merging the Schedule workspace tab
  separation with FS-023: 92 focused backend tests and 387 complete client tests
  passed; client lint and production build also passed.
- Client lint: passed. Client production build: passed.
- Command adjustment: backend tests were run from `backend/` with
  `..\.venv\Scripts\python.exe -m pytest ...` so the local `app` package was on
  the import path. Client tests used `npm run test -- --run ...`.
- Not run: the product-owner five-planner usability study, manual browser
  keyboard/200%-zoom/narrow-layout review, and anonymized SC-008 evidence
  collection. These remain the T026 release-readiness gate; automated
  implementation completion does not claim that gate has passed.
