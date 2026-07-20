# FS-011 Performance Evidence

**Executed:** 2026-07-20  
**Database:** in-memory SQLite test database  
**Build:** working tree on `codex/fs-011-holiday-calendar`

## Automated reference case

The automated reference creates exactly 50 current holidays and validates 500 sessions, with every session colliding with a holiday. It also executes the existing overlap, capacity, generation-constraint, and study-window validation paths.

| Trial | Result | Threshold |
|---|---:|---:|
| 50-holiday/500-session derived alert call | 0.10 s | < 2.00 s |

Command:

```text
cd backend
.venv\Scripts\python.exe -m pytest tests/performance/test_holiday_calendar_performance.py -q --durations=1
```

Result: PASS.

## Acceptance timing still requiring an interactive environment

The quickstart's browser-level warmed CRUD trials, mutation-to-review refresh trials, and 20 selected-semester interactive loads require an acceptance database, running browser, and acceptance operator. No results are fabricated here; these remain part of the participant/manual acceptance item T059.
