# FS-020 Automated Client Evidence

Environment: Windows, Node v26.7.0, npm 11.13.0, Vite 8.1.3, isolated branch `codex/fs-020-lecturer-calendar-export`.

| Command | Result | Duration |
|---|---:|---:|
| `npm test -- --run src/api/lecturerReview.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/LecturerCalendarDownloadDialog.test.tsx src/pages/LecturerReviewPage.test.tsx` | 4 files, 75 tests passed | 3.43 s |
| `npm run lint` | passed, zero findings | 12.5 s |
| `npm run build` | passed, 78 modules transformed | 0.381 s Vite build; 18.9 s command |
| `npm test` | 55 files, 412 tests passed | 15.26 s |

The tests cover fixed bearer-only transport, strict response metadata, notice/cancel/confirm, focus and keyboard behavior, busy/retry/terminal outcomes, object-URL cleanup, workspace-state preservation, empty scope, and no double-modal action.
