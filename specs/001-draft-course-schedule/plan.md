# Implementation Plan: Draft Course Schedule

**Working Branch**: `master` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-draft-course-schedule/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement explicit draft schedule generation for one course. The backend will expose a small contract for admins to trigger generation from existing planning inputs and retrieve the generated draft sessions. The core scheduling rules will live in a pure service that is tested first: unit splitting, 45-minute teaching units, 10-minute breaks, selected Study Type Time Window preference, fallback windows, capacity validation, no partial drafts, and replacement of existing generated drafts for the same course. The frontend will provide a minimal admin-triggered generation flow and display either generated sessions or all detected failure reasons.

## Technical Context

**Language/Version**: Python 3 with existing FastAPI backend; TypeScript with existing React/Vite frontend

**Primary Dependencies**: FastAPI, Pydantic, pytest, React, Vite; add SQLAlchemy and Alembic for persistence and migrations

**Storage**: SQLite for the first implementation, modeled through SQLAlchemy/Alembic so PostgreSQL can be introduced later without rewriting feature logic

**Testing**: Backend pytest service tests first, then endpoint tests; frontend build/lint checks plus focused UI tests if a test runner is introduced in tasks

**Target Platform**: Browser-based client-server web application; the backend runs as a server process that can serve multiple browser clients, with local execution used only for development and verification

**Project Type**: Client-server web application

**Performance Goals**: Admin receives success or all validation failures for a single-course generation request in under 1 minute; service-level generation for normal semester-sized inputs should complete fast enough for interactive use

**Constraints**: Keep this slice limited to one course, one lecturer, one room, one Cohort, one semester, one study type, and generated draft sessions only. No holiday handling, exams, multi-course conflicts, manual drag/drop editing, or calendar UI polish.

**Scale/Scope**: First slice targets one generation request at a time for semester-sized course data. Data model should not block later expansion to hundreds of lecturers and many courses, but this feature does not optimize a full semester schedule.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. Feature spec exists at `specs/001-draft-course-schedule/spec.md` with clarifications integrated.
- **Acceptance criteria**: PASS. User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: PASS. The plan identifies backend service and endpoint tests before production code, with frontend verification for admin interaction.
- **Simplicity**: PASS with justified additions. SQLAlchemy/Alembic are added because replacement semantics and future PostgreSQL migration require structured persistence. Direct in-memory storage was rejected because it would not validate draft replacement or migration-ready data boundaries.
- **Technology fit**: PASS. Backend remains FastAPI; frontend remains React with Vite; API contracts are documented in `contracts/`.
- **Delivery workflow**: PASS. Current branch is `master`; this is acceptable as a solo Spec Kit workflow if the working tree remains controlled and verification passes before commit.
- **Verification before commit**: PASS. Commands and expected evidence are listed in the Verification Plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-draft-course-schedule/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- draft-schedule.openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- draft_schedule.py
|   |-- db/
|   |   |-- base.py
|   |   |-- session.py
|   |   `-- migrations/
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   `-- draft_schedule.py
|   |-- services/
|   |   `-- schedule_generation.py
|   `-- main.py
`-- tests/
    |-- api/
    |   `-- test_draft_schedule.py
    `-- services/
        `-- test_schedule_generation.py

client/
|-- src/
|   |-- api/
|   |   `-- draftSchedule.ts
|   |-- components/
|   |   `-- DraftSchedulePanel.tsx
|   |-- pages/
|   |   `-- CourseSchedulePage.tsx
|   `-- App.tsx
`-- package.json
```

**Structure Decision**: Use the existing `backend/` and `client/` applications. Put deterministic scheduling behavior in `backend/app/services/schedule_generation.py` so most TDD can happen without HTTP or UI. Keep API and UI layers thin: endpoint validates/persists/replaces drafts, frontend triggers generation and shows returned sessions or failure reasons.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Add SQLAlchemy and Alembic | Draft sessions must be persisted and replaced per course, and the project should migrate cleanly from SQLite to PostgreSQL later. | In-memory storage would be simpler but would not validate persistence boundaries, replacement behavior, or migration readiness. |

## Verification Plan

Before commit, run:

```text
cd backend
python -m pytest
```

```text
cd client
npm run lint
npm run build
```

Expected evidence:

- Backend service tests cover unit splitting, break-inclusive duration, selected-window preference, fallback windows, once-per-week default, multi-session week fallback, one-session-per-day limit, capacity failure, invalid preference failure, impossible scheduling failure, and draft replacement.
- Backend API tests cover successful generation, retrieving generated sessions, rejecting insufficient capacity, returning all detected failure reasons, and avoiding partial draft creation.
- Frontend verification confirms the admin can trigger generation and see either generated sessions or all returned failure reasons.

## Phase 0 Research Summary

Research decisions are captured in [research.md](./research.md). All technical choices are resolved for planning.

## Phase 1 Design Summary

Design artifacts generated:

- [data-model.md](./data-model.md)
- [contracts/draft-schedule.openapi.yaml](./contracts/draft-schedule.openapi.yaml)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Spec-first**: PASS. Design artifacts trace back to the approved spec and clarifications.
- **Acceptance criteria**: PASS. Data model, contracts, and quickstart preserve the Given/When/Then scenarios.
- **Test-first**: PASS. Quickstart and plan require service tests before endpoint/UI implementation.
- **Simplicity**: PASS. New persistence dependencies are limited and justified; scheduling logic remains a pure service.
- **Technology fit**: PASS. Contracts document the FastAPI/React boundary.
- **Delivery workflow**: PASS. Continue on `master` only with controlled changes and verification.
- **Verification before commit**: PASS. Backend and frontend commands are listed.
