# Implementation Plan: FS-016 Authenticated Planner Access and Account Administration

**Working Branch**: `master` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from
`/specs/016-authenticated-planner-access/spec.md`

## Summary

Protect every planner page, read, and mutation with named local accounts while
leaving the existing accountless lecturer capability boundary unchanged. Add a
single direct FastAPI authentication/account service backed by four SQLite
tables, Argon2id password hashes, opaque one-row-per-account server sessions,
durable one-time startup/account-access state, transactionally enforced
exactly-one administrator behavior, and a central exact-allowlist/default-deny
middleware. Add a React authentication gate, fixed standalone authentication
routes, one shared credentialed planner request helper, and an
administrator-only responsive `Planer-Konten` view using the current German,
responsive, and accessibility patterns.

## Technical Context

**Language/Version**: Python 3.12 backend; TypeScript 6.0.2 and React JSX
frontend; Node.js 24 container build

**Primary Dependencies**: FastAPI 0.139.0, Starlette 1.3.1, SQLAlchemy 2.0.45,
Alembic 1.18.0, Pydantic 2.13.4, Uvicorn 0.49.0; React 19.2.7, React DOM
19.2.7, Vite 8.1.1; add direct `argon2-cffi` for Argon2id password hashing

**Storage**: Existing persistent SQLite database and sequential manual migration
chain; four new tables for accounts, one-time account access, one current session
per account, and startup-credential anti-replay state

**Testing**: pytest 9.1.1/FastAPI TestClient and file-backed SQLite concurrency
tests; Vitest 4.0.16 with jsdom, TypeScript build, ESLint, production Vite build;
manual supported-browser, keyboard, assistive-technology, 200%-zoom,
browser-close, HTTPS, and container verification where automation is not
available

**Target Platform**: Existing single-process non-root Linux container serving
FastAPI and the built React SPA; modern desktop/mobile browsers; HTTPS
termination required for remote production access

**Project Type**: Full-stack web application with same-origin JSON API and an
independent public lecturer capability surface

**Performance Goals**: Preserve existing planner workflow responsiveness;
session authorization uses indexed digest/account lookups; successful bootstrap
and administrator recovery remain completable within five minutes and planner
setup/sign-in within three minutes; Argon2 parameters are benchmarked in the
production image so deliberate password work does not exhaust configured memory

**Constraints**: Default-deny backend authorization; exactly one active
administrator after bootstrap; one current session per account; 24-hour
one-time access, 60-minute inactivity, 12-hour absolute session life; no email,
SSO, MFA, external identity/store, broad roles/audit, authenticated lecturers,
or browser-stored planner secrets; formal German UI, keyboard operability,
narrow viewport and 200% zoom; existing lecturer bearer behavior unchanged

**Scale/Scope**: One administrator plus a small named planner population in the
confirmed single-process SQLite deployment; four public authentication/access
surfaces, one protected password-change surface, one account-administration
view, six administrator account actions, and migration of the existing planner
API call sites to one credentialed request boundary

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- **Spec-first — PASS**: [spec.md](./spec.md) defines the approved slice,
  exclusions, seven independently testable stories, 54 functional requirements,
  ten test requirements, and measurable outcomes before production work.
- **Acceptance criteria — PASS**: Stories have independent test paths and
  Given/When/Then acceptance scenarios; clarification fixed password, retry,
  normalization, credential, session, account-state, and German wording rules.
- **Test-first — PASS**: [quickstart.md](./quickstart.md) orders model, service,
  API, concurrency, authorization, lecturer-regression, and frontend tests before
  the matching production changes. Manual exceptions are limited to browser
  cookie restoration, responsive/zoom, assistive-technology, HTTPS, and image
  architecture behavior and have explicit verification paths.
- **Simplicity and KISS — PASS**: The design stays in the existing FastAPI,
  React/Vite, SQLAlchemy, SQLite, and fixed-route structure. Four tables and one
  focused password dependency map to current requirements; no provider, role,
  repository, session UI, audit, router, or external service is added.
- **Technology fit — PASS**: Backend work remains FastAPI, frontend work remains
  React/Vite, and [planner-access.openapi.yaml](./contracts/planner-access.openapi.yaml),
  [authorization-boundary.md](./contracts/authorization-boundary.md), and
  [planner-access-ui.md](./contracts/planner-access-ui.md) define the cross-stack
  contract.
- **Delivery workflow — PASS WITH PRE-IMPLEMENTATION ACTION**: Planning artifacts
  are being prepared on `master` as a clean solo documentation change. Because
  authentication is security-sensitive and touches most planner APIs, create a
  `codex/fs-016-authenticated-planner-access` feature branch before production
  implementation unless the implementer explicitly records why a clean,
  verified solo `master` change remains appropriate.
- **Verification before commit — PASS**: Focused and full pytest, Vitest, lint,
  build, contract, manual accessibility/browser, HTTPS, secret-disclosure, and
  deployment checks are listed below and in the quickstart.

### Post-design re-check

Phase 1 introduces no constitution exception. Argon2 is a narrowly scoped
security dependency that removes custom password-hash format/upgrade code. The
shared planner request helper is justified by ten existing planner API modules
that must all apply cookies, CSRF, activity, and 401 invalidation consistently.
The direct authentication service is the established backend service boundary,
not a new generic architecture. Complexity Tracking is therefore not required.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Add one `planner_auth` schema/API/service slice,
   four direct SQLAlchemy tables in the existing model/migration system, one
   central exact-public-allowlist middleware, one HttpOnly opaque session cookie,
   and one React authentication gate plus shared planner fetch function. Store
   no raw secrets, use one boolean administrator flag with a partial unique
   index, and reuse existing transaction, card, dialog, focus, navigation,
   lecturer-fragment, and transient-copy patterns.
2. **Necessary abstractions**: The existing FastAPI router/service/schema split;
   one authentication service because password, credential, session, and
   account transitions share transaction/security invariants; one planner
   request helper because the same cookie/CSRF/activity/401 behavior applies to
   ten current API modules; one authentication gate because protected data must
   never mount before session validation; one reusable account-action dialog and
   one reusable transient one-time-access result because four concrete actions
   share those behaviors.
3. **Deliberately excluded**: Identity-provider adapters, OAuth/OIDC/SSO, email,
   MFA/passkeys, general users/roles/permissions, multiple administrators,
   external session/cache stores, JWT, repository/unit-of-work layers, event
   sourcing, detailed audit/event history, self-service forgotten-password,
   session/device UI, React Router, global state/query libraries, browser storage
   auth, lecturer account conversion, automatic credential delivery, account
   edit/delete, and planner-work attribution.

Implementation MUST NOT begin until these answers remain consistent with the
feature spec and contract artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/016-authenticated-planner-access/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- planner-access.openapi.yaml
|   |-- authorization-boundary.md
|   `-- planner-access-ui.md
`-- tasks.md                         # Created by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- planner_auth.py                 # New feature endpoints
|   |-- schemas/
|   |   `-- planner_auth.py                 # Safe request/response projections
|   |-- services/
|   |   `-- planner_auth.py                 # Password, credential, session, account transactions
|   |-- models/
|   |   `-- planning.py                     # Four direct FS-016 models
|   |-- db/
|   |   |-- migrations/
|   |   |   `-- 0010_planner_authentication.py
|   |   `-- schema.py                       # Current/pre-0010 recognition
|   |-- frontend.py                         # Exact public/protected SPA paths if classified here
|   `-- main.py                             # Startup reconciliation, router, default-deny middleware, CORS
|-- tests/
|   |-- api/
|   |   |-- test_planner_auth.py            # New
|   |   |-- test_planner_authorization.py   # New complete inventory
|   |   |-- test_lecturer_bearer_authorization.py
|   |   `-- test_lecturer_review.py
|   |-- services/
|   |   |-- test_planner_auth.py            # New
|   |   `-- test_planner_auth_concurrency.py # New file-backed races
|   |-- db/test_migrations.py
|   |-- test_main.py
|   `-- test_frontend.py
|-- requirements-runtime.txt                # Argon2 direct dependency and lock closure
|-- requirements-dev.txt
`-- README.md

client/
|-- src/
|   |-- api/
|   |   |-- plannerFetch.ts                 # New credential/CSRF/activity/401 boundary
|   |   |-- authentication.ts               # New FS-016 API contract adapter
|   |   |-- academicCatalog.ts              # Move planner calls to plannerFetch
|   |   |-- calendarWorkspace.ts
|   |   |-- conflictAwareGeneration.ts
|   |   |-- draftSchedule.ts
|   |   |-- examScheduling.ts
|   |   |-- holidayCalendar.ts
|   |   |-- lecturerReview.ts               # Planner half only; public half stays omit
|   |   |-- planningOptions.ts
|   |   |-- resourceCatalog.ts
|   |   `-- scheduleLifecycle.ts
|   |-- components/
|   |   |-- ApplicationNavigation.tsx
|   |   |-- AccountActionDialog.tsx         # New, existing dialog behavior reused
|   |   `-- OneTimeAccessResult.tsx          # New transient-only result
|   |-- pages/
|   |   |-- LoginPage.tsx                    # New
|   |   |-- BootstrapPage.tsx                # New
|   |   |-- AccountAccessPage.tsx            # New shared setup/reset/reactivation
|   |   |-- AdministratorRecoveryPage.tsx    # New
|   |   |-- PasswordChangePage.tsx           # New
|   |   `-- PlannerAccountsPage.tsx           # New
|   |-- PlannerApplication.tsx               # New auth gate
|   |-- main.tsx                             # Exact dispatch and fragment scrubbing
|   |-- App.tsx                              # Protected planner/account view state
|   `-- App.css                              # Existing visual/responsive language
|-- package.json                             # No new frontend dependency expected
`-- tests colocated with changed source files

.env.example                                  # Optional startup credential names
compose.yaml                                  # Startup credential passthrough
infrastructure/docker/
|-- Dockerfile                               # Argon2 import/build verification
`-- README.md                                # Generation, rotation, HTTPS, recovery runbook
```

**Structure Decision**: Preserve the single backend and single frontend
applications. Keep models in the repository's existing `planning.py`, use one
feature-specific backend schema/service/API group, and colocate frontend tests
with the current source-test convention. No new app, package, state layer, or
deployment service is introduced.

## Phase 0: Research Outcome

[research.md](./research.md) resolves the implementation choices for password
hashing, opaque sessions, browser-close limitations, data constraints,
transactional transfer, durable startup credentials, one-time access, default
denial, CSRF, activity semantics, route dispatch, authorization inventory, and
deployment prerequisites. There are no open design questions for task
generation.

The important platform constraint is explicit: the product can use a
non-persistent session cookie and verify close/reopen with session restoration
disabled, but no web server can reliably observe browser close, and a browser
may restore session cookies. The implementation must not claim unload/beacon
logout as a security guarantee; inactivity and absolute expiry are the server
backstops.

## Phase 1: Design Outcome

- [data-model.md](./data-model.md) defines four entities, constraints,
  projections, transitions, concurrency rules, and migration compatibility.
- [planner-access.openapi.yaml](./contracts/planner-access.openapi.yaml) defines
  the public, protected, and administrator feature operations and safe schemas.
- [authorization-boundary.md](./contracts/authorization-boundary.md) defines the
  exact public allowlist, planner default denial, lecturer separation, CSRF,
  privacy, and inventory-test method.
- [planner-access-ui.md](./contracts/planner-access-ui.md) defines fixed routes,
  auth gate, fragment handling, account cards/actions, transient links, focus,
  German wording, and responsive/accessibility behavior.
- [quickstart.md](./quickstart.md) defines test-first order, operator setup,
  automated commands, acceptance walkthroughs, manual exceptions, and
  production verification.

The installed Codex Spec Kit integration was inspected after design. This
repository version provides no `update-agent-context` script and no managed
agent-context target; `specify integration status` reports the installed Codex
integration without missing managed files. No context file was invented or
overwritten.

## Complexity Tracking

No constitution violations require an exception. The narrowly scoped Argon2
dependency and planner request helper are justified present needs in the
Simplicity Check and do not establish generic extension architecture.

## Verification Plan

### Test-first implementation evidence

For each task group, commit or retain evidence that the new/updated tests fail
for the intended behavior before production code and then pass after the
smallest implementation. Required groups:

1. migration/model constraints and partial-schema rejection;
2. password/login normalization/retry/dummy verification;
3. startup credential reconciliation, replacement, replay, bootstrap, recovery;
4. account-access issue/replacement/expiry/redemption;
5. session issue/replacement/activity/expiry/all invalidations;
6. administrator create/list/reset/disable/reactivate/transfer and stale races;
7. full API/page authorization inventory and lecturer boundary regression;
8. planner fetch/auth gate/routes/pages/account UI/privacy/accessibility.

### Focused backend commands

```powershell
python -m pytest backend/tests/db/test_migrations.py -q
python -m pytest backend/tests/services/test_planner_auth.py backend/tests/services/test_planner_auth_concurrency.py -q
python -m pytest backend/tests/api/test_planner_auth.py backend/tests/api/test_planner_authorization.py -q
python -m pytest backend/tests/api/test_lecturer_bearer_authorization.py backend/tests/api/test_lecturer_review.py -q
```

### Full automated verification

```powershell
python -m pytest backend/tests -q
Set-Location client
npm test
npm run lint
npm run build
```

Expected evidence: all existing planner behavior passes through an authenticated
test principal; every non-public route denies every invalid-session class before
mutation; FS-015 remains anonymous and passing; concurrency produces at most one
redemption/session and exactly one administrator; secret canaries are absent
from responses, logs, addresses, storage, and announcements; the frontend build
contains no new routing/state dependency.

### Manual and deployment verification

Automated jsdom tests cannot fully establish browser cookie restoration,
responsive zoom, real assistive-technology announcements, or HTTPS cookie
transport. Follow [quickstart.md](./quickstart.md) and record:

- keyboard-only and screen-reader-relevant focus/status behavior for every new
  surface and confirmation;
- 360 px, 820 px, and 200% zoom layout evidence;
- supported-browser close/reopen with session restoration disabled, plus the
  documented restoration limitation;
- production image Argon2 import and memory benchmark on supported architectures;
- exact production cookie attributes, no production credentialed CORS, HTTPS
  success, remote plain-HTTP failure, startup secret-free logs, and preserved
  backup/restore state.

Any unavailable command or check must be recorded with its reason and residual
risk before commit; it does not silently count as passed.
