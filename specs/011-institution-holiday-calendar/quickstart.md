# Quickstart Validation: FS-011 Institution-Wide Holiday Calendar and Avoidance

## Purpose

Validate implementation against [spec.md](spec.md), [data-model.md](data-model.md), and [the HTTP contract](contracts/holiday-calendar.openapi.yaml). This is an end-to-end validation guide, not implementation code or a substitute for test-first tasks.

## Prerequisites

- Prefer a `codex/` feature branch before changing production code.
- Python 3.12 with `backend/requirements.txt` installed.
- Node.js with `client/package-lock.json` installed through `npm ci`.
- A disposable SQLite acceptance database plus a copy of a current FS-008-through-FS-010 database for upgrade testing.
- Tests for each scenario written and shown failing before its production behavior.
- A reference acceptance semester with up to 500 sessions and a calendar with 50 holidays for timing checks.

## Automated verification

From `backend/`:

```text
python -m pytest tests/services/test_holiday_calendar.py tests/api/test_holiday_calendar.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_generation.py tests/services/test_multi_course_generation.py tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py
python -m pytest tests/services/test_draft_schedule_validation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py tests/api/test_conflict_aware_generation.py
python -m pytest tests/performance/test_holiday_calendar_performance.py
python -m pytest
```

From `client/`:

```text
npm test -- holidayCalendar HolidayAdministration ApplicationNavigation AcademicDataPage
npm test -- draftSchedule DraftSchedulePanel BatchResultSummary CourseSchedulePage conflictAwareGeneration
npm test
npm run lint
npm run build
```

## Scenario 1: Clean schema and current-schema upgrade

1. Start with an empty disposable database.
2. Confirm the current schema contains `institution_holidays` and its unique-date and positive-revision constraints.
3. Upgrade a copy of a database at the existing 0004 schema head that contains academic/resource data and saved sessions.
4. Compare all pre/post rows outside the new table.
5. Restart initialization against the upgraded database.

Expected:

- Clean creation and 0004-to-0005 upgrade both succeed.
- No holiday backfill is invented.
- Existing courses, constraints, resources, schedules, and sessions are byte-for-byte equivalent in their stored business fields.
- Repeated initialization is idempotent.
- Unknown partial schemas stop with an actionable unsupported-schema error.

## Scenario 2: Current holiday CRUD and no-history behavior

1. Open Academic Data → Holidays.
2. Create holidays on a past date, a future date, and a valid leap day.
3. Attempt blank/whitespace-only and over-200-character names and an invalid date.
4. Attempt a second holiday on an occupied date.
5. Edit one holiday's date and name.
6. Confirm deletion of another holiday.
7. Reload the API and administration view.

Expected:

- Valid rows appear sorted by date with readable names.
- Invalid values do not change stored state and show field-addressable feedback.
- Duplicate date returns `DUPLICATE_HOLIDAY_DATE` and identifies the date conflict.
- Edit increments revision and only the new date/name remains.
- Delete returns 204 only after confirmation and no current/history row remains.
- No archive, inactive, import-source, or historical-version control appears.

## Scenario 3: Stale and concurrent holiday mutations

1. Open the same holiday in two independent clients.
2. Save a valid edit in the first.
3. Attempt update and delete using the older revision in the second.
4. Concurrently attempt two creates or re-dates to the same unoccupied date.

Expected:

- Older update/delete returns `STALE_REVISION` and cannot overwrite/remove current state.
- Exactly one competing unique-date mutation succeeds.
- The losing mutation returns `DUPLICATE_HOLIDAY_DATE`, not an unhandled server error.
- The client retains entered values and offers current-state review/retry.

## Scenario 4: Single-course hard avoidance and explanations

1. Configure a course with an allowed weekday/window on a maintained holiday and another feasible non-holiday date.
2. Generate the course and inspect saved sessions.
3. Remove the alternate date so the holiday contributes to failure.
4. Add several unrelated holidays outside the course's applicable planning space.

Expected:

- Successful generation uses only the non-holiday date.
- No generated session is saved on a holiday.
- Failure retains the existing primary failure semantics and includes one `INSTITUTION_HOLIDAY` item for each substantiated relevant holiday with correct `holidayDate` and `holidayName`.
- Unrelated holidays do not appear in the explanation.

## Scenario 5: Legacy multi-course hard avoidance

1. Prepare at least two courses with holiday and non-holiday choices.
2. Run the FS-006 batch endpoint.
3. Construct one course that cannot avoid a holiday while another remains feasible.
4. Change the holiday calendar after generation calculation but before persistence.

Expected:

- Every newly saved course session avoids current holidays.
- The blocked/stale course retains its prior draft and shows named holiday/stale-calendar evidence.
- Unaffected course results retain the established independent batch behavior.
- The batch never partially replaces an affected course draft.

## Scenario 6: FS-010 union, reasons, and stale snapshots

1. Prepare optimization with one maintained holiday and one caller-supplied `unavailableDates` value.
2. Confirm that the preparation response echoes only the caller value.
3. Run optimization with otherwise feasible placements on both excluded dates and on an ordinary date.
4. Create two relevant holidays that contribute to remaining units.
5. Add, rename, redate, and delete a relevant holiday between preparation/solve/save in separate trials.

Expected:

- The optimizer excludes the union of both sources.
- `UNAVAILABLE_DATE` remains generic caller evidence; `INSTITUTION_HOLIDAY` includes current name/date.
- A date present in both sources is excluded and reported once as a named holiday.
- Several holidays remain separate reason items and render without duplicate keys.
- Existing complete/partial/unchanged/failed/stale and non-worsening rules remain unchanged.
- A result invalid under refreshed holidays is not saved; affected drafts remain unchanged and the response identifies stale calendar input.
- Removed holidays never persist by being echoed as caller unavailable dates.

## Scenario 7: Existing and manual session alerts

1. Save generated and manual sessions on ordinary dates.
2. Create a holiday on those dates.
3. Rename and redate the holiday onto a different saved session.
4. Manually create/edit a structurally valid session onto a holiday and then move it away.
5. Delete the holiday.

Expected:

- Holiday CRUD never changes any session field or deletes a session.
- Every current matching session shows `INSTITUTION_HOLIDAY` with correct name/date.
- Manual create/edit remains saveable and receives the alert after refresh.
- Rename/redate removes obsolete alerts and adds current alerts.
- Moving a session or deleting the holiday removes the alert when no longer applicable.
- Existing overlap, capacity, eligibility, availability, and window alerts remain visible alongside it.

## Scenario 8: Review presentation and refresh

1. View affected sessions in list and weekly modes with several filters.
2. Switch to Holidays administration without changing the selected semester.
3. Create/edit/delete a holiday that affects the selected semester.
4. Return to Schedule and inspect selection, filters, mode, sessions, and alerts.
5. Repeat with the overview refresh forced to fail, then retry successfully.

Expected:

- Holiday alerts stay attached to correct sessions in both modes and through filters.
- No standalone holiday entry, empty holiday day, or holiday card appears in schedule review.
- The administration view continues to list standalone current holidays.
- Successful mutation refreshes current alerts without requiring the semester to be reopened and preserves user review state.
- Failed refresh retains last-known schedules, warns that data may be stale, and offers retry.

## Scenario 9: No automatic schedule mutation

1. Capture every stored field for sessions on a date about to become a holiday.
2. Create, rename, redate, and delete holidays involving those session dates.
3. Compare the stored sessions after each mutation.

Expected:

- Date, time, units, Lecturer, Room, Cohort, schedule ownership, revisions, and existence remain unchanged solely due to holiday maintenance.
- Only derived alert responses change.
- A later explicit generation may replace sessions only under that generation mode's existing confirmation/replacement rules.

## Scenario 10: Scope and future-import boundary

Inspect schema, API, UI, and dependency changes.

Expected:

- No campus/region calendar, timed closure, exam, provider/source, CSV, iCalendar, synchronization, publication-history, automatic repair, or new dependency is present.
- Holiday stable IDs, unique dates, and revisions remain available for a future FS-017 import design without encoding matching or ownership policy now.

## Performance acceptance

Record operating system, CPU, RAM, storage, browser/version, database type, and build identifier. Use exactly 50 current holidays across multiple years and 500 sessions in one selected semester, including at least 100 holiday collisions and sessions with other alerts.

1. Run 20 warmed holiday list/create/edit/delete trials; at least 19 must become usable within 2 seconds.
2. Run 10 successful holiday mutations affecting the selected semester; all 10 must refresh administration state and affected alerts within 2 seconds without leaving/reopening the semester.
3. Run 20 selected-semester schedule loads; at least 19 must become usable with correct alerts within 2 seconds.
4. Compare single, legacy multi, and FS-010 generation reference timings before/after FS-011 and record any material regression.
5. Store raw durations, failures, and excluded runs with reasons under `specs/011-institution-holiday-calendar/validation/performance-results.md`.

## Usability acceptance

With at least 10 representative planner users or acceptance reviewers familiar with the planner, record role, first-attempt outcome, time, and non-identifying blockers under `specs/011-institution-holiday-calendar/validation/usability-results.md`.

1. Add a named holiday and find it again within 2 minutes.
2. Given a session with a holiday alert, identify the affected session, holiday name, and date within two interactions.
3. Edit and delete a holiday, correctly predicting that sessions remain saved while warnings refresh.

At least 9 of 10 participants must pass each protocol without assistance.

## Regression boundary

Run every existing FS-001 through FS-010 automated test plus representative single-course generation, review, generation constraints, manual editing/creation/deletion, validation alerts, multi-course generation, academic/resource administration, navigation, and conflict-aware optimization flows.

Expected:

- Existing behavior remains usable with empty and populated holiday calendars.
- FS-010 caller-supplied unavailable dates remain supported.
- No generated session uses a current maintained holiday.
- No hidden history or out-of-scope behavior is introduced.
