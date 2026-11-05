# Data Model - I-006

Extend existing prepared-input/coverage/comparison entities; add no schedule revision state. JSON is camelCase, Python snake_case. D1–D11 constraints are quoted in corresponding task descriptions.

## Budget Policy

Fields: defaultSeconds, ceilingSeconds; policyFingerprint derived from effective values. Optional operator JSON selected by TEACHING_OPTIMIZATION_POLICY_FILE.

- **D1:** defaultSeconds and ceilingSeconds are finite positive whole seconds, excluding booleans and strings; defaultSeconds <= ceilingSeconds; absent keys default to 300 and 1800 respectively.
- **D2:** policyFingerprint is a 64-character lowercase hexadecimal SHA-256 digest; a changed fingerprint at start requires preparation again. Unset file path uses defaults; a supplied unreadable/malformed file or unknown key blocks new generation.

No request can override the policy.

## Optimization Operation Receipt (durable)

Table: optimization_operations in SQLite, planning.py model, migration0011 and schema.py support. Technical execution metadata, not schedule authority or planner history.

Fields: operationId, ownerAccountId, originatingSessionId, originatingSessionSecretDigest, contextSecretDigest, requestFingerprint, semesterId, scheduleRevisionId, selectedCourseIds, budgetSeconds, capturedCeilingSeconds, policyFingerprint, phase, startedAt, finishedAt, elapsedMilliseconds, terminalCode, savedResult. Runtime monotonic deadline, child handle, raw secret and exact candidate are NOT durable fields.

- **D3:** operationId is a unique UUIDv4; requestFingerprint, contextSecretDigest and originatingSessionSecretDigest are 64-character lowercase hexadecimal SHA-256 digests. originatingSessionSecretDigest copies the existing authenticated PlannerSession.secret_digest server-side, never a raw credential. Owner/account, originating session, semester and revision IDs are required positive identifiers. selectedCourseIds contains 1–20 distinct positive IDs from the same semester.
- **D4:** budgetSeconds is the captured positive whole-second default, never above its captured ceiling; startedAt is required UTC, finishedAt is nullable UTC until terminal, and elapsedMilliseconds is a non-negative integer without a 60000 cap.
- **D5:** phase is one of preparing, optimizing, checking, ready_to_save, awaiting_decision, saving, saved, cancelled, timeout_no_candidate, failed, stale, interrupted. savedResult is present only for saved; terminalCode is nullable except for failed/stale/interrupted/no-candidate diagnostics. saved means the selected schedule writes and receipt committed together.
- **D6:** same operationId plus identical owner/originating-session-secret-digest/request/context identity returns the same operation without dispatching another worker; a mismatched reuse is a conflict. Saved receipts are immutable; no terminal receipt can launch another solve or become reviewable again.

Keep compact terminal receipts/tombstones for at-most-once recovery. Discard heavy candidate/snapshot data at terminal invalidation. Saved facts may include scoped proof/coverage, never raw secret. Foreign-key lifecycle handling must not grant deleted/revoked accounts/revisions authority. Outcome reads require a currently authorized owner account; originating-session-digest restrictions apply to start replay, live review, accept and finalize, not owner outcome reconciliation or owner cancellation after reauthentication. A reused numeric session row ID with a different secret digest never restores live action authority. The session digest is server-internal, never returned in the API or logged; cancellation of an abandoned operation is allowed to a current authenticated session of its owner.

## Live Operation / Review Context (memory only)

Contains immutable prepared request and snapshot, owner/originating-session-secret-digest identity, context secret/digest, budget/deadline, detached solver inputs, child handle, latest complete candidate and evidence. Server restart loses this context. A receipt cannot recreate it.

- **D7:** contextSecret is 32 cryptographically random bytes encoded as 64 lowercase hexadecimal characters; it is required for live review/finalize/accept and is never persisted in browser storage, logs, URLs or saved schedules. Context loss invalidates action authority; no fixed elapsed-time review expiry applies.

Only operationId may survive in per-tab session storage for outcome-only reconciliation. Navigation, dismissal, auth loss, confirmed retry and recognized interruption invalidate the epoch/context and register cancellation. Failed observation switches to unknown/outcome-only recovery; no actionable review is silently restored. Server discards context on cancellation/restart; secret alone cannot authorize a terminal operation.

## Detached Solver Input / Exact Joint Candidate

Input copies existing course/semester plans, constraints, fixed teaching/active exams, holidays/resources/canonical unavailable dates and tokens. No ORM object or database session crosses spawn.

Candidate fields: candidateFingerprint, preparedSnapshotToken, courses, session tuples, reasons, objectives, unitBound. Sessions reuse established date/start/end/units/window/lecturer/room fields and I-003 constraints.

- **D8:** candidateFingerprint and preparedSnapshotToken are 64-character lowercase hexadecimal digests; candidate courses represent every selected course exactly once. Each session must satisfy every FR-009 hard rule, and per-course scheduled units equal the sum of its session units. An unproven timeout candidate must have aggregate scheduledUnits > 0; individual courses may have zero.

Exact independent validation never inserts provisional sessions. Candidate is immutable once offered. Earlier received checkpoints remain eligible after later UNKNOWN only with evidence for that same candidate/problem.

## Coverage and Objective Evidence

Coverage reuses requiredUnits, scheduledUnits, remainingUnits and status for selection and every course. Current saved work may exceed requirements; this is not optimizer evidence. Preserve I-004 arithmetic: current courses with required/scheduled40/50 and60/40 have per-course remaining0 and20, while selection totals100/90 give remaining10. Do not claim excess units in one course fulfill another course; keep all course facts visible. Hard-valid generated candidates do not exceed per-course required units, so their remaining totals are additive as a consequence, not an invariant for all current work.

- **D9:** coverage counts are non-negative integers; at each course and selection level remainingUnits = max(requiredUnits - scheduledUnits, 0), and status is complete when scheduledUnits >= requiredUnits, otherwise partial. Selection requiredUnits and scheduledUnits equal their respective sums across all courses, including zero-unit courses; selection remainingUnits is computed from selection totals, not summed from course remainingUnits when current work is over-scheduled.

Objective fields: objectiveKey, direction, proofStatus, value, preparedSnapshotToken, candidateFingerprint, optional condition identifying earlier fixed values.

- **D10:** objectiveKey order is total_units, conflicts, schedule_shape, lecturer_changes, room_changes, retained_drafts, canonical_temporal, canonical_resource; proofStatus is proven, unfinished, not_attempted or conditional; value is nullable unless evidence supplies a value for this candidate. A proven full-priority claim requires all earlier objectives proven. Conditional evidence identifies its fixed earlier values.
- **D11:** unitUpperBound and additionalPossibleUnits are both nullable; a known bound must be finite, from total_units for the same prepared problem, and >= candidate scheduled units. Conservatively round a sound integer upper bound upward, then tighten to required units; additionalPossibleUnits = upperBound - scheduledUnits. Proven maximum coverage sets the bound to scheduledUnits. Missing/contradictory/wrong-stage evidence sets both fields null and gap unknown.

Coverage completeness and preference proof are separate. Do not manufacture evidence from required units. Saved outcomes retain original prepared-selection/fixed-occupancy scope.

## State transitions and atomic boundary

Start creates preparing receipt before dispatch; subsequent phases optimizing/checking use the captured deadline. Checked usable result enters awaiting_decision if any proof is incomplete or saved sessions exist, otherwise ready_to_save.

ready_to_save -> automatic browser finalize -> saving -> saved, without a new planner click.
awaiting_decision -> explicit accept -> saving -> saved, without re-solving.
Exhaustion without usable assignment -> timeout_no_candidate.
Malformed model/runtime fault -> failed; relevant input change -> stale.
Nonterminal work may be cancelled/interrupted; saved remains saved on late cancel.
No terminal-to-active transitions; retry creates a new ID after confirmed old discard.

Saving is transient runtime status. Its terminal saved receipt and all selected writes commit together, or neither commits. Crash before commit leaves no saved receipt; startup invalidates unfinished work after database rollback recovery. Late checkpoints cannot revive a terminal result.

At apply: claim existing active Working revision, fresh reload and fingerprint comparison, exact full hard validation, complete selected application and outcome retention plus saved receipt in one transaction. Cancel shares operation/semester serialization but does not demand active editability merely to discard. No search/human wait inside a write transaction.
