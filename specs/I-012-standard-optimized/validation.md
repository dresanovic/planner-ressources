# I-012 validation — 2026-11-10

Implemented the separate `standard_optimized` strategy and `standard-optimized-v1`
proof profile through the existing registry, worker, validation, review and save
workflow. The live policy remains `standard`, 900/1800 seconds. No live database
migration, server restart, live schedule write or policy activation was performed
by this implementation.

## Behavior

On the same detached eight-week course (8 LE, fixed 2-LE sessions):

| Strategy | Dates | Scheduled LE |
|---|---|---|
| Standard | 07.09, 14.09, 21.09, 28.09.2026 | 8 |
| Standard optimiert | 07.09, 21.09, 05.10, 19.10.2026 | 8 |

Both completed with full proof on this small fixture. This demonstrates the new
distribution preference, not a universal improvement guarantee. Tests also cover
blocked dates, protected occupancy, coverage before distribution, mathematical
full-coverage proof, stage budget reservation, deadline/checkpoint cancellation,
conditional lower-priority proof and explicit atomic acceptance.

## Verification

- Red-first new service tests failed because the strategy was absent.
- Initial policy/real-worker HTTP/migration matrix: **110 passed**, including
  all four selectors at 1/20 courses, captured settings after policy deletion,
  exact review/save and schema preservation/idempotence/downgrade refusal.
- Standard baselines, strategy lifecycle, worker and operation protections:
  **133 passed**; additional interruption/conditional acceptance checks:
  **3 passed**. Lifecycle fixtures use `allow_unproven=True`, matching the real
  worker contract, because a reserved stage allowance can leave proof unfinished.
- Broad backend command: `.venv/Scripts/python.exe -m pytest tests
  --ignore=tests/performance -q --maxfail=2
  --basetemp=../.tmp/standard-optimized-backend-all`:
  **1082 passed, 29 subtests passed**, 358.62 seconds.
- Latest-source compatibility command: pytest over `test_standard_optimized.py`,
  `test_teaching_strategies.py`, `test_teaching_strategy_baselines.py`,
  `test_teaching_strategy_acceptance.py` and `test_optimization_continuation.py`:
  **36 passed**, including actual spawned-worker dispatch and continuation.
- Latest frontend suite: **70 files, 617 tests passed**, using portable
  Node **24.22.2** in `.tmp/node-v24.22.2-win-x64`.
- Full frontend ESLint, TypeScript (`tsc -b`), Vite production build and
  whitespace checks passed. Backend deprecation warnings remain non-failing.

All test databases/policies are disposable workspace-local fixtures. Process and
temporary-directory tests used approved sandbox escalation. No automatic review
rejection occurred. Long comparative performance benchmarks and a full live
cohort rerun were not performed; coverage and runtime are not guaranteed to beat
Standard on every input.

## Source isolation and concurrent changes

This feature did not write `semester_optimization.py`. Its SHA256 at the start
and the completed isolation checks was
`439a74caafeeafb9978545b314256d56d30284b58f5f373ae433bb87e3d213ce`.
The new module imports Standard's existing legality/candidate/model helpers and
types; only orchestration is copied and extended.

During the broad verification run, another process implemented I-013 continuation
and changed Standard, the worker, operations, client files and the extension's
optional incumbent support. Those changes were preserved. Consequently the final
working-tree Standard file is not claimed byte-identical to the initial hash.
The broad test collection preceded those concurrent additions; the fresh 36-test
backend compatibility pass and latest full frontend/typecheck/build/lint passes
checked their integration. Existing completed Standard baselines passed there.

Code-review scope covered the extension, selector/profile registration, migration,
proof serialization, explicit review and current compatibility. No unresolved
material finding remains within I-012's scope. Activation instructions are in
[quickstart.md](quickstart.md); migration 0016 must run on backend startup before
selecting the new algorithm.
