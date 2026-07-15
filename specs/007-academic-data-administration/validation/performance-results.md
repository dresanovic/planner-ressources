# FS-007 Performance Results

Date: 2026-07-15 (Europe/Vienna)

## Reference environment

- OS: Microsoft Windows 11, build 10.0.22631.7219
- CPU: Intel64 Family 6 Model 170, stepping 4 (host model/cores were not exposed to the workspace)
- RAM: not exposed to the workspace
- Storage: local workspace storage; media type not exposed to the workspace
- Browser: Codex in-app Chromium browser (exact version not exposed)
- Database: SQLite, in-memory for the repeatable timing test; file-backed SQLite for browser validation
- Python: 3.12.8
- Node.js: 26.4.0
- Build identifier: repository base `233fbac` plus the uncommitted FS-007 working tree
- Dataset: exactly 100 Semesters, Cohorts, Courses, Study Types, and Study Type Time Windows; one reusable read-only Lecturer and Room
- Network: local in-process HTTP acceptance client, no artificial latency

## Automated timing protocol

Command: `python -m pytest tests/performance/test_academic_catalog_performance.py -q -s`

The automated protocol warms the catalog, alternates paginated 100-record list loads with valid revisioned saves for 20 administration trials, then performs 10 valid Course mutations followed by Semester-filtered planning-option reads. Durations are in seconds.

| Trial | Administration | Trial | Mutation + planning refresh |
|---:|---:|---:|---:|
| 1 | 0.062544 | 1 | 0.039897 |
| 2 | 0.014494 | 2 | 0.029346 |
| 3 | 0.041175 | 3 | 0.025881 |
| 4 | 0.007696 | 4 | 0.023584 |
| 5 | 0.097013 | 5 | 0.023222 |
| 6 | 0.008707 | 6 | 0.024776 |
| 7 | 0.119584 | 7 | 0.027373 |
| 8 | 0.010672 | 8 | 0.026738 |
| 9 | 0.066103 | 9 | 0.020231 |
| 10 | 0.007874 | 10 | 0.052773 |
| 11 | 0.040529 |  |  |
| 12 | 0.007207 |  |  |
| 13 | 0.072482 |  |  |
| 14 | 0.008160 |  |  |
| 15 | 0.139279 |  |  |
| 16 | 0.009099 |  |  |
| 17 | 0.056571 |  |  |
| 18 | 0.011268 |  |  |
| 19 | 0.045619 |  |  |
| 20 | 0.007785 |  |  |

No trials were excluded.

## Results

- SC-008 automated threshold: PASS — 20/20 administration trials (100%) completed within 2 seconds; required threshold is at least 19/20.
- SC-007 automated threshold: PASS — 10/10 mutation-to-planning refresh trials completed within 2 seconds.
- Browser smoke validation: PASS — create feedback, canonical list refresh, delete dialog focus entry, Escape close with focus return, permanent delete refresh, and the narrow 390×844 layout were verified against file-backed SQLite. At the narrow width the catalog grid stacked to one column, all record actions remained visible, and document width did not overflow.

The repeatable raw timings measure the local backend contract boundary, while the browser pass verifies UI usability and refresh behavior. Exact end-to-end browser timing instrumentation was not available in the bundled browser surface; this limitation should be considered if acceptance requires a separately instrumented production-like browser benchmark.
