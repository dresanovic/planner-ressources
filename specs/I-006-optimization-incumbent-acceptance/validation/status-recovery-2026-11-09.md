# Optimization status recovery — 09.11.2026

## Report and evidence

The reported 11-course operation ended as `cancelled` after 101,375 ms of its 900-second budget. Its receipt has no terminal code: the old implementation did not retain cancellation reasons, so the individual trigger cannot be established retrospectively from that receipt.

The client had two destructive transport paths: a failed status request immediately submitted `cancel(context_lost)`, and five seconds without confirmation invoked the same cancellation/reconciliation path. Both discarded the live candidate authority. The earlier visibility fix addressed tab switching but left these transport paths intact.

## Corrected behavior and requirement traceability

| Requirement | Implementation and verification |
| --- | --- |
| FR-023a: transport failure must not cancel unchanged context | `useOptimizationOperation` retains memory-only authority, shows unknown status, disables decisions, and retries the same operation. Failed/stalled requests after 100 seconds recover and save in regression tests. |
| FR-006: promptly report unconfirmed status | Five seconds without confirmation shows uncertainty; a slow in-flight response can still finish. A still-stalled request is replaced after thirty seconds, with a new callback epoch. |
| FR-021/022: discarded authority stays discarded | Navigation, pagehide, authentication loss and refresh still discard authority; late status cannot finalize. Lost explicit cancellation requests are retried with their original reason. |
| FR-020/023: one operation and accurate committed outcome | An unregistered lost start reuses its original ID/secret/preparation. Definitive rejection ends recovery. A saved receipt survives later cancellation without duplicate writes. |
| FR-028: explain confirmed cancellation | API passes the validated reason into the receipt's terminal code. Repeated cancellation preserves the first reason. UI maps recorded reasons into German and explicitly identifies older receipts without a recorded reason. |

No raw live secret or candidate authority is persisted. Server ownership, originating-session checks, candidate validation and atomic application remain in place. No new database migration or dependency is needed.

## Automated verification

- Full client suite: **70 files, 565 tests passed**.
- Production frontend build and TypeScript checks: **passed**.
- Backend operation services/API group: **95 tests passed**.
- Final API forwarding and saved-receipt invariants: **2 tests passed**, including one additional API test and one strengthened existing test.
- Targeted hook suite: **27 tests passed**, included in the client total.
- Scoped `git diff --check`: passed.
- Live Vite source was read over HTTP and confirmed to contain the reconnect fix. The existing backend is configured with reload enabled.

## Full selection verification

Executed the same semester/revision and 11-course selection on an isolated SQLite backup with the unchanged **900-second policy**, using the normal spawned solver and operation services. Status was sampled every fifteen seconds and remained responsive (observed reads at most 0.016 seconds). The run passed the previously reported 101-second cancellation point and the complete search budget without cancellation.

The operation reached **awaiting_decision**, observed at the 915-second sample after search completion and candidate checking. Its independently validated provisional candidate scheduled **339 teaching units**, with **19 remaining**. Applying that exact reviewed candidate through `apply_operation(..., finalize=False)` succeeded: the copied receipt became **saved**. A provisional candidate requires the normal explicit acceptance action; it is not an automatic-save result.

All writes for this verification were confined to the copied database. The production database retained the reported cancelled receipt. The local verification helper and database copies are in ignored `.tmp` storage; no production authentication state or live planner record was modified.

## Review

Reviewed the recovery state transitions, callback epochs, decision gating, memory-only context, same-ID start retry, explicit cancellation retry, terminal reason persistence and saved-result idempotence against the I-006 requirements and contract. No outstanding material finding in the corrected scope. The live browser interaction was not automated; service-level full-selection execution and client transport regressions provide separate verification.

Unrelated existing dated-teaching-window changes in the working tree were outside this corrective review. No commit or push was made.
