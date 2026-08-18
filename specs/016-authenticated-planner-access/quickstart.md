# Quickstart and Verification: FS-016

## Purpose

This guide defines the implementation and acceptance evidence for authenticated
planner access. It does not create production credentials or change a running
deployment. Execute implementation test-first: add the failing test for one
behavior, implement the smallest change, then keep the suite green.

## Prerequisites

- Python 3.12 and the backend development requirements.
- Node.js compatible with the repository container/toolchain and installed
  `client` dependencies.
- A temporary file-backed SQLite database for concurrency tests.
- Same hostname on both local origins when testing cookies (`127.0.0.1` with
  `127.0.0.1`, or `localhost` with `localhost`).
- HTTPS termination for remote production access. Production secure cookies are
  intentionally unusable over remote plain HTTP.

## Test-first delivery order

1. Migration and model constraints.
2. Password, startup credential, account-access, and session service tests.
3. Bootstrap/login/default-deny API tests.
4. Session replacement, expiry, invalidation, and concurrency tests.
5. Administrator account actions, transfer, and recovery tests.
6. Complete authorization-inventory and FS-015 boundary regression tests.
7. Frontend request-helper and route/fragment tests.
8. Authentication gate/pages and planner account UI component tests.
9. Full automated suites, production build, and manual browser/accessibility
   acceptance.

Do not add a production authentication bypass. Existing planner API tests use a
shared test-only current-planner fixture; public lecturer tests remain
anonymous.

## Operator credential setup

Generate a separate value for each required purpose using a cryptographically
secure 32-byte generator. The application accepts the 64-character hexadecimal
representation. Example generation commands:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

```sh
openssl rand -hex 32
```

Deliver and store the value using the operator's approved secret-handling
channel. Do not paste it into issue trackers, source files, logs, screenshots,
or this guide.

Configure only the purpose currently needed:

```text
PLANNER_BOOTSTRAP_CREDENTIAL=<64 hex characters>
PLANNER_ADMIN_RECOVERY_CREDENTIAL=<different 64 hex characters>
```

An unchanged unused value remains current across restarts. A newly configured
value replaces the previous unused value for that purpose. A consumed or
replaced value can never become current again. Remove redeemed values from
deployment configuration as operational hygiene, although database anti-replay
state remains authoritative.

Once registered, an unused current value remains redeemable even if the
environment variable is absent on a later restart; absence is not replacement.
Leaving a consumed value configured also cannot reactivate it and must not stop
the main application from starting.

## Automated verification

### Backend focused tests

Run the feature tests first:

```powershell
python -m pytest backend/tests/db/test_migrations.py -q
python -m pytest backend/tests/services/test_planner_auth.py backend/tests/services/test_planner_auth_concurrency.py -q
python -m pytest backend/tests/api/test_planner_auth.py backend/tests/api/test_planner_authorization.py -q
```

Required focused evidence:

- a fresh and FS-015 database both reach the complete `0010` schema;
- partial authentication schemas fail safely;
- password acceptance, login normalization, dummy verification, ten-attempt
  restriction, fixed 15-minute boundary, and reset behavior match the spec;
- unchanged startup values survive restarts, replacement retires old values,
  cross-purpose/replayed values fail, and concurrent redemption has one winner;
- account access expires at 24 hours, is replaceable and single-use, and creates
  no session;
- successful login leaves one session, failed login preserves an existing
  session, and every invalidation event rejects the former cookie;
- inactivity expires at 60 minutes, absolute life at 12 hours, only successful
  marked requests refresh activity, and equality counts as expired;
- bootstrap and transfer expose exactly one administrator under race/stale
  conditions;
- recovery preserves administrator identity/authority and invalidates password
  and session atomically;
- listing/error/log canaries contain no password, usable secret, or digest.

### Authorization and lecturer boundary

The inventory test must enumerate registered routes and verify every non-public
operation against all required invalid states. Run it with existing FS-015
tests:

```powershell
python -m pytest backend/tests/api/test_planner_authorization.py backend/tests/api/test_lecturer_bearer_authorization.py backend/tests/api/test_lecturer_review.py -q
```

Confirm rejected mutation requests leave database snapshots unchanged. Confirm
public terminology and all lecturer review/calendar/feedback cases still work
without a planner cookie and that a lecturer bearer never reaches a planner
operation.

### Complete backend suite

```powershell
python -m pytest backend/tests -q
```

Benchmark Argon2 verification inside the production image on both supported
architectures. Record peak memory for realistic concurrent attempts. Add a
small process-local verification semaphore only if evidence shows that the
64-MiB profile can exhaust the configured container memory.

### Frontend

```powershell
Set-Location client
npm test
npm run lint
npm run build
```

Required component/contract evidence:

- account-access fragments are removed before terminology fetch or module load
  and never reach history/storage/logs;
- planner/auth calls include credentials, unsafe calls include CSRF protection,
  activity marking is explicit, and public terminology/lecturer calls continue
  with `credentials: "omit"`;
- the planner shell never mounts before successful session inspection;
- protected `401` removes existing protected UI/data and focuses/announces the
  approved ended-session result;
- password controls clear after failed/expired/unauthorized submits;
- ordinary planners do not receive account navigation, and server `403` removes
  stale administrator UI;
- account cards expose only the approved projection and state-appropriate
  actions;
- confirmation dialogs trap/cancel/restore focus;
- one-time URLs exist only in immediate component state, are absent from live
  announcements, and clear on dismiss/replacement/navigation.

## End-to-end acceptance walkthrough

Use a disposable database and synthetic identities/secrets.

### 1. Bootstrap and default denial

1. Start without an administrator and configure one bootstrap credential.
2. Request `/` and representative planner reads/mutations anonymously; confirm
   redirect/`401`, no planner data, and no mutation.
3. Open `/bootstrap/`, establish a named administrator, and confirm no automatic
   login.
4. Retry the same credential, restart with it still configured, and attempt a
   replacement bootstrap; confirm no second account and no identity disclosure.
5. Sign in normally and complete one existing planner workflow.

### 2. Planner setup and one-current-session behavior

1. Create an inactive planner and copy the immediate setup link.
2. Dismiss the result and confirm the account list cannot reproduce the link or
   show pending/expired status.
3. Redeem once, confirm the fragment disappears before requests, and sign in.
4. Confirm the same access fails on replay and the planner cannot list/manage
   accounts.
5. Sign in from a second browser context; confirm the first context fails on its
   next protected read and the second remains current.
6. Submit a failed later login and confirm the current session remains usable.

### 3. Reset, disable, and reactivate

1. Issue reset access for the ordinary planner; confirm the old password and
   current session stop working immediately while the account remains `Aktiv`.
2. Redeem the reset, sign in, then disable the account; confirm next read,
   mutation, and login are denied and `disabledAt` is current.
3. Issue reactivation access; confirm issuance alone leaves the account
   `Inaktiv`.
4. Redeem it with a new password; confirm `Aktiv`, current `reactivatedAt`, and
   normal login.

### 4. Transfer and recovery

1. With two active accounts, confirm transfer to the other planner.
2. Verify the target immediately becomes the sole administrator and the former
   administrator remains a normal signed-in planner without account authority.
3. Run stale/competing transfer attempts and confirm exactly one administrator
   and no partial changes.
4. Configure a distinct recovery startup credential, recover the current
   administrator without selecting an account, and verify the old password and
   session fail.
5. Restart with the redeemed value still present; confirm it remains unusable.

### 5. Lecturer regression

Run valid, expired, revoked, replaced, malformed, wrong-scope, feedback, and
calendar FS-015 journeys without signing in as a planner. Then present each
lecturer credential to planner pages, reads, mutations, and account management;
all planner access must fail without changing lecturer behavior.

## Manual browser and accessibility verification

Perform this evidence in each supported browser:

- keyboard-only login, bootstrap, account access, recovery, password change,
  account creation, reset, disablement, reactivation, and transfer;
- visible focus, logical order, programmatic labels, field-linked errors,
  result announcements, dialog trap/Escape/cancel/focus restoration;
- exact safe German messages and no secret spoken by live regions;
- 360 px, the 820 px breakpoint, and 200% zoom without lost actions or
  two-dimensional ordinary-text scrolling;
- state/action meaning without color;
- close all browser windows with session restoration disabled, reopen, and
  confirm sign-in is required.

Also record the platform limitation: browsers configured to restore a prior
session may restore non-persistent cookies. Do not use unload/beacon logout as a
security claim; the server's 60-minute inactivity and 12-hour absolute limits
remain the backstops.

## Deployment verification

Build and run the production image, then verify:

- `APP_ENV=production` sets only `__Host-planner_session` with `Secure`,
  `HttpOnly`, `SameSite=Strict`, `Path=/`, and no persistence attributes;
- production emits no credentialed cross-origin CORS permission;
- remote plain HTTP cannot establish a production session cookie;
- HTTPS-terminated access can establish and use it;
- authentication/protected responses are `Cache-Control: no-store`;
- startup logs never contain configured credentials;
- the SQLite backup/restore workflow preserves accounts, anti-replay state, and
  current session digests without exposing raw secrets.

## Final verification before commit

```powershell
python -m pytest backend/tests -q
Set-Location client
npm test
npm run lint
npm run build
```

Record any unavailable command, reason, and residual risk. Implementation is not
complete until all feasible automated checks pass and the manual browser,
accessibility, browser-close, and HTTPS evidence is attached to the delivery.
