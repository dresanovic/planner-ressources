# Implementation Plan: I-014 Time-Grid Calendar with Teaching Window Context

**Working Branch**: `codex/i-014-time-grid-calendar` | **Planning date**: 2026-11-12 | **Implementation evidence**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: `specs/I-014-time-grid-calender/spec.md`. Setup resolves the feature independently of Git and reports `BRANCH=I-014-time-grid-calender`; this is the feature selector, not evidence of a Git checkout.

## Summary

Replace the existing stacked calendar cards with proportional Day/Week surfaces and a complete Month date grid, retaining workspace navigation, filters, summaries, List and established correction panes. Add only a read-only projection of already assembled teaching-window context to the existing workspace response. Resolve date applicability with the existing backend helper so the browser does not implement teaching permission. No scheduling, validation, availability, persistence or publication rules change.

## Technical Context

**Language/Version**: Python 3.13 deployment baseline; TypeScript ~6.0.2. Existing Docker frontend build uses Node 26. Use compatible installed runtimes and existing lockfiles, recording actual versions during verification.
**Primary Dependencies**: Existing FastAPI 0.139.0, Pydantic 2.13.4, SQLAlchemy 2.0.45; React 19.2.x, Vite 8.1.x, CSS. No additional dependencies.
**Storage**: Existing SQLite/SQLAlchemy. No schema, migration, saved-view preference or snapshot-format change.
**Testing**: pytest 9.1.1; Vitest 4/jsdom; existing TypeScript build and ESLint. Real-browser, keyboard and assistive-technology observations supplement automation.
**Target Platform**: Existing authenticated planner web app on supported desktop/narrow browsers, 320 CSS pixels and 200% text enlargement. Preserve shared restricted lecturer-review consumption.
**Project Type**: Web application; frontend presentation plus additive read-only backend contract.
**Performance Goals**: Preserve existing workspace performance checks; no invented latency target. Meet SC-004: four of five planners identify each reference case within 30 seconds. All entries remain reachable for 20 sessions/date and dense overlaps.
**Constraints**: Existing profiles/precedence/findings remain authoritative. Full-day scrolling, calendar identity, non-color cues, unchanged actions and no mutation during viewing. No optimizer work or availability overlays.
**Scale/Scope**: One planner workspace, three calendar modes plus retained List; per-course window context across the selected semester, including empty dates and zero-session revision courses. Existing selectable calendars only.

## Constitution Check

| Gate | Before research | After design |
| --- | --- | --- |
| I: Spec-first | PASS: I-014 spec and quality checklist exist | PASS: design maps to FR-001–020; no production change |
| II: Test-first | PASS: explicit TR-001–006 | PASS: failing automated checks precede each story; manual limitations below |
| III: Acceptance | PASS: four independent stories and measurable SC-001–006 | PASS: contract and quickstart make geometry, provenance and zero-write outcomes observable |
| IV: KISS | PASS: reuse existing workspace/data | PASS: one response extension, two surfaces and pure layout helpers; no new dependency/layer |
| V: Verified workflow | PASS: planning only on current master; existing user work preserved | PASS: implementation uses `codex/i-014-time-grid-calendar` before production work; full relevant checks before commit |
| VI: Incremental delivery | PASS: core comparison first | PASS: US1 comparison, US2 multiple/provenance contexts, US3 Month/workflows, US4 complete accessibility verification; basic accessibility accompanies every increment |
| Technology/boundaries | PASS: established FastAPI and React/TypeScript/Vite | PASS: existing backend/client directories and explicit cross-stack contract |

The clean-master implementation exception is not invoked: this checkout contains existing work. The implementation branch recommendation does not authorize committing, discarding or moving unrelated changes. No constitution exception is needed.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Extend the existing workspace read with source profiles/date applicability; keep filtering/state/action ownership; render Day/Week with one shared minute scale and Month with enumerated dates. Use native buttons and labeled sections.
2. **Necessary abstractions**: A small pure layout utility for date enumeration/minute geometry/overlap lanes, an hourly surface shared by Day/Week, and a compact Month surface. These isolate demonstrably different layouts for direct testing; no scheduling abstraction is introduced.
3. **Deliberately excluded**: Calendar library, state store, generic rendering engine, recurrence engine, new API route, migrations, new snapshots/caching, virtualization, new resource overlays, drag/drop, resize, automatic correction and optimizer changes.

## Project Structure

### Documentation (this feature)

```text
specs/I-014-time-grid-calender/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/interfaces.md
`-- checklists/requirements.md
```

Implementation is tracked in `tasks.md`; actual checks and remaining observed acceptance are recorded in `validation.md` and `verification/`.

### Source Code (repository root)

```text
backend/app/schemas/calendar_workspace.py           # additive response types
backend/app/services/calendar_workspace.py          # same profiles, read-only projection
backend/tests/services/test_calendar_workspace.py
backend/tests/api/test_calendar_workspace.py
backend/tests/performance/test_calendar_workspace_performance.py
client/src/api/calendarWorkspace.ts                 # additive types/validation
client/src/api/calendarWorkspace.test.ts
client/src/components/CalendarPlanningWorkspace.tsx # retain state/actions, delegate surfaces
client/src/components/calendarWorkspaceUtils.ts     # retain filters/period rules
client/src/components/calendarTimeGridLayout.ts     # new pure presentation helpers
client/src/components/CalendarTimeGrid.tsx           # new Day/Week surface
client/src/components/CalendarMonthGrid.tsx          # new Month surface
client/src/components/SessionPane.tsx               # read-only context inside modal accessibility boundary
client/src/components/*.test.ts[x]                  # colocated targeted tests
client/src/test/calendarWorkspaceFixtures.ts
client/src/App.css                                  # scoped calendar styles
client/src/pages/CourseSchedulePage.tsx              # pane integration only if needed
```

**Structure Decision**: No new package or architectural boundary. Existing `schedule_generation.window_applies` is consumed unchanged. Existing lifecycle, generation, persistence and mutation modules are regression subjects, not production edit targets. The public lecturer adapter remains compatible with absent planner-only context; public endpoints gain no new access.

Implementation observation (2026-11-15): the existing narrow SessionPane makes
calendar siblings inert. FR-007/017 therefore also require reusing the read-only
window disclosure inside the planner pane in detail and editing modes. No pane
authority, mutation, focus-trap or restricted-review behavior changes.

## Complexity Tracking

No exceptions, new dependencies or architectural layers. The read-only response addition is required because the existing response drops profiles and cannot represent empty teaching opportunities. Exposing that projection is smaller and safer than client catalog joins; details are in [research.md](research.md).

## Design and Delivery Sequence

1. **US1**: Write failing response/geometry tests; expose per-course source context and resolved dates; render one-calendar hourly comparison including empty dates and the 80-minute overrun. Keep keyboard/text facts available from the first increment.
2. **US2**: Extend failing cases for intensive precedence, source identities, zero-session calendars, differing course contexts and legacy publication. Add labeled calendar groups and profile-specific inspection, unknown/retry states and token coverage. Never merge source windows into a new permitting interval.
3. **US3**: Test complete Month weeks, three-entry default, exact overflow, affected counts, date-to-Day and session-to-pane actions; retain List set parity and correction lifecycle.
4. **US4**: Finish keyboard/focus/reading-order checks and actual browser/AT/zoom/user trials across all modes; fix presentation defects without changing business rules.

Use one hour = 72 CSS pixels initially, with a full 1,728-pixel day canvas and exact proportional block dimensions. The scale is an internal presentation constant, not a preference to persist. End-exclusive interval partitioning assigns deterministic overlap lanes; it is not conflict detection. Native buttons plus labeled sections avoid the incomplete existing `role=grid` behavior. Month can expand in place, avoiding another modal/focus manager.

Backend date applicability is projected using the same source profile, period boundaries and `window_applies` semantics as existing validation, never reconstructed in TypeScript. Published provenance stays captured; current validation labels stay unchanged. Preserve source lists even when background paint uses an interval union for visual coverage; the union cannot imply single-session validity. When courses in one calendar have different effective profiles, show labeled course-context subgroups rather than a misleading common background.

## Verification Plan

Commands are future implementation gates, not results from this planning run. From repository root, use the existing backend virtual environment:

```powershell
Push-Location backend
.venv/Scripts/python.exe -m pytest tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py tests/services/test_dated_intensive_windows.py tests/services/test_draft_schedule_validation.py tests/services/test_schedule_lifecycle.py
.venv/Scripts/python.exe -m pytest tests/performance/test_calendar_workspace_performance.py
.venv/Scripts/python.exe -m pytest tests
Pop-Location
Push-Location client
npm test -- src/api/calendarWorkspace.test.ts src/components/calendarTimeGridLayout.test.ts src/components/CalendarTimeGrid.test.tsx src/components/CalendarMonthGrid.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/pages/CourseSchedulePage.test.tsx src/pages/LecturerReviewPage.test.tsx
npm test
npm run build
npm run lint
Pop-Location
git diff --check
```

New test files must be created before the associated production files. `npm run build` includes `tsc -b`; there is no separate current typecheck script. Backend tests assert response shape/provenance/date resolution, unchanged findings, no writes and response-token changes; client API tests assert malformed/partial context handling. Shared fixtures exercise the same reference facts across backend and frontend. Full suites catch public review, pane, navigation and lifecycle regressions.

Manual exception: automated layout/DOM assertions do not establish actual rendered scale, contrast, assistive-technology comprehension, genuine 200% enlargement or five-human SC-004. Follow [quickstart.md](quickstart.md), record viewport/browser/AT/version/screenshots and individual results during implementation. Missing observations remain pending acceptance, never inferred from unit passes. Record final command outcomes and limitations in a future `validation.md`; do not mark tests complete from this plan.

Implementation now exists and automated gates pass. See `validation.md` for actual results, reviewed scope and the remaining T044/T045/T049 observed acceptance. No extension configuration is present.

## Calendar simplification — 15.11.2026

Reuse existing components and client projection. Remove redundant Month/source summaries, derive compact cohort labels from existing names, retain empty dates once and session-bearing profile columns, and replace the cohort select with a native checkbox popover. No API, dependency or scheduling changes. Simplicity check: direct state and existing profile grouping suffice. Regression tests cover empty dates, cohort labels, date-local columns and checkbox/lecturer filtering across modes and refresh.
