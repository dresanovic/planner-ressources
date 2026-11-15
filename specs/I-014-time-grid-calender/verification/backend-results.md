# Backend verification — I-014

Final focused run: **69 passed**, exit 0 (2026-11-15).

From `C:/Codex/planner-resource/backend`:

```powershell
.venv/Scripts/python.exe -m pytest tests/services/test_calendar_workspace.py tests/api/test_calendar_workspace.py tests/services/test_dated_intensive_windows.py tests/services/test_draft_schedule_validation.py tests/services/test_schedule_lifecycle.py -q
.venv/Scripts/python.exe -m pytest tests/performance/test_calendar_workspace_performance.py -q --basetemp=C:/Codex/planner-resource/tmp/i014-pytest-perf-approved
.venv/Scripts/python.exe -m pytest tests -q --basetemp=C:/Codex/planner-resource/tmp/i014-pytest-full-approved
```

| Gate | Result | Exit |
|---|---|---|
| Focused workspace/API/dated/validation/lifecycle | 69 passed | 0 |
| Existing workspace performance, 20 reference loads | 1 passed | 0 |
| Full backend at final backend production state | 1,119 passed, 1 skipped, 29 subtests passed | 0 |

The full run took 1,032.56 seconds. Later additions expanded test fixtures and
contract coverage; all those additions pass in the final focused run. Backend
production did not change after the full run. The skipped test and deprecation
warnings are retained in `backend-full.txt`; no skip was introduced by I-014.

Initial sandboxed full/performance attempts failed on temporary-directory
permissions. Approved runs with explicitly disposable workspace temp paths
completed. These were runner failures, not performance/acceptance passes.

Service reads preserve complete SQLite dumps. Authenticated API reads preserve
planning records and snapshots; the normal authentication session activity timestamp
is deliberately excluded from the API comparison. Existing authentication,
revision errors, validation decisions, dated precedence and snapshot behavior are
covered by unchanged regression tests. No scheduling, validation or persistence
production module was modified.

Raw results: `backend-targeted.txt`, `backend-performance.txt`, `backend-full.txt`.
