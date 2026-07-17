# Implementation Plan: FS-010 Conflict-Aware Semester Optimization

**Working Branch**: `codex/fs-010-semester-optimization` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-conflict-aware-semester-optimization/spec.md`

**Note**: Implementation runs on the dedicated `codex/fs-010-semester-optimization` feature branch because this is a large cross-stack scheduling change with a new runtime dependency.

## Summary

Add a planner-triggered semester optimization workflow for 1–20 selected courses that maximizes total scheduled teaching units while respecting existing course, semester, resource, capacity, availability, fixed-occupancy, and unavailable-date rules. A new pure backend optimization service will enumerate canonical temporal/resource choices from the existing planning model and use pinned OR-Tools CP-SAT to prove each lexicographic objective tier: total units, current conflict reduction, lecturer continuity, room continuity, complete-draft preservation, and a stable final ordering. Existing Draft Schedule persistence, revision protection, generation-constraint behavior, validation-alert derivation, and page refresh behavior remain authoritative. The FastAPI orchestration layer will prepare replacement confirmation, solve synchronously within a bounded deadline, revalidate exact planned results against current data, save only still-valid per-course improvements, and return complete/improved-partial/unchanged/failed/stale outcomes with remaining-unit reasons and explicit proof scope. The React planning page will replace the primary independent batch action with conflict-aware optimization while retaining the existing course selection, confirmation, review, and retry patterns.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, Alembic 1.18; React 19, Vite 8, Vitest 4; add pinned `ortools==9.15.6755` for CP-SAT optimization

**Storage**: Existing SQLite database through SQLAlchemy; no schema migration or new persisted optimization entity. Successful results reuse `DraftSchedule`, `DraftSession`, and `GenerationConstraintSet`.

**Testing**: pytest 9 for solver model, candidate generation, orchestration, API, persistence, stale-state, regression, and performance tests; Vitest 4 with jsdom for client API/component/page tests; TypeScript build and ESLint

**Target Platform**: Existing FastAPI service on Python 3.12 and modern desktop browsers used by planner users

**Project Type**: Full-stack web application with synchronous JSON HTTP contracts

**Performance Goals**: For the documented reference workload of up to 20 selected courses, 600 requested units, and 500 fixed sessions, at least 95% of operations return a saved-state result or actionable failure within 30 seconds and all return within 60 seconds. Only a solver result proven optimal at every objective tier may be saved.

**Constraints**: Preserve FS-001 through FS-009 behavior and current records; no fairness allocation, holiday administration, exams, background job system, algorithm selector, silent re-optimization after stale input, or feasible-but-unproven save; canonical input ordering, one solver worker, fixed seed, and pinned solver version support deterministic output; use existing allowed-window start semantics and one course session per date; implementation must remain within signed 64-bit integer model limits

**Scale/Scope**: One planner role; 1–20 distinct selected courses; at most 600 requested teaching units and 500 fixed semester sessions in the accepted reference workload; zero or more caller-supplied unavailable dates; existing independent batch endpoint remains compatible but is no longer the primary optimized action

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The clarified FS-010 spec defines four independently testable stories, 32 functional requirements, ten measurable outcomes, explicit exclusions, and nine recorded decisions.
- **Acceptance criteria — PASS**: Given/When/Then scenarios cover complete and partial optimization, hard conflicts, eligible-resource choice, non-worsening replacement, stale inputs, unavailable dates, deterministic outcomes, summaries, and refresh behavior.
- **Test-first — PASS**: Solver, service, API, client, performance, and regression tests are identified before production work. No automated-test exception is planned.
- **Simplicity and KISS — PASS**: The design adds one focused solver service and one justified scheduling dependency, reusing current ORM entities, revision fields, repository writes, alert derivation, batch confirmation, and page orchestration. No new persistence layer, job queue, operation table, repository framework, or client state library is added.
- **Technology fit — PASS**: FastAPI and React/Vite remain the application boundaries. The additive optimization JSON interface is documented in `contracts/conflict-aware-optimization.openapi.yaml`.
- **Delivery workflow — PASS**: Implementation is isolated on `codex/fs-010-semester-optimization` because the change is large, cross-stack, and customer-facing.
- **Verification before commit — PASS**: Focused and full backend/client commands, deterministic repeat checks, bounded optimality fixtures, and reference workload timing evidence are listed below and in `quickstart.md`.

### Post-design re-check

The Phase 1 design introduces no constitution violation. CP-SAT is justified by the present requirement to prove a global optimum across optional interval and resource assignments; custom backtracking cannot credibly meet the same correctness and workload target with less risk. The solver remains isolated behind domain dataclasses rather than leaking library types into FastAPI, SQLAlchemy, or React. Existing tables remain sufficient, exact planned results are revalidated before per-course atomic replacement, and no background processing or speculative holiday model is introduced. Contracts and validation scenarios cover all cross-stack changes.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Add one synchronous optimization endpoint pair and one pure CP-SAT-backed domain service. Reuse the current preparation/confirmation flow, existing planning input loaders, Draft Schedule replacement repository, validation-alert refresh, and result components. Build one canonical finite candidate model from existing allowed windows, eligible resources, availability, and current semester occupancy; solve and return no persisted optimization record.
2. **Necessary abstractions**: A solver-independent `OptimizationInput`/`OptimizationResult` domain boundary is necessary so solver tests do not require HTTP or ORM state and so current data can be revalidated before persistence. A small candidate/reason builder inside the same optimization module is necessary because temporal/resource candidate derivation and blocking evidence are shared by modeling and result explanation. No generic optimizer interface or repository abstraction is required.
3. **Deliberately excluded**: Custom backtracking, multiple solver implementations, plugin architecture, background jobs, polling, operation-history tables, event sourcing, distributed locks, resource-ranking configuration, fairness weights, holiday CRUD, exams, manual-session pinning beyond current whole-draft replacement, arbitrary start-time grids, automatic stale-input re-optimization, and client state-management dependencies.

Implementation MUST NOT begin until all three answers remain consistent with the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/010-conflict-aware-semester-optimization/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- conflict-aware-optimization.openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                      # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- requirements.txt                              # pinned OR-Tools runtime
|-- app/
|   |-- api/
|   |   `-- conflict_aware_generation.py          # prepare/optimize HTTP boundary
|   |-- schemas/
|   |   `-- conflict_aware_generation.py          # request/result/reason contracts
|   `-- services/
|       |-- semester_optimization.py              # domain inputs, candidates, CP-SAT model
|       |-- conflict_aware_generation.py          # load, snapshot, solve, revalidate, save
|       |-- draft_schedule_repository.py          # reuse atomic whole-draft replacement
|       |-- resource_rules.py                     # reuse availability/overlap semantics
|       `-- draft_schedule_validation.py          # reuse post-save alert derivation
`-- tests/
    |-- api/
    |   `-- test_conflict_aware_generation.py
    |-- services/
    |   |-- test_semester_optimization.py
    |   `-- test_conflict_aware_generation.py
    `-- performance/
        `-- test_semester_optimization_performance.py

client/
|-- src/
|   |-- api/
|   |   |-- conflictAwareGeneration.ts
|   |   `-- conflictAwareGeneration.test.ts
|   |-- components/
|   |   |-- MultiCourseGenerationPanel.tsx        # optimized action and 20-course bound
|   |   |-- ReplacementConfirmationDialog.tsx     # reuse replacement confirmation
|   |   |-- BatchResultSummary.tsx                # five outcomes, units, reasons
|   |   `-- *.test.tsx
|   `-- pages/
|       |-- CourseSchedulePage.tsx                # orchestration and semester refresh
|       `-- CourseSchedulePage.test.tsx
`-- package.json
```

**Structure Decision**: Retain the current backend/client split. Keep pure model construction and solving in `semester_optimization.py`; keep ORM loading, preparation snapshots, stale validation, and persistence in a separate feature service because those concerns already have transactional behavior independent from mathematical solving. Add a dedicated API/schema pair rather than changing the existing FS-006 batch contract, preserving backward compatibility and making optimized outcome semantics explicit. Extend existing React planning and result components rather than create a new route or workspace.

**Agent Context Update**: This Spec Kit installation has no `update-agent-context.ps1` script. The required script location was checked; no substitute context file will be invented.

## Design Decisions

### Candidate and constraint model

- Canonically sort all courses, dates, windows, resources, current sessions, and unavailable dates. Convert semester-local date/time values to integer minutes from semester start for CP-SAT.
- Generate temporal candidates at the established allowed-window start time for every valid date and session-unit size from the course minimum through maximum. Deduplicate equivalent date/time/unit candidates and enforce at most one selected session per course/date and total selected units no greater than the current course total.
- Give each chosen temporal candidate exactly one active eligible available lecturer and one active eligible available capacity-sufficient room. Use optional fixed-size intervals and `NoOverlap` by lecturer, room, and cohort for newly generated candidates. Pre-eliminate choices conflicting with unselected fixed sessions or caller-supplied unavailable dates.
- Represent each current selected-course draft as a whole retained alternative. Retaining it excludes regenerated candidates for that course. Existing conflicts in retained data remain countable baselines; new candidates may not overlap retained current sessions. A generated alternative must schedule at least the actual sum of units in the current draft. When that sum exceeds the current course total, no generated alternative can qualify and the complete current draft remains unchanged.

### Objective and solver outcome

- Solve lexicographically in separate objective stages, locking each proven optimum before advancing: maximize scheduled units; minimize distinct retained conflict relationships by session pair and conflict type; minimize adjacent lecturer changes; minimize adjacent room changes; maximize completely preserved current drafts; minimize canonical stable rank.
- Reuse each stage's solution as the next stage's hint and enforce one overall solver deadline. Configure one search worker, fixed random seed, canonical model construction, and pinned OR-Tools version. Record solver status and timing for diagnostics without persisting a domain operation.
- Save only when every required stage returns `OPTIMAL` for the prepared snapshot. `FEASIBLE`, `UNKNOWN`, `MODEL_INVALID`, or deadline exhaustion returns an actionable operation failure and saves nothing. `INFEASIBLE` on a model that always contains retain/zero alternatives is treated as a model/input defect and saves nothing.
- Final stable rank prefers canonical earlier dates/times and normalized lecturer/room codes with stable IDs as final keys. Any remaining solver-level tie is resolved by the deterministic single-worker configuration and canonical variable order.

### Partial results and explanations

- Permit generated alternatives with zero through total course units, respecting valid session sizes. Do not create empty Draft Schedules. A no-draft zero result and every non-improving current result are `unchanged`.
- Derive scheduled and remaining units from the exact saved Draft Sessions. Classify results as `complete`, `improved_partial`, `unchanged`, `failed`, or `stale`.
- Accumulate blocking evidence during candidate construction and final validation using stable categories: occupied lecturer, occupied room, occupied cohort, lecturer unavailable, room unavailable, no eligible lecturer, no eligible room, insufficient room capacity, unavailable date, planning/date window, course constraint, selected-course competition, invalid input, and stale input. Explanations report substantiated categories, not a unique-cause proof.

### Preparation, stale validation, and persistence

- `prepare` loads the complete selected-semester planning boundary, canonically deduplicates unavailable dates, and returns replacement targets and opaque canonical snapshot fingerprints for each selected course plus shared semester occupancy. The client echoes the canonical preparation in the confirmed optimize request.
- Before solve, reload and compare preparation identity/revisions. After solve and before writes, reload current data again. Preserve a changed course and validate each exact unaffected planned result against refreshed resource rules, occupancy, and retained stale-course data. Never silently solve again.
- Save each still-valid improving course within a nested transaction using the existing whole-draft replacement path. Preserve every existing custom Generation Constraint Set unchanged; when a successfully generated course had no saved set, save the exact active defaults used by the result through the established generation-constraint path. Failed, stale, unchanged, and cancelled outcomes do not change constraints or source academic/resource records. A per-course write failure rolls back that course. Any exact unaffected result invalidated by refreshed data becomes stale/failed and remains unchanged. Commit the combined operation once orchestration is complete.
- When post-solve stale input exists, report that the solver proved optimality for the prepared snapshot only. Exact unaffected results may save after current-state validation, but the response must not describe the refreshed final semester state as globally optimal.
- Recompute the final response from saved state and reload the semester overview on the client so remaining units and validation alerts cannot reflect speculative solver state.

### API and client

- Add `/api/draft-schedules/optimization/prepare` and `/api/draft-schedules/optimization/generate`. Requests use one semester, 1–20 distinct course IDs, zero or more unavailable-date values that are canonically deduplicated, explicit replacement confirmation, and preparation snapshots.
- Keep the synchronous request model; the 60-second contract does not justify a background queue. Provide an in-progress state, prevent duplicate submission, keep selection visible, and expose actionable request/solver failures.
- Reuse the existing multi-course picker but cap optimized selection at 20 and label the action “Optimize selected courses.” Reuse replacement confirmation with explicit affected courses/manual edits. Expand the batch summary to show all five classifications, scheduled/remaining units, improvements, and reason categories; retry targets failed/stale courses through a fresh preparation.

## Complexity Tracking

No constitution violations require justification. The one new runtime dependency and focused solver boundary are justified above by the current global-optimality requirement and are not speculative abstractions.

## Verification Plan

Write failing tests before production behavior. Run backend commands from `backend/` and client commands from `client/`.

```text
python -m pytest tests/services/test_semester_optimization.py
python -m pytest tests/services/test_conflict_aware_generation.py tests/api/test_conflict_aware_generation.py
python -m pytest tests/performance/test_semester_optimization_performance.py
python -m pytest
npm test -- conflictAwareGeneration MultiCourseGenerationPanel BatchResultSummary CourseSchedulePage
npm test
npm run lint
npm run build
```

Verification evidence must include independently established small optimal totals, a request-order counterexample, all hard constraint families, current-conflict counting, lecturer/room transition metrics, complete-draft preservation, repeated deterministic output (20 runs), complete and partial results, zero placement, actual-unit non-worsening including over-scheduled current drafts, equal-unit replacement, confirmation cancellation, every material stale-input category, prepared-snapshot proof reporting, unaffected exact-result saving without re-optimization, generation-constraint/source-record preservation, rollback behavior, unavailable-date deduplication, blocking reasons, refreshed alerts, the SC-006/SC-007 usability protocol, and FS-001 through FS-009 regressions. The performance fixture must document hardware and dataset construction for 20 selected courses, 600 requested units, and 500 fixed sessions, then record 30/60-second acceptance results under this feature directory.

## Implementation audit (2026-07-17)

The implementation retains the backend/client split, adds only the pinned OR-Tools runtime, introduces no schema migration, and leaves FS-006 routes intact. Contract names and five outcome semantics match the OpenAPI artifact. The solver boundary contains finite candidates, hard availability/eligibility/capacity/occupancy rules, lexicographic proof stages, fixed seed/single worker, and `OPTIMAL`-only extraction. The orchestration boundary owns canonical snapshots, confirmation, pre/post-solve stale checks, exact unaffected validation, nested whole-draft saves, default/custom constraint preservation, and final-state outcomes. The client exposes the 1-20 bound, unavailable dates, confirmation, five-status summary, proof scope, refresh, and fresh failed/stale retry.

Automated constitution/simplicity/scope checks pass: no background queue, algorithm selector, fairness weighting, holiday/exam behavior, automatic unselected movement/deletion, persisted optimization operation, or unrelated academic/resource mutation was added. Full backend/client regression, lint, build, deterministic, and performance evidence is stored under `validation/`.

The final acceptance audit remains open only for T068: the constitutionally specified SC-006/SC-007 study needs ten representative human reviewers. The repository contains the protocol and recording template, and no synthetic human evidence is claimed.
