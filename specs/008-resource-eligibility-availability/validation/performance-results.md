# Performance Validation Results

Date: 2026-07-15

Environment:

- Microsoft Windows 11 Education 10.0.22631
- Intel Core Ultra 7 165H, 16 cores / 22 logical processors
- 31.5 GB RAM
- Samsung PM9F1 1 TB NVMe SSD
- Python 3.12.8; Node.js 26.4.0
- SQLite in-memory automated dataset and warmed local SQLite browser dataset
- Codex in-app browser, production build flavor; browser engine version not exposed by the acceptance runtime
- Baseline commit: `a2dd7d68f5fb69dfbea8bdabad02ca777d723c34`

## Automated reference dataset

Command:

```text
cd backend
python -m pytest tests/performance/test_resource_catalog_performance.py -q
```

Result: `1 passed in 1.08s`; end-to-end command wall time `1.899s`.

The test creates exactly 100 Lecturers, 100 Rooms, 100 Courses, and 1,000 unavailability periods. It verifies the complete relational dataset load and the real planning-options response under two seconds. A separate instrumented warmed call returned 100 Courses in `0.059s` using 12 SQL statements.

## Browser view and interaction trials

All 20 representative trials became usable within two seconds: 20/20 passed, exceeding the required 19/20.

| Trial | Scenario | Duration |
|---:|---|---:|
| 1 | Schedule view | 369 ms |
| 2 | Academic Data view | 323 ms |
| 3 | Lecturers list | 312 ms |
| 4 | Rooms list | 325 ms |
| 5 | Courses list | 321 ms |
| 6 | Return to Lecturers | 319 ms |
| 7 | Lecturer search | 70 ms |
| 8 | Lecturer detail and availability | 309 ms |
| 9 | Close Lecturer detail | 296 ms |
| 10 | Alternate Room search | 153 ms |
| 11 | Restore Room search | 131 ms |
| 12 | Room detail and availability | 307 ms |
| 13 | Close Room detail | 297 ms |
| 14 | Return to Courses | 422 ms |
| 15 | Course detail and eligibility | 315 ms |
| 16 | Cancel eligibility changes | 310 ms |
| 17 | Close Course detail | 338 ms |
| 18 | Lecturer retirement list/search | 522 ms |
| 19 | Retirement assessment | 320 ms |
| 20 | Cancel retirement | 318 ms |

No browser view trial failed or was excluded. Maximum duration was `522 ms`.

## Successful mutation and refresh trials

Ten alternating Lecturer name edits were saved through the browser. Each trial waited until the refreshed list displayed the current saved value. The tenth trial restored the original name.

| Trial | Duration |
|---:|---:|
| 1 | 336 ms |
| 2 | 338 ms |
| 3 | 328 ms |
| 4 | 318 ms |
| 5 | 331 ms |
| 6 | 442 ms |
| 7 | 329 ms |
| 8 | 401 ms |
| 9 | 330 ms |
| 10 | 324 ms |

All 10/10 successful mutations showed current saved values within two seconds. No mutation trial failed or was excluded. Maximum duration was `442 ms`.

Conclusion: the documented environment satisfies SC-008 and SC-009 for the required reference dataset and warmed acceptance protocol.
