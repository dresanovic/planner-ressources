# Implementation Plan: I-005 — Filterable Course Lists for Generation and Administration

**Working Branch**: `master` (planning only; implementation isolation required below) | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

**Input**: `specs/I-005 - filter-course-plan-list/spec.md`, including confirmed session-only, independent filter memory.

## Summary

Add local cohort filtering to the existing generation selector and Academic Data course list. Keep the complete generation selection independent of rendered matches. Existing responses already supply semester/cohort identity: no backend, database, HTTP contract, generator, or dependency change is needed. Preserve I-004 preparation and joint decision behavior. Planning does not authorize starting production work.

## Technical Context

**Language/Version**: Existing TypeScript ~6.0.2, React ^19.2.7 and Vite ^8.1.1 from client/package.json; Python 3.12 container baseline, FastAPI 0.139.0 backend unchanged.
**Primary Dependencies**: Existing React state, native form controls, Vitest/jsdom; no additions.
**Storage**: In-memory React state only; existing SQLite academic/schedule data untouched. No browser storage or migration.
**Testing**: Colocated Vitest tests; existing pytest API/service regressions; manual screen reader, viewport/text enlargement, timing and planner walkthrough.
**Target Platform**: Existing browser application and narrow planning panel, including 320 CSS-pixel width and 200% text enlargement.
**Project Type**: Frontend slice in existing full-stack web application.
**Performance Goals**: After catalog load, at least 19 of 20 cohort changes per surface display matches/count within one second for 94 courses (SC-006).
**Constraints**: Single cohort; no search, grouping or bulk selection. Full selected-ID set remains authoritative; 1–20 distinct courses, eligibility, editable revision, stale-state and atomic replacement safeguards unchanged. Follow existing German terminology catalog.
**Scale/Scope**: Two course lists; eleven target-cohort courses among 94 semester courses. Administration must filter the complete loaded catalog, not just its first page. No new server scalability or telemetry work.

## Constitution Check

*Pre-research and post-design gates both PASS for planning; implementation prerequisites remain explicit tasks.*

| Principle / constraint | Evidence and decision |
| --- | --- |
| I. Spec first | Approved slice and clarification in spec.md; no production changes in this workflow. |
| II. Test first | Each story starts with failing tests before the smallest production change. Manual-only visual/screen-reader/usability checks have named paths in quickstart.md. |
| III. Clear acceptance | Four Given/When/Then stories; FR-001–017, TR-001–006 and SC-001–009 mapped into tasks. |
| IV. KISS | Existing list components, parent state and local predicates; no store, provider, endpoint or filter framework. |
| V. Verified delivery | Current master has unrelated work; do not invoke the clean-master exception. Before production work create/use a codex/ feature branch or isolated worktree without discarding unrelated changes. Verification commands below are mandatory before commit. |
| VI. Incremental delivery | Generation discovery, administration discovery, complete selection safety, then cross-surface accessibility/lifetime verification. Basic selection safety is mandatory from the first generation increment. |
| Stack / layout / contracts | Existing React/TypeScript/Vite under client; FastAPI backend unchanged. Existing boundary projections documented in contracts/course-list-contract.md; no new cross-stack fields. |

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Filter already-loaded records at rendering time by stable cohort ID and applicable semester. Keep generation filter state in the always-mounted CourseSchedulePage; keep administration semester/cohort state in App so it survives AcademicDataPage unmount. Pass ordinary props. Preserve selection and captured generation evidence.
2. **Necessary abstractions**: One shared test fixture for the same eleven-of-94 catalog in both response shapes. A narrow optional metadata renderer on AcademicCatalogList supports course identity without changing other categories. No shared production filter abstraction is needed for two small predicates.
3. **Deliberately excluded**: Generic state management, local/sessionStorage, per-semester filter caches, server-side filters, endpoints/schema changes, migrations, sorting/grouping, search, bulk selection, unrelated refactoring and new tooling dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/I-005 - filter-course-plan-list/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/course-list-contract.md
  quickstart.md
  tasks.md
  checklists/requirements.md
```

### Source Code (repository root)

```text
client/src/App.tsx                                      # admin filter ownership
client/src/App.test.tsx                                 # navigation lifetime
client/src/pages/CourseSchedulePage.tsx                  # generation filter ownership/context
client/src/pages/CourseSchedulePage.test.tsx             # exact input/I-004 integration
client/src/components/MultiCourseGenerationPanel.tsx     # visible matches/full selection review
client/src/components/MultiCourseGenerationPanel.test.tsx
client/src/pages/AcademicDataPage.tsx                    # semester/cohort predicates/load states
client/src/pages/AcademicDataPage.test.tsx
client/src/components/AcademicCatalogList.tsx            # optional course identity metadata
client/src/App.css                                      # scoped wrapping/focus/reflow
client/src/test/fixtures/courseLists.ts                  # new shared acceptance fixture
client/src/api/conflictAwareGeneration.test.ts          # existing contract regression
backend/tests/api/test_planning_options.py              # unchanged regressions only
backend/tests/api/test_academic_catalog.py
backend/tests/services/test_academic_catalog.py
backend/tests/api/test_conflict_aware_generation.py
backend/tests/services/test_conflict_aware_generation.py
backend/tests/services/test_conflict_aware_generation_concurrency.py
```

**Structure Decision**: Retain existing files/boundaries. No production backend/API type change is planned. If implementation discovers a missing field or altered boundary, update spec/design/contracts and add failing boundary tests before changing it.

## Phase 0 — Research

Completed repository research is in research.md. Both list projections contain cohort and semester identity. Academic Data loads all pages; generation receives all applicable semester courses, including unavailable entries. App keeps the schedule page mounted while administration unmounts. Neither course projection exposes a course code; display available identity and an ID fallback when needed without inventing a stored code. All technical unknowns resolved.

## Phase 1 — Design and Contracts

- data-model.md defines existing records, local filter state, complete selection and state transitions.
- contracts/course-list-contract.md specifies render-only predicates, filter props, response assumptions and unchanged generation boundaries.
- quickstart.md defines runnable checks and expected outcomes.
- Keep course options complete when passing them to the generation panel; derive visible matches there. Never filter selected IDs or pass visible IDs to startBatch.
- Parent-controlled cohort state survives panel closure. Reset only in the committed semester transition, after existing unsaved-edit navigation handling accepts it; cancelled navigation must preserve state.
- Administration owns no new mutations. Preserve the selected editor, values, editor generation and exact action handlers through filter changes. Render course metadata through a scoped optional list extension.
- CourseSchedulePage must track initial and refresh planning-option load outcomes at the page boundary, not just panel-local matches. Initial loading/failure can render outside the panel; with retained options, expose pending/failed freshness, preserve selected IDs and last-known identity, and do not report successful no-matches or permit generation from failed-refresh context. Pass retrieval/freshness context to the panel when mounted. Distinguish successful empty data, filtered no-match, loading and failure explicitly. Retain an unavailable filter label when a chosen cohort disappears; do not broaden silently. Keep missing selected IDs reviewable with last-known identity or an explicit ID/unavailable fallback.
- Use native labelled controls, live result/count feedback, existing German terminology and visible focus. Do not change calendar-session filters.

## Complexity Tracking

No constitution exception or new architectural layer is requested. Dirty master is acceptable for documentation preparation only; production isolation is a prerequisite, not an exception. A shared test fixture and optional catalog metadata slot each serve two concrete verification/rendering needs without adding a dependency.

## Verification Plan

Write tests first for each story, observe failure for the intended behavior, then implement that increment and rerun its focused checks. From repository root:

```powershell
npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/AcademicDataPage.test.tsx src/App.test.tsx src/api/conflictAwareGeneration.test.ts
npm --prefix client test
npm --prefix client run build
npm --prefix client run lint
```

From `backend/`, using its existing virtual environment (root executable is `backend/.venv/Scripts/python.exe`):

```powershell
.venv/Scripts/python.exe -m pytest tests/api/test_planning_options.py tests/api/test_academic_catalog.py tests/services/test_academic_catalog.py tests/api/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation_concurrency.py
```

No new backend test implementation is needed while server behavior stays unchanged. Existing API tests plus frontend request assertions verify shared contracts. Manual checks in quickstart.md cover actual keyboard/screen-reader speech, reflow, 200% text and the planner comprehension walkthrough; jsdom cannot prove these visual/assistive outcomes. Time twenty loaded-catalog filter changes per surface with a browser performance recording. Record outcomes before claiming implementation complete; planning checks are not acceptance-test results.

