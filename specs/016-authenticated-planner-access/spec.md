# Feature Specification: FS-016 Authenticated Planner Access and Account Administration

**Working Branch**: `master`

**Created**: 2026-08-17

**Status**: Draft

**Input**: Development slice FS-016, "Authenticated Planner Access and Account Administration"

**Constitution Requirements**: This specification MUST be updated before
production implementation. All user stories require clear acceptance criteria
and independent test paths. Implementation planning MUST preserve the existing
planner and accountless lecturer boundaries and follow the project's
test-first and simplicity requirements.

## Clarifications

### Session 2026-08-17

- Q: Which German terminology, form of address, and generic authentication
  failure wording apply? → A: Use the application's existing formal `Sie`
  style, `Planer-Konten`, `Anmelden`, `Benutzername`, and `Passwort`. Use one
  generic login failure that does not disclose whether the login name, password,
  or account state caused the failure.
- Q: Which password acceptance and retry policy applies? → A: Accept passwords
  from 12 through 128 characters without composition rules, permit spaces and
  other normal characters, and reject a password equal to the login name. After
  ten consecutive failed login attempts, refuse further login attempts for 15
  minutes. Reset the failure count after successful login, password reset, or
  administrator recovery. Do not add a separate retry counter to one-time
  account-access redemption.
- Q: Which one-time-access and session lifetime policy applies? → A: Setup,
  reset, and reactivation access remains valid for 24 hours. A planner session
  expires after 60 minutes of inactivity or 12 hours absolutely. Successful
  user-initiated protected planner requests refresh inactivity; background
  activity does not. Do not show an advance-expiry warning.
- Q: How are login names normalized, compared, and displayed? → A: Remove
  leading and trailing whitespace, compare login names case-insensitively, and
  preserve the resulting entered spelling for display.
- Q: How does Planner accounts represent pending or expired setup, reset, and
  reactivation access? → A: Show only the account state `Aktiv` or `Inaktiv`.
  Show one-time access only in the immediate issuance result and do not retain a
  pending or expired access indicator on the account page.
- Q: How are bootstrap and recovery credentials created and handled across
  application restarts? → A: The operator generates a distinct value with at
  least 32 random bytes for the required purpose and supplies it at startup. An
  unused value remains current across restarts until redeemed or explicitly
  replaced. Successful redemption makes that exact value permanently unusable;
  a later recovery requires a newly generated value.
- Q: May the sole administrator issue administrator-managed reset access for
  their own account? → A: No. A signed-in administrator uses self-service
  password change; a locked-out administrator uses operator-assisted recovery.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish the First Administrator Safely (Priority: P1)

On a deployment with no administrator, an infrastructure operator supplies a
one-time startup credential. The person becoming the first administrator uses
that credential to choose a unique named login, display identity, and password.
After successful setup, planner pages and planner operations require a valid
planner sign-in and the bootstrap path can never create another administrator.

**Why this priority**: The application cannot safely expose existing planner
work until a named administrator exists and anonymous planner access is denied.

**Independent Test**: Start with no administrator and one valid startup
credential, establish the first administrator, verify that this person can sign
in and use an existing planner workflow, and verify that anonymous access and a
second bootstrap attempt reveal no planner data and create no account.

**Acceptance Scenarios**:

1. **Given** no system administrator exists and the deployment has a valid
   unused bootstrap credential, **When** a person supplies that credential and
   acceptable unique account details, **Then** exactly one active named system
   administrator is established and the bootstrap credential becomes unusable.
2. **Given** the first administrator has been established, **When** anyone
   attempts bootstrap with the original credential, a replacement value, or no
   credential, **Then** no account is created, no administrator identity is
   disclosed, and exactly one administrator remains.
3. **Given** no valid planner session exists, **When** a person requests any
   planner page or planner read or action, **Then** the request exposes no
   planner data and directs the person to authenticate where a user interface is
   applicable.
4. **Given** an active administrator has completed bootstrap, **When** that
   administrator signs in with the chosen credentials, **Then** the
   administrator can use every existing planner workflow and can reach planner
   account administration.
5. **Given** an operator knows only the bootstrap credential, **When** the
   operator does not create an application account, **Then** the operator gains
   no planner or account-administration authority.

---

### User Story 2 - Set Up and Use a Named Planner Account (Priority: P1)

The administrator creates an inactive named planner account and manually shares
fresh one-time setup access. The planner chooses their own password, signs in,
and completes all existing planner workflows without receiving administrator
authority.

**Why this priority**: Named planners need a complete route from account
invitation to protected day-to-day work without email, SSO, or administrator
knowledge of their password.

**Independent Test**: Create an inactive planner, redeem the manually delivered
setup access once, sign in, exercise representative existing planner reads and
mutations, and verify that the same planner cannot open Planner accounts or use
account-management actions.

**Acceptance Scenarios**:

1. **Given** the administrator is signed in, **When** the administrator provides
   a unique login and display identity for a new planner, **Then** an inactive
   planner account is created without a password and one-time setup access is
   made available for manual delivery.
2. **Given** an inactive planner has current unexpired setup access, **When** the
   planner supplies that access and an acceptable new password, **Then** the
   access is consumed, the account becomes active, and the planner can sign in.
3. **Given** setup access has been used, expired, or replaced, **When** anyone
   tries to use it, **Then** no password is changed, no session is created, and
   the failure state discloses no protected account data.
4. **Given** an active planner signs in successfully, **When** the planner uses
   any existing planning, scheduling, publication, academic-data, or Lecturer
   coordination workflow, **Then** the workflow remains available with its
   existing business behavior.
5. **Given** an ordinary planner is signed in, **When** the planner requests the
   Planner accounts page or any account-management action, **Then** access is
   denied and no account listing or action outcome is disclosed.

---

### User Story 3 - Keep One Current Session per Account (Priority: P1)

Each active planner uses at most one current browser-bound session. A later
successful login replaces the earlier session, while logout, browser close,
password change, expiry, reset, disablement, and administrator recovery end the
applicable session before it can expose or change more planner data.

**Why this priority**: Authentication does not protect planner work if stale or
superseded sessions remain usable.

**Independent Test**: Sign in from two browser contexts, verify that the second
successful sign-in invalidates the first, and exercise every required session
ending event against a protected planner read and mutation.

**Acceptance Scenarios**:

1. **Given** an account has a current session, **When** the same account signs in
   successfully in another browser context, **Then** the new session becomes the
   only current session and the earlier session fails on its next protected
   request.
2. **Given** an account has a current session, **When** a later login attempt for
   that account fails, **Then** the current session is not replaced.
3. **Given** a planner logs out or closes the browser, **When** the former session
   is presented again, **Then** it cannot read or change planner data.
4. **Given** a current session reaches its inactivity or absolute lifetime,
   **When** the user next requests a protected page or action, **Then** the
   session is rejected, no requested mutation occurs, and the user receives a
   clear sign-in recovery path.
5. **Given** a signed-in planner changes their own password after proving
   knowledge of the current password, **When** the change succeeds, **Then** the
   current session ends, the old password is unusable, and the planner must sign
   in with the new password.

---

### User Story 4 - Reset, Disable, and Reactivate Planner Access (Priority: P2)

The sole administrator can reset access, disable an account immediately, and
reactivate a disabled planner through fresh one-time access. The administrator
never sees or assigns another person's password.

**Why this priority**: A simple local account model still needs safe joiner,
mover, and recovery actions without an email or identity provider.

**Independent Test**: For one ordinary planner, issue a reset, disable the
account with an active session, and reactivate it with fresh access; verify the
password, session, state, and lifecycle timestamp outcome after every action.

**Acceptance Scenarios**:

1. **Given** an active planner has a password and current session, **When** the
   administrator issues reset access, **Then** the old password and session stop
   working and fresh one-time expiring access is available for manual delivery.
2. **Given** an active planner has a current session, **When** the administrator
   disables the account, **Then** access is denied on the next protected request,
   new login is denied, and the account shows inactive with a disablement time.
3. **Given** an account is disabled, **When** the administrator begins
   reactivation, **Then** the account remains unable to sign in until the planner
   successfully uses fresh one-time access and chooses a new password.
4. **Given** a disabled account has current reactivation access, **When** the
   planner redeems it successfully, **Then** the account becomes active, records
   a reactivation time, and can sign in with the new password.
5. **Given** the administrator creates newer setup, reset, or reactivation
   access for an account, **When** older unredeemed access is presented, **Then**
   the older access is rejected and cannot change account state.
6. **Given** the administrator views or manages an account, **When** the action
   completes or fails, **Then** no raw password or usable setup, reset, recovery,
   bootstrap, or session secret appears in the account listing or diagnostic
   text.

---

### User Story 5 - Transfer or Recover the Sole Administrator (Priority: P2)

The current administrator can atomically transfer the additional account-
management authority to an active planner. If the sole administrator is locked
out, an operator can supply a one-time startup recovery credential that lets
that same administrator choose a new password without creating another
administrator or exposing planner data to the operator.

**Why this priority**: Exactly-one administration must remain maintainable
without permitting a zero-administrator or multi-administrator state.

**Independent Test**: Transfer authority between two active planners and
attempt concurrent or stale transfers, then recover the current administrator
with an operator-supplied one-time credential and verify authority, password,
session, and credential invalidation.

**Acceptance Scenarios**:

1. **Given** exactly one administrator and at least one other active planner
   exist, **When** the administrator confirms transfer to that active planner,
   **Then** the target immediately becomes the sole administrator and the prior
   administrator immediately becomes an ordinary active planner as one
   indivisible outcome.
2. **Given** a transfer target is inactive, disabled, no longer current, or is
   the existing administrator, **When** transfer is attempted, **Then** no
   authority changes and exactly one administrator remains.
3. **Given** two transfer requests compete or account state changes before a
   transfer completes, **When** the transfer decision is applied, **Then** at
   most one valid transfer succeeds and the product never exposes a zero- or
   multi-administrator state.
4. **Given** the sole administrator is locked out and the deployment has a
   valid unused recovery credential, **When** that administrator supplies the
   credential and an acceptable new password, **Then** the same account remains
   the sole administrator, the old password and prior session are invalidated,
   and the recovery credential is consumed.
5. **Given** recovery has completed or no valid startup recovery credential was
   supplied, **When** recovery is attempted, **Then** no account, password, or
   authority changes and no protected account information is disclosed.
6. **Given** an operator supplies a recovery credential, **When** recovery is
   completed by the administrator, **Then** the operator receives no
   application account and no planner authority.

---

### User Story 6 - Preserve Accountless Lecturer Capabilities (Priority: P1)

An accountless lecturer continues to use every existing token-scoped review
capability without a planner account. Lecturer capability credentials remain
limited to their established lecturer scope and can never authenticate to
planner pages or planner operations.

**Why this priority**: Protecting planner work must not regress the already
delivered minimum-scope lecturer collaboration workflow or turn lecturer links
into planner credentials.

**Independent Test**: Run the established valid, expired, revoked, replaced,
wrong-scope, and feedback scenarios for FS-015, then present each lecturer
credential to representative planner pages, reads, and mutations and verify
complete planner denial.

**Acceptance Scenarios**:

1. **Given** a valid lecturer capability credential, **When** the lecturer uses
   an existing permitted review or feedback capability, **Then** the existing
   scoped behavior succeeds without requiring planner login.
2. **Given** a lecturer capability credential of any lifecycle state, **When**
   it is presented to a planner page, planner read, planner mutation, or Planner
   accounts function, **Then** planner access is denied and no planner data is
   exposed.
3. **Given** a lecturer link is expired, revoked, replaced, malformed, or for a
   different scope, **When** it is used, **Then** the existing FS-015 safe-
   failure and minimum-disclosure behavior remains unchanged.
4. **Given** planner authentication is unavailable or a planner session expires,
   **When** a lecturer uses valid scoped access, **Then** the lecturer workflow
   remains available within its existing capability boundary.

---

### User Story 7 - Administer Accounts Accessibly and Privately (Priority: P3)

The sole administrator uses a responsive Planner accounts page to understand
each named account's identity, access level, current state, and minimal
lifecycle timestamps, and to start only the actions permitted by that state.
Authentication, setup, expiry, recovery, and failure screens remain clear and
operable with the application's established German visual and accessibility
language.

**Why this priority**: Account controls must be understandable and safe in
routine use, while exposing no password, credential, session, or broad audit
history.

**Independent Test**: Navigate every authentication and account-management
state using keyboard-only and common responsive viewports; inspect visible
fields, focus movement, labels, errors, confirmations, and secret handling.

**Acceptance Scenarios**:

1. **Given** the administrator opens Planner accounts, **When** account data is
   displayed, **Then** each row or detail shows display identity, login name,
   planner or administrator level, current state as `Aktiv` or `Inaktiv`,
   creation time, and applicable most recent disablement and reactivation times
   only.
2. **Given** an account action is unavailable for the account's current state,
   **When** the administrator reviews that account, **Then** the unavailable
   action is absent or clearly disabled and cannot be performed by bypassing the
   interface.
3. **Given** the administrator initiates disablement, reset, reactivation, or
   transfer, **When** the action can immediately remove or change access,
   **Then** the interface identifies the affected account, states the effect,
   and requires an explicit confirmation.
4. **Given** a user navigates by keyboard or assistive technology, **When** a
   login, setup, password-change, failure, recovery, or account action succeeds
   or fails, **Then** focus and an announced status move to the relevant result
   without relying on color, pointer use, or visual position alone.
5. **Given** the interface is used at a narrow viewport or 200% zoom, **When**
   authentication or account administration is performed, **Then** content and
   controls remain readable, reachable, and operable without losing actions or
   requiring two-dimensional scrolling for ordinary text content.

### Edge Cases

- No administrator exists but no valid bootstrap credential is supplied: no
  planner account can be created and all planner work remains denied.
- A bootstrap request races with another valid bootstrap request: only one can
  establish the first administrator; the other safely fails without revealing
  the winning identity or credential validity details.
- A login name differs from an existing one only by the matching rules used at
  sign-in: the duplicate is rejected so one entered login cannot identify two
  accounts.
- An inactive or disabled account is given the correct former password: login
  fails with the same safe public wording used for other invalid credentials.
- A setup, reset, reactivation, bootstrap, or recovery credential is malformed,
  expired, used, replaced, or submitted concurrently: at most one successful
  redemption occurs and failure reveals no usable secret or protected account
  state.
- An account is disabled, reset, or recovered while a planner request is in
  progress: no later protected read or mutation may succeed under the invalidated
  session; an indivisible mutation already accepted before invalidation is not
  partially applied.
- A session reaches inactivity and absolute expiry at the same time: it ends
  once and the user receives one consistent sign-in outcome.
- A second successful login replaces a session that currently displays planner
  data: subsequent reads and actions fail; content from any newly requested
  protected response is not shown.
- A password-change submission has the wrong current password or an unacceptable
  new value: the password and current session remain unchanged and the response
  does not reveal the stored password or its properties.
- The sole administrator attempts to disable themselves or otherwise perform an
  action that would leave no active administrator: the action is rejected
  without changing account or session state.
- The sole administrator attempts to issue administrator-managed reset access
  for their own account: the action is rejected without changing the password
  or session and directs them to password change or operator-assisted recovery,
  as applicable.
- An administrator transfer is retried after it succeeded: the former
  administrator has no account-management authority, and the current sole
  administrator remains unchanged.
- The transfer target is disabled or begins reset/reactivation during transfer:
  transfer fails safely unless the target is still an active planner at the
  indivisible authority change.
- The account page contains a long display identity or many accounts: identity,
  state, timestamps, and actions remain distinguishable without exposing
  secrets or confusing one account with another.
- A planner session expires while a protected form is open: submission changes
  no planner data and the user receives a clear authentication-required result;
  password fields are not retained in the rendered failure state.
- A lecturer credential and a planner session are both present: the requested
  surface applies its own authorization boundary; lecturer capability scope
  never expands planner authority and planner identity never expands the
  lecturer link's data scope.
- Application startup receives a bootstrap credential after an administrator
  already exists or a recovery credential when bootstrap is required: neither
  credential can be used for the other purpose.

## Scope Boundaries

### In Scope

- Named local planner accounts with login name, display identity, password
  setup, active state, and exactly one of two fixed access levels: planner or
  system administrator.
- Default denial of every planner page and planner read or mutation unless an
  active named planner has a current valid session.
- First-administrator bootstrap, planner setup, sign-in, sign-out, self-service
  password change, administrator-issued reset, disablement, reactivation,
  administrator transfer, and operator-assisted administrator recovery.
- One current browser-bound session per account with replacement, inactivity,
  absolute expiry, and all specified invalidation events.
- Existing accountless lecturer capabilities preserved unchanged and explicitly
  unable to grant planner access.
- One administrator-only Planner accounts page and minimal account lifecycle
  visibility limited to current state plus account creation, most recent
  disablement, and most recent reactivation times.
- Clear responsive and accessible German authentication and account-
  administration states using the application's existing visual language.

### Out of Scope

- Authenticated lecturer accounts or any change to lecturer-token issuance,
  scope, expiry, replacement, revocation, feedback, export, or availability
  behavior.
- Institutional SSO, VPN-derived identity, external identity providers, email
  delivery, and automated provisioning.
- Multifactor authentication, passkeys, self-service forgotten-password
  recovery, and administrator access to or direct assignment of another user's
  password.
- Permanent bootstrap or recovery secrets and operator access to application
  data or account administration.
- Multiple concurrent sessions, remembered-device behavior, session or device
  management interfaces, broad roles or permissions, and multiple
  administrators.
- Detailed login, password, session, security, or administrator-action audit
  history and attribution of schedule, publication, lecturer, or academic-data
  mutations to a planner.
- Changes to existing planner workflow authority beyond requiring an active
  named planner; the administrator has no additional scheduling authority.

## Requirements *(mandatory)*

### Functional Requirements

#### Authorization Boundary

- **FR-001**: The product MUST deny every planner page, planner data read, and
  planner mutation by default unless the request belongs to an active named
  planner's current valid session.
- **FR-002**: Authorization MUST be enforced at the protected operation, so
  hidden navigation or controls alone can never permit or prevent access.
- **FR-003**: An unauthorized, inactive, disabled, expired, replaced, or
  otherwise invalid session MUST expose no protected planner or account data
  and MUST apply no requested mutation.
- **FR-004**: Every existing planner workflow MUST remain available to an active
  ordinary planner, except that planner account administration MUST be limited
  to the sole system administrator.
- **FR-005**: The system administrator MUST have the same scheduling and
  academic-data authority as an ordinary planner, with only planner-account
  management added.
- **FR-006**: Lecturer capability credentials MUST be accepted only for their
  existing explicit accountless lecturer capabilities and MUST never satisfy a
  planner authorization decision.
- **FR-007**: Existing FS-015 lecturer access, privacy, safe-failure, token
  lifecycle, and feedback behavior MUST remain unchanged for valid and invalid
  lecturer credentials, whether or not planner authentication is available.

#### Account Identity and Bootstrap

- **FR-008**: A planner account MUST have a required unique login name, required
  display identity, current active or inactive state, and a fixed planner or
  system-administrator access level. Leading and trailing whitespace MUST be
  removed from the login name at account creation, and the resulting entered
  spelling MUST be retained for display.
- **FR-009**: Login matching MUST ignore letter case after removing leading and
  trailing whitespace and MUST identify at most one account. A proposed login
  that differs from an existing login only by letter case or surrounding
  whitespace MUST be rejected.
- **FR-010**: While no administrator exists, one valid deployment-supplied
  bootstrap credential MUST allow a person to establish exactly one active
  named system administrator by choosing the account identity and password.
- **FR-011**: Bootstrap MUST be unavailable once any administrator has been
  established, and no bootstrap attempt may create an ordinary planner or a
  second administrator.
- **FR-012**: The bootstrap credential MUST be purpose-specific, single-use,
  generated by the operator from at least 32 random bytes, and unusable for
  normal login or administrator recovery. An unused value MUST remain current
  across restarts until redeemed or explicitly replaced. Successful bootstrap
  and the resulting administrator existence MUST make that exact value
  permanently unusable.
- **FR-013**: Possession or supply of a startup credential MUST NOT itself create
  an infrastructure operator account or grant the operator planner authority.

#### Planner Creation, Setup, and Passwords

- **FR-014**: Only the current system administrator MUST be able to create a
  planner account, and every newly created planner MUST begin inactive without
  a password selected by the administrator.
- **FR-015**: Creating an account, issuing reset access, or beginning
  reactivation MUST provide a copyable one-time credential or link for manual
  delivery without requiring an email or external identity service.
- **FR-016**: Setup, reset, and reactivation access MUST expire 24 hours after
  issue. The same validity period MUST apply to all three purposes.
- **FR-017**: Each setup, reset, or reactivation credential MUST be usable for
  at most one successful password choice; concurrent submissions MUST produce
  at most one success.
- **FR-018**: Issuing newer setup, reset, or reactivation access for an account
  MUST invalidate every older unredeemed access credential for that account.
- **FR-019**: Successful initial setup or reactivation redemption MUST activate
  the account and consume the credential; successful reset redemption MUST
  restore password login and consume the credential.
- **FR-020**: Issuing reset access MUST immediately invalidate the account's old
  password and current session, without exposing or assigning a replacement
  password to the administrator. This administrator-managed action MUST apply
  only to another planner account and MUST NOT be available for the sole
  administrator's own account.
- **FR-021**: Reactivation MUST require administrator initiation, fresh
  reactivation access, and a new password chosen by the planner; administrator
  initiation alone MUST NOT permit login.
- **FR-022**: An authenticated planner MUST be able to change their own password
  by providing the current password and an acceptable new password.
- **FR-023**: A successful self-service password change MUST invalidate the old
  password and current session and require a new login.
- **FR-024**: A password MUST contain from 12 through 128 characters, MUST permit
  spaces and other normal characters, MUST NOT require any character-class
  composition, and MUST NOT equal the account's login name under the login
  matching rules. After ten consecutive failed login attempts, the product MUST
  refuse further login attempts for that account for 15 minutes without
  changing the generic public failure wording; attempts during the restriction
  MUST NOT extend it. A successful login, administrator-issued password reset,
  or successful administrator recovery MUST clear accumulated login failures
  and any applicable restriction. One-time setup, reset, and reactivation
  access MUST NOT have a separate attempt counter or temporary attempt
  restriction; its expiry, single-use, replacement, concurrency, and generic-
  failure rules remain authoritative.
- **FR-025**: The product MUST NOT provide a self-service Forgot password flow;
  ordinary forgotten-password recovery MUST begin with administrator-issued
  reset access.

#### Login and Session Lifecycle

- **FR-026**: An active account with a valid password MUST be able to sign in
  using its login name and password; inactive, disabled, or invalid credentials
  MUST NOT create a session.
- **FR-027**: Each account MUST have at most one current session across all
  browser contexts, and a new successful login MUST invalidate the earlier
  session before the new session is considered current.
- **FR-028**: A failed login attempt MUST NOT replace or otherwise invalidate an
  already current valid session for that account.
- **FR-029**: A current session MUST expire after 60 minutes without a
  successful user-initiated protected planner request or 12 hours after login,
  whichever occurs first. A successful user-initiated protected planner request
  MUST refresh the inactivity boundary; background activity MUST NOT refresh
  it, and no activity may extend the absolute boundary. The product MUST NOT
  provide an advance session-expiry warning; after expiry, the next protected
  interaction MUST use the approved ended-session wording and route the user to
  sign in again.
- **FR-030**: Logout, browser close, session replacement, inactivity expiry,
  absolute expiry, successful password change, reset issuance, account
  disablement, and successful administrator recovery MUST make the applicable
  former session unusable for every later protected request.
- **FR-031**: Closing and reopening the browser MUST require a new sign-in and
  MUST NOT restore access from the earlier browser session.
- **FR-032**: When authentication expires or is invalidated during a protected
  workflow, the next protected read or action MUST be denied without applying
  the requested mutation and MUST provide a clear route to sign in again.

#### Account Administration and Lifecycle

- **FR-033**: Only the current system administrator MUST be able to list planner
  accounts or create, reset, disable, reactivate, or transfer their access.
- **FR-034**: Disabling an account MUST immediately mark it inactive, invalidate
  its password-based login and current session, and record the most recent
  disablement time.
- **FR-035**: The product MUST reject disabling the sole administrator or any
  other action that would leave no active system administrator. It MUST also
  reject administrator-managed reset access for the sole administrator's own
  account without changing that account's password or session; self-service
  password change and operator-assisted recovery are the only password-change
  paths for that account.
- **FR-036**: The administrator MUST explicitly confirm reset, disablement,
  reactivation initiation, and administrator transfer after the interface
  identifies the affected account and the access consequence.
- **FR-037**: The Planner accounts page MUST show each account's login name,
  display identity, fixed access level, current state as `Aktiv` or `Inaktiv`,
  creation time, and the applicable most recent disablement and reactivation
  times. It MUST NOT show a pending, expired, used, or replaced one-time-access
  indicator. A newly issued setup, reset, or reactivation link or code MUST be
  available only in the immediate issuance result; after that result is left or
  dismissed, the administrator MUST issue fresh access to obtain another
  deliverable value.
- **FR-038**: The Planner accounts page and user-facing diagnostics MUST NOT
  expose raw passwords, password representations, or usable bootstrap,
  recovery, setup, reset, reactivation, or session secrets.
- **FR-039**: No account listing or user-facing history introduced by this slice
  may expose login attempts, password events, session events, action actors,
  reasons, or planner-work attribution.

#### Sole Administrator Transfer and Recovery

- **FR-040**: After bootstrap, the product MUST maintain exactly one active
  system administrator at every externally observable point.
- **FR-041**: The current administrator MUST be able to transfer the additional
  administrator authority only to another currently active planner.
- **FR-042**: Administrator transfer MUST make the target the sole administrator
  and the prior administrator an ordinary active planner as one indivisible
  change, with no intermediate zero- or multi-administrator state.
- **FR-043**: A stale, duplicate, competing, ineligible, or failed transfer MUST
  change neither account's authority.
- **FR-044**: When exactly one administrator exists and the deployment starts
  with a valid purpose-specific recovery credential, that credential MUST allow
  the same administrator to choose a new password without creating or selecting
  another account.
- **FR-045**: Successful administrator recovery MUST atomically invalidate the
  prior password and current session, preserve the administrator identity and
  sole authority, consume the recovery credential, and require normal sign-in
  with the new password.
- **FR-046**: A recovery credential MUST be one-time, startup-supplied,
  purpose-specific, generated by the operator from at least 32 random bytes,
  distinct from every bootstrap value, and unusable for bootstrap, ordinary
  login, another account, or administrator transfer. An unused recovery value
  MUST remain current across restarts until redeemed or explicitly replaced.
  Successful recovery MUST make that exact value permanently unusable; a later
  recovery MUST require a newly generated value.

#### Privacy, Failure, and Accessibility

- **FR-047**: Login, setup, reset, reactivation, bootstrap, and recovery failures
  MUST use safe wording that does not distinguish an unknown account from an
  inactive account, reveal whether a submitted credential was once valid, or
  expose protected planner data.
- **FR-048**: Raw passwords and usable credential or session secrets MUST never
  appear in account listings, success or failure diagnostics, page addresses
  after successful redemption, or accessibility announcements.
- **FR-049**: Login, setup, password change, expiry, access failure, recovery,
  and Planner accounts interactions MUST be operable by keyboard with visible
  focus, programmatic labels, logical focus order, and announced validation and
  status results.
- **FR-050**: Authentication and account state MUST NOT be communicated by color,
  icon, or visual position alone, and errors MUST identify the affected field or
  action plus a safe next step.
- **FR-051**: Authentication and Planner accounts content MUST remain readable
  and operable at narrow supported viewports and at 200% zoom, consistent with
  the application's established responsive patterns.
- **FR-052**: Destructive or authority-changing confirmation dialogs MUST keep
  focus within the dialog while open, identify the affected account and
  consequence, support cancellation, and return focus predictably when closed.
- **FR-053**: Password inputs MUST not redisplay entered password values after a
  failed, expired, or unauthorized submission.
- **FR-054**: All new user-facing wording MUST be German, use the formal `Sie`
  form, reuse the I-002 terminology and actionable-message conventions, and use
  the canonical labels and safe messages defined below.

#### Approved German Authentication Wording

- Account page: `Planer-Konten`
- Login title and primary action: `Anmelden`
- Login fields: `Benutzername` and `Passwort`
- Logout action: `Abmelden`
- Password-change action: `Passwort ändern`
- Account actions: `Planer-Konto erstellen`, `Zugang zurücksetzen`,
  `Deaktivieren`, `Reaktivieren`, and `Administration übertragen`
- Generic login failure: `Die Anmeldung war nicht möglich. Prüfen Sie Ihre
  Angaben und versuchen Sie es erneut. Wenn Sie weiterhin keinen Zugang haben,
  wenden Sie sich an die Systemadministration.`
- Unusable setup, reset, or reactivation access: `Der Zugang ist nicht
  verfügbar. Bitten Sie die Systemadministration um einen neuen Zugangslink.`
- Unusable bootstrap or recovery access: `Der Startzugang ist nicht verfügbar.
  Prüfen Sie die bereitgestellten Zugangsdaten oder wenden Sie sich an den
  Infrastruktur-Betrieb.`
- Ended or expired session: `Ihre Sitzung ist beendet. Melden Sie sich erneut
  an.`
- Successful password setup or reset: `Das Passwort wurde festgelegt. Melden
  Sie sich jetzt an.`

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each
  implemented user story where automated testing is practical.
- **TR-002**: Backend behavior MUST be verified with FastAPI-compatible tests,
  normally using `pytest`.
- **TR-003**: Frontend behavior MUST be verified through React/Vite-appropriate
  build, lint, component, and UI checks relevant to the changed behavior.
- **TR-004**: Any exception to automated test-first work MUST document the
  reason and manual verification path in the plan.
- **TR-005**: Authorization tests MUST enumerate every planner page and planner
  read or mutation and verify denial for no session, malformed session, expired
  session, replaced session, inactive account, disabled account, and lecturer
  capability credentials.
- **TR-006**: Session tests MUST verify successful-login replacement, failed-
  login non-replacement, logout, browser-close behavior, inactivity expiry,
  absolute expiry, password change, reset, disablement, and recovery.
- **TR-007**: Concurrency and stale-state tests MUST prove at-most-one successful
  redemption, exactly one administrator after bootstrap and transfer, and no
  partial account or authority change on failure.
- **TR-008**: Existing FS-015 lecturer capability, privacy, failure, and feedback
  tests MUST remain passing without requiring a planner session.
- **TR-009**: Secret-disclosure tests MUST inspect account listings, page
  addresses after redemption, visible diagnostics, and accessibility status
  text for raw passwords and usable credential or session values.
- **TR-010**: Accessibility verification MUST cover keyboard-only operation,
  focus behavior, programmatic names and errors, status announcements, non-color
  cues, narrow viewports, and 200% zoom for every new user-facing state.

### Key Entities

- **Planner Account**: A named person allowed to use planner work. It has a
  unique login name, display identity, fixed planner or system-administrator
  level, active or inactive state, password eligibility, creation time, and
  applicable most recent disablement and reactivation times. Exactly one active
  account is the system administrator after bootstrap.
- **One-Time Account Access**: Purpose-specific setup, reset, or reactivation
  access manually delivered to one account. It has one purpose, one account
  scope, an issue and expiry state, replacement state, and single-use outcome;
  the usable secret is never part of account listings or diagnostics, and its
  current or historical status is not shown on the Planner accounts page.
- **Planner Session**: The one current browser-bound authenticated access state
  for an account. It has an account scope, inactivity boundary, absolute
  boundary, and current or invalidated state. It cannot be used as a lecturer
  capability.
- **Bootstrap Access**: One-time startup-supplied authority to establish the first
  named administrator while none exists. The operator-generated value may
  remain current across restarts until redemption or explicit replacement, but
  can never be reused after successful bootstrap. It is not an account, normal
  login, or recovery credential.
- **Administrator Recovery Access**: One-time startup-supplied authority to let the
  existing sole administrator choose a new password. It cannot create an
  account, select a different account, transfer authority, or grant operator
  access. The operator-generated value may remain current across restarts until
  redemption or explicit replacement, but successful use permanently consumes
  that exact value.
- **Account Lifecycle Summary**: The minimal administrator-visible account
  state consisting only of current identity and access state, creation time,
  and applicable most recent disablement and reactivation times.
- **Lecturer Capability**: The existing FS-015 minimum-scope accountless access
  credential. Its scope and lifecycle remain unchanged and it has no
  relationship that can confer planner or account-administration authority.

## Dependencies

- **I-001 Containerized Distribution** supplies the supported startup boundary
  through which an operator provides one-time bootstrap or recovery material.
- **FS-015 Accountless Lecturer Token Review** supplies the anonymous capability
  boundary and regression contract that MUST remain unchanged.
- **FS-019 Streamline Schedule Workspace** supplies the current planner shell,
  navigation, and planner workflows that become protected.
- **I-002 Terminology, European Dates, and Actionable Messages** supplies the
  German terminology, responsive presentation, and safe actionable-message
  conventions for the new user-facing states.
- Production credential and session exchange is protected in transit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the complete authorization inventory, 100% of planner pages,
  planner reads, and planner mutations expose no planner data and apply no
  change for anonymous users, invalid sessions, inactive accounts, disabled
  accounts, and lecturer capability credentials.
- **SC-002**: From a deployment with no administrator, a first administrator can
  complete bootstrap and reach an existing planner workflow in no more than
  five minutes without VPN identity, SSO, email, or operator access to planner
  data; 100% of later bootstrap attempts fail to create an account.
- **SC-003**: An administrator can create an inactive planner and obtain manual
  setup access in no more than three minutes, and a planner with that access can
  choose a password and complete sign-in in no more than three minutes.
- **SC-004**: For every specified invalidation event, the former session fails
  on its next protected request; a newer successful login leaves exactly one
  usable session for the account in 100% of acceptance tests.
- **SC-005**: Disablement prevents the affected account's next protected read,
  mutation, and login attempt in 100% of acceptance tests, while successful
  reactivation restores access only after fresh one-time access and a new
  password.
- **SC-006**: Across successful, failed, concurrent, repeated, and stale
  bootstrap and transfer tests, every observable state after bootstrap contains
  exactly one active system administrator and no partial authority change.
- **SC-007**: A locked-out administrator can complete operator-assisted recovery
  and resume normal sign-in in no more than five minutes without creating a new
  account, changing administrator identity, or using an external identity or
  email provider.
- **SC-008**: 100% of established FS-015 accountless lecturer acceptance tests
  continue to pass, and 100% of attempts to use lecturer credentials for
  planner access are denied.
- **SC-009**: Inspection of every account listing, visible or announced
  diagnostic, and post-redemption address finds zero raw passwords and zero
  usable bootstrap, recovery, setup, reset, reactivation, or session secrets.
- **SC-010**: Account creation, disablement, and successful reactivation show
  the correct current state and corresponding lifecycle time within one minute
  of the completed action in 100% of acceptance tests, with no additional audit
  history displayed.
- **SC-011**: At least 90% of representative planner and administrator
  participants complete sign-in, planner setup, password change, disablement,
  reactivation, and transfer correctly on their first attempt using only the
  interface guidance.
- **SC-012**: All new authentication and account-administration journeys can be
  completed with keyboard-only input at a narrow supported viewport and 200%
  zoom, with every error and state change available without color alone.

## Assumptions

- Local password authentication, one browser-bound current session per account,
  and exactly one system administrator are confirmed product decisions.
- The system administrator is always also a planner and has no broader
  scheduling, publication, lecturer, or academic-data authority than any other
  active planner.
- Account creation time is retained once. The account page shows the most recent
  disablement and reactivation times when applicable rather than a detailed
  event history.
- Successful setup and reactivation are the points at which an inactive account
  becomes active; merely issuing one-time access does not activate it.
- Reset issuance invalidates the old password and current session immediately;
  the administrator is expected to deliver the newly displayed one-time access
  through an appropriate manual channel.
- A browser-close outcome is verified from the user's perspective: reopening
  the browser does not restore planner access and requires a new sign-in.
- An authenticated request that is accepted before a concurrent invalidation
  remains indivisible, but no later protected request may use the invalidated
  session.
- Bootstrap and recovery material is generated by the operator and supplied
  through the deployment boundary established by I-001. An unused value may
  remain current across restarts, but successful redemption permanently
  consumes it. Operators are expected to remove a consumed value from startup
  configuration, while the product's single-use guarantee does not depend on
  that cleanup. Startup material is never an identity source for the operator.
- The canonical German labels and messages in FR-054 are final for this slice.
  Content review verifies their consistency with I-002 and MUST NOT change them
  or weaken their minimum-disclosure behavior without updating this
  specification first.
- Authentication is application-owned. A VPN may be used only as optional
  defense in depth and is neither required nor trusted as an identity source.
- Password, one-time-access, and session transport is protected in production.
- No external service, new authenticated actor, general authorization model, or
  broad audit capability is required for this slice.
