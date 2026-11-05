# Phase 0 Research - I-006

Date: 2026-11-04. Read-only research completed by backend_research, client_research and verification_research; consolidated by the Builder. This is research, not independent analysis evidence. Sources are current repository code and installed package source.

## Exact candidate acceptance

**Decision:** retain exact decoded sessions in the live context; never re-solve on acceptance.
**Rationale:** conflict_aware_generation.py:accept_optimization calls _execute_optimization and verifies a reproduced candidate fingerprint. An unproven retry may differ or produce nothing. Reuse comparison/fingerprint/coverage helpers, but apply stored sessions after fresh validation.
**Alternatives considered:** deterministic replay only suits the old all-proven flow; accepting client-supplied sessions risks changing an unvalidated proposal.

## Responsive operations

**Decision:** short endpoints, parent coordinator, stdlib spawned solver-only child, immutable DTOs, pipe/event control, checkpointed assignment and stop/terminate/reap handling.
**Rationale:** candidate/model construction is Python-heavy and solving blocks. Single shipped Uvicorn must remain responsive. Installed OR-Tools9.15.6755 exposes asynchronous stop_search and best_objective_bound. LoadedOperation contains ORM entities and cannot cross spawn. Parent owns DB sessions; close read transactions before solve.
**Alternatives considered:** thread-only requires cooperation across all Python/native stages; request-blocking preserves response/proxy fragility; Celery/Redis adds unsupported complexity.

## Hot-read budget policy

**Decision:** optional mounted JSON policy read on preparation/start, fingerprint preview and captured values.
**Rationale:** editing .env does not reload an existing process. Restarting would kill a run required to retain its prior captured allowance. Mount the containing policy directory read-only, not the individual file; host-side atomic replacement then becomes visible to the running container. An individual-file bind mount can retain the old inode. Verify replacement on the host while operation A and the container remain live, with A retaining its captured budget and the next preparation observing the new policy.
**Alternatives considered:** environment-only reload adds a mechanism anyway; planner overrides violate scope.

## One deadline, incumbents and proof

**Decision:** preparation/enumeration/model/search share one monotonic allowance; checking follows afterward. Retain complete received assignments; stop at first unproven stage and mark later stages not_attempted. Decode only FEASIBLE/OPTIMAL.
**Rationale:** current service has a 60-second deadline/five-second reserve/final-save checks; optimizer rejects non-OPTIMAL and caps elapsed at60000. Preserve objective order/seed/single search worker. Keep coverage evidence separate from preference bounds; upward integer rounding is conservative.
**Alternatives considered:** per-stage budgets exceed allowance; UNKNOWN values are not assignments; conditional continuation is unnecessary. UI still understands conditional evidence if encountered.

## Independent hard validity

**Decision:** exact validation reuses teaching/resource/overlap predicates plus missing assignment checks, before review and application.
**Rationale:** _exact_sessions_valid only checks occupancy overlap. FR-009 also needs session arithmetic, dates/windows, eligibility/capacity, exam boundaries and selected joint validity. draft_schedule_validation.py/resource_rules.py provide shared predicates. load_operation supplies relevant fingerprints and excludes ignored past exams. Existing generated_only zero-total rejection supports clarified empty-result behavior.
**Alternatives considered:** trusting solver status violates FR-010; temporarily inserting provisional sessions into Working violates FR-011.

## Atomicity and recovery

**Decision:** minimal durable technical receipts; apply uses existing semester mutation claim, exact snapshot validation and one schedule/receipt transaction. Solver never saves. Live browser auto-finalizes all-proven new selections; others explicitly accept.
**Rationale:** claim_active_working_revision already provides physical SQLite serialization. Receipt in the same commit proves actual outcome after response/process loss; file-backed concurrency fixtures test real writer races. Compact deduplication receipts are not a new planner decision-log feature.
**Alternatives considered:** memory-only loses commit knowledge; fixed review leases conflict with uninterrupted-review validity; worker auto-save risks mutation after UI abandonment.

## Client/authentication lifecycle

**Decision:** feature hook owns operation ID/epoch/secret and passive two-second polling; outcome-only recovery after context loss; reuse comparison/focus components.
**Rationale:** App hides but keeps CourseSchedulePage mounted; unguarded promises currently revive discarded review. plannerFetch supports abort/keepalive, but the generation wrapper marks every call as deliberate activity. Passive polls must not prolong authentication. Bind live operation authority to the current session's existing secret_digest plus row ID: planner_auth.py deletes/recreates PlannerSession on login, and SQLite can reuse integer primary keys. A deterministic reused-row-ID test must reject old live authority. Owner-only outcome observation/cancel after reauthentication remains allowed and cannot grant apply authority. BatchResultSummary currently equates missing proof with unsolved inputs; accepted unproven results require new wording.
**Alternatives considered:** unmount-only cleanup misses hidden navigation; fetch abort is not server cancellation; stored preview restoration violates FR-021.

## Deployment and verification

**Decision:** retain one app container/Uvicorn process with SQLite; migration0011 plus schema completeness/upgrade support; startup invalidates unfinished contexts while preserving saved receipts. No online restore changes.
**Rationale:** Docker/compose document this single-process architecture. schema.py checks complete migration groups. Restore is explicitly offline. CI uses Python3.12/Node24, pytest, npm lint/test/build.
**Alternatives considered:** distributed/multiworker support expands architecture; trials against existing planner.db risk user data.

No planning-blocking technical unknown remains. Actual Windows/Linux child behavior, latency, assistive usability and larger-selection outcomes remain implementation validation duties.
