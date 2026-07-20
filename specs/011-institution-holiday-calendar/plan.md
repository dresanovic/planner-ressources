# Implementation Plan: FS-011 Institution-Wide Holiday Calendar and Avoidance

**Working Branch**: `master` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-institution-holiday-calendar/spec.md`

**Note**: Planning is being completed on `master`. Before production implementation, a `codex/` feature branch is recommended because this slice changes persisted data, every generation mode, API contracts, and planner UI behavior.

## Summary

Add one current-state institution holiday calendar whose records contain a unique full date, readable name, and optimistic revision. A focused FastAPI holiday boundary will provide list/create/read/update/delete behavior, while a new sequential migration adds the table without changing existing sessions. Single-course generation, legacy multi-course generation, and FS-010 optimization will load current holidays server-side and exclude those dates as hard constraints. FS-010's existing caller-supplied `unavailableDates` remain separate and are unioned with maintained holiday dates only inside the backend. Generation failures and optimizer reasons will carry structured holiday date/name context when holiday exclusion is substantiated. Current session alerts will be derived during schedule serialization, so holiday edits immediately change review warnings without persisting alerts or modifying sessions. React will add a Holidays leaf and focused CRUD controls under Academic Data, reuse existing session-alert rendering, and refresh the selected semester overview after holiday mutations; no standalone holiday entries are added to schedule review.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0 and React 19 frontend

**Primary Dependencies**: Existing FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, Alembic 1.18, React 19, Vite 8, and Vitest 4; no new runtime dependency

**Storage**: Existing SQLite database through SQLAlchemy; one new `institution_holidays` table created by sequential migration `0005_institution_holidays.py`; no history, archive, import-source, alert, or calendar-singleton table

**Testing**: pytest 9 for model/service/API/migration/generation/validation/concurrency/performance coverage; Vitest 4 with jsdom for API, administration, navigation, refresh, alert, and result-display coverage; TypeScript build and ESLint

**Target Platform**: Existing FastAPI service on Python 3.12 and modern desktop browsers used by planner users

**Project Type**: Full-stack web application with synchronous JSON HTTP contracts

**Performance Goals**: After a successful holiday or session mutation, the administration calendar and affected session alerts reflect saved state within 2 seconds for a reference semester containing up to 500 sessions and 50 holidays; CRUD and normal review remain usable within the same target

**Constraints**: One institution-wide calendar; one current holiday per date; full-day local dates only; hard exclusion for newly generated sessions; manual sessions remain saveable with alerts; no holiday history, archive state, automatic movement/deletion, import, timed closure, exam behavior, or standalone schedule-review entries; preserve existing FS-010 unavailable-date input and result semantics

**Scale/Scope**: One planner role; approximately 50 current holidays across years; reference semesters up to 500 saved sessions; all current single-course, legacy multi-course, and FS-010 generation paths

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The clarified FS-011 spec defines three independently testable stories, 25 functional requirements, ten measurable outcomes, explicit exclusions, and three recorded decisions.
- **Acceptance criteria — PASS**: Given/When/Then scenarios cover CRUD, duplicate/stale changes, no-history behavior, all generation modes, named holiday explanations, current session alerts, refresh, and non-mutation of saved sessions.
- **Test-first — PASS**: Migration, service, API, generator, stale-state, validation, client, regression, usability, and performance tests are identified before production code. No automated-test exception is planned.
- **Simplicity and KISS — PASS**: The design adds one table and one focused feature boundary, then extends existing generators, snapshot logic, derived validation, navigation, page refresh, and generic alert rendering. It adds no dependency, history model, provider abstraction, persisted alert, calendar singleton, job queue, or client state library.
- **Technology fit — PASS**: Backend work remains in FastAPI/SQLAlchemy and frontend work remains in React/Vite. The additive and modified JSON interfaces are documented in `contracts/holiday-calendar.openapi.yaml`.
- **Delivery workflow — PASS**: Planning may remain on `master`; the plan explicitly recommends a `codex/` feature branch before this larger cross-stack migration enters production implementation.
- **Verification before commit — PASS**: Focused and full backend/client commands plus migration, stale-input, regression, performance, and usability evidence are listed below and in `quickstart.md`.

### Post-design re-check

The Phase 1 design introduces no constitution violation. The dedicated holiday module is justified by three current consumers—CRUD, generation, and validation—and avoids forcing holidays into academic lifecycle or resource-unavailability abstractions whose rules do not fit. The table has no speculative provider fields or historical records. API changes are additive except for optional holiday context on existing failure/reason models and one new validation-alert code. Current generation, repository, snapshot, alert, and client refresh paths remain authoritative. No complexity-tracking exception is required.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Store current holidays as independent date/name/revision rows, expose five focused CRUD endpoints, load relevant rows once per request, pass date-keyed holiday context into existing generators and validation, and render the new alert/reason through existing generic components. Re-query holidays inside the existing persistence boundary before saving generated results.
2. **Necessary abstractions**: One small `holiday_calendar` backend module is necessary because CRUD, three generation workflows, and session validation require the same validation, range query, canonical ordering, and snapshot representation. One focused client API plus a compact administration component is necessary because generic Academic Data components assume active/archive/usage semantics that holidays deliberately lack. No generic repository or provider interface is needed.
3. **Deliberately excluded**: Holiday history/version tables, soft delete, archive/reactivate, provider/source identifiers, CSV/iCalendar parsing, synchronization ownership, multiple calendars, region/campus inheritance, partial-day ranges, calendar singleton rows, persisted alert rows, event sourcing, background jobs, automatic session repair, exam behavior, standalone review calendar entries, new state-management libraries, and generic unavailable-date abstractions beyond the current concrete consumers.

Implementation MUST NOT begin until all three answers remain consistent with the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/011-institution-holiday-calendar/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- holiday-calendar.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                      # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   |-- holiday_calendar.py                   # CRUD HTTP boundary
|   |   |-- draft_schedule.py                     # single generation and alert serialization
|   |   |-- multi_course_generation.py            # existing batch HTTP boundary
|   |   `-- conflict_aware_generation.py          # existing optimization HTTP boundary
|   |-- schemas/
|   |   |-- holiday_calendar.py                   # holiday CRUD DTOs/errors
|   |   |-- draft_schedule.py                     # holiday failure/alert additions
|   |   |-- multi_course_generation.py            # holiday failure context
|   |   `-- conflict_aware_generation.py          # holiday blocking context
|   |-- services/
|   |   |-- holiday_calendar.py                   # validation, CRUD, range query, snapshot
|   |   |-- schedule_generation.py                # single-course exclusion/evidence
|   |   |-- multi_course_generation.py            # server-side load and final validation
|   |   |-- semester_optimization.py              # named holiday evidence
|   |   |-- conflict_aware_generation.py          # snapshot union/revalidation
|   |   `-- draft_schedule_validation.py          # derived holiday alerts
|   |-- models/
|   |   `-- planning.py                            # InstitutionHoliday ORM entity
|   `-- db/
|       |-- schema.py                              # recognize/apply migration head
|       `-- migrations/
|           `-- 0005_institution_holidays.py
`-- tests/
    |-- api/
    |   |-- test_holiday_calendar.py
    |   |-- test_draft_schedule.py
    |   |-- test_multi_course_generation.py
    |   `-- test_conflict_aware_generation.py
    |-- services/
    |   |-- test_holiday_calendar.py
    |   |-- test_schedule_generation.py
    |   |-- test_multi_course_generation.py
    |   |-- test_semester_optimization.py
    |   |-- test_conflict_aware_generation.py
    |   `-- test_draft_schedule_validation.py
    |-- db/
    |   `-- test_migrations.py
    `-- performance/
        `-- test_holiday_calendar_performance.py

client/
|-- src/
|   |-- api/
|   |   |-- holidayCalendar.ts
|   |   |-- holidayCalendar.test.ts
|   |   |-- draftSchedule.ts                      # new alert code/failure context
|   |   `-- conflictAwareGeneration.ts            # holiday reason context
|   |-- components/
|   |   |-- ApplicationNavigation.tsx              # Holidays navigation leaf
|   |   |-- HolidayAdministration.tsx              # list/editor/delete confirmation
|   |   |-- HolidayAdministration.test.tsx
|   |   |-- DraftSchedulePanel.tsx                 # generic renderer reused
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- BatchResultSummary.tsx                 # stable multiple-holiday keys
|   |   `-- BatchResultSummary.test.tsx
|   |-- pages/
|   |   |-- AcademicDataPage.tsx                   # holiday administration branch
|   |   |-- AcademicDataPage.test.tsx
|   |   |-- CourseSchedulePage.tsx                 # external alert refresh
|   |   `-- CourseSchedulePage.test.tsx
|   |-- test/
|   |   `-- draftScheduleFixtures.ts
|   `-- App.tsx                                    # existing revision propagation
`-- package.json
```

**Structure Decision**: Retain the current backend/client split. Use a dedicated holiday API/schema/service because holidays have neither the archive/usage lifecycle of academic catalogs nor the owner/time-range shape of resource unavailability. Add Holidays as an Academic Data navigation leaf and branch within the existing page shell rather than create a route or workspace. Extend generator and validation modules at their current decision points, and keep holiday merging server-side so browser state can never weaken a hard constraint.

**Agent Context Update**: This Spec Kit installation contains no `update-agent-context.ps1` or equivalent agent-context script under `.specify/scripts`; the required location was checked and no substitute context file will be invented.

## Design Decisions

### Current-state persistence and CRUD

- Add `InstitutionHoliday(id, date, name, revision)` with a unique constraint on `date`, a positive-revision check, and mapper-level optimistic version protection. Trim names, reject blank names and names over 200 characters, and accept valid past, future, and leap-day dates.
- Treat the calendar as the ordered collection of current rows; do not add a singleton calendar record. Stable ID plus unique date and revision is sufficient for CRUD and is a clean future input for FS-017 without choosing import identity or ownership now.
- Edit replaces the current date/name and increments revision. Confirmed delete physically removes the row. Neither action retains a prior holiday record or creates a relationship to sessions.
- Add migration `0005_institution_holidays.py`, update schema-head detection, and recognize the current FS-008-through-FS-010 schema as the predecessor. Empty databases create current metadata directly; existing recognized databases migrate without backfill.
- Expose `GET/POST /api/holidays`, `GET/PATCH/DELETE /api/holidays/{holidayId}`. Update/delete require `expectedRevision`; delete additionally requires explicit confirmation. Return the established structured `errors` envelope for invalid fields, duplicates, missing records, confirmation, and stale writes.
- Preflight duplicate dates for actionable feedback and keep the unique database constraint authoritative. Translate concurrent unique violations and stale mapper writes to stable 409 responses rather than leaking server errors.

### Holiday query and snapshot boundary

- Load holidays once per applicable date range, ordered by `(date, id)`, and represent them internally as an immutable date-keyed map plus canonical `(id, date, name, revision)` tuples. Do not query per course or session.
- Use calendar dates directly; no timestamp or timezone conversion is introduced. Only a session's date participates in the holiday rule.
- Row revision protects a stale edit to one holiday. Generation safety additionally fingerprints or reloads the complete relevant holiday set so a concurrent add, delete, redate, or rename is observable.
- Perform final holiday validation inside the existing generation persistence boundary after acquiring the same semester write barrier used by FS-010 where necessary. A result invalid under the current calendar is not saved; existing drafts remain unchanged and the operation returns a stale-calendar outcome.

### Generation integration and explanations

- Extend the pure single-course generator with named holiday context. Candidate-date selection and its secondary feasibility scan both exclude holiday dates so placement and failure classification use identical rules.
- Legacy multi-course generation bulk-loads relevant holidays, passes them into each independent course generation, and re-reads them during its existing pre-persistence validation. Only affected course results fail/stale; unrelated course outcomes keep established behavior.
- FS-010 retains caller-supplied `unavailableDates` unchanged in its public contract. Internally, union those dates with maintained holiday dates for candidate exclusion, but keep evidence distinct: `UNAVAILABLE_DATE` remains generic caller input and `INSTITUTION_HOLIDAY` carries the maintained holiday name/date.
- Never echo maintained holidays into FS-010's `unavailableDates`; doing so would preserve a later-removed holiday as a caller-supplied exclusion. Include canonical holiday state in existing opaque preparation/shared fingerprints and reload it in current pre/post-solve validation.
- Add optional structured `holidayDate` and `holidayName` to single-course failures, legacy batch course failures, and FS-010 blocking reasons. The two fields are present together and non-null for `INSTITUTION_HOLIDAY` evidence and are both omitted otherwise. One reason entry represents one substantiated holiday. Preserve existing primary failure/outcome classifications and append holiday evidence only when the date was within the active planning period, matched an allowed teaching day/window, and removed an otherwise considered placement.
- If a date is both a maintained holiday and caller-supplied unavailable date, exclude it once and report the named holiday once. Deduplicate optimizer evidence by `(code, holidayDate)` rather than code alone, and use the same composite key in React so multiple holidays remain visible.
- Existing saved sessions remain available as retained current alternatives in FS-010 and are never moved by calendar changes. Holiday hard constraints apply only to newly generated candidates.

### Derived validation and refresh

- Add `INSTITUTION_HOLIDAY` to the existing validation-alert code set. Pass current holidays into `collect_validation_alerts`; for each matching session append a non-blocking alert whose message includes the holiday name and ISO date and whose related-session list is empty.
- Do not persist alerts or copy holiday values into Draft Sessions. `GET /api/draft-schedules` and normal generation/mutation serializers derive alerts from current calendar state on every reload.
- Existing manual create/edit structural validation stays unchanged: a session on a holiday saves if otherwise valid, then receives the derived alert.
- The generic `DraftSchedulePanel` alert renderer remains structurally unchanged. List and weekly modes show the alert only inside affected sessions; no holiday collection is passed to review components and no empty holiday day/card is synthesized.
- Holiday CRUD calls the existing catalog-change callback. Extend `CourseSchedulePage`'s external revision response to reload both planning options and the selected semester schedules while preserving semester selection, filters, and list/weekly mode. On refresh failure, retain last-known schedules and existing retry behavior.

### Client administration

- Add `holidays` after Semesters in `ACADEMIC_DATA_CATEGORIES`, reusing current navigation expansion, active state, narrow-layout dialog, and focus behavior.
- Add a focused `holidayCalendar.ts` client and compact HolidayAdministration branch. Show all current records sorted by date with date/name, provide date and name fields for create/edit, and require a confirmation dialog before hard delete.
- Do not reuse `AcademicCatalogList`, `AcademicRecordEditor`, or `ProtectedDeleteDialog` where doing so would introduce status, archive, usage, or protected-history semantics. Reuse existing CSS classes and accessible status/error/dialog conventions rather than add a new visual system.
- Preserve form content on validation/stale failures, reset selection only after successful mutation, and notify the app of catalog changes only after a successful server response.

## Complexity Tracking

No constitution violations require justification. The focused holiday service and client component are necessary because the existing generic catalogs encode incompatible lifecycle rules; they do not introduce a new architectural layer or dependency.

## Verification Plan

Write failing tests before production behavior. Run backend commands from `backend/` and client commands from `client/`.

```text
python -m pytest tests/services/test_holiday_calendar.py tests/api/test_holiday_calendar.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_generation.py tests/services/test_multi_course_generation.py tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py
python -m pytest tests/services/test_draft_schedule_validation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py tests/api/test_conflict_aware_generation.py
python -m pytest tests/performance/test_holiday_calendar_performance.py
python -m pytest
npm test -- holidayCalendar HolidayAdministration ApplicationNavigation AcademicDataPage
npm test -- draftSchedule DraftSchedulePanel BatchResultSummary CourseSchedulePage conflictAwareGeneration
npm test
npm run lint
npm run build
```

Verification evidence must include clean and FS-008-through-FS-010 schema startup; unique-date and positive-revision constraints; valid past/future/leap-day CRUD; whitespace, duplicate, stale, and concurrent-write handling; no retained history; no session mutation; all three generation paths excluding current holidays; generic unavailable dates remaining distinct; multiple named holiday reasons; failure/reason deduplication; calendar changes during generation preserving invalidated drafts; manual and existing session alerts after create/edit/delete; coexistence with other alerts; review filters/modes preserved; no standalone schedule-review entry; alert refresh and last-known-state failure behavior; future import fields remaining absent; the 50-holiday/500-session 2-second reference target; representative planner usability protocols; and full FS-001-through-FS-010 regression coverage.
