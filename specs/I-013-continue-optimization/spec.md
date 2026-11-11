# I-013: Continue optimization from the current proposal

Authorized on 2026-11-10: replace “Erneut optimieren” with “Weiter optimieren”.
This supersedes I-006's fresh-retry/discard behavior and exclusion of continuation.

## Requirements

- Continue the same operation, selection, algorithm and captured policy with an
  additional captured per-round time allowance; do not save or discard the proposal.
- Revalidate the original prepared inputs and exact incumbent before continuation.
  Reject changed inputs, wrong owners, lost contexts and mismatched proposals.
- Pass the incumbent to the selected strategy. Exact strategies use its assignments
  as hints, protect its lexicographic quality, retain proven objective prefixes and
  resume at the first unproven objective. Recognize full required coverage as an
  attained mathematical upper bound. Heuristics start repair from the incumbent.
- Keep the incumbent if the allowance expires without an improvement. Preserve
  reviewability after a continuation worker failure. Explicit cancellation still
  cancels the operation; stale inputs must never be accepted.
- Repeated delivery of the same continuation request must not grant another budget.
- The button reads “Weiter optimieren” and explains that the current proposal is
  retained. No discard confirmation or fresh preparation is performed.

## Acceptance

1. Given a reviewed proposal, when continuation is clicked, then the operation ID,
   inputs and proposal are retained, one new allowance starts, and no schedule is saved.
2. Given complete coverage but unfinished proofs, when continuing, then coverage
   is fixed at its maximum and search proceeds to the first unproven preference.
3. Given partial coverage, when continuing, then no lexicographically worse result
   replaces the incumbent; higher-priority improvement may trade lower preferences.
4. Given timeout or worker failure, when no better candidate was produced, then the
   incumbent remains available to accept or continue.
5. Given a replayed continuation request, then no second worker is dispatched.
6. Given changed inputs or an unauthorized context, then continuation is rejected
   and no saved planning data changes.
