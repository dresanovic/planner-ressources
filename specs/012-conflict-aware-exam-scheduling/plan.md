# Implementation Plan: FS-012 Conflict-Aware Exam Scheduling

**Working Branch**: `master` (create `codex/fs-012-exam-scheduling` before production implementation) | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-conflict-aware-exam-scheduling/spec.md`

## Summary

Add planner-controlled exam configuration, generation, review, and manual management without changing teaching-session persistence. One revisioned current exam configuration per course-semester supplies the next exam's inputs; it may be saved before teaching exists but remains ineligible until a final teaching anchor is available, and it is read-only while its active exam exists. Separate revisioned exam sessions retain unlimited history and their own saved configuration context. A focused deterministic CP-SAT planner jointly places at most one active exam per selected course-semester, reusing current teaching/exam occupancy, FS-008 eligibility and availability, and FS-011 holidays as hard constraints while treating the configured date window as a soft preference. Automatic generation uses applicable active Study Type Time Window starts as its explicit bounded proposal domain; manual placement is not restricted to those starts. Additive FastAPI contracts and focused React components extend the existing Schedule workspace and unified review.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0.2 and React 19.2.7 frontend

**Primary Dependencies**: FastAPI 0.139.0, Pydantic 2.13.4, SQLAlchemy 2.0.45, Alembic 1.18.0, OR-Tools 9.15.6755; React 19, Vite 8.1.1

**Storage**: SQLAlchemy persistence with SQLite by default (`DATABASE_URL` remains configurable); custom sequential schema initialization plus migration `0006_conflict_aware_exam_scheduling.py`

**Testing**: pytest 9.1.1 for backend API/service/migration/performance tests; Vitest 4.0.16, React Testing Library conventions already in the client, ESLint, TypeScript/Vite build

**Target Platform**: FastAPI service on the existing supported server environment and modern desktop browsers used by planner users

**Project Type**: Full-stack web application

**Performance Goals**: Produce mixed scheduled/failed/stale outcomes within 60 seconds for 100 enabled exam requirements, 500 teaching sessions, and 100 existing exams; refresh saved outcomes and affected conflict context without requiring a manual reload

**Constraints**: No new dependency; no external exam integration; no change to teaching draft replacement semantics; all generated/manual exams must satisfy final-teaching, semester, resource, capacity, availability, holiday, and overlap rules; configurations without a final teaching anchor remain saved but unplaceable; active-exam configurations are read-only; recommended dates remain soft; automatic start proposals come from applicable active Study Type Time Windows; server-derived institution-local today controls active/past state

**Scale/Scope**: One planner role; one institution timezone; up to 100 selected exam requirements per generation operation; unlimited retained past exams; one exam dated today or later per course-semester

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- **Spec-first — PASS**: [spec.md](spec.md) contains clarified scope, 39 functional requirements, independently testable stories, and measurable outcomes.
- **Acceptance criteria — PASS**: All user stories contain Given/When/Then acceptance scenarios and independent test paths.
- **Test-first — PASS**: Backend, client, migration, performance, and dependency-regression tests listed below and in [quickstart.md](quickstart.md) must be created or updated before their corresponding production behavior. `tasks.md` places the performance test in the US2 test block and establishes dependency-regression coverage before production changes.
- **Simplicity and KISS — PASS**: The design adds only two persisted concepts and two focused domain services; it reuses current resource, holiday, overlap, revision, and UI patterns.
- **Technology fit — PASS**: Backend remains FastAPI/SQLAlchemy/OR-Tools; frontend remains React/Vite; [contracts/exam-scheduling.openapi.yaml](contracts/exam-scheduling.openapi.yaml) defines the cross-stack boundary.
- **Delivery workflow — PASS WITH PRE-IMPLEMENTATION ACTION**: Planning is on `master`; because FS-012 is a cross-stack scheduling feature and the worktree contains planning changes, production implementation must begin on `codex/fs-012-exam-scheduling` or another approved feature branch.
- **Verification before commit — PASS**: Concrete backend, client, contract, migration, performance, and regression commands are listed under Verification Plan.

### Post-Design Re-check

- Phase 1 introduces no new dependency, generic repository layer, session inheritance hierarchy, state framework, or external integration.
- Exam persistence remains separate from teaching drafts because the domains have demonstrably different identity, lifecycle, history, and hard-validation rules.
- The time-of-day candidate gap is resolved and specified without a new administration surface: automatic generation proposes starts at every applicable active Study Type Time Window start; a missing proposal domain produces `AUTOMATIC_START_TIME_UNAVAILABLE`, while manual placements may use any time satisfying the approved hard constraints.
- A configuration may be saved without a final teaching anchor, with nullable derived recommendation dates and explicit generation ineligibility. Once an active exam exists, its consumed configuration is read-only until the exam becomes past or is deleted.
- All constitution gates remain passed. No exception or complexity waiver is required.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Add one current `CourseExamConfiguration` row per course-semester and separate `ExamSession` rows; allow an anchorless configuration to remain explicitly enabled but ineligible, keep a consumed active-exam configuration read-only, and implement one exam scheduling service, one focused optimizer, one additive API module, one client API module, and focused exam UI components inside the current Schedule page.
2. **Necessary abstractions**: `exam_scheduling` owns persistence, lifecycle, snapshots, manual mutations, and derived validity; `exam_optimization` owns deterministic joint candidate selection. The split is required because solver inputs are transient and should not depend on HTTP or ORM state.
3. **Deliberately excluded**: A generic teaching/exam session superclass, a new repository framework, a generic optimization framework, Redux or another client state library, a form framework, a fixed or managed exam-type catalog, exam-hours administration, invigilator management, publication/history infrastructure, audit logging, external exam/room-booking adapters, and FS-014 workspace redesign.

## Project Structure

### Documentation (this feature)

```text
specs/012-conflict-aware-exam-scheduling/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- exam-scheduling.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                         # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- exam_scheduling.py
|   |-- schemas/
|   |   `-- exam_scheduling.py
|   |-- services/
|   |   |-- exam_scheduling.py
|   |   `-- exam_optimization.py
|   |-- models/
|   |   `-- planning.py              # add CourseExamConfiguration and ExamSession
|   |-- db/
|   |   |-- schema.py
|   |   `-- migrations/
|   |       `-- 0006_conflict_aware_exam_scheduling.py
|   `-- main.py
`-- tests/
    |-- api/test_exam_scheduling.py
    |-- services/test_exam_scheduling.py
    |-- services/test_exam_optimization.py
    |-- performance/test_exam_scheduling_performance.py
    `-- db/test_migrations.py

client/
|-- src/
|   |-- api/
|   |   |-- examScheduling.ts
|   |   `-- examScheduling.test.ts
|   |-- components/
|   |   |-- ExamRequirementEditor.tsx
|   |   |-- ExamRequirementEditor.test.tsx
|   |   |-- ExamGenerationPanel.tsx
|   |   |-- ExamGenerationPanel.test.tsx
|   |   |-- ExamGenerationResultSummary.tsx
|   |   |-- ExamManualSessionEditor.tsx
|   |   |-- ExamManualSessionEditor.test.tsx
|   |   |-- ExamDeletionDialog.tsx
|   |   |-- ExamDeletionDialog.test.tsx
|   |   |-- DraftSchedulePanel.tsx
|   |   `-- DraftSchedulePanel.test.tsx
|   `-- pages/
|       |-- CourseSchedulePage.tsx
|       `-- CourseSchedulePage.test.tsx
```

**Structure Decision**: Keep the existing full-stack application layout. Register a dedicated exam router and client API rather than widening teaching-specific contracts. Extend `CourseSchedulePage` orchestration and `DraftSchedulePanel` review through typed exam inputs; keep configuration, generation, manual mutation, and deletion UI in focused components.

## Phase 0: Research Decisions

Research decisions and rejected alternatives are recorded in [research.md](research.md). All technical-context unknowns are resolved, including persistence separation, active/past enforcement, institution-local clock behavior, finite automatic start-time candidates, solver objectives, stale-input boundaries, API shape, and client integration.

## Phase 1: Design Outputs

- [data-model.md](data-model.md) defines persisted configuration/session fields, snapshots, relationships, validation rules, transient optimizer inputs/outcomes, and lifecycle transitions.
- [contracts/exam-scheduling.openapi.yaml](contracts/exam-scheduling.openapi.yaml) defines configuration, overview, prepare/generate, manual create/edit/delete, structured errors, and stale-state contracts.
- [quickstart.md](quickstart.md) defines migration, backend, client, end-to-end, hard-constraint, stale-state, history, and performance validation.
- The repository does not contain `.specify/scripts/powershell/update-agent-context.ps1` or an equivalent agent-context updater, so no agent context file can be updated by this workflow. No substitute project file is invented.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Run from the repository root unless a working directory is stated:

1. `python -m pytest backend/tests/db/test_migrations.py`
2. `python -m pytest backend/tests/services/test_exam_scheduling.py backend/tests/services/test_exam_optimization.py`
3. `python -m pytest backend/tests/api/test_exam_scheduling.py`
4. `python -m pytest backend/tests/performance/test_exam_scheduling_performance.py`
5. `python -m pytest backend/tests`
6. In `client/`: `npm run test`
7. In `client/`: `npm run lint`
8. In `client/`: `npm run build`
9. Validate `contracts/exam-scheduling.openapi.yaml` using the repository's contract-validation approach and confirm request/response examples match backend schemas and client types.
10. Execute the end-to-end scenarios in [quickstart.md](quickstart.md), recording mixed generation, manual override, stale mutation, active/past history, accessibility, and 100-requirement performance evidence before commit.
