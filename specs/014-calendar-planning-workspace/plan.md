# Implementation Plan: FS-014 Calendar Planning Workspace and Operational Dashboard

**Working Branch**: `codex/fs-014-calendar-workspace` (created from the verified
`master` planning baseline before production changes) | **Date**: 2026-07-23 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`/specs/014-calendar-planning-workspace/spec.md`

## Summary

Deliver one calendar-centered semester workspace inside the existing Schedule
destination. One coherent Working or Current Published read supplies Week, Day,
Month, and List modes, operational summaries, filters, trace targets, alerts,
and details. The existing Courses overview is adapted into the workspace's only
List mode—its current review, filter, alert, summary, and correction behavior is
preserved and is not rebuilt or removed prematurely.

The backend adds a revision-scoped composite read, persists only the latest
reliable per-course planning outcome for each operation kind, and evaluates
Current Published occurrences against current planning data without mutating
their snapshot or mixing Working content. The client keeps orchestration in the
existing Schedule page, uses the current correction/lifecycle workflows, and
adds no calendar, date, routing, state-management, drag/drop, or accessibility
dependency.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript ~6.0.2 and React 19.2.7
frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13.4, SQLAlchemy 2.0.45;
React 19.2.7, React DOM 19.2.7, Vite 8.1.1. No new runtime dependency planned.

**Storage**: Existing configurable SQLAlchemy database with SQLite as the
default; sequential project migration 0008 adds one latest-outcome table.
Published snapshot JSON advances to schema v2 for new publications while v1
remains readable.

**Testing**: pytest 9.1.1 for service/API/migration/performance coverage;
Vitest 4.0.16 and Testing Library for client behavior; ESLint 10.6.0, TypeScript
through Vite build; manual real-browser keyboard, screen-reader, zoom,
responsive, contrast, visual-reference, and moderated usability validation.

**Target Platform**: FastAPI service and modern desktop/mobile-width web
browsers supported by the existing React application

**Project Type**: Cross-stack web application in the existing `backend/` and
`client/` projects

**Performance Goals**: At 100 courses, 500 total teaching/exam occurrences, and
50 holidays: at least 95% of initial loads within 3 seconds and all load or
present actionable failure within 10 seconds; at least 95% of presentation
interactions within 1 second and all update or fail actionably within 3 seconds;
at least 95% of successful action refreshes within 2 seconds.

**Constraints**: Exactly one permitted revision context per response; immutable
Published content with separately labelled current validation; filters and
calendar controls are non-mutating; every metric reconciles to contributors;
zero differs from partial, unavailable, and not applicable; planning-outcome
coverage is measured across included eligible courses; other metric
applicability is based on included courses, occurrences, or capacity-evaluable
occurrences; current-period navigation clamps to the nearest semester boundary
when today is outside the semester; no second List, Dashboard destination,
drag/drop/resize, new optimization, external sync, authentication, lecturer
access, or new domain rule; 320 CSS-pixel and 200% zoom access; FS-018
navigation remains unobstructed.

Loaded and no-revision responses are separate discriminated contract variants.
The no-revision variant contains no revision-owned records or facets and only
not-applicable summaries with no-revision scope.

**Scale/Scope**: One selected semester, active Working and/or Current Published
selector, up to 100 course contexts, 500 occurrences, and 50 holidays. Historical
revisions remain in existing lifecycle history. This slice coordinates
FS-009–FS-013 and FS-018 behavior rather than replacing it.

## Constitution Check

*GATE: Passed before research and re-checked after design.*

### Pre-research gate

- **Spec-first — PASS**: `spec.md` is complete for this slice, incorporates the
  clarification choices, and excludes unsupported reference-image behavior.
- **Acceptance criteria — PASS**: Six independently testable stories use
  Given/When/Then scenarios; functional, accessibility, responsive, test, and
  measurable success requirements are defined.
- **Test-first — PASS**: The plan requires focused service/API/UI tests before
  production behavior, followed by full regression. Visual, screen-reader,
  zoom, contrast, and moderated usability outcomes have documented manual paths
  because the current automated environments cannot establish them fully.
- **Simplicity and KISS — PASS**: One composite read, one persistence table,
  existing workflow reuse, and no new runtime dependency are the minimum
  additions that satisfy the current requirements.
- **Technology fit — PASS**: FastAPI/SQLAlchemy backend and React/Vite frontend
  remain in their established boundaries; API and UI contracts are documented.
- **Delivery workflow — PASS WITH PRE-IMPLEMENTATION ACTION**: Planning is on
  `master`. Because implementation is cross-stack, persistence-changing, and
  customer-facing, create `codex/fs-014-calendar-workspace` before production
  changes.
- **Verification before commit — PASS**: Focused and full commands, performance
  thresholds, browser checks, and residual human acceptance are documented in
  this plan and [quickstart.md](quickstart.md).

### Post-design gate

The design artifacts introduce no constitution violation. The data model adds
only the persistence demanded by clarified cross-reload outcomes. The shared
validation evaluator has two concrete consumers—live Working records and
Published snapshot records—and prevents duplicate domain rules. Contracts
preserve the existing List implementation, earlier-slice mutation ownership,
and FS-018 navigation. No unresolved clarification or speculative dependency
remains.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Add one bounded, revision-scoped GET response
   and one table containing the latest outcome per revision/course/operation
   kind. Keep `CourseSchedulePage` as coordinator, introduce a focused calendar
   workspace component and pure date/filter/summary helpers, and adapt the
   existing `DraftSchedulePanel` Courses overview as List mode. Continue to
   invoke the existing correction and lifecycle components.
2. **Necessary abstractions**:
   - `calendar_workspace` service assembles one atomic response and canonical
     contributor sets required across five operational metrics.
   - `planning_outcomes` helper centralizes the same-key/newer-result upsert
     used by four concrete operation kinds.
   - small pure validation records/evaluators allow established rules to
     evaluate both live Working ORM rows and immutable Published snapshot JSON
     without rule duplication.
   - client calendar workspace utilities provide UTC-safe ISO date arithmetic
     and deterministic filtering/filtered-summary projection shared by Week,
     Day, Month, and List.
3. **Deliberately excluded**: calendar/date/state/router/animation libraries;
   virtualization at the approved scale; repositories, factories, plug-in
   frameworks, event sourcing, outcome audit history, background jobs, a
   generic analytics/read-model platform, a generic validation framework, new
   endpoints per panel/filter/mode, a separate Dashboard or List, rebuilding
   existing editors, drag/drop/resize, recurring-session support, external
   synchronization, new optimization behavior, and broader access control.

## Project Structure

### Documentation (this feature)

```text
specs/014-calendar-planning-workspace/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- calendar-workspace.openapi.yaml
|   `-- calendar-workspace-ui.md
|-- checklists/
|   `-- workspace-validation.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- calendar_workspace.py
|   |-- db/
|   |   |-- migrations/
|   |   |   `-- 0008_calendar_workspace_outcomes.py
|   |   `-- schema.py
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   `-- calendar_workspace.py
|   |-- services/
|   |   |-- calendar_workspace.py
|   |   |-- planning_outcomes.py
|   |   |-- draft_schedule_validation.py
|   |   `-- schedule_lifecycle.py
|   `-- main.py
`-- tests/
    |-- calendar_workspace_fixtures.py
    |-- api/
    |   `-- test_calendar_workspace.py
    |-- db/
    |   `-- test_migrations.py
    |-- performance/
    |   `-- test_calendar_workspace_performance.py
    `-- services/
        |-- test_calendar_workspace.py
        `-- test_planning_outcome_retention.py

client/
|-- src/
|   |-- api/
|   |   |-- calendarWorkspace.ts
|   |   `-- calendarWorkspace.test.ts
|   |-- components/
|   |   |-- CalendarPlanningWorkspace.tsx
|   |   |-- CalendarPlanningWorkspace.test.tsx
|   |   |-- calendarWorkspaceUtils.ts
|   |   |-- calendarWorkspaceUtils.test.ts
|   |   |-- DraftSchedulePanel.tsx
|   |   `-- ScheduleLifecyclePanel.tsx
|   |-- pages/
|   |   |-- CourseSchedulePage.tsx
|   |   `-- scheduleSnapshot.ts
|   |-- test/
|   |   `-- calendarWorkspaceFixtures.ts
|   `-- App.css
`-- README.md
```

**Structure Decision**: Use the existing FastAPI and React/Vite applications.
The listed new files isolate the composite read, outcome retention, calendar
presentation, and pure view derivations. Existing generation, optimization,
exam, lifecycle, validation, Schedule page, Courses overview, navigation, and
editor files are modified only where they must supply or consume FS-014 context.
Implementation tasks must identify every touched existing endpoint/service and
its test; this tree is not authorization for unrelated refactoring.

## Design and Delivery Sequence

### Phase 0 — Research complete

[research.md](research.md) records the chosen response boundary, retention
semantics, Published validation strategy, aggregation identities, List reuse,
date approach, responsive/accessibility model, failure atomicity, migration,
and verification approach. All planning unknowns are resolved.

### Phase 1 — Data and contracts complete

- [data-model.md](data-model.md) defines `PlanningOutcome`, snapshot v2
  compatibility, transient workspace records, canonical findings, summaries,
  filter state, and availability transitions.
- [calendar-workspace.openapi.yaml](contracts/calendar-workspace.openapi.yaml)
  defines the single public read and retained-outcome representation.
- [calendar-workspace-ui.md](contracts/calendar-workspace-ui.md) defines mode,
  List parity, filter, traceability, detail/action, responsive, accessibility,
  and failure behavior.
- [quickstart.md](quickstart.md) defines runnable automated and manual
  acceptance evidence.

### Implementation sequence for task generation

1. Create the feature branch and write migration/retention tests before the
   outcome table and operation upserts.
2. Write pure validation and aggregation tests before adapting existing rule
   evaluation or adding the composite service.
3. Write API contract/context-isolation tests before registering the workspace
   endpoint.
4. Write UTC-date/filter/summary utility tests and API client tests.
5. Write workspace and existing Courses overview parity tests before adapting
   List and adding Week/Day/Month presentation.
6. Connect existing correction/lifecycle actions and test atomic refresh,
   failure, and focus behavior.
7. Complete full regression, deterministic performance, real-browser
   accessibility/responsive/reference validation, and later moderated
   acceptance.

## Complexity Tracking

No constitution violations require exceptions. The new table and small shared
validation evaluator are justified current needs rather than optional
architecture.

## Verification Plan

Run from repository root unless a command changes directory:

```powershell
python -m pytest backend/tests/db/test_migrations.py
python -m pytest backend/tests/services/test_calendar_workspace.py backend/tests/services/test_planning_outcome_retention.py
python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py backend/tests/api/test_conflict_aware_generation.py backend/tests/api/test_exam_scheduling.py backend/tests/api/test_schedule_lifecycle.py
python -m pytest backend/tests/performance/test_calendar_workspace_performance.py
python -m pytest backend/tests

Set-Location client
npm run test -- src/api/calendarWorkspace.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/calendarWorkspaceUtils.test.ts src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/ScheduleLifecyclePanel.test.tsx src/components/ApplicationNavigation.test.tsx src/App.test.tsx
npm run test
npm run lint
npm run build
```

Expected automated evidence:

- exact revision isolation and Published current-validation behavior;
- latest-outcome retention/supersession and no fabricated backfill;
- exact aggregation/contributor reconciliation and zero/unavailable semantics;
- Week/Day/Month/List behavior with List parity and no duplicate list;
- filter intersections and non-mutation;
- traceability, existing action handoff, atomic refresh, failure/recovery, and
  FS-009–FS-013/FS-018 regression;
- deterministic reference-scale timing.

Manual evidence required before final acceptance:

- keyboard and supported screen-reader/browser workflows;
- contrast, 320 CSS-pixel width, 200% zoom, dense dates, and FS-018 navigation
  access;
- documented visual comparison to both UI references;
- at least 10 actual representative reviewers for SC-004 through SC-006.

Manual acceptance criteria must remain reported as pending until performed.

## Agent Context Update

The standard `.specify` agent-context update script is not present in this
repository, so no generated agent context could be updated and no substitute
file was invented. The repository-local spec, research, data model, contracts,
quickstart, and this plan remain the authoritative planning context.
