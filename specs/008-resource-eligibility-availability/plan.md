# Implementation Plan: FS-008 Resource Eligibility and Availability

**Working Branch**: `master` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-resource-eligibility-availability/spec.md`

**Note**: Planning is being completed on `master`; create a `codex/` feature branch before production implementation because this is a cross-stack schema migration and customer-facing workflow.

## Summary

Add planner-maintained lecturers, rooms, resource lifecycle, recurring and dated unavailability, and atomic multi-resource course eligibility without implementing semester-wide optimization. The backend will extend the existing SQLAlchemy catalog with normalized reference codes, optimistic revisions, authoritative course-resource junctions, resource-owned unavailability, transactional delete-or-inactivate behavior, cohort-growth cleanup, and separate validation alerts. Existing scalar Course resource assignments will be backfilled into eligibility sets and removed as sources of truth; Draft Sessions retain exactly one lecturer and room. Current single-course and batch generation will remain course-local, choose only active eligible resources that satisfy capacity and availability, and minimize within-course lecturer and room switches using deterministic tie-breaking. The React client will extend Academic Data with active-by-default Lecturer and Room administration, nested unavailability, atomic course eligibility editing, outcome-driven retirement, and recoverable stale-write flows.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, Alembic 1.18; React 19 and Vite 8; no new runtime dependency

**Storage**: SQLite by default through SQLAlchemy, with sequential Alembic-compatible migration `0004_resource_eligibility_availability` and a portable relational design suitable for PostgreSQL

**Testing**: pytest 9 for backend model/service/API/migration/regression tests; Vitest 4 with jsdom for client API/component/page tests; TypeScript build and ESLint

**Target Platform**: Existing FastAPI service and modern web browsers used by planner users

**Project Type**: Full-stack web application with JSON HTTP contracts

**Performance Goals**: Affected resource, eligibility, planning, and validation views usable within 2 seconds after a successful change; 95% of administration views and saves usable within 2 seconds for the reference dataset

**Constraints**: Preserve FS-001 through FS-007 behavior and saved Draft Session assignments; keep one lecturer and room per session; no authentication, lecturer self-service, holidays, exams, external synchronization, resource ranking, preference switches, or cross-course/global optimization; use half-open availability overlap; preserve entered form data after validation or stale-write errors; use keyboard-operable controls, labelled fields, focus-managed dialogs, and announced outcomes; add no client router, state library, recurrence library, background service, or infrastructure dependency

**Scale/Scope**: One planner role; at least 100 lecturers, 100 rooms, 100 courses, and 1,000 unavailability periods; resource lists default to active records and support explicit inactive/all filters plus search; availability and eligibility are planner-maintained aggregates with no arbitrary product limit introduced by this slice

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The clarified FS-008 specification defines 4 independently testable user stories, 44 functional requirements, 12 measurable outcomes, bounded exclusions, and 5 recorded product decisions.
- **Acceptance criteria — PASS**: Given/When/Then scenarios cover resource CRUD, availability, eligibility, generation/validation use, lifecycle, migration, capacity changes, stale writes, and regression behavior.
- **Test-first — PASS**: Backend and frontend tests are identified before corresponding production work; no automated-test exception is planned.
- **Simplicity — PASS**: The design uses existing FastAPI, SQLAlchemy, Alembic, React, fetch, controlled forms, and revision patterns. One focused shared resource-rule module is justified so generation and validation use identical availability and eligibility semantics. No new dependency, external service, event system, or generic repository framework is added.
- **Technology fit — PASS**: FastAPI and React/Vite remain the application boundaries, and all new and changed JSON contracts are documented in `contracts/resource-eligibility-availability.openapi.yaml`.
- **Delivery workflow — PASS WITH REQUIRED ACTION**: Planning is on `master`; implementation must move to a `codex/` feature branch before production code because the change includes persistent-data migration and multiple customer-facing workflows.
- **Verification before commit — PASS**: Focused and complete backend tests, client tests, lint, build, migration checks, and acceptance protocols are listed below and in `quickstart.md`.

### Post-design re-check

The Phase 1 design introduces no constitution violation. Course-resource junctions eliminate competing eligibility sources, deterministic course-local assignment does not cross the FS-010 boundary, and the shared resource-rule evaluator avoids divergent overlap semantics without adding a framework. Migration preserves every Draft Session assignment, generates editable collision-free legacy reference codes, and changes startup ordering so existing schemas migrate before new tables are created. Transactional retirement and cohort-growth cleanup explicitly preserve schedule history. The contract and validation guide cover all cross-stack changes and test-first verification.

## Project Structure

### Documentation (this feature)

```text
specs/008-resource-eligibility-availability/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- resource-eligibility-availability.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                      # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   |-- academic_catalog.py                   # Course/Cohort contract integration
|   |   |-- resource_catalog.py                   # Resource, availability, eligibility endpoints
|   |   |-- draft_schedule.py                     # Lecturer-aware session edits
|   |   `-- planning_options.py                    # Eligible resource choices/readiness
|   |-- db/
|   |   |-- migrations/
|   |   |   `-- 0004_resource_eligibility_availability.py
|   |   `-- schema.py                             # empty-create vs sequential upgrade ordering
|   |-- models/
|   |   `-- planning.py                           # Resources, junctions, unavailability
|   |-- schemas/
|   |   |-- academic_catalog.py
|   |   |-- resource_catalog.py
|   |   |-- draft_schedule.py
|   |   `-- planning_options.py
|   `-- services/
|       |-- academic_catalog.py                   # Cohort-growth eligibility cleanup
|       |-- resource_catalog.py                   # Revisioned resource mutations
|       |-- resource_rules.py                     # Shared overlap/usability/allocation rules
|       |-- schedule_generation.py                # Course-local resource assignment
|       |-- multi_course_generation.py            # Independent course-local generation
|       |-- draft_schedule_repository.py          # Per-session resource context
|       `-- draft_schedule_validation.py          # New eligibility/availability alerts
|-- scripts/
|   `-- seed_dummy_planning_data.py                # Codes, eligibility, availability-safe seeds
`-- tests/
    |-- api/
    |   |-- test_resource_catalog.py
    |   |-- test_academic_catalog.py
    |   |-- test_draft_schedule.py
    |   `-- test_planning_options.py
    |-- db/
    |   `-- test_migrations.py
    |-- services/
    |   |-- test_resource_catalog.py
    |   |-- test_resource_rules.py
    |   |-- test_schedule_generation.py
    |   `-- test_draft_schedule_validation.py
    `-- performance/
        `-- test_resource_catalog_performance.py

client/
|-- src/
|   |-- api/
|   |   |-- academicCatalog.ts                    # Course/cohort impact additions
|   |   |-- resourceCatalog.ts
|   |   |-- resourceCatalog.test.ts
|   |   |-- draftSchedule.ts
|   |   `-- planningOptions.ts
|   |-- components/
|   |   |-- ResourceCatalogList.tsx
|   |   |-- ResourceEditor.tsx
|   |   |-- ResourceAvailabilityEditor.tsx
|   |   |-- CourseResourceEligibilityEditor.tsx
|   |   `-- ResourceRemovalDialog.tsx
|   |-- pages/
|   |   |-- AcademicDataPage.tsx                  # Lecturer/Room categories
|   |   `-- AcademicDataPage.test.tsx
|   |-- App.tsx                                   # Existing two-view shell retained
|   `-- App.css
`-- package.json
```

**Structure Decision**: Retain the existing backend/client split and the current two-view application shell. Add dedicated resource schema/service/API modules because lifecycle, availability, and eligibility differ materially from generic academic catalog CRUD, while keeping them under the existing Academic Data workspace. A small shared `resource_rules.py` module is the single source for eligibility, half-open overlap, current usability, and course-local assignment decisions used by generation and validation.

**Agent Context Update**: No `.specify/scripts/*/update-agent-context` script and no project `AGENTS.md` are present in this Spec Kit installation. The required script step was checked but cannot be run; no substitute context file is invented.

## Design Decisions

### Persistence and migration

- Add normalized, catalog-unique reference codes, active state, and revisions to Lecturer and Room. Duplicate display names remain valid. Existing resources receive deterministic editable codes such as `LECT-<id>` and `ROOM-<id>`, remain active, and start at revision 1.
- Add composite-key CourseEligibleLecturer and CourseEligibleRoom junctions. Backfill each current Course lecturer and room before removing the scalar Course resource columns so eligibility has one authoritative source. Preserve every DraftSession lecturer and room foreign key unchanged.
- Add one ResourceUnavailabilityPeriod owner table with exactly one Lecturer or Room, a recurring or dated kind, revision, and kind-specific date/time fields. Store recurring weekdays in a child table so a multi-day weekly rule remains one revisioned aggregate. Enforce owner and shape checks and reject exact duplicates transactionally.
- Change runtime schema initialization to create all tables only for an empty database; an existing recognized FS-007 database must run sequential migration 0004 before current metadata creation/verification. Unknown partial schemas still stop with actionable diagnostics.

### Resource administration and lifecycle

- Use revisioned resource edits and period edits with the existing `409 STALE_REVISION` error envelope. Keep local form values on validation or stale failure and require explicit review before retry.
- A confirmed resource removal rechecks revision and usage in one transaction. Active-course eligibility or any Draft Session reference changes the outcome to `inactivated`; otherwise the transaction removes inactive-course eligibility, owned unavailability, and the resource and returns `deleted`.
- Inactive resources remain available through explicit administration filters and historical session context but are absent from new eligibility and assignment candidates. Reactivation validates current code/details and restores preserved relationships only where current hard rules permit.

### Eligibility, availability, and assignment

- Replace both eligible sets atomically through one revisioned Course aggregate command. Reject duplicate IDs, missing/inactive additions, newly undersized rooms, and planner removal of the final lecturer or room. Return current invalid preserved relationships visibly with reasons.
- Treat availability as institution-local wall-clock time consistent with existing sessions. Recurring rules apply indefinitely on selected weekdays; dated periods span their full local date/time range. All rules union, and overlap uses `[start, end)` semantics.
- Deliver availability-conflict validation with US2 and eligibility/capacity validation with US3 so both stories pass their independent acceptance checkpoints. US4 composes those existing rules into generation, editing, and combined-alert workflows.
- Generate temporal session candidates only where at least one active eligible lecturer and capacity-sufficient eligible room are available. After placement, assign resources per course using deterministic dynamic programming that minimizes lecturer changes and room changes independently; normalized reference code and stable ID break equal-cost ties. This is not planner ranking and never considers another course's conflicts.
- Keep DraftSession lecturer and room non-null. Extend existing session edits to accept Lecturer as well as Room. An unchanged legacy invalid assignment may remain during an unrelated edit, but changing an assignment must select an active eligible resource and preserve the established hard capacity rule; availability and cross-session conflicts remain visible through non-blocking validation consistent with FS-004/FS-005.

### Capacity and validation

- A Room capacity reduction preserves existing eligibility as visibly invalid and excludes it from generation. A Cohort size increase atomically removes every newly insufficient room eligibility, increments affected Course revisions, preserves Draft Sessions, and reports removed links plus courses left without rooms.
- Add separate `LECTURER_INELIGIBLE`, `ROOM_INELIGIBLE`, `LECTURER_UNAVAILABLE`, and `ROOM_UNAVAILABLE` alerts while retaining `ROOM_CAPACITY`. Evaluate current resource rules at read time and preserve all applicable alerts on one session.
- Resolve lecturer and room display context from each DraftSession assignment rather than from Course-level resources. Preserve FS-007 academic snapshots for historical course, semester, cohort, and study-type display; do not silently rewrite schedule facts.

### Client interaction

- Extend Academic Data with Lecturer and Room categories; default those lists to Active, allow All/Inactive filtering, and search by name or reference code. Display `Name · CODE`, status, and Room capacity.
- Use resource detail panels for details, unavailable periods, usage, removal, and reactivation. Use discriminated recurring/dated controlled forms and independently revisioned mutations.
- Edit Course eligibility as one Save/Cancel aggregate with searchable checkbox groups. Show inactive or insufficient preserved relationships with reasons, disable invalid additions, and present the always-considered preference meanings as read-only guidance with no switches or ranking controls.
- Fetch a fresh removal assessment before confirmation, describe whether confirmation will delete or inactivate, list active courses and session counts, and render the server's actual transactional outcome. Preserve focus management, keyboard operation, announced errors/status, last-known content during refresh, and responsive stacking.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Run backend commands from `backend/` and client commands from `client/` after writing the corresponding tests first. Create the performance acceptance dataset and failing automated timing coverage during Foundation before corresponding production work; collect final timing measurements only after implementation.

```text
python -m pytest tests/services/test_resource_catalog.py tests/services/test_resource_rules.py tests/api/test_resource_catalog.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_generation.py tests/services/test_draft_schedule_validation.py tests/api/test_draft_schedule.py tests/api/test_planning_options.py tests/api/test_academic_catalog.py
python -m pytest
npm test
npm run lint
npm run build
```

Verification evidence must cover clean schema creation and FS-007-to-FS-008 upgrade, legacy eligibility backfill without Draft Session changes, duplicate-name/code behavior, recurring/dated boundaries, stale writes, both retirement outcomes, reactivation, atomic eligibility, capacity asymmetry, course-local resource assignment, distinct validation alerts, active-default filtering, keyboard dialog behavior, and all FS-001 through FS-007 regressions. Record the SC-001/SC-002/SC-004 usability protocol and SC-008/SC-009 timing protocol results under this feature directory before completion.
