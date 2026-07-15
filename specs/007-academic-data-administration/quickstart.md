# Quickstart Validation: Academic Planning Data Administration

## Purpose

Use this guide after implementation to prove FS-007 end to end without relying on developer-seeded academic records. Lecturer and Room administration remains outside FS-007, so the reference environment must contain at least one existing Lecturer and Room from the FS-001–FS-006 baseline; they are selectable but read-only here.

## Prerequisites

- Python 3.12 environment with `backend/requirements.txt` installed.
- Node/npm environment with `client` dependencies installed.
- A disposable or backed-up SQLite database. Do not run migration validation against the only copy of planner data.
- FS-001 through FS-006 tests passing before FS-007 changes.

## Automated verification

From `backend/`:

```text
python -m pytest tests/api/test_academic_catalog.py tests/services/test_academic_catalog.py tests/db/test_migrations.py
python -m pytest
```

From `client/`:

```text
npm run test
npm run lint
npm run build
```

Expected result: every command exits successfully. Migration tests cover fresh creation, supported legacy upgrades, snapshot backfill, non-blocking normalized-name repair states, current-Semester repair, seed compatibility, unknown-partial-schema diagnostics, and idempotent restart.

## Run locally

Start the backend from `backend/`:

```text
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the client from `client/` with the backend URL configured:

```text
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the Resource Planner and navigate to Academic Data.

## Scenario 1: Build the academic catalog from empty academic data

1. Confirm the Semester, Cohort, Course, and Study Type lists have usable empty states and Create actions.
2. Create Semester `Fall 2026` with valid dates.
3. Create Cohort `AI 1` with a positive whole-number size.
4. Create Study Type `Full-time`, then add at least one valid weekly Time Window.
5. Create Course `Scheduling 101` with units/session preferences, the created Cohort, Study Type, and Semester, plus one existing read-only Lecturer and Room assignment.
6. Leave and return to Academic Data.
7. Return to Schedule and select `Fall 2026`.

Expected:

- All academic records persist.
- `Scheduling 101` is available only for `Fall 2026`.
- No developer seed or restart is needed for the academic records.
- The existing one-course and several-course generation paths can use the new Course.

## Scenario 2: Validate fields, uniqueness, and correction retention

1. Try invalid Semester dates, zero/negative Cohort size, invalid Course units, and a Time Window whose end is not after its start.
2. Try names that differ from existing names only by capitalization or surrounding whitespace.
3. Try an exact duplicate Time Window, then a partially overlapping window.
4. Verify Cohort size and Course total/minimum/maximum units accept positive whole numbers, reject zero/negative/fractional values, and enforce `minimum <= maximum <= total` without an additional FS-007 upper limit.

Expected:

- All detected invalid fields are identified and the entered valid values remain in the form.
- Normalized-name and exact-window duplicates are rejected.
- The partially overlapping Time Window remains allowed.
- Course creation is blocked with actionable feedback if no existing read-only Lecturer or Room option is available; no placeholder resource is created.

## Scenario 3: Preserve saved schedule facts

1. Generate and save a Draft Schedule for `Scheduling 101`.
2. Record its displayed Course name/units, Cohort name/size, Study Type, Semester, session results, and applicable capacity/window validation.
3. Edit each academic source value, including Course name/units, Cohort name/size, and Study Type name.
4. Review the existing saved schedule.
5. Generate a replacement or a new schedule using the current catalog values.

Expected:

- The existing saved schedule retains every recorded academic value and historical validation behavior.
- The new/replaced schedule captures the current values.
- Source edits do not move, delete, or silently rewrite sessions.

## Scenario 4: Reassign a Course

1. Create a second Semester.
2. Reassign `Scheduling 101` to it.
3. Review the earlier Semester and then open new planning for both Semesters.

Expected:

- Earlier saved schedules remain reviewable and editable through established session-edit behavior.
- The Course is available for new planning only in the newly assigned Semester.
- No second simultaneous current assignment exists.

## Scenario 5: Archive without cascading

1. Archive a Cohort or Study Type used by an active Course.
2. Inspect the dependent Course and planning options.
3. Reactivate the parent.

Expected:

- Dependent statuses do not change.
- The dependent remains visible as active-but-unavailable while its parent is inactive.
- Reactivation restores availability when every required relationship is valid.

## Scenario 6: Protected and permitted deletion

1. Inspect usage for a record with dependent records and saved schedules.
2. Attempt deletion.
3. Verify the dialog distinguishes dependent-record and saved-schedule blockers and offers Archive.
4. Create an unused record, inspect usage, confirm deletion, then cancel once and confirm once.

Expected:

- Protected deletion never mutates data and explains blocker types/counts.
- Cancel sends no destructive request.
- Confirmed deletion succeeds only for the unused record.

## Scenario 7: Semester date protection

1. Choose a Semester with saved sessions.
2. Try to narrow its dates so one session falls outside.
3. Expand or safely narrow its dates while all sessions remain inside.

Expected:

- The excluding edit is rejected with saved-session usage feedback and no mutation.
- The safe date edit succeeds.

## Scenario 8: Stale write and refresh failure

1. Open the same record in two browser views.
2. Save in the first, then attempt save/archive/delete from the stale second view.
3. Simulate a planning-option or catalog refresh failure after retaining loaded data.

Expected:

- The stale mutation returns a conflict, preserves the newer record, and keeps the stale form values for review.
- Refresh failure keeps last-known content and selections, shows a warning, and offers Retry.
- No option is silently substituted.

## Scenario 9: Legacy repair and missing-window planning feedback

1. Upgrade supported legacy data containing a Course with no safely inferable current Semester and two records in one named category whose names collide after trimming and case-folding.
2. Confirm startup completes, the records and saved schedules remain usable, and administration visibly identifies both repair conditions.
3. Assign the Course to a Semester and uniquely rename each conflicting record; confirm a new conflicting create or unresolved reactivation is rejected.
4. Archive or remove the final active Time Window for an otherwise eligible Course's Study Type, then open planning and attempt generation.

Expected:

- Legacy repair records remain visible and historical schedules remain usable throughout repair.
- A successfully edited Course has exactly one current Semester, and successfully edited/reactivated named records are unique.
- The Course with no active usable Time Window remains visible in planning as unavailable with `MISSING_ACTIVE_TIME_WINDOW`.
- Generation is blocked with actionable feedback and no default window is invented.

## Scenario 10: Keyboard and responsive validation

1. Complete create/edit/archive/delete flows using only the keyboard.
2. Confirm focus enters and returns from the delete dialog, Escape cancels, and errors/success are announced.
3. Repeat the list/editor flow at the supported narrow layout.

Expected:

- Every action remains operable and clearly labelled.
- The list/editor stacks without hiding required actions or feedback.

## Performance acceptance

Before measuring, record the operating system, CPU, RAM, storage type, browser/version, database type, and build identifier in `specs/007-academic-data-administration/validation/performance-results.md`. Use exactly 100 records of each in-scope type, a warmed application, the local acceptance database, and no artificial network latency.

Run these timed protocols from the planner's activation of the action until the affected UI is usable:

1. Run 20 administration trials spanning ordinary list loads and valid save outcomes. At least 19 of 20 trials must complete within 2 seconds.
2. Run 10 successful catalog-mutation trials that require planning-option refresh. All 10 must show the current option state within 2 seconds.
3. Record every raw duration, pass/fail result, and any excluded run with its reason in the results file.

Expected:

- At least 95% of administration views/save outcomes become usable within 2 seconds.
- A successful catalog change appears in planning choices within 2 seconds.

## Usability acceptance

Record participant role, first-attempt outcome, completion time, and observed blocker—without personally identifying information—in `specs/007-academic-data-administration/validation/usability-results.md`. Use at least 10 representative planner users or acceptance reviewers familiar with the current planner. Give each participant the goal and starting state but no procedural assistance.

For every participant:

1. From empty academic data, create a complete valid Semester, Cohort, Study Type with a Time Window, and Course assigned to the Semester; pass when completed within 5 minutes on the first attempt.
2. Correct a prepared record form containing invalid required values and relationships using only displayed feedback; pass when all issues are corrected on the first attempt.
3. Attempt a protected deletion, identify the blocking reason, and either locate the prerequisite dependent record or choose Archive; pass when completed within 2 minutes without assistance.

Expected: at least 9 of 10 participants pass each protocol, satisfying SC-001, SC-002, and SC-004 independently.
