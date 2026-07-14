# Quickstart: Multi-Course Draft Generation

This guide validates Slice 6 after implementation. It assumes Slices 1-5 are available.

## Prerequisites

- Backend dependencies from `backend/requirements.txt` are installed.
- Client dependencies are installed.
- The reference performance environment uses file-backed SQLite, one FastAPI process, a production client build, a warm start, and no artificial network or database latency.
- Test or seed data includes:
  - at least two Semesters;
  - at least three available Courses;
  - one Course with saved custom constraints;
  - one Course that uses semester and Study Type defaults;
  - one Course whose inputs or windows produce an expected generation failure;
  - at least one same-semester Draft Schedule with a saved manual edit;
  - at least one Course that can be generated in both Semesters;
  - shared lecturer, room, or Cohort data that can produce non-blocking overlap alerts.
  - 50 valid Courses in one Semester for the performance dataset.

The detailed contract is in [contracts/openapi.yaml](./contracts/openapi.yaml), and persistence/concurrency rules are in [data-model.md](./data-model.md).

## Recorded Baseline

Before Slice 6 production changes on 2026-07-13:

- backend: 45 tests passed, with no failures;
- client: 24 tests passed, with no failures;
- client lint: passed;
- client production build: passed.

No pre-existing regression failure was recorded.

## Automated Verification

Run backend verification:

```powershell
cd backend
python -m pytest tests/db/test_migrations.py tests/services/test_draft_schedule_repository.py tests/services/test_multi_course_generation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py
```

Expected backend coverage:

- migration preserves current rows, adds revisions, permits the same Course in different Semesters, and rejects duplicate course-semester Draft Schedules;
- all Draft Schedule repository reads and replacements are semester-specific;
- single-course generation saves Draft Schedule and constraints in one transaction;
- preparation validates `initial` 2-50 and `retry` 1-50 limits and rejects duplicates;
- preparation identifies only selected same-semester replacement targets;
- nonexistent Courses remain prepared/unavailable and later receive course-level failures;
- saved custom constraints and derived defaults are loaded independently per Course;
- preparation and execution use bounded bulk planning-data reads, with query-count or repository-call assertions proving reads do not grow into per-course database loading after the selected input set is loaded;
- all-success, partial-success, and all-expected-failure responses contain exact summary counts and one ordered outcome per Course;
- failed Courses retain their Draft Schedule, sessions, manual edits, and constraints;
- changed Draft Schedule revisions and changed constraint snapshots yield stale course outcomes;
- known stale failures roll back only that Course savepoint while other valid Courses commit;
- an injected unexpected failure rolls back every change from the attempt and returns no success outcomes;
- successful regeneration changes only the selected course-semester and increments its Draft Schedule revision;
- manual session edits increment the parent Draft Schedule revision;
- same-course schedules in other Semesters remain unchanged;
- refreshed semester reads continue returning current Slice 5 validation alerts.

Concurrency verification should use a file-backed test database and separate sessions, or a deterministic repository/orchestration seam. The existing in-memory `StaticPool` fixtures alone do not prove concurrent stale-write handling.

Run frontend verification:

```powershell
cd client
npm run test
npm run lint
npm run build
```

Expected frontend coverage:

- one-course mode preserves current selection, constraint editing, generation, and manual editing behavior;
- several-courses mode keeps its selection separate from the focused Course and local constraint editor;
- initial selection requires 2-50 distinct Courses, prevents a 51st selection, and shows selected count;
- preparation is called with the selected Semester, operation kind, and selected Course IDs only;
- the confirmation dialog lists only selected same-semester replacement targets and explains loss of manual edits;
- cancelling confirmation performs no execution request;
- confirming submits the immutable prepared IDs/revisions once and blocks double submission;
- partial and all-failed results display exact counts, Course identities, and all reasons;
- retry includes failed Courses only and accepts one failed Course;
- retry performs a fresh preparation and replacement confirmation;
- operation-wide failure never displays false per-course successes;
- every normal batch result triggers one selected-semester overview refresh;
- overview refresh shows newly generated and pre-existing schedules plus recalculated alerts;
- a refresh failure preserves the batch result and last known overview and offers refresh retry;
- overview filters/edit state reset after successful batch refresh so new schedules are visible;
- the result summary remains mounted during the current planner session and clears after remount/reload;
- option, constraint, overview, single-generation, preparation, and batch-generation loading/errors remain scoped to the correct action.

## Manual Scenario 1: All Courses Succeed

1. Start the backend and client.
2. Open the planner and choose a Semester.
3. Switch from **One course** to **Several courses**.
4. Select at least two Courses without Draft Schedules in the selected Semester.
5. Confirm the UI states that each Course uses its own saved constraints or defaults and that unsaved one-course editor changes are not included.
6. Start generation.
7. Confirm no replacement dialog appears.
8. Confirm the result shows the correct total with every Course successful.
9. Confirm the Courses overview refreshes and displays all generated schedules.

## Manual Scenario 2: Partial Failure And Retry

1. Select one valid Course and one Course with invalid or insufficient generation inputs.
2. Start generation.
3. Confirm the valid Course succeeds and the invalid Course fails without blocking it.
4. Confirm the failure row identifies the Course and every understandable reason.
5. Correct the failed Course through the existing one-course planning workflow.
6. Choose **Retry failed courses**.
7. Confirm only the failed Course is prepared, even when it is the only retry target.
8. Confirm the previously successful Course is not regenerated.

## Manual Scenario 3: Replacement Confirmation

1. Use a selected Semester containing a manually edited Draft Schedule.
2. Select that Course together with a Course without a schedule.
3. Start generation.
4. Confirm the dialog lists only the Course with the same-semester Draft Schedule and warns that its schedule and manual edits will be replaced.
5. Cancel the dialog.
6. Confirm no generation occurs and every schedule and constraint remains unchanged.
7. Repeat, confirm replacement, and generate.
8. Confirm only successfully regenerated same-semester targets are replaced.

## Manual Scenario 4: Cross-Semester Retention

1. Generate a Course in Semester A.
2. Switch to Semester B and generate the same Course there.
3. Return to Semester A.
4. Confirm the original Draft Schedule and any manual edits remain.
5. Regenerate the Course in Semester B.
6. Confirm only Semester B changes.

## Manual Scenario 5: Stale Draft And Constraint Safety

Use two browser sessions or a controlled test seam.

1. In session A, prepare a selection containing an existing same-semester Draft Schedule and open confirmation.
2. In session B, manually edit that Course's Draft Session.
3. Confirm and execute in session A.
4. Confirm that Course fails with a stale Draft Schedule reason, the newer edit remains, and other valid Courses continue.
5. Prepare another operation in session A.
6. After execution starts, change or clear one selected Course's constraints through session B or the controlled seam.
7. Confirm that Course fails with a stale constraints reason, its newer constraints and existing schedule remain, and other valid Courses continue.
8. Retry either stale Course and confirm preparation/confirmation uses current state.

## Manual Scenario 6: Overview Alerts Remain Non-Blocking

1. Generate Courses whose independent schedules overlap by lecturer, room, or Cohort.
2. Confirm their Course outcomes are successful.
3. Inspect the refreshed semester overview.
4. Confirm affected sessions display the existing Slice 5 validation alerts.
5. Confirm no automatic movement, optimization, or conflict resolution occurred.

## Manual Scenario 7: Transient Result State

1. Complete a partial-success operation.
2. Switch between one-course and several-courses modes, change the focused Course, and temporarily view another Semester.
3. Confirm the result remains available and clearly identifies its original Semester in the mounted planner session.
4. If retrying from another selected Semester, confirm the planner returns to the result Semester before preparing the retry.
5. Reload the page.
6. Confirm the prior batch summary/retry state may be gone while saved Draft Schedules and constraints remain.

## Usability Acceptance Check

1. Recruit at least 10 office staff or designated acceptance reviewers who are familiar with the existing planner and have not been coached on the batch workflow.
2. Starting with no target Semester or batch Courses selected, give every participant the same instruction to generate at least two named first-time Courses in a named Semester.
3. Time each participant from presenting that instruction until they activate **Generate**, and record whether they complete the selection and start within two minutes without assistance.
4. Give every participant the same replacement-identification, failure-identification, conflict-scope, and failed-only retry scenarios without assistance.
5. Record participant-level pass/fail evidence separately for the SC-001 timed start, SC-008 comprehension, and SC-009 retry scenarios.
6. Confirm at least 90% of participants pass each scenario unaided, including completing the SC-001 timed start within two minutes.

## Performance Check

1. Use file-backed SQLite, one FastAPI process, a production client build, and no artificial network or database latency.
2. Seed exactly 50 valid Courses in one Semester and complete one untimed warm-up operation.
3. Run three measured initial generation operations for all 50 Courses.
4. Measure each run from activating **Generate** until the complete result summary is rendered.
5. Record all three durations and confirm their median is at most 10 seconds; confirm every run contains exactly 50 ordered outcomes.
6. Confirm each run performs one post-result semester-overview refresh and no per-course client round trips.

## Operation-Wide Rollback Check

This scenario should be automated with an injected unexpected persistence failure after at least one candidate save.

1. Capture all selected Draft Schedules and constraints before execution.
2. Inject the unexpected failure during persistence.
3. Confirm the response contains one operation-wide failure and no success outcomes.
4. Confirm every selected schedule and constraint matches the pre-operation state.

## Out-Of-Scope Checks

Review the complete Slice 6 implementation diff, not only the orchestration service and planner page, and confirm it does not expose or persist:

- conflict-aware placement or semester optimization;
- automatic conflict resolution;
- persisted batch results or operation history;
- background jobs, polling, or progress streams;
- public holiday avoidance;
- exam scheduling;
- multiple lecturers or eligible rooms per Course;
- individual session creation, deletion, splitting, or merging;
- course-semester eligibility administration;
- dashboard or approval workflow behavior.

## Recorded Slice 6 Verification

Executed on 2026-07-13:

- focused backend verification: 48 passed; no failures;
- full backend regression suite: 68 passed; no failures;
- file-backed 50-Course automated guard: passed the 10-second threshold, returned 50 ordered successful outcomes, and stayed below the bounded SELECT threshold;
- frontend test suite: 34 passed across 8 files; no failures;
- frontend lint: passed;
- frontend production build: passed (Vite 8.1.3).

The automated rollback injection passed: an unexpected failure after the first Course savepoint returned one operation-wide error, no outcomes, and left no attempt-created Draft Schedule or constraint rows.

Scope audit result: the Slice 6 diff adds no conflict-aware placement, optimization, automatic conflict resolution, persistent batch history, background processing, holiday or exam behavior, approval/dashboard workflow, eligibility administration, multiple lecturer/eligible-room behavior, or individual-session CRUD expansion. Existing navigation text and CSS `background` declarations are not feature additions.

The at-least-10-participant unaided usability study and its three measured end-to-end reference-environment runs have not been executed. The protocol above remains the acceptance procedure; no participant pass rate or manual performance median is claimed.
