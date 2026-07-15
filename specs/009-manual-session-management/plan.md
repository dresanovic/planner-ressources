# Implementation Plan: FS-009 Manual Session Management

**Working Branch**: `master` | **Date**: 2026-07-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-manual-session-management/spec.md`

**Note**: This plan is limited to FS-009. It does not plan or depend on the separate FS-008 resource-eligibility slice.

## Summary

Extend the existing course-semester draft workflow so a planner can create one manual Draft Session, delete one session, or clear one course-semester draft. Reuse the existing Draft Schedule and Draft Session models, derive remaining units from the current course total and saved session units, use the existing Draft Schedule revision for stale-deletion protection, and refresh the existing semester overview so remaining-unit indicators and non-blocking alerts reflect every successful mutation. Add focused FastAPI contracts and React/Vite interactions inside the current scheduling page; no migration, new dependency, optimizer, or automatic repair behavior is required.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, React 19, Vite 8; no new dependencies

**Storage**: Existing SQLAlchemy relational model and Alembic migration chain; in-memory SQLite for automated backend tests. Existing `DraftSchedule.revision`, Draft Schedule snapshots, Draft Session fields, cascade deletion, and course-semester uniqueness are sufficient; no schema migration is planned.

**Testing**: `pytest` and FastAPI `TestClient` for repository/API/validation behavior; Vitest with jsdom for API clients, components, and page orchestration; TypeScript build and ESLint for frontend verification

**Target Platform**: Existing FastAPI service and modern browser planner UI

**Project Type**: Full-stack web application

**Performance Goals**: The affected course's remaining-unit state and refreshed semester alerts are visible within one second of a successful create or delete action in the documented reference acceptance environment.

**Constraints**: Preserve all source records and saved generation constraints; keep capacity and structural validation blocking; keep established overlap/window alerts non-blocking; never retain an empty Draft Schedule; reject stale deletion confirmations; do not add generation, optimization, bulk semester deletion, splitting/merging, automatic repair, drag/drop, or FS-008 eligibility enforcement.

**Scale/Scope**: One planner action mutates one session or one course-semester draft. Refresh and alert evaluation remain scoped to the existing modest semester overview volume and existing synchronous request flow.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

- **Spec-first — PASS**: The clarified FS-009 spec defines three independently testable stories, explicit scope, edge cases, 33 functional requirements, and measurable outcomes.
- **Acceptance criteria — PASS**: All primary and stale-state flows use Given/When/Then scenarios.
- **Test-first — PASS**: Repository, API, client API, component, and page-orchestration tests are identified before production changes; no manual-only exception is planned.
- **Simplicity — PASS**: The design reuses existing tables, revision fields, validation service, page state ownership, and dialog patterns. No dependency, service, schema migration, or infrastructure addition is proposed.
- **Technology fit — PASS**: Backend changes stay in FastAPI/Pydantic/SQLAlchemy and frontend changes stay in the existing React/Vite client. The cross-stack contract is captured in `contracts/manual-session-management.openapi.yaml`.
- **Delivery workflow — PASS**: This command creates planning artifacts only. Before production implementation, preserve unrelated user changes and create a `codex/` feature branch unless the implementer can confirm the constitution's clean, isolated, verified solo-work condition for `master`.
- **Verification before commit — PASS**: Concrete targeted and full-suite commands are listed below and in `quickstart.md`.

### Post-Design Re-check

All gates remain satisfied after research and contract design. The design adds no migration or dependency, uses optimistic comparison against the existing Draft Schedule revision for destructive actions, retains established alert derivation, and keeps remaining units derived rather than persisted. No constitution exception or complexity justification is required.

## Project Structure

### Documentation (this feature)

```text
specs/009-manual-session-management/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- manual-session-management.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                              # created later by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- draft_schedule.py             # create/delete routes and response mapping
|   |-- schemas/
|   |   |-- draft_schedule.py             # mutation requests, results, and failure codes
|   |   `-- planning_options.py            # expose cohort size for capacity-valid room choice
|   `-- services/
|       `-- draft_schedule_repository.py  # transactional create/delete/progress operations
`-- tests/
    |-- api/
    |   `-- test_draft_schedule.py
    `-- services/
        |-- test_draft_schedule_repository.py
        `-- test_draft_schedule_validation.py

client/
|-- src/
|   |-- api/
|   |   |-- draftSchedule.ts
|   |   |-- draftSchedule.test.ts
|   |   |-- planningOptions.ts
|   |   `-- planningOptions.test.ts
|   |-- components/
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- ScheduleDeletionDialog.tsx
|   |   `-- ScheduleDeletionDialog.test.tsx
|   `-- pages/
|       |-- CourseSchedulePage.tsx
|       `-- CourseSchedulePage.test.tsx
```

**Structure Decision**: Implement FS-009 as a focused extension of the existing draft-schedule vertical slice. Repository functions own atomic validation and persistence, the existing draft-schedule API owns transport mapping, `CourseSchedulePage` continues to own selected-course progress, manual creation, complete-draft clearing, overview refresh, and mutation orchestration, and `DraftSchedulePanel` owns session-level edit/delete controls. A small schedule-specific confirmation dialog is justified because existing replacement and protected source-record dialogs do not express both single-session and complete-draft consequences or stale reconfirmation.

## Phase 0: Research Outcome

Research decisions are recorded in [research.md](./research.md). All technical unknowns are resolved:

- reuse current Draft Schedule and Draft Session storage without migration;
- derive, rather than persist, scheduled and remaining units;
- use Draft Schedule revision as the optimistic deletion token;
- preserve existing snapshot and generation-constraint boundaries;
- reuse the current validation-alert service and overview refresh;
- calculate the initial end time in the client and validate the submitted final values on the server;
- return one consistent mutation result for create, single delete, and complete delete;
- keep manual/generated provenance out of scope because behavior and deletion semantics are identical.

## Phase 1: Design and Contracts

### Backend Design

1. Add request and response schemas for manual creation, deletion results, progress values, validation failures, and stale conflicts.
2. Add repository operations that:
   - load current course, semester, cohort, lecturer, room, and draft state;
   - calculate current scheduled and remaining units;
   - create a Draft Schedule with current snapshots when none exists;
   - add one Draft Session using the course lecturer/cohort and selected room;
   - increment the Draft Schedule revision for every mutation that leaves it present;
   - delete the parent Draft Schedule when its last session is removed;
   - delete the complete parent draft without touching source records or `GenerationConstraintSet` rows;
   - compare the submitted expected Draft Schedule identity and atomically claim its expected revision before destructive changes, then roll back on any mismatch.
3. Reuse `_to_response_with_validation` for a surviving affected draft and the existing semester-wide alert collector. Mutation responses expose the affected course's scheduled/remaining values; the client then reloads the existing semester overview so alerts on related surviving sessions also refresh.
4. Keep all hard validation in the backend: current references, semester bounds, positive whole units, units not exceeding current remaining units, time order, one session per draft per date, and room capacity. Overlap and window findings remain response alerts rather than save blockers.

### Frontend Design

1. Extend the draft-schedule API client with the three mutation calls, typed progress/result payloads, validation errors, and `409 STALE_DRAFT` handling.
2. Compute the initial proposed end time from the chosen start time and units using `units × 45 minutes + (units - 1) × 10 minutes`. Recalculate it whenever start time or units changes; allow the planner to edit the result afterward before saving. The submitted unit count remains unchanged by an end-time override.
3. Derive progress for the currently selected course-semester from planning-option `totalUnits` and the complete unfiltered schedule set. Display it beside the existing selected-course Planning Summary even when that course has no Draft Schedule; filters affect only visible sessions, never progress calculations. Do not introduce a semester-wide unscheduled-course dashboard in this slice.
4. Extend the existing planning-options course shape with `cohortSize`, then add manual-create controls beneath the selected-course summary using the inherited lecturer/cohort and capacity-valid room choices.
5. Add a delete action beside Edit for each generated or manual session in list and weekly views, and place the clear-draft action in the selected-course section. Confirmation state captures the current Draft Schedule revision and the exact consequence summary.
6. On successful mutation, retain the current semester and filters where possible, refresh the complete overview, and close the relevant form/dialog. On `STALE_DRAFT`, close the obsolete confirmation, refresh current state, explain that the draft changed, and require the planner to invoke deletion again.
7. Replace “Generated plans/sessions” wording on surfaces that now include manual sessions with the canonical “Draft plans/sessions” terminology.
8. Make confirmation dialogs modal and keyboard operable, move focus into the dialog, trap focus, support Escape/cancel, restore focus on close, expose failures through an alert region, announce calculated end time and refreshed remaining units politely, and keep destructive labels action-specific.

### Cross-Stack Contract

The contract in [manual-session-management.openapi.yaml](./contracts/manual-session-management.openapi.yaml) defines:

- `POST /api/courses/{course_id}/draft-schedule/sessions` for one manual session;
- `DELETE /api/draft-sessions/{session_id}?expectedDraftScheduleId=...&expectedDraftRevision=...` for one session;
- `DELETE /api/courses/{course_id}/draft-schedule?semesterId=...&expectedDraftScheduleId=...&expectedDraftRevision=...` for one complete course-semester draft;
- the additive `cohortSize` field on the existing planning-options Course shape so room choices can be capacity-filtered before the first draft exists;
- `201/200` mutation results with nullable current draft plus scheduled and remaining units;
- `404` missing input/target, `409 STALE_DRAFT`, and `422` structural/capacity/unit validation outcomes.

### Agent Context Update

The installed Spec Kit integration does not provide an `update-agent-context.ps1` script or equivalent project agent-context file. The required technology context is already governed by `.specify/memory/constitution.md`; no agent context file is created or modified by this plan.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Run targeted tests first while implementing each story, then the complete suites before commit.

```powershell
Set-Location backend
python -m pytest tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py tests/services/test_draft_schedule_validation.py
python -m pytest
```

```powershell
Set-Location client
npm test -- src/api/draftSchedule.test.ts src/components/DraftSchedulePanel.test.tsx src/components/ScheduleDeletionDialog.test.tsx src/pages/CourseSchedulePage.test.tsx
npm test
npm run lint
npm run build
```

Verification evidence must cover default and overridden end times, hard-validation rollback, non-blocking alerts, accurate remaining units, both confirmation cancellations, last-session cleanup, complete-draft isolation, constraint/source preservation, stale rejection and renewed confirmation, alert refresh on related sessions, and applicable FS-001–FS-006 regressions. Complete the end-to-end checks and one-second reference-environment observation in [quickstart.md](./quickstart.md).
