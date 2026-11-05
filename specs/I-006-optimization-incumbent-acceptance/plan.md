# Implementation Plan: I-006 - Configurable Optimization Time and Valid Incumbent Acceptance

**Working Branch**: master (planning artifacts only) | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Approved specification in specs/I-006-optimization-incumbent-acceptance. User approval in this chat: “Approve the current I-006 specification and proceed with Goal 2.” Implementation requires separate plan/task approval.

## Summary

Give the unified teaching-generation workflow an operator-configured time allowance, responsive running status, and explicit acceptance of exact hard-valid timeout candidates. Preserve objective priorities, the twenty-course limit, protected occupancy, Working revision rules, and whole-selection atomic decisions.

Use short authenticated HTTP requests, a feature-specific parent coordinator and a standard-library spawned solver process. The solver receives immutable inputs and cannot write the database. Retain the exact candidate in the live operation context; acceptance validates and applies it without another solve. A minimal durable operation receipt proves actual outcomes after interrupted responses. For fully proven wholly unplanned selections, the live client automatically finalizes with no new human decision; otherwise reuse I-004 comparison.

## Technical Context

**Language/Version**: Python 3.12 (container 3.12.16; backend venv 3.12.8), TypeScript ~6.0.2; Node 24 acceptance target.
**Primary Dependencies**: existing FastAPI 0.139.0, SQLAlchemy 2.0.45, OR-Tools 9.15.6755, React ^19.2.7, Vite ^8.1.1, Vitest ^4.0.16. No new package dependency.
**Storage**: existing SQLite; one optimization_operations technical receipt table, migration 0011, and schema-state detection. Provisional sessions remain outside Working data.
**Testing**: backend venv pytest, existing API/service/file-backed concurrency fixtures; Vitest, ESLint, TypeScript/Vite build; manual assistive and real-time evidence.
**Target Platform**: existing single Uvicorn process/container; Windows development/Linux deployment; explicitly test spawn on both.
**Project Type**: existing full-stack web application.
**Performance Goals**: 300-second shipped allowance, initial configurable 1800-second ceiling; one preparation/search deadline; connected updates <=5 seconds apart; visible start/cancel acknowledgment <=1 second. Checking may finish after search ends.
**Constraints**: unchanged scheduling rules/priorities; no per-run budget control, solver resume, automatic batching, new role/editor, guaranteed optimum or completion time.
**Scale/Scope**: 1–20 selected courses in one editable semester revision. No new feasible-course-count guarantee. Backend/API/client/operator documentation affected.

## Constitution Check

| Gate | Before research | After design |
|---|---|---|
| I Spec first | Approved bounded specification present | Specification unchanged; design derives from FR-001–029 |
| II Test first | TR-001–009 require test-first delivery | Story tests precede their production tasks; manual exceptions below |
| III Acceptance | Five Given/When/Then stories; SC-001–010 | Validation guide covers positive, negative, concurrency and interruption branches |
| IV KISS | Reuse existing stack/rules/comparison | Process, receipt and validator justified below; no broker/framework |
| V Verified workflow | Existing master; documentation work only | No clean-master production exception claimed; later implementation must use an isolated codex/ branch/worktree carrying approved artifacts |
| VI Incremental delivery | US1–4 P1, US5 P2 | Story increments; shared setup limited to required schemas/contracts |
| Technology/boundaries | FastAPI and React/TypeScript/Vite | Existing backend/app, backend/tests and client boundaries retained; cross-stack contract written |
| Verification | Existing commands inspected | Concrete commands in quickstart and verification tasks; no implementation success claimed |

No constitution exception is requested. A feature branch/worktree is a prerequisite for later implementation; this Goal performs no Git mutation.

## Simplicity Check

1. **Simplest viable solution**: extend current service/UI, adding one operation coordinator, solver-only process entry point, policy reader and receipt model. Use fetch polling. Reuse snapshot loaders, predicates, warning comparison, save/revision claims and fixtures.
2. **Necessary abstractions**: detached solver input/result avoids ORM/session sharing; exact-candidate validation independently proves hard validity; operation context owns deadline/cancellation/candidate/idempotence; one client feature hook controls asynchronous lifetimes and late navigation responses. These directly satisfy FR-005/006/009/019–023.
3. **Deliberately excluded**: Celery/Redis, distributed jobs, generic job repositories/transports, solver replacement or parallel-search tuning, planner decision history, reviewer roles, automatic retries/resume, per-course salvage and planner budget controls.

## Design

### Budget and execution

Read optional operator JSON from TEACHING_OPTIMIZATION_POLICY_FILE on preparation/start. Keys: defaultSeconds and ceilingSeconds; missing keys use 300/1800. Unset path uses defaults. A supplied missing/unreadable/malformed file or invalid value blocks new generation with actionable diagnostics, without crashing unrelated startup or silent clamping. Require finite positive whole numbers, excluding bool/string/NaN/infinity, and default <= ceiling; no immutable ceiling.

Mount the policy's containing directory read-only (for example host ./config/optimization to container /config/optimization), and point TEACHING_OPTIMIZATION_POLICY_FILE to /config/optimization/policy.json. Do not bind-mount the individual file: host atomic replacement can leave a file bind mount reading the old inode. Operators atomically replace policy.json inside the host directory while the container and existing operation continue running, without rebuilding/restarting. Preparation exposes effective values and fingerprint before start. A changed fingerprint at start returns BUDGET_POLICY_CHANGED and requires re-preparation. Capture values once at successful start; subsequent policy edits do not affect that operation.

Start captures one monotonic deadline before background preparation. Parent loads/copies planning inputs in its own short SQLAlchemy session and closes the transaction. Child enumerates/builds/searches within the remaining allowance. Parent watches deadline, cancellation and child health. Use pipe/event control, cooperative stop followed by terminate/reap fallback. Checkpoint complete decoded assignments so later UNKNOWN or forced stop does not erase earlier received work. At exhaustion stop new search; checking/delivery may finish afterward. No database transaction spans search or review.

Create receipt/context before dispatch; dispatch failure produces a non-saving failure receipt. Repeated start identity never launches a second worker. Concurrent operations have independent snapshots/deadlines/children; serialize only final database mutation, with no hidden queue changing the time allowance.

### Candidate and evidence

Preserve seed/single search worker and priority order: total_units, conflicts, schedule_shape, lecturer_changes, room_changes, retained_drafts, canonical_temporal, canonical_resource. Stop at the first unproven objective; later objectives are not_attempted. Decode only FEASIBLE/OPTIMAL; UNKNOWN provides no assignment. Preserve earlier complete candidates and their evidence for the same prepared problem. MODEL_INVALID/unexpected runtime failures remain failures.

Before review and immediately before application, independently validate every course/session against all FR-009 rules. Existing _exact_sessions_valid covers only occupancy overlap and is insufficient. Reuse shared teaching/resource/overlap predicates and validate dates/windows, units/session size/duration/breaks, totals, holidays/unavailable dates, resource activity/eligibility/availability/capacity, same-course exam boundaries, selected-to-selected and fixed teaching/active-exam conflicts. Invalid/incomplete assignments are never offered.

An entirely empty unproven timeout result follows no-candidate recovery. Individual zero-unit courses remain in a nonempty joint decision. Any incomplete proof requires explicit review, even first plans/full coverage. Fully proven results with existing sessions still require I-004 comparison.

Only total_units evidence for the identical prepared problem supplies a unit bound. Reject non-finite, contradictory, wrong-stage/snapshot evidence; conservatively round a sound bound upward for integer units, then tighten to required total. Proven maximum coverage sets zero coverage gap even if preferences are unproven. Never invent evidence from required-unit arithmetic. Review and saved outcomes preserve scoped proof, coverage and uncertainty.

### Application and cancellation

Keep the exact immutable candidate in server memory. Fully proven wholly unplanned results enter ready_to_save; the live browser automatically POSTs finalize, without a new click. Worker never saves. Other results require explicit accept. Neither path reruns solving.

For application, claim the existing semester/Working revision mutation boundary, reload/compare relevant fingerprints, revalidate exact sessions and apply all selected results. Receipt-state CAS, schedule replacement/creation/deletion, planning outcome retention and saved receipt commit in the same transaction. Repetition returns the saved receipt. Failed application rolls back the entire selection; mark non-saving failure only after rollback is established, never overwrite saved.

Cancel serializes against the same operation/semester boundary but remains possible after revision publication/abandonment; discarding requires no active-editability gate. Registered cancel before apply commit wins; cancel after commit returns actual saved receipt. “Cancellation requested” is distinct from confirmed cancellation. No partial salvage.

### Context, interruption and security

Owner is the authenticated planner account. Bind the originating authentication session using both its row ID and the existing PlannerSession.secret_digest, derived server-side; a numeric row ID alone may be reused after delete/relogin. Persist this digest as originatingSessionSecretDigest, not the raw credential, and never expose it in status JSON or logs. Compare the current authenticated session digest for start replay and every live review/accept/finalize, including fresh comparison inside the apply transaction. Each live operation has an opaque secret held only in browser/server memory; receipt stores its digest, never raw secret. Require current owner/originating-session-digest authorization and context secret for actionable review/accept/finalize. Owner-authorized outcome reads and cancellation are deliberate exceptions: a current session of the same owner may observe outcomes or discard abandoned work after reauthentication, without the old session binding/context secret; it cannot restore review or initiate application. Do not log secrets or put them in URLs. Passive status polling omits deliberate-user-activity headers.

Navigation, running-surface closure, dismissal, auth loss and pagehide invalidate client epoch and send cancellation. Fetch abort alone is insufficient. Pagehide is best effort; abrupt interruption follows receipt reconciliation. After refresh/reconnection, only an operation ID may survive for outcome-only observation; no actionable review/secret is restored. Unconfirmed transport switches to unknown/reconciliation and invalidates action authority.

Continuous review has no fixed expiry while context/inputs remain unchanged. Startup/shutdown invalidates unfinished contexts, stops/reaps children and never resumes search/review. Child exits on parent control-channel loss. Startup preserves committed saved receipts and marks other unfinished operations interrupted after DB recovery. Session revocation or replacement prevents apply even if SQLite reuses the previous numeric session row ID; child has no DB authority.

Keep compact terminal receipts/tombstones for deduplication/reconciliation, deleting heavy provisional materials on discard. These are technical execution metadata, not a new permanent planner decision log, review history UI or mandatory justification.

### Client and fresh retry

A new feature hook, client/src/hooks/useOptimizationOperation.ts, owns operation ID/secret/epoch, non-overlapping two-second polls, cancellation teardown and unknown-outcome reconciliation. Show actual budget/elapsed/phase, not solution percentage or finish estimate. Local elapsed ticking never fabricates server progress. Visible acknowledgment <=1 second can precede durable confirmation. Announce phase/terminal changes without repeated elapsed announcements or focus stealing.

Extend existing comparison with scope, proof, coverage, reasons/unknown evidence, quality trade-offs, manual replacement and unplanned creation wording. Preserve exact decisions and I-004 focus behavior. Update BatchResultSummary so consciously accepted unproven results are truthfully saved.

Separate fresh-retry confirmation explains discard, current policy, fresh saved inputs, no resume and possible worse/no result. Back returns to unchanged review. Confirmed retry durably discards old candidate before preparing/starting a new identity. Never retry blindly while apply outcome is unknown.

## Project Structure

Feature artifacts: plan.md, research.md, data-model.md, contracts/optimization-operation.md, quickstart.md and tasks.md. goal-progress.md contains process continuity only.

Later production paths:
- backend/app/services/optimization_config.py (new policy reader)
- backend/app/services/optimization_operations.py (new operation coordinator)
- backend/app/services/optimization_worker.py (new spawn-safe solver entry)
- backend/app/services/conflict_aware_generation.py (prepare, exact validation, compare/apply)
- backend/app/services/semester_optimization.py (deadlines, incumbents and evidence)
- backend/app/schemas/conflict_aware_generation.py and backend/app/api/conflict_aware_generation.py
- backend/app/models/planning.py, backend/app/db/migrations/0011_optimization_operations.py, backend/app/db/schema.py
- backend/app/main.py (lifespan cleanup)
- backend/tests/api, backend/tests/services, backend/tests/db, backend/tests/performance
- client/src/api/conflictAwareGeneration.ts; client/src/hooks/useOptimizationOperation.ts
- client/src/pages/CourseSchedulePage.tsx
- client/src/components/MultiCourseGenerationPanel.tsx, ReplacementConfirmationDialog.tsx, BatchResultSummary.tsx
- client/src/App.css; .env.example; compose.yaml; backend/README.md; infrastructure/docker/README.md

Preserve App/PlannerApplication ownership and plannerFetch behavior; verify their lifecycle signals rather than building another navigation/auth layer.

## Complexity Tracking

| New element | Present need | Simpler alternative insufficient because |
|---|---|---|
| Solver process/coordinator | FR-006/022 responsive long-running cancellation | Synchronous request lacks independent cancel; thread-only requires cooperation across native/Python-heavy preparation |
| Receipt table | FR-020/023 actual outcome after lost response/restart | Memory-only loses commit evidence; rerun may change candidate |
| Exact validator | FR-009/010 | Existing overlap-only check omits mandatory rules |
| Feature lifecycle hook | FR-021–023 | Hidden persistent Schedule page and unguarded promises can revive discarded review |

## Verification Plan

Write tests first for policy, migration/schemas, process/deadline, exact validity, incumbent/evidence extraction, API decisions, file-backed races and client lifetimes. Replace superseded 55-second reserve, universal 30/60-second completion, all-unproven-503 and acceptance-reproduction expectations, retaining their hard-rule/atomicity/reference performance coverage.

Concrete commands/scenarios are in [quickstart.md](quickstart.md) and explicit verification tasks. Backend/client JSON fixtures exercise the shared contract. Client build includes TypeScript checking.

Use backend/.venv, not global Anaconda (inspection found incompatible NumPy extension warnings there). Use Node24; local Node27 alpha is outside the npm acceptance environment. No runtime or test success is claimed by this planning phase.

Manual exceptions: assistive announcement quality, visual layouts/zoom, five-reviewer comprehension, real >60-second operation, and external HTTPS/proxy behavior require recorded evidence in validation/acceptance.md. These supplement deterministic automated tests. No test-first exception applies to service/API/UI state logic.
