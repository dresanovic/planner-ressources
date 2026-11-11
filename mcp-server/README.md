# Local Planner Resource MCP server

```text
Codex <-> local MCP process (stdio) --HTTP(S)--> planner-resource --> database
```

This independent Python package runs on the computer running Codex. It uses
the existing authenticated HTTP API; it never opens the application database.
No MCP port, Docker service or shared MCP deployment is needed.

## Install (PowerShell, from the repository root)

```powershell
py -3.12 -m venv mcp-server/.venv
mcp-server/.venv/Scripts/python.exe -m pip install -e './mcp-server[test]'
```

Python 3.11+ is supported. Dependencies are isolated from the backend. The
package deliberately uses the supported MCP Python SDK 1.x API (`mcp<2`).

## Connect Codex

Start the application normally. Use an existing, activated planner account with
a password; bootstrap and account administration remain in the application.
Make these environment variables available to the Codex process before launching it:

- `PLANNER_LOGIN_NAME`: planner login name.
- `PLANNER_PASSWORD`: planner password, supplied securely through your local environment.
- The API URL is configured in the example below; change it to the application server URL.

Merge [codex-config.example.toml](codex-config.example.toml) into your Codex
`~/.codex/config.toml`. Adjust the absolute Python executable path for your
checkout and set `PLANNER_API_URL` to the application origin, for example
`https://planner.example.org`. Use HTTP only for loopback development. A URL
path prefix is supported, but do not append `/api`. Do not put passwords in the
configuration file or commit them. Restart Codex so it receives the environment
and loads the server. Codex starts/stops the local process itself.

On Windows, if a `PLANNER_*` variable is absent from the process environment,
the bridge also reads that variable from the current user's saved environment
(`HKEY_CURRENT_USER\Environment`). This supports Codex processes started before
the variables were added. Process variables take precedence, including explicitly
empty values. No machine-level variables or other registry settings are read.
An already failed MCP connection still needs to be reconnected or restarted.

Manual startup is also possible once the variables are set:

```powershell
$env:PLANNER_API_URL = 'http://127.0.0.1:8000'
mcp-server/.venv/Scripts/python.exe -m planner_resource_mcp.server
```

The process speaks MCP on stdin/stdout and waits for a client. Startup errors
go to stderr. There is no OpenAI API key requirement.

## Tools and workflow

| Tool | Purpose |
| --- | --- |
| `list_cohorts` | Paginated active cohorts; optional name search |
| `get_planning_options` | Semesters, courses, cohorts and resource/window options |
| `get_course_constraints` | Course planning dates and teaching windows |
| `get_schedule_lifecycle` | Working revision and current state token |
| `get_saved_plans` | Saved semester draft sessions and validation alerts |
| `create_working_revision` | Create a working revision using a current state token |
| `save_plan_session` | Persist one new session through the existing API |
| `update_plan_session` | Persist edits to one saved session |

Example request to Codex: “Retrieve the cohorts and planning options for this
semester, read the course constraints and existing plans, then save the agreed
teaching sessions to the current working revision.”

Read the lifecycle before writing. If a working revision must be created, pass
its current `expected_state_token` to `create_working_revision`. Use the returned
working revision ID as `schedule_revision_id` in session saves. Dates use
`YYYY-MM-DD`, times use `HH:MM`, and units are positive whole numbers.

Each save commits one session immediately. Multiple calls are **not** an atomic
plan replacement. Inspect the returned `draftSchedule` and `validationAlerts`;
the application can save a session with nonblocking warnings. All existing
authentication, lifecycle guards and domain validation remain in effect. The
bridge provides no publication, deletion, administration or SQL tools.

The bridge logs in lazily and holds its session cookie in memory. Session
revocation/expiry is reported to Codex; restart the MCP server after resolving
authentication. HTTP validation and conflict codes are returned as MCP tool
errors. Redirects and automatic write retries are disabled. After a timeout or
connection failure, retrieve saved plans before retrying because the original
write may have committed. HTTPS certificates are verified normally.

## Verify

```powershell
mcp-server/.venv/Scripts/python.exe -m pytest mcp-server/tests -q
```

Tests exercise cookie authentication, HTTP payloads and failures, tool schemas,
and a real stdio MCP initialize/list/call exchange with a disposable HTTP server.
No live planner records or credentials are used.

CI additionally runs `mcp-server/tests/backend_contract.py` with the backend
dependencies installed and `PYTHONPATH=backend`. This exercises the actual
FastAPI login, cohort/options reads, session save/edit/readback, and stale
revision rejection against an isolated in-memory database. With the two local
environments above, run the same contract test in PowerShell as follows:

```powershell
backend/.venv/Scripts/python.exe -c "import sys; sys.path.extend(['backend','mcp-server/src','mcp-server/.venv/Lib/site-packages']); import pytest; raise SystemExit(pytest.main(['mcp-server/tests/backend_contract.py','-q']))"
```

Protocol/setup references: [Codex MCP configuration](https://developers.openai.com/codex/mcp/)
and [official MCP Python SDK 1.x](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
