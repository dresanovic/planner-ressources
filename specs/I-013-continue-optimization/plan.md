# Implementation and verification

Reuse the current operation receipt, memory-only proposal, worker boundary and
strategy implementations. A continuation endpoint carries a unique request ID,
context secret and candidate fingerprint. The same live operation grants another
captured budget; no migration or new dependency is needed. The solver process may
be recreated after its previous allowance, but search is seeded from the retained
proposal and its proven prefix rather than an empty schedule.

Simplicity check: use a shared exact-model incumbent hint/lexicographic constraint
helper, existing heuristic best-state repair, and existing client polling. No
persistent solver serialization, distributed execution or planner budget controls.

The working branch already contains related uncommitted strategy implementation;
preserve those changes and extend it in place without reset, commit or push.

Test first: service tests for continuation identity/replay, stale inputs, fallback
and strategy seeding; exact solver tests for preserved quality and proven-prefix
continuation; client tests for the label and continuation API action. Run relevant
backend service/API tests, frontend tests, type/build and lint, then inspect changes
using code-review. Update operator/user guidance for the new behavior.
