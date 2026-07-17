# Phase 0 Research: FS-010 Conflict-Aware Semester Optimization

## Decision: Use OR-Tools CP-SAT Behind a Domain Boundary

**Decision**: Add pinned `ortools==9.15.6755` and isolate CP-SAT model construction and solving in `backend/app/services/semester_optimization.py`. FastAPI, SQLAlchemy, and client code exchange project-owned dataclasses and schemas only.

**Rationale**: FS-010 requires a proven optimum across optional session placement, resource assignment, and no-overlap constraints. Google documents CP-SAT as its primary constraint-programming solver and scheduling as a suited problem class; its integer variables, optional intervals, and no-overlap constraints match the existing minute/unit domain. OR-Tools 9.15 supports the repository's Python 3.12 runtime. The official status contract distinguishes `OPTIMAL` from `FEASIBLE`, which is essential to the product promise. Sources: [CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver), [constraint optimization](https://developers.google.com/optimization/cp), [job-shop scheduling](https://developers.google.com/optimization/scheduling/job_shop), [OR-Tools releases](https://github.com/google/or-tools/releases/tag/v9.15).

**Alternatives considered**:

- Extend the existing greedy generator: rejected because request-order choices cannot prove the global maximum.
- Write custom backtracking/branch-and-bound: rejected because optional resources, intervals, partial units, retained baselines, and lexicographic objectives create substantial correctness and performance risk.
- Use a hosted optimization service: rejected because there is no integration requirement and it would add credentials, network failure, privacy, and operating cost.

## Decision: Preserve Existing Slot Semantics and Enumerate Finite Candidates

**Decision**: Continue placing generated sessions at the start of an active allowed teaching window. For each allowed date, enumerate valid unit sizes from course minimum through maximum and separately model lecturer and room assignments. Enforce at most one session per course/date and deduplicate identical temporal candidates.

**Rationale**: Existing generation uses the allowed-window start and the current unit/break duration convention. Reusing that observable boundary avoids inventing an arbitrary minute grid, controls candidate volume, and keeps FS-003 behavior stable while allowing partial combinations that the fixed full-course distribution cannot express.

**Alternatives considered**:

- Allow every minute as a start: rejected as an unrequested behavior change and an excessive search space.
- Reuse only the current greedy full-course distribution: rejected because partial optimization must choose the greatest schedulable units and may require another valid session-size combination.
- Pre-generate complete per-course schedules and choose among them: rejected because resource conflicts require joint placement/assignment decisions and exhaustive schedule enumeration grows combinatorially.

## Decision: Model Current Drafts as Whole Retained Alternatives

**Decision**: For every selected course with a current Draft Schedule, include one alternative that retains the complete draft unchanged and one regenerated alternative. Retention excludes regenerated sessions for that course. The generated alternative must meet or exceed the current capped scheduled-unit baseline and may replace manual edits only after confirmation.

**Rationale**: Whole-draft replacement is the existing persistence and confirmation boundary. A retained alternative structurally prevents another course from gaining units by silently discarding reviewed work, while still allowing confirmed equal-unit improvements or higher coverage.

**Alternatives considered**:

- Pin individual manual sessions: rejected because the current model has no provenance flag and FS-010 confirms whole-draft replacement.
- Delete current drafts before solving: rejected because it violates non-worsening behavior and makes rollback/stale handling unsafe.
- Persist solver alternatives: rejected because only the accepted Draft Schedule is domain data in this slice.

## Decision: Use Staged Lexicographic Optimization

**Decision**: Solve objective tiers sequentially, require `OPTIMAL` for each tier, add equality fixing the proven value, and pass the solution as a hint to the next tier. Use one overall deadline and these tiers: total units, conflict count, lecturer changes, room changes, unchanged-draft count, canonical stable cost.

**Rationale**: Staged solving implements the specified strict order without fragile large weights or signed 64-bit overflow. CP-SAT works over integers, and its official status contract makes proof state explicit. Hints and progressively fixed objectives keep later stages bounded.

**Alternatives considered**:

- One weighted objective: rejected because safe dominance weights across candidate ranks and several tiers can approach integer limits and are hard to audit.
- Accept the first feasible result at timeout: rejected because `FEASIBLE` explicitly does not prove optimality and would contradict SC-001.
- Optimize only total units and calculate preferences afterward: rejected because arbitrary post-processing can violate conflict and continuity priorities.

## Decision: Make Solver Execution Deterministic and Bounded

**Decision**: Canonically order every input and variable, pin the solver version, set one search worker and a fixed seed, use stable decision/rank ordering, and reserve request time for load and save around an overall solver deadline. Repeat reference fixtures 20 times.

**Rationale**: The spec requires identical results for unchanged inputs. Single-worker canonical search avoids portfolio timing differences, while a pinned version prevents solver upgrades from silently changing tie outcomes. The 60-second maximum requires explicit deadline handling.

**Alternatives considered**:

- Multi-worker portfolio search: rejected for the initial slice because timing can change which equal optimum is returned and complicate deterministic acceptance.
- No solver deadline: rejected because it violates the planner-visible response bound.
- Persist a prior result solely to force repeatability: rejected because it would add an operation cache/table and could mask changed inputs.

## Decision: Save Only Proven-Optimal Results

**Decision**: Persist only when every objective tier is proven `OPTIMAL`. A merely feasible or unknown result, invalid model, deadline, or unexpected infeasibility returns an actionable operation-level failure and saves nothing.

**Rationale**: The specification promises the measurable maximum within the supported workload, not a best-effort heuristic. The official CP-SAT status definitions state that `FEASIBLE` does not prove optimality. Existing schedule preservation is safer than presenting an unproven candidate as the promised result.

**Alternatives considered**:

- Save a feasible partial result with a warning: rejected because it weakens the agreed outcome and makes non-worsening comparison misleading.
- Continue solving asynchronously: rejected because a job queue, polling contract, cancellation, and operation persistence are not justified by the initial 60-second boundary.

## Decision: Revalidate Exact Results Without Silent Re-optimization

**Decision**: Capture canonical preparation snapshots, verify them before solving, reload material inputs before writes, preserve stale courses, and validate each exact unaffected planned result against refreshed occupancy and rules. Save only exact results that remain valid; never rebuild or re-solve within the same request after changed input.

**Rationale**: This implements the clarification directly and extends current optimistic Draft Schedule revisions to all material input categories. Exact-result validation permits safe partial success without applying a plan the user did not confirm.

**Alternatives considered**:

- Abort every course on any stale input: rejected because unaffected partial success is required.
- Automatically re-solve: rejected because the planner did not confirm replacement against the changed state and response time would become unpredictable.
- Hold database locks throughout the solve: rejected because a solve can take tens of seconds and would block unrelated planner writes.

## Decision: Reuse Existing Persistence and Derived Alerts

**Decision**: Keep optimization operations transient. Save successful course results through the existing whole-draft repository, derive remaining units from saved sessions/current course totals, and reload the complete semester overview to derive alerts.

**Rationale**: The accepted result is already fully represented by Draft Schedule and Draft Session. Operation history, solver diagnostics, and persisted blocking reasons are not required. Reuse prevents counter drift and keeps alerts consistent with manual edits and earlier slices.

**Alternatives considered**:

- Add optimization-operation/result tables: rejected because no history, audit, resume, or reporting requirement uses them.
- Persist remaining-unit counters or alerts: rejected because both are derived from current saved state.
- Patch client state from solver output: rejected because stale filtering and alerts involving other courses could be wrong.

## Decision: Derive Blocking Reasons from Candidate Evidence

**Decision**: Record stable rejection categories while creating candidates and while validating the final arrangement. Add selected-course competition when individually viable choices are excluded by the accepted global arrangement. Return all substantiated categories for remaining units without claiming a unique cause.

**Rationale**: Optimization proof does not inherently provide a human explanation for every omitted unit. Candidate evidence is understandable, testable, and consistent with the spec's requirement to avoid unsupported unique-cause claims.

**Alternatives considered**:

- Expose solver logs or unsatisfied clauses: rejected because they are unstable implementation details and not planner-readable.
- Return only the first rejection: rejected because multiple constraints may apply and the spec requires relevant categories.
- Run separate proof models per reason: rejected because it multiplies solve time without a requirement for minimal explanations.

## Decision: Add a Dedicated Additive HTTP Contract

**Decision**: Add `/api/draft-schedules/optimization/prepare` and `/generate` with dedicated schemas. Preserve FS-006 batch routes unchanged. Reuse existing page, picker, replacement dialog, and result-summary patterns.

**Rationale**: Optimization has a different 20-course bound, unavailable-date input, snapshot scope, five outcome states, units, reasons, and solver failure semantics. A dedicated additive contract avoids breaking existing clients while limiting frontend change.

**Alternatives considered**:

- Add a mode flag to FS-006 endpoints: rejected because nearly every response and several validation rules differ.
- Replace FS-006 routes: rejected because regression compatibility remains required.
- Add a new frontend route: rejected because optimization belongs to the existing course-semester planning workflow.
