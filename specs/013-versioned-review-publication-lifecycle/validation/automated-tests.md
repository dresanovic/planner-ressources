# Automated validation — FS-013

Validated on 2026-07-23 in `C:\Codex\planner-resource`.

## Results

| Area | Command | Result |
|---|---|---|
| Backend migration, lifecycle, guards, concurrency, performance, and regressions | `backend\.venv\Scripts\python.exe -m pytest -q` from `backend` | PASS — 322 tests in 47.45 s |
| Focused lifecycle client | `npm run test -- --run src/api/scheduleLifecycle.test.ts src/components/ScheduleLifecyclePanel.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/components/AbandonRevisionDialog.test.tsx src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/CourseSchedulePage.snapshot.test.ts` | PASS — 7 files, 62 tests |
| Full client regression | `npm run test -- --run` | PASS — 35 files, 170 tests |
| Client lint | `npm run lint` | PASS |
| TypeScript project build | `npx tsc -b` | PASS |
| Production client build | `npm run build` | PASS — 55 modules transformed |
| Runtime OpenAPI | Included in `backend/tests/api/test_schedule_lifecycle.py` during the full backend run | PASS |

The backend emitted existing dependency/deprecation warnings; no test failed. A pre-release run caught a missing test import, which was corrected before the release run above.

## Coverage highlights

- Clean and sequential migration, populated-semester adoption, integrity constraints, downgrade refusal, and idempotent initialization.
- Direct publication, replacement publication, immutable captured detail, Draft/Ready transitions, abandon/restore, stale requests, mutation guards, and ordered event history.
- The browser-discovered two-event replacement sequence defect is covered by the API replacement test; the old revision receives `superseded` immediately before the successor receives `published`.
- Publication preparation captures remaining units, teaching validation alerts, enabled unscheduled exams, exam validity issues, and recommendation deviations as non-blocking conditions.
- Existing single-course, multi-course, conflict-aware, and exam scheduling regressions pass with active-working-revision guards.
- The reference fixture contains 100 courses, 500 teaching sessions, and 100 exams; preparation remains under two seconds and below 50 SQL statements.
- Multi-course and conflict-aware generation acquire the lifecycle write claim only after calculation/optimization and revalidate immediately before final reload and persistence.
- Exam generation also acquires the lifecycle claim only after joint optimization, expires previously loaded state, and rejects changed prepared inputs before saving.
- Historical exam course labels, teaching alerts, related sessions, exam validity issues, and final-teaching identity are rendered from captured snapshot data.
- A failed historical snapshot read keeps live data hidden and offers a same-revision retry that can recover without a page or semester change.
- Publication validation preserves the distinction between current default generation constraints and captured Study Type windows after catalog changes.
- File-backed races cover competing first and replacement publication, duplicate-event prevention, atomic rollback, create-versus-restore, restore-versus-restore, and abandon-versus-mutation outcomes.

## Known evidence boundary

The literal 200% browser-zoom pass in T065 and moderated 10-planner acceptance study in T066 remain open follow-up evidence.
