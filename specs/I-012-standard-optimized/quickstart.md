# Standard Optimized

The live installation policy remains unchanged. To use the extension:

1. Finish active runs/reviews, then deploy/restart the updated backend once so startup can apply migration 0016. Existing saved plans and receipts remain intact.
2. In `config/optimization/policy.json` set `activeAlgorithm` to `standard_optimized`, preserving the installation's budget values. `config/optimization/policy.standard-optimized.example.json` is a valid example. The explicit deployment policy-path override still takes precedence.
3. Refresh the client before starting a new run. Prepare a selection; the interface must show “Standard optimiert”. Run, inspect the distribution/proof evidence and explicitly accept the whole result.

Switch back by setting `activeAlgorithm` to `standard`. New preparations read the policy; existing runs retain their captured settings. A policy change between preparation and Start requires preparation again.

The extension targets even cumulative teaching units over each course's feasible weeks, after higher-priority coverage/intensive/variety/conflict values are fixed. Existing effective course date boundaries, holidays, excluded dates, protected bookings and resource constraints still govern feasibility. Narrow a course's effective teaching period if teaching should end before the semester end.

Stage weights reserve time for distribution and roll unused time forward. A bounded stage's best feasible value is frozen before lower objectives; later proofs can therefore be conditional. Full coverage stops coverage proof search immediately because it reaches the mathematical hard cap. Improved spread is a preference, not a guarantee, and neither coverage nor runtime is guaranteed to improve over Standard on every input.

The new algorithm always requires review, even when every objective is proved. It uses the existing independent candidate validation, atomic save, stale-input rejection, cancellation, policy snapshot and navigation behavior. Browser refresh/closure still discards live review authority. No live data or policy must be used for automated tests.
