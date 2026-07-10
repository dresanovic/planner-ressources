# Implementation Plan: Configurable Generation Constraints

**Working Branch**: `master` | **Date**: 2026-07-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-configurable-generation-constraints/spec.md`

## Summary

Slice 3 adds configurable generation constraints before single-course draft schedule generation. Office staff can use semester and study type defaults, override the planning period, define multiple weekly teaching windows, save successful custom constraints per course and semester, clear saved constraints back to defaults, and generate Draft Sessions only within the active constraints. The implementation extends the existing FastAPI generation endpoint, SQLAlchemy planning model, service-level scheduler input model, and React/Vite planner controls while keeping Slice 2 review filters separate from generation constraints. The planner review surface is also changed from a selected-course schedule to a semester-scoped Courses overview that lists all generated plans for the selected semester while keeping the left planning input independent.

## Technical Context

**Language/Version**: Python 3.12-compatible backend code; TypeScript 6.0 and React 19 frontend.

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x, pytest, React, Vite, Vitest, ESLint. No new runtime dependency is planned.

**Storage**: Existing SQLAlchemy relational model backed by the project database. Tests use in-memory SQLite through `Base.metadata.create_all`.

**Testing**: Backend pytest service and API tests; frontend Vitest component/unit tests plus `npm run build` and `npm run lint`.

**Target Platform**: Browser planner UI calling the local FastAPI backend.

**Project Type**: Full-stack web application with FastAPI backend and React/Vite frontend.

**Performance Goals**: Loading active generation constraints should feel part of the existing planning-options workflow; schedule generation for the single selected course should remain comfortably under the spec goal of 1 minute and should not add extra user-visible waiting beyond one backend request per generate action.

**Constraints**: Keep generation scope to one selected course, one semester, one lecturer, one room, and one Cohort. Custom planning periods must stay within the selected semester. Custom constraints save only after successful generation. Failed or blocked generation must not overwrite saved constraints. Clearing constraints deletes saved constraints for the course-semester combination and restores defaults. Generation constraints must be visually and functionally distinct from Slice 2 review filters. The central Courses overview is scoped to the selected semester and must not be driven by the selected course in the left planning input area.

**Scale/Scope**: Single-course generation with semester-scoped review of generated plans. Expected data volume is a small set of courses, semesters, study type windows, saved constraint records, and generated sessions suitable for interactive office-staff planning.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. `specs/003-configurable-generation-constraints/spec.md` exists and includes clarifications, scope, requirements, acceptance criteria, edge cases, and measurable outcomes.
- **Acceptance criteria**: PASS. User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: PASS. Verification plan identifies backend service/API tests and frontend component/unit tests to create before production code.
- **Simplicity**: PASS. Plan uses existing FastAPI, SQLAlchemy, React, and Vite structure with no new dependencies or infrastructure.
- **Technology fit**: PASS. Backend remains FastAPI; frontend remains React/Vite; cross-stack contracts are documented in `contracts/openapi.yaml`.
- **Delivery workflow**: PASS. Current branch is `master`; this planning artifact does not create production code. Implementation should either continue as a clean verified solo change or move to a feature branch if the worktree remains broad/risky.
- **Verification before commit**: PASS. Concrete backend and frontend verification commands are listed below.

## Project Structure

### Documentation (this feature)

```text
specs/003-configurable-generation-constraints/
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
|-- app/
|   |-- api/
|   |   |-- draft_schedule.py
|   |   `-- planning_options.py
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   |-- draft_schedule.py
|   |   `-- planning_options.py
|   `-- services/
|       |-- draft_schedule_repository.py
|       `-- schedule_generation.py
`-- tests/
    |-- api/
    |   `-- test_draft_schedule.py
    `-- services/
        |-- test_draft_schedule_repository.py
        `-- test_schedule_generation.py

client/
|-- src/
|   |-- api/
|   |   |-- draftSchedule.ts
|   |   `-- planningOptions.ts
|   |-- components/
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- scheduleReviewUtils.ts
|   |   `-- scheduleReviewUtils.test.ts
|   `-- pages/
|       `-- CourseSchedulePage.tsx
```

**Structure Decision**: Implement Slice 3 as a full-stack change in the existing resource planner application. Backend model, schema, repository, and generator changes live beside the existing draft schedule code. Frontend generation constraint controls live in the planning input sidebar below semester dates, while the review panel becomes a semester-scoped Courses overview with compact one-row filters.

## Complexity Tracking

No constitution violations requiring complexity justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|

## Phase 0 Research

Research is captured in [research.md](./research.md). Key decisions: store saved constraints per course-semester combination, model custom windows independently from study type windows, keep source study type window IDs optional, and save constraints only after successful generation.

## Phase 1 Design

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)
- Semester-scoped draft schedule list contract in [contracts/openapi.yaml](./contracts/openapi.yaml)

Agent context update: skipped because this repository has no `.specify/scripts/powershell/update-agent-context.ps1` or equivalent agent-context script.

## Post-Design Constitution Check

- **Spec-first**: PASS. Design artifacts trace back to the approved Slice 3 spec and clarifications.
- **Acceptance criteria**: PASS. Data model, contracts, and quickstart cover defaults, overrides, saved constraints, clearing, invalid inputs, and generation placement.
- **Test-first**: PASS. Quickstart lists test commands and the implementation tasks should create failing backend/frontend tests before production changes.
- **Simplicity**: PASS. Uses existing app boundaries and dependencies; no new service, framework, or infrastructure.
- **Technology fit**: PASS. FastAPI/React/Vite boundaries and cross-stack contracts are explicit.
- **Delivery workflow**: PASS. Planning only; implementation branch decision remains explicit before coding.
- **Verification before commit**: PASS. Commands below define expected evidence.

## Verification Plan

Before committing implementation work for this feature, run:

```powershell
cd backend
python -m pytest tests/services/test_schedule_generation.py tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

```powershell
cd client
npm run test
npm run lint
npm run build
```

Feature-specific verification should prove:

- default constraints come from the selected semester and study type windows;
- saved constraints reload per course and semester;
- custom planning periods and windows are passed into generation;
- generated Draft Sessions stay inside the active planning period and allowed windows;
- failed generation does not replace saved constraints;
- clearing constraints deletes saved course-semester constraints and restores defaults;
- generation constraint controls remain distinct from review filters.
- generation controls live with the planning input selection;
- Courses overview shows all generated plans for the selected semester and overview filters use all generated plan values rather than only the selected planning input.
