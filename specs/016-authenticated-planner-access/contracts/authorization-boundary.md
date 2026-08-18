# Authorization Boundary Contract

## Purpose

FS-016 changes the default planner boundary from anonymous access to denial.
Every API or page is public only when explicitly listed here. All near-miss
paths, newly registered planner operations, reads, and mutations inherit
planner-session protection.

## Request classifications

The authentication middleware classifies requests before FastAPI route
validation or business logic.

### Public operations

| Method | Exact path | Authority | Notes |
|---|---|---|---|
| `GET` | `/health` | None | Health status only; no planner or identity data |
| `GET` | `/api/public/ui-terminology` | None | Existing terminology contract; `credentials: omit` |
| `GET` | `/api/public/lecturer-review` | Lecturer bearer | Existing FS-015 scope unchanged |
| `GET` | `/api/public/lecturer-review/calendar` | Lecturer bearer | Existing FS-015 scope unchanged |
| `POST` | `/api/public/lecturer-review/feedback` | Lecturer bearer | Existing FS-015 scope unchanged; no planner CSRF header |
| `POST` | `/api/auth/login` | None | JSON and `X-CSRF-Protection: 1`; generic failure |
| `POST` | `/api/auth/bootstrap` | Startup bootstrap credential | Only while no administrator exists |
| `POST` | `/api/auth/account-access/redemption` | One-time account access | Purpose/account resolved from opaque secret |
| `POST` | `/api/auth/administrator-recovery` | Startup recovery credential | Targets existing sole administrator only |

Static assets, `/login/`, `/bootstrap/`, `/account-access/`,
`/administrator-recovery/`, and `/lecturer-review/` may load without a planner
session because they contain no protected planner data. Account-access fragments
must be removed before a network request or module load.

### Authenticated planner operations

The following operations and every existing planner API require a valid current
session for an active account:

- `GET /api/auth/session`
- `POST /api/auth/logout`
- `POST /api/auth/password-change`
- all academic catalog, resource catalog, holiday, schedule generation,
  planning option, exam planning, draft schedule, schedule lifecycle, calendar
  workspace, publication, and planner-side lecturer-review APIs;
- every future `/api/**` operation not added to the exact public table above.

Unsafe requests also require `X-CSRF-Protection: 1`. A deliberate foreground
request may carry `X-Planner-Activity: user`; only a successful protected
response with that marker refreshes inactivity. Initial session inspection,
automatic loads, and background work omit the activity marker.

Planner HTML entry paths, including `/`, require a valid planner session at the
production FastAPI boundary and redirect to `/login/` without exposing planner
data. The React authentication gate performs the equivalent check in Vite
development and never mounts the existing planner shell before success.
FastAPI documentation paths (`/docs`, `/redoc`, and `/openapi.json`) are also
protected as planner surfaces or disabled in production; programmatic
`app.openapi()` remains available to the test inventory.

### Administrator-only operations

These operations require both a valid planner session and transaction-time
confirmation that the account remains the sole administrator:

- `GET /api/planner-accounts`
- `POST /api/planner-accounts`
- `POST /api/planner-accounts/{accountId}/setup-access`
- `POST /api/planner-accounts/{accountId}/reset-access`
- `POST /api/planner-accounts/{accountId}/disable`
- `POST /api/planner-accounts/{accountId}/reactivation-access`
- `POST /api/planner-accounts/{accountId}/administrator-transfer`

Frontend navigation visibility is convenience only. The backend remains
authoritative, rechecks administrator state inside each write transaction, and
returns `403` without an account projection when authority is absent or was
transferred.

## Credential separation

| Credential | Transport | Accepted on | Never accepted on |
|---|---|---|---|
| Planner session | HttpOnly same-site cookie | Protected planner/API operations | Lecturer capability authorization |
| Lecturer capability | `Authorization: Bearer` | Exact FS-015 public lecturer operations | Planner pages, planner APIs, account administration |
| Account access | JSON body after fragment scrubbing | Exact redemption operation | Login, planner APIs, other accounts |
| Bootstrap startup access | JSON body | Exact bootstrap operation before first administrator | Recovery, login, planner APIs |
| Recovery startup access | JSON body | Exact recovery operation for the sole administrator | Bootstrap, other accounts, transfer, planner APIs |

A stored lecturer bearer credential on any planner API receives planner denial
and is never converted into planner identity. If both a lecturer bearer and a
planner cookie are presented to a planner operation, the lecturer credential
causes denial; credentials cannot be combined to widen authority. Public
lecturer operations ignore planner cookies and retain their bearer-only scope.

## Session rejection behavior

Missing, malformed, unknown, expired, replaced, or invalidated sessions, and
sessions belonging to inactive/disabled accounts, produce the same `401`
planner-session outcome:

- no route validation or mutation runs;
- no protected response data is returned;
- the presented cookie is cleared;
- the response is `Cache-Control: no-store`;
- the React gate removes protected components/data and presents
  `Ihre Sitzung ist beendet. Melden Sie sich erneut an.`

An account-management request from an authenticated ordinary planner produces
`403` and no account listing or target-state information. After transfer, the
former administrator remains a valid planner but immediately loses the account
page and management API authority.

## CSRF and origin rules

- State-changing planner/authentication operations use JSON only and require
  `X-CSRF-Protection: 1`.
- No state change is implemented as `GET`.
- Production sends no cross-origin credentialed CORS permission.
- Development allows credentials only from exact supported Vite origins using
  the same host spelling on frontend and backend (`localhost` with `localhost`
  or `127.0.0.1` with `127.0.0.1`). Allowed methods and headers are explicit.
- Existing lecturer bearer operations remain exempt from cookie CSRF handling.

## Response privacy

Authentication, account-management, and protected responses use
`Cache-Control: no-store`. Account listings and diagnostics never serialize:

- passwords or password hashes;
- login counters or block boundaries;
- session cookies, session digests, timestamps, or device details;
- startup credential values/digests/state;
- one-time credential digests or historical/pending access state.

The only usable account-access secret appears once in the immediate successful
creation/reset/reactivation response. Live-region announcements state only that
access was created or copied and never contain the URL or credential.

## Authorization inventory test

The backend test suite builds an operation inventory from the registered
FastAPI/OpenAPI routes. It subtracts only the exact public method/path entries in
this contract, then verifies every remaining planner operation denies before
validation and before database mutation for:

1. no cookie;
2. malformed/unknown cookie;
3. inactivity-expired cookie;
4. absolute-expired cookie;
5. replaced cookie;
6. inactive/disabled account;
7. stored lecturer bearer credential.

The test substitutes valid path parameters and compares database snapshots for
rejected mutation attempts. A route added later is protected by middleware and
fails the public-inventory review unless deliberately added to this document and
the exact allowlist.
