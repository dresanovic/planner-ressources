# Optimization Operation Contract - I-006

Internal planner API/client contract, rooted at /api/draft-schedules/optimization. Existing camelCase JSON and structured errors remain. All routes inherit active planner authentication, same-origin CSRF/JSON mutation protection and Cache-Control:no-store. No lecturer/public access; cross-owner IDs return404 without disclosure. Start replay, actionable review, accept and finalize require the current originating authentication session, bound server-side to PlannerSession.secret_digest as well as row ID; numeric ID reuse cannot restore authority. Owner-authorized outcome status and cancellation are explicit exceptions: a current session of the same owner may observe or discard abandoned work after reauthentication, but may not review/accept/finalize it. No client-authored sessions, per-course acceptance or budget override.

## Preparation and operation creation

POST /prepare retains existing semesterId, scheduleRevisionId, courseIds and unavailableDates input and all shared/course snapshot evidence. Add budgetPolicy: {defaultSeconds, ceilingSeconds, policyFingerprint}. Show effective default before start. Invalid operator policy returns503 OPTIMIZATION_CONFIGURATION_INVALID with safe planner recovery guidance and precise operator diagnostics (path/key/reason; no secrets).

POST /operations starts a new operation using:
- operationId: client-created UUIDv4, generated before submission;
- contextSecret: 32 cryptographically random bytes encoded as64 lowercase hexadecimal characters, held in live client memory;
- policyFingerprint from preparation;
- preparation: existing OptimizationGenerationRequest (semesterId, scheduleRevisionId, canonical unavailableDates, sharedSnapshotToken, courses with courseId/expectedDraftScheduleId/expectedDraftRevision/inputSnapshotToken).

Use existing 1–20 distinct-course/same-semester/editable-revision validation. Reject extra fields, including budget overrides. Compare policy fingerprint before new operation creation; changed policy returns409 BUDGET_POLICY_CHANGED for re-preparation. Record captured budget/deadline before preparation/dispatch. Return202 OperationStatus; start does not wait for solving.

Operation ID is durable idempotence identity. Same ID/owner/originating-session-secret-digest/canonical request/context digest returns existing operation, even after config changes; it must not launch a second child or extend deadline. Different reuse returns409 OPERATION_ID_CONFLICT. Start/receipt creation and dispatch are coordinated: failure to dispatch ends failed/non-saving; restart never launches an unfinished receipt. A lost start response is reconciled by GET of the known ID. If it was never registered, reissue the original start with the same ID, secret and preparation rather than creating a second operation. A definitive rejection ends this recovery and offers fresh preparation.

## Status and decisions

| Route | Input | Behavior |
|---|---|---|
| GET /operations/{operationId} | owner auth; optional X-Optimization-Context secret header | 200 current status. Secret/matching originating session digest permits live review facts; without it return outcome-only status, no actionable preview |
| POST /operations/{operationId}/accept | contextSecret, candidateFingerprint | Apply exact stored candidate only from awaiting_decision; explicit whole-selection choice |
| POST /operations/{operationId}/finalize | contextSecret, candidateFingerprint | Automatic live-client action only from ready_to_save; server independently requires all proofs and wholly unplanned selection |
| POST /operations/{operationId}/cancel | optional contextSecret; owner auth; reason cancel/navigation/dismiss/retry/context_lost | Discard nonterminal operation atomically; idempotent. Saved returns saved outcome. A current authenticated session of the same owner may cancel abandoned work even after reauthentication, without the old originating-session binding or restored context secret |

Accept/finalize return200 saved status/result after commit. They never rerun optimization. Repeat of already-saved operation returns its same receipt after owner authorization, not a new application. Wrong/missing live secret or discarded context returns409 REVIEW_CONTEXT_LOST; changed fingerprint409 CANDIDATE_MISMATCH; relevant stale input409 STALE_PLANNING_INPUT with no selected mutation. Invalid candidate produces a non-saving failed result; failed application500 OPTIMIZATION_APPLICATION_FAILED only after confirmed rollback. Unknown outcome remains unknown during transport uncertainty; do not convert it to confirmed unsaved.

Cancel can register even after publication/abandonment or other invalidation. It cannot require active Working editability merely to discard. SQLite operation-state/semester mutation claim linearizes cancel against apply. Cancel waiting for a concurrent DB writer is pending, not confirmed. If save commits first, return actual saved receipt. Late child messages cannot transition a terminal operation.

The first confirmed cancellation stores its reason in terminalCode: CANCELLED_BY_USER, CANCELLED_BY_NAVIGATION, CANCELLED_BY_DISMISSAL, CANCELLED_FOR_RETRY or CANCELLED_CONTEXT_LOST. Later cancellation requests preserve this reason; they never overwrite a saved receipt. Older receipts with no recorded reason must be described as such rather than guessing a trigger.

The old synchronous /generate and replay-based /accept paths must not remain a bypass. Migrate the internal client to operation routes. Retire their old mutation bodies with structured409 OPERATION_API_REQUIRED, or adapt only when all new operation identity/context requirements are present; never run old acceptance replay. Existing independent legacy single/multi-course APIs remain outside the I-006 UI path and retain unrelated safeguards.

## OperationStatus response

Common fields:
- operationId, semesterId, scheduleRevisionId, selectedCourseIds, selectionCount;
- phase (data-model D5), budgetSeconds, elapsedMilliseconds, budgetExhausted;
- currentObjectiveKey nullable (only when known), saved boolean;
- canAccept, canFinalize (true only for matching current live context and corresponding phase);
- review nullable; result nullable (saved receipt facts); errors/reasons as applicable.

No 60000 cap on elapsedMilliseconds. Runtime elapsed uses monotonic time from start, including checking; after terminal use captured terminal duration. Human review consumes no optimization allowance; total elapsed remains displayed, with search budget exhaustion separate. No invented solution percentage or finish estimate.

review contains candidateFingerprint, scoped prepared evidence, existing RegenerationComparison, required/scheduled/remaining overall and per-course counts, existing warning/manual replacement evidence, ordered objectives, unitUpperBound/additionalPossibleUnits or null, gapKnown, and whether saved sessions exist. review is present only for a usable hard-validated candidate with a live action context. For an unproven timeout aggregate scheduled units must exceed zero. No draft/session is inserted before successful application.

Fully proven new selections become ready_to_save; the matching live client automatically calls finalize without another user decision. Fully proven existing selections and any unproven selection become awaiting_decision. A ready_to_save state observed after context loss is outcome-only, then cancelled; it cannot auto-finalize from restored operation ID.

## Evidence invariants

Implement data-model D8–D11 identically in backend schemas and TypeScript fixtures. Preserve objective order and definitions. Generated schedule_shape is the existing combined weekly concentration/session-size objective, not an additional new objective. Stop at first unfinished stage; later stages not_attempted. Conditional evidence must state preceding fixed values and cannot imply full-priority proof.

A usable candidate is independently hard-valid, not necessarily complete or optimal. Coverage and objective proof remain distinct. Preserve existing I-004 current arithmetic: aggregate required/scheduled are course sums; remaining=max(required-scheduled,0) independently at each level. Current required/scheduled40/50 and60/40 yield remaining0/20 by course and selection100/90/10. Aggregate remaining is not the sum of current course remaining in this case; excess in one course is not proof of fulfillment or optimum for another. Bounds belong only to total_units for the same prepared problem. Example: S80/R100/U90 means20 remaining and at most10 additional possible, not a promise90 is attainable. With no trustworthy bound both bound/gap are null/unknown. Proven maximum80/100 has zero coverage gap despite20 remaining. Full100/100 without preference proof remains provisional.

A checkpoint from an earlier stage may survive later UNKNOWN; evidence must refer to that candidate/problem. Never fabricate fallback COURSE_CONSTRAINT as proof that unplaced units are impossible. Display established substantiated reasons as observations, or explicit missing evidence.

## UI and interruption contract

Start and cancellation clicks remain visibly acknowledged within one second under connected acceptance conditions. A cancellation request is not durable confirmation of cancellation.

Poll status every two seconds, non-overlapping; passive requests omit X-Planner-Activity:user. Explicit start/accept/cancel/retry are deliberate activity. Use plannerFetch credentials/CSRF/401 behavior. At >5 seconds without a confirmed update, show unknown status and disable decisions, while allowing an in-flight response to finish. After thirty seconds without confirmation, replace a still-stalled request and invalidate its callback epoch before retrying; late responses cannot reopen decisions. A slow or failed status request alone does not cancel optimization or discard its memory-only context. Retry the same ID and live secret; resume decisions only after a fresh server-confirmed status. Explicit cancellation/context-loss intent still retries until a terminal receipt is confirmed, preserving the original requested reason. Timers/health polling cannot claim solver completion probability.

Guard every callback with operation ID and context epoch. Losing active Schedule/generation surface, semester/revision change, closing/dismissing, auth loss/pagehide invalidates epoch and sends cancel (keepalive best effort for browser departure). Abort only observation, never pretend abort registered cancellation. Persist operation ID only for outcome recovery; do not store secret, preview or candidate authority. Reconnection cannot silently restore review. After uncertain accept/finalize, use same ID receipt, disable contradictory decisions, and show actual saved outcome even if local context disappeared.

Switching browser tabs or minimizing the window preserves the planning context and does not request cancellation. While the document is hidden, suspend the five-second status watchdog because browsers throttle background timers. On return, allow five seconds for a confirmed status, immediately poll if no request is in flight, and preserve non-overlapping requests. Refresh, pagehide, authentication loss and deliberate context changes still discard authority and reconcile outcome only; retaining an unchanged in-memory context across a transport retry does not restore discarded authority.

Review: exact buttons “Neu erzeugten Stundenplan übernehmen” and “Abbrechen”; operation-wide decision; individual zero-unit courses included. Explain manual replacement when current sessions exist, otherwise no saved teaching and acceptance creates candidate schedules. Explain avoidable remaining units, unproven preferences and fixed-occupancy effect on later runs. Lower coverage remains permitted.

Retry action “Erneut optimieren” is separate. Before discard show fresh start/current budget/no resume/no improvement guarantee; Back preserves review. After confirmation cancel old operation durably, then freshly prepare and start a new ID. If old outcome is saved or unknown, reconcile before offering a contradictory retry.

German actionable terminology/date conventions, keyboard/programmatic labels/status, visible focus, no color-only meaning, terminal announcements, no focus stealing on progress; preserve comparison focus trap/restoration. At320/820/1280 CSS pixels and200% text zoom all evidence/actions remain reachable.

## Recovery, authorization and storage

Startup after DB recovery marks preparing/optimizing/checking/ready_to_save/awaiting_decision receipts interrupted and destroys context; never resumes solve/review. Saved receipts remain saved. Shutdown signals/stops/reaps known children; child detects parent-channel closure. Raw secret is never persisted/logged. Derive and persist originatingSessionSecretDigest from the existing authenticated PlannerSession.secret_digest; never accept it from client input or return/log it. Before start replay or live review/accept/finalize compare both the current session ID and secret digest; check again inside application transaction. A same-account replacement login deliberately reusing the numeric ID must fail old live authority. Owner-authorized status/cancel after reauthentication remains allowed, and an already-saved receipt can be returned without applying again.

Technical receipts retain only compact request identity/captured facts/terminal results for deduplication and reconciliation. Heavy provisional material is memory-only and cleared on invalidation; no new permanent planner decision-history feature. Schema migration must support fresh install, current FS-016 and earlier supported sequential upgrades, and reject partial new-table states without silent destructive repair.

## Contract verification

Backend tests/api/test_optimization_operations.py exercises full JSON states, auth/ownership/session, policy errors, idempotent start, exact apply, cancellation and recovery. Client api tests and test/optimizationFixtures.ts use matching states/evidence. File-backed concurrency service tests verify transaction/race claims; StaticPool-only tests are insufficient. Old deadline/replay expectations are intentionally superseded, other scheduling/lifecycle/auth protections retained.
