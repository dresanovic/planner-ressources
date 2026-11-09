# Research: I-011

Read-only research used current repository code and approved specification. Fresh research agent `/root/planning_research` inspected existing interfaces independently; this is design input, not the Goal 2 analysis assessment. No unresolved technical question remains.

## Search boundary

Decision: fixed Strategy registry with thin Standard wrapper and concrete Cohort/Lecturer constructive searches sharing legality/undo/score primitives.
Rationale: semester_optimization.py already supplies detached OptimizationCourse/FixedSession/TemporalCandidate, generate_candidates, intensive_arrangement and OptimizationSearchControl. schedule_generation.py supplies duration/window/intensive helpers. Three real searches justify one small interface; existing CP-SAT model need not be rewritten.
Alternatives considered: merely supplying CP-SAT hints/objectives would not deliver the specified constructive algorithms; independent legality engines would drift.

## Policy lifetime and dispatch

Decision: derive normal repository policy from module location, explicit env override wins; strict missing-file errors only on new prepare/Start. Freeze effective algorithm/budget/default version and ordered portion inputs into detached worker context.
Rationale: optimization_config.py currently silently defaults without env path. optimization_operations.start_operation already checks existing operation before policy reload; apply_operation checks planning data without policy reload and applies retained exact solution atomically. Preserve these boundaries. optimization_worker.py uses spawn, deadline, stop event, checkpoints and owner-loss handling.
Alternatives considered: reading policy in worker or acceptance changes captured identity; cwd-based resolution fails normal launch paths; absent-file defaults contradict FR-004.

## Placement bypass

Decision: retire synchronous service generation/acceptance production functions and migrate integration callers. Keep pure Standard optimizer for unit tests only.
Rationale: HTTP /generate and /accept already reject with OPERATION_API_REQUIRED and batch routes are retired, but conflict_aware_generation._execute_optimization still directly calls optimize_semester and saves from callable service paths. Worker-only wrapping is incomplete.
Alternatives considered: a second synchronous captured-context lifecycle duplicates the operation/auth/cancel/atomic workflow without a current requirement.

## Proof and durable identity

Decision: profile-aware evidence with unchanged Standard key list and explicit heuristic key order. Persist algorithm/profile/settings through additive operation migration; compatibility-normalize legacy Standard receipts.
Rationale: CandidateProof validates exactly Standard OBJECTIVE_KEYS and _decision_required_result constructs that list. SemesterOptimizationResult defaults optimal=True, requiring explicit false for heuristics. Worker NoGeneratedAlternative currently sends timeout even without budget exhaustion; independent termination is necessary. Current receipts lack algorithm fields.
Alternatives considered: labeling rhythm/balance as Standard schedule_shape gives false proof meaning; memory-only identity cannot survive terminal status reload.

## Lecturer sequence and bounded search

Decision: per-run shares derived with divmod over normalized-code/stable-ID order; independent validator reconstructs expected allocation/order from captured input. Shared demand plus portion ledgers and complete rollback. Exact scaled/rational comparison of the spec's preferences.
Rationale: ResourceCandidatePlan supplies normalized_code/activity; current input fingerprints include code/eligibility, so extend existing freshness. No available explicit-allocation source was found; optional detached explicit input is honored only when genuinely supplied, without inventing I-010 storage/UI. Spec supersedes older architecture's interchangeable eligibility premise for Lecturer.
Alternatives considered: availability order, free alternation or transferring incompatible shares contradict confirmed intent; fixed preferred-size splitting strands LE. A generic allocation framework is unnecessary.

## Verification

Decision: extend existing config/operation/worker/hard-rule/migration/component suites, add score/search/portion/contract cases and isolated three-strategy comparisons. Use existing pinned toolchain.
Rationale: existing tests cover replay, post-commit loss, cancellation races, stale inputs, whole-selection zero rows and publication locks. Real runtime/AT/deployment checks remain necessary alongside deterministic automation.
Alternatives considered: new orchestration/test infrastructure adds no required capability; narrow mocks cannot establish actual dispatch or runtime limits.
