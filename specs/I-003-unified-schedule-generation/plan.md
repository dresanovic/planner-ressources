# Implementation Plan: Unified Teaching Schedule Generation

**Working Branch**: `master` (planning only; implementation requires
`codex/I-003-unified-schedule-generation` or an equivalent isolated clean
worktree) | **Date**: 2026-08-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`specs/I-003-unified-schedule-generation/spec.md`

**Note**: The clarified specification is authoritative where the earlier
`docs/architecture/unified-teaching-schedule-generation.md` differs, particularly
for immediate constraint activation, active-versus-past exams, and study-type
ownership of weekly windows.

## Summary

Make the existing conflict-aware OR-Tools workflow the only teaching scheduler
for selections of one to twenty courses. Extend its preparation and freshness
snapshot to include active saved course dates, live study-type windows, unselected
teaching sessions, and active exams; active exams are immutable resource/cohort
occupancy and a same-course latest teaching boundary, while past exams are
ignored. Save course-semester date overrides immediately through their own
lifecycle- and revision-checked operation. Retire the legacy single-course and
independent batch operations with structured `410 Gone` guidance and no mutation.

Replace the Calendar's single/batch UI split with one selection workflow and a
focused course date editor that shows study-type windows read-only. Give teaching
List rows a dedicated nine-field grid shared with the header, explicit narrow
labels, and scoped CSS. Preserve the existing conflict codes but render precise,
resource-specific lecturer, room, and cohort warnings.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0.2 with JSX and React
19.2.7 frontend; Node 24 in the production image

**Primary Dependencies**: Existing FastAPI 0.139, SQLAlchemy, Pydantic 2.13,
OR-Tools CP-SAT, React 19, React DOM 19, and Vite 8.1; no new runtime dependency

**Storage**: Existing SQLite/SQLAlchemy planning data. Reuse
`GenerationConstraintSet` for the optional course-semester date override; stop
reading/writing its legacy copied window children. Existing draft schedules,
sessions, exams, holidays, resources, and lifecycle records remain in place.

**Testing**: pytest 9 backend unit/service/API/contract/regression tests; Vitest 4
with jsdom for React component/page behavior; existing ESLint and TypeScript/Vite
build; manual teaching List review at 1280, 820, and 320 CSS pixels plus a
1280-pixel viewport at 200% browser zoom; end-to-end scheduling review; the
defined one-warm-up/twenty-run performance protocol; and the defined
ten-participant unaided planner usability review

**Target Platform**: Existing containerized Linux FastAPI service and supported
desktop browsers on Windows; teaching List acceptance at the existing 821-pixel
wide boundary and 320-to-820-pixel narrow range, including the defined 200%
browser-zoom case

**Project Type**: Cross-stack feature in the existing FastAPI and React/Vite web
application

**Performance Goals**: In the documented acceptance environment, after one
unmeasured warm-up, twenty sequential fresh-input reference operations of up to
twenty selected courses, six hundred requested teaching units, and five hundred
protected occurrences all finish with a saved result or actionable failure within
sixty seconds and at least nineteen finish within thirty seconds; evidence records
the application version, allocated processor/memory, environment, durations, and
outcomes

**Constraints**: One solver and one visible workflow; one-to-twenty distinct
same-semester courses; active editable revision only; zero newly generated
lecturer/room/cohort conflicts; half-open interval overlap; active exams protected
and past exams ignored; immediate independent date-override save; live read-only
study-type windows; atomic proven draft replacement; no exam movement, automatic
repair, algorithm selector, new dependency, or database migration

**Scale/Scope**: Existing conflict-aware generation/optimization services and
contracts, date-constraint repository/API, validation/lifecycle integrations,
three retired API operations, one Calendar planning page and generation panel,
teaching List/warning presentation, and related backend/client regression suites

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first - PASS**: The clarified specification and completed requirements
  checklist exist under `specs/I-003-unified-schedule-generation/` before
  production implementation.
- **Acceptance criteria - PASS**: Five prioritized stories have independently
  testable Given/When/Then scenarios, explicit edge cases, 53 functional
  requirements, nine test requirements, and eleven measurable success criteria.
- **Test-first - PASS**: Service, API contract, optimizer, state-transition,
  component, layout, regression, and performance tests are identified in this
  plan and `quickstart.md`. Tasks must place failing tests before production edits.
- **Simplicity and KISS - PASS**: The plan extends the existing optimizer and
  optimistic snapshot, reuses the existing constraint record, keeps current
  conflict codes, and fixes the CSS cascade directly. It adds no generator,
  database table, solver phase, data-grid, or dependency.
- **Technology fit - PASS**: Backend work remains in FastAPI/SQLAlchemy/OR-Tools;
  frontend work remains in React/Vite. Proposed API and UI contracts are captured
  under `contracts/`.
- **Delivery workflow - PASS WITH REQUIRED ACTION**: This is a broad,
  customer-facing cross-stack change and the current `master` worktree contains
  unrelated user changes. Before production implementation, use
  `codex/I-003-unified-schedule-generation` or an equivalent isolated clean
  worktree while preserving those changes.
- **Verification before commit - PASS**: Focused and complete backend/client
  commands plus manual and performance evidence are listed below and in
  `quickstart.md`.

### Post-design re-check

Phase 1 introduces no constitution violation. A single added constraint mutation
contract is necessary because clarified constraints must commit before generation;
it reuses the existing router, model, and validation response. Extending the
optimizer's existing fixed occupancy and snapshot is less complex than another
engine or locking layer. The UI contract replaces two surfaces with one and uses
component-scoped CSS rather than a grid dependency. Legacy window rows remain only
as ignored compatibility data, avoiding an unrelated schema migration. All new
contract fields have current consumers in Calendar Planning or stale validation.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Route one and many selected courses through the
   existing conflict-aware prepare/generate service; add active exams and current
   constraints to its existing inputs and token checks; save only date overrides
   through the existing constraint resource; return 410 from legacy operations;
   replace the mode split with one React panel; scope the conflicting CSS and map
   current validation codes to precise copy.
2. **Necessary abstractions**: No new architectural layer. Extend the existing
   normalized fixed-occupancy value to identify teaching versus active-exam
   evidence, and add one small client conflict-presentation mapper because the
   same three codes require stable distinct titles/details. Retain existing API,
   repository, solver, and component boundaries.
3. **Deliberately excluded**: A new generator or strategy interface, planner
   algorithm choice, automatic exam rescheduling, automatic unselected-schedule
   repair, course-specific weekly-window persistence/editing, bulk date-override
   rules, database migration solely to rename/remove legacy constraint tables,
   pessimistic locks, background jobs, a data-grid library, a general warning
   framework, and unrelated Calendar or Academic Data redesign.

Implementation MUST NOT begin until these answers remain consistent with the
approved I-003 vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/I-003-unified-schedule-generation/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- unified-teaching-generation.openapi.yaml
|   `-- unified-teaching-generation-ui.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                  # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- models/
|   |   `-- planning.py                       # existing constraint/exam entities
|   |-- schemas/
|   |   |-- draft_schedule.py                 # date constraint mutation/read shapes
|   |   `-- conflict_aware_generation.py      # prepared constraints/exam reason codes
|   |-- api/
|   |   |-- draft_schedule.py                 # save/reset; retired single operation
|   |   |-- conflict_aware_generation.py      # only prepare/generate endpoints
|   |   `-- multi_course_generation.py        # retired batch 410 responses
|   `-- services/
|       |-- draft_schedule_repository.py      # dates only; live study-type windows
|       |-- conflict_aware_generation.py      # active exams, tokens, atomic save
|       |-- semester_optimization.py           # exam deadline/fixed occupancy rules
|       |-- draft_schedule_validation.py       # distinct deduplicated alert evidence
|       |-- calendar_workspace.py              # live constraint revalidation
|       `-- schedule_lifecycle.py              # current constraint/window snapshots
`-- tests/
    |-- api/
    |   |-- test_conflict_aware_generation.py
    |   |-- test_draft_schedule.py
    |   `-- test_multi_course_generation.py
    `-- services/
        |-- test_conflict_aware_generation.py
        |-- test_semester_optimization.py
        |-- test_draft_schedule_repository.py
        |-- test_draft_schedule_validation.py
        |-- test_exam_scheduling.py
        `-- test_schedule_lifecycle.py

client/
|-- src/
|   |-- api/
|   |   |-- conflictAwareGeneration.ts        # only supported generation calls
|   |   `-- draftSchedule.ts                  # immediate date save/reset contract
|   |-- pages/
|   |   |-- CourseSchedulePage.tsx            # one generation workflow/focused course
|   |   `-- CourseSchedulePage.test.tsx
|   |-- components/
|   |   |-- MultiCourseGenerationPanel.tsx    # evolve/rename into unified panel
|   |   |-- DraftSchedulePanel.tsx             # dates, precise warnings, row markup
|   |   `-- DraftSchedulePanel.test.tsx
|   `-- App.css                                # scoped occurrence and teaching grids
`-- package.json                               # existing commands; no dependency change
```

**Structure Decision**: Preserve the established FastAPI/React split and extend
the current conflict-aware generation vertical slice. The implementation may
rename the current `MultiCourseGenerationPanel` to a teaching-neutral name, but
must not introduce a wrapper plus a second panel. Constraint persistence remains
in the existing draft-schedule repository/router; exam lifecycle semantics reuse
`exam_scheduling.institution_today`; List layout stays in current markup/CSS.

**Agent Context Update**: The prescribed `.specify/scripts/*/update-agent-context`
script is not present in this Spec Kit installation. The script directory was
checked after Phase 1; no context file was invented or modified.

## Implementation Design

### 1. Constraint ownership and immediate activation

- Change `load_generation_constraints` to obtain dates from the optional
  `GenerationConstraintSet` but always call `load_time_windows` for the course's
  current study type. Return study-type identity and read-only windows to the
  client.
- Replace the save signature that accepts copied windows with a date-only save.
  Validate start/end ordering and semester bounds, claim the active working
  revision, enforce `expectedRevision`, increment only on a real change, clear
  legacy child windows, commit, and reload.
- Add a reset operation with the same lifecycle/concurrency checks. Its response
  contains inherited constraints and the refreshed current draft rather than an
  empty 204, allowing the client to replace validation alerts authoritatively.
- Remove all constraint writes from single, batch, and conflict-aware generation.
  Preparation/generation only read effective constraints. Update Calendar and
  lifecycle projections that currently prefer copied windows so they use live
  mappings and revalidate on study-type/window changes.

### 2. One prepared generation snapshot

- Retain `/api/draft-schedules/optimization/prepare` and `/generate` as the one
  supported API path. Strengthen selection validation for one-to-twenty unique,
  eligible courses from one requested semester and active revision.
- Extend prepared course output with effective planning period, custom/default
  state, study type, mapped windows, and precise unavailable reasons. These are
  read-only evidence, not editable request overrides.
- Build shared/per-course snapshot tokens from the existing evidence plus active
  date constraint revision/inherited semester dates, study-type/window revisions,
  active exams, and selected-course exam deadline. Exclude past exams. Recompute
  tokens immediately before solving and again before persistence using the
  service's established stale checks.
- Preserve replacement preparation and require explicit confirmation listing all
  selected drafts that would be replaced.

### 3. Conflict-safe optimizer extension

- Query all `ExamSession` rows in the selected semester and classify them with the
  shared institution-local `institution_today()` definition. Convert only active
  exams to fixed occupancy with their lecturer, room, cohort, date, and interval.
- Pass the selected course's active exam start as `latest_teaching_end`. Reject
  candidates ending later; allow a session ending exactly at exam start.
- Continue treating unselected teaching as fixed occupancy and enforcing mutual
  lecturer, room, and cohort constraints among selected candidates. The solver
  may use prior conflicts only as a secondary improvement score; no new conflict
  is permitted.
- Retain `LECTURER_OCCUPIED`, `ROOM_OCCUPIED`, and `COHORT_OCCUPIED` for active
  exam conflicts and attach the protected source kind and exam identifier; use
  `ACTIVE_EXAM_BOUNDARY` only for the same-course latest teaching-end rule. Add
  `STUDY_TYPE_WINDOW_UNAVAILABLE` when current study-type mappings cannot host
  the minimum session. Save only a proven permitted, non-worsening complete or
  partial result under the existing operation deadline.
  Any stale, invalid, timeout, unproven, or persistence failure rolls back all
  selected draft mutations and does not touch constraints or exams.

### 4. Immediate legacy retirement

- Replace the legacy single generate handler and independent batch prepare/generate
  handlers with a shared small response constructor returning HTTP 410, code
  `GENERATION_ENDPOINT_RETIRED`, a concise message, and the two supported paths.
- Prove via API tests that service/solver functions are not called and persisted
  state is byte-for-byte/logically unchanged. Remove the corresponding client
  imports, API calls, mode state, and user-facing controls. Production scheduling
  code unique to the retired services may be deleted once no supported caller or
  regression dependency remains; do not retain it as a fallback.

### 5. Unified Calendar interaction

- Evolve the existing multi-course selection panel into the sole teaching
  generation panel; one selected course is a normal valid selection. Show count,
  selected courses, preparation status, replacement courses, and one outcome per
  course.
- Keep a focused-course selector within Planning inputs. The date form explicitly
  saves/resets through the new constraint contract and displays study type/windows
  without editing controls. Disable preparation during invalid/dirty/saving date
  state and explain how to proceed.
- On save/reset/generation/manual mutation, replace schedules and alerts from an
  authoritative refresh. On stale response, discard prepared tokens and require
  preparation again. Do not maintain parallel single/batch client state.

### 6. Precise warnings and stable List layout

- Confirm validation deduplication identity includes affected session, related
  session, and category. Preserve distinct lecturer, room, and cohort codes and
  related occurrence/resource evidence.
- Add a direct client mapper for those three codes with localized visible titles
  equivalent to Lecturer conflict, Room conflict, and Cohort conflict and precise
  sentences naming the shared resource. Related course/date/interval remain
  visible; do not fall back to one generic overlap sentence for known codes.
- Give header and teaching rows one dedicated nine-column class/template in the
  required order. Scope the generic five-column `.schedule-occurrence-row` rule to
  its owning list so the cascade cannot override teaching rows. Keep warnings in
  the Date cell.
- Add explicit narrow labels in markup/CSS and wrapping/overflow rules. Component
  tests assert DOM field order/labels and warning category identity; manual review
  covers computed layout at wide, narrow, long-copy, and 200% zoom states.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Implementation must run focused tests first and then the complete suites.

From the repository root:

```text
python -m pytest backend/tests/services/test_conflict_aware_generation.py backend/tests/services/test_semester_optimization.py backend/tests/services/test_draft_schedule_repository.py
python -m pytest backend/tests/api/test_conflict_aware_generation.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py
python -m pytest backend/tests/services/test_draft_schedule_validation.py backend/tests/services/test_exam_scheduling.py backend/tests/services/test_schedule_lifecycle.py
python -m pytest backend/tests
```

From `client/`:

```text
npm test -- src/pages/CourseSchedulePage.test.tsx src/components/DraftSchedulePanel.test.tsx
npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/components/ScheduleOccurrenceList.test.tsx
npm test
npm run lint
npm run build
```

Expected evidence:

- One- and multi-course generation introduce zero lecturer, room, or cohort
  overlaps against selected teaching, protected teaching, and active exams.
- Same-course teaching ends no later than active exam start; exact adjacency is
  accepted and past exams do not affect results or token freshness.
- Constraint save/reset is immediate, revision-safe, and refreshes warnings while
  leaving sessions unmoved; later generation failure preserves those constraints.
- All retired operations return structured 410 guidance and cause no mutation.
- Cancellation, stale input, timeout, unproven solve, and persistence failure
  preserve prior drafts, manual edits, constraints, exams, and unrelated state.
- Client tests prove one visible workflow, no editable weekly windows, explicit
  replacement, per-course outcomes, distinct conflict titles/details, resolved
  warning removal, and stable ordered List fields.
- Complete suites prove manual teaching/exam management, lifecycle/publication,
  Calendar modes, resources, and Academic Data retain established behavior.
- Manual and performance steps in `quickstart.md` pass. If any command cannot run,
  record the exact reason, affected acceptance scenarios, and residual risk before
  commit.
- At least 90% of a minimum ten representative semester planners complete the
  SC-006 selection, focused-constraint review, and unified-preparation journey on
  their first unaided attempt; otherwise SC-006 remains failed or unverified.
