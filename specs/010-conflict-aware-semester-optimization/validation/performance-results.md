# Reference performance evidence

Date: 2026-07-17. Fixture: deterministic 20 Courses × 30 requested units = 600 units, three weekly windows, 500 fixed semester sessions, SQLite/in-memory solver boundary. Hardware/platform: Windows 11 10.0.22631, Intel64 Family 6 Model 170 Stepping 4. Python 3.12.8; OR-Tools 9.15.6755.

All six lexicographic stages returned `OPTIMAL`; each run returned 600 units.

| Run | Wall seconds | Solver-reported ms |
|---:|---:|---:|
| 1 | 10.142 | 10141 |
| 2 | 10.132 | 10141 |
| 3 | 10.147 | 10139 |
| 4 | 9.994 | 10000 |
| 5 | 9.831 | 9827 |

Five of five runs completed within 30 seconds (100%); maximum was 10.147 seconds, below 60 seconds. The automated performance acceptance test also passed independently in 12.75 seconds.
