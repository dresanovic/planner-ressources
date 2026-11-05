# Quickstart and Validation Guide - I-006

This is a later implementation acceptance guide, not passing evidence. Do not run trials against backend/planner.db or user backups. Use an isolated SQLite file/volume with seeded representative data and an authorized test planner. Tests precede production changes under TR-001.

## Environment

Use Python3.12 and backend/.venv (global Anaconda had incompatible optional NumPy extension warnings during inspection). Use Node24 as CI/Docker do; local Node27 alpha is not the acceptance environment. Install existing requirements/package-lock dependencies only. From backend, activate the venv and use its python. Windows equivalent: ./.venv/Scripts/python.exe. From client: npm ci when dependencies are not already installed.

Before production implementation, obtain plan/task approval and use an isolated codex/ branch/worktree containing these approved artifacts. This planning Goal does not create a branch or authorize implementation/Git delivery.

## Configuration trial

Set TEACHING_OPTIMIZATION_POLICY_FILE to an operator-owned JSON file, located beneath a read-only directory bind mount if deployed: host ./config/optimization -> container /config/optimization, with TEACHING_OPTIMIZATION_POLICY_FILE=/config/optimization/policy.json. Do not mount the individual file. Example content: {"defaultSeconds":300,"ceilingSeconds":1800}. Unset path or missing keys uses shipped values. Supplied invalid/missing/unreadable file blocks new generation, not unrelated routes. Atomically replace policy.json inside the host directory when editing; directory mounting exposes the new file to the live container. Do not edit the container copy or restart it for this trial. No UI editor or per-run override.

While the container and operation A remain running with300 seconds, atomically replace policy.json on the host with default600/ceiling1200. Operation A retains300; next preparation/start shows/uses600. If policy changes between preview/start, receive BUDGET_POLICY_CHANGED and re-prepare before starting. Test nonpositive, fractional, bool/string, NaN/infinity, malformed JSON, unknown keys and default>ceiling; no clamping. Both values may exceed shipped settings when operator-configured consistently.

## Automated checks

Commands below run from backend using its activated venv. Add deterministic failing tests first, observe intended failure, then implement.

    python -m pytest tests/db/test_migrations.py tests/services/test_optimization_config.py tests/services/test_optimization_operations.py tests/services/test_optimization_worker.py tests/api/test_optimization_operations.py
    python -m pytest tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation_concurrency.py tests/api/test_conflict_aware_generation.py
    python -m pytest tests/services/test_schedule_lifecycle.py tests/services/test_schedule_lifecycle_concurrency.py tests/api/test_schedule_lifecycle.py tests/services/test_exam_optimization.py tests/api/test_multi_course_generation.py tests/api/test_planner_authorization.py tests/services/test_draft_schedule_validation.py
    python -m pytest tests/performance/test_semester_optimization_performance.py
    python -m pytest

Use file-backed SQLite and independent sessions/barriers for accept/accept, cancel/accept, cancel/finalize, publication/apply and worker-failure/commit races. Existing optimization/planner-auth/lifecycle fixtures are reusable. Tests must verify complete before/after saved-state preservation, not just HTTP status. Fresh/current/older schema upgrades and partial-schema rejection need migration tests. No DB transaction spans search/review.

From client under Node24:

    npm run test -- src/api/conflictAwareGeneration.test.ts src/api/plannerFetch.test.ts src/hooks/useOptimizationOperation.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/components/ReplacementConfirmationDialog.test.tsx src/components/BatchResultSummary.test.tsx src/App.test.tsx src/PlannerApplication.test.tsx
    npm run lint
    npm run test
    npm run build

Build runs tsc -b and Vite; no separate TypeScript script exists. API/client fixture tests must agree with contracts/optimization-operation.md and D1–D11. Retain I-003/I-004/FS-013/auth/manual/exam/publication and existing cohort-filter/selection regression coverage.

Supersede old universal30/60-second completion assertions, <=55-second reserve expectation, blanket unproven503 and solve-again acceptance. Keep reference workload timing measurements and hard-rule/transaction safeguards.

Container/deployment commands from repository root, using an isolated local image/test volume:

    docker build --file infrastructure/docker/Dockerfile --tag planner-i006:validation .

Start that image with the isolated database volume, required existing auth/lecturer-review deployment configuration, mounted policy and HTTPS termination per infrastructure/docker/README.md. Do not repoint the normal production compose volume. Verify one app/Uvicorn process, health responsiveness, child stop/reaping and restart behavior. Exercise Windows spawn and Linux container execution; no extra solver/database packages should be introduced.

## Deterministic outcome matrix

| Case | Expected result |
|---|---|
| Feasible-only timeout: courses40/60, candidate32/48 | Review80/100/20 and32/40/8,48/60/12; unsaved; whole-selection accept/cancel |
| Same candidate, sound coverage bound90 |20 remaining, at most10 additional, no promise90 achievable |
| Missing/nonfinite/contradictory/wrong-stage/snapshot bound | Explicit unknown, no invented gap/percentage |
| Total coverage optimum80/100 proven; preference timeout | Coverage proven,20 remaining, later proof unfinished/not attempted |
|100/100 but preference incomplete | Complete coverage, unproven preferences; explicit acceptance |
| Later stage UNKNOWN, earlier decoded hard-valid candidate | Earlier exact assignment eligible; correctly bound evidence |
| Conditional supplied evidence | Fixed earlier values stated; never full-priority proof |
| No assignment/invalid/unchecked/all-zero unproven result | No acceptance; zero saved change; timeout versus actual fault distinguished |
| One zero-unit course in nonempty joint candidate | Course remains in joint comparison; accept may clear its old sessions without creating an empty draft |
| Fully proven, all unplanned | Automatic live finalize after fresh validation; no additional user click |
| Fully proven, existing sessions | Existing I-004 comparison and explicit acceptance |
| Lower coverage/manual/warned current work | Disclosure and allowed operation-wide choice; cancel preserves warned work |\n| Current courses required/scheduled40/50 and60/40 | Per-course remaining0 and20; selection required100/scheduled90/remaining10 using established aggregate subtraction; all course facts visible, excess does not fulfill another course or prove optimality |
| Retry confirm/back | Explain discard/current budget/no resume/worse possible; Back retains exact review; confirmed retry invalidates old first |

Test hard-rule invalidation independently: dates/semester/study windows, session size/units/breaks/totals, holidays/unavailable dates, eligibility/activity/capacity/availability, selected joint and fixed teaching/exam conflicts, same-course exam boundary. Test relevant changes in every FR-019 category cause whole stale rejection even if still feasible; ignored past-exam/unrelated changes alone do not. Include revision publication/abandonment/new Working state.

## Interruption and concurrency matrix

- Cancel preparing/optimizing/checking/review; late child/API responses must not save/reopen.
- Close running surface; change semester/revision/app area; App's hidden persistent page must not revive review.
- Refresh, pagehide, network loss, reconnect, logout/401/session replacement/revocation, server restart/shutdown, child failure.
- No worker ever saves. Lost start response reconciles same ID. Lost accept/finalize response observes receipt; do not falsely state cancelled/unsaved. Receipt after commit is saved even if cancellation arrived later.
- Before-commit registered cancel prevents apply; after-commit cancel reports saved. Repeated accept/finalize/start creates no duplicates.
- Partial selected-course save failure rolls back all; unrelated data remains equal. Failure after commit/response delivery does not overwrite saved receipt.
- Status polling is passive and does not renew auth inactivity. Live action authority checks both current originating session row ID and existing secret digest, freshly at apply. Deliberately delete/relogin the same account with a reused numeric session ID but different secret digest: old context must not review/accept/finalize or replay a start. The current owner session may still read outcome-only status or cancel abandoned work. Other accounts/public lecturer cannot read or act.
- Review remains usable indefinitely while context/inputs unchanged. Refresh/reconnection must not restore actionable review from operation ID or secret storage.

## Real-time and human acceptance evidence

Create validation/acceptance.md during implementation validation, recording dates, commit/worktree state, versions/hardware, isolated dataset, selected courses/units/fixed occupancy, policy/effective budget, wall and monotonic durations, phases/status timestamps, health timings, candidate/proof/bounds and final saved outcome.

1. Controlled real search/workload runs beyond60 seconds with a300-second budget; no inherited service/proxy/client cutoff. A mocked clock/sleep alone is insufficient evidence of usable long optimization.
2. Record connected status gaps <=5 seconds and visible start/cancel acknowledgments <=1 second under stated connected conditions, including health responsiveness during model/search. Checking after allowance exhaustion is visibly distinct.
3. Representative2027 S-style larger selection within20 courses; record honest candidate/no-candidate/failure and preservation outcome, not a universal feasible-course threshold or guaranteed optimum.
4. Keyboard-only/focus trap/restoration, programmatic course/column associations, phase/terminal announcements, no focus steal/color-only meaning;320/820/1280 CSS-pixel widths and200% text zoom with long/twenty-course evidence.
5. At least four of five representative planners/reviewers, unaided within two minutes, identify saved/provisional state, distinguish validity/proof, explain a quality trade-off and make intended decision.
6. Actual external proxy/HTTPS and container interruption/restart trials on isolated data. Keep unmet evidence explicitly pending; do not infer assistive/manual success from green unit tests.

No production code or test result is generated by this guide.
