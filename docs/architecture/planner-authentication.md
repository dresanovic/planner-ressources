# Architecture Exploration: Planner Authentication

## Status

Needs validation. This exploration does not approve a feature, assign an
improvement identifier, change `Feature_slices.md`, or authorize implementation.

## Context

Anyone who can reach the current application listener can load the planner UI
and call planner APIs without authenticating. Planner operations can maintain
academic data, generate or edit schedules, issue lecturer links, and publish
revisions, so network reachability must not be treated as planner identity.

The existing lecturer-review feature already uses high-entropy capability
tokens, but those credentials are deliberately limited to one lecturer and one
revision. A planner credential would authorize substantially broader reads and
mutations and therefore needs its own lifecycle and server-side authorization
boundary.

## Current system

- FastAPI serves the API and compiled React application from one Uvicorn
  process.
- SQLite is the persistent store and only one application container may use it.
- `compose.yaml` publishes container port `8080` directly on a host port.
- No planner account, login, session, password, SSO, or role check exists in the
  application.
- Backend middleware rejects a known lecturer-review bearer on non-public APIs,
  but an anonymous request or unrelated bearer continues to the planner route.
- The documented trusted-gateway contract expects an external gateway to
  authenticate planners and make the backend listener unreachable directly.
  That gateway is not included in the one-container distribution.
- Lecturer-review secrets are 256-bit random values. Only SHA-256 digests are
  stored; links expire and can be revoked or replaced. Invalid attempts are
  rate-limited using a keyed source fingerprint.
- The frontend already separates `/lecturer-review/` from the planner bundle
  before dynamically importing either application surface.
- The backend currently treats these operations as public:
  `GET /api/public/lecturer-review`,
  `POST /api/public/lecturer-review/feedback`, and
  `GET /api/public/ui-terminology`. The older gateway document lists only the
  first two APIs and would need reconciliation in any approved authentication
  feature.
- The project constitution requires spec-first, test-first, and the simplest
  implementation that satisfies confirmed requirements.

## Goals

- Deny planner pages, planner data, and planner mutations unless the backend has
  authenticated the request.
- Preserve the existing accountless lecturer-review capability and its minimum
  scope.
- Support logout, expiry, replacement, and immediate revocation.
- Prevent a leaked lecturer token from becoming planner authority.
- Keep the same-origin FastAPI/React deployment and existing SQLite boundary.
- Make direct backend access safe instead of relying only on hidden UI controls.
- Avoid making institutional SSO a required runtime dependency when it may not
  be available.

## Constraints

- Authentication must be enforced server-side before planner route validation
  or service execution.
- Production authentication requires HTTPS.
- Raw planner credentials must not be stored in the database, logs, browser
  local storage, or normal URL query parameters.
- Planner and lecturer credentials must use separate models, scopes, and route
  policies.
- Anonymous access must use an explicit exact-method-and-path allowlist; all
  other frontend and API access defaults to denied.
- The direct Uvicorn port must be loopback-bound, private, or firewalled when a
  gateway terminates authentication or TLS.
- Authorization is limited to two fixed access levels: planner and system
  administrator. Only the system administrator may manage planner access.
- Authentication must not alter schedule, publication, lecturer-feedback, or
  regeneration business rules.

## Decision drivers

In priority order:

1. Protection against unauthorized planner access and mutation.
2. Server-side revocation and default-deny authorization.
3. Simplicity within the one-container FastAPI/React/SQLite architecture.
4. Individual accountability when more than one planner uses the installation.
5. Operational portability for institutions without an identity provider.
6. Compatibility with the public lecturer-review surface.
7. Compatibility with institutional SSO and MFA policy.

## Assumptions

- The application continues to run as one deployment for one institution.
- Planner access is powerful but currently has only one authorization level.
- Some institutional deployments may limit network access through a VPN. The
  application neither requires nor trusts that VPN for authentication or
  authorization; it must remain secure when directly reachable.
- Institutional SSO may not exist and therefore cannot be a mandatory
  dependency.
- Each planner uses an individual local identity. Every active planner
  session identifies who triggered protected operations; whether that actor must
  be persisted on every domain mutation remains to be confirmed.
- Exactly one active system administrator may create, disable, and recover
  planner accounts. Normal planners cannot manage planner access.
- The first system administrator uses the same normal login flow after a
  one-time bootstrap establishes the initial account.
- Setup and recovery links are one-time and time-limited. They establish or
  reset a durable authenticator; they never become permanent credentials.
- Production can provide HTTPS either through a gateway or a narrowly added TLS
  deployment boundary.

## Options considered

### Option 1: External identity-aware gateway

#### Description

Put the application behind a reverse proxy or identity-aware gateway connected
to the institution's identity provider. The gateway authenticates planners,
permits only the exact anonymous lecturer surface, and blocks direct access to
Uvicorn. If the application needs planner identity, FastAPI accepts an identity
header only from the known gateway peer after removing any caller-supplied
version of that header.

#### Benefits

- Reuses institutional identity, account deactivation, MFA, and sign-in policy.
- Adds little authentication code to the application.
- Closely matches the existing trusted-gateway contract.
- Avoids distributing new planner secrets.

#### Disadvantages

- Requires institution-specific gateway and identity-provider configuration.
- The downloadable container is not secure by itself.
- Local and small standalone installations have a heavier operational setup.
- Test and release evidence must cover proxy trust, header rewriting, anonymous
  allowlists, and direct-port blocking.

#### Risks

- A reachable backend port or trusted identity header accepted from arbitrary
  peers completely bypasses authentication.
- Different customer gateways may behave differently unless one supported
  deployment contract is selected.

### Option 2: One installation-wide planner token exchanged for a session

#### Description

An operator generates one high-entropy planner secret for the installation. A
planner submits it to a login endpoint over HTTPS. After validation, FastAPI
creates an opaque server-side session and returns only a secure session cookie.
The long-lived installation secret is not sent with normal API requests.

The configured secret may be stored as a digest. Because it must be a randomly
generated high-entropy token, a fast cryptographic digest is sufficient; a
human-chosen password would instead require a password hashing design and a new
credential-recovery boundary.

#### Benefits

- Smallest self-contained application change that blocks outsiders.
- No planner account administration or external identity provider.
- Server-side sessions support logout, timeout, rotation, and immediate global
  revocation.
- Fits the existing one-container and SQLite model.

#### Disadvantages

- Every planner shares one identity and secret.
- Individual access cannot be revoked without rotating the secret for everyone.
- Planner attribution and per-person security events are impossible.
- Secure secret delivery remains an operator responsibility.

#### Risks

- Sharing encourages copying the secret through insecure channels.
- A leaked secret compromises the complete planner surface until rotation.
- Teams may assume the shared session identifies a person when it does not.

### Option 3: Named planner SSO memberships with enrollment links

#### Description

Integrate OpenID Connect directly at the FastAPI boundary and maintain a minimal
local planner membership without introducing general role management. An
operator or access administrator may issue a short-lived, one-time enrollment
invitation, but the recipient must complete institutional SSO before membership
and an opaque server-side session are created. The browser then uses only a
secure local session cookie.

Minimal records would be:

- `PlannerIdentity`: stable ID, OIDC issuer and subject, display name,
  active/inactive status, revision;
- `PlannerInvitation`: identity, digest, issue/expiry/redeem/revoke state;
- `PlannerSession`: identity, digest, creation, idle/absolute expiry, revocation.

The first planner is authorized by an identity-provider group or a configured
bootstrap OIDC subject and still completes the normal SSO flow. Lecturer-review
records remain separate and cannot be promoted into planner credentials.

#### Benefits

- Individual revocation, session termination, and security-event attribution.
- No password database or password-reset flow is required; institutional SSO and
  MFA remain authoritative.
- Reuses proven lecturer-token design ideas while keeping planner authority
  separate.
- Remains portable as one self-contained container.
- The application can identify and revoke individual planners while retaining
  institutional authentication.

#### Disadvantages

- More schema, UI, API, OIDC callback, and lifecycle behavior than a shared
  token or group-only gateway.
- Invitation delivery and lost-device recovery need explicit operational rules.
- Identity-provider and callback configuration becomes a required operational
  dependency.
- Domain-action attribution would require additional approved work if every
  schedule mutation must retain the acting planner.

#### Risks

- Treating the invitation as a permanent bearer instead of exchanging it for a
  session would increase leakage exposure.
- An over-general role framework would violate the current simplicity rule.
- Weak bootstrap handling could undermine every later credential.

### Option 4: Self-contained named local accounts

#### Description

Maintain a small local account model in SQLite. Each planner has a unique login
name and password, and FastAPI exchanges a successful login for an opaque
server-side session. Exactly one account also has the fixed
`manage_planner_access` capability. That system administrator creates planners
and issues one-time, expiring setup or recovery links.

Minimal records would be:

- `PlannerIdentity`: stable ID, login name, display name, password hash,
  active/inactive state, and fixed access level;
- `PlannerSetup`: identity, token digest, issue/expiry/use/revoke state;
- `PlannerSession`: identity, token digest, creation, idle/absolute expiry, and
  revocation state.

#### Benefits

- No dependency on an institutional identity provider.
- Individual revocation, session termination, and action attribution.
- Directly enforces that normal planners cannot create other planners.
- Fits the current one-container FastAPI/React/SQLite deployment.

#### Disadvantages

- The application must securely hash passwords and provide setup, reset,
  rate-limit, and recovery behavior.
- The institution operates the complete account lifecycle.
- Exactly one administrator creates an availability risk without an operator
  recovery procedure.

#### Risks

- Weak passwords or unsafe reset links can defeat the application's identity
  boundary regardless of network placement.
- A bootstrap secret retained in environment or compose configuration becomes a
  long-lived master credential.
- Permitting deletion or disablement of the only administrator could make normal
  access management impossible.

### Option 5: Reuse an individual identity supplied by network infrastructure

#### Description

If network infrastructure or a reverse proxy authenticates each person and injects a
cryptographically trustworthy identity into every request, FastAPI can map that
identity to a local planner membership. This is not available merely because a
user has joined a network through a VPN; the infrastructure must expose and
protect the per-user identity contract.

#### Benefits

- Avoids local passwords and full OIDC integration.
- Can provide individual accounts with little application authentication code.

#### Disadvantages and risks

- Feasibility depends on the institution's specific VPN and proxy.
- Direct backend access or acceptance of caller-supplied identity headers would
  completely bypass authentication.
- It introduces an infrastructure dependency similar to an identity-aware
  gateway and is not a portable default.

## Comparison

| Driver | Gateway/SSO | Shared token | Named SSO | Named local accounts | Network identity |
|---|---|---|---|---|---|
| Blocks anonymous planner access | Strong | Strong | Strong | Strong | Strong if trusted |
| Individual identity/revocation | Strong | None | Strong | Strong | Strong |
| Application complexity | Low | Low | Medium | Medium | Low to medium |
| Deployment dependency | High | Low | Medium | Low | High/unknown |
| Standalone portability | Low | High | Medium | High | Low |
| Admin-only account creation | Via IdP | Impossible | Supported | Supported | Supported locally |
| Credential recovery owned by | Institution | Operator | Institution | Application/operator | Institution |

## Conditional recommendation when institutional SSO is available

The shared-identity option is technically simpler, but it no longer satisfies
the confirmed requirements. It conflicts with institutional SSO, cannot identify
who triggered a schedule change, and cannot revoke one planner independently.

The simplest acceptable architecture is **institutional OpenID Connect SSO with
named planner identities and opaque local sessions**. Authorization can then be
managed in one of two ways:

| Authorization model | Complexity | Operation |
|---|---|---|
| Identity-provider groups | Lower | Institutional administrators add users to a Planner group and optionally an Access Administrators group. The application trusts validated group claims. |
| Application-managed enrollment | Medium | An access administrator issues a one-time, expiring enrollment link. The recipient must still complete SSO before planner membership is created. |

Use identity-provider groups when the institution can reliably operate them;
this removes invitation issuance, bootstrap tokens, and local access-management
UI from the application. Use application-managed enrollment only when planners
must control membership inside this product.

An application-managed enrollment link is authorization, not authentication.
It says that the next validated institutional identity may become a planner; the
identity provider still proves who that person is. After enrollment, future
sign-ins use SSO and do not require another invitation.

### Administrative responsibilities

Keep three responsibilities distinct even when one person performs several:

- **Infrastructure operator**: deploys the container and configures the OIDC
  issuer, client, callback, and bootstrap authorization. This person does not
  automatically receive planner access.
- **Access administrator**: is an authenticated planner with the additional
  ability to invite, activate, disable, and revoke planner access.
- **Planner**: performs all current schedule and academic-data work.

The access-administrator distinction is not obsolete even when that person has
the same schedule permissions as a planner. Their extra power is creating and
removing identities. If every planner receives that power, the role can be
removed, but compromise of any planner session would then allow an attacker to
create persistent additional access. The safer minimal design is one additional
`manage_planner_access` capability, not a general role framework or unrestricted
"superuser".

### First-planner bootstrap example

Prefer an institutional group claim when available. The first planner simply
joins the configured Planner/Access Administrators groups and follows the normal
SSO flow.

If application-managed enrollment is required, configure the first authorized
institutional identity at deployment using the stable OIDC pair `(issuer,
subject)`, not a raw access token in a URL. Example configuration:

```text
OIDC_ISSUER=https://identity.example.edu/
OIDC_CLIENT_ID=resource-planner
OIDC_CLIENT_SECRET=<deployment secret>
BOOTSTRAP_PLANNER_SUBJECT=<stable OIDC subject identifier>
```

The first planner then uses the same workflow as everyone else:

1. Open the planner and choose institutional sign-in.
2. FastAPI starts Authorization Code flow with PKCE, state, and nonce.
3. The identity provider authenticates the person, including institutional MFA.
4. FastAPI validates issuer, audience, redirect, nonce, code verifier, and the
   ID token, then reads the stable `(issuer, subject)` identity.
5. When no planner membership exists and the identity matches the configured
   bootstrap subject, create the first active planner with
   `manage_planner_access`.
6. Mark bootstrap enrollment consumed in the database and issue an opaque local
   session cookie.

This is simpler and safer than passing a bootstrap token as a request parameter.
If a bootstrap token is unavoidable, it must be high-entropy, one-time,
short-lived, stored only as a digest, entered manually or carried in a URL
fragment, and accepted only after successful SSO. It should be a fallback, not
the primary design.

### Later-planner enrollment example

1. The access administrator creates an enrollment for a named institutional
   address or intended person with an approved short expiry.
2. The application displays one raw enrollment link once; only its digest and
   lifecycle state are stored.
3. The recipient opens the link and completes institutional SSO.
4. The backend validates both the enrollment and the SSO identity, binds the
   stable `(issuer, subject)` to a new `PlannerIdentity`, and consumes the link.
5. The backend creates an opaque local session. Later visits require normal SSO,
   not another enrollment link.
6. Disabling the planner or revoking a session immediately blocks planner APIs.

Invitations and sessions solve different problems. The simpler secure rule is:

- enrollment link: one use plus a short wall-clock expiry;
- planner session: idle timeout plus absolute expiry;
- institutional SSO: required again after the local session can no longer be
  renewed.

Making an invitation valid only for one browser session would force a new
invitation for every login and mix enrollment with authentication. It is less
usable and not simpler once institutional SSO exists.

### Application boundary

1. Keep an exact anonymous allowlist for the lecturer shell, its required static
   assets, the two lecturer-review APIs, and public terminology.
2. Add narrowly defined OIDC start/callback, session-status, logout, and optional
   enrollment-redemption endpoints.
3. Protect every other planner page and `/api/...` route in centralized FastAPI
   middleware before route validation.
4. Use Authorization Code flow with PKCE and exact registered redirect URIs; do
   not expose identity-provider tokens to React.
5. Map the validated `(issuer, subject)` to an active local planner membership,
   create a random opaque session, store only its digest, and set a `__Host-`
   cookie with `Secure`, `HttpOnly`, `SameSite=Strict`, and `Path=/`.
6. Protect state-changing requests with strict Origin checking and a CSRF token;
   SameSite remains defense in depth rather than the only CSRF control.
7. Apply idle and absolute session expiry, logout, per-session revocation,
   planner disablement, generic authentication failures, and rate limiting.
8. Load the planner React bundle only after session bootstrap succeeds. Continue
   loading the lecturer-review bundle independently.
9. Require HTTPS and prevent direct access to Uvicorn in production.
10. Attach the authenticated planner identity to every protected request.
    Persisting the actor on every domain mutation remains a separate acceptance
    decision, but security-event attribution is required.

## Current recommendation: self-contained application security

Use **named local planner accounts with opaque server-side sessions**. The
application must authenticate and authorize every planner request without
depending on a VPN, gateway identity, or institutional SSO. An institutional
VPN may still reduce who can reach the listener, but it is an optional deployment
layer and does not change application behavior or trust decisions.

Keep authorization deliberately small:

- **Planner**: all current planner operations, but no account-management API or
  UI.
- **System administrator**: all planner operations plus the single fixed
  `manage_planner_access` capability. Exactly one active account has it.
- **Infrastructure operator**: can run an offline recovery/bootstrap command but
  has no account merely because they operate the server.

This is not a general role system and the administrator is not an unrestricted
technical superuser. The only application-level difference is management of
planner access.

### First-system-administrator bootstrap

Prefer a container-local command over a token passed as a normal URL parameter.
For example, a future approved implementation could provide:

```text
docker compose exec planner python scripts/bootstrap_system_admin.py
```

The command would work only while no system administrator exists. It would
create a random, short-lived, single-use setup secret, store only its digest,
and display the secret once. The operator gives that secret to the intended
administrator through a protected channel. The administrator opens the planner,
chooses a login name and password, and consumes the setup secret. From then on,
this person signs in through the same login screen and receives the same kind of
session as every planner.

A configured `BOOTSTRAP_ADMIN_TOKEN` is possible but inferior: deployment
secrets are easy to leave behind in compose files, environment inspection, or
operational notes. If selected, it must be random, short-lived, accepted only
while no administrator exists, stored only as a digest where persisted, consumed
once, and removed from deployment configuration immediately afterward.

### Later-planner workflow

1. The system administrator creates a named inactive planner account.
2. The application displays a random one-time setup link or setup code once;
   only its digest and expiry are retained.
3. The planner reaches the application, consumes the setup credential, and
   chooses a password.
4. The password is stored only as a modern password hash, preferably Argon2id.
5. Later logins use the login name and password; successful authentication
   creates an opaque server-side session cookie.
6. The system administrator can disable the planner or revoke their sessions.

Setup links and sessions have different lifetimes. The setup link expires after
one use or a short wall-clock period. The account remains usable through its
password, while each session has both an idle timeout and an absolute lifetime.
Making the setup link valid for only one session would require a new link for
every login and would make account administration harder rather than simpler.

### Security and recovery boundary

- Protect all planner pages and APIs by default in centralized FastAPI
  middleware; retain only an exact anonymous lecturer-review allowlist.
- Require HTTPS regardless of VPN use, use `Secure`, `HttpOnly`, and
  `SameSite=Strict` cookies, and add explicit CSRF protection for mutations.
- Rate-limit login and setup attempts and return generic authentication errors.
- Never store raw passwords, setup secrets, reset secrets, or session tokens.
- Do not allow the only active administrator to be disabled or demoted through
  ordinary UI. If authority must change, use an atomic transfer that leaves
  exactly one administrator.
- Provide an operator-only recovery command to reset the administrator and
  revoke their sessions. This is a break-glass recovery path, not a second
  application administrator.
- Attach the authenticated planner ID to every protected request. Persisting it
  on schedule/publication mutations should be decided explicitly in the future
  feature specification.

Passkeys/WebAuthn are a stronger future authenticator and remove stored
passwords, but they add browser, device enrollment, HTTPS-origin, and recovery
work. They are not the simplest first implementation unless passwordless access
is itself a requirement.

## Consequences

- Authentication becomes a new cross-cutting feature touching backend
  middleware, database schema, frontend bootstrap, deployment, and tests.
- The lecturer token implementation can supply reviewed patterns and test
  fixtures, but its tables and services should not become generic planner-auth
  abstractions unless actual duplication justifies extraction.
- Cookie sessions require explicit CSRF protection and HTTPS deployment tests.
- Planner disablement and session revocation become operational responsibilities.
- With the current recommendation, password hashing, account recovery, and the
  single-administrator lifecycle become application and operator
  responsibilities.
- If SSO becomes available later, the local identity boundary can be replaced or
  migrated without weakening planner authorization or sessions.
- The existing trusted-gateway document must be reconciled with the selected
  model and the public terminology endpoint.

## Validation required

- Verify that planner authentication and authorization behave identically with
  and without a VPN in front of the application.
- Confirm local password authentication as the initial authenticator, with
  passkeys deferred.
- Confirm whether individual attribution is needed only for security events or
  also for every domain mutation and publication action.
- Confirm that exactly one system administrator may create, disable, and recover
  planner access, and choose how setup links or codes are delivered without
  email delivery.
- Confirm acceptable invitation lifetime, session idle timeout, absolute
  lifetime, and concurrent-session policy.
- Confirm password policy, Argon2id parameters, administrator transfer/recovery,
  HTTPS termination, and reverse-proxy ownership.
- Prototype the public/planner frontend bootstrap to prove that authentication
  does not expose planner bundles or block the accountless lecturer surface.
- Test default denial for planner pages, APIs, health, API documentation, and
  direct backend access before considering production release.

## Open questions

1. How should the one system administrator deliver setup and recovery codes to
   planners?
2. Should closing the browser end the session, or may a planner remain signed in
   across restarts?
3. Must every schedule and publication mutation retain its acting planner?
4. What operator approval is required to transfer or recover the sole system
   administrator?

## Handoff to specification

Do not modify the current feature map until the user approves a product-scope
change. If approved, create a new improvement specification rather than folding
authentication silently into I-001, lecturer review, or FS-016.

The specification should define independently testable stories for:

- local named-account login and opaque session creation;
- one-time bootstrap of the sole system administrator;
- administrator-only planner creation, disablement, recovery, and setup-link
  invalidation;
- password setup, storage, verification, change, and recovery;
- authenticated planner session use and renewal policy;
- logout, expiry, disablement, and revocation;
- default-deny planner page/API behavior;
- preserved accountless lecturer access;
- CSRF, rate-limit, direct-port, HTTPS, and secret-leakage boundaries;
- recovery and operational ownership;
- accessibility of login, expiry, and failure states.

Only after specification approval should planning decide concrete table names,
cookie names, durations, migration details, and whether a small shared helper
can be extracted from lecturer-token code.

## Security references

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [RFC 6750: Bearer Token Usage](https://datatracker.ietf.org/doc/rfc6750/)
- [RFC 9700: OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [NIST SP 800-207: Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [W3C Web Authentication Level 3](https://www.w3.org/TR/webauthn-3/)
