# User Story 1 evidence

Date: 2026-07-17. Environment: Windows 11, Python 3.12.8, SQLite, OR-Tools 9.15.6755, Node/Vite client stack from the repository lockfile.

- `python -m pytest tests/services/test_semester_optimization.py -q`: passed 6 tests. The request-order counterexample schedules the larger competing course, resource assignments are eligible and deterministic, continuity changes are zero, fixed/unavailable candidates are removed, and the same fixture returned an identical signature across 20 runs.
- `python -m pytest tests/services/test_conflict_aware_generation.py tests/api/test_conflict_aware_generation.py -q`: passed preparation, canonical date deduplication, snapshot, complete save, default-constraint, confirmation, proof-failure, and stale tests.
- Client focused suite: passed typed prepare/generate requests, loading/selection behavior, result rendering, and page integration.

Observed optimums: the one-slot 2-unit/4-unit counterexample returns 4 total units with `{course 1: 0, course 2: 4}`; the independent two-course API fixture returns 16/16 units and two complete saved drafts. No generated lecturer, room, or cohort overlap is accepted.
