# Implementation Plan: Conflict Detection

**Working Branch**: `master` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-conflict-detection/spec.md`

## Summary

Slice 5 adds non-blocking validation alerts to generated Draft Sessions in the selected-semester Courses overview. Office staff can see lecturer, room, and Cohort overlaps across all generated plans in the semester, plus room capacity and active generation/Study Type Time Window violations. The implementation will compute alerts from existing persisted Draft Session and planning data whenever draft schedules are returned, extend the existing Draft Session response shape with alert details, and render those alerts in the existing list and weekly review surfaces. Generation and manual edit saves remain allowed when alerts exist.

## Technical Context

**Language/Version**: Python 3.12-compatible backend code; TypeScript 6.0 and React 19 frontend.

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x, pytest, React, Vite, Vitest, ESLint. No new runtime dependency is planned.

**Storage**: Existing SQLAlchemy relational model backed by the project database. Validation alerts are derived from Draft Session, Draft Schedule, Course, Lecturer, Cohort, Room, Semester, Study Type Time Window, and Generation Constraint data at read time; no new persisted alert table or migration is planned.

**Testing**: Backend pytest service/API tests; frontend Vitest component tests plus `npm run lint` and `npm run build`.

**Target Platform**: Browser planner UI calling the local FastAPI backend.

**Project Type**: Full-stack web application with FastAPI backend and React/Vite frontend.

**Performance Goals**: Semester overview loading and post-edit refresh should remain interactive for current planner volumes. Alert computation should use the already loaded selected-semester schedule set and avoid per-session API calls.

**Constraints**: Alerts are non-blocking. Do not add automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summaries, multi-course generation, session creation/deletion/splitting/merging, or multiple lecturers/rooms per course. Use currently active course-semester generation constraints for generation-window violations. Each overlap alert must identify every related conflicting session available in the selected semester.

**Scale/Scope**: Modest office-staff review volume: generated Draft Sessions for one selected semester across currently generated single-course plans. The design can use straightforward in-memory grouping over the selected semester schedule set rather than introducing a scheduling engine or background validation service.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: PASS. `specs/005-conflict-detection/spec.md` exists and includes clarifications, scope, requirements, acceptance criteria, edge cases, and measurable outcomes.
- **Acceptance criteria**: PASS. User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: PASS. This plan identifies backend validation/API tests and frontend component/API type tests to create before production code.
- **Simplicity**: PASS. Plan uses existing FastAPI, SQLAlchemy, React, and Vite structure with no new dependencies, background services, or persisted alert model.
- **Technology fit**: PASS. Backend remains FastAPI; frontend remains React/Vite; cross-stack contracts are documented in `contracts/openapi.yaml`.
- **Delivery workflow**: PASS. Current branch is `master`; this planning artifact does not create production code. Implementation should either continue as a clean verified solo change or move to a feature branch if the work remains broad/risky.
- **Verification before commit**: PASS. Concrete backend and frontend verification commands are listed below.

## Project Structure

### Documentation (this feature)

```text
specs/005-conflict-detection/
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
|   |   |-- draft_schedule_repository.py
|   |   `-- draft_schedule_validation.py
|   |-- schemas/
|   |   `-- draft_schedule.py
|   `-- api/
|       `-- draft_schedule.py
`-- tests/
    |-- api/
    |   `-- test_draft_schedule.py
    `-- services/
        |-- test_draft_schedule_repository.py
        `-- test_draft_schedule_validation.py

client/
|-- src/
|   |-- api/
|   |   `-- draftSchedule.ts
|   |-- components/
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- scheduleReviewUtils.ts
|   |   `-- scheduleReviewUtils.test.ts
|   |-- pages/
|   |   `-- CourseSchedulePage.tsx
|   `-- test/
|       `-- draftScheduleFixtures.ts
```

**Structure Decision**: Implement Slice 5 as an additive full-stack change inside the existing draft schedule overview flow. Backend validation logic should live in a focused service module that accepts the selected-semester Draft Schedule set and returns per-session alerts. The repository/API response mapping should attach alerts to existing Draft Session responses. The frontend should treat alerts as part of `DraftSession` data and render them in the existing list and weekly views without changing generation or manual edit save rules.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations requiring complexity justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|

## Phase 0 Research

Research is captured in [research.md](./research.md). Key decisions: derive validation alerts at read time, extend existing Draft Session responses, use direct interval/grouping checks over selected-semester sessions, validate generation-window alerts against currently active constraints, keep Study Type Time Window checks based on source study-type windows, and treat alerts as non-blocking UI state.

## Phase 1 Design

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

Agent context update: skipped because this repository has no `.specify/scripts/powershell/update-agent-context.ps1` or equivalent agent-context script.

## Post-Design Constitution Check

- **Spec-first**: PASS. Design artifacts trace back to the approved Slice 5 spec and clarifications.
- **Acceptance criteria**: PASS. Data model, contracts, and quickstart cover overlap alerts, capacity alerts, current generation-constraint alerts, Study Type Time Window alerts, multi-alert sessions, filter/view persistence, and non-blocking generation/edit behavior.
- **Test-first**: PASS. Quickstart lists test commands and implementation tasks should create failing backend/frontend tests before production changes.
- **Simplicity**: PASS. Uses existing app boundaries and read-time derived alerts; no migration, new dependency, background worker, or broad scheduler abstraction is introduced.
- **Technology fit**: PASS. FastAPI/React/Vite boundaries and cross-stack contracts are explicit.
- **Delivery workflow**: PASS. Planning only; implementation branch decision remains explicit before coding.
- **Verification before commit**: PASS. Commands below define expected evidence.

## Verification Plan

Before committing implementation work for this feature, run:

```powershell
cd backend
python -m pytest tests/services/test_draft_schedule_validation.py tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

```powershell
cd client
npm run test
npm run lint
npm run build
```

Feature-specific verification should prove:

- lecturer, room, and Cohort overlaps create alerts on all affected sessions;
- back-to-back sessions where one ends exactly when another starts do not create overlap alerts;
- cross-course overlaps in the same selected semester identify every related conflicting session available in that semester;
- room capacity violations create alerts without blocking generation or otherwise valid manual edits;
- sessions outside currently active course-semester generation constraints create alerts;
- sessions outside Study Type Time Windows create alerts;
- sessions with multiple issues expose every applicable alert;
- alerts refresh after generation, regeneration, and saved manual edits;
- resolved alerts disappear after schedule changes;
- alerts remain associated with the correct sessions across filters and list/weekly modes;
- missing validation reference data produces a clear validation-data issue rather than a false safe state;
- no automatic conflict resolution, conflict-aware generation, public holiday handling, exam scheduling, dashboard summary, multi-course generation, session creation/deletion/splitting/merging, or multiple lecturer/room behavior is introduced.
