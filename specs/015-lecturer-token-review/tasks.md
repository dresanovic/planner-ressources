# Tasks: FS-015 Accountless Lecturer Token Review

**Input**: Design documents from
`specs/015-lecturer-token-review/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`

**Tests**: Tests are required by the specification and constitution. Write the
listed test tasks first and confirm they fail for the intended missing behavior
before implementing production changes wherever practical.

**Organization**: Tasks are grouped by user story so each behavior can be
implemented and verified as a bounded increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on another incomplete task in the same phase.
- **[Story]**: Maps the task to one specification user story.
- Every task names the exact file or files it changes.

## Phase 1: Setup (Shared Test Support)

**Purpose**: Establish reusable, slice-specific fixtures without adding a new
framework or runtime dependency.

- [X] T001 Create backend FS-015 fixtures for three lecturers, two revisions, multi-course teaching/exam assignments, multiple eligible lecturers, assignment changes, and deterministic UTC time in `backend/tests/lecturer_review_fixtures.py`
- [X] T002 [P] Create minimum-scope planner/public DTO and feedback fixtures with secret canaries in `client/src/test/lecturerReviewFixtures.ts`

---

## Phase 2: Foundational (Blocking Data and Contract Types)

**Purpose**: Add the durable records and shared schemas required by every user
story.

**CRITICAL**: Complete this phase before implementing a user story.

- [X] T003 [P] Add failing clean-create, `0008`-to-`0009` upgrade, idempotent startup, partial-schema rejection, foreign-key, check-constraint, digest uniqueness, active-pair uniqueness, feedback-idempotency, short-lived invalid-source state, cleanup-index, and restart-continuity migration tests in `backend/tests/db/test_migrations.py`
- [X] T004 Add `LecturerReviewLink`, `LecturerReviewFeedback`, `LecturerReviewActivityEvent`, and short-lived `LecturerReviewInvalidSourceState` with the constraints and indexes from `data-model.md` in `backend/app/models/planning.py`
- [X] T005 Implement migration `0009` for the four FS-015 tables, replacement relation, throttle field, short-lived invalid-source state, and required indexes/checks in `backend/app/db/migrations/0009_lecturer_token_review.py`
- [X] T006 Update clean/current/predecessor/partial schema recognition and sequential upgrade handling for FS-015 in `backend/app/db/schema.py`
- [X] T007 [P] Define the shared planner and public request/response types, bounded enums, comment validation, and generic public error envelopes from the OpenAPI contract in `backend/app/schemas/lecturer_review.py`

**Checkpoint**: The database can be created or upgraded safely and the
cross-stack types exist, but no review behavior is exposed yet.

---

## Phase 3: User Story 1 - Share One Lecturer's Revision Safely (Priority: P1) Internal Checkpoint

**Goal**: A planner can issue and copy a one-, two-, or three-day link for one
lecturer and Working revision; the accountless reviewer sees every and only
that lecturer's current teaching/exam assignments across courses.

**Independent Test**: Seed one Working revision with at least two lecturers and
multiple courses, issue a default-duration link for one lecturer, open it
without an account, and verify exact 72-hour expiry plus a complete
single-lecturer projection with no planner-only or cross-revision data.

### Tests for User Story 1 (write before implementation)

- [X] T008 [P] [US1] Add failing service tests for 256-bit opaque secret generation, digest-only persistence, one-time reveal, duration boundaries, eligible issuance states, one-active-pair enforcement, issuing one pair without changing another pair, dynamic assignment projection, empty/restored assignments, and minimum disclosure in `backend/tests/services/test_lecturer_review.py`
- [X] T009 [P] [US1] Add failing planner issue/overview and exact-two-operation public API contract tests, including one-time raw-secret response, authorization-header transport, all-success/error security headers, generic unavailable equivalence, `request.client.host` source selection, forged forwarding-header non-effect, trusted/untrusted proxy-peer behavior, independent source buckets, missing/short source-fingerprint key configuration failure against the 256-bit minimum, active-block and rolling-attempt continuity across application restart, and raw-secret canaries in `backend/tests/api/test_lecturer_review.py`
- [X] T010 [P] [US1] Add failing file-backed SQLite tests for simultaneous initial issuance and concurrent assignment change versus protected view in `backend/tests/services/test_lecturer_review_concurrency.py`
- [X] T011 [P] [US1] Add failing client transport tests for fixed relative same-origin public paths, `credentials: "omit"`, bearer headers, issue payload/default duration, one-time raw-secret response handling, client URL construction, runtime DTO rejection, and absence of secrets from routine errors in `client/src/api/lecturerReview.test.ts`
- [X] T012 [P] [US1] Add failing bootstrap/public-page tests for exact `/lecturer-review/#/{secret}` parsing, fragment removal while preserving the public path, dynamic public-page import before planner code, isolated rendering without planner navigation, multi-course teaching/exam scope, explicit empty schedule, identity disclaimer, expiry/state display, safe failure, and no browser storage in `client/src/main.test.tsx` and `client/src/pages/LecturerReviewPage.test.tsx`
- [X] T013 [P] [US1] Add failing planner tests for Draft/Ready issuance, Ready recommendation, lecturer eligibility, 1/2/3-day selection with default 3, transient one-time URL, copy success/failure, warnings, and secret clearing in `client/src/components/LecturerReviewManagement.test.tsx`

### Implementation for User Story 1

- [X] T014 [US1] Implement injected UTC clock support, exact token-shape parsing, `secrets.token_urlsafe(32)` generation, digest lookup, generic unavailable mapping, privacy-safe activity events, atomic database-backed invalid-source limiting keyed by a configured stable HMAC secret and normalized `request.client.host`, and one-minute physical source-state cleanup without parsing forwarding headers in `backend/app/services/lecturer_review.py`
- [X] T015 [US1] Implement atomic initial issuance with cross-pair isolation plus Working/current-Published lecturer projection using FS-013 content semantics, stable `COURSE-{sourceCourseId}` codes, current assignment revalidation, complete-empty behavior, and minimum public DTO construction in `backend/app/services/lecturer_review.py`
- [X] T016 [US1] Expose gateway-protected planner overview/issue operations and only `GET /api/public/lecturer-review` for public protected views, with structured errors and the complete public response-header policy in `backend/app/api/lecturer_review.py`
- [X] T017 [US1] Register the lecturer-review router, require a stable source-fingerprint secret containing at least 256 bits of random key material at production startup, and register the one-minute persisted invalid-source cleanup lifecycle without adding application-level planner authentication, broadening CORS, parsing forwarding headers, or logging bearer headers in `backend/app/main.py`
- [X] T018 [P] [US1] Implement issue, planner-overview, and public-view transport functions with runtime response validation, fixed relative public paths, `credentials: "omit"`, and in-memory bearer handling in `client/src/api/lecturerReview.ts`
- [X] T019 [US1] Implement exact-path bootstrap that dynamically imports `LecturerReviewPage` for `/lecturer-review/` or the planner `App` otherwise, removes only the secret fragment, and renders complete scoped schedule/empty/safe states with refresh and plain-text display in `client/src/main.tsx` and `client/src/pages/LecturerReviewPage.tsx`
- [X] T020 [US1] Implement planner lecturer selection, duration choice, issue action, construction of `{window.location.origin}/lecturer-review/#/{secret}` from the one-time raw secret, URL details, clipboard result, manual-delivery warning, and secret dismissal in `client/src/components/LecturerReviewManagement.tsx`
- [X] T021 [US1] Add the `reviews` Schedule destination and render the initial management workspace for the selected semester/revision in `client/src/components/ApplicationNavigation.tsx`, `client/src/App.tsx`, and `client/src/components/CourseSchedulePage.tsx`
- [X] T022 [US1] Add public/planner responsive styles and the defense-in-depth no-referrer document policy in `client/src/App.css` and `client/index.html`

**Checkpoint**: User Story 1 is an internal technical checkpoint, not a
releasable feature. It proves minimum-scope reading, but production release
still requires US2 feedback, US3 revoke/replace and terminal access control, US4
planner feedback handling, and all cross-cutting verification.

---

## Phase 4: User Story 2 - Submit Advisory Schedule Feedback (Priority: P2)

**Goal**: A valid reviewer can append revision comments, session comments, and
not-possible flags while every item remains immutable, correctly associated,
plain text, idempotent for retries, and advisory.

**Independent Test**: Seed a valid link directly, submit all three feedback
kinds, repeat one transport request, deliberately add a second flag, and verify
the correct link/revision/lecturer/session attribution, current submission-time
context, immutability, and no schedule mutation.

### Tests for User Story 2 (write before implementation)

- [X] T023 [P] [US2] Add failing service/API tests for every feedback kind, 1/2,000/2,001-character boundaries, optional flag comments, inert active-content strings, current-state session capture, out-of-scope rejection, immutable repeated flags, idempotent retry/fingerprint conflict, same-link history, and exact 10/11-minute plus 60/61-hour limits in `backend/tests/services/test_lecturer_review.py` and `backend/tests/api/test_lecturer_review.py`
- [X] T024 [P] [US2] Add failing file-backed SQLite tests for duplicate submission races, revoke/reassignment versus feedback, and concurrent feedback threshold crossing in `backend/tests/services/test_lecturer_review_concurrency.py`
- [X] T025 [P] [US2] Add failing client API tests for feedback payloads, stable retry UUIDs, created versus already-accepted results, validation, refresh-required, and throttle responses in `client/src/api/lecturerReview.test.ts`
- [X] T026 [P] [US2] Add failing public-page tests for revision comments, per-session comments, not-possible flags, optional recommendations, pending/accepted/rejected announcements, draft preservation on ambiguous retry, separate deliberate flags, same-link history, and literal markup rendering in `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 2

- [X] T027 [US2] Implement authoritative feedback revalidation, canonical request fingerprints, retry idempotency, immutable insertion, submission-time session context, same-link history, and feedback misuse counting in `backend/app/services/lecturer_review.py`
- [X] T028 [US2] Expose only `POST /api/public/lecturer-review/feedback` with created/idempotent/validation/refresh/throttle outcomes and the complete no-store/no-cache/no-referrer/noindex response policy in `backend/app/api/lecturer_review.py`
- [X] T029 [US2] Implement public feedback transport and logical submission UUID reuse in `client/src/api/lecturerReview.ts`
- [X] T030 [US2] Add revision and per-session feedback forms, 2,000-character counters, advisory/not-authenticated wording, pending controls, precise announcements, history refresh, and inert feedback display in `client/src/pages/LecturerReviewPage.tsx`

**Checkpoint**: User Stories 1 and 2 work together, while User Story 2 remains
testable from a directly seeded valid link.

---

## Phase 5: User Story 3 - End or Replace Access Immediately (Priority: P3)

**Goal**: Expiry, revoke, replacement, abandonment, and supersession end access
without disclosure; first publication keeps access; concurrent operations leave
one authoritative outcome.

**Independent Test**: Seed active links and exercise each end condition,
publication, simultaneous replacements, and revoke versus feedback; verify only
the current valid link can read or submit and every unusable credential returns
the identical safe result.

### Tests for User Story 3 (write before implementation)

- [X] T031 [P] [US3] Add failing service/API tests for immediately-before/at/after expiry, revoke, replace-all-earlier behavior, replacement duration default, first publication, permanent abandonment/supersession ending, restore non-reactivation, and generic failure equivalence in `backend/tests/services/test_lecturer_review.py` and `backend/tests/api/test_lecturer_review.py`
- [X] T032 [P] [US3] Add failing file-backed SQLite tests for simultaneous replacement, replacement versus expiry, revoke versus feedback, abandonment versus feedback, and supersession versus feedback in `backend/tests/services/test_lecturer_review_concurrency.py`
- [X] T033 [P] [US3] Add failing FS-013 lifecycle regression tests proving atomic link termination on abandon/supersede, no termination on first publication, and no reactivation on restore in `backend/tests/services/test_schedule_lifecycle.py`, `backend/tests/services/test_schedule_lifecycle_concurrency.py`, and `backend/tests/api/test_schedule_lifecycle.py`
- [X] T034 [P] [US3] Add failing planner/public client tests for revoke, replacement, lost replacement response recovery, ended statuses, protected-data clearing after later invalidation, and identical unusable-link UI in `client/src/components/LecturerReviewManagement.test.tsx` and `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 3

- [X] T035 [US3] Implement exact effective expiry, idempotent expiry evidence, atomic revoke, atomic replace-all-earlier links, replacement eligibility for Working/current Published, and permanent revision-ended states in `backend/app/services/lecturer_review.py`
- [X] T036 [US3] Terminalize active review links inside the authoritative FS-013 abandon and publication-supersession transactions without changing first-publication or restore behavior in `backend/app/services/schedule_lifecycle.py`
- [X] T037 [US3] Expose gateway-protected planner revoke and replacement endpoints with one-time raw replacement secret and authoritative conflict results in `backend/app/api/lecturer_review.py`
- [X] T038 [US3] Add revoke/replace transport functions and planner controls, including new duration selection, client construction of the replacement URL, non-secret history statuses, lost-secret guidance, and refreshed authoritative overview in `client/src/api/lecturerReview.ts` and `client/src/components/LecturerReviewManagement.tsx`
- [X] T039 [US3] Clear protected public data on later expiry/revoke/replace/revision end and render only the generic unavailable or bounded valid-link throttle state in `client/src/pages/LecturerReviewPage.tsx`

**Checkpoint**: User Stories 1–3 provide the complete secure link lifecycle and
accountless feedback path.

---

## Phase 6: User Story 4 - Consider Feedback Without Losing Planner Control (Priority: P4)

**Goal**: The planner can inspect retained feedback, recognize exact impossible
flag counts in a prominent top filter, open affected current sessions, and
publish under unchanged FS-013 rules.

**Independent Test**: Seed no feedback, comments, repeated flags on one session,
flags on another session, removed/reassigned sessions, and
partial/unavailable feedback; verify exact counts, distinct filtered groups,
guarded session navigation, retained context, and unchanged publication.

### Tests for User Story 4 (write before implementation)

- [X] T040 [P] [US4] Add failing planner overview API tests for revision/session grouping, intended-link attribution, retained submission context, exact flag-item count, distinct affected-session groups, complete zero, partial/unavailable null counts, current occurrence references, and ended-link feedback retention in `backend/tests/api/test_lecturer_review.py`
- [X] T041 [P] [US4] Add failing service regressions proving no-feedback, passed-expiry, comments, flags, publication, abandonment, supersession, revoke, and replacement do not mutate feedback or gate any applicable FS-013 publication action in `backend/tests/services/test_lecturer_review.py` and `backend/tests/services/test_schedule_lifecycle.py`
- [X] T042 [P] [US4] Add failing component tests for the top keyboard-operable Not possible filter, exact flag-item count, distinct session groups, complete zero, partial/unavailable states, clear behavior, non-color labels, historical context, and current-session action in `client/src/components/LecturerReviewManagement.test.tsx`
- [X] T043 [P] [US4] Add failing navigation tests for the reviews destination, selected revision preservation, dirty-session guard, and authoritative switch to the existing Calendar occurrence workflow in `client/src/components/ApplicationNavigation.test.tsx`, `client/src/App.test.tsx`, and `client/src/components/CourseSchedulePage.test.tsx`

### Implementation for User Story 4

- [X] T044 [US4] Implement the planner feedback read model with completeness metadata, exact item counts, distinct session grouping, retained context, and optional authoritative occurrence navigation in `backend/app/services/lecturer_review.py` and `backend/app/api/lecturer_review.py`
- [X] T045 [US4] Extend planner overview runtime validation for feedback completeness, grouped items, counts, attribution, and navigation targets in `client/src/api/lecturerReview.ts`
- [X] T046 [US4] Implement the top Not possible filter, complete/partial/unavailable states, grouped retained feedback, non-color kind labels, and non-mutating clear behavior in `client/src/components/LecturerReviewManagement.tsx`
- [X] T047 [US4] Wire the reviews destination's authoritative revision/occurrence action through the existing unsaved-change guard into Calendar without adding a second session workflow in `client/src/components/CourseSchedulePage.tsx` and `client/src/App.tsx`
- [X] T048 [US4] Add feedback-filter focus handling, live announcements, single-column 320-pixel layout, 200% zoom wrapping, and visible keyboard focus styles in `client/src/components/LecturerReviewManagement.tsx` and `client/src/App.css`

**Checkpoint**: All four stories are independently verifiable and the planner
retains complete publication control.

---

## Phase 7: Polish and Cross-Cutting Verification

**Purpose**: Prove security, performance, accessibility, migration safety, and
slice-wide regression behavior after all selected stories are complete.

- [X] T049 [P] Add repeatable reference-scale backend performance guards for 100 scoped sessions and 200 retained feedback items, and document an end-to-end acceptance run of exactly 20 valid review openings and 20 feedback submissions after three unrecorded warm-up operations; measure each opening from navigation until either the complete usable schedule or a safe actionable state is visible, count only complete usable schedules toward the requirement that at least 19 of 20 openings complete within 3 seconds, require all 20 openings to reach either permitted state within 10 seconds, require at least 19 of 20 submissions to show an accepted or rejected result within 2 seconds and all 20 within 5 seconds without duplicates, and record the environment and individual measurements in `backend/tests/performance/test_lecturer_review_performance.py` and `specs/015-lecturer-token-review/quickstart.md`
- [X] T050 [P] Add a complete public failure-equivalence, activity-evidence, and privacy-canary matrix covering every FR-058 event type, excluded token/comment/network fields, no source-state deletion during an active block, physical row removal by 15 minutes with a fake clock, exact 20/21 source and 120/121 view boundaries, stable-key restart continuity during rolling attempts and an active block, atomic concurrent same-source requests, spoofed forwarding-header non-effect, and independent normalized-source buckets in `backend/tests/api/test_lecturer_review.py`
- [X] T051 [P] Add client security/accessibility regressions for secret absence from paths/storage/errors after bootstrap, public-path preservation, dynamic planner-code exclusion, fixed same-origin APIs, omitted credentials, external-navigation prevention, no executable comment DOM, keyboard operation, focus, and assistive status semantics in `client/src/main.test.tsx`, `client/src/pages/LecturerReviewPage.test.tsx`, and `client/src/components/LecturerReviewManagement.test.tsx`
- [X] T052 Add negative contract and UI tests confirming FS-015 introduces no additional public endpoints, multi-lecturer links, automated delivery, lecturer accounts, schedule editing, feedback editing/deletion, attachments, threads, approval gates, publication blocking, or authenticated FS-016 behavior in `backend/tests/api/test_lecturer_review.py`, `client/src/pages/LecturerReviewPage.test.tsx`, and `client/src/components/LecturerReviewManagement.test.tsx`
- [ ] T053 After the deployment owner identifies the target environment, gateway configuration/runbook, trusted peer/CIDR, and evidence recorder, execute and record every deployed trusted-gateway release check: authorized planner access, exact anonymous page/API allowlist, anonymous planner/health/docs rejection, wrong-method/subpath rejection, direct-backend denial, forwarding-header overwrite, single-source non-evasion, two-source independence, application-restart block continuity, HTTPS, same-origin API calls, and omitted credentials in `specs/015-lecturer-token-review/contracts/gateway-boundary.md` and `specs/015-lecturer-token-review/quickstart.md`
- [ ] T054 Measure and record that every valid planner issuance path completes in no more than 60 seconds and five deliberate interactions from selected lecturer/revision in `specs/015-lecturer-token-review/quickstart.md`
- [ ] T055 Execute and record keyboard-only, supported screen-reader, 320-CSS-pixel, and 200%-zoom manual acceptance in `specs/015-lecturer-token-review/quickstart.md`
- [ ] T056 Conduct the 10-participant moderated SC-006/SC-007 review and record results in `specs/015-lecturer-token-review/quickstart.md`; if participants are unavailable, leave this task unchecked and do not mark FS-015 accepted
- [ ] T057 Run the focused FS-015, FS-013 regression, migration, concurrency, performance, proxy-boundary, and full pytest commands from `specs/015-lecturer-token-review/quickstart.md`
- [ ] T058 After T001–T052 are complete, run focused and full Vitest, ESLint, and Vite build commands, then update the FS-015 implementation status only after T053–T057 and all required delivery evidence pass in `specs/015-lecturer-token-review/quickstart.md` and `docs/planning/Feature_slices.md`

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 — Setup**: No dependencies.
- **Phase 2 — Foundational**: Depends on Phase 1 and blocks production work in
  every user story.
- **Phase 3 — US1**: Depends on Phase 2 and is an internal secure-read
  checkpoint, not a releasable feature.
- **Phase 4 — US2**: Uses the valid-link boundary delivered by US1 in
  production, but its service/API behavior can be tested from directly seeded
  foundational records.
- **Phase 5 — US3**: Uses issued links from US1; it can proceed in parallel
  with US2 after US1. US2 and US3 complete the second internal checkpoint but
  are not production-releasable without US4.
- **Phase 6 — US4**: Uses retained feedback from US2 and existing session
  navigation; start after US2. It does not depend on US3 to test its core
  filter, but ended-link retention cases do.
- **Phase 7 — Polish**: Depends on all stories selected for delivery.

### User story completion order

```text
Setup -> Foundation -> US1 (secure read checkpoint)
                         |-> US2 (feedback) ----|
                         |-> US3 (link ending) -|-> US4 (planner action)
                                                -> Cross-cutting verification
```

### Within each user story

1. Write the story's failing tests and confirm the intended failure.
2. Implement the smallest backend domain behavior.
3. Expose only the contract endpoints required by that story.
4. Implement client transport and UI against the recorded contract.
5. Run the independent story test before moving to the next story.

Database and concurrency authority always precede returning a secret or
accepted feedback. Public projection is complete-or-fail-closed. Planner
feedback completeness is explicit and never inferred from an empty array.

## Parallel Opportunities

- T001 and T002 can run in parallel.
- T003 and T007 can run in parallel; T004–T006 then complete the migration path
  in order.
- US1 test tasks T008–T013 can run in parallel before implementation.
- After US1 backend contracts stabilize, T018 can run alongside T014–T017;
  T019/T020 then consume the client API.
- US2 test tasks T023–T026 can run in parallel.
- US3 test tasks T031–T034 can run in parallel, and US3 as a whole can run
  alongside US2 after US1 if separate developers avoid shared files.
- US4 test tasks T040–T043 can run in parallel.
- Cross-cutting test tasks T049–T051 can run in parallel.

## Parallel Example: User Story 1

```text
Task T008: Backend token, issuance, scope, and projection service tests
Task T009: Backend planner/public API and security-header tests
Task T010: Backend issuance/scope concurrency tests
Task T011: Client API contract tests
Task T012: Public page isolation and scope tests
Task T013: Planner issue/copy management tests
```

## Parallel Example: User Story 2

```text
Task T023: Backend feedback and rate-boundary tests
Task T024: Backend feedback concurrency tests
Task T025: Client feedback API tests
Task T026: Public feedback-form tests
```

## Parallel Example: User Story 3

```text
Task T031: Backend link-ending service/API tests
Task T032: Backend link-ending concurrency tests
Task T033: FS-013 lifecycle regression tests
Task T034: Planner/public ended-link UI tests
```

## Parallel Example: User Story 4

```text
Task T040: Planner feedback overview API tests
Task T041: Publication non-gating and retention tests
Task T042: Planner feedback-filter component tests
Task T043: Existing Calendar navigation bridge tests
```

## Implementation Strategy

### Technical checkpoints and complete slice release

1. Complete Setup and Foundational phases.
2. Complete User Story 1 only.
3. Run T008–T013 and verify the independent minimum-scope link flow.
4. Stop for an internal technical review; do not release this checkpoint.
5. Complete US2 and US3, then validate feedback plus immediate access ending as
   a second internal checkpoint.
6. Complete US4 and cross-cutting verification before any production release.

US1 proves the highest-risk read boundary, but it is not independently
releasable. US1–US3 form a security-complete internal checkpoint, but are not a
complete FS-015 release because the planner feedback view, prominent
impossible-session filter, and planner action path are delivered by US4. Every
production release of FS-015 requires US1–US4 and the cross-cutting release
evidence.

### Incremental delivery

1. **US1**: Internal secure-read checkpoint; no production release.
2. **US2**: Immutable advisory comments and not-possible flags.
3. **US3**: Immediate revoke/replace and every terminal lifecycle condition;
   second internal checkpoint, still not eligible for production release.
4. **US4**: Planner feedback filter and guarded path to the existing session
   workflow; required for every production release.
5. **Polish**: Full security, performance, accessibility, and migration
   evidence required before release.

Each increment retains FS-013 publication behavior and adds no account,
automated delivery, editing, acceptance, or resolution workflow.

## Notes

- Use a feature branch such as `codex/fs-015-lecturer-token-review` before
  implementation because this is a customer-facing security slice.
- A task marked `[P]` still waits for its phase prerequisites.
- Avoid parallel edits to `backend/app/services/lecturer_review.py`,
  `client/src/api/lecturerReview.ts`, or
  `client/src/components/LecturerReviewManagement.tsx`.
- Do not add React Router, Redis, Celery, authentication packages, a general
  token framework, rich text, polling, multi-lecturer session relations, or a
  feedback-resolution/publication gate.
- Commit after each task or coherent test-first task group and run the relevant
  focused tests before proceeding.
