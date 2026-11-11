# Implementation plan

Use the existing Strategy registry. Implement `standard_optimized.py` by copying Standard's `optimize_semester` orchestration and importing its existing types and model/resource helpers. Add cumulative-weekly spread expressions and bounded stage transitions in that module only. Preserve Standard's search behavior and baseline outputs.

Extend explicit policy/API/database/client identifiers and proof profiles. New migration 0016 widens receipt constraints; initialization detects and upgrades the previous complete schema atomically. Keep Standard's auto-finalization rules unchanged; new strategy requires review.

Simplicity: one concrete strategy module and one migration; no dependencies, abstractions for hypothetical algorithms, separate worker or save path. Copying orchestration is intentional isolation requested by the user; shared legality and validation remain reused.

Tests first: new service distribution/proof/interruption cases; policy/serialization/migration tests; actual spawned-worker HTTP acceptance and frontend decoder/label coverage. Re-run Standard baselines, backend operation/strategy/migration tests, complete frontend tests, lint/typecheck/build. Tests use temporary databases/policies; do not edit live policy or restart a server with an active run.

## Validated starting-plan correction

Problem: the eight-course live selection has a valid constructive arrangement, but only solver hints retain it. A bounded diagnostic measured 503,679 variables and stopped after 60 seconds of presolve with no search branches. If the coverage solver returns UNKNOWN, the original orchestration loses the arrangement and exits at its 35% share.

Simplicity check: expose the existing constructive helper's selected sessions, with no new scheduling strategy, dependency, worker, or state store. The optimized extension evaluates and independently validates that arrangement, publishes it before expensive model construction, and reuses existing incumbent seeding and lexicographic guards. Keep cancellation, freshness validation and explicit acceptance. Coverage uses the entire remaining budget only if no initial candidate exists. Correct the existing algorithm fallback label.

Tests first: force solver UNKNOWN and model-build deadline expiry; verify candidate checkpoints precede model construction, full coverage is proved while preferences remain unproved, cancellation discards the candidate, and partial candidates never lose coverage. Pin the constructive assignment in a real solve to compare every initial objective with exact model values. Verify no-candidate time allowance, algorithm-specific completion labels, and operation-level checkpoint/deadline review without writes. Re-run strategy, baseline, continuation, worker, and acceptance tests. Exercise the eight-course current database read-only; never save its diagnostic candidate or restart the server.

## Semester spread and compact model

Reuse the deterministic constructor with an optional date-order callback; Standard keeps its existing chronological default. Compare the original construction, an intensive-first spread ordering over feasible weeks, and any currently valid saved sessions using recomputed exact objective values and independent validation. Never replace a continuation incumbent with a worse fresh seed.

On the real selection, changing date order alone lowered intensive priorities and was correctly rejected. Add one constructive relocation pass on the best seed: move ordinary sessions only to ordinary legal candidates of the same unit count, keeping selected/protected occupancy and one-session-per-course/day constraints. Accept strictly better per-course weekly-spread moves; compare and independently validate the resulting whole selection. Intensive session presence and coverage stay unchanged.

The compact generated-only model uses one chosen time interval per course/date and one resource assignment per resource/date. Group temporal alternatives by identical resource eligibility to enforce the selected candidate's exact resource set and resource-ranking cost. Reuse continuity helpers with day-level views and incumbent lexicographic guards with a compact hint adapter. Keep all temporal alternatives and retain the original formulation for non-generated direct callers. No new dependency, background service, schema, policy setting, UI control or automatic save is needed.

Tests first: timeout spread quality, saved-seed preservation and stale rejection, exact compact/original objective and legality comparisons with varying eligibility, interval-count reduction, continuation and cancellation. Compare the current eight-course saved input read-only for coverage, spread objective, teaching span, model size and bounded solver behavior. Update only implementation/specification/tests; leave prior validation reports as historical evidence.
