# Implementation Plan: Dated Windows, Copying and Intensive-Week Scheduling

**Working Branch**: `master` (planning only) | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)
**Slice**: I-009 | **Input**: `specs/I-009-dated-intensive-windows/spec.md`

Human specification approval: “Approve I-009 specification and proceed with Goal 2”, in this chat on 2026-11-06. Implementation requires separate plan/task approval and a human-started Goal 3. The setup script reports a feature-derived BRANCH value; actual Git branch is `master`.

## Summary

Extend the existing single-form window record, catalog/editor, shared planning values, validation and unified optimizer. Add exact instructional intensive coverage and cohort/date variety directly after total selected teaching coverage, preserving all lower preferences, hard constraints and I-004 acceptance protections. Extend installed I-006 proof/worker paths coherently without making I-006/I-007/I-008 prerequisites.

## Technical Context

**Language/Version**: Python 3.12 (CI/container), TypeScript ~6.0.2, React 19, Vite 8, Node 24 (CI).
**Primary Dependencies**: Existing FastAPI 0.139.0, Pydantic 2.13.4, SQLAlchemy 2.0.45, Alembic 1.18.0, OR-Tools 9.15.6755 locks; no dependency changes.
**Storage**: SQLite/SQLAlchemy; in-place window extension through new sequential migration `0013_dated_teaching_windows.py` and `db/schema.py`. No live DB migration during planning.
**Testing**: pytest, Vitest/jsdom, TypeScript/Vite build and ESLint; real-browser timing/layout and assistive-technology/representative-user acceptance.
**Target Platform**: Existing authenticated planner web application; existing local calendar dates and wall-clock times.
**Performance Goals**: SC-008: 100 windows, 20 courses, 100 current teaching sessions, twenty changes, each affected open view refreshed within two seconds of save acknowledgement. Inherit optimizer workload/deadline policy; no new solve-time promise.
**Constraints**: One form per window, no stitching, no linked copies/week entity/bulk creation/new exam policy. Source changes never mutate sessions or captured history. Unmarked output stays deterministic and unchanged.
**Scale/Scope**: Catalog, course availability/derived opportunities, shared permission, optimizer/worker evidence, current alerts/freshness and result/comparison UI. No new service or architectural layer.

## Constitution Check

| Gate | Pre-research | Post-design |
| --- | --- | --- |
| I: Spec first | PASS: human approved current spec | PASS: FR-001–031 remain unchanged |
| II: Test first | PASS: TR-001 requests failing tests | PASS: story/contract tests precede production tasks; manual exceptions below |
| III: Testable acceptance | PASS: five stories and measurable FR/SC/TR | PASS: exact shared contracts/accounting and independent oracle tests |
| IV: KISS | PASS: retain stack/architecture | PASS: reuse model/routes/solver; small shared pure interval helpers have concrete consumers |
| V: Verified delivery | PASS for documentation planning | Before production, create dedicated `codex/021-dated-intensive-windows` branch from recovered tree, preserving existing changes and recording baseline. Dirty master does not qualify for the clean-master exception. Verify before any later approved commit. |
| VI: Incremental delivery | PASS: useful dated permission first | PASS: US1 includes minimum validation/freshness safety, then US2 objectives, US3 deeper protection/refresh verification, P2 copy/usability |
| Technology/contracts | PASS: existing backend/client | PASS: FastAPI under backend/app, tests under backend/tests, React/TS/Vite under client; contracts below |

No unresolved design clarification or constitution exception. No production code is written in Goal 2.

## Simplicity Check

1. **Simplest viable solution**: Extend `StudyTypeTimeWindow` and `TimeWindowPlan`, existing endpoints/editor and sequential optimizer objectives. Client-only copying submits ordinary creation.
2. **Necessary abstractions**: Pure applicability/instructional-union helpers in `schedule_generation.py` serve generation, validation and evidence. Extend detached fixed-teaching values because the existing spawned worker cannot access ORM data. No new layer/dependency.
3. **Deliberately excluded**: New week/copy tables, recurrence engine, scoring plugins, another solver, weighted coverage tradeoffs, event bus, timeout extension, bulk editing and capacity diagnostics.

## Phase 0: Research

[research.md](research.md) records repository findings, alternatives and resolved technical questions. Builder researched storage/catalog/client integration; fresh-context read-only research agent `/root/planning_research` inspected optimizer/worker/proof integration. Research is distinct from independent analysis.

## Phase 1: Design

### Persistence and catalog

Extend the existing table with kind/date/marker and nullable weekday. Backfill old records as weekly/false, preserving IDs, revisions, owners/activity/order and incoming references. Replace old uniqueness with weekly/dated partial unique indexes, excluding marker/activity. Use SQLite-safe batch alteration, equivalent new-DB metadata constraints, sequential schema detection and explicit rejection of partial/unsupported states. Historical snapshots are never rewritten. Preserve FK integrity and test both predecessor upgrade and fresh creation.

Retain owner/create and record/edit routes. PATCH can change one active form while preserving record ID; kind stays fixed. Validate discriminator/date/time/active relationships, aggregate German field errors, translate uniqueness races, enforce revisions/lifecycle/usage protections. Overlap is informative and adds no capacity. A client copy snapshots only values and carries no source relationship/ID/revision into creation. Exact duplicates still fail.

### Permission, availability and safety in the first increment

Update normalized values, loaders and every serializer: catalog, planning options, read-only course derived windows, snapshots and detached inputs. Explicit direct paths include api/draft_schedule.py:_constraints_to_response, calendar_workspace.py current constraintProfile serialization/reconstruction, schedule_lifecycle.py current window loading/new capture serialization, and DraftSchedulePanel.tsx derived-window rendering. Capture kind/date/marker in new snapshots and interpret missing fields in old captured snapshots as weekly/false without modifying their bytes. Current Calendar/List/detail and lifecycle validation use the same opportunity values; the read-only panel labels weekly/dated windows and displays full German dates rather than indexing a nullable weekday. Shared applicability matches dated records by exact date and weekly by weekday, for the same active form/record inside the course period. A session including breaks must fit one record; narrower explicit course restrictions remain additional constraints. Availability recognizes a usable dated-only occurrence of minimum elapsed session duration in the effective period; resource/holiday/exam rules still apply through existing checks. No weekly fallback is invented.

US1 explicitly updates semester_optimization.py date matching, filtering, stable mixed-kind ordering and retained-session containment, with failing dated-generation tests before production and its checkpoint. Intensive scoring/start-boundary extensions remain in US2. US1 also filters exam_scheduling.py automatic start proposals and active-start eligibility to weekly records only, preserving the existing exam policy for mixed and dated-only forms. Mixed/dated-only exam service/API/optimizer regressions precede production. US1 already integrates current validation and date/marker/form/revision freshness so enabling dated windows cannot expose unsafe intermediate behavior. US3 adds exhaustive current-view/failure/lifecycle/atomicity checks and completes refresh integration. Manual warnings retain their severity, and history/publication remains immutable.

### Exact objectives and candidate completeness

Use integer microsecond ticks, consistent with current `_time_ticks`; one LE = 2,700,000,000 ticks. Build actual 45-minute instructional blocks separated by existing ten-minute breaks and intersect with the union of applicable marked windows. Source-window identity does not affect credit. No floating or rounded score, elapsed-time credit or double counting. Check supported integer bounds.

Extend start-event closure with marked endpoints aligned to every instructional/break boundary for allowed session sizes, including discrete positive-overlap boundary representatives at inherited microsecond precision. Close these under packing-duration/resource events so intensive and variety optima cannot be missed inside wider ordinary windows. Independently exhaustive small alternatives must verify candidate completeness, including tightly packed cases; retain legacy seeds/order when unmarked.

For each cohort/date/LV, presence is the OR of selected positive-intensive candidates plus a constant for qualifying fixed unselected teaching. Count unique LVs and maximize summed `max(0,K-1)`. Capture fixed teaching units/form and its own marked context before worker dispatch; exclude exams and unrelated cohorts. Fixed teaching affects variety only, never selected coverage or occupancy mutation.

Order: `total_units` max → `intensive_teaching_time` max → `daily_variety` max → existing `conflicts`, `schedule_shape`, `lecturer_changes`, `room_changes`, `retained_drafts`, `canonical_temporal`, `canonical_resource` with existing directions and relative order. Conflicts remain hard zero; existing schedule-shape sub-order is retained. Lock each proven earlier optimum before a later stage; preserve installed unfinished/conditional/not-attempted proof and acceptance boundaries. Constant new stages must not materially consume deadline when unmarked; unchanged result/tiebreak tests are mandatory.

### Freshness, results and UI

Fingerprint kind/date/weekday/hours/form/activity/marker/revision in prepared inputs, current/generated evidence and final revalidation, including marker context for fixed teaching. Marker-only edits stale evidence without creating validity warnings. Reuse I-004 operation-wide transaction/idempotency and installed I-006 checkpoint/worker paths, including direction/key validation and exact acceptance reproduction.

Notify `App.tsx` catalogRevision immediately after write acknowledgement, before awaited catalog reload. Mark affected mounted current options/Calendar/List/detail non-current until refreshed, prevent prior-revision responses from restoring currency and provide failure/retry status. Preserve editor input, filters and unrelated selections. Revisited current views load current context; history uses captured facts. Existing revision callback suffices, with no new service.

Generation-constraint freshness is scoped to catalog/retry context plus the focused course and semester. Retained constraints may remain visible only for that same selection; save/reset require a successful current matching load. A same-selection refresh failure preserves entered dates while disabling those mutations. Semester workspace readiness is tracked separately; an unavailable, absent or mismatched focused course does not require a constraint load or block generation for other eligible courses. Cancelled loads from former selections cannot leave the current selection permanently loading or restore former constraints as current. Delayed save/reset responses update the editor and its feedback only while their initiating selection/catalog/retry context remains current.

Result/comparison facts identify total selected LE, exact intensive LE and summed/per-cohort/date variety for each arrangement separately. Installed proof labels show actual priority/status and convert time ticks into LE. German explanation permits single-LV fallback and promises no placement. Basic accessible controls ship with each story; US5 completes dedicated real-browser/AT/timed acceptance.

## Project Structure

Feature docs: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/interfaces.md`, `quickstart.md`, `tasks.md`. Separate continuity notes never alter task/checklist semantics.

| Impact | Actual paths |
| --- | --- |
| DB | `backend/app/models/planning.py`, `backend/app/db/schema.py`, new `backend/app/db/migrations/0013_dated_teaching_windows.py` |
| Catalog | `backend/app/{api,schemas,services}/academic_catalog.py` |
| Planning/validation | `backend/app/services/schedule_generation.py`, `draft_schedule_repository.py`, `draft_schedule_validation.py`, `calendar_workspace.py`, `schedule_lifecycle.py`, `exam_scheduling.py`; `backend/app/{api,schemas}/planning_options.py`; `backend/app/api/draft_schedule.py`; `backend/app/schemas/draft_schedule.py` |
| Solver/evidence | `backend/app/services/semester_optimization.py`, `conflict_aware_generation.py`, `optimization_operations.py`, `optimization_worker.py`; `backend/app/schemas/conflict_aware_generation.py` |
| Client catalog | `client/src/api/academicCatalog.ts`, `components/AcademicRecordEditor.tsx`, `components/AcademicCatalogList.tsx`, `pages/AcademicDataPage.tsx` |
| Client planning | `client/src/App.tsx`, `api/planningOptions.ts`, `api/draftSchedule.ts`, `api/conflictAwareGeneration.ts`, `hooks/useOptimizationOperation.ts`, `pages/CourseSchedulePage.tsx`, `components/OptimizationProofFacts.tsx`, `components/BatchResultSummary.tsx`, `components/DraftSchedulePanel.tsx`, `App.css` |
| Tests | Existing `backend/tests/{db,services,api,performance}` and colocated `client/src/**/*.test.ts[x]`; exact new paths in tasks |

**Structure Decision**: Extend the current application only. Result/comparison integration stays in existing CourseSchedulePage/BatchResultSummary/proof surfaces. No speculative component.

## Complexity Tracking

No new architectural layer, dependency or constitution exception. SQLite table alteration is required by current non-null weekday/unique constraints; migration/reference tests cover it.

## Verification Plan

### Authorized completion-aware search and report clarification — 2026-11-09

Add a bounded deterministic constructive hint inside semester_optimization.py only for generated-only searches containing a preferred-size remainder smaller than the course minimum. Reuse existing hard-filtered TemporalCandidates; greedily consider scarce-date courses, dates, completion-compatible session sizes and available resource assignments without changing the model, candidate ranks or objective expressions. Populate existing temporal/resource hint values; incomplete hints remain advisory and native search retains every alternative. Check the shared control during construction. Preserve the legacy path for problems without this demonstrated remainder problem. No room-domain pruning is justified without further profiling. No lecturer-allocation implementation, storage or API changes.

Clarify OptimizationProofFacts.tsx in German: measured candidate values do not imply a preference stage ran or was proven; schedule_shape is a composite penalty with a lower-is-better interpretation. Existing backend proof contracts remain authoritative. Behavioral tests precede production edits; compare first-incumbent coverage on detached 25/34-LE cases and proven outcomes with and without hints, plus deadline/cancellation/no-hint behavior. Run affected backend solver/acceptance/worker tests and frontend proof tests, types/lint/build. Timing observations are serial, do not prove the full twenty-run release SLA, and must not overlap other solver tests/builds.

### Authorized review corrections — 2026-11-09

Seed intensive candidate closure with recurring and dated resource-unavailability starts on their actual start date, as well as the existing ends. Preserve end boundaries beyond the latest feasible start through reverse closure, filtering returned starts only afterward. Verify lecturer/room boundaries against independently enumerated feasible alternatives, retaining unmarked candidate behavior.

Separate generation eligibility from date-constraint maintenance: constraint GET/PUT/DELETE may disregard only `MISSING_ACTIVE_TIME_WINDOW`, retaining every other academic/lifecycle/revision guard. Offer explicit date-limit inspection for that unavailable focused course; optional recovery loading/dirty state must not block generation for other eligible courses. Refresh availability after successful save/reset.

Preserve exact session/window clock strings in current draft and calendar serializers and calendar validation; retain `HH:MM` for minute-aligned values and use ISO seconds/fractions when present. Extend the calendar client validator and existing teaching editor to retain and display such values without browser time-input truncation. End-time arithmetic preserves fractional seconds. No new persistence field or scheduling precision rule is introduced. Add API/calendar/edit round-trip and frontend form regressions before production changes.

Future implementation commands, not current passing evidence. Backend commands run from `backend/` with `.venv/Scripts/python.exe`; npm commands run from `client/`. Use existing locks without upgrades.

- Test-first: write each story's failing tests before its production changes and record intended failures; rerun story and prior-story suites afterward.
- Full backend: `.venv/Scripts/python.exe -m pytest tests`.
- Shared contracts: `.venv/Scripts/python.exe -m pytest tests/api/test_academic_catalog.py tests/api/test_dated_intensive_windows.py tests/api/test_conflict_aware_generation.py tests/api/test_optimization_operations.py`; client `npm test -- src/api/academicCatalog.test.ts src/api/planningOptions.test.ts src/api/conflictAwareGeneration.test.ts`.
- Exact scoring/permission/migration: `.venv/Scripts/python.exe -m pytest tests/services/test_intensive_objectives.py tests/services/test_dated_intensive_windows.py tests/services/test_draft_schedule_validation.py tests/services/test_calendar_workspace.py tests/services/test_schedule_lifecycle.py tests/api/test_draft_schedule.py tests/api/test_calendar_workspace.py tests/api/test_schedule_lifecycle.py tests/db/test_migrations.py`. Exam compatibility: `.venv/Scripts/python.exe -m pytest tests/services/test_exam_scheduling.py tests/services/test_exam_optimization.py tests/api/test_exam_scheduling.py`. Derived display: `npm test -- src/components/DraftSchedulePanel.test.tsx`.
- Regression/performance: `.venv/Scripts/python.exe -m pytest tests/performance/test_semester_optimization_performance.py tests/performance/test_academic_catalog_performance.py tests/services/test_optimization_worker.py tests/services/test_optimization_operations.py tests/services/test_conflict_aware_generation_concurrency.py`.
- Client: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`. Targeted refresh/editor integration: `npm test -- src/pages/CourseSchedulePage.test.tsx src/pages/AcademicDataPage.test.tsx src/components/AcademicRecordEditor.test.tsx src/App.test.tsx`.
- SC-008 requires real save-acknowledgement-to-current-render timings for twenty changes with its dataset; record each view/sample, environment, maximum and errors. Fake timers/API-only metrics do not prove browser latency.
- Manual exceptions: jsdom cannot establish real screen-reader announcements, 320 CSS px/200% enlargement or five-person timed comprehension. [quickstart.md](quickstart.md) supplies mandatory browser/AT/user acceptance steps and evidence requirements; all other behavior remains automated test-first.

No custom checklist exists at planning start. Built-in requirements checklist is 16/16 and verifies specification quality only. Preserve reviewer-owned markers. Manual writing remains Goal 5; this guide only prepares validation. Do not implement/commit/push/merge in Goal 2.
