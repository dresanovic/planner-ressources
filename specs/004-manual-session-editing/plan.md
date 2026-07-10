# Implementation Plan: Manual Session Editing

**Working Branch**: `master` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-manual-session-editing/spec.md`

## Summary

Slice 4 adds manual editing for existing generated Draft Sessions in the semester Courses overview. Office staff can edit a session's date, start time, end time, and room; saved edits persist across overview filters, list/weekly modes, and later visits to the same selected semester. The implementation will reuse the existing Draft Session persistence fields for date/time/room, add a focused edit contract, extend planning options with room capacity metadata for room selection, and enforce only the Slice 4 validation rules: selected-semester date bounds, valid start/end time order, existing target session, existing replacement room, and sufficient room capacity. Conflict detection, room occupancy checks, teaching-window validation, session creation/deletion/splitting/merging, and source planning-record edits remain out of scope.

## Technical Context

**Language/Version**: Python 3.12-compatible backend code; TypeScript 6.0 and React 19 frontend.

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x, pytest, React, Vite, Vitest, ESLint. No new runtime dependency is planned.

**Storage**: Existing SQLAlchemy relational model backed by the project database. Draft Session date, start time, end time, and room fields already exist; no schema migration is planned for Slice 4. Tests use in-memory SQLite through `Base.metadata.create_all`.

**Testing**: Backend pytest repository/API tests; frontend Vitest component tests plus `npm run lint` and `npm run build`.

**Target Platform**: Browser planner UI calling the local FastAPI backend.

**Project Type**: Full-stack web application with FastAPI backend and React/Vite frontend.

**Performance Goals**: Opening and saving a manual edit should feel like the existing planner interactions: no more than one save request per edit and one overview refresh or local state update. Semester overview loading should remain interactive for the small course/session volumes used by the current planner.

**Constraints**: Edit only existing generated Draft Sessions. Date edits must stay inside the selected semester and preserve the existing one-session-per-draft-schedule-per-date invariant. End time must be later than start time. Replacement rooms must have capacity greater than or equal to the session cohort size. Room occupancy, lecturer overlap, cohort overlap, generation-window, teaching-window, holiday, and exam checks are deferred to future slices. Do not add new dependencies, background services, drag/drop editing, or broad scheduling abstractions.

**Scale/Scope**: Single-session edits inside a semester-scoped Courses overview. Expected data volume is a modest number of generated draft schedules and sessions suitable for office-staff review and manual correction.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. `specs/004-manual-session-editing/spec.md` exists and includes clarifications, scope, requirements, acceptance criteria, edge cases, and measurable outcomes.
- **Acceptance criteria**: PASS. User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: PASS. This plan identifies backend API/repository tests and frontend component/API tests to create before production code.
- **Simplicity**: PASS. Plan uses existing FastAPI, SQLAlchemy, React, and Vite structure with no new dependencies or infrastructure.
- **Technology fit**: PASS. Backend remains FastAPI; frontend remains React/Vite; cross-stack contracts are documented in `contracts/openapi.yaml`.
- **Delivery workflow**: PASS. Current branch is `master`; this planning artifact does not create production code. Implementation should either continue as a clean verified solo change or move to a feature branch if the worktree remains broad/risky.
- **Verification before commit**: PASS. Concrete backend and frontend verification commands are listed below.

## Project Structure

### Documentation (this feature)

```text
specs/004-manual-session-editing/
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
|   |-- models/
|   |   `-- planning.py
|   |-- services/
|   |   `-- draft_schedule_repository.py
|   |-- schemas/
|   |   |-- draft_schedule.py
|   |   `-- planning_options.py
|   `-- api/
|       |-- draft_schedule.py
|       `-- planning_options.py
`-- tests/
    |-- api/
    |   `-- test_draft_schedule.py
    `-- services/
        `-- test_draft_schedule_repository.py

client/
|-- src/
|   |-- components/
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- scheduleReviewUtils.ts
|   |   `-- scheduleReviewUtils.test.ts
|   |-- pages/
|   |   `-- CourseSchedulePage.tsx
|   `-- api/
|       |-- draftSchedule.ts
|       `-- planningOptions.ts
```

**Structure Decision**: Implement Slice 4 as a focused full-stack change inside the existing draft schedule and planning option boundaries. Backend edit validation and persistence live in the draft schedule repository/API. Frontend edit controls live in the existing Courses overview component and reuse the page-level overview refresh/state ownership.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations requiring complexity justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|

## Phase 0 Research

Research is captured in [research.md](./research.md). Key decisions: reuse existing Draft Session fields with no migration, edit length through end time, return an updated Draft Schedule after save, extend planning options with room capacity metadata, enforce capacity but not occupancy/conflict checks, preserve the existing one-session-per-date invariant, and preserve regeneration replacement behavior.

## Phase 1 Design

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

Agent context update: skipped because this repository has no `.specify/scripts/powershell/update-agent-context.ps1` or equivalent agent-context script.

## Post-Design Constitution Check

- **Spec-first**: PASS. Design artifacts trace back to the approved Slice 4 spec and clarifications.
- **Acceptance criteria**: PASS. Data model, contracts, and quickstart cover editing date/start/end/room, capacity rejection, semester bounds, cancel/failure behavior, overview persistence, and deferred conflict scope.
- **Test-first**: PASS. Quickstart lists test commands and the implementation tasks should create failing backend/frontend tests before production changes.
- **Simplicity**: PASS. Uses existing app boundaries and fields; no migration, new dependency, new service, or broad scheduler abstraction is introduced.
- **Technology fit**: PASS. FastAPI/React/Vite boundaries and cross-stack contracts are explicit.
- **Delivery workflow**: PASS. Planning only; implementation branch decision remains explicit before coding.
- **Verification before commit**: PASS. Commands below define expected evidence.

## Verification Plan

Before committing implementation work for this feature, run:

```powershell
cd backend
python -m pytest tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

```powershell
cd client
npm run test
npm run lint
npm run build
```

Feature-specific verification should prove:

- generated Draft Sessions can be opened for editing from the Courses overview;
- valid date, start time, end time, and room edits persist and appear in list and weekly modes;
- edited room values affect room filter results;
- out-of-semester dates, invalid time ranges, missing sessions, missing rooms, and insufficient room capacity are rejected without changing existing Draft Session data;
- duplicate dates within the same Draft Schedule are rejected without surfacing a database constraint error;
- room occupancy/overlap conflicts are not blocked or warned about in this slice;
- canceling an edit leaves the session unchanged;
- saved edits remain visible after changing overview filters, switching view modes, and reopening the same selected semester;
- regenerating a course continues to replace that course's previous generated sessions according to existing behavior.
