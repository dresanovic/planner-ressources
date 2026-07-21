# Automated validation — FS-013

Validated on 2026-07-20 in `C:\Codex\planner-resource`.

## Results

| Area | Command | Result |
|---|---|---|
| Backend migration, lifecycle, guards, concurrency, performance, and regressions | `backend\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-fs013-release-20260720` from `backend` | PASS — 310 tests in 80.98 s |
| Focused lifecycle client | `npm run test -- src/api/scheduleLifecycle.test.ts src/components/ScheduleLifecyclePanel.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/components/AbandonRevisionDialog.test.tsx src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx` | PASS — 56 tests |
| Full client regression | `npm run test` | PASS — 34 files, 164 tests |
| Client lint | `npm run lint` | PASS |
| TypeScript project build | `npx tsc -b` | PASS |
| Production client build | `npm run build` | PASS — 54 modules transformed |
| Runtime OpenAPI | Included in `backend/tests/api/test_schedule_lifecycle.py` during the full backend run | PASS |

The backend emitted existing dependency/deprecation warnings; no test failed. A pre-release run caught a missing test import, which was corrected before the release run above.

## Coverage highlights

- Clean and sequential migration, populated-semester adoption, integrity constraints, downgrade refusal, and idempotent initialization.
- Direct publication, replacement publication, immutable captured detail, Draft/Ready transitions, abandon/restore, stale requests, mutation guards, and ordered event history.
- The browser-discovered two-event replacement sequence defect is covered by the API replacement test; the old revision receives `superseded` immediately before the successor receives `published`.
- Publication preparation captures remaining units, teaching validation alerts, enabled unscheduled exams, exam validity issues, and recommendation deviations as non-blocking conditions.
- Existing single-course, multi-course, conflict-aware, and exam scheduling regressions pass with active-working-revision guards.

## Known evidence boundary

The deterministic performance test covers lifecycle preparation, publication, successor creation, captured-detail retrieval, and 101-revision history under the two-second limit. It does not yet instantiate the quickstart's full 100-course/500-teaching-session/100-exam reference dataset or assert a strict bounded SQL-query count.
