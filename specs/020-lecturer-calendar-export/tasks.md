# Tasks: Lecturer iCalendar Export

**Input**: Design documents from `/specs/020-lecturer-calendar-export/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are required by the constitution and FS-020 TR-001. Write each listed automated test before its corresponding production task and confirm the intended failure where practical. Manual Outlook, browser-download, zoom, and assistive-technology tasks cover behavior that pytest/jsdom cannot prove.

**Organization**: Tasks are grouped by user story. All three P1 stories are required for a safe deployable MVP; User Story 1 alone is a functional checkpoint, not a release boundary.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its phase prerequisites because it changes a different file and does not depend on another incomplete task in the same group.
- **[Story]**: Maps the task to the numbered user story in `spec.md`.
- Every task names the exact repository path it creates, changes, verifies, or uses for retained evidence.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a safe implementation workspace and install the one justified serializer dependency.

- [X] T001 Create a clean worktree from the verified `master` base on `codex/fs-020-lecturer-calendar-export`, transfer only `.specify/feature.json` and `specs/020-lecturer-calendar-export/` through a user-approved scoped commit or reviewed patch, do not switch the dirty `C:\Codex\planner-resource` workspace or transfer unrelated files, and record the base commit, transferred paths, and clean status in `specs/020-lecturer-calendar-export/validation/baseline.md`
- [X] T002 Pin `icalendar==7.2.2` in `backend/requirements-runtime.txt`, install the updated backend development requirements, record the resolved `icalendar` and `tzdata` versions in `specs/020-lecturer-calendar-export/validation/baseline.md`, and select the institution-approved iCal4j CLI release with exact version, official artifact URL, SHA-256 checksum, installation command, and validation command recorded in `specs/020-lecturer-calendar-export/validation/toolchain.md` before any validator task runs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Supply shared fixtures and one institution-time-zone authority before any story implementation.

**CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T003 [P] Create reusable FS-020 backend fixtures spanning at least three lecturers, two revisions, multiple courses, and at least 20 total mixed teaching/exam sessions, including assignment changes, an explicit empty lecturer projection, and deterministic clock/UID-key inputs in `backend/tests/lecturer_calendar_fixtures.py`
- [X] T004 [P] Extend public-review UI fixtures with mixed, empty, long-label, and safe export-response/error cases in `client/src/test/lecturerReviewFixtures.ts`
- [X] T005 [P] Write failing tests for startup validation, the `Europe/Vienna` default, invalid TZIDs, and FS-015 projection consistency with `INSTITUTION_TIMEZONE` in `backend/tests/api/test_lecturer_review.py`
- [X] T006 Implement the startup-validated `INSTITUTION_TIMEZONE` authority and replace the FS-015 hard-coded time-zone value in `backend/app/services/lecturer_review.py` and `backend/app/main.py` until T005 passes

**Checkpoint**: Shared test data and authoritative institution time-zone configuration are ready.

---

## Phase 3: User Story 1 — Download the Complete Personal Schedule (Priority: P1)

**Goal**: A valid FS-015 lecturer can explicitly confirm one download containing every and only the current assigned teaching/exam sessions, independent of displayed mode, dates, filters, selection, or stale page data; an explicitly empty projection yields a zero-event calendar.

**Independent Test**: Load a valid mixed multi-course review, apply restrictive filters and a non-covering visible period, select a session, change assignments after page load, confirm download, and verify one `.ics` with exactly the newly authoritative event set. Repeat with an explicitly complete empty projection and verify zero events.

### Tests for User Story 1 (write first and confirm intended failure)

- [X] T007 [P] [US1] Write service tests for every-and-only lecturer/revision scope, teaching plus exams, stale assignment additions/removals, source-order independence at the set level, and explicit empty projection handling in `backend/tests/services/test_lecturer_calendar_export.py`
- [X] T008 [P] [US1] Write FastAPI contract tests for one fixed bearer-only `GET /api/public/lecturer-review/calendar`, no request scope inputs, successful `.ics` delivery, explicit empty delivery, and no cross-scope bytes in `backend/tests/api/test_lecturer_calendar_export.py`
- [X] T009 [P] [US1] Extend exact public-route and near-miss authorization tests for the third lecturer-review operation, header-only bearer handling, rejected alternate methods/paths/query scope, and absent cookie authorization in `backend/tests/api/test_lecturer_bearer_authorization.py`
- [X] T010 [P] [US1] Write a performance test inside the release backend container constrained to 2 vCPUs and 2 GiB memory, using one process, release pins, disabled debug instrumentation, container-local SQLite, the deterministic seeded 100-event projection, and no concurrent requests; run 10 untimed warm-ups then 100 requests measured from invocation through complete body, retain image digest, host CPU, Docker version, every sample and percentile calculation, and assert p95 at most 3 seconds and maximum at most 10 seconds in `backend/tests/performance/test_lecturer_calendar_export_performance.py`
- [X] T011 [P] [US1] Write client transport tests for the fixed relative path, `Authorization` and `Accept` headers, `credentials: 'omit'`, successful blob return, and absence of secret/query/body scope in `client/src/api/lecturerReview.test.ts`
- [X] T012 [P] [US1] Write shared-workspace tests proving an optional neutral context action renders in the restricted context header, stays outside date/filter controls, and leaves planner usage unchanged in `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T013 [P] [US1] Write initial dialog tests for the complete unfiltered currently displayed event count including zero, explicit explanation that confirmation may re-evaluate to a different count, cancel/continue, no request on open, and duplicate-confirm prevention in `client/src/components/LecturerCalendarDownloadDialog.test.tsx`
- [X] T014 [P] [US1] Write page tests for action availability only after a valid complete load, filter/period/mode/selection independence, stale reassignment behavior, exactly one browser object-URL/anchor handoff, URL revocation, and workspace-state preservation in `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 1

- [X] T015 [US1] Add a read-only confirmed-export projection entry point that re-resolves the bearer and returns one complete current FS-015 lecturer/revision projection without consuming successful-view limits in `backend/app/services/lecturer_review.py`
- [X] T016 [US1] Create the focused in-memory calendar snapshot builder with one `VCALENDAR`, one event per projected teaching/exam session, explicit empty-calendar support, and no persistence/provider calls in `backend/app/services/lecturer_calendar_export.py`
- [X] T017 [US1] Expose the exact calendar GET route, transaction-scoped reauthorization/serialization, initial attachment response, and exact public allowlist entry in `backend/app/api/lecturer_review.py` and `backend/app/main.py`
- [X] T018 [P] [US1] Implement `downloadPublicLecturerCalendar(secret)` as a fixed-path bearer blob request returning validated download data in `client/src/api/lecturerReview.ts`
- [X] T019 [P] [US1] Add the optional neutral context-header action prop without filter or iCalendar knowledge in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T020 [P] [US1] Create the initial explicit-confirmation dialog with the informational complete opened-projection count, explanation that confirmation may export newer assignments with a different count, cancel/continue decisions, and pending duplicate-submit protection in `client/src/components/LecturerCalendarDownloadDialog.tsx`
- [X] T021 [US1] Orchestrate action visibility, informational count calculation from the complete unfiltered currently displayed `PublicReview`, confirmed secret-only authoritative request, and one temporary anchor/object-URL handoff in `client/src/pages/LecturerReviewPage.tsx`

**Checkpoint**: User Story 1 passes its focused backend/client tests and demonstrates complete-scope static download, but is not deployable until the P1 standards/import and privacy stories also pass.

---

## Phase 4: User Story 2 — Import Recognizable Events into Outlook (Priority: P1)

**Goal**: Every event is standards-valid, recognizable, explicitly Busy, and represented at the correct institution-local instant with complete time-zone metadata; the retained corpus validates independently and imports in the representative Outlook environment.

**Independent Test**: Generate the teaching-only, exam-only, mixed, empty, DST, cross-midnight, missing-location, identical-display, 100-event, Unicode/reserved-character, embedded-newline, and long-line fixtures; validate all independently and import them in the designated Outlook environment while comparing counts and required fields.

### Tests and fixtures for User Story 2 (write first and confirm intended failure)

- [X] T022 [P] [US2] Add the complete conformance source/expectation corpus, using synthetic serializer-level `CalendarEvent` values for missing location and for cross-midnight with explicit complete start and following-day end date-times, without expanding production models or inferring rollover from clock times, under `backend/tests/fixtures/lecturer_calendar/`
- [X] T023 [US2] Extend serializer tests for exact `VCALENDAR`/`VEVENT` property cardinality, recognizable summaries/descriptions, optional location omission, `TRANSP:OPAQUE`, UTF-8 escaping, CRLF endings, 75-octet folding, one bounded `VTIMEZONE`, DST/different-device-zone instants, forbidden component/property absence, exact UID derivation vectors, revision-created `DTSTAMP`, start/end/UID ordering, source-order independence, and three-run unchanged-fixture byte equality in `backend/tests/services/test_lecturer_calendar_export.py`
- [X] T024 [P] [US2] Extend API tests for `text/calendar; charset=utf-8`, the exact NFC/Unicode-category/180-scalar/reserved-device filename algorithm, fixed `resource-planner-calendar.ics` ASCII fallback, authoritative Unicode `filename*`, privacy/no-store headers, `nosniff`, and no calendar bytes or disposition on failure in `backend/tests/api/test_lecturer_calendar_export.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement the complete final RFC 5545/RFC 7986 byte profile, fixed `PRODID`, effective I-002 labels, recognizable event content, `TRANSP:OPAQUE`, standards escaping/folding, deterministic semester-bounded `VTIMEZONE`, byte-exact UID derivation, immutable revision-created `DTSTAMP`, start/end/UID event ordering, stable component/property ordering, and download-clock independence in `backend/app/services/lecturer_calendar_export.py`
- [X] T026 [US2] Implement the exact filename algorithm from `specs/020-lecturer-calendar-export/contracts/icalendar-profile.md`, fixed `resource-planner-calendar.ics` RFC 6266 fallback, authoritative UTF-8 `filename*`, exact media type, attachment, privacy, and `nosniff` headers in `backend/app/api/lecturer_review.py`
- [X] T027 [US2] Generate and retain the exact `.ics` fixture corpus, source expectation manifest, dependency versions, and SHA-256 checksums under `specs/020-lecturer-calendar-export/validation/fixtures/`
- [X] T028 [US2] Verify the iCal4j artifact against the version and SHA-256 pinned in `specs/020-lecturer-calendar-export/validation/toolchain.md`, run every retained fixture with that exact CLI, and record tool version, command, fixture checksums, and zero syntax/structural errors in `specs/020-lecturer-calendar-export/validation/rfc5545-validation.md`
- [ ] T029 [US2] Manually import/open every retained fixture in the institution-designated Outlook environment and record Outlook/Windows build, account type, import path, tester/date, repair prompts, event counts, summaries, starts/ends, durations, time zones, Busy status, locations, and descriptions in `specs/020-lecturer-calendar-export/validation/outlook-import.md`

**Checkpoint**: User Story 2 proves standards conformance and the bounded representative Outlook import contract independently of privacy-notice behavior.

---

## Phase 5: User Story 3 — Understand and Preserve the Privacy Boundary (Priority: P1)

**Goal**: The lecturer receives a complete pre-download static/privacy notice; cancellation is inert; ended, unauthorized, or incomplete scope returns no file and minimum disclosure; retryable and terminal outcomes preserve or clear protected state correctly; export does not mutate domain, link-lifecycle, or provider data.

**Independent Test**: Exercise notice open/cancel/confirm plus before/at/after expiry, revocation, replacement, abandonment, supersession, malformed/unknown secrets, incomplete/corrupt projection, interruption, and a lifecycle change between notice and confirmation. Verify no partial/cross-scope data, safe outcomes, exact focus/context behavior, and non-mutation.

### Tests for User Story 3 (write first and confirm intended failure)

- [X] T030 [P] [US3] Extend API tests for before/at/after expiry, revocation, replacement, abandonment, supersession, malformed/unknown bearer, incomplete/corrupt projection, safe 404/429/503 bodies, privacy deny-list inspection, and snapshots proving no changes to schedule, feedback, revision, publication, review-link lifecycle, successful-view limits, export records, or provider data; separately assert any permitted invalid-source abuse-control evidence contains no bearer, identity, schedule, filename, or event data and does not alter link validity in `backend/tests/api/test_lecturer_calendar_export.py`
- [X] T031 [P] [US3] Add concurrent assignment/lifecycle/projection tests proving a locked coherent snapshot or no file, strict published-snapshot completeness, no partial bytes, and no link lifecycle/view-limit mutation in `backend/tests/services/test_lecturer_review_concurrency.py`
- [X] T032 [P] [US3] Extend client API tests for safe 404 terminal mapping, retryable 429/network/5xx/wrong-media/missing-or-unsafe-filename outcomes, bounded error handling, and secret/raw-header/body/exception non-disclosure in `client/src/api/lecturerReview.test.ts`
- [X] T033 [P] [US3] Extend dialog tests for the full static-file/privacy/repeat-import notice, accessible name/description, safe default focus, Tab/Shift+Tab containment, Escape/cancel, focus restoration, busy/error announcements, and no backdrop confirmation in `client/src/components/LecturerCalendarDownloadDialog.test.tsx`
- [X] T034 [P] [US3] Extend page tests for no request on notice open/cancel, context and unsent-feedback preservation, retry without duplicate request, terminal protected-DOM clearing, polite success, alert failure, long labels, zero count, and forced no-double-modal composition in `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 3

- [X] T035 [US3] Harden the read-only export authorization/projection path to apply every FS-015 lifecycle/current-revision check without recording successful page access, consuming limits, or materializing token lifecycle, and distinguish explicit empty from missing/corrupt published data in `backend/app/services/lecturer_review.py`
- [X] T036 [US3] Map authorization/lifecycle failures to indistinguishable 404 responses and incomplete/serialization failures to safe retryable no-file responses, with no raw diagnostics or attachment metadata, in `backend/app/api/lecturer_review.py` and `backend/app/schemas/lecturer_review.py`
- [X] T037 [P] [US3] Implement strict media/disposition validation and safe retryable/terminal error mapping without logging protected values in `client/src/api/lecturerReview.ts`
- [X] T038 [P] [US3] Complete the purpose-built modal's fixed German notice, accessibility mechanics, busy behavior, safe retryable alert, Escape/backdrop rules, and deterministic focus restoration in `client/src/components/LecturerCalendarDownloadDialog.tsx`
- [X] T039 [US3] Complete cancel/success/retryable/terminal orchestration, protected-state clearing, workspace-context retention, and safe live-region announcements in `client/src/pages/LecturerReviewPage.tsx`
- [X] T040 [US3] Add only the required context-action, dialog, error, focus, 44-pixel target, 200%-zoom, and 320-CSS-pixel wrapping styles in `client/src/App.css`
- [ ] T041 [US3] Run keyboard-only, NVDA/Firefox, 200% zoom, 320-CSS-pixel, and Edge/Chrome/Firefox checks plus an unaided review with at least 10 total participants, each either a representative lecturer or designated acceptance reviewer; calculate `required_successes = ceil(0.90 * participant_count)` and retain anonymized participant category, outcome, duration, and failed step while requiring at least `required_successes` complete find/notice/download/manual-Outlook-import paths within five minutes, unanimous static-snapshot comprehension, and at least `required_successes` correct repeat-import/manual-removal responses against SC-008/SC-009/SC-012 in `specs/020-lecturer-calendar-export/validation/accessibility-usability.md`

**Checkpoint**: User Stories 1–3 together form the minimum safe deployable FS-020 outcome.

---

## Phase 6: User Story 4 — Receive a Deterministic Snapshot (Priority: P2)

**Goal**: Unchanged authoritative inputs produce identical filenames and bytes; the same session retains an opaque UID across display changes within one revision; distinct sessions/revisions remain distinct; the UI makes no repeat-import reconciliation promise.

**Independent Test**: Export every unchanged fixture three times, vary retrieval order, then edit/add/remove sessions and create identical-looking sessions across revisions. Compare filename, bytes, metadata, order, UIDs, and repeat-import notice without asking Outlook to reconcile files.

### Tests for User Story 4 (write first and confirm intended failure)

- [X] T042 [P] [US4] Add advanced regression tests for three-run byte equality under identical projection/terminology/label/TZID-rule/key/serializer/`tzdata` inputs, display edit/add/remove behavior, identical-looking sessions, cross-revision UID distinction, and changed-snapshot output without redefining the final byte profile already tested in T023 in `backend/tests/services/test_lecturer_calendar_export.py`
- [X] T043 [P] [US4] Add repeat-request API tests for identical filenames/bytes and privacy-safe content disposition across unchanged inputs in `backend/tests/api/test_lecturer_calendar_export.py`
- [X] T044 [P] [US4] Add dialog/page assertions that repeat import may duplicate, the product cannot reconcile/remove prior imports, and success never claims Outlook update/de-duplication in `client/src/components/LecturerCalendarDownloadDialog.test.tsx` and `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 4

- [X] T045 [US4] Reconcile T042–T044 against the final serializer and retained evidence without a planned byte-profile change; if any correction in `backend/app/services/lecturer_calendar_export.py` or `backend/app/api/lecturer_review.py` changes calendar or filename bytes, regenerate `specs/020-lecturer-calendar-export/validation/fixtures/` and repeat T028 and T029 before proceeding
- [X] T046 [P] [US4] Document that `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` stability preserves FS-020 UIDs and that key or serializer/tzdata changes require renewed fixture/Outlook evidence in `infrastructure/docker/README.md`
- [X] T047 [US4] Re-run the complete retained corpus three times and record byte/filename equality, UID continuity/distinction, source-order invariance, changed-snapshot behavior, tool versions, and checksums in `specs/020-lecturer-calendar-export/validation/determinism.md`

**Checkpoint**: All four user stories are independently evidenced and the P2 deterministic snapshot guarantees are complete.

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Prove full-slice regression safety and consolidate release evidence without adding new scope.

- [X] T048 [P] Run the focused backend commands from `specs/020-lecturer-calendar-export/quickstart.md` and record exact commands, environment, duration, and passing results in `specs/020-lecturer-calendar-export/validation/automated-backend.md`
- [X] T049 [P] Run the focused client tests plus lint and build from `specs/020-lecturer-calendar-export/quickstart.md` and record exact commands, environment, duration, and passing results in `specs/020-lecturer-calendar-export/validation/automated-client.md`
- [X] T050 Inspect the final route surface, request/response bytes, filename, calendar metadata/events/UIDs, client DOM/errors, repository imports, and provider fakes for TR-009/TR-012 exclusions and record the deny-list result in `specs/020-lecturer-calendar-export/validation/privacy-scope-audit.md`
- [X] T051 Run the complete backend pytest suite and complete client test suite after T048–T050, then record passing results or explicit unresolved residual risks in `specs/020-lecturer-calendar-export/validation/full-regression.md`
- [X] T052 Reconcile every FR/TR/SC and all four independent-test checkpoints with automated, iCal4j, Outlook, privacy, performance, usability, browser, and accessibility evidence in `specs/020-lecturer-calendar-export/validation/release-checklist.md`

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 — Setup**: Starts immediately. T001 precedes every file-changing task; T002 follows in the isolated workspace.
- **Phase 2 — Foundational**: Depends on Phase 1 and blocks all user stories. T003–T005 can proceed in parallel; T006 follows T005.
- **Phase 3 — US1**: Depends on Phase 2. All US1 tests T007–T014 precede production tasks T015–T021.
- **Phase 4 — US2**: Depends on the complete-download endpoint from US1. T022 supplies fixtures before T023; T024 can run in parallel; T025–T026 implement the complete final byte and delivery contracts; T027 generates those final fixtures before external validation T028–T029.
- **Phase 5 — US3**: Depends on US1's endpoint/interaction and may proceed alongside US2 after US1. Tests T030–T034 precede T035–T040; manual acceptance T041 follows the completed interaction.
- **Phase 6 — US4**: Depends on US2's final calendar bytes/evidence and US3's final repeat-import notice. Tests T042–T044 precede evidence gate T045; documentation T046 can proceed in parallel, and T047 follows the gate. Any byte-changing correction at T045 forces T027–T029 to be repeated.
- **Phase 7 — Polish**: Depends on all desired story phases. T048 and T049 can run in parallel; T050 follows integrated behavior; T051 follows focused verification; T052 is last.

### User story dependency graph

```text
Setup -> Foundation -> US1 Complete Download
                            |-> US2 Recognizable Standards/Outlook Import -|
                            |-> US3 Privacy and Safe Lifecycle ------------|-> US4 Determinism
                                                                              -> Polish/Release Evidence
```

- **US1 (P1)**: First functional vertical after Foundation; no dependency on another story.
- **US2 (P1)**: Extends US1's static calendar with the complete standards/import profile; independently tested through fixtures, validator, and Outlook.
- **US3 (P1)**: Extends US1's request/dialog with the required privacy and lifecycle boundary; independently tested through safe-failure/non-mutation and interaction paths. It can run in parallel with US2 after US1.
- **US4 (P2)**: Requires the final calendar profile and notice semantics from US2/US3; independently tested through repeat and changed-snapshot comparisons.

### Within each story

- Complete and observe the listed automated tests failing before changing their corresponding production files where practical.
- Test fixtures precede tests that consume them; services precede HTTP/page integrations; external/manual evidence follows complete automated behavior.
- Do not mark a checkpoint complete with partial files, skipped privacy checks, a library self-parse substituted for independent validation, or unrecorded manual residual risk.

---

## Parallel Execution Examples

### User Story 1

After Foundation, separate workers can write T007–T014 concurrently because each targets a distinct test file. After those failures are established, backend T015–T017 and client T018–T020 can proceed on their respective files; T021 integrates the completed client pieces.

```text
Backend tests: T007 + T008 + T009 + T010
Client tests:  T011 + T012 + T013 + T014
Implementation after tests: (T015 -> T016 -> T017) || T018 || T019 || T020; then T021
```

### User Story 2

T022 creates the fixture corpus while T024 defines the HTTP delivery assertions. T023 follows the fixture data and fixes the final UID/DTSTAMP/order expectations before T025. After the final byte and HTTP implementations T025–T026 pass, fixture retention T027 precedes independent validator and Outlook work.

```text
Test preparation: (T022 -> T023) || T024
Implementation:    T025 -> T026
Evidence:          T027 -> (T028 || T029)
```

### User Story 3

T030–T034 can be written concurrently in distinct backend/client test files. After failures are established, server hardening and client interaction work can proceed in parallel before the page/CSS/manual integration tasks.

```text
Tests:          T030 || T031 || T032 || T033 || T034
Implementation: (T035 -> T036) || T037 || T038; then T039 -> T040 -> T041
```

### User Story 4

The backend service/API determinism regressions and client copy tests are independent. The final byte profile was already implemented before US2 evidence; documentation can proceed alongside the no-stale-evidence gate.

```text
Tests:          T042 || T043 || T044
Evidence gate:  T045 || T046; then T047
```

---

## Implementation Strategy

### P1 minimum deployable scope

1. Complete Setup and Foundation.
2. Complete US1 and stop for its functional checkpoint; do not deploy it alone.
3. Complete US2 and US3, which may run in parallel after US1.
4. Validate US1–US3 together as the minimum safe, standards-compatible, privacy-complete release candidate.
5. Verify US4 deterministic repeat behavior without changing the final US2 bytes; if a correction changes bytes, repeat the retained-fixture, validator, and Outlook evidence before declaring FS-020 complete.

### Incremental delivery

1. **US1** proves complete authoritative scope and browser file handoff.
2. **US2** proves recognizable, time-zone-correct, standards-valid Outlook import.
3. **US3** closes the notice, authorization-race, safe-failure, privacy, non-mutation, and accessibility boundary.
4. **US4** verifies stable identities, changed-snapshot behavior, and byte-for-byte repeatability against the already finalized profile.
5. **Polish** consolidates full regression and release evidence.

### Scope discipline

- Do not introduce database migrations, export persistence/history, preview tokens, client scope arguments, planner export, calendar subscriptions, provider adapters/APIs, account connections, invitations, reminders, background jobs, global client stores, new terminology fetches, or multi-client certification.
- Keep the implementation inside the existing FS-015 API/service/page boundary plus the one focused serializer service, one neutral workspace action slot, and one dedicated dialog justified in `plan.md`.
- A task is complete only when its tests/evidence pass and protected data never appears outside the contract.

---

## Notes

- `[P]` tasks touch different files or independent retained-evidence files once their phase prerequisites are satisfied.
- `[US1]` through `[US4]` map directly to the four user stories in `spec.md`.
- Commit only logical verified groups; never stage or overwrite unrelated workspace changes.
- If the independent validator, representative Outlook environment, at-least-10-participant acceptance review, or assistive-technology environment is unavailable, record the exact missing evidence and residual risk. FS-020 remains not acceptance-complete until the required evidence exists.
