# FS-010 validation evidence

This directory records reproducible evidence for the twelve scenarios in `quickstart.md` and the two usability criteria. Evidence must name the command, fixture, expected result, actual result, date, and environment.

## Quickstart scenario evidence

1. Request-order counterexample and maximum units — `user-story-1-results.md`
2. Resource continuity and deterministic tie-breaking — `user-story-1-results.md`
3. Fixed occupancy and unavailable-date deduplication — `user-story-1-results.md`
4. Optimal partial and zero-placement results — `user-story-2-results.md`
5. Non-worsening replacement — `user-story-3-results.md`
6. Equal-unit strict improvement — `user-story-3-results.md`
7. Solver proof failure saves nothing — `user-story-1-results.md`
8. Stale course preservation — `user-story-3-results.md`
9. Unaffected exact-result continuation — `user-story-3-results.md`
10. Constraint and source-record preservation — `quickstart-results.md`
11. Mixed five-status result and fresh retry — `user-story-4-results.md`
12. Supported-workload performance — `performance-results.md`

## SC-006 / SC-007 usability protocol

At least ten representative planners or acceptance reviewers receive anonymized complete, improved-partial, unchanged, failed, stale, and replacement examples. Record whether they identify the outcome and reasons, distinguish improved partial from unchanged, understand the replacement guardrail, and complete each prompt within the specified time. Store aggregate results in `usability-results.md`; do not invent human observations.
