# Quickstart Validation: FS-009 Manual Session Management

This guide verifies the FS-009 behavior end to end without covering FS-008 resource eligibility, generation optimization, or later calendar-workspace features.

## Prerequisites

- Python 3.12 environment with `backend/requirements.txt` installed.
- Node.js and the locked dependencies from `client/package-lock.json`.
- Seed or fixture data containing:
  - one active course assigned to a semester, lecturer, cohort, study type, and default room;
  - at least one additional room above cohort capacity and one room below capacity;
  - saved generation constraints for the target course-semester;
  - another course draft in the same semester and another draft for the target course in a different semester;
  - sessions that can produce overlap and window alerts.

## Automated Verification

Run focused backend tests first:

```powershell
Set-Location backend
python -m pytest tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py tests/services/test_draft_schedule_validation.py
```

Run focused client tests:

```powershell
Set-Location client
npm test -- src/api/draftSchedule.test.ts src/components/DraftSchedulePanel.test.tsx src/components/ScheduleDeletionDialog.test.tsx src/pages/CourseSchedulePage.test.tsx
```

Before commit, run complete verification:

```powershell
Set-Location backend
python -m pytest
Set-Location ../client
npm test
npm run lint
npm run build
```

## Scenario 1: Create a First Manual Session

Focused automated evidence (2026-07-16): repository/API/planning-option tests passed for first and partial creation, snapshot inheritance, capacity and structural rules, current remaining-unit enforcement, rollback, saved-constraint preservation, and related-session alert refresh. Client API, calculation, and page tests passed for typed mutation handling, default end times, earlier/later overrides, capacity-valid rooms, progress, announcements, and refresh without filter reset.

1. Select a course-semester with no Draft Schedule.
2. Confirm the selected-course Planning Summary shows zero scheduled units and all course units remaining.
3. Open manual creation and enter a date, start time, whole-unit count, and capacity-valid room.
4. Verify start time plus units produces the expected default end time using 45 minutes per unit and 10 minutes between units.
5. Save the session.

Expected:

- One Draft Schedule and one session exist only for the selected course-semester.
- The session inherits the course lecturer and cohort and uses the selected room.
- Scheduled units equal the new session units; remaining units decrease by exactly that amount.
- Saved generation constraints are unchanged.

## Scenario 2: Override End Time and Complete a Partial Draft

1. Open manual creation for a partial draft.
2. Change start time or units and observe end time recalculate.
3. Move end time later to represent an unplanned pause; save and verify units do not change.
4. Repeat with an earlier end time representing merged teaching units.
5. Add a final session whose units equal the remaining units.

Expected:

- Each override is retained when its end remains later than its start.
- Units, not elapsed duration, drive scheduled and remaining values.
- Existing sessions are not replaced or moved.
- The completed course shows zero remaining units.

## Scenario 3: Verify Hard Rules and Non-Blocking Alerts

Attempt manual creation separately with:

- a date outside the semester;
- zero, fractional, or more-than-remaining units;
- end time not later than start time;
- a duplicate date in the same course draft;
- a missing room or room below cohort capacity.

Expected: each attempt is rejected with an understandable reason and leaves the prior draft, progress, alerts, source data, and constraints unchanged.

Then create a structurally valid session that overlaps a lecturer, room, or cohort session or lies outside an active/default teaching window.

Expected: the session is saved and all applicable established alerts appear after the overview refresh.

## Scenario 4: Delete One Session

Focused automated evidence (2026-07-16): repository and API tests passed for atomic identity/revision claims, one-of-many deletion, last-session parent cleanup, over-scheduled progress, saved constraints, nullable mutation results, and `409 STALE_DRAFT` for missing or changed confirmed targets. Client API, dialog, overview, and page tests passed for exact query parameters, cancellation, list/weekly Delete actions, accessible consequence content, success refresh, stale refresh, and renewed confirmation.

1. Request deletion of one session from a multi-session draft.
2. Verify the confirmation identifies the session, course, semester, units removed from scheduled coverage, and the resulting remaining-unit count.
3. Cancel and confirm no state changes.
4. Request again and confirm.

Expected:

- Only the selected session is deleted.
- Scheduled units decrease by its exact units and remaining units are recalculated from the resulting schedule; for a pre-existing over-scheduled course, the displayed remainder may stay at zero until enough scheduled coverage is removed.
- Related alerts on surviving sessions refresh.
- Source records and generation constraints remain unchanged.

## Scenario 5: Delete the Last Session

1. Request deletion of the only session in a course-semester draft.
2. Verify the confirmation explains that the draft becomes empty.
3. Confirm deletion.

Expected:

- The session and parent Draft Schedule no longer exist.
- The course remains visible with zero scheduled and all units remaining.
- No empty or “Cleared” Draft Schedule is retained.

## Scenario 6: Clear One Complete Course Draft

Focused automated evidence (2026-07-16): repository and API tests passed for complete ORM parent/session deletion, no empty draft, full remaining units, cross-course and cross-semester isolation, source/constraint preservation, nullable mutation results, and stale rollback. Client contract, dialog, and page tests passed for exact query parameters, session-count/full-remainder consequences, preservation copy, cancellation, disabled no-draft state, success refresh, and renewed confirmation after stale failure.

1. Prepare a target draft with generated, manually edited, and manually created sessions.
2. Request complete deletion.
3. Verify the confirmation lists course, semester, session count, resulting remaining units, and preservation of source records/constraints.
4. Cancel once and verify no change; request and confirm again.

Expected:

- Only the selected course-semester Draft Schedule and all of its sessions are deleted.
- The same course's other-semester draft and other courses' selected-semester drafts remain unchanged.
- All target course units are remaining.
- Saved generation constraints and all source planning records remain unchanged.
- Alerts no longer refer to deleted sessions; unrelated surviving alerts remain.

## Scenario 7: Reject a Stale Confirmation

1. Open a single-session deletion confirmation and record the displayed scope.
2. In another request or test action, edit, add, delete, or regenerate a session in the same parent draft.
3. Confirm the original deletion.
4. Repeat for complete-draft deletion.

Expected:

- Each stale deletion is rejected with `STALE_DRAFT` and removes nothing from the current draft.
- The UI closes the obsolete confirmation, refreshes current schedules/progress/alerts, and explains the change.
- Deletion occurs only after the planner opens and confirms a new current summary.

## Scenario 8: Performance and Regression Review

Regression evidence (2026-07-16): 60 targeted backend regression tests passed across draft generation/regeneration, multi-course behavior, manual editing, constraint revisions, and derived validation alerts. The 49 focused client API/calculation/dialog/panel/page tests passed, including keyboard focus behavior, filter/view preservation, Draft terminology, polite announcements, and failure states. ESLint and the Vite production build passed.

1. In the documented reference acceptance environment, measure from successful create/delete confirmation until the updated remaining units and alert state are visible. The result must be at most one second.
2. Verify generation still replaces drafts according to existing behavior.
3. Verify existing manual date/time/room editing still works.
4. Verify list/weekly modes, filters, multi-course generation, and validation-alert inspection still pass their established acceptance cases.

Record command results, the reference-environment timing, and any residual risk before commit.

## Implementation Validation Record (2026-07-16)

The automated reference acceptance environment combined FastAPI/SQLAlchemy integration tests with the client Vitest/jsdom interaction tests. Each scenario above passed through the following mapped coverage:

| Scenario | Result | Recorded evidence |
|---|---|---|
| 1. Create a first manual session | PASS | First-draft creation, inherited context, capacity filtering, progress, alert refresh, and constraint preservation passed. |
| 2. Override end time and complete a partial draft | PASS | Default calculation, earlier/later overrides, authoritative units, append behavior, and zero remaining units passed. |
| 3. Hard rules and non-blocking alerts | PASS | Structural, capacity, date, duplicate-date, and remaining-unit rejection plus retained overlap/window alerts passed. |
| 4. Delete one session | PASS | Cancellation, exact target deletion, progress/alert refresh, and unrelated-session preservation passed. |
| 5. Delete the last session | PASS | Parent removal, nullable draft response, and full remaining-unit state passed. |
| 6. Clear one complete course draft | PASS | Exact course-semester clearing, cross-course/semester isolation, and source/constraint preservation passed. |
| 7. Reject a stale confirmation | PASS | Revision/identity mismatch rollback, refresh, stale notice, and renewed-confirmation behavior passed. |
| 8. Performance and regression review | PASS | Existing generation, editing, multi-course, filter/view, alert, accessibility, lint, and production-build coverage passed. |

Reference browser timing (2026-07-16) used the seeded SQLite dataset, FastAPI on `127.0.0.1:8010`, and the Vite client on `127.0.0.1:5173` in the local Windows environment. Measurement started with the create or confirmed-delete click and ended only when the updated remaining-unit state was visible in the DOM:

- Manual creation: 307 ms to visible `22` remaining units and the refreshed saved-session overview.
- Confirmed last-session deletion: 298 ms to the visible `24 units remaining` announcement and refreshed empty overview.

Both integrated measurements passed the 1,000 ms target. The unit-level page tests no longer use mocked elapsed time as acceptance evidence; they instead verify visible progress/refresh behavior and write blocking after refresh failure. Live deployed latency can still differ from this reference environment.

Full verification outcomes:

- `python -m pytest`: PASS — 184 tests passed; 411 existing SQLAlchemy `datetime.utcnow()` deprecation warnings were reported.
- `npm test`: PASS — 21 test files and 119 tests passed.
- `npm run lint`: PASS.
- `npm run build`: PASS — Vite production build completed successfully.

Residual risks:

- Live deployed latency can differ from the automated local reference environment and should be observed after deployment.
- The required unaided usability review with at least 10 representative planners/reviewers has not yet been conducted; its aggregate evidence remains the only open FS-009 implementation task.
