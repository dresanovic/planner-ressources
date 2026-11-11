# Code Review

## Scope reviewed

Local MCP package, its Codex configuration example, setup documentation, root
README integration link, and the new MCP CI job. Existing unrelated worktree
changes are outside this review.

## Context used

Requested prototype topology: Codex launches a local MCP process; that process
retrieves cohorts and saves plans through the application HTTP API. Existing
planner authentication, CSRF, manual-session and lifecycle API contracts were
used without backend changes.

## Verification performed

The original 17 tests passed together, covering cookie authentication, prefixed URLs,
invalid URLs, API errors, timeout handling, typed inputs, tool annotations,
real stdio initialization/discovery/calls, and a real FastAPI contract test
against an isolated in-memory database. The latter checks login, cohort/options
and constraint reads, session creation/editing/readback, and stale revision
rejection without an additional write. Windows named-pipe creation required
running the combined test command outside the filesystem sandbox. Two existing
backend dependency deprecation warnings remain. `git diff --check` passed.

The Windows startup follow-up adds three regression tests; all 19 bridge tests
pass. A live stdio probe using the configured command with both credential
variables deliberately removed from the child environment completed the
handshake, discovered eight tools and retrieved ten active cohorts. This verifies
the saved-user-variable fallback independently of the earlier explicit injection.

## Findings

No material findings in the reviewed scope. No critical, high, medium or low
findings, and no required corrective follow-up.

## Requirement traceability

The stdio entry point implements local process hosting. The HTTP client and
eight tools implement cohort/context retrieval and draft-session persistence.
No database access, application-server MCP deployment or shared endpoint is
introduced. Setup is supplied as a reviewable configuration example.

## Test assessment

Protocol, transport errors and real application persistence are covered. CI is
configured to run both suites; hosted CI itself has not been run here. Tests
use disposable data and do not modify live planner records.

## Architecture and design assessment

An isolated Python package keeps MCP dependencies out of the backend runtime.
Each session save commits independently using existing application behavior.
Atomic replacement of an entire plan is outside the implemented prototype.

## Security assessment

Credentials come from the process environment, or on Windows from the current
user's saved environment when absent from the process, and are absent from tool schemas
and configuration examples. Session cookies stay in process memory. Remote
HTTP is rejected in favor of verified HTTPS; redirects are disabled. The server
exposes no publication, SQL, deletion or account-administration tools.

## Performance and reliability assessment

HTTP requests have bounded timeouts; access is serialized around one cookie
session. Writes are not retried automatically, and failures instruct callers
to read saved state before retrying an uncertain write. Existing lifecycle
revision checks remain authoritative. Large semester responses retain the
application API's current response size behavior.

## Overall recommendation

Approve within the prototype scope.

## Suggested next action

Local deployment connectivity has now been verified with the configured planner
account, including startup without inherited credentials. Reconnect/restart Codex
to discard an already failed MCP connection and verify native tool availability
in a new chat. Native Codex tool registration after restart remains a user-side
check. No refactor is required.
No commit or push was performed.
