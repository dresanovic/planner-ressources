# Client verification — I-014

Final runs on 2026-11-15, from `C:/Codex/planner-resource/client`:

| Gate | Result | Exit |
|---|---|---|
| Focused API/layout/Day/Week/Month/workspace/pane/pages | 214 passed, 9 files | 0 |
| Full Vitest suite | 661 passed, 74 files | 0 |
| `npm run build` (`tsc -b` and Vite) | Passed | 0 |
| `npm run lint` | Passed | 0 |

```powershell
npm test -- src/api/calendarWorkspace.test.ts src/components/calendarTimeGridLayout.test.ts src/components/CalendarTimeGrid.test.tsx src/components/CalendarMonthGrid.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/SessionPane.test.tsx src/components/calendarWorkspaceUtils.test.ts src/pages/CourseSchedulePage.test.tsx src/pages/LecturerReviewPage.test.tsx
npm test
npm run build
npm run lint
```

The existing Node 27 prerelease emits an npm support warning. All listed commands
actually completed; dependencies and lockfiles were not changed. Vite child-process
startup required the approved process-sandbox retry. Lint initially caught the
shared non-component export, a render/ref heuristic, and an export in the ignored
acceptance harness; each was corrected and final lint passes. TypeScript caught a
fixture's widened snapshot-version literal; the fixture now supplies literal 2.

Focused checks include authoritative/malformed/legacy context isolation,
identity/profile grouping, exact geometry, connected overlaps, Month overflow,
hidden affected-entry cues, guarded Month date changes, preserved unsaved inputs,
restricted review without planner fetch, and source facts inside a narrow modal's
accessible subtree in both detail and editing modes.

jsdom does not prove visual contrast, actual AT use, genuine 200% enlargement or
human comprehension. Browser observations and remaining gates are in validation.md.

Raw results: `client-targeted.txt`, `client-full.txt`, `client-build.txt`, `client-lint.txt`.


## T052 convergence follow-up

Latest full client suite: **670 passed / 74 files**, exit 0. T052's required
workspace/utils/TimeGrid/MonthGrid targeted set: **56 passed / 4 files**, exit 0.
Production TypeScript/Vite build and ESLint both pass, exit 0. Raw logs are
`convergence-t052-tests.txt`, `convergence-t052-full.txt`,
`convergence-t052-build.txt` and `convergence-t052-lint.txt`.
