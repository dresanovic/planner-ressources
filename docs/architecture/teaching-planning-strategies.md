# Architecture Exploration: Teaching Planning Strategies

## Status

Proposed architecture for I-011. Product scope and the three strategy choices
were confirmed on 09.11.2026; this document authorizes no production changes.

## Context

Planners need different scheduling approaches for different planning situations
while retaining one teaching-generation and acceptance workflow. The user
requires the current algorithm to be named `standard`, two additional algorithms
named `cohort` and `lecturer`, the Strategy design pattern, and selection through
`config/optimization/policy.json` at the beginning of each generation run.

Confirmed clarifications:

- Apply the selector to all supported teaching generation, including a single
  selected course. Exam generation keeps its current algorithm.
- Cohort-first and lecturer-first both seek balanced weekly teaching across the
  semester. Lecturer-first groups by lecturer; reducing teaching days or packing
  teaching into dense blocks is not its primary goal.
- Read policy for preparation, verify it at Start, and freeze the selected
  strategy through computation, review and acceptance. This is not login-scoped.

## Current system

Repository observations, including the existing uncommitted working tree:

- FastAPI services prepare one selected-course planning snapshot. I-003 retired
  independent single-course and batch generation routes; retain that boundary.
- `backend/app/services/optimization_config.py` currently accepts only
  `defaultSeconds` and `ceilingSeconds`. It reloads an explicitly configured
  `TEACHING_OPTIMIZATION_POLICY_FILE` during preparation and operation start,
  rejects invalid policy, and fingerprints effective values. With no configured
  path it uses shipped defaults; it does not automatically read the repository
  file. Merely adding a selector to that file would therefore be insufficient.
- The requested local file currently contains 900 default seconds and 1800
  ceiling seconds. Preserve these operator values when the feature is delivered.
- `optimization_operations.py` owns operation identity, policy-change detection,
  background execution, cancellation, freshness checks and atomic acceptance.
- `optimization_worker.py` sends detached planning values to a spawned process
  and calls `semester_optimization.optimize_semester` directly.
- `semester_optimization.py` implements CP-SAT search with staged objectives,
  candidate generation, bounded computation, checkpoints and proof evidence.
- `conflict_aware_generation.py` independently validates exact assignments
  against selected and protected occupancy before offering a result and saving.
  There is also a direct optimizer call in this service; every supported
  teaching placement entry point must use the chosen strategy or be explicitly
  retired. Wrapping only the worker leaves a possible bypass.
- Current objective ordering includes total LE, intensive teaching time and
  daily LV variety before lower arrangement preferences. These priorities must
  remain above any new strategy-specific balance penalties.
- Cohort records have no permanent-room assignment. Eligible course rooms and
  room-continuity preferences exist; the first eligible room is not evidence
  that a planner designated a permanent room.
- I-010 defines future fixed lecturer LE portions, but is not implemented by
  this analysis. Existing eligibility does not identify those portions.

## Goals

Support three genuinely distinct planning strategies with equal validity and
acceptance guarantees, preserve standard behavior, and make the algorithm used
for a result visible and traceable. Compare algorithm quality without promising
that either heuristic always improves coverage or runtime.

## Constraints

The requested Strategy pattern is justified by three concrete algorithms.
Keep the current backend, worker lifecycle and frontend surfaces. Do not create
another scheduler UI, distributed queue, external service, dynamic plugin
loader or dependency-injection framework. Only explicitly selected courses may
be planned; unselected teaching and active exams remain protected occupancy.
Selected current sessions are replaced only under existing atomic acceptance
rules; search and backtracking affect provisional generated work only.

## Decision drivers

1. Shared hard constraints and protection of saved work.
2. Preservation of standard results, priorities and proof semantics.
3. Effective policy selection and immutable per-operation identity.
4. Actual cohort-first and lecturer-first scheduling behavior.
5. Bounded computation and honest incomplete-result reporting.
6. Small, testable design using current components.

## Assumptions

- Recommended machine identifiers are `standard`, `cohort`, and `lecturer`;
  recommended JSON key is `activeAlgorithm`. These names make the requested
  choices explicit; precise contract naming can be finalized in specification.
- Missing `activeAlgorithm` in an otherwise valid legacy policy means
  `standard`. Invalid explicit identifiers must never silently select another
  algorithm. Existing duration defaults and validation remain.
- Recommend resolving the normal local policy to the repository's
  `config/optimization/policy.json` independently of process working directory.
  Preserve an explicit deployment path for the same logical file, including
  `/config/optimization/policy.json` in containers. Do not hardcode the Windows
  workspace path into application code.
- Recommend an unreadable, missing resolved file or invalid policy blocks new
  preparation/start with actionable configuration feedback. This changes the
  current no-path shipped-default behavior; specification must state the
  deployment migration and missing-file policy explicitly. No application
  startup or unrelated health operation needs to fail.
- The attachment's capacity screen and permanent-room assumption are narrowed
  below to avoid taking ownership of I-007 or inventing a new catalog feature.

Proposed policy example, retaining the current local duration values (this
analysis does not edit the live file):

```json
{
  "defaultSeconds": 900,
  "ceilingSeconds": 1800,
  "activeAlgorithm": "standard"
}
```

## Options considered

### Option 1: Three concrete strategies with shared scheduling primitives

#### Description

Wrap the current CP-SAT algorithm as Standard. Add cohort-first and
lecturer-first bounded greedy searches with limited backtracking. All implement
one small strategy contract over detached planning input, search control and
normalized results. Share candidate legality, duration/resource rules,
occupancy, result validation and evidence. An explicit identifier-to-strategy
registry resolves the frozen selector inside the worker.

#### Benefits

Delivers the attachment's alternative algorithm and the user's lecturer variant,
preserves standard internals, and supports independent algorithm verification.
Requires no new technology or deployment boundary.

#### Disadvantages

Heuristic search needs its own placement/rollback logic. It can miss feasible
placements and cannot generally prove coverage or preference optimality.

#### Risks

Duplicated hard rules, double-counted demand and incomplete rollback can create
incorrect results. Use shared primitives and independent exact validation;
never trust a strategy's assertion of validity alone.

### Option 2: Strategy objects configuring one shared CP-SAT solver

#### Description

Use Standard, Cohort and Lecturer strategy objects to supply search ordering,
objective expressions and hints to a common mathematical model.

#### Benefits

Keeps one constraint model and retains access to solver proof evidence. Useful
if the intended difference is primarily optimization preferences.

#### Disadvantages

Does not directly implement the attachment's greedy/backtracking approach;
grouping or hints may produce identical behavior and offer no meaningful
alternative when proof time is the practical problem.

#### Risks

Moving common model construction can change Standard tie-breaking and make
its preservation harder to demonstrate. Distinct labels could conceal nearly
identical algorithms unless observable behavior is specified.

## Comparison

| Driver | Separate searches, shared primitives | Shared CP-SAT with strategy policies |
| --- | --- | --- |
| Attachment's greedy/backtracking approach | Direct fit | Partial fit |
| Preserve existing Standard | Small wrapper | Broader solver refactor |
| Shared legality | Shared primitives plus exact validator | Shared model plus exact validator |
| Mathematical proofs | Standard; heuristic claims limited | Available to all when search proves them |
| Distinct planning behavior | Explicit grouping and traversal | Depends on search/objective changes |
| Delivery risk | New bounded search logic | Existing model and proof regression |

## Recommendation

Choose Option 1. Keep a single application orchestration path and replace only
the scheduling search decision. Use a small interface, three concrete
implementations and a fixed registry; the existence of three actual algorithms
earns this abstraction under the constitution's simplicity rule.

The conceptual boundary is:

`prepare/start -> captured policy and snapshot -> worker strategy dispatch ->
shared exact validation -> existing review -> fresh validation -> atomic save`.

The worker receives the captured identifier and any effective algorithm
parameters as serializable values; it never rereads policy or receives ORM
records. Normalized results include sessions for every selected course,
scheduled/remaining LE, substantiated reasons, algorithm identity, termination
reason, objective evidence and elapsed time. Strategy-specific balancing metrics
must not be mislabeled as Standard's proven objectives.

### Cohort strategy

Group explicitly selected demand by cohort, prioritize scarce feasible
opportunities, and distribute sessions over semester weeks. Evaluate candidate
placements across the semester instead of filling the first weeks first. Rank
valid alternatives for weekly cohort balance, sensible per-course weekly
frequency and room continuity below the common higher priorities. Preserve
allowed session-size flexibility, including redistribution of valid session
sizes where a fixed initial split would strand LE. Every placed session updates
shared lecturer/room/cohort occupancy across all groups. Limited repair may
revisit provisional sessions from earlier groups; it cannot move fixed bookings.

Keep existing regeneration semantics: a replacement candidate covers the full
selected LV targets. Current selected sessions are the comparison alternative,
not extra fixed occupancy to subtract from demand and then replace with only the
remaining LE. Protected unselected teaching still consumes load and occupancy.

### Lecturer strategy

Use the same bounded-search approach and weekly-balance goal, grouping demand
by lecturer across the selected courses and cohorts. Weekly load belongs to the
lecturer, rather than the cohort, and includes relevant fixed teaching as load
and occupancy. Cohort feasibility and room eligibility remain mandatory.

Before I-010, an LV with alternative eligible lecturers is one shared demand
pool: candidate lecturer assignments compete for the same remaining LE. Never
copy the LV's entire required LE into every lecturer group. Once fixed portions
are introduced, each group's demand is the relevant confirmed portion and no
search strategy may transfer it to someone else. This does not implement or
infer I-010 allocations.

### Common quality and evidence

Compare complete provisional candidates first by total permitted LE, then
applicable intensive teaching, then intensive daily variety, then the strategy's
lower preferences. A flat weighted sum must not trade away higher-priority LE
for balance or room stability. Heuristics seek these priorities within bounded
search; selecting one does not promise global maximization or proven
intensive-use/variety optima. Retain the best valid checkpoint encountered.

Cheap capacity checks may identify a substantiated necessary shortfall, but
sufficient aggregate minutes never prove feasibility. Merge overlapping windows,
avoid shared-time double counting, and distinguish LE, occupied teaching/break
minutes and search seconds. Continue useful partial planning after a shortage
warning. Full capacity screens and additional-slot proposals remain I-007.

Report early heuristic completion, backtracking-limit exhaustion, deadline
exhaustion, cancellation and failure distinctly. An early heuristic result with
unproven objectives requires explicit acceptance even before timeout; extend
I-006's result semantics accordingly. No candidate or zero placed LE preserves
saved work. No placement found by bounded search is not proof of infeasibility.
Complete coverage can establish that no additional required LE remains, but does
not prove lower preferences. Report only sound bounds for the same snapshot;
otherwise report an unknown improvement gap.

## Consequences

- Extend effective policy, preparation/status/results, worker payload and
  operation identity to bind the chosen strategy and relevant parameters.
  Include them in policy freshness and candidate acceptance evidence.
- A policy change before Start requires fresh preparation. A change after
  Start applies to future runs only, including when the old candidate is
  awaiting acceptance. Acceptance revalidates planning inputs against the
  captured operation context, not newly loaded algorithm configuration.
- Idempotent repeated Start for an existing operation returns that operation;
  a fresh retry reads current policy and starts a new run. Do not rerun an
  accepted candidate under whichever algorithm is active later.
- Preserve operator time limits and shared cancellation/checkpoint handling.
  Bound every search phase, including candidate enumeration, capacity checks,
  scoring, backtracking and finalization.
- Show algorithm identity read-only in the existing preparation, progress and
  review surfaces. No planner dropdown or per-request override is introduced.
- Fixed-weight tuning, dynamic algorithm discovery, automatic selection from
  filters, automatic fallback and heuristic-to-CP-SAT portfolios are deferred.
- No catalog change for a permanent room is included. Use established eligible
  room continuity; a named permanent-room feature needs separate confirmed scope.

## Validation required

- Standard equivalence against representative deterministic baseline fixtures,
  allowing elapsed-time differences without requiring identical timeout races.
- All three selectors are actually read from the requested logical file on
  normal local startup paths and correctly dispatched for one/multiple courses.
- Legacy selector omission, invalid selector/types, duplicate/unknown keys,
  malformed/missing files, policy changes and atomic file replacement.
- Frozen running/review identity, idempotent Start, fresh retries and stale
  planning input; reject client attempts to override strategy.
- Shared conflicts, holiday/window/size/break rules, room capacity, active exams,
  fixed occupancy and protected publication facts across every strategy.
- Cohort and lecturer fixtures where weekly grouping changes the intended
  distribution; shared lecturers across cohorts and alternative lecturers on
  one LV; no lost, duplicated or overallocated demand.
- Partial/zero demand, incompatible session remainders, cross-group bounded
  repair, complete rollback on unsuccessful repair and no protected movement.
- Unproven early completion, real timeout, cancellation, failure, objective
  evidence, unknown gap and operation-wide atomic accept/cancel behavior.
- Compare coverage, weekly distribution, runtime and remaining LE on identical
  snapshots and budgets; report observed trade-offs without claiming universal
  superiority. Check existing supported selection limits, not a new 94-course
  promise. Use isolated fixtures/databases, never the live plan.

## Open questions

Specification should settle exact balance/frequency penalties, week boundaries,
partial-week normalization, tie-breaking, finite backtracking allowance and
checkpoint frequency. Set the explicit policy-file migration/missing-file
behavior. Confirm the attachment's permanent-room statement is satisfied by
room continuity or move actual permanent-room administration to separate scope.
These details do not change the confirmed three-strategy slice boundary.

## Handoff to specification

Use I-011 in `docs/planning/Feature_slices.md`. Preserve I-003's one workflow,
I-004's atomic choice, I-006's operation lifecycle and honest proofs, I-009's
higher priorities, and I-010's no-transfer boundary when delivered. This analysis
creates no spec, implementation plan, tasks, production code or live policy edit.

Reference: Google's [CP-SAT status documentation](https://developers.google.com/optimization/cp/cp_solver)
distinguishes feasible, optimal, proven infeasible and unknown results. That
supports keeping result validity, proof and search termination separate; the
specific strategy recommendation above is an inference from this repository and
the confirmed user requirements, not an OR-Tools performance guarantee.
