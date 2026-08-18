# Research: FS-016 Authenticated Planner Access and Account Administration

## Decision 1: Keep authentication application-owned and local

**Decision**: Add local named planner accounts to the existing FastAPI and
React/Vite application. Do not add an identity-provider adapter, role framework,
separate authentication service, or external store.

**Rationale**: The slice explicitly excludes SSO, email, automated provisioning,
and broad roles. The deployed product is one application process with one
persistent SQLite database, so a direct service and API module fit the present
architecture and operational boundary.

**Alternatives considered**:

- SSO, LDAP, or an external identity provider: outside scope and creates a
  dependency the recovery workflow must not require.
- A generic authorization framework: unnecessary for one planner capability and
  one additional singleton administrator authority.
- A separate authentication process or database: adds deployment and failure
  modes without satisfying a current requirement.

## Decision 2: Use Argon2id for human passwords

**Decision**: Add the focused `argon2-cffi` runtime dependency and use its
high-level `PasswordHasher` with the RFC 9106 low-memory Argon2id profile: 64
MiB, three iterations, four lanes, a 16-byte salt, and a 32-byte result. Rehash
after a successful login when the library reports that the stored parameters
are outdated.

**Rationale**: Passwords are human-selected and require a memory-hard password
hash. The library owns salt generation, encoded-hash validation, constant-time
verification, and parameter migration. This is less application-specific
security code than designing and maintaining a custom `hashlib.scrypt`
serialization and upgrade format. Benchmark the production container and, only
if needed, cap concurrent verification work with a small process-local
semaphore.

For an unknown, inactive, passwordless, or temporarily blocked account, perform
one verification against a precomputed dummy Argon2 hash before returning the
same generic login failure. Never log or serialize a submitted password or a
stored password hash.

**Alternatives considered**:

- `hashlib.scrypt`: avoids a package, but requires custom encoding, parsing,
  parameter validation, versioning, and rehash logic.
- bcrypt: introduces password-length handling that the accepted 128-character
  policy would have to special-case.
- Passlib or a multi-scheme facade: legacy hash migration is not a present need.
- Fast hashes such as SHA-256: unsuitable for human-selected passwords.

References: [argon2-cffi high-level API](https://argon2-cffi.readthedocs.io/en/stable/api.html),
[RFC 9106](https://www.rfc-editor.org/rfc/rfc9106.html).

## Decision 3: Store opaque sessions server-side

**Decision**: Generate a session value with `secrets.token_urlsafe(32)`, store
only its SHA-256 digest, and place the raw value in an HttpOnly cookie. Each
account has at most one session row; successful login atomically replaces that
row. Production uses `__Host-planner_session` with `Secure`, `HttpOnly`,
`SameSite=Strict`, `Path=/`, no `Domain`, and no `Expires` or `Max-Age`.
Development over local HTTP uses the non-prefixed `planner_session` name.

The server validates the current digest, active account state, 60-minute
inactivity boundary, and 12-hour absolute boundary on every protected request.
Logout, password change, reset issuance, disablement, recovery, and replacement
delete the current session row. Authentication and protected responses carry
`Cache-Control: no-store`; rejected cookies are cleared.

**Rationale**: Server-side opaque sessions directly support immediate
invalidation and the one-current-session rule. A unique account foreign key is
the database backstop against concurrent sessions.

**Alternatives considered**:

- JWT or signed client-side sessions: immediate invalidation would require an
  additional revocation store and would not be simpler.
- Browser storage bearer tokens: expose credentials to JavaScript and risk
  mixing planner authentication with lecturer bearer capabilities.
- A session-management UI: explicitly outside scope.

References: [Python `secrets`](https://docs.python.org/3.12/library/secrets.html),
[Starlette cookie API](https://www.starlette.io/responses/#set-cookie).

### Browser-close platform constraint

A non-persistent cookie is the simplest feasible implementation of
browser-close behavior, but browsers may restore session cookies when session
restoration is enabled, and the server receives no reliable browser-close
event. `beforeunload`, `pagehide`, and close-time beacons are not dependable
security controls and can also fire during refresh or navigation.

The plan therefore applies normal browser-session-cookie semantics, verifies
close/reopen with session restoration disabled in supported-browser acceptance
testing, and retains the 60-minute inactivity and 12-hour absolute server
limits as backstops. A strict claim that a copied former cookie becomes invalid
at the instant a browser process closes is not technically enforceable by a web
application. This limitation must remain visible in implementation evidence and
release notes rather than being represented as a server guarantee.

Reference: [MDN session-cookie restoration note](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#expiresdate).

## Decision 4: Use four purpose-specific tables, not a role model

**Decision**: Add `planner_accounts`, `planner_account_access`,
`planner_sessions`, and `planner_startup_credentials` in migration `0010`.
Represent administrator authority with an `is_administrator` flag on the
account, protected by a partial unique index and an active-administrator check.

**Rationale**: Four small tables map directly to the four product entities that
require persistence. A boolean plus a partial unique index is simpler than a
role/permission schema or a separate singleton assignment table. Service
transactions enforce the post-bootstrap lower bound of one administrator; the
unique index enforces the upper bound of one.

**Alternatives considered**:

- General users, roles, permissions, and join tables: no broad roles or multiple
  administrators are permitted.
- A separate administrator singleton table: valid, but adds a fifth entity and
  extra joins for a single boolean authority.
- Event/audit tables: detailed authentication history is explicitly excluded.

## Decision 5: Make transfer and credential use transactional

**Decision**: Reuse the repository's existing SQLite critical-write pattern:
claim the authoritative row with a no-op `UPDATE`, reload and recheck current
state inside the transaction, apply the complete state change, then commit
once. Use this for bootstrap, login replacement, one-time redemption,
disablement/reset, recovery, and administrator transfer.

Transfer claims both involved accounts, confirms the requester remains the
administrator and the target remains active, demotes the current administrator,
flushes, promotes the target, and commits once. The partial unique index rejects
two administrators; transaction isolation prevents the temporary internal
zero-administrator step from becoming externally observable. Stale UI actions
carry an `expectedRevision` and fail without a partial change.

**Rationale**: This matches existing concurrency handling and avoids adding a
locking, event-sourcing, or distributed-coordination layer to a single-process
SQLite deployment.

**Alternatives considered**:

- Trusting middleware identity throughout a later write transaction: authority
  can become stale during a competing transfer.
- Application-only checks without database constraints: insufficient for races.
- Distributed locks or Redis: no multi-process deployment or external cache is
  in scope.

## Decision 6: Persist startup-credential state across restarts

**Decision**: Operators provide distinct 64-hex-character values representing
32 random bytes through `PLANNER_BOOTSTRAP_CREDENTIAL` and
`PLANNER_ADMIN_RECOVERY_CREDENTIAL`. Startup rejects malformed values and rejects
the same value for both purposes. The application hashes configured values
immediately, retains only current digests in process memory, and registers every
observed digest in `planner_startup_credentials` with purpose and state
`current`, `consumed`, or `replaced`.

At startup, the unchanged current digest remains usable. If the environment
value is later absent, the persisted unused current digest remains redeemable;
absence is not an implicit replacement. A new valid digest for a purpose
atomically marks the previous unused current value replaced. A digest already
consumed, replaced, or observed for the other purpose can never become current;
if it remains or reappears in configuration, the application starts but exposes
no access for that value and reports only a secret-free operator warning.
Redemption consumes the credential in the same transaction as administrator
creation or recovery. Bootstrap also requires no administrator; recovery
requires exactly one active administrator and targets that account without an
account selector.

**Rationale**: Startup configuration registers a raw credential, while the
database supplies the durable current, replacement, one-time, and anti-replay
state. Leaving the same value configured across restarts cannot recreate usable
access after redemption and does not prevent the main application from
starting. No permanent master secret or external secret service is required.

**Alternatives considered**:

- Treat every startup as a fresh credential: repeats a configured value and
  violates permanent single-use behavior.
- Delete the environment value automatically: the application cannot safely
  mutate its deployment configuration.
- Store the raw credential: unnecessary and increases disclosure impact.
- Generate and print a credential on every start: creates ambiguous rotation,
  leaks into logs, and does not support deliberate operator delivery.

## Decision 7: Use one replaceable one-time access row per account

**Decision**: Setup, reset, and reactivation issue a 256-bit URL-safe secret and
store only its SHA-256 digest, purpose, issue time, and 24-hour expiry. Each
account has at most one row, so new issuance replaces the previous value.
Redemption claims the row, checks purpose/state/expiry, applies password and
account-state changes, deletes the access row, and commits once. The raw secret
is returned once with `Cache-Control: no-store`.

The frontend constructs `/account-access/#/<secret>`, keeps it only in React
memory, and clears the fragment before terminology loading, network work, or
dynamic import. Account listings never show pending, expired, consumed, or
replaced access.

**Rationale**: This follows the proven lecturer-secret pattern while keeping
account access purpose-specific and invisible to server access logs and browser
path history.

**Alternatives considered**:

- Query-string or path secrets: likely to appear in logs, referrers, and
  diagnostics.
- A history table: conflicts with the deliberately minimal visible lifecycle.
- Email delivery: expressly excluded.

## Decision 8: Centralize default denial at the backend boundary

**Decision**: Replace the current lecturer-only planner rejection middleware
with one default-deny authentication middleware. Maintain an exact method/path
public allowlist for `/health`, public terminology, the existing lecturer
capability operations, static assets and lecturer UI, and the new login,
bootstrap, account-access redemption, and administrator-recovery operations.
Every other `/api/**` request requires a current active planner session before
route validation or business logic. Planner HTML entry paths redirect to
`/login/` when no valid session is present; static assets contain no planner
data and remain public. Framework documentation entry points (`/docs`,
`/redoc`, and `/openapi.json`) are protected like planner pages or disabled in
production; they are not added to the public allowlist.

Stored lecturer bearer credentials remain explicitly rejected on planner paths,
even if a planner cookie is also present. Public lecturer operations continue to
ignore planner cookies and use their current bearer contract.

**Rationale**: One exact gate protects existing and future planner endpoints and
is easier to inventory than attaching authentication independently to every
router. Exact public exceptions preserve FS-015 without allowing near-miss
paths.

**Alternatives considered**:

- Route-by-route dependencies only: easy to omit when adding a planner API.
- Frontend-only protection: cannot protect direct API requests.
- Reusing lecturer bearer authentication: violates the minimum-scope capability
  boundary.

## Decision 9: Use a constant custom header for CSRF defense

**Decision**: Require `X-CSRF-Protection: 1` on every unsafe planner or
authentication request and require JSON content types where a body is expected.
Use it with `SameSite=Strict`, no state changes through GET, and credentialed
CORS restricted to exact localhost/127.0.0.1 development origins. Production
CORS is disabled. Existing lecturer bearer endpoints are exempt because the
browser does not attach their bearer credential automatically.

**Rationale**: Another origin cannot add the header without a successful CORS
preflight. This supplies an explicit CSRF control without a per-session CSRF
token table or a second browser-readable secret.

**Alternatives considered**:

- Rely only on SameSite: useful defense in depth but not the sole CSRF control.
- Synchronizer or double-submit tokens: extra state and frontend handling with
  no demonstrated benefit for this same-origin JSON application.
- Origin-only checking: requires canonical proxy/origin configuration not
  currently present.

Reference: [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## Decision 10: Mark only deliberate planner requests as activity

**Decision**: Add `X-Planner-Activity: user` through one shared planner request
helper for deliberate foreground interactions. Initial session inspection,
automatic loads, and any future background polling omit the marker. After a
successful protected response, the backend refreshes `last_activity_at` only if
the presented session is still current and the marker was present.

**Rationale**: The existing client has planner fetch duplication across ten API
modules. One small helper is justified now to apply cookies, CSRF, activity, and
401 invalidation consistently. Refreshing only after success satisfies the
clarified inactivity rule without allowing failing or background traffic to
extend access.

**Alternatives considered**:

- Treat every request as activity: background work could keep a session alive.
- UI timers only: the server remains authoritative and must reject stale
  sessions.
- A heartbeat endpoint: adds traffic and directly conflicts with the inactivity
  requirement.

## Decision 11: Retain dependency-free frontend route dispatch

**Decision**: Keep the current `main.tsx` path classification and React view
state. Add exact standalone routes for `/login/`, `/bootstrap/`,
`/account-access/`, and `/administrator-recovery/`; use one lazy-loaded
`PlannerApplication` authentication gate above the existing planner shell. Do
not mount planner components or retain planner data after a protected 401.

Add `Passwort ändern`, `Abmelden`, current display identity, and the
administrator-only `Planer-Konten` navigation entry. Render account
administration as responsive cards/lists and reuse established focus-trapped
confirmation patterns. Store only safe current-account metadata in React
memory; never store authentication or account-access secrets in browser
storage.

**Rationale**: The application has a handful of fixed routes and no router
dependency. This design reuses its established accessibility, responsive, and
German visual language without introducing routing or global-state machinery.

**Alternatives considered**:

- React Router: unnecessary for the fixed route set.
- Local/session storage authentication: increases credential exposure and does
  not provide authoritative invalidation.
- A wide account table: conflicts with narrow-view and 200%-zoom requirements.

## Decision 12: Verify authorization as an inventory, not samples

**Decision**: Generate a test inventory from FastAPI's registered/OpenAPI paths,
subtract only the exact public contract, substitute path parameters, and prove
that every remaining planner operation is denied before validation or mutation
for missing, malformed, expired, replaced, inactive, disabled, and lecturer
credentials. Use a shared test-only authenticated planner fixture for existing
business API tests; do not add a production bypass.

Add file-backed SQLite race tests for bootstrap, redemption, session
replacement, disablement, recovery, and transfer. Keep all FS-015 lecturer tests
anonymous. Add frontend contract tests for credentials, CSRF, activity, 401
unmounting, fragment scrubbing, transient secrets, account actions, focus, and
German safe messages.

**Rationale**: The slice requires default denial of every planner read and
mutation. An inventory test catches future omissions, while shared test setup
prevents unrelated existing business tests from becoming repetitive.

**Alternatives considered**:

- Representative endpoint sampling: cannot demonstrate 100% authorization
  coverage.
- A production authentication bypass for tests: creates an unsafe runtime mode.
- Browser automation dependency added solely for this slice: current Vitest and
  manual browser accessibility checks cover the implemented surfaces; a new E2E
  stack is not required.

## Deployment prerequisites

Remote production access must terminate HTTPS before reaching the application.
The current repository exposes plain HTTP and does not include a TLS proxy;
production secure cookies must intentionally fail over remote plain HTTP. Add
the startup credential variables to Compose and deployment documentation, keep
them optional, never print their values, and document operator generation using
a cryptographically secure 32-byte generator. VPN remains optional defense in
depth and is not an identity source.
