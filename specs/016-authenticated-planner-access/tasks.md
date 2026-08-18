# Tasks: FS-016 Authenticated Planner Access and Account Administration

**Input**: Design documents from `specs/016-authenticated-planner-access/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, and `quickstart.md`

**Tests**: Tests are required before corresponding production changes wherever
automated verification is practical. Manual verification is limited to the
browser-cookie-restoration constraint, real assistive-technology behavior,
responsive/200%-zoom presentation, production HTTPS cookies, and container
architecture/memory evidence described in `plan.md` and `quickstart.md`.

**Discovery rule**: If implementation exposes behavior that differs from the
approved requirements or contracts, stop before changing production behavior,
update `spec.md` and the affected design/task artifacts, then resume test-first
delivery.

**Organization**: Tasks are grouped by user story. P1 stories are ordered US1,
US2, US3, then US6 so the protected planner foundation exists before the
lecturer regression boundary is finalized. P2 stories follow as US4 and US5;
the P3 administration/accessibility story is last.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on an incomplete task.
- **[Story]**: Maps directly to the user story number in `spec.md`.
- Every checklist item names its exact target file or files.

---

## Phase 1: Setup and Baseline Evidence

**Purpose**: Isolate the security-sensitive implementation and establish the
pre-change verification/configuration baseline.

- [ ] T001 Create or switch to `codex/fs-016-authenticated-planner-access`, run the existing focused backend/client suites, and record the branch, dirty-worktree baseline, commands, and pre-existing failures in `specs/016-authenticated-planner-access/quickstart.md`
- [ ] T002 [P] Add the direct Argon2 runtime dependency and production-image import check in `backend/requirements-runtime.txt` and `infrastructure/docker/Dockerfile`
- [ ] T003 [P] Add optional bootstrap/recovery startup variable passthrough with secret-free examples in `.env.example` and `compose.yaml`

**Checkpoint**: Implementation is isolated, the baseline is known, and required
dependency/configuration entry points exist without creating credentials.

---

## Phase 2: Foundational Persistence and Planner Request Boundary

**Purpose**: Create the shared database and frontend request foundations used by
every story.

**CRITICAL**: Complete this phase before user-story production work.

### Foundational tests

- [ ] T004 Add failing fresh-database, FS-015-upgrade, partial-schema rejection, column/check/unique-index, one-session/account, one-access/account, and one-current-startup-purpose migration tests in `backend/tests/db/test_migrations.py`
- [ ] T005 [P] Create deterministic clock, file-backed SQLite, startup-credential, account, session-cookie, and authenticated planner test helpers without a production bypass in `backend/tests/planner_auth_fixtures.py`
- [ ] T006 [P] Add failing tests for a shared planner fetch boundary covering `credentials: "include"`, unsafe-request CSRF headers, explicit activity marking, non-activity inspection, one 401 invalidation signal, no automatic mutation replay, and no secret persistence in `client/src/api/plannerFetch.test.ts`

### Foundational implementation

- [ ] T007 Implement the four FS-016 SQLAlchemy entities, foreign keys, checks, digest uniqueness, partial unique administrator/current-startup indexes, and account revision field in `backend/app/models/planning.py` and `backend/app/db/migrations/0010_planner_authentication.py`
- [ ] T008 Recognize only complete pre-0010 or complete FS-016 schemas, run migration 0010, and reject partial authentication schemas in `backend/app/db/schema.py`
- [ ] T009 Implement the shared credentialed planner/auth fetch helper justified by the ten existing call sites in `client/src/api/plannerFetch.ts`

**Checkpoint**: The persistent invariants and one frontend planner request
boundary are ready; no authentication endpoint is public yet.

---

## Phase 3: User Story 1 - Establish the First Administrator Safely (Priority: P1) MVP

**Goal**: Register and redeem one durable operator bootstrap credential, create
the sole named administrator, deny anonymous planner access by default, and let
that administrator sign in and use existing planner workflows.

**Independent Test**: Start with no administrator and one valid bootstrap
credential, establish the administrator, sign in and complete an existing
planner workflow, then prove anonymous access and every later bootstrap attempt
expose no planner data and create no account.

### Tests for User Story 1 (write before implementation)

- [ ] T010 [US1] Add failing service tests for Argon2 parameters/rehash, 12–128 character password acceptance, login-name inequality, trim/casefold uniqueness, dummy verification, ten-failure/15-minute restriction, startup registration across restarts, absence persistence, replacement, consumed/cross-purpose replay, bootstrap gating, and secret-free diagnostics in `backend/tests/services/test_planner_auth.py`
- [ ] T011 [P] [US1] Add failing file-backed concurrency tests proving one bootstrap winner, one normalized login, atomic startup consumption, and no partial administrator/account state in `backend/tests/services/test_planner_auth_concurrency.py`
- [ ] T012 [P] [US1] Add failing API contract tests for `POST /api/auth/bootstrap`, `POST /api/auth/login`, `GET /api/auth/session`, and administrator-only `GET /api/planner-accounts`, covering generic German failures, no automatic bootstrap login, safe current-account/self-list projection, no-store responses, and production/development cookie attributes in `backend/tests/api/test_planner_auth.py`
- [ ] T013 [P] [US1] Add a failing registered-route/page authorization inventory for anonymous, malformed, unknown, inactive, and passwordless sessions; mutation snapshot preservation; exact public auth exceptions; CSRF/content-type rejection; protected FastAPI docs; and production CORS denial in `backend/tests/api/test_planner_authorization.py`, `backend/tests/test_frontend.py`, and `backend/tests/test_main.py`
- [ ] T014 [P] [US1] Add failing strict transport tests for bootstrap, login, session inspection, minimal administrator account listing, safe errors, and absence of credential/password echoing in `client/src/api/authentication.test.ts`
- [ ] T015 [P] [US1] Add failing React tests proving the planner shell never mounts before successful inspection, login failures clear only the password, bootstrap never auto-signs in, exact German messages are announced, the administrator can reach a read-only self account listing, and current account state stays in memory only in `client/src/PlannerApplication.test.tsx`, `client/src/pages/LoginPage.test.tsx`, `client/src/pages/BootstrapPage.test.tsx`, and `client/src/pages/PlannerAccountsPage.test.tsx`
- [ ] T016 [P] [US1] Add failing exact-route tests for `/login/` and `/bootstrap/`, lazy planner/auth loading, and preservation of the isolated lecturer route in `client/src/main.test.tsx`
- [ ] T017 [P] [US1] Update planner API transport tests to require the shared credentials/CSRF/activity contract while preserving public `credentials: "omit"` expectations in `client/src/api/academicCatalog.test.ts`, `client/src/api/calendarWorkspace.test.ts`, `client/src/api/conflictAwareGeneration.test.ts`, `client/src/api/draftSchedule.test.ts`, `client/src/api/examScheduling.test.ts`, `client/src/api/holidayCalendar.test.ts`, `client/src/api/planningOptions.test.ts`, `client/src/api/resourceCatalog.test.ts`, `client/src/api/scheduleLifecycle.test.ts`, and `client/src/api/lecturerReview.test.ts`
- [ ] T018 [US1] Replace anonymous local TestClient setup with the shared authenticated planner fixture for existing planner behavior while preserving separate no-session public calls in `backend/tests/api/test_academic_catalog.py`, `backend/tests/api/test_calendar_workspace.py`, `backend/tests/api/test_conflict_aware_generation.py`, `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_exam_scheduling.py`, `backend/tests/api/test_holiday_calendar.py`, `backend/tests/api/test_multi_course_generation.py`, `backend/tests/api/test_planning_options.py`, `backend/tests/api/test_resource_catalog.py`, `backend/tests/api/test_schedule_lifecycle.py`, `backend/tests/api/test_lecturer_review.py`, `backend/tests/api/test_lecturer_calendar_export.py`, `backend/tests/performance/test_academic_catalog_performance.py`, `backend/tests/performance/test_lecturer_review_performance.py`, and `backend/tests/performance/test_lecturer_calendar_export_performance.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Define strict bootstrap, login, current-account, minimal account-list, and safe authentication error schemas without secret-bearing response fields in `backend/app/schemas/planner_auth.py`
- [ ] T020 [US1] Implement password hashing/verification, login normalization/retry state, startup credential reconciliation, atomic bootstrap, session issuance/replacement, safe current-account lookup, administrator authorization, minimal self account listing, and secret-free logging in `backend/app/services/planner_auth.py`
- [ ] T021 [US1] Expose bootstrap, login, session inspection, and administrator-only account listing with exact cookie/no-store/generic-failure behavior in `backend/app/api/planner_auth.py`
- [ ] T022 [US1] Register startup reconciliation and the auth router, replace anonymous planner access with the exact-public-allowlist/default-deny middleware, require JSON plus `X-CSRF-Protection: 1` on unsafe auth/planner operations, restrict CORS to development origins, and protect planner/docs entry paths in `backend/app/main.py` and `backend/app/frontend.py`
- [ ] T023 [P] [US1] Implement strict frontend bootstrap/login/session and minimal administrator account-list adapters without browser persistence or error-detail expansion in `client/src/api/authentication.ts`
- [ ] T024 [P] [US1] Move academic/resource/holiday planner calls to the shared request boundary in `client/src/api/academicCatalog.ts`, `client/src/api/resourceCatalog.ts`, and `client/src/api/holidayCalendar.ts`
- [ ] T025 [P] [US1] Move schedule/calendar/generation planner calls to the shared request boundary in `client/src/api/calendarWorkspace.ts`, `client/src/api/conflictAwareGeneration.ts`, `client/src/api/draftSchedule.ts`, and `client/src/api/examScheduling.ts`
- [ ] T026 [P] [US1] Move planning options, schedule lifecycle, and only the planner half of lecturer review to the shared request boundary while retaining direct public omission in `client/src/api/planningOptions.ts`, `client/src/api/scheduleLifecycle.ts`, and `client/src/api/lecturerReview.ts`
- [ ] T027 [US1] Implement the in-memory authentication gate, login/bootstrap cards, exact path dispatch, post-login planner mounting, anonymous login routing, and administrator navigation to a read-only minimal self account list in `client/src/PlannerApplication.tsx`, `client/src/pages/LoginPage.tsx`, `client/src/pages/BootstrapPage.tsx`, `client/src/pages/PlannerAccountsPage.tsx`, `client/src/components/ApplicationNavigation.tsx`, `client/src/main.tsx`, and `client/src/App.tsx`

**Checkpoint**: US1 is independently demonstrable: exactly one first
administrator can be established, anonymous planner access is denied, and that
administrator can sign in and use existing planner work.

---

## Phase 4: User Story 2 - Set Up and Use a Named Planner Account (Priority: P1)

**Goal**: Let the administrator create an inactive named planner, manually
deliver replaceable 24-hour setup access, and let the planner choose a password,
sign in, use all planner workflows, and receive no administration authority.

**Independent Test**: Create an inactive planner, redeem manually delivered
setup access once, sign in and exercise representative planner reads/mutations,
then prove replay/expiry/replacement fail safely and the planner cannot list or
manage accounts.

### Tests for User Story 2 (write before implementation)

- [ ] T028 [US2] Add failing service tests for inactive creation, normalized duplicate rejection, 256-bit setup issuance, SHA-256-only persistence, one current access/account, setup reissue/replacement, 24-hour equality expiry, single-use redemption, password policy, activation, retry reset, and no session creation in `backend/tests/services/test_planner_auth.py`
- [ ] T029 [P] [US2] Add failing file-backed concurrency tests proving at-most-one setup redemption and safe create/reissue races without partial activation in `backend/tests/services/test_planner_auth_concurrency.py`
- [ ] T030 [P] [US2] Add failing API tests for administrator-only `POST /api/planner-accounts`, `POST /api/planner-accounts/{accountId}/setup-access`, public account-access redemption, exact one-time response shape, ordinary-planner list/action 403 plus representative planner read/mutation success, revision conflicts, generic expiry/replay failures, and listing omission of access/password/session/retry state in `backend/tests/api/test_planner_auth.py`
- [ ] T031 [P] [US2] Add failing frontend transport tests for account list/create/setup reissue and account-access redemption, including exact-key validation and one-time-secret responses in `client/src/api/authentication.test.ts`
- [ ] T032 [P] [US2] Add failing fragment tests proving `/account-access/#/<secret>` is scrubbed before terminology/network/module work and never reaches history/storage/logs, plus page tests for setup success, generic unusable access, cleared password fields, no auto-login, and safe focus/status behavior in `client/src/main.test.tsx` and `client/src/pages/AccountAccessPage.test.tsx`
- [ ] T033 [P] [US2] Add failing administrator page tests for inactive account creation, minimal list projection, admin-only navigation, setup link copy/manual fallback/dismissal/replacement, memory-only secret lifetime, and ordinary-planner denial in `client/src/pages/PlannerAccountsPage.test.tsx`, `client/src/components/OneTimeAccessResult.test.tsx`, and `client/src/components/ApplicationNavigation.test.tsx`

### Implementation for User Story 2

- [ ] T034 [P] [US2] Extend strict account, revision, one-time access, creation, setup-reissue, and redemption schemas in `backend/app/schemas/planner_auth.py`
- [ ] T035 [US2] Implement administrator authorization, minimal account listing, inactive account creation, setup access replacement/expiry/redemption, atomic activation, and safe ordinary-planner denial in `backend/app/services/planner_auth.py`
- [ ] T036 [US2] Expose account list/create/setup-reissue and account-access redemption with one-time no-store responses in `backend/app/api/planner_auth.py`
- [ ] T037 [P] [US2] Implement strict account administration and redemption adapters in `client/src/api/authentication.ts`
- [ ] T038 [US2] Implement synchronous account-access fragment scrubbing and the shared setup/reset/reactivation password page without purpose/account disclosure or automatic login in `client/src/main.tsx` and `client/src/pages/AccountAccessPage.tsx`
- [ ] T039 [US2] Extend the administrator account view with inactive creation/setup reissue and implement the transient one-time access copy/manual fallback/dismissal result in `client/src/pages/PlannerAccountsPage.tsx`, `client/src/components/OneTimeAccessResult.tsx`, `client/src/components/ApplicationNavigation.tsx`, and `client/src/App.tsx`

**Checkpoint**: US2 is independently demonstrable from administrator creation
through ordinary planner setup/sign-in, with no account-management authority or
reusable displayed secret.

---

## Phase 5: User Story 3 - Keep One Current Session per Account (Priority: P1)

**Goal**: Enforce one current server-side session per account, replacement by a
later successful login, explicit logout/password-change invalidation, 60-minute
inactivity, 12-hour absolute expiry, and immediate protected-UI removal on 401.

**Independent Test**: Sign in from two browser contexts, prove the second login
replaces the first while failed login does not, and exercise logout, activity,
both expiries, password change, and browser-session-cookie behavior against a
protected read and mutation.

### Tests for User Story 3 (write before implementation)

- [ ] T040 [US3] Add failing service tests for one-session/account replacement, failed-login non-replacement, malformed/current digest checks, active/password state, inactivity and absolute equality expiry, marked-success-only activity refresh, logout, self-password proof/change, and all applicable session deletions in `backend/tests/services/test_planner_auth.py`
- [ ] T041 [P] [US3] Add failing API tests for logout idempotence, password-change validation/invalidation, cookie clearing, no-store headers, ended-session wording, activity versus background requests, and rejected mutation preservation in `backend/tests/api/test_planner_auth.py` and `backend/tests/api/test_planner_authorization.py`
- [ ] T042 [P] [US3] Extend fetch/gate tests for one invalidation event, immediate protected-tree/data unmount, stale 401 ordering, no automatic retry, ended-session focus/status, and non-touch session inspection in `client/src/api/plannerFetch.test.ts` and `client/src/PlannerApplication.test.tsx`
- [ ] T043 [P] [US3] Add failing UI tests for explicit logout, current/new/confirmation password change, wrong-current preservation, cleared password controls, successful return to login, current display identity, and no advance-expiry warning in `client/src/pages/PasswordChangePage.test.tsx` and `client/src/components/ApplicationNavigation.test.tsx`

### Implementation for User Story 3

- [ ] T044 [US3] Complete session validation, replacement, fixed inactivity/absolute expiry, success-only activity refresh, logout, current-password verification, password change, cookie clearing, and session invalidation transactions in `backend/app/services/planner_auth.py`
- [ ] T045 [US3] Expose logout and self-service password change with safe session/error behavior in `backend/app/api/planner_auth.py` and `backend/app/schemas/planner_auth.py`
- [ ] T046 [US3] Apply post-success `X-Planner-Activity: user` refresh only while the presented digest is still current, clear invalid cookies, and emit no protected response after expiry in `backend/app/main.py`
- [ ] T047 [P] [US3] Complete shared planner request invalidation ordering and add logout/password-change adapters in `client/src/api/plannerFetch.ts` and `client/src/api/authentication.ts`
- [ ] T048 [US3] Add password-change/logout/current-identity navigation and ended-session transitions to the protected application in `client/src/pages/PasswordChangePage.tsx`, `client/src/components/ApplicationNavigation.tsx`, and `client/src/PlannerApplication.tsx`

**Checkpoint**: US3 independently proves one usable session, every specified
implemented invalidation path, authoritative expiry, and safe removal of stale
planner UI; literal browser-close limitations remain reserved for manual
acceptance.

---

## Phase 6: User Story 6 - Preserve Accountless Lecturer Capabilities (Priority: P1)

**Goal**: Keep every FS-015 lecturer review/calendar/feedback capability
anonymous and unchanged while ensuring lecturer credentials can never grant or
combine into planner authority.

**Independent Test**: Run valid, expired, revoked, replaced, malformed,
wrong-scope, feedback, and calendar lecturer scenarios without planner login,
then present each credential to every planner operation class and prove denial.

### Tests for User Story 6 (write before implementation)

- [ ] T049 [US6] Expand the authorization inventory with active/ended/replaced lecturer digests, lecturer bearer plus valid planner cookie, exact public lecturer exceptions, near-miss paths, mutation snapshots, and unchanged generic FS-015 outcomes in `backend/tests/api/test_planner_authorization.py`, `backend/tests/api/test_lecturer_bearer_authorization.py`, `backend/tests/api/test_lecturer_review.py`, and `backend/tests/api/test_lecturer_calendar_export.py`
- [ ] T050 [P] [US6] Add regression tests proving public lecturer review/calendar/feedback and terminology calls always use `credentials: "omit"`, never receive planner CSRF/activity headers, and remain isolated from auth-route loading in `client/src/api/lecturerReview.test.ts`, `client/src/config/terminology.test.ts`, and `client/src/main.test.tsx`
- [ ] T051 [P] [US6] Add backend route tests proving `/lecturer-review/` and public assets remain reachable without a planner session while planner/auth data never enters their HTML or cacheable responses in `backend/tests/test_frontend.py` and `backend/tests/test_main.py`

### Implementation for User Story 6

- [ ] T052 [US6] Preserve exact public lecturer operations outside cookie authentication, explicitly deny any stored lecturer bearer on planner APIs even beside a valid planner cookie, and keep public operations bearer-scoped in `backend/app/main.py` and `backend/app/api/lecturer_review.py`
- [ ] T053 [P] [US6] Keep public lecturer/terminology transport direct and credential-omitting while only planner-side lecturer management uses `plannerFetch` in `client/src/api/lecturerReview.ts` and `client/src/config/terminology.ts`

**Checkpoint**: All established lecturer capability acceptance tests remain
green without planner authentication, and every planner use of a lecturer
credential is denied.

---

## Phase 7: User Story 4 - Reset, Disable, and Reactivate Planner Access (Priority: P2)

**Goal**: Let the sole administrator reset another active planner, disable them
immediately, and reactivate a disabled account only through fresh one-time
access and a planner-chosen password.

**Independent Test**: Issue reset access, disable an active planner, and
reactivate through fresh access; after each action verify password/session/state,
replacement, lifecycle timestamps, confirmation, and no secret disclosure.

### Tests for User Story 4 (write before implementation)

- [ ] T054 [US4] Add failing service tests for reset issuance clearing password/session/retry state while remaining active, disablement clearing password/session/access and setting latest timestamp, reactivation issuance remaining inactive, redemption activation/timestamp, replacement/expiry/replay, self-admin rejection, revision conflicts, and transaction rollback in `backend/tests/services/test_planner_auth.py`
- [ ] T055 [P] [US4] Add failing file-backed races for reset versus login/request, disable versus request/redemption, reactivation reissue/redemption, and stale revision actions with at most one successful credential outcome in `backend/tests/services/test_planner_auth_concurrency.py`
- [ ] T056 [P] [US4] Add failing API tests for reset, disable, and reactivation-access endpoints; immediate session/password denial; safe state/timestamps; explicit expected revision; self-admin restrictions; no-store one-time results; and ordinary-planner 403 in `backend/tests/api/test_planner_auth.py` and `backend/tests/api/test_planner_authorization.py`
- [ ] T057 [P] [US4] Add failing UI tests for state-appropriate reset/disable/reactivate actions, explicit consequence confirmations, self-action absence, stale refresh, transient replacement links, dismissal, and affected-account identification in `client/src/pages/PlannerAccountsPage.test.tsx`, `client/src/components/AccountActionDialog.test.tsx`, and `client/src/components/OneTimeAccessResult.test.tsx`

### Implementation for User Story 4

- [ ] T058 [US4] Implement atomic reset, disablement, reactivation issuance/redemption, session/access deletion, revision checking, administrator self-protection, and latest lifecycle timestamps in `backend/app/services/planner_auth.py`
- [ ] T059 [US4] Expose reset, disable, and reactivation-access operations with strict request/response schemas and safe errors in `backend/app/api/planner_auth.py` and `backend/app/schemas/planner_auth.py`
- [ ] T060 [P] [US4] Implement the reusable focus-trapped/cancel-first account consequence confirmation in `client/src/components/AccountActionDialog.tsx`
- [ ] T061 [US4] Wire reset, disablement, reactivation, stale refresh, immediate state changes, and one-time result replacement/clearing into `client/src/api/authentication.ts` and `client/src/pages/PlannerAccountsPage.tsx`

**Checkpoint**: US4 independently proves immediate access removal and fresh
planner-controlled recovery without administrator password assignment.

---

## Phase 8: User Story 5 - Transfer or Recover the Sole Administrator (Priority: P2)

**Goal**: Atomically transfer administration to another active planner and let
the existing locked-out sole administrator recover through a distinct durable
startup credential without creating another account.

**Independent Test**: Transfer between two active planners under normal,
stale, and competing requests, then recover the current administrator and prove
exactly one administrator, unchanged identity, password/session invalidation,
credential consumption, and no operator account.

### Tests for User Story 5 (write before implementation)

- [ ] T062 [US5] Add failing service tests for eligible transfer, current/target revision checks, inactive/self targets, demote/promote atomicity, immediate former-admin authority loss, recovery registration/replacement/replay, no account selector, password policy, session/password invalidation, and identity preservation in `backend/tests/services/test_planner_auth.py`
- [ ] T063 [P] [US5] Add failing file-backed races for competing transfers, target disablement versus transfer, recovery replay, and recovery versus current session/login, proving exactly one administrator and no partial mutation in `backend/tests/services/test_planner_auth_concurrency.py`
- [ ] T064 [P] [US5] Add failing API tests for administrator-transfer and public administrator-recovery contracts, stale/ineligible failures, same-account recovery, safe generic wording, no automatic login, consumed startup access, and former-admin account API 403 with planner session retained in `backend/tests/api/test_planner_auth.py`
- [ ] T065 [P] [US5] Add failing recovery page/transport tests for credential plus new/confirmation password, no login/account selector, secret clearing, generic start-access failure, safe success, and normal-login requirement in `client/src/api/authentication.test.ts` and `client/src/pages/AdministratorRecoveryPage.test.tsx`
- [ ] T066 [P] [US5] Add failing transfer UI tests for only other active targets, explicit confirmation, revision payloads, stale handling, immediate sole-admin navigation change, and former-admin return to the ordinary planner shell in `client/src/pages/PlannerAccountsPage.test.tsx`, `client/src/components/AccountActionDialog.test.tsx`, and `client/src/PlannerApplication.test.tsx`

### Implementation for User Story 5

- [ ] T067 [US5] Implement claimed-row atomic administrator transfer and same-administrator startup recovery with password/session invalidation, startup consumption, revision checks, and exactly-one postconditions in `backend/app/services/planner_auth.py`
- [ ] T068 [US5] Expose administrator transfer and public recovery without identity selection/disclosure in `backend/app/api/planner_auth.py` and `backend/app/schemas/planner_auth.py`
- [ ] T069 [P] [US5] Implement recovery transport/page with memory-only secrets, canonical German outcomes, cleared controls, and normal-login routing in `client/src/api/authentication.ts` and `client/src/pages/AdministratorRecoveryPage.tsx`
- [ ] T070 [US5] Implement transfer confirmation, eligible target selection, revision handling, immediate current-account refresh, and account-view removal after lost authority in `client/src/pages/PlannerAccountsPage.tsx`, `client/src/PlannerApplication.tsx`, and `client/src/App.tsx`

**Checkpoint**: US5 independently proves maintainable exactly-one
administration and operator-assisted recovery without a second identity or
external service.

---

## Phase 9: User Story 7 - Administer Accounts Accessibly and Privately (Priority: P3)

**Goal**: Finish the responsive administrator account experience and all
authentication states with the exact minimal lifecycle projection, formal
German wording, keyboard/focus/status behavior, and zero secret exposure.

**Independent Test**: Navigate every authentication and account-management
state keyboard-only at narrow widths and 200% zoom, inspect labels, focus,
announcements, fields/actions, and prove listings/diagnostics/addresses/storage
contain no raw password or usable credential/session secret.

### Tests for User Story 7 (write before implementation)

- [ ] T071 [US7] Add backend secret-canary and projection tests covering listings, auth/account errors, redirects, logs, cache headers, lifecycle fields only, and absence of passwords, hashes, digests, retry/session/access/startup history in `backend/tests/api/test_planner_auth.py`, `backend/tests/api/test_planner_authorization.py`, and `backend/tests/services/test_planner_auth.py`
- [ ] T072 [P] [US7] Add account-card tests for semantic list/definition structure, exact identity/access/state/timestamps, state text independent of color, action availability, hidden revision metadata, current administrator restrictions, and ordinary-planner absence in `client/src/pages/PlannerAccountsPage.test.tsx`
- [ ] T073 [P] [US7] Add authentication-page accessibility/privacy tests for programmatic German labels, formal `Sie`, autocomplete intent, aria error links, visible result focus, live-region wording, cleared password/credential controls, no Forgot-password flow, and no secrets in DOM/history/storage/announcements in `client/src/pages/LoginPage.test.tsx`, `client/src/pages/BootstrapPage.test.tsx`, `client/src/pages/AccountAccessPage.test.tsx`, `client/src/pages/AdministratorRecoveryPage.test.tsx`, and `client/src/pages/PasswordChangePage.test.tsx`
- [ ] T074 [P] [US7] Add dialog/result tests for Cancel initial focus, focus trap, Escape, predictable restoration, affected-account/consequence text, keyboard copy fallback, and secret-free live announcements in `client/src/components/AccountActionDialog.test.tsx` and `client/src/components/OneTimeAccessResult.test.tsx`
- [ ] T075 [P] [US7] Add a canonical authentication/account German-copy regression inventory in `client/src/pages/plannerGermanCopy.test.ts`

### Implementation for User Story 7

- [ ] T076 [US7] Normalize safe validation/error/no-store handling and minimal account serialization across authentication/account operations without adding audit fields in `backend/app/api/planner_auth.py`, `backend/app/schemas/planner_auth.py`, and `backend/app/main.py`
- [ ] T077 [US7] Finish the semantic responsive account cards, exact lifecycle projection, state/action text, confirmation/result status focus, and private transient values in `client/src/pages/PlannerAccountsPage.tsx`, `client/src/components/AccountActionDialog.tsx`, and `client/src/components/OneTimeAccessResult.tsx`
- [ ] T078 [P] [US7] Finish labels, field-linked validation, focus/status movement, autocomplete, secret clearing, and canonical formal German copy across `client/src/pages/LoginPage.tsx`, `client/src/pages/BootstrapPage.tsx`, `client/src/pages/AccountAccessPage.tsx`, `client/src/pages/AdministratorRecoveryPage.tsx`, and `client/src/pages/PasswordChangePage.tsx`
- [ ] T079 [P] [US7] Add authentication/account card, wrapping action, 360/820-pixel breakpoint, 200%-zoom, min-target, non-color state, dialog, and visible-focus styling in `client/src/App.css`
- [ ] T080 [US7] Reconcile current identity, `Passwort ändern`, `Abmelden`, and administrator-only `Planer-Konten` navigation with predictable mobile overlay focus/inert behavior in `client/src/components/ApplicationNavigation.tsx` and `client/src/App.tsx`

**Checkpoint**: US7 independently proves that routine account administration
is understandable, accessible, responsive, and limited to the approved private
lifecycle summary.

---

## Phase 10: Polish and Cross-Cutting Verification

**Purpose**: Prove the full slice across security, deployment, performance,
accessibility, regression, and documentation boundaries.

- [ ] T081 [P] Document operator credential generation/rotation/replay behavior, bootstrap and emergency recovery runbooks, HTTPS prerequisite, cookie/CORS behavior, backup implications, and no-external-provider boundary in `backend/README.md` and `infrastructure/docker/README.md`
- [ ] T082 [P] Benchmark Argon2 verification and realistic concurrent attempts inside each supported production image architecture, record timing/peak-memory evidence and any justified process-local cap decision in `specs/016-authenticated-planner-access/quickstart.md`, and do not add a limiter without measured need
- [ ] T083 [P] Run focused migration, planner-auth service/concurrency/API/authorization, FS-015 lecturer, and the full backend pytest suites from `specs/016-authenticated-planner-access/quickstart.md` and record exact results or residual failures in `specs/016-authenticated-planner-access/quickstart.md`
- [ ] T084 [P] Run focused auth/request/component tests plus full Vitest, ESLint, TypeScript/Vite build from `specs/016-authenticated-planner-access/quickstart.md` and record exact results or residual failures in `specs/016-authenticated-planner-access/quickstart.md`
- [ ] T085 Execute keyboard-only, screen-reader-status, 360/820-pixel, 200%-zoom, non-color, dialog focus, password clearing, supported-browser close/reopen acceptance with session restoration disabled, timed five-minute bootstrap/recovery and three-minute setup/sign-in journeys, and the representative-participant 90% first-attempt completion protocol; record evidence and the restoration limitation in `specs/016-authenticated-planner-access/quickstart.md`
- [ ] T086 Execute production deployment checks for secure `__Host-planner_session`, remote plain-HTTP failure, HTTPS success, disabled production credentialed CORS, no-store responses, secret-free startup logs, startup credential restart/replay, and SQLite backup/restore in `specs/016-authenticated-planner-access/quickstart.md`
- [ ] T087 Perform a final scope/contract/constitution audit across `specs/016-authenticated-planner-access/spec.md`, `specs/016-authenticated-planner-access/plan.md`, `specs/016-authenticated-planner-access/data-model.md`, `specs/016-authenticated-planner-access/contracts/planner-access.openapi.yaml`, `specs/016-authenticated-planner-access/contracts/authorization-boundary.md`, and `specs/016-authenticated-planner-access/contracts/planner-access-ui.md`; reopen affected spec/design/test tasks before changing any discrepant behavior

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 - Setup**: Starts immediately.
- **Phase 2 - Foundation**: Depends on Phase 1 and blocks every story.
- **Phase 3 - US1**: Depends on Foundation and supplies bootstrap, login,
  default denial, and authenticated planner transport.
- **Phase 4 - US2**: Depends on US1 because account administration requires the
  sole signed-in administrator.
- **Phase 5 - US3**: Depends on US1's session issuance; may proceed beside US2
  after shared `planner_auth` file edits are sequenced.
- **Phase 6 - US6**: Depends on US1's final middleware/request boundary but is
  behaviorally independent of US2 and US3.
- **Phase 7 - US4**: Depends on US2 account creation/access and US3 session
  invalidation.
- **Phase 8 - US5**: Depends on US2 active target accounts and US3 invalidation;
  transfer is independent of US4, while recovery shares startup state.
- **Phase 9 - US7**: Depends on all user-facing account/authentication actions
  selected for delivery.
- **Phase 10 - Polish**: Depends on every selected story.

### User story dependency graph

```text
Setup -> Foundation -> US1 -> US2 -> US4 -> US7
                         |      \-> US5 -/
                         \-> US3 -> US4/US5
                         \-> US6
All selected stories ----------------> Polish
```

### Within each story

- Write/update the listed tests first and confirm the intended failure where
  practical.
- Add/extend strict schemas before service/API code that returns them.
- Implement service transactions and database invariants before route/UI
  exposure.
- Keep server authorization authoritative; frontend visibility never completes
  an authorization task.
- Complete the story's independent test and checkpoint before advancing.

### Parallel opportunities

- Setup dependency work T002 and environment passthrough T003 target different
  files and can proceed together after T001.
- Foundation test helpers T005 and planner fetch tests T006 can proceed while
  migration tests T004 are written.
- US1 service, API, authorization, frontend transport, page, route, and existing
  transport tests T010-T017 target separate files and can be written in
  parallel; client migrations T024-T026 target disjoint modules.
- US2 concurrency/API/transport/page tests T029-T033 can run beside the service
  test extension T028; frontend transport T037 can proceed beside fragment/page
  implementation T038 after contracts pass.
- US3 API, gate/fetch, and password/navigation tests T041-T043 can run in
  parallel; frontend request work T047 can proceed beside backend service work
  T044 after their tests fail.
- US6 backend boundary, client omission, and frontend-route tests T049-T051 can
  run in parallel.
- US4 concurrency/API/UI tests T055-T057 can run in parallel; dialog T060 is
  independent of backend service/API T058-T059.
- US5 concurrency/API/recovery/transfer tests T063-T066 can run in parallel;
  recovery UI T069 can proceed beside backend transfer/recovery T067-T068 after
  contracts are fixed.
- US7 backend privacy, page, auth-surface, dialog/result, and copy tests
  T071-T075 can run in parallel; CSS T079 can proceed beside auth-page behavior
  T078 after test expectations are established.
- Documentation, Argon2 evidence, backend verification, and frontend
  verification T081-T084 can proceed in parallel after story completion.

---

## Parallel Examples

### User Story 1

```text
Task T010: Password/startup/bootstrap service tests
Task T012: Bootstrap/login/session API tests
Task T013: Default-deny authorization inventory
Task T014: Frontend authentication transport tests
Task T015: Authentication gate/login/bootstrap UI tests
Task T016: Exact route-dispatch tests
```

### User Story 2

```text
Task T029: Setup redemption race tests
Task T030: Account/setup API contract tests
Task T031: Frontend account transport tests
Task T032: Fragment/account-access page tests
Task T033: Planner account creation/result tests
```

### User Story 3

```text
Task T041: Session API/invalidation tests
Task T042: Fetch/gate invalidation tests
Task T043: Password-change/navigation tests
```

### User Story 6

```text
Task T049: Backend lecturer/planner boundary matrix
Task T050: Client credential-omission regressions
Task T051: Public lecturer route regressions
```

### User Story 4

```text
Task T055: Reset/disable/reactivation race tests
Task T056: Account-action API tests
Task T057: Account action/dialog/result UI tests
```

### User Story 5

```text
Task T063: Transfer/recovery race tests
Task T064: Transfer/recovery API tests
Task T065: Recovery transport/page tests
Task T066: Transfer UI and authority-loss tests
```

### User Story 7

```text
Task T071: Backend projection/secret canaries
Task T072: Semantic account-card tests
Task T073: Authentication accessibility/privacy tests
Task T074: Dialog/result focus/privacy tests
Task T075: Canonical German copy inventory
```

---

## Implementation Strategy

### MVP first: User Story 1

1. Complete Setup and Foundation.
2. Complete US1 bootstrap, login, default denial, and planner transport.
3. Stop and run the US1 independent test plus focused authorization and existing
   planner regression suites.
4. Demonstrate one named administrator using existing planner workflows while
   all anonymous planner access is denied.

US1 is the smallest safe demonstrable increment. It protects the application
and supports one administrator but intentionally does not yet claim multi-planner
account administration or full FS-016 completion.

### Incremental delivery

1. **US1**: Protect planner work and establish/sign in the first administrator.
2. **US2**: Create and set up ordinary named planners.
3. **US3**: Complete one-current-session lifecycle and self password change.
4. **US6**: Certify unchanged accountless lecturer behavior at the new boundary.
5. **US4**: Add reset, disablement, and reactivation.
6. **US5**: Add atomic administrator transfer and operator recovery.
7. **US7**: Finish the minimal, accessible, responsive administration surface.
8. **Polish**: Run full automated/manual/deployment acceptance.

### Parallel team strategy

After Foundation and US1 establish the shared contract:

- Session lifecycle (US3) and lecturer regression (US6) can proceed beside
  planner setup/account creation (US2).
- After US2/US3, account lifecycle (US4) and administrator transfer/recovery
  (US5) can proceed in parallel if shared service/API file edits are sequenced.
- US7 test design can begin against stable contracts while the final P2 actions
  are integrated, but its implementation completes after those actions.

---

## Notes

- Do not add authenticated lecturer accounts, SSO/OIDC, email, MFA/passkeys,
  general roles, multiple administrators, JWT, an external session/cache store,
  detailed auth audit history, account deletion/editing, device/session UI,
  React Router, global state/query libraries, or planner-work attribution.
- Do not implement unload/beacon logout as a security control. Manual acceptance
  uses normal session-cookie semantics with restoration disabled and records the
  browser restoration limitation; server inactivity/absolute expiry remain the
  backstops.
- Do not place usable setup/reset/reactivation secrets in server-visible paths or
  query strings. Fragment values are scrubbed before network/module work and
  retained only in immediate React memory.
- Do not add a production authentication bypass to preserve existing tests.
  Adapt planner tests through test-only authenticated fixtures and keep lecturer
  public tests anonymous.
- Commit after each task or coherent task group only after relevant tests pass.
