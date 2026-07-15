# Implementation Plan: Academic Planning Data Administration

**Working Branch**: `master` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-academic-data-administration/spec.md`

**Note**: Planning is being completed on `master`; create a `codex/` feature branch before production implementation because this is a cross-stack schema migration and customer-facing workflow.

## Summary

Add planner-facing administration for semesters, cohorts, courses, study types, and Study Type Time Windows while preserving all FS-001 through FS-006 workflows. The backend will extend the existing SQLAlchemy catalog with normalized uniqueness, lifecycle state, optimistic revisions, one current semester assignment per new, successfully updated, or planning-eligible Course, explicit usage checks, and immutable academic snapshots on saved Draft Schedules. A focused FastAPI catalog surface will expose CRUD, archive/reactivate, usage, protected deletion, and stale-write outcomes. The React client will add a lightweight Academic Data view with reusable catalog list/editor patterns and will refetch planning options after catalog changes without silently replacing invalid selections.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, Alembic 1.18; React 19 and Vite 8; no new runtime dependency

**Storage**: SQLite by default through SQLAlchemy, with Alembic-compatible schema migrations and a design that remains portable to PostgreSQL

**Testing**: `pytest` 9 for backend API/service/migration tests; Vitest 4 with jsdom for client API/component/page tests; TypeScript build and ESLint

**Target Platform**: Existing FastAPI service and modern desktop/mobile web browsers

**Project Type**: Full-stack web application with JSON HTTP contracts

**Performance Goals**: Updated planning options visible within 2 seconds after a successful mutation; 95% of administration views and save outcomes usable within 2 seconds for the reference dataset

**Constraints**: Preserve FS-001 through FS-006; no authentication, external synchronization, resource availability administration, or cascading lifecycle changes; prevent destructive deletion of referenced data; preserve entered form values after validation; keep historical academic schedule facts immutable; use keyboard-operable controls, labelled fields, focus-managed dialogs, and announced feedback; do not add a client router, form library, state library, or backend infrastructure service

**Scale/Scope**: One planner role; at least 100 records of each academic type; admin list pages default to 50 and cap at 200 records; one current Semester assignment per new, successfully updated, or planning-eligible Course, with a temporary unassigned repair state permitted only for migrated Courses; existing saved schedules may span earlier Semester assignments

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The clarified FS-007 spec defines scope, 4 independently testable user stories, explicit acceptance scenarios, 40 functional requirements, and measurable outcomes.
- **Acceptance criteria — PASS**: Scenarios use Given/When/Then and cover creation, editing, historical preservation, lifecycle, protected deletion, refresh, and regression behavior.
- **Test-first — PASS**: Backend and frontend tests are identified before their corresponding production changes; no automated-test exception is planned.
- **Simplicity — PASS**: The design uses existing FastAPI, SQLAlchemy, React, fetch, and controlled-form patterns. No dependency, background service, generic repository framework, event system, or client cache library is added.
- **Technology fit — PASS**: FastAPI and React/Vite are retained, and the cross-stack contract is documented in `contracts/academic-administration.openapi.yaml`.
- **Delivery workflow — PASS WITH REQUIRED ACTION**: Planning is on `master`; implementation must move to a `codex/` feature branch before production code because the change includes a persistent-data migration and multiple user workflows.
- **Verification before commit — PASS**: Focused and full backend tests, client tests, lint, and build commands are listed below and in `quickstart.md`.

### Post-design re-check

The Phase 1 design introduces no constitution violation. Migration repair states are limited to legacy courses for which no current semester can be inferred and legacy normalized-name conflicts. The UI provides planner-owned remediation, existing planning and saved schedules remain usable, and all newly created or successfully updated courses require exactly one semester and a unique name. This avoids silently inventing or destructively rewriting business data while preserving the specified steady-state invariants.

## Project Structure

### Documentation (this feature)

```text
specs/007-academic-data-administration/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- academic-administration.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                         # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   |-- academic_catalog.py      # CRUD, lifecycle, usage, protected deletion
|   |   `-- planning_options.py      # active/assigned option filtering
|   |-- db/
|   |   |-- migrations/
|   |   |   `-- 0003_academic_catalog_administration.py
|   |   |-- schema.py                # sequential 0002/0003 startup upgrade
|   |   `-- session.py               # SQLite integrity enforcement
|   |-- models/
|   |   `-- planning.py              # catalog state, assignment, snapshots
|   |-- schemas/
|   |   |-- academic_catalog.py
|   |   `-- planning_options.py
|   `-- services/
|       |-- academic_catalog.py      # validation, usage, revisioned mutations
|       |-- draft_schedule_repository.py
|       `-- draft_schedule_validation.py
|-- scripts/
|   `-- seed_dummy_planning_data.py  # compatible development data creation
`-- tests/
    |-- api/
    |   `-- test_academic_catalog.py
    |-- db/
    |   `-- test_migrations.py
    |-- scripts/
    |   `-- test_seed_dummy_planning_data.py
    `-- services/
        `-- test_academic_catalog.py

client/
|-- src/
|   |-- api/
|   |   |-- academicCatalog.ts
|   |   |-- academicCatalog.test.ts
|   |   `-- planningOptions.ts
|   |-- components/
|   |   |-- AcademicCatalogList.tsx
|   |   |-- AcademicRecordEditor.tsx
|   |   |-- AcademicRecordEditor.test.tsx
|   |   |-- ProtectedDeleteDialog.tsx
|   |   `-- ProtectedDeleteDialog.test.tsx
|   |-- pages/
|   |   |-- AcademicDataPage.tsx
|   |   |-- AcademicDataPage.test.tsx
|   |   `-- CourseSchedulePage.tsx
|   |-- App.tsx                       # lightweight view/hash navigation
|   `-- App.css
`-- package.json
```

**Structure Decision**: Keep the existing two-project web application. Add one focused backend catalog router/service/schema group and one reusable frontend administration page rather than one route/service/page per entity. Study Type Time Windows are nested under their owning Study Type. Existing schedule repositories change only where planning eligibility and immutable saved-schedule context require it.

**Agent Context Update**: The repository contains no `update-agent-context` script and no `AGENTS.md`; the required Phase 1 script step was inspected but cannot be run in this Spec Kit installation. No substitute context file is invented.

## Design Decisions

### Persistence and migration

- Add `is_active` and integer `revision` to every administrable academic row. For each named category, store the canonical normalized value under a database uniqueness constraint for new and repaired rows; legacy conflicts temporarily use a collision-safe internal key plus `name_repair_required` until the planner renames them uniquely.
- Add exact window uniqueness on `(study_type_id, weekday, start_time, end_time)` and keep partial overlaps valid.
- Add `current_semester_id` to Course. New and updated courses require it. A legacy course that cannot be inferred safely remains visible in a repair-required state, excluded from new planning until the planner assigns it.
- Add immutable Course, Semester, Cohort, and Study Type academic snapshot columns to Draft Schedule and backfill current source values once during migration. Saved schedule responses and academic validation use those snapshots rather than mutable catalog rows. Lecturer and Room historical handling remains unchanged from FS-001 through FS-006 and is not added to the FS-007 academic snapshot boundary.
- Extend startup schema detection to apply `0002` then `0003` sequentially. Supported legacy normalized-name conflicts become visible repair states without blocking startup; only unknown partial schemas that cannot be migrated safely stop with actionable errors.

### Backend behavior

- Keep catalog validation and mutation transaction logic in `services/academic_catalog.py`; API functions own commit/rollback, matching existing boundaries.
- Use atomic expected-revision checks for edit, archive, reactivate, and delete. Return `409 STALE_REVISION` without mutation when another view saved first.
- Query and report dependent-record and saved-schedule blockers before deletion; recheck in the mutation transaction and never rely on ORM cascades or database errors as user feedback.
- Return otherwise eligible Courses in planning options even when their Study Type lacks an active usable Time Window, marking them unavailable with `MISSING_ACTIVE_TIME_WINDOW`; enforce that status with actionable errors in single and batch generation independent of client behavior.
- Preserve the existing one Lecturer and one Room course assignments. Course create/edit includes name, total/minimum/maximum session units, Semester, Cohort, Study Type, and selections from existing read-only Lecturer/Room options. If either resource option type is unavailable, creation is blocked with actionable feedback; FS-007 does not invent placeholders or create, edit, archive, or manage availability for resources.

### Frontend behavior

- Add a minimal app-owned Schedule/Academic Data view switch and matching sidebar entry; do not add a routing dependency.
- Use one catalog page with entity tabs, a list/detail editor, and nested time-window editing under Study Types. Use controlled forms so 422 and 409 responses do not erase input.
- Show active/inactive and active-but-unavailable states separately. Archiving a parent never changes dependent badges.
- Fetch usage before deletion. If protected, present categorized blockers and Archive; otherwise require a destructive confirmation.
- After a successful mutation, refetch the affected administration data and planning options. Preserve valid selected IDs; retain and flag an invalid prior selection until the planner chooses a replacement.
- Keep last-known content on refresh failure and offer Retry. Announce validation/success feedback and manage focus for destructive dialogs.

## Complexity Tracking

No constitution violations require justification. Legacy assignment and name-conflict repair states are migration compatibility mechanisms, not alternative steady-state catalog models.

## Verification Plan

Run tests before production changes for each task group, then run all checks before commit.

```text
cd backend
python -m pytest tests/api/test_academic_catalog.py tests/services/test_academic_catalog.py tests/db/test_migrations.py tests/scripts/test_seed_dummy_planning_data.py
python -m pytest

cd ../client
npm run test
npm run lint
npm run build
```

Manual acceptance additionally covers keyboard-only operation in a real browser, rendered responsive list/editor layout, protected-deletion explanations, the complete no-seeded-academic-data workflow, participant success rates, and reference-environment timing described in `quickstart.md`. These aspects require human interaction, rendered-browser inspection, or timing against the documented end-to-end environment and therefore cannot be represented completely by jsdom unit tests alone.

Manual acceptance is not a blanket test-first exception. Keyboard focus, announcements, API behavior, and other reproducible outcomes that can be automated are covered by the preceding backend and client test tasks. If manual acceptance reveals a reproducible defect, implementation MUST first add or update a failing automated regression test wherever practical. When automation is genuinely impractical, the specific reason and repeatable manual verification path MUST be added to this plan before production code is corrected, and the result MUST be recorded in the applicable validation results file.
