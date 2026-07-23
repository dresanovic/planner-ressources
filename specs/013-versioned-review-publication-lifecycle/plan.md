# Implementation Plan: FS-013 Versioned Review and Publication Lifecycle

**Working Branch**: `master` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-versioned-review-publication-lifecycle/spec.md`

## Summary

Add a semester-wide planner-controlled schedule lifecycle around the teaching and exam behavior delivered through FS-012. The existing `DraftSchedule`/`DraftSession` and `ExamSession` rows remain the one mutable materialization of an active Draft or Ready for review revision. New revision metadata and ordered lifecycle-event records identify and constrain that workspace, while Published, superseded, and abandoned revisions retain a canonical versioned snapshot document containing the semester's teaching sessions, exam sessions, planner-visible labels, and publication conditions. A focused lifecycle service performs state transitions, snapshot capture/restoration, stale-state checks, and atomic replacement publication. Additive FastAPI contracts and focused React components expose current-versus-working state, explicit prepare/confirm publication, abandon/restore, and on-demand history without adding authentication, approval, feedback, external publication, or field-level audit behavior.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0.2 and React 19.2.7 frontend

**Primary Dependencies**: FastAPI 0.139.0, Pydantic 2.13.4, SQLAlchemy 2.0.45, Alembic 1.18.0; React 19, Vite 8.1.1

**Storage**: SQLAlchemy persistence with SQLite by default (`DATABASE_URL` remains configurable); existing mutable teaching/exam tables plus new `schedule_revisions` and `schedule_revision_events` tables; inactive revision content stored as a versioned JSON snapshot document; custom sequential schema initialization plus migration `0007_versioned_schedule_lifecycle.py`

**Testing**: pytest 9.1.1 for backend service, API, migration, concurrency, regression, and performance tests; Vitest 4.0.16 with the current native DOM/createRoot conventions; ESLint; TypeScript/Vite build; runtime FastAPI OpenAPI assertions

**Target Platform**: FastAPI service on the existing supported server environment and modern desktop browsers used by planner users

**Project Type**: Full-stack web application

**Performance Goals**: For a reference semester with 100 courses, 500 teaching sessions, and 100 exam sessions, each publication preparation, completed publication, successor materialization, and current-publication read completes within 2 seconds; an ordered 100-revision history summary loads within 2 seconds without loading every historical snapshot body

**Constraints**: No new dependency; FS-012 must be integrated first; exactly one active working revision and, after first publication, exactly one current Published revision per semester; a semester with no lifecycle revision requires an explicit planner-triggered Start Draft action before scheduling writes or publication; existing scheduling writes are permitted only while an active Draft or Ready for review revision exists; persisted lifecycle timestamps are UTC instants and API timestamps are RFC 3339 offset-bearing values, while planner-facing display uses Europe/Vienna with an explicit timezone indication; Published/superseded snapshot display must not join to mutable catalog labels; publication warnings remain non-blocking; replacement and its two history events complete in one transaction with `superseded` immediately before `published`; no course-level publication, approval, authentication, lecturer feedback, automatic or external publication, or field-by-field edit audit

**Scale/Scope**: One planner role; semester-wide publication; one active working revision; one current publication after first publish; complete retained revision/event metadata; historical snapshot bodies loaded on demand; reference validation up to 100 revisions, 100 courses, 500 teaching sessions, and 100 exams

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- **Spec-first — PASS**: [spec.md](spec.md) defines the bounded planner-only lifecycle, 32 functional requirements, independently testable stories, edge cases, and measurable outcomes before production work.
- **Acceptance criteria — PASS**: All four user stories include independent test paths and Given/When/Then acceptance scenarios; the four requested clarification topics are resolved in requirements and assumptions.
- **Test-first — PASS**: Migration, service, API, concurrency, client API, component, page, regression, accessibility, and performance tests listed below and in [quickstart.md](quickstart.md) must be written before their corresponding production behavior.
- **Simplicity and KISS — PASS**: The design adds two persisted concepts and one focused service. It reuses existing mutable schedule tables, transaction boundaries, optimistic revisions, snapshot-token conventions, dialogs, refresh behavior, and Schedule page orchestration.
- **Technology fit — PASS**: Backend remains FastAPI/SQLAlchemy; frontend remains React/Vite; [contracts/schedule-lifecycle.openapi.yaml](contracts/schedule-lifecycle.openapi.yaml) defines the cross-stack boundary.
- **Delivery workflow — PASS WITH PRE-IMPLEMENTATION ACTION**: Planning currently shares the in-progress FS-012 branch. Because FS-013 depends on FS-012 and is a cross-stack persistence feature, production implementation must begin from integrated FS-012 on `codex/fs-013-versioned-publication` or another approved FS-013 feature branch.
- **Verification before commit — PASS**: Concrete backend, client, contract, migration, concurrency, performance, and end-to-end commands are listed under Verification Plan.

### Post-Design Re-check

- The design does not version every existing scheduling row or introduce a generic repository, event-sourcing framework, state-machine library, client state library, snapshot storage service, or external publication adapter.
- A canonical JSON snapshot is justified because inactive revisions are immutable aggregate documents read or restored as a whole; individual historical sessions are not independently queried or edited in this slice.
- A separate lifecycle-event table is required to retain every Ready/Draft, publish/supersede, abandon, and restore event in stable order; it is not a field-level edit audit.
- Existing live teaching/exam rows remain the only mutable workspace. Server-side guards at existing write boundaries prevent published-only semesters and historical views from being edited in place.
- Partial unique indexes and the established semester transaction-claim pattern enforce the one-working and one-current-publication invariants under races; optimistic row versions and opaque state/publication tokens handle stale user actions.
- History summaries and selected revision content use separate reads, so complete retained history does not force every historical session snapshot into the lifecycle overview.
- All constitution gates remain passed. No exception or complexity waiver is required.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Keep the current teaching and exam tables as one mutable semester workspace; add `ScheduleRevision` metadata, `ScheduleRevisionEvent` history, and a canonical snapshot document for each inactive revision. Add one lifecycle service, one router/schema module, one client API module, one lifecycle panel, and focused publication/abandon confirmation dialogs inside the existing Schedule page.
2. **Necessary abstractions**: `schedule_lifecycle` owns state transitions, snapshot capture/restoration, transition guards, state/publication tokens, and lifecycle reads because the same authority must protect teaching generation, manual teaching mutations, exam mutations, and UI actions. A canonical snapshot serializer/deserializer is required to make Published/superseded content independent of mutable catalog rows and to restore abandoned/published content safely.
3. **Deliberately excluded**: Per-row temporal tables, event sourcing, a generic workflow/state-machine framework, a generic repository layer, Redux or another client state library, a new form framework, object storage, field-by-field audit, revision diffs, independent course publication, mandatory approval, lecturer review, authentication/authorization, notification delivery, external publication adapters, automatic publication, and FS-014 calendar-workspace redesign.

## Project Structure

### Documentation (this feature)

```text
specs/013-versioned-review-publication-lifecycle/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- schedule-lifecycle.openapi.yaml
|   `-- working-revision-guards.md
|-- checklists/
|   `-- requirements.md
|-- validation/
|   |-- automated-tests.md
|   |-- quickstart-results.md
|   |-- usability-results.md
|   `-- final-review.md
`-- tasks.md                              # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   |-- schedule_lifecycle.py
|   |   |-- draft_schedule.py             # require working revision identity
|   |   |-- multi_course_generation.py    # require working revision identity
|   |   |-- conflict_aware_generation.py  # require working revision identity
|   |   `-- exam_scheduling.py             # require working revision identity
|   |-- schemas/
|   |   |-- schedule_lifecycle.py
|   |   |-- draft_schedule.py             # lifecycle identity additions
|   |   |-- multi_course_generation.py    # lifecycle identity/token additions
|   |   |-- conflict_aware_generation.py  # lifecycle identity/token additions
|   |   `-- exam_scheduling.py            # lifecycle identity/token additions
|   |-- services/
|   |   |-- schedule_lifecycle.py
|   |   |-- draft_schedule_repository.py # guard teaching mutations
|   |   |-- multi_course_generation.py   # include working revision in prepared writes
|   |   |-- conflict_aware_generation.py # guard semester replacement
|   |   |-- exam_scheduling.py            # guard exam-session mutations
|   |   |-- academic_catalog.py           # protect historical source references
|   |   `-- resource_catalog.py           # protect historical source references
|   |-- models/
|   |   `-- planning.py                   # add revision and event models
|   |-- db/
|   |   |-- schema.py
|   |   `-- migrations/
|   |       `-- 0007_versioned_schedule_lifecycle.py
|   `-- main.py
`-- tests/
    |-- schedule_lifecycle_fixtures.py
    |-- api/
    |   |-- test_schedule_lifecycle.py
    |   |-- test_draft_schedule.py
    |   |-- test_multi_course_generation.py
    |   |-- test_conflict_aware_generation.py
    |   `-- test_exam_scheduling.py
    |-- services/
    |   |-- test_schedule_lifecycle.py
    |   |-- test_schedule_lifecycle_concurrency.py
    |   |-- test_academic_catalog.py
    |   `-- test_resource_catalog.py
    |-- performance/test_schedule_lifecycle_performance.py
    `-- db/test_migrations.py

client/
`-- src/
    |-- api/
    |   |-- scheduleLifecycle.ts
    |   |-- scheduleLifecycle.test.ts
    |   |-- draftSchedule.ts
    |   |-- draftSchedule.test.ts
    |   |-- multiCourseDraftGeneration.ts
    |   |-- multiCourseDraftGeneration.test.ts
    |   |-- conflictAwareGeneration.ts
    |   |-- conflictAwareGeneration.test.ts
    |   |-- examScheduling.ts
    |   `-- examScheduling.test.ts
    |-- components/
    |   |-- ScheduleLifecyclePanel.tsx
    |   |-- ScheduleLifecyclePanel.test.tsx
    |   |-- PublicationConfirmationDialog.tsx
    |   |-- PublicationConfirmationDialog.test.tsx
    |   |-- AbandonRevisionDialog.tsx
    |   |-- AbandonRevisionDialog.test.tsx
    |   |-- DraftSchedulePanel.tsx
    |   |-- DraftSchedulePanel.test.tsx
    |   |-- ExamGenerationPanel.tsx
    |   `-- ExamGenerationPanel.test.tsx
    |-- pages/
    |   |-- CourseSchedulePage.tsx
    |   `-- CourseSchedulePage.test.tsx
    `-- App.css
```

**Structure Decision**: Keep the existing full-stack application layout. Lifecycle logic receives a dedicated router/schema/service because it is a semester aggregate spanning teaching and exams. Existing scheduling services retain their current responsibilities and call the lifecycle guard at their mutation boundaries. `CourseSchedulePage` remains the authoritative semester orchestrator, while lifecycle presentation and confirmation behavior live in focused components. `DraftSchedulePanel` gains only dynamic context/read-only support so historical views can reuse it without leaking current catalog labels or edit controls.

## Phase 0: Research Decisions

Research decisions and rejected alternatives are recorded in [research.md](research.md). All planning-sensitive questions are resolved, including current-data backfill, snapshot content, live-workspace ownership, state and concurrency enforcement, atomic publication, warning preparation, API shape, client integration, history loading, and performance boundaries.

## Phase 1: Design Outputs

- [data-model.md](data-model.md) defines revision/event persistence, the canonical snapshot document, transient publication preparation, invariants, validation, migration/backfill, and lifecycle transitions.
- [contracts/schedule-lifecycle.openapi.yaml](contracts/schedule-lifecycle.openapi.yaml) defines overview/history, selected-revision content, working-revision creation, authoritative publication preparation, explicit transitions, and structured stale/validation errors. [contracts/working-revision-guards.md](contracts/working-revision-guards.md) defines the required `scheduleRevisionId` amendment for every existing teaching/exam schedule mutation contract.
- [quickstart.md](quickstart.md) defines migration, backend, client, concurrency, immutable-snapshot, warning, history, accessibility, and reference-performance validation.
- The repository contains no `.specify/scripts/powershell/update-agent-context.ps1` or equivalent agent-context updater. The required script cannot be run, and no substitute project file is invented.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Run from the repository root unless a working directory is stated:

1. `python -m pytest backend/tests/db/test_migrations.py`
2. `python -m pytest backend/tests/services/test_schedule_lifecycle.py backend/tests/services/test_draft_schedule_repository.py backend/tests/services/test_exam_scheduling.py`
3. `python -m pytest backend/tests/api/test_schedule_lifecycle.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py backend/tests/api/test_exam_scheduling.py`
4. `python -m pytest backend/tests/performance/test_schedule_lifecycle_performance.py`
5. `python -m pytest backend/tests`
6. In `client/`: `npm run test -- src/api/scheduleLifecycle.test.ts src/components/ScheduleLifecyclePanel.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/components/AbandonRevisionDialog.test.tsx src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx`
7. In `client/`: `npm run test`
8. In `client/`: `npm run lint`
9. In `client/`: `npm run build`
10. Assert the runtime FastAPI OpenAPI paths, aliases, enums, tokens, and response envelopes against [contracts/schedule-lifecycle.openapi.yaml](contracts/schedule-lifecycle.openapi.yaml), and assert every operation listed in [contracts/working-revision-guards.md](contracts/working-revision-guards.md) requires `scheduleRevisionId`; the repository has no separate OpenAPI-validator dependency.
11. Run the file-backed SQLite concurrency cases for competing create/restore and publish/publish operations and verify the database retains at most one working revision and exactly one current publication after first publish.
12. Execute the end-to-end and accessibility scenarios in [quickstart.md](quickstart.md), recording first publication, safe replacement, immutable context, warning-confirmed publication, abandon/restore, stale refresh, complete history, keyboard dialog behavior, and reference-scale timing evidence before commit.
