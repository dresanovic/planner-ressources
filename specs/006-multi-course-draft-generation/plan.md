# Implementation Plan: Multi-Course Draft Generation

**Working Branch**: `master` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-multi-course-draft-generation/spec.md`

## Summary

Slice 6 adds foreground generation for 2-50 selected courses in one semester, with 1-50-course failed-only retries. The backend will reuse the existing deterministic single-course generator behind a focused multi-course orchestration service, derive each course's own saved constraints or defaults, and return one outcome per course without attempting conflict avoidance. A read-only preparation contract will identify same-semester replacement targets and provide optimistic revision snapshots for confirmation. Successful course candidates will be persisted in one outer transaction with per-course savepoints; expected validation or stale-data failures remain course-level outcomes, while unexpected failures roll back the whole attempt. Draft Schedule identity will change from globally unique per course to unique per course and semester. The React page will add a separate several-courses mode, replacement confirmation, transient result summary, failed-only retry, and a refreshed semester overview that continues to show Slice 5 alerts.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0, React 19, and Node.js 26 frontend toolchain.

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, Alembic 1.18, pytest 9; React 19, Vite 8, Vitest 4, and ESLint 10. No new runtime or test dependency is planned.

**Storage**: Existing SQLAlchemy relational model with SQLite as the current default. Add a composite Draft Schedule uniqueness rule for `(course_id, semester_id)` plus integer optimistic revisions on Draft Schedule and Generation Constraint Set. Do not persist batch operations, result summaries, or retry sets.

**Testing**: Backend pytest migration, repository, orchestration, and API tests; frontend Vitest API/component/page tests plus `npm run lint` and `npm run build`.

**Target Platform**: Browser planner UI calling the FastAPI backend; local SQLite remains the default development database.

**Project Type**: Full-stack web application with FastAPI backend and React/Vite frontend.

**Performance Goals**: The reference environment uses file-backed SQLite, one FastAPI process, a production client build, 50 seeded valid courses, a warm start, and no artificial latency. The median of three runs from activating Generate until the complete result summary is rendered must be at most 10 seconds. Preparation and execution use bounded bulk reads whose query count does not grow once the selected-course input set has been loaded, avoid per-course client round trips, and perform one semester-overview refresh after the batch result.

**Constraints**: Initial operations accept 2-50 distinct courses and retries accept 1-50 failed courses. Each course uses its own saved constraints or defaults. Same-semester replacements require explicit confirmation. Expected course failures allow partial success; unexpected operation failures are atomic. Changed drafts or constraints produce stale course outcomes and preserve newer data. Cross-semester schedules must coexist. Conflict alerts remain non-blocking, and generation does not optimize around them. Preserve single-course generation and manual editing. Do not add persistent batch history, background work, holiday/exam behavior, course-semester eligibility administration, multiple lecturers/rooms, or session CRUD expansion.

**Scale/Scope**: One office-staff foreground operation, one selected semester, and at most 50 courses. Current schedule and alert volumes are small enough for synchronous generation and straightforward in-process orchestration. SQLite concurrency is limited, so correctness relies on optimistic revisions and conditional writes rather than row locking.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. `specs/006-multi-course-draft-generation/spec.md` exists and includes clarified scope, requirements, acceptance scenarios, concurrency rules, limits, and measurable outcomes.
- **Acceptance criteria**: PASS. Four independently testable user stories use Given/When/Then scenarios and cover all-success, partial failure, replacement safety, retry, cross-semester retention, and alert refresh.
- **Test-first**: PASS. This plan requires migration, repository, orchestration, API, frontend component, and page/API tests before production changes.
- **Simplicity**: PASS. The design reuses the existing generator, repository model, semester overview, and alert computation. It adds only focused batch modules, one migration, and optimistic revision fields required by the approved stale-data behavior. No new dependency, worker, or persisted operation model is introduced.
- **Technology fit**: PASS. Backend remains FastAPI/SQLAlchemy/Alembic; frontend remains React/Vite; the preparation, execution, and updated draft response contracts are documented in `contracts/openapi.yaml`.
- **Delivery workflow**: PASS for planning. The current branch is `master` and only specification/design artifacts are being created. Because implementation spans migration, transaction, API, and customer-facing UI boundaries, implementation should move to a `codex/` feature branch unless the verified solo-change condition is deliberately retained.
- **Verification before commit**: PASS. Concrete backend and frontend commands and feature evidence are listed below and in `quickstart.md`.

## Project Structure

### Documentation (this feature)

```text
specs/006-multi-course-draft-generation/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- README.md
|-- app/
|   |-- main.py
|   |-- api/
|   |   |-- draft_schedule.py
|   |   `-- multi_course_generation.py
|   |-- db/migrations/
|   |   |-- 0001_create_planning_tables.py
|   |   `-- 0002_course_semester_drafts.py
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   |-- draft_schedule.py
|   |   `-- multi_course_generation.py
|   `-- services/
|       |-- draft_schedule_repository.py
|       |-- schedule_generation.py
|       `-- multi_course_generation.py
`-- tests/
    |-- multi_course_fixtures.py
    |-- api/
    |   |-- test_draft_schedule.py
    |   `-- test_multi_course_generation.py
    |-- db/
    |   `-- test_migrations.py
    `-- services/
        |-- test_draft_schedule_repository.py
        `-- test_multi_course_generation.py

client/
|-- src/
|   |-- App.css
|   |-- api/
|   |   |-- draftSchedule.ts
|   |   |-- draftSchedule.test.ts
|   |   |-- multiCourseDraftGeneration.ts
|   |   `-- multiCourseDraftGeneration.test.ts
|   |-- components/
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- MultiCourseGenerationPanel.tsx
|   |   |-- BatchResultSummary.tsx
|   |   `-- ReplacementConfirmationDialog.tsx
|   |-- pages/
|   |   |-- CourseSchedulePage.tsx
|   |   `-- CourseSchedulePage.test.tsx
|   `-- test/
|       `-- draftScheduleFixtures.ts
|-- package.json
`-- README.md
```

**Structure Decision**: Implement Slice 6 as an additive full-stack feature within the existing planner. Keep the pure placement algorithm in `schedule_generation.py` unchanged. Place request-wide coordination and transaction policy in a focused backend `multi_course_generation` service and expose it through a focused router/schema pair rather than expanding the already broad single-course route module. Add small React components for selection, confirmation, and results while keeping page-level ownership of semester, schedules, and transient batch state. Continue rendering schedules and alerts through the existing `DraftSchedulePanel`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations requiring complexity justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|

## Phase 0 Research

Research is captured in [research.md](./research.md). Key decisions are: reuse independent single-course generation; add a read-only preparation step plus an execution step; make Draft Schedules unique by course and semester; use integer optimistic revisions and conditional writes for stale detection; own commits at service/API boundaries; use one outer transaction and per-course savepoints; keep batch results transient; refresh the existing semester overview after execution; and introduce no new dependencies or background processing.

## Phase 1 Design

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

Agent context update: skipped because this repository has no `.specify/scripts/powershell/update-agent-context.ps1` or equivalent agent-context update script.

## Post-Design Constitution Check

- **Spec-first**: PASS. All design decisions trace to the clarified Slice 6 specification.
- **Acceptance criteria**: PASS. Data model, contracts, and quickstart cover selection limits, preparation/confirmation, course-specific constraints, all-success, partial/all failure, one-course retry, cross-semester retention, stale draft/constraint outcomes, operation-wide rollback, overview refresh, and non-blocking alerts.
- **Test-first**: PASS. Quickstart and verification sections require focused failing tests before migration, repository, service, API, and frontend implementation.
- **Simplicity**: PASS. The design adds no operation table, queue, worker, solver, state-management library, or UI dependency. Preparation snapshots are returned to the client rather than persisted.
- **Technology fit**: PASS. FastAPI/SQLAlchemy/Alembic and React/Vite boundaries are explicit; the cross-stack contract is documented.
- **Delivery workflow**: PASS for planning. Implementation branch choice remains explicit before production edits.
- **Verification before commit**: PASS. Required commands and expected evidence are concrete.

## Verification Plan

Before committing implementation work, run:

```powershell
cd backend
python -m pytest tests/db/test_migrations.py tests/services/test_draft_schedule_repository.py tests/services/test_multi_course_generation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py
```

```powershell
cd client
npm run test
npm run lint
npm run build
```

Feature-specific verification must prove:

- the migration preserves current data, permits the same course in different semesters, and rejects duplicate course-semester schedules;
- initial and retry size/duplicate validation is enforced;
- preparation identifies only selected same-semester replacement targets and returns immutable draft revision snapshots;
- each course uses its own saved constraints or defaults and never another course's local editor values;
- preparation and execution use bounded bulk planning-data reads verified by query-count or repository-call assertions rather than per-course database loading;
- all-success, partial-success, and all-expected-failure results contain exactly one outcome per requested course;
- nonexistent courses fail individually while valid courses continue;
- failed courses preserve schedules, manual edits, and constraints;
- cancellation performs no execution write;
- changed draft or constraint revisions yield stale course outcomes while other valid courses succeed;
- injected unexpected failures roll back every change from the attempt;
- successful regeneration affects only the selected course-semester and increments its revision;
- failed-only retry permits one course and excludes successful courses;
- the refreshed semester overview shows newly generated and pre-existing schedules with recalculated non-blocking alerts;
- transient batch results disappear after a page remount without affecting saved schedules;
- existing single-course generation, constraint editing, manual session editing, overview filters, and validation alerts remain functional;
- no conflict-aware placement, batch history, background processing, holiday/exam behavior, dashboard, multiple lecturer/room behavior, or session CRUD expansion is introduced.
- the reference performance environment uses file-backed SQLite, one FastAPI process, a production client build, 50 seeded valid courses, a warm start, and no artificial latency; the median of three user-visible runs is at most 10 seconds;
- a usability review includes at least 10 qualifying participants without batch-workflow coaching, records whether at least 90% select the named semester and at least two first-time courses and activate Generate within two minutes, and records whether at least 90% pass each comprehension and failed-only retry scenario unaided.
