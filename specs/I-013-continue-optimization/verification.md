# Code Review

## Scope reviewed

I-013 continuation endpoint, live operation state, detached worker input, exact
incumbent hints/lexicographic constraints, both exact strategies, heuristic repair
initialization, client API/hook, comparison action and related tests/documentation.
The existing branch contained substantial uncommitted I-011/I-012 work before this
request; unrelated changes are outside this review and have been preserved.

## Context used

User authorization on 2026-11-10, I-013 spec/plan, I-006 operation contract,
I-011/I-012 strategy implementations and the project constitution. Review followed
the local code-review skill after implementation and targeted verification.

## Verification performed

- Backend suite A: continuation, Standard, Standard Optimized, recorded Standard
  baselines, real spawned worker and operation HTTP tests: **133 passed**.
- Backend suite B: operation services, heuristics, strategy lifecycle, strategy
  contracts and strategy acceptance: **207 passed**.
- Final continuation suite including two additional real placement-improvement
  scenarios: **17 passed** (15 overlap suite A; 342 distinct backend cases total).
- Frontend API, operation hook, comparison dialog and planning-page tests:
  **190 passed**. API wire test rerun after adding continuation assertions:
  **45 passed**, included in those 190.
- TypeScript/Vite production build: passed. ESLint: passed.
- `git diff --check`: passed; existing Windows line-ending notice only.
- Tests use isolated databases. No real planning database was changed or real
  schedule accepted. No deployment or live browser acceptance was performed.

## Findings

No material findings in the scoped implementation after verification. No critical,
high, medium or low defects requiring follow-up were identified. No refactor is
required. Existing dependency deprecation warnings do not originate in I-013.

## Requirement traceability

| Requirement | Implementation | Evidence |
|---|---|---|
| Same operation, seeded proposal, extra allowance | continue endpoint, live state, worker input | service continuation identity; HTTP continuation; spawned continuation |
| Ordered quality preservation | exact lexicographic guard and parent candidate comparison | four guard scenarios; worse-result fallback; both exact strategies |
| Resume proven prefix/full coverage | seed_incumbent and exact stage loops | prefix progress; FEASIBLE full-coverage proof; intensive placement improvement |
| Timeout/worker failure retain proposal | coordinator fallback | timeout, failure and acceptance tests |
| No duplicate dispatch on replay | continuation UUID registry under live lock | service and HTTP replay tests |
| Changed inputs/context rejected | existing context checks, snapshot loader and candidate validator | stale input and wrong secret/fingerprint tests; existing lifecycle/auth regressions |
| Continue button instead of restart | client API/hook/dialog/page | hook, dialog, API wire and cross-view page tests |
| No automatic persistence | continuation returns explicit review | isolated saved-state comparisons; HTTP explicit acceptance |

## Test assessment

Coverage includes positive improvement, no improvement, rejected worse outcomes,
failure, timeout, replay, stale snapshots and explicit persistence. Real Windows
spawn transports the incumbent and starts at the first unfinished stage. Recorded
completed Standard baselines continue to pass.

## Architecture and design assessment

Reuses the operation receipt, memory-only review authority, strategy registry and
validation paths. No migration, new dependency, generic job layer or distributed
state was introduced. A continuation starts a fresh native solver process/model
seeded from the retained assignment and proven prefix; it does not serialize the
native solver's internal search tree. The user-facing operation and proposal are
retained throughout. Ordinary explicit cancellation retains its existing semantics.

## Security assessment

Continuation requires the owning account, original authenticated session and
memory-only context secret plus exact candidate fingerprint. The existing CSRF,
JSON and no-store middleware applies. Request schemas forbid session assignments
and budget overrides. Fresh input and hard-rule checks remain before acceptance.

## Performance and reliability assessment

Each explicit continuation is bounded by its captured allowance and deduplicated
by request UUID. Proven prefixes are skipped, and full coverage exits coverage
search early. Rebuilding temporal candidates still consumes some of the allowance;
no large-instance speedup or eventual optimum is promised. Parent-side fallback
protects the incumbent even if the worker fails before producing a checkpoint.

## Overall recommendation

Approve the scoped I-013 changes. The entire pre-existing working branch was not
reviewed or declared merge-ready.

## Suggested next action

Load the new application build and verify the workflow with representative planning
data. No further code-review round is required unless implementation changes.

## Working tree

Existing dirty branch: `codex/I-011-policy-teaching-strategies`. I-013 adds the
incumbent helper, continuation tests and spec/plan/verification files and extends
the existing operation/solver/client files. No commit, push or reset was performed.
