# Data Model: FS-016 Authenticated Planner Access and Account Administration

## Conventions

- Identifiers use the repository's existing integer primary-key convention.
- Timestamps are timezone-aware UTC values and are rendered through the existing
  European/German date-time conventions.
- Secret values are generated from at least 32 random bytes. Only lowercase
  64-character SHA-256 hex digests are persisted.
- Human passwords are persisted only as encoded Argon2id hashes.
- Login matching uses `trim(casefold(login_name))`; the trimmed original spelling
  remains available for display.
- All security-sensitive transitions are committed atomically after the service
  reloads the current rows inside the write transaction.

## Entity: Planner Account

Table: `planner_accounts`

| Field | Type | Null | Rules |
|---|---|---:|---|
| `id` | integer | no | Primary key |
| `login_name` | string | no | Trimmed display spelling; 1–128 characters |
| `normalized_login_name` | string | no | Case-folded trimmed login; unique |
| `display_name` | string | no | Named human identity; trimmed; 1–200 characters |
| `password_hash` | string | yes | Argon2id encoded hash; null before setup, after reset issuance, and while disabled |
| `is_active` | boolean | no | `false` on creation; only successful setup/reactivation makes it true |
| `is_administrator` | boolean | no | At most one `true`; administrator must be active |
| `failed_login_count` | integer | no | Default 0; non-negative |
| `login_blocked_until` | timestamp | yes | End of the fixed 15-minute restriction |
| `revision` | integer | no | Starts at 1; increments on administrator-visible/actionable account changes |
| `created_at` | timestamp | no | Immutable creation time |
| `disabled_at` | timestamp | yes | Most recent successful disablement |
| `reactivated_at` | timestamp | yes | Most recent successful reactivation redemption |

### Constraints and indexes

- Unique constraint on `normalized_login_name`.
- Partial unique index on a constant/administrator flag where
  `is_administrator = true`, enforcing at most one administrator.
- Check: `is_administrator = false OR is_active = true`.
- Check: `failed_login_count >= 0`.
- Service invariant after bootstrap: exactly one account is active and marked
  administrator.
- The sole administrator cannot be disabled or receive administrator-managed
  reset access.

### Safe account projection

Only these fields appear in account listings:

- `id`
- `loginName`
- `displayName`
- `accessLevel` (`planner` or `administrator`)
- `state` (`active` or `inactive`, rendered `Aktiv`/`Inaktiv`)
- `revision`
- `createdAt`
- `disabledAt`
- `reactivatedAt`

`revision` is transport metadata for stale-action prevention and need not be
visually presented. Password hashes, retry state, session state, one-time-access
state, and startup credential state never enter this projection.

## Entity: One-Time Account Access

Table: `planner_account_access`

| Field | Type | Null | Rules |
|---|---|---:|---|
| `id` | integer | no | Primary key |
| `account_id` | integer | no | Foreign key to planner account; unique |
| `secret_digest` | char(64) | no | Unique SHA-256 hex digest |
| `purpose` | enum string | no | `setup`, `reset`, or `reactivation` |
| `issued_at` | timestamp | no | Issue time |
| `expires_at` | timestamp | no | Exactly 24 hours after issue |

### Constraints and lifecycle

- Unique `account_id` allows only the newest account-access credential.
- Unique `secret_digest` prevents ambiguous redemption.
- New issuance deletes/replaces any earlier row for the same account.
- Successful redemption deletes the row in the same transaction as the account
  update.
- Expired rows may be lazily deleted when presented or replaced; they are never
  shown in account listings.
- Disablement removes any existing access row. Reactivation issuance then
  creates a fresh purpose-specific row.

### Purpose-specific outcomes

| Purpose | Required account state before use | Successful outcome |
|---|---|---|
| `setup` | Inactive, never completed setup | Store password hash, activate account, consume access |
| `reset` | Active but password cleared by reset issuance | Store password hash, remain active, consume access |
| `reactivation` | Inactive after disablement | Store password hash, activate, set `reactivated_at`, consume access |

No redemption creates a session; the person signs in normally afterward.

## Entity: Planner Session

Table: `planner_sessions`

| Field | Type | Null | Rules |
|---|---|---:|---|
| `id` | integer | no | Primary key |
| `account_id` | integer | no | Foreign key to planner account; unique |
| `secret_digest` | char(64) | no | Unique SHA-256 hex digest |
| `created_at` | timestamp | no | Login time |
| `last_activity_at` | timestamp | no | Last successful user-initiated protected request |
| `absolute_expires_at` | timestamp | no | Exactly 12 hours after creation |

### Validity rule

A session is valid only when all of the following hold at request time:

1. The submitted raw cookie hashes to the current session row.
2. The related account is active and has a usable password state.
3. `now < last_activity_at + 60 minutes`.
4. `now < absolute_expires_at`.

At equality, the session is expired. Expired rows are deleted lazily and the
cookie is cleared. A successful request marked `X-Planner-Activity: user`
updates `last_activity_at` after the response only if the same digest is still
current. Background, failed, and public requests do not refresh inactivity.

### Invalidation events

Delete the account's session row on:

- successful replacement login;
- explicit logout;
- successful self-service password change;
- administrator reset issuance;
- account disablement;
- successful administrator recovery.

Deletion makes every copied form of the former cookie unusable at the next
protected request.

## Entity: Startup Credential State

Table: `planner_startup_credentials`

| Field | Type | Null | Rules |
|---|---|---:|---|
| `secret_digest` | char(64) | no | Primary key; digest is globally unique across purposes |
| `purpose` | enum string | no | `bootstrap` or `recovery` |
| `state` | enum string | no | `current`, `consumed`, or `replaced` |
| `first_seen_at` | timestamp | no | First valid startup configuration observation |
| `retired_at` | timestamp | yes | Redemption or replacement time |

### Startup reconciliation

- Check constraints restrict `purpose` and `state` to the listed values.
- A partial unique index on `purpose` where `state = 'current'` permits at most
  one current bootstrap and one current recovery credential.
- The digest primary key prevents reuse across purposes and across later
  rotations.

For each configured purpose:

1. Validate that the raw value is exactly 64 hexadecimal characters encoding 32
   random bytes; reject invalid startup configuration.
2. Reject equal bootstrap and recovery values.
3. Hash/decode without logging and compare with the registered rows.
4. If the digest is the same current value, leave it current.
5. If it is new, mark the prior current row for that purpose `replaced` and
   insert the new row as `current` in one transaction.
6. If it was consumed, replaced, or registered for the other purpose, do not
   make it current; start the application with that value unavailable and emit
   only a secret-free operator warning.
7. Discard the raw environment value after reconciliation.

An absent environment value does not replace or retire a persisted unused
current credential. This is what lets an operator supply a value once and lets
it survive later restarts until redemption or explicit replacement. If no
current bootstrap row exists while there is no administrator, starting is still
allowed but all planner work remains denied.

## Relationships

```text
planner_accounts (1) ---- (0..1) planner_account_access
planner_accounts (1) ---- (0..1) planner_sessions
planner_startup_credentials      independent technical one-time state
```

Account access and sessions use `ON DELETE CASCADE` as a database safety net,
although account deletion is not exposed by this slice. Startup credentials do
not identify an account; recovery discovers the sole administrator only after a
valid purpose-specific credential is claimed.

## State transitions

### Account lifecycle

```text
create + setup issued
  -> inactive/passwordless
  -> successful setup redemption
  -> active/password set
  -> reset issued
  -> active/passwordless
  -> successful reset redemption
  -> active/password set

active/password set
  -> disable
  -> inactive/passwordless
  -> reactivation issued
  -> inactive/passwordless
  -> successful reactivation redemption
  -> active/password set
```

Issuing reactivation access does not activate the account. Reissuing setup,
reset, or reactivation replaces the current access row without changing the
visible `Aktiv`/`Inaktiv` state.

### Login restriction

```text
0..9 consecutive known-account failures
  -> increment count
10th consecutive failure
  -> set blocked_until = now + 15 minutes
attempt during block
  -> same generic failure; boundary unchanged
attempt at/after boundary
  -> begin a new failure sequence
successful login, reset redemption, or recovery
  -> count = 0; blocked_until = null
```

Failed login never deletes or replaces an existing current session.

### Administrator lifecycle

```text
no administrator + valid bootstrap
  -> create active administrator atomically

active administrator + another active planner + confirmed current revisions
  -> demote current and promote target in one transaction
  -> exactly one externally observable administrator
```

No action can disable, reset through administrator access, or transfer to the
current sole administrator. Recovery changes only the current administrator's
password/security state; it never changes administrator identity.

## Concurrency invariants

- Unique normalized login permits at most one account for a matching login.
- Unique administrator index permits at most one administrator.
- Unique session account permits at most one session per account.
- Unique account-access account permits at most one redeemable account access
  row per account.
- Claimed-row/reload checks permit at most one successful credential redemption.
- `expectedRevision` plus transaction-time authority checks reject stale
  account actions without partial updates.
- Every invalidating account mutation and its session/access deletion share one
  transaction.

## Migration and compatibility

Migration `0010_planner_authentication.py` creates the four tables and their
constraints without backfilling existing planning or lecturer data. Schema
recognition accepts only:

- a complete FS-015 schema with none of the new authentication tables, which is
  upgraded through `0010`; or
- the complete FS-016 schema.

Any partial authentication-table set is unsupported and causes startup to fail
safely. Existing lecturer token, feedback, schedule, publication, and academic
data rows remain unchanged.
