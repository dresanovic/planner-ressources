# Implementation Plan: Review Generated Schedule In Planner UI

**Working Branch**: `master` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-review-generated-schedule/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Slice 2 upgrades the existing single-course draft schedule experience from a generation table into an inspection-focused planner review UI. The implementation will keep the current single-course draft schedule endpoint, enrich the returned schedule/session contract with the display context required by the spec, and add frontend review controls for list mode, weekly calendar-style mode, and filters by the current course, Cohort, lecturer, room, and study type. Manual editing, conflict detection, semester-wide multi-course review, and validation alerts remain out of scope.

## Technical Context

**Language/Version**: Python 3.12-compatible backend code; TypeScript 6.0 React frontend

**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic for backend; React 19 with Vite 8 for frontend

**Storage**: Existing SQLite-backed SQLAlchemy planning tables for local development; no new persistence tables required

**Testing**: Backend `pytest`; frontend TypeScript build and ESLint via `npm run build` and `npm run lint`; dev-only Vitest/jsdom component and helper tests for frontend UI behavior

**Target Platform**: Browser-based planner UI backed by the local FastAPI service

**Project Type**: Web application with FastAPI backend and React/Vite frontend

**Performance Goals**: Staff can identify session context within 10 seconds; filter and view-mode interactions complete in one to two user interactions; no server-side optimization required for this single-course slice

**Constraints**: Preserve single-course scope; avoid new runtime dependencies unless implementation proves existing React/TypeScript and CSS are insufficient; no manual edit controls; no conflict, holiday, exam, dashboard, or multi-course planning behavior

**Scale/Scope**: Current selected course only, using the generated Draft Sessions for that course; expected session counts are semester-course sized, not full institutional timetables

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. [spec.md](./spec.md) exists and includes scope, user stories, requirements, acceptance scenarios, clarifications, and success criteria.
- **Acceptance criteria**: PASS. User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: PASS. Backend contract tests and frontend behavior checks are identified before production implementation.
- **Simplicity**: PASS. No new tables, services, background jobs, or runtime dependencies are planned. The response contract is enriched through existing relationships and the UI is implemented in the existing React app.
- **Technology fit**: PASS. Backend work remains FastAPI/Pydantic/SQLAlchemy; frontend work remains React/Vite; cross-stack contracts are documented in [contracts/draft-schedule-review.md](./contracts/draft-schedule-review.md).
- **Delivery workflow**: PASS. Current branch is `master`; this planning-only change is a small solo documentation change. Implementation can remain on `master` only if the worktree is intentionally kept clean and verification passes, otherwise a feature branch is recommended.
- **Verification before commit**: PASS. Required verification commands are listed below.

## Project Structure

### Documentation (this feature)

```text
specs/002-review-generated-schedule/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- draft-schedule-review.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- draft_schedule.py
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   `-- draft_schedule.py
|   `-- services/
|       `-- draft_schedule_repository.py
`-- tests/
    `-- api/
        `-- test_draft_schedule.py

client/
|-- src/
|   |-- api/
|   |   `-- draftSchedule.ts
|   |-- components/
|   |   `-- DraftSchedulePanel.tsx
|   |-- pages/
|   |   `-- CourseSchedulePage.tsx
|   |-- App.css
|   `-- App.tsx
`-- package.json
```

**Structure Decision**: Use the existing full-stack Resource Planner layout. Backend changes stay inside the current draft schedule API/schema/repository surface because Slice 2 reviews data created by Slice 1. Frontend changes stay inside the existing course schedule page and draft schedule panel unless tasks identify a small local component split for review controls.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dev-only Vitest/jsdom test tooling | Slice 2 requires practical frontend UI behavior tests for list rendering, view switching, filters, empty states, and no-results states. | `npm run build` and `npm run lint` verify types/style but do not exercise user interactions or DOM behavior required by the spec. Manual-only verification would weaken the constitution's test-first requirement. |

## Phase 0: Research Summary

See [research.md](./research.md). Decisions:

- Keep the existing single-course endpoint and enrich its response contract rather than adding semester-wide review endpoints.
- Return display context with the draft schedule response so the UI can filter and render without hard-coded mock labels.
- Implement weekly view as a simple grouped review presentation, not a drag-and-drop calendar.
- Use client-side filtering for this slice because the visible dataset is limited to one selected course.

## Phase 1: Design Summary

Design artifacts generated:

- [data-model.md](./data-model.md)
- [contracts/draft-schedule-review.md](./contracts/draft-schedule-review.md)
- [quickstart.md](./quickstart.md)

Agent context update: skipped because this repository does not contain an agent-context update script under `.specify/scripts/powershell/`.

## Post-Design Constitution Check

- **Spec-first**: PASS. Design artifacts align with the approved Slice 2 spec and clarification.
- **Acceptance criteria**: PASS. Contracts and quickstart map to the user stories and measurable outcomes.
- **Test-first**: PASS. Quickstart and future tasks must create/update backend API tests and frontend behavior checks before implementation.
- **Simplicity**: PASS. The design avoids new storage, a new API family, and new frontend dependencies.
- **Technology fit**: PASS. Contracts remain FastAPI-compatible and frontend responsibilities remain in React/Vite.
- **Delivery workflow**: PASS. Larger implementation should use a feature branch if the worktree remains broad or dirty.
- **Verification before commit**: PASS. Commands below define required evidence.

## Verification Plan

Required before committing implementation:

```text
cd backend
python -m pytest

cd ../client
npm run lint
npm run test
npm run build
```

Feature-specific verification:

- Backend API tests confirm generated/read schedule responses include course, Cohort, lecturer, room, and study type context.
- Frontend tests or documented UI verification confirm list/weekly mode switching preserves visible sessions.
- Frontend tests or documented UI verification confirm filters combine by all active values and show clear empty/no-results states.
- Build output confirms TypeScript types match the updated backend response contract.
