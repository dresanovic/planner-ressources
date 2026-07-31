# Tasks: FS-015 Accountless Lecturer Token Review

**Input**: Design documents from
`specs/015-lecturer-token-review/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, and `quickstart.md`

**Baseline boundary**: The token lifecycle, one-time secret handling,
one-lecturer/one-revision scope, immutable feedback persistence, lifecycle
coupling, misuse controls, generic safe failures, and non-blocking publication
are implemented. These tasks extend that baseline and add regression coverage;
they do not recreate migration `0009`, add another endpoint, or introduce a
parallel lecturer workspace.

**Tests**: Tests are required before corresponding production changes wherever
automated verification is practical.

**Discovery rule**: If implementation reveals a behavioral discrepancy or a
new requirement, stop before changing the corresponding production behavior,
update `spec.md` and the affected plan/contract/task artifacts, then resume
test-first delivery.

**Organization**: Tasks are grouped by user story. Story numbers map directly
to `spec.md`, while phases are ordered by delivery priority for the remaining
extension.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on an incomplete task.
- **[Story]**: The user story from `spec.md`.
- Every task names its exact target file or files.

---

## Phase 1: Setup and Baseline Evidence

**Purpose**: Establish a trustworthy pre-extension baseline without changing
the implemented domain model.

- [X] T001 Run the existing focused FS-015 backend and client suites and record the pre-extension command results without claiming extension acceptance in `specs/015-lecturer-token-review/quickstart.md`

**Checkpoint**: Existing failures and unrelated working-tree changes are known
before production work begins.

---

## Phase 2: Foundational Security Boundary

**Purpose**: Enforce the access boundary required by every restricted public
composition.

**CRITICAL**: Complete this phase before any user-story production work.

- [X] T002 Add failing matrix tests proving active and ended exact-shape bearer secrets whose digests resolve to stored lecturer-review links are rejected before validation or mutation on representative non-public planner APIs, while an unrelated exact-length bearer is not classified as a lecturer credential and gateway-authorized planner requests still pass, in `backend/tests/api/test_lecturer_bearer_authorization.py`
- [X] T003 Implement a centralized non-public API guard that parses the exact FS-015 bearer grammar, resolves its digest against active or ended lecturer-review links, rejects only a stored-link match before route handling, and leaves unrelated bearer values to the gateway-authorized planner path in `backend/app/main.py`

**Checkpoint**: A lecturer link cannot acquire planner authority through a
constructed request, independent of which controls the client renders.

---

## Phase 3: User Story 1 - Share One Lecturer's Revision Safely (Priority: P1)

**Goal**: Extend the existing public GET with the complete, current, sanitized
teaching/exam projection needed by the shared workspace while preserving the
implemented issue/copy/token behavior.

**Independent Test**: Issue a link for one lecturer in a revision containing
several lecturers and courses, call the public GET, and verify that it returns
every and only that lecturer's current teaching/exam assignments, safe facets
and validation context, and a valid authoritative empty projection after all
assignments leave scope.

### Tests for User Story 1

- [X] T004 [US1] Extend reusable backend fixtures with multi-course teaching/exam assignments, cross-scope validation counterparts, assignment changes, and zero-assignment cases in `backend/tests/lecturer_review_fixtures.py`
- [X] T005 [P] [US1] Extend strict public-review client fixtures with semester bounds, course/cohort/study-type data, teaching units, exam duration/type, room references, safe lifecycle/validation facets, and privacy canaries in `client/src/test/lecturerReviewFixtures.ts`
- [X] T006 [P] [US1] Add failing tests for a reusable full-revision validation derivation with unchanged planner results, complete current lecturer projection, reload-time assignment changes, authoritative empty scope, sanitized scoped findings, and expanded reference-scale timing in `backend/tests/services/test_calendar_workspace.py`, `backend/tests/services/test_lecturer_review.py`, and `backend/tests/performance/test_lecturer_review_performance.py`
- [X] T007 [P] [US1] Add failing API contract tests for the expanded safe DTO, exact public allowlist, no-store headers, lecturer-only facets, and absence of planner/other-lecturer fields in `backend/tests/api/test_lecturer_review.py`
- [X] T008 [US1] Add failing TypeScript exact-key transport tests for the expanded public contract, nullable historical context, and rejection of unsafe extra fields without presentation adaptation in `client/src/api/lecturerReview.test.ts`

### Implementation for User Story 1

- [X] T009 [P] [US1] Expand only the lecturer-safe public review, course, session, validation, facet, and captured-session schemas defined by the OpenAPI contract in `backend/app/schemas/lecturer_review.py`
- [X] T010 [US1] Expose one reusable internal FS-014 full-revision validation derivation, retain planner behavior, invoke it for the complete bound-lecturer projection, sanitize it to scoped occurrences, and emit safe facets without changing persistence in `backend/app/services/calendar_workspace.py` and `backend/app/services/lecturer_review.py`
- [X] T011 [US1] Return the expanded safe projection and preserve generic failure, stale-target, and non-cacheable response behavior on the existing two public operations in `backend/app/api/lecturer_review.py`
- [X] T012 [P] [US1] Extend only strict public transport types and exact-key validators without importing or adapting to the planner calendar API model in `client/src/api/lecturerReview.ts`

**Checkpoint**: The public API independently provides the complete safe
projection required by the extension, with no new table, migration, or route.

---

## Phase 4: User Story 2 - Review Every Personal Assignment in the Shared Workspace (Priority: P1)

**Goal**: Render the public projection through the established
Week/Day/Month/List workspace and adaptive session pane under an explicit
restricted access profile.

**Independent Test**: Open one valid lecturer link, exercise every calendar/list
mode and applicable filter, select teaching and exam occurrences at wide,
constrained, and narrow widths, and verify fixed lecturer context, preserved
workspace state, correct empty states, safe pane content, and complete absence
of planner controls.

### Tests for User Story 2

- [X] T013 [US2] Extend shared calendar and public review fixtures with long labels, partial validation, no-match filters, and responsive selection-retention cases in `client/src/test/calendarWorkspaceFixtures.ts` and `client/src/test/lecturerReviewFixtures.ts`
- [X] T014 [P] [US2] Add failing adapter and restricted-access tests for modes, fixed lecturer context, applicable facets, intersecting filters, state retention, complete schedule with partial validation, authoritative-empty versus filter-empty results, keyboard operation, and planner-control DOM absence in `client/src/components/calendarWorkspaceUtils.test.ts` and `client/src/components/CalendarPlanningWorkspace.test.tsx`
- [X] T015 [P] [US2] Add failing shared selectable-row tests for teaching/exam identity, keyboard selection, filter results, and planner List-mode regression in `client/src/components/ScheduleOccurrenceList.test.tsx` and `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T016 [P] [US2] Add failing restricted-pane tests for safe field allowlisting, feedback-only actions, responsive beside/overlay/full-screen composition, inert obscured content, non-color semantics, focus containment, and focus restoration in `client/src/components/SessionPane.test.tsx`
- [X] T017 [P] [US2] Replace flat-page expectations with failing integration tests for shared calendar/list composition, fixed context, live-region announcements, 320-CSS-pixel structure, no polling/refresh action, reload-only updates, exact selection, and isolated exact-path public bootstrap in `client/src/pages/LecturerReviewPage.test.tsx` and `client/src/main.test.tsx`

### Implementation for User Story 2

- [X] T018 [P] [US2] Extract the established selectable teaching/exam row behavior into the neutral shared renderer in `client/src/components/ScheduleOccurrenceList.tsx`
- [X] T019 [US2] Refactor planner List mode to consume the neutral occurrence renderer without changing planner edit/generation behavior in `client/src/components/DraftSchedulePanel.tsx`
- [X] T020 [US2] Implement the sole public-to-presentation adapter and filter mapping in `client/src/components/calendarWorkspaceUtils.ts`, then add the discriminated lecturer-review access profile, fixed-context slot, permitted facet configuration, and filter-empty handling in `client/src/components/CalendarPlanningWorkspace.tsx`
- [X] T021 [P] [US2] Add restricted presentation/action composition to the existing pane while keeping planner behavior as the default in `client/src/components/SessionPane.tsx`
- [X] T022 [US2] Compose the normalized public projection through the shared workspace, neutral list, and restricted session pane with exact teaching/exam selection in `client/src/pages/LecturerReviewPage.tsx`
- [X] T023 [US2] Add responsive restricted-workspace, fixed-context, filter, overlay, full-screen pane, wrapping, and focus-visible styling in `client/src/App.css`

**Checkpoint**: The accountless lecturer has the familiar shared schedule
experience with a minimum-data transport and no planner authority.

---

## Phase 5: User Story 4 - End or Replace Access Immediately (Priority: P1)

**Goal**: Preserve the implemented terminal-link and generic safe-failure
semantics after the public page gains richer workspace state.

**Independent Test**: Load the expanded workspace, then exercise expired,
revoked, replaced, abandoned, superseded, malformed, unknown, and throttled
credentials and verify that every terminal result clears all protected
workspace data and feedback drafts and that only the replacement/current link
can load or submit.

### Tests for User Story 4

- [X] T024 [P] [US4] Extend API regression tests across expiry, revoke, replace, abandon, supersede, malformed, unknown, and throttled outcomes to prove generic response equivalence and no expanded DTO leakage in `backend/tests/api/test_lecturer_review.py`
- [X] T025 [P] [US4] Add failing client tests proving terminal results and older in-flight responses cannot restore fixed context, facets, occurrences, selection, pane details, drafts, or same-link history in `client/src/pages/LecturerReviewPage.test.tsx`

### Implementation for User Story 4

- [X] T026 [US4] Clear every protected restricted-workspace and draft state before rendering the generic unavailable result and prevent stale request completion from restoring it in `client/src/pages/LecturerReviewPage.tsx`
- [X] T027 [US4] Preserve generic terminal/throttle parsing and request-generation precedence for the expanded public contract in `client/src/api/lecturerReview.ts`

**Checkpoint**: Richer presentation state does not weaken revocation,
replacement, expiry, lifecycle ending, or safe-failure privacy.

---

## Phase 6: User Story 3 - Submit Advisory Schedule Feedback (Priority: P2)

**Goal**: Move established feedback actions into the restricted pane, protect
nonblank drafts during lecturer-initiated context changes, and keep successful
submissions from refreshing the assignment projection.

**Independent Test**: Enter session feedback, attempt close/session/filter
changes and responsive transitions, exercise Cancel and Discard, submit all
three feedback kinds, and verify immutable traceability, local same-link
history updates, stale-scope rejection, and zero schedule mutation.

### Tests for User Story 3

- [X] T028 [P] [US3] Add failing neutral-copy and accessible-focus tests for feedback discard/cancel use without changing planner unsaved-change behavior in `client/src/components/DiscardChangesDialog.test.tsx`
- [X] T029 [P] [US3] Add failing page tests for drafts keyed by occurrence, close/session/filter guards, responsive preservation, automatic scope-loss discard, successful local history append, and stale-target reload guidance without an automatic GET in `client/src/pages/LecturerReviewPage.test.tsx`
- [X] T030 [P] [US3] Extend client API tests for stable retry UUIDs, created/idempotent results, authoritative stale-target rejection, and no implicit projection reload in `client/src/api/lecturerReview.test.ts`

### Implementation for User Story 3

- [X] T031 [P] [US3] Generalize the existing discard dialog with caller-supplied feedback wording and predictable cancel/discard focus behavior in `client/src/components/DiscardChangesDialog.tsx`
- [X] T032 [US3] Keep comment and impossible-explanation drafts by occurrence and guard pane close, session change, and target-hiding filters through the shared discard dialog in `client/src/pages/LecturerReviewPage.tsx`
- [X] T033 [US3] Remove the public refresh control and post-submit projection GET, clear only the successful draft, and append the returned immutable feedback item locally in `client/src/pages/LecturerReviewPage.tsx`
- [X] T034 [US3] On authoritative scope loss, clear the selected occurrence and drafts, announce the reason, restore predictable workspace focus, and direct reload/reopen without creating feedback in `client/src/pages/LecturerReviewPage.tsx`

**Checkpoint**: Feedback remains advisory and immutable, drafts are not lost
silently, and the clarified reload-only assignment behavior is preserved.

---

## Phase 7: User Story 5 - Coordinate Feedback Without Losing Planner Control (Priority: P3)

**Goal**: Broaden the existing planner destination into one
revision-contextual Lecturer coordination surface for link management,
item-first feedback filtering, exact counters, and affected-session navigation.

**Independent Test**: Create comments and repeated impossible items for several
lecturers and sessions, apply every filter alone and in intersection, verify
all four counters and partial/unavailable behavior, navigate to a current exact
occurrence, inspect historical context for unavailable targets, and publish
without a feedback gate.

### Tests for User Story 5

- [X] T035 [P] [US5] Add failing navigation-label and snapshot expectations for the single `Lecturer coordination` destination while preserving its existing internal destination identity in `client/src/components/ApplicationNavigation.test.tsx` and `client/src/pages/CourseSchedulePage.snapshot.test.ts`
- [X] T036 [P] [US5] Add failing item-first filter and counter tests covering lecturer, course, session kind, feedback kind, revision-comment exclusion, repeated impossible items, distinct sessions, clear-all, link-history isolation, and partial/unavailable counts in `client/src/components/LecturerReviewManagement.test.tsx`
- [X] T037 [P] [US5] Add failing exact-session navigation tests for correct semester/revision establishment, dirty-navigation guarding, current occurrence selection, and no substitution for unavailable targets in `client/src/pages/CourseSchedulePage.test.tsx`
- [X] T038 [P] [US5] Extend publication regression tests to prove absent, negative, repeated, expired-link, and retained historical feedback never changes FS-013 lifecycle eligibility in `backend/tests/services/test_schedule_lifecycle.py`

### Implementation for User Story 5

- [X] T039 [P] [US5] Rename user-facing Schedule navigation and page copy to `Lecturer coordination` without adding a second destination or generic Action Center in `client/src/components/ApplicationNavigation.tsx` and `client/src/pages/CourseSchedulePage.tsx`
- [X] T040 [US5] Filter immutable feedback items before regrouping and derive all-item, comment-item, impossible-item, and distinct-affected-session counters from the identical active scope while leaving link management outside filters in `client/src/components/LecturerReviewManagement.tsx`
- [X] T041 [US5] Preserve immutable captured context and wire only authoritative current occurrence references through the existing guarded FS-019 Schedule navigation path in `client/src/components/LecturerReviewManagement.tsx` and `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: Planners manage links and feedback in one destination, can
reach exact current sessions, and retain sole revision/publication authority.

---

## Phase 8: Polish and Cross-Cutting Verification

**Purpose**: Prove the complete extension is secure, accessible, performant,
and regression-safe.

- [X] T042 [P] Run the test-first 100-session/200-feedback expanded-projection performance guard and confirm existing thresholds remain unchanged in `backend/tests/performance/test_lecturer_review_performance.py`
- [X] T043 [P] Run the test-first privacy canaries for raw tokens, other lecturers, contacts, planner notes, raw finding counterparts, administrative fields, and executable feedback text in `backend/tests/api/test_lecturer_review.py` and `client/src/api/lecturerReview.test.ts`
- [X] T044 [P] Run the test-first keyboard, live-region, non-color, focus-containment, focus-restoration, and 320-CSS-pixel structure checks in `client/src/components/CalendarPlanningWorkspace.test.tsx`, `client/src/components/SessionPane.test.tsx`, and `client/src/pages/LecturerReviewPage.test.tsx`
- [X] T045 Run the focused and full backend suites from `specs/015-lecturer-token-review/quickstart.md`, including migration and FS-013 lifecycle regressions, and record exact extension results in `specs/015-lecturer-token-review/quickstart.md`
- [X] T046 Run the focused and full client suites, lint, and production build from `specs/015-lecturer-token-review/quickstart.md` and record exact extension results in `specs/015-lecturer-token-review/quickstart.md`
- [X] T047 Execute the manual gateway, stored-link bearer denial and unrelated-bearer passage, reload-only, responsive pane, keyboard, 200% zoom, screen-reader, privacy-canary, reference-scale, and SC-006/SC-007/SC-016 ten-participant moderated protocols and record evidence or explicit pending status in `specs/015-lecturer-token-review/quickstart.md`
- [X] T048 Perform a final consistency audit across `specs/015-lecturer-token-review/spec.md`, `specs/015-lecturer-token-review/plan.md`, `specs/015-lecturer-token-review/data-model.md`, and `specs/015-lecturer-token-review/contracts/`; if behavior differs, reopen the affected specification, planning, and test tasks before any further production change

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 - Setup**: Starts immediately.
- **Phase 2 - Foundation**: Depends on T001 and blocks all production work.
- **Phase 3 - US1**: Depends on Phase 2; supplies the safe transport needed by
  the shared public workspace.
- **Phase 4 - US2**: Depends on US1's strict public transport contract.
- **Phase 5 - US4**: Backend regression tests can start after Phase 2; expanded
  client-state clearing completes after US2.
- **Phase 6 - US3**: Depends on US2 because feedback is composed inside the
  restricted shared pane.
- **Phase 7 - US5**: Depends only on Phase 2 behaviorally and may proceed beside
  US1-US4; a single developer should sequence shared fixture/API-file edits
  after US1 to avoid conflicts.
- **Phase 8 - Polish**: Depends on every story selected for delivery.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 -> US2 -> US3
                         \-> US4
                    \-----------> US5
All selected stories -----------> Polish
```

### Within Each User Story

- Write or update the listed tests first and confirm they fail for the intended
  missing behavior where practical.
- Update fixtures before tests that consume the new fixture shape.
- Implement the smallest production change that satisfies the failing tests.
- Keep transport privacy enforcement before presentation reuse.
- Complete the independent test at each checkpoint before advancing.

### Parallel Opportunities

- After T004, backend service and API projection tests T006-T007 can run in
  parallel with client fixture and transport work T005/T008.
- After fixture task T013, US2 component tests T014-T017 target separate files
  and can run in parallel.
- Neutral list extraction T018 and restricted pane composition T021 can run in
  parallel.
- US4 backend and client regression tests T024-T025 can run in parallel.
- US3 test tasks T028-T030 can run in parallel; T031 can proceed separately
  from the page implementation after its test fails.
- US5 test tasks T035-T038 can run in parallel, and navigation copy T039 can
  proceed separately from coordination derivation T040.
- Cross-cutting guards T042-T044 can run in parallel after story completion.

---

## Parallel Example: User Story 1

```text
After T004 and T005:
Task T006: Service projection and sanitization tests
Task T007: Public API contract/privacy tests
Task T008: Client exact-key transport tests
```

## Parallel Example: User Story 2

```text
Tests:
Task T014: Restricted calendar workspace tests
Task T015: Neutral occurrence-list tests
Task T016: Restricted session-pane tests
Task T017: Public-page integration tests

Implementation after failing tests:
Task T018: Neutral list extraction
Task T021: Restricted pane composition
```

## Parallel Example: User Story 4

```text
Task T024: Backend terminal-link privacy regressions
Task T025: Client terminal-state clearing regressions
```

## Parallel Example: User Story 3

```text
Task T028: Shared discard-dialog tests
Task T029: Public draft/submission integration tests
Task T030: Client retry/stale-response tests
```

## Parallel Example: User Story 5

```text
Task T035: Navigation/heading tests
Task T036: Coordination filter/counter tests
Task T037: Exact-session navigation tests
Task T038: Publication non-gating regressions
```

---

## Implementation Strategy

### Extension MVP

1. Complete Setup and Foundational phases.
2. Complete US1 so the public API provides the expanded sanitized projection.
3. Complete US2 so lecturers receive the shared calendar/list and restricted
   pane experience.
4. Complete US4 so the richer workspace is cleared by every terminal-link
   outcome.
5. Stop and run the US1/US2/US4 independent tests plus the focused security
   regression suite.

US1 alone preserves and expands the secure transport but does not deliver the
new product outcome, and US1 plus US2 without US4 does not finish the
security-sensitive terminal-state integration. The smallest safe demonstrable
extension MVP is therefore US1 plus US2 plus US4.

### Incremental Delivery

1. **US1 + US2**: Complete safe shared schedule review.
2. **US4**: Confirm richer client state cannot weaken access ending.
3. **US3**: Move feedback into the pane and add draft protection.
4. **US5**: Complete planner-side Lecturer coordination.
5. **Polish**: Run full security, accessibility, performance, and regression
   acceptance.

### Parallel Team Strategy

After Foundation:

- Backend work can advance US1 projection/security and US4 regressions.
- Shared frontend work can prepare US2 tests after the US1 transport contract
  is fixed.
- Planner-only US5 component work can proceed independently, avoiding shared
  fixture/API files while US1 changes them.

---

## Notes

- No task adds a database migration, token entity, endpoint, package, router,
  account system, email integration, export, availability workflow, polling,
  saved draft, generic Action Center, or parallel lecturer calendar/list.
- The planner calendar DTO must never be returned from a public endpoint.
- Shared components must omit unauthorized controls and data by access
  composition, not CSS hiding.
- Existing migration, concurrency, lifecycle, and misuse tests remain required
  regression gates even when no production file in those areas changes.
- Commit after each task or coherent task group only after relevant
  verification passes.

---

## Phase 9: Convergence

- [X] T049 Add regression tests, then make target-hiding lecturer filter changes transactional so Keep writing restores the prior filters, selection, and draft while Discard applies the requested filter and clears both target drafts in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/pages/LecturerReviewPage.tsx`, and their tests per FR-083 and US3/AC7 (partial)
- [X] T050 Add stale-target and refreshed-scope tests, then announce automatic or authoritative scope loss and move focus to the restricted workspace results heading after clearing the unavailable selection and drafts in `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/pages/LecturerReviewPage.tsx`, and `client/src/pages/LecturerReviewPage.test.tsx` per FR-082 and FR-095 (partial)
- [X] T051 Add partial/unavailable overview tests, then prevent `LecturerReviewManagement` live regions and empty states from announcing numeric zero or definitive no-feedback results when completeness is not confirmed in `client/src/components/LecturerReviewManagement.tsx` and `client/src/components/LecturerReviewManagement.test.tsx` per FR-087 (partial)
- [X] T052 Add prominent-filter intersection tests, then include the Not possible toggle in the identical item-first result/counter scope and in the clear-all action without changing link management in `client/src/components/LecturerReviewManagement.tsx` and `client/src/components/LecturerReviewManagement.test.tsx` per FR-086, FR-089, and US5/AC6 (partial)
- [X] T053 Add public-history presentation tests, then render a safe understandable associated-session identity for every same-link session comment and impossible-session item without exposing planner or out-of-scope schedule fields in `client/src/pages/LecturerReviewPage.tsx` and `client/src/pages/LecturerReviewPage.test.tsx` per FR-025 and US3/AC5 (partial)
- [X] T054 Add restricted-pane allowlist tests, then show the bound revision label, lifecycle state, and course code/title inside the restricted pane, including its narrow full-screen presentation, in `client/src/components/SessionPane.tsx`, `client/src/pages/LecturerReviewPage.tsx`, and `client/src/components/SessionPane.test.tsx` per FR-076 (partial)
- [X] T055 Add historical-edit context tests, then render each planner feedback item's own captured course, session kind/type, date/time, room, cohort, study type, and teaching-unit or exam-duration context instead of relying on the group's first item in `client/src/components/LecturerReviewManagement.tsx` and `client/src/components/LecturerReviewManagement.test.tsx` per FR-092 and US5/AC9 (partial)
- [X] T056 Add adapter truthfulness tests, then replace fabricated planner-only capacity, validity, final-teaching, source, and parsed revision-number placeholders with an access-specific shared presentation shape that preserves planner defaults and component reuse in `client/src/api/calendarWorkspace.ts`, `client/src/components/calendarWorkspaceUtils.ts`, `client/src/components/CalendarPlanningWorkspace.tsx`, `client/src/components/SessionPane.tsx`, and their tests per plan: restricted presentation adapter decision (contradicts)
