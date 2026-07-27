# Quickstart Validation: FS-014 Calendar Planning Workspace

This guide defines reproducible validation for the plan. It does not replace
the acceptance scenarios in [spec.md](spec.md), the data rules in
[data-model.md](data-model.md), or the contracts in
[contracts/](contracts/).

## Prerequisites

- Python 3.12 and the backend dependencies installed.
- Node.js and client dependencies installed.
- A disposable SQLite database; do not run migration validation against
  irreplaceable planner data.
- Reviewers have both UI reference images:
  `docs/designs/resource-planner-calendar-screen-reference.png` and
  `docs/designs/resource-planner-unified-navigation-ground-truth.png`.
- For moderated acceptance, at least 10 representative planners or designated
  acceptance reviewers are available.

## 1. Review the design boundaries

Before implementation, confirm:

- the API is one revision-scoped read, as defined in
  [calendar-workspace.openapi.yaml](contracts/calendar-workspace.openapi.yaml);
- List mode is the adapted existing Courses overview, as defined in
  [calendar-workspace-ui.md](contracts/calendar-workspace-ui.md);
- `PlanningOutcome` is the only new relational entity;
- there is no Dashboard route, second list, new optimizer, drag/drop/resize,
  lecturer access, or external synchronization;
- the two UI references guide gradual presentation and shared navigation but
  do not authorize unsupported controls.

## 2. Migration verification

Apply all migrations to a new disposable database, then upgrade an existing
schema at revision 0007.

```powershell
python -m pytest backend/tests/db/test_migrations.py
```

Expected:

- both paths reach schema revision 0008;
- `planning_outcomes` has its foreign keys and unique
  revision/course/operation-kind constraint;
- no outcome history is fabricated during upgrade;
- existing schedule and lifecycle rows remain intact.

## 3. Backend focused tests

Write the feature tests before production behavior where practical, confirm
they fail for the intended missing behavior, then run:

```powershell
python -m pytest backend/tests/services/test_calendar_workspace.py backend/tests/services/test_planning_outcome_retention.py
python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py backend/tests/api/test_conflict_aware_generation.py backend/tests/api/test_exam_scheduling.py backend/tests/api/test_schedule_lifecycle.py
python -m pytest backend/tests/performance/test_calendar_workspace_performance.py
```

Expected:

- default/explicit revision selection never blends contexts;
- Published content remains captured and immutable while current validation
  excludes Working/historical occurrences;
- reliable per-course outcomes persist, reload, supersede only the matching
  revision/course/kind, and do not survive into a successor by inference;
- all complete-revision metrics exactly reconcile with contributor references;
- planning-outcome coverage produces the defined not-applicable, unavailable,
  partial-known, and available states, with zero used only for complete
  available coverage;
- the reference-scale response meets the timing checks in section 8.

## 4. Frontend focused tests

```powershell
Set-Location client
npm run test -- src/api/calendarWorkspace.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/ScheduleLifecyclePanel.test.tsx src/components/ApplicationNavigation.test.tsx src/App.test.tsx
```

Expected:

- Week, Day, Month, and adapted List preserve context and filters;
- List parity proves existing alerts, summaries, review, and editor paths;
- mode/date/filter/drilldown operations make no mutation requests;
- filtered summaries reconcile to canonical contributors;
- loading/failure never relabel old records as a new context;
- focus, names, roles, announcements, and deterministic focus return are
  covered where the DOM test environment can verify them.

## 5. Full automated regression

```powershell
python -m pytest backend/tests
Set-Location client
npm run test
npm run lint
npm run build
```

Expected: all commands pass, including the applicable FS-009 through FS-013 and
FS-018 regression paths.

## 6. End-to-end acceptance matrix

Use deterministic fixtures and verify each row against the spec and contracts.

| Scenario | Evidence |
|---|---|
| No semester / no revision | Distinct state; null revision; empty revision-owned records/facets; all summaries not applicable with no-revision scope; established Start Draft path only where applicable |
| Working only / Published only / both | Correct default; complete atomic switch; text designation and lifecycle state |
| Published planning-data change | Captured occurrences/totals unchanged; current warnings change; Working occurrences excluded |
| Week / Day / Month / List | Correct range/navigation; all occurrences reachable; List is the existing overview behavior |
| Filters | Every facet and intersection; no-match/clear; remaining-work room and exam-only semantics; no mutations |
| Aggregation | Independent expected units/minutes, conflict pair/type, capacity occurrence, latest failures, and distinct needs-review courses |
| Traceability | Every nonzero value exposes all and only contributors within two interactions |
| Existing correction/lifecycle action | Existing validation/confirmation/stale behavior; successful atomic refresh; cancel/failure preserves data |
| Empty/partial/failure/retry | Zero, not applicable, unavailable, and partial-known remain distinct; last-known labeling; no cross-context data |
| Dense dates | Count/continuation reaches every occurrence with keyboard and assistive technology |
| Scope exclusions | No second list, Dashboard route, drag/drop/resize, new planning behavior, lecturer access, or sync |
| Gradual visual adoption | Calendar reference informs hierarchy; navigation reference remains authoritative; existing terminology wins |

For current-period navigation, run the matrix with today inside, before, and
after the semester. Day, Week, and Month use today or the nearest semester
boundary and communicate boundary substitution; List remains in place and
marks the action not applicable.

## 7. Browser, accessibility, and responsive validation

DOM tests cannot establish all visual, zoom, focus, contrast, or screen-reader
outcomes. Validate manually in the supported real browser and
screen-reader/browser combination:

1. Complete all primary workflows using keyboard only.
2. Verify visible focus, detail/drilldown focus entry, and focus return after
   close, deletion, or filter disappearance.
3. Verify teaching, exam, holidays, warnings, selected state, and revision
   designation without color.
4. Verify metric name, value/unavailability, scope, activation purpose, and
   contributor relationship are announced.
5. Verify simultaneous sessions remain individually discoverable.
6. Verify at 320 CSS pixels and 200% text zoom that the FS-018 navigation and
   all workspace content/actions remain reachable without overlap.
7. Measure required color contrast.
8. Compare wide and narrow presentation with both supplied reference images,
   recording deliberate deviations caused by established terminology,
   accessibility, or scope.

Record browser, screen reader, viewport, zoom, result, and evidence. Do not mark
these criteria passed from code inspection alone.

## 8. Performance validation

Use one deterministic semester with exactly:

- 100 course-semester contexts;
- 500 teaching and exam occurrences total;
- 50 current holidays;
- mixed conflicts, capacity/holiday/exam findings, and retained outcomes.

Repeat each timing path 20 times after documented warm-up:

- initial load: at least 19/20 complete within 3 seconds; every run completes or
  shows an actionable failure within 10 seconds;
- mode/date/filter/drilldown/context change: at least 19/20 visible within
  1 second; every run completes or shows an actionable failure within 3
  seconds;
- successful correction/lifecycle refresh: at least 19/20 visible within
  2 seconds.

Record server response time separately from browser render/interaction time so
regressions are diagnosable. A failure-state timeout is not a successful load.

## 9. Moderated acceptance

With at least 10 actual representative planners or designated reviewers,
measure SC-004 through SC-006:

- selected semester/revision/lifecycle/largest issue identification within
  30 seconds;
- named teaching session, exam, remaining-work course, and review reason within
  two minutes;
- trace a summary and invoke the correct existing Working action on the first
  attempt without trying to mutate Published.

At least 90%, rounded up to the next participant, must succeed for each
criterion. Record anonymized task outcomes and observed issues. These criteria
remain pending—not passed—until the sessions occur.
