# Implementation Plan: Policy-Selected Teaching Planning Strategies (I-011)

**Working Branch**: `codex/021-dated-intensive-windows` (existing branch preserved) | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: `specs/I-011-policy-teaching-strategies/spec.md`. Human approval: “Approve I-011 specification and proceed with Goal 2”, 2026-11-09; SHA256 `A6F4078949894D3870C5AB970635567C370CCEE6EC9D1B8839607FEC4DDEDF51`. Directory renamed at user's request without changing spec bytes. Setup script's feature-derived BRANCH is not the actual Git branch.

**Note**: Filled by `$speckit-plan`; its skill definition describes the workflow.
This project override retains the mandatory Simplicity Check and Verification Plan.
Read `.specify/memory/constitution.md` for all engineering rules and exceptions.

## Summary

Keep CP-SAT as Standard; add genuine Cohort and Lecturer constructive searches with bounded repair through a small Strategy contract. Reuse existing detached worker, candidate legality, exact validation and atomic acceptance. Freeze policy and code-ordered Lecturer portions per run. Add a heuristic objective profile without changing Standard's objective order. All five P1 stories are required for delivery.

## Technical Context

**Language/Version**: existing Python 3.12 backend; TypeScript 6.0/Node 24 client toolchain.
**Primary Dependencies**: existing FastAPI/Pydantic, SQLAlchemy/Alembic, OR-Tools 9.15; React 19, Vite 8, Vitest 4. No new dependencies/upgrades.
**Storage**: SQLite operation receipts; one additive migration for captured algorithm/profile/settings. Candidate/portion ledgers remain memory-only. No catalog allocation or room fields.
**Testing**: pytest, Vitest component/API/hook tests, TypeScript, lint and Vite build; isolated real worker/deadline comparisons.
**Target Platform**: existing Windows/local backend, Linux container and responsive browsers; institution-local calendar semantics.
**Project Type**: full-stack web slice.
**Performance Goals**: 1–20 selected courses; connected Start/cancel <=1s and status/checkpoints <=5s apart. Captured deadline covers every search phase; no universal speed/quality gain promised.
**Constraints**: strict policy, German operator/UI feedback, immutable operation, active Working revision, independent validity, atomic save and protected publications. Repair <=1000 attempted alternatives/run, <=8 displaced provisional sessions/attempt.
**Scale/Scope**: existing prepare/progress/comparison/results UI and APIs, three concrete strategies. Exams unchanged. No I-007/008/010 administration or live database validation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Before Phase 0 | After Phase 1 |
|---|---|---|
| I Spec first | PASS approved spec identified above | PASS FR-001–026 preserved, no spec edit |
| II Test first | PASS TR-001–010 require tests | PASS failing tests before code/migration/contracts; manual exception below |
| III Acceptance | PASS five Given/When/Then stories | PASS concrete fixtures and SC-001–010 validation |
| IV KISS | PASS three algorithms earn Strategy | PASS static registry, shared primitives, no new framework/service |
| V Verified delivery | PASS existing feature branch | PASS record dirty baseline before implementation; concrete checks before any separately approved commit |
| VI Incremental | PASS vertical story outcomes | PASS setup → US1 → US2 → US3 → US4 → US5; validity/review gate accompanies first heuristic |
| Technology/contracts | PASS existing boundaries | PASS FastAPI/React/TypeScript/Vite, cross-stack contract before code |

No constitution exception or unresolved technical clarification. Implementation requires plan/task approval and human-started Goal 3. Existing dirty production/test files belong to prior work and must be recorded and preserved.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: thin Standard adapter, two concrete owner-specific strategies calling shared bounded construction/repair and score helpers, existing worker and UI.
2. **Necessary abstractions**: static Strategy contract/registry (FR-001); reversible demand/occupancy state shared by two heuristics (FR-011); heuristic objective profile because Standard evidence differs. No generalized allocation engine.
3. **Deliberately excluded**: dynamic plugins, automatic fallback/portfolios, queues/services, planner selector/editor, permanent-room catalog, allocation UI, solver rewrite, new dependencies and protected-booking repair.

Implementation MUST NOT begin until all three answers are complete and consistent
with the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/I-011-policy-teaching-strategies/
|-- plan.md              # $speckit-plan
|-- research.md          # Phase 0
|-- data-model.md        # Phase 1, if applicable
|-- quickstart.md        # Phase 1
|-- contracts/           # Phase 1, if applicable
`-- tasks.md             # $speckit-tasks; not created by $speckit-plan
```

### Source Code (repository root)

```text
backend/app/             # FastAPI production code
backend/tests/           # pytest tests
client/src/              # React/TypeScript code and colocated tests
```

**Structure Decision**: retain current boundaries. Existing backend paths: `backend/app/services/optimization_config.py`, `optimization_operations.py`, `optimization_worker.py`, `conflict_aware_generation.py`, `semester_optimization.py`, `schedule_generation.py`; schemas/API in `backend/app/{schemas,api}/conflict_aware_generation.py`; model `backend/app/models/planning.py`, schema `backend/app/db/schema.py`, new migration `backend/app/db/migrations/0015_teaching_strategy_identity.py`.

New focused modules: `backend/app/services/teaching_strategies.py` (protocol/three classes/static registry); `heuristic_teaching.py` (construction/scarcity/occupancy/undo/repair); `teaching_preferences.py` (week/score and independent portion helpers). No new layer/service boundary. Reuse temporal legality/intensive helpers without changing Standard tie order.

Client: `client/src/api/conflictAwareGeneration.ts`, `hooks/useOptimizationOperation.ts`, `components/MultiCourseGenerationPanel.tsx`, `BatchResultSummary.tsx`, `ReplacementConfirmationDialog.tsx`, `OptimizationProofFacts.tsx`, `pages/CourseSchedulePage.tsx`, colocated tests and `client/src/test/optimizationFixtures.ts`.

Tests: existing config/worker/operations/semester/exam/migration suites plus new `backend/tests/services/test_teaching_strategies.py`, `test_heuristic_teaching.py`, `test_teaching_preferences.py`, `backend/tests/api/test_teaching_strategy_contracts.py`, `backend/tests/fixtures/teaching_strategies.py`, `backend/tests/fixtures/teaching_strategy_contracts.json`, `backend/tests/performance/test_teaching_strategy_comparison.py` and `client/src/test/teachingStrategyContracts.json`.

Operator docs/config: `backend/README.md`, `README.md`, `infrastructure/docker/README.md`, `compose.yaml`, `config/optimization/policy.example.json`. Preserve live policy 900/1800; selector omission already means Standard, so no live edit needed.

## Phase 0: Research

See [research.md](research.md). Current code confirms worker/direct-call integration, strict policy change, fixed Standard proof list and existing normalized-code freshness. Earlier architecture's interchangeable Lecturer assumption is superseded by FR-025/026. No product choice remains delegated to implementation.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contract](contracts/teaching-strategies.md) and [quickstart.md](quickstart.md).

1. Preparation resolves server policy; repeated Start checks existing operation before file access. New Start checks effective fingerprint, freezes context and sets one absolute deadline before loading/enumeration. Worker receives detached values, never ORM/policy reads. Acceptance rechecks planning data, not current policy.
2. Persist algorithm/profile/settings on receipts for identity after restart. Migration backfills historical Standard/legacy settings. Old saved payloads normalize to Standard only; never invent shares. Candidates remain memory-only and restart interrupts unfinished operations.
3. Static registry is the only production teaching placement path. Retire callable synchronous `generate_optimization`/`accept_optimization` with operation-required errors and migrate integration/performance callers. Existing retired HTTP/batch routes stay retired. Pure optimizer remains callable for Standard unit baselines; exams retain their path.
4. Standard passes identical inputs/flags/order to current optimize_semester. Cohort/Lecturer use existing candidate legality across all permitted sizes and a single global occupancy/demand ledger. Selected current sessions are comparison alternatives, not target deductions. Fixed unselected teaching/exams remain protected.
5. Enumerate/deduplicate date/start/size opportunities before tentative competition, excluding resource/source duplicates. Traverse scarcity/groups and evaluate complete provisional scores lexicographically. Consider alternative course start weeks and size redistributions, not a fixed preferred-size split. Maintain construction state separately from immutable best checkpoint; after constructive additions explore deterministic moves/resizes/reinsertions/cross-group swaps. Concrete acceptance fixtures remain mandatory despite bounded heuristic search.
6. Failed repair restores occupancy, course/portion demand, weekly loads, room sets and predecessor state via reversible state. Count every attempted alternative, including failures, across the whole run; <=1000, <=8 displaced sessions each. Never replenish by group. Check deadline/cancel in every date/resource/scoring/repair/rollback/finalization loop. Preserve best hard-valid checkpoint; strict improvements immediately, refresh <=5s while active. Incomplete enumeration never proves infeasibility. Truthful termination distinguishes permitted-neighborhood completion, cap and deadline.
7. Exact rational/scaled-integer preference arithmetic preserves weights 1/2 and half-unit preferences. Week/cadence/owner load/room/ties follow the approved definitions and numeric fixtures verbatim. Reuse actual intensive instruction overlap/variety. Fixed teaching adds load once; exams/breaks add no LE. Common higher priorities always precede lower preferences.
8. Lecturer derives ordered shares once from active eligibility/codes, quotient/remainder and explicit-size precedence. Zero shares do not block; nonzero successors require every predecessor complete and earlier sessions ended. Repair reopening a predecessor removes now-invalid successors. Independent validation reconstructs expected order/targets from authoritative captured inputs, checks actual sessions/shared totals, and checks current code/eligibility/explicit-share freshness. Sorting generated sessions alone is not validation. Cohort/Standard retain existing eligibility semantics.
9. Necessary capacity merges opportunities without shared-time double counting; packing/search failure is uncertainty. Results include every selected course. Whole zero placement has no review/save.
10. Profile-aware proofs/fingerprints bind algorithm/settings/ordered shares with assignments and snapshot. Explicitly set heuristic optimal=False (existing result default is True). Heuristics never prove preferences; full demand equality may prove coverage only. Sound same-snapshot bounds only, unknown otherwise. Every nonempty valid unproven heuristic requires explicit whole-selection accept even before timeout; never auto-finalize. Preserve auth/Working revision/cancel/atomicity and saved-receipt reconciliation.

## Complexity Tracking

> Fill only for constitution exceptions or a new architectural element requiring justification.

| New layer, dependency, pattern, abstraction, or exception | Demonstrated current need | Simpler alternative rejected because |
|---------------------------------------------------------|---------------------------|--------------------------------------|
| Static Strategy | FR-001, three searches | Labels on one solver do not satisfy distinct searches |
| Shared reversible state | Two searches, cross-group repair | Separate ledgers duplicate demand and corrupt rollback |
| Heuristic proof profile | FR-016/017/021 | Fixed Standard keys would mislabel evidence |
| Additive receipt fields | FR-006/008 restart identity | Memory-only facts vanish from terminal status |

## Verification Plan

Write/run failing tests for intended new behavior before code. Capture completed Standard baselines first. From repository root, future Goal 3 commands:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/services/test_optimization_config.py backend/tests/services/test_teaching_preferences.py backend/tests/services/test_teaching_strategies.py backend/tests/services/test_heuristic_teaching.py -q
backend/.venv/Scripts/python.exe -m pytest backend/tests/api/test_teaching_strategy_contracts.py backend/tests/api/test_optimization_operations.py backend/tests/services/test_optimization_operations.py backend/tests/services/test_optimization_worker.py backend/tests/db/test_migrations.py -q
backend/.venv/Scripts/python.exe -m pytest backend/tests/services/test_semester_optimization.py backend/tests/services/test_exam_scheduling.py backend/tests/services/test_exam_optimization.py backend/tests/services/test_dated_intensive_windows.py backend/tests/services/test_intensive_objectives.py backend/tests/services/test_schedule_lifecycle.py -q
backend/.venv/Scripts/python.exe -m pytest backend/tests/performance/test_teaching_strategy_comparison.py -q
npm --prefix client test -- src/api/conflictAwareGeneration.test.ts src/hooks/useOptimizationOperation.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/BatchResultSummary.test.tsx src/components/ReplacementConfirmationDialog.test.tsx src/components/OptimizationProofFacts.test.tsx
npm --prefix client run lint
npm --prefix client run build
```

Contract test consumes backend JSON fixtures and asserts semantic parity with client fixtures; client API test exercises decoding. Validate profiles/identity/invalid states, not only snapshots. Real comparison cases: single, cohort competition, cross-cohort shared lecturer, intensive, partial-week and 20 courses; identical snapshot/budget, record coverage/weekly measures/remaining LE/time/termination/proofs, environment and observed trade-offs. Real spawned budget/cancel/latency/update checks supplement fake clocks; missing performance evidence is not a pass.

Manual exception: actual screen-reader speech, browser narrow/200% zoom layout and real deployment file permissions/mount/atomic replacement cannot be proven by mocks. Automated semantic/focus/config tests still precede code. Record isolated local/deployment smoke and keyboard/AT/browser observations in validation.md; unavailable checks remain acceptance limitations. Never use live data. Built-in quality checklist is not software verification; no custom checklist found, preserve markers. User manual authoring remains Goal 5. No implementation/commit/push/merge is authorized by Goal 2.
