# Planner Access UI Contract

## Route dispatch and protected shell

Keep the current dependency-free `main.tsx` route classification. Exact routes:

| Route | Surface | Planner session required |
|---|---|---:|
| `/lecturer-review/` | Existing accountless lecturer bundle | No |
| `/login/` | Login card | No |
| `/bootstrap/` | First-administrator setup card | No |
| `/account-access/` | Setup/reset/reactivation password card | No |
| `/administrator-recovery/` | Operator-assisted recovery card | No |
| `/` and planner entry paths | Existing planner shell through `PlannerApplication` | Yes |

`PlannerApplication` performs a non-activity `GET /api/auth/session`. It renders
no planner component until safe current-account metadata returns. `401` renders
login. A protected `401` emitted by the shared planner request helper
immediately clears the in-memory account state, unmounts the protected shell,
and focuses/announces the ended-session result.

Do not keep authentication state or secrets in `localStorage`, `sessionStorage`,
history state, URLs, logs, or a service worker. Safe current-account metadata
lives only in React memory.

## Shared planner request behavior

The planner/authentication request helper:

- uses `credentials: "include"`;
- adds `X-CSRF-Protection: 1` to unsafe operations;
- adds `X-Planner-Activity: user` only when the caller identifies a deliberate
  foreground planner interaction;
- emits one session-invalidated event for a protected `401`;
- does not retry authentication or replay a mutation automatically.

Initial session inspection and future automatic/background requests use the
non-activity form. Public terminology and lecturer APIs remain independent
direct calls with `credentials: "omit"` and never receive planner headers.

## Account-access fragment handling

The deliverable link is `${origin}/account-access/#/${credential}`. Before
terminology fetch, dynamic import, analytics/logging, or any other network work:

1. recognize only the exact `/account-access/` route;
2. extract the 43-character opaque value from the fragment;
3. call `history.replaceState` to remove the fragment;
4. pass the value directly as an in-memory prop to the account-access page;
5. clear the prop after submission, route change, or component removal.

Malformed or absent fragments show the same unusable-access state. The page
never writes the secret back into an address, diagnostic, announcement, or
storage.

## Authentication surfaces

All surfaces reuse the existing card, form, focus, responsive, and formal German
language. Password confirmation is a client-side safeguard and is not sent to
the API.

### Login

- Title/action: `Anmelden`.
- Fields: `Benutzername`, `Passwort`.
- On every failure, show exactly the approved generic login wording, clear the
  password field, retain only the login name, and focus the error/first invalid
  control.
- Links to bootstrap and operator recovery may remain visible; their APIs reveal
  no account existence or identity.

### Bootstrap

- Fields: startup credential, display identity, login name, password,
  confirmation.
- Never auto-login.
- Success directs to `Anmelden`; failure uses the approved generic start-access
  wording and clears credential/password controls.

### Account setup/reset/reactivation

- One page handles all three purposes because the server resolves purpose and
  account from the opaque value.
- Fields: new password and confirmation only.
- Success shows `Das Passwort wurde festgelegt. Melden Sie sich jetzt an.` and a
  login action; never auto-login.
- Missing, expired, replaced, used, malformed, or inapplicable access shows
  `Der Zugang ist nicht verfügbar. Bitten Sie die Systemadministration um einen neuen Zugangslink.`
- Failure clears password controls and never reveals purpose or account.

### Administrator recovery

- Fields: startup recovery credential, new password, confirmation.
- No login name or account selector; the server targets the sole administrator.
- Success requires normal login. Failure uses the approved generic start-access
  wording and clears all secret/password controls.

### Password change

- Protected surface with current password, new password, and confirmation.
- Success clears planner state and returns to login because the session ended.
- Failure clears all password controls and leaves the existing session/password
  unchanged.

## Planner navigation

The protected application navigation adds:

- safe current display identity;
- `Passwort ändern`;
- `Abmelden`;
- `Planer-Konten` only when `currentAccount.isAdministrator` is true.

The backend remains authoritative. If account management returns `403`, remove
the account view/navigation, refresh safe session metadata, and return to the
ordinary planner shell without exposing target details.

## Planner accounts

Use a semantic list of responsive cards (`ul`, one `li` per account, and `dl`
for labeled values), not a wide table. Display exactly:

- display identity;
- login name;
- `Planer` or `Systemadministration`;
- `Aktiv` or `Inaktiv` as explicit text;
- creation time;
- applicable latest disablement time;
- applicable latest reactivation time.

Do not display password/setup state, pending/expired access, login attempts,
sessions, event history, actors, reasons, or planner-work attribution.

Available actions are derived from the returned state but enforced again by the
backend:

| Account state | Available administrator actions |
|---|---|
| New inactive planner | Reissue setup access if needed |
| Active ordinary planner | Reset access, disable, transfer administration |
| Disabled ordinary planner | Issue/reissue reactivation access |
| Current administrator | No self-reset or disable; self password change only |

Creation, reset, reactivation initiation, disablement, and transfer use the
current hidden `revision`. Stale `409` results refresh the list and explain that
the account changed without revealing security state.

## Confirmation dialog

Reset, disablement, reactivation initiation, and administrator transfer require
an explicit confirmation dialog that:

- names the affected display identity and login safely;
- states the immediate consequence;
- puts initial focus on Cancel;
- traps focus while open;
- closes on Escape as cancellation;
- restores focus to the triggering action when still present;
- announces the safe result after close.

Self-reset/disable controls are absent. Transfer targets include only other
active ordinary planners, but stale/ineligible server responses remain safe.

## One-time access result

After create, reset, or reactivation issuance:

- compose the fragment URL only in component memory;
- show purpose-neutral manual-delivery guidance and the 24-hour expiry;
- provide `Link kopieren`, manual selection fallback, and `Schließen`;
- announce only that access was created/copied, never announce the URL;
- clear the URL on dismissal, route change, another action, or component
  removal;
- replace and clear any older result when a newer issuance succeeds.

Returning to the account list never restores the value. The administrator must
issue fresh access to see another deliverable link.

## Accessibility and responsive acceptance

- Every input has a programmatic German label, autocomplete intent where safe,
  visible focus, `aria-invalid`, and linked error text.
- Safe errors use `role="alert"`; non-error outcomes use `role="status"` and do
  not repeat secrets.
- After submit, focus moves to the first invalid field or result heading.
- Password controls are blank after failed, expired, or unauthorized submit.
- State is expressed in text and not only by color/icon/position.
- Controls meet the application's established target sizing and remain keyboard
  operable.
- At 360 px, the 820 px application breakpoint, and 200% zoom, cards stack,
  actions wrap, and ordinary text requires no two-dimensional scrolling.
- Dialog focus trap, Escape/cancel, and focus restoration follow the existing
  navigation/removal-dialog patterns.

Manual browser evidence supplements Vitest/jsdom for zoom, responsive layout,
browser-close semantics, and assistive-technology announcements because the
repository has no browser E2E or automated accessibility dependency.
