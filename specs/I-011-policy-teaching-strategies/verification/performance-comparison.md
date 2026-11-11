# Teaching strategy performance comparison

Measured on 2026-11-10 with Python 3.12.8 on Windows 11. All three concrete strategies use detached copies of each identical snapshot and a two-second search allowance. No live plan or policy is accessed. The comparison suite passes **33 tests**: three harness checks, 18 search comparisons, six real spawned 1/20-course runs, three expired-deadline/cancellation runs and three active-budget runs.

All 18 search candidates passed independent exact validation and covered the full selected demand, with zero remaining LE. These small fixtures establish neither a universal runtime advantage nor preference optimality for the heuristics. Values below are one measured run, not a statistical benchmark; 0.000 reflects clock resolution.

| Scenario | Algorithm | Scheduled / required LE | Search seconds | Termination |
|---|---|---:|---:|---|
| single | standard | 6 / 6 | 0.031 | standard_completed |
| single | cohort | 6 / 6 | 0.047 | heuristic_completed |
| single | lecturer | 6 / 6 | 0.047 | heuristic_completed |
| cohort_competition | standard | 12 / 12 | 0.344 | standard_completed |
| cohort_competition | cohort | 12 / 12 | 2.000 | deadline |
| cohort_competition | lecturer | 12 / 12 | 0.281 | heuristic_completed |
| shared_lecturer | standard | 12 / 12 | 0.063 | standard_completed |
| shared_lecturer | cohort | 12 / 12 | 0.219 | heuristic_completed |
| shared_lecturer | lecturer | 12 / 12 | 0.344 | heuristic_completed |
| intensive | standard | 12 / 12 | 1.968 | standard_completed |
| intensive | cohort | 12 / 12 | 2.000 | deadline |
| intensive | lecturer | 12 / 12 | 2.000 | deadline |
| partial_week | standard | 6 / 6 | 0.016 | standard_completed |
| partial_week | cohort | 6 / 6 | 0.000 | heuristic_completed |
| partial_week | lecturer | 6 / 6 | 0.000 | heuristic_completed |
| twenty | standard | 40 / 40 | 0.062 | standard_completed |
| twenty | cohort | 40 / 40 | 0.062 | heuristic_completed |
| twenty | lecturer | 40 / 40 | 0.062 | heuristic_completed |

The dated-intensive case exposes a quality trade-off within this allowance: Standard reaches daily variety 2, while both heuristics retain variety 1 when their deadline arrives. A separate ten-second deterministic regression verifies that both heuristics can revisit groups and reach variety 2. Full coverage does not establish preference optimality. Standard retains its own objective profile; heuristic preference proofs remain unproven, even on early completion. Profiles should not be treated as interchangeable scores.

`performance-comparison.json` retains snapshot SHA256, weekly cohort and lecturer LE maps (including relevant fixed teaching), remaining LE, intensive instruction, variety, ordered objective/proof evidence, sound coverage bounds and environment. Search timings exclude worker startup, HTTP and saving.

| Algorithm | Active two-second run elapsed | Budget exhausted | Active cancellation acknowledgement |
|---|---:|---|---:|
| standard | 2.031 s | True | 0.094 s |
| cohort | 2.000 s | True | 0.218 s |
| lecturer | 2.000 s | True | 0.219 s |

All six spawned 1/20-course dispatch runs returned independently hard-valid full coverage, acknowledged dispatch within one second and observed phase/checkpoint/result intervals within five seconds. All three already-expired deadlines returned no result. Active cancellation acknowledged within 0.219 seconds. Active-budget checks include process startup in the original absolute allowance and allow one second of finalization tolerance; a faster early completion is also valid.

Separate connected evidence:

- `connected-acceptance.json`: all three selectors × 1/20 courses through isolated endpoint preparation, Start, real worker, review, accepted save and post-commit cancellation reconciliation.
- `http-latency.json`: actual loopback TCP/Uvicorn Start and immediate cancellation for all six combinations; maximum Start 0.031 s and cancellation 0.094 s, with saved planning tables unchanged. Immediate cancellation can precede worker startup; the active-worker test above covers cancellation during search.
- Save latency and long-running statistical performance distributions are not measured here.

Reproduce from the repository root:

```powershell
$env:PYTHONPATH = 'backend'
$env:TEACHING_COMPARISON_REPORT = 'specs/I-011-policy-teaching-strategies/verification/performance-comparison.json'
backend/.venv/Scripts/python.exe -m pytest backend/tests/performance/test_teaching_strategy_comparison.py -q
```

Timing and bounded preference results can vary with machine load. Acceptance asserts validity, coverage accounting, control limits and truthful proof evidence rather than requiring one algorithm always to win.
