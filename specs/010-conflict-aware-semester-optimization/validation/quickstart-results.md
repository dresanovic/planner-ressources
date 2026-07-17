# Consolidated quickstart acceptance

Date: 2026-07-17.

| Scenario | Result | Evidence |
|---:|:---:|---|
| 1 | Pass | Global one-slot counterexample selects 4 rather than request-order 2; deterministic ordering. |
| 2 | Pass | Multiple eligible lecturer/room choice and continuity test. |
| 3 | Pass | Fixed occupancy filtering and retained conflict-tier test. |
| 4 | Pass | Proven 3/5 partial result and zero-placement no-parent test. |
| 5 | Pass | Staged unit, conflict, lecturer, room, preservation, canonical objectives each lock only `OPTIMAL`. |
| 6 | Pass | Actual-unit baseline, equal preservation, increased-unit replacement, confirmation test. |
| 7 | Pass | Canonical unavailable-date deduplication and candidate exclusion. |
| 8 | Pass | Post-solve stale preservation plus exact unaffected save, one solver call. |
| 9 | Pass | Injected unproven solver result returns 503 and saves nothing. |
| 10 | Pass | Twenty identical deterministic solve signatures. |
| 11 | Pass | Five-status summary/retry UI fixture and overview refresh page tests. |
| 12 | Pass | Five raw reference runs, all 9.831-10.147 seconds and proven optimal. |

No scenario introduces holiday CRUD, exam scheduling, fairness quotas, an algorithm selector, migration, persisted operation history, or background processing.
