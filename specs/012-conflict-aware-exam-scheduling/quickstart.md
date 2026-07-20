# Quickstart Validation Guide: FS-012 Conflict-Aware Exam Scheduling

## Purpose

Validate the migration, configuration lifecycle, conflict-aware generation, unified review, manual safeguards, stale-state handling, history preservation, accessibility, and reference performance defined by [spec.md](spec.md), [data-model.md](data-model.md), and [contracts/exam-scheduling.openapi.yaml](contracts/exam-scheduling.openapi.yaml).

## Prerequisites

- Python 3.12 with `backend/requirements.txt` installed.
- Node.js with `client/package-lock.json` installed.
- A disposable SQLite database; do not use a planner database containing user data.
- Institution timezone left at the default `Europe/Vienna` or explicitly set through `INSTITUTION_TIMEZONE` for clock-boundary tests.
- Test data containing one semester, several courses/cohorts, multiple eligible lecturers and rooms, recurring/dated unavailability, institution holidays, and saved teaching sessions.

## Automated Verification

From the repository root:

```powershell
python -m pytest backend/tests/db/test_migrations.py
python -m pytest backend/tests/services/test_exam_scheduling.py backend/tests/services/test_exam_optimization.py
python -m pytest backend/tests/api/test_exam_scheduling.py
python -m pytest backend/tests/performance/test_exam_scheduling_performance.py
python -m pytest backend/tests
```

From `client/`:

```powershell
npm run test
npm run lint
npm run build
```

Expected: every command exits successfully. Exam tests are written before production behavior and fail for the intended missing behavior before implementation.

## Contract Validation

Validate [contracts/exam-scheduling.openapi.yaml](contracts/exam-scheduling.openapi.yaml) with the same OpenAPI validation approach used by existing feature contracts.

Confirm:

- Every route, request field, response field, status, and error envelope matches backend schemas and `client/src/api/examScheduling.ts`.
- `expectedRevision`, per-course snapshot tokens, and shared generation tokens are required where documented.
- Active/past lifecycle status comes from the backend.
- Effective recommendation dates are null while a final teaching anchor is missing, and the configuration remains explicitly enabled but ineligible.
- `AUTOMATIC_START_TIME_UNAVAILABLE` is returned when no applicable active Study Type Time Window supplies an automatic proposal time; manual placement remains independent of that proposal domain.
- Recommendation deviation is separate from hard validity issues.
- Generated results return exactly one outcome per prepared course-semester.

## Local End-to-End Setup

Use a disposable database URL, then start the existing applications:

```powershell
$env:DATABASE_URL='sqlite:///./fs012-validation.db'
$env:INSTITUTION_TIMEZONE='Europe/Vienna'
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

In a second terminal:

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:8002'
Set-Location client
npm run dev -- --host 127.0.0.1 --port 5173
```

Use the existing data-administration screens or test fixtures to establish the prerequisites. Do not add new navigation or an exam-type catalog.

## Scenario 1: Explicit Configuration and Disabled Courses

1. Select a semester and one course with saved teaching sessions.
2. Verify exam planning is disabled by default and no missing-exam warning appears.
3. Enable the next exam and enter identifier, duration, required capacity, free-text type, and an eligible responsible lecturer.
4. Leave the recommendation overrides empty.
5. Save and inspect the returned recommendation.
6. Repeat with another course that has no saved teaching session.

Expected:

- The recommendation is seven through fourteen calendar days after the final saved teaching session.
- The course without teaching retains its enabled configuration, returns null effective recommendation dates, and is visibly ineligible with `FINAL_TEACHING_SESSION_MISSING` until a final teaching session exists.
- Blank/whitespace type, non-positive duration/capacity, missing lecturer, or an override end date before its start returns all applicable field errors and preserves prior state.
- A partly or wholly pre-teaching recommendation is retained as a soft planner preference, but generation never places an exam before the final teaching boundary and may therefore place outside that recommendation.
- A disabled course is not selectable for generation and receives no failure outcome.

## Scenario 2: Conflict-Aware Mixed Generation

1. Configure several courses with a combination of feasible and deliberately infeasible resource/date conditions.
2. Include teaching occupancy, one existing active exam, past exams, one holiday, resource unavailability, and a capacity shortage.
3. Include one course whose Study Type has no active Time Window.
4. Prepare generation for all selected courses, review eligibility, then submit the exact preparation tokens.

Expected:

- Existing active and past exams and all teaching sessions remain unchanged.
- At most one active exam is saved for each eligible course-semester.
- Proposed exams do not overlap teaching/exams by lecturer, room, or cohort.
- Rooms are active, eligible, available for the full interval, and meet configured exam capacity.
- Holidays and the pre-final-teaching interval are never used.
- Feasible courses return `scheduled`; infeasible courses return `failed` with every substantiated reason; changed inputs return `stale`; active/disabled selections are skipped without false missing outcomes.
- The course without an automatic proposal time returns `AUTOMATIC_START_TIME_UNAVAILABLE`; the result does not claim that every possible clock time or a resource conflict was evaluated, and manual placement remains available.
- The summary does not claim complete success for a mixed result.

## Scenario 3: Recommended Window Is Soft

1. Create a configuration with its default or planner-changed recommended date window.
2. Make every candidate inside the recommendation infeasible while leaving a valid post-teaching in-semester candidate outside it.
3. Generate the exam.
4. Manually move or create another validation example outside the recommendation.

Expected:

- Automatic generation prefers an inside-window candidate whenever one is hard-constraint-valid.
- When none exists, automatic generation may save the outside-window candidate.
- Manual creation/correction outside the recommendation is accepted when all hard constraints pass.
- Review shows `Outside recommended window` as soft context, not as current invalidity.
- Neither automatic nor manual placement silently changes the saved recommendation.

## Scenario 4: Hard Manual Safeguards

Attempt manual creation/correction for each case:

- starts before the final teaching session ends;
- falls outside the semester or crosses midnight;
- overlaps a teaching session or another exam by lecturer, room, or cohort;
- uses an inactive/ineligible lecturer or room;
- uses an insufficient room;
- overlaps lecturer or room unavailability;
- occurs on an institution holiday;
- would create a second active exam.

Expected: each mutation is rejected, all substantiated errors are shown together, and every existing teaching/exam/configuration record remains unchanged. A back-to-back interval whose start exactly equals another interval's end remains valid.

## Scenario 5: Active/Past Lifecycle and Fresh Configuration

1. With the institution clock fixed, save one exam dated today and verify it is `active`.
2. Attempt to edit, disable, or freshen its consumed configuration and attempt to generate or manually create another active exam for the same course-semester.
3. Advance the injected institution date beyond the exam date and reload.
4. Prepare the next exam configuration.

Expected:

- The second active exam is rejected without changing the first.
- The consumed configuration is read-only while the active exam exists.
- After the date advances, the exam is `past`, remains reviewable, and no longer occupies the active slot.
- Preparing the next exam starts fresh; changing it does not alter any past exam snapshot.
- Unlimited past rows may be retained.
- The browser never independently changes lifecycle status based on its own timezone.

## Scenario 6: Manual Correction and Deletion

1. Correct one active exam and one past exam to valid alternative placements.
2. Attempt to correct a past exam onto today/future while another active exam exists.
3. Open active deletion confirmation, verify its exact consequence, and cancel.
4. Reopen and confirm active deletion.
5. Open and confirm deletion of one past exam.

Expected:

- Valid corrections change only the selected exam and increment its revision.
- A correction creating a second active exam is rejected.
- Cancellation changes nothing.
- Active deletion leaves the current configuration enabled and unscheduled.
- Past deletion removes only the selected historical row and leaves current configuration, active exam, other history, teaching, and resources unchanged.
- Dialog focus entry, trap, Escape, busy-state lock, and focus restoration are keyboard operable.

## Scenario 7: Current Validity Without Automatic Repair

1. Save a valid exam.
2. Add a holiday on its date, reduce room capacity, make the resource unavailable, remove eligibility, move the final teaching session past it, or add conflicting teaching/exam occupancy.
3. Reload the semester review after each change.

Expected:

- The saved exam is never automatically moved or deleted.
- Current validity issues identify every applicable hard-rule failure with relevant date/resource/session evidence.
- Removing the underlying cause removes the issue on the next authoritative read.
- The soft recommendation notice remains separate from hard validity issues.

## Scenario 8: Stale Input Protection

For configuration save, generation, manual correction, and deletion:

1. Load the state and retain its revision/snapshot token.
2. Change a material target or related input in a second action: configuration, teaching/exam occupancy, resource eligibility/capacity/availability, holiday, semester boundary, final teaching anchor, or institution date.
3. Submit the original action.

Expected:

- The request returns a structured `409` or per-course `stale` outcome.
- No invalid requested change is saved.
- The client preserves the last known complete combined review until a full refresh succeeds.
- The stale editor/dialog closes or refreshes and requires the planner to review current state before retrying.

## Scenario 9: Unified Review and Accessibility

1. Review a semester containing teaching sessions, active exams, and past exams in list and weekly views.
2. Filter by existing course/cohort/lecturer/room controls.
3. Navigate exam controls and dialogs using keyboard only and inspect at 200% zoom/narrow supported layouts.

Expected:

- Exam/Teaching, Active/Past, and validity/recommendation states use text or semantics, not color alone.
- Sorting and filters operate across the combined view without making teaching fields nullable or mislabeling exams.
- Required exam context is available within two interactions.
- Existing Schedule/Academic Data navigation remains unchanged.

## Scenario 10: Reference Performance

Build the documented reference dataset:

- 100 enabled valid unscheduled configurations;
- 500 teaching sessions;
- 100 existing active/past exams distributed so the one-active rule remains valid;
- representative eligible resources, unavailability, holidays, and conflicts.

Expected:

- Preparation plus proven deterministic generation completes within 60 seconds.
- Every selected course receives exactly one scheduled/failed/stale/skipped outcome.
- Repeating the same prepared state produces the same canonical arrangement and reason ordering.
- No result is saved if an optimal result for the prepared snapshot is not proven within the bounded operation.

## Evidence to Record Before Commit

- Migration clean-create and 0005→0006 results.
- Backend service/API/regression command output.
- Client test/lint/build output.
- OpenAPI validation result.
- Mixed generation and failure screenshots or structured response captures.
- Keyboard/accessibility review notes.
- 100-requirement performance timing and deterministic rerun comparison.
- Confirmation that pre-existing FS-008, FS-009, FS-010, FS-011, and FS-018 workflows remain green.

## Implementation Verification Evidence — 2026-07-20

Validation used the `codex/fs-012-exam-scheduling` branch, the `Europe/Vienna` institution timezone, and a disposable SQLite database. The browser session, local servers, and disposable database were closed and removed after verification.

### Automated results

| Check | Result |
|---|---|
| Clean-create, idempotence, and 0005-to-0006 migration coverage | Passed as part of the complete backend suite |
| Complete backend regression suite | 292 passed; warnings were pre-existing dependency deprecations |
| FS-012 service and 100-course reference performance rerun | 12 passed; reference case completed in 1.18 seconds |
| Runtime OpenAPI route/schema contract assertions | Passed for all six FS-012 route templates and required aliases/tokens |
| Client Vitest suite | 30 files, 154 tests passed |
| Client ESLint | Passed |
| TypeScript and Vite production build | Passed; 50 modules transformed |
| Whitespace and conflict-marker checks | Passed |

The reference performance fixture contains 100 enabled course inputs, 500 teaching occupancies, 100 existing exam occupancies, a holiday, deterministic rerun comparison, and an explicit zero-budget unproven-result assertion. No candidate is returned for the unproven run.

### Scenario evidence

| Scenario | Evidence and result |
|---|---|
| 1. Explicit configuration | Rendered Schedule review confirmed disabled-by-default courses show no missing-teaching warning. After explicit enablement, an anchorless course shows placement guidance; after a saved final teaching session, the effective recommendation was 2026-09-14 through 2026-09-21. Atomic field-validation, nullable recommendation, and default derivation assertions passed. |
| 2. Mixed generation | A protected preparation was reviewed and submitted in the browser. The result was `1 scheduled`, `0 failed`, `0 stale`, `0 already active`, and `2 disabled`; the generated 2026-09-14 08:00 exam appeared in unified review. Optimizer/API tests cover holiday, fixed teaching/exam occupancy, deterministic resource selection, and empty automatic-start evidence. |
| 3. Soft recommendation | A manual exam was accepted on 2026-10-01 outside the 2026-09-14 through 2026-09-21 recommendation. Review displayed `Outside recommended window` separately from hard validity. The saved recommendation remained unchanged. |
| 4. Manual safeguards | Service tests rejected aggregated before-final-teaching, capacity, and cross-midnight failures atomically; optimizer and resource regressions cover holidays, occupancy, availability, and eligibility. A valid manual placement was created and reviewed through the browser. |
| 5. Lifecycle/history | Injected-clock tests classified today/future as active and moved an elapsed exam to retained past history. Browser review showed an active exam, locked its consumed configuration, prevented another placement, and returned the course to enabled/unscheduled after exact active deletion. |
| 6. Correction/deletion | Manual update and exact deletion API/service assertions passed. Browser deletion showed the active consequence, trapped Tab between controls, closed on Escape without mutation, restored focus, and then deleted only the confirmed exam. |
| 7. Current validity | After an exam was saved, adding a holiday produced `INSTITUTION_HOLIDAY` on the next authoritative read without moving or deleting the exam. The exam identifier and date remained unchanged. |
| 8. Stale protection | Configuration/API stale assertions and related-input token tests passed. Adding a holiday invalidated the prior exam token; correction returned structured `409`/`STALE_INPUT_SNAPSHOT` and made no change. Existing Schedule refresh-failure tests confirm the last complete view remains visible and writes stay blocked until refresh. |
| 9. Unified review/accessibility | Rendered review distinguished Teaching/Exam, Generated/Manual, Active/Past, hard issues, and soft recommendation context. Keyboard deletion was verified. At a 360-pixel viewport and a 640-pixel CSS viewport representing a 1280-pixel layout at 200% scaling, no horizontal page overflow remained. Schedule and Academic Data navigation both remained reachable and unchanged. |
| 10. Reference performance | The documented 100/500/100 dataset passed deterministically in 1.18 seconds, below the 60-second target; the zero-time solver run returned no unproven placement. |

The complete backend regression includes the existing FS-008, FS-009, FS-010, FS-011, and FS-018 workflows. The targeted correctness pass additionally verified preserved infeasibility evidence, aggregated configuration errors, selection-bound preparation tokens, retained teaching-anchor identity, authoritative post-write refreshes, exam-aware resource removal, historical-duration review, recommendation context, and disabled/active generation controls. The UI inspection found and resolved combined-refresh and responsive-overflow regressions before the final passing suites.
