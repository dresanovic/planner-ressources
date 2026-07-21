# Tasks: FS-013 Versioned Review and Publication Lifecycle

**Input**: Design documents from `/specs/013-versioned-review-publication-lifecycle/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are required by the project constitution and FS-013 test requirements. In every user-story phase, create the listed failing tests before the corresponding production behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified as an independently meaningful increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it uses different files and does not depend on another incomplete task in the same phase.
- **[Story]**: Maps the task to a user story in `spec.md`.
- Every task names the exact repository file or files it changes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Start FS-013 from the completed FS-012 dependency and preserve the approved design boundary.

- [X] T001 Confirm FS-012 and migration `0006_conflict_aware_exam_scheduling.py` are integrated, then create/switch to `codex/fs-013-versioned-publication` as required by `specs/013-versioned-review-publication-lifecycle/plan.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the persisted revision/event foundation and migration path required by every lifecycle story.

**CRITICAL**: No user-story production work begins until this phase is complete.

- [X] T002 Add failing clean-create, exact 0006→0007 upgrade, populated-semester Draft backfill, empty-semester non-backfill, data-preservation, uniqueness/check/index, repeat-initialization, unsupported-partial-schema, and safe-downgrade tests in `backend/tests/db/test_migrations.py`
- [X] T003 [P] Create deterministic semester lifecycle, teaching-session, exam-session, publication-condition, and canonical snapshot fixtures in `backend/tests/schedule_lifecycle_fixtures.py`
- [X] T004 Add `ScheduleRevision` and append-only `ScheduleRevisionEvent` models with state/number/version/snapshot/timestamp constraints, relationships, and partial unique indexes in `backend/app/models/planning.py`
- [X] T005 Implement schema creation, existing-content Draft revision/event backfill, integrity indexes, and preservation-aware downgrade refusal in `backend/app/db/migrations/0007_versioned_schedule_lifecycle.py`
- [X] T006 Extend sequential schema recognition and 0006→0007 initialization while retaining supported earlier upgrade paths in `backend/app/db/schema.py`

**Checkpoint**: FS-013 persistence can be created and upgraded safely, with no lifecycle behavior exposed yet.

---

## Phase 3: User Story 1 — Publish a Stable Semester Schedule (Priority: P1) MVP

**Goal**: Let the planner establish a semester Draft, review authoritative non-blocking publication conditions, publish directly from Draft, and view an immutable current publication that rejects in-place teaching or exam edits.

**Independent Test**: Prepare one semester Draft containing teaching and exam sessions plus known incomplete/non-blocking conditions, publish it directly, change live planning records, and verify one current Published revision retains its captured content while every scheduled-occurrence mutation without an active working revision is rejected.

### Tests for User Story 1 (write and confirm failing first)

- [X] T007 [P] [US1] Add failing service tests for explicit initial Draft establishment from populated and empty saved semester content, canonical snapshot construction, complete non-blocking publication preparation, direct first publication, stable UTC publication time/identity, repeated request handling, stale tokens, and immutable detail reads in `backend/tests/services/test_schedule_lifecycle.py`
- [X] T008 [P] [US1] Add failing API and runtime OpenAPI tests for lifecycle overview, explicit initial Draft creation from populated and empty semesters, selected revision detail, UTC RFC 3339 lifecycle timestamps, publication preparation, explicit publish, aliases, enums, and structured 404/409/422 responses in `backend/tests/api/test_schedule_lifecycle.py`
- [ ] T009 [P] [US1] Add failing file-backed SQLite tests for simultaneous first-Draft creation, simultaneous first publication, duplicate-event prevention, and stale editor save after publication in `backend/tests/services/test_schedule_lifecycle_concurrency.py`
- [X] T010 [P] [US1] Add failing request/response serialization, offset-bearing lifecycle timestamp parsing, state/publication token, preparation-condition, and structured conflict parsing tests in `client/src/api/scheduleLifecycle.test.ts`
- [X] T011 [P] [US1] Add failing explicit Start Draft trigger, Draft/current-publication designation, action visibility, text-state, allowed-action, and named-region tests in `client/src/components/ScheduleLifecyclePanel.test.tsx`
- [X] T012 [P] [US1] Add failing first-publication consequence, complete non-blocking condition display, confirmation/cancellation, busy-state, focus trap, Escape, and focus-return tests in `client/src/components/PublicationConfirmationDialog.test.tsx`
- [X] T013 [P] [US1] Add failing explicit Start Draft orchestration for populated and empty semesters, pre-Draft mutation/publication unavailability, direct-publication, authoritative combined refresh, stale dialog refresh/reopen, failed-refresh write freeze, Published read-only page, and active-revision exam-generation propagation tests in `client/src/pages/CourseSchedulePage.test.tsx` and `client/src/components/ExamGenerationPanel.test.tsx`
- [X] T014 [P] [US1] Add failing dynamic context heading, captured-label rendering, and omission of teaching/exam mutation controls in read-only mode tests in `client/src/components/DraftSchedulePanel.test.tsx`
- [X] T015 [US1] Add failing `scheduleRevisionId` serialization, guard, and published-only rejection coverage to `backend/tests/api/test_draft_schedule.py`, `backend/tests/api/test_multi_course_generation.py`, `backend/tests/api/test_conflict_aware_generation.py`, `backend/tests/api/test_exam_scheduling.py`, `client/src/api/draftSchedule.test.ts`, `client/src/api/multiCourseDraftGeneration.test.ts`, `client/src/api/conflictAwareGeneration.test.ts`, and `client/src/api/examScheduling.test.ts`

### Implementation for User Story 1

- [X] T016 [P] [US1] Define lifecycle states/actions, revision/event/overview/content, canonical snapshot, publication preparation, transition requests, allowed actions, and structured error schemas in `backend/app/schemas/schedule_lifecycle.py`
- [X] T017 [US1] Implement initial Draft establishment, lifecycle overview/history summaries, canonical working snapshot capture, publication-condition aggregation, deterministic state/publication tokens, first publication, inactive revision detail, and `require_active_working_revision` in `backend/app/services/schedule_lifecycle.py`
- [X] T018 [US1] Expose semester lifecycle, working-revision creation, selected-revision detail, publication preparation, and transition endpoints in `backend/app/api/schedule_lifecycle.py`
- [X] T019 [US1] Register the lifecycle router and include lifecycle paths in structured request-validation responses in `backend/app/main.py`
- [X] T020 [P] [US1] Add `scheduleRevisionId` to single-course generation and manual teaching create/edit/delete/clear contracts and enforce the active-working guard in `backend/app/schemas/draft_schedule.py`, `backend/app/api/draft_schedule.py`, and `backend/app/services/draft_schedule_repository.py`
- [X] T021 [P] [US1] Add `scheduleRevisionId` to multi-course and conflict-aware prepare/execute contracts, include it in stale tokens, and enforce the active-working guard in `backend/app/schemas/multi_course_generation.py`, `backend/app/api/multi_course_generation.py`, `backend/app/services/multi_course_generation.py`, `backend/app/schemas/conflict_aware_generation.py`, `backend/app/api/conflict_aware_generation.py`, and `backend/app/services/conflict_aware_generation.py`
- [X] T022 [P] [US1] Add `scheduleRevisionId` to exam generation and manual exam create/edit/delete contracts, include it in material tokens, and enforce the active-working guard in `backend/app/schemas/exam_scheduling.py`, `backend/app/api/exam_scheduling.py`, and `backend/app/services/exam_scheduling.py`
- [X] T023 [P] [US1] Implement typed lifecycle overview/detail/preparation/transition requests and errors, then add `scheduleRevisionId` to every scheduled-occurrence client request in `client/src/api/scheduleLifecycle.ts`, `client/src/api/draftSchedule.ts`, `client/src/api/multiCourseDraftGeneration.ts`, `client/src/api/conflictAwareGeneration.ts`, and `client/src/api/examScheduling.ts`
- [X] T024 [US1] Implement the explicit Start Draft trigger for a semester with no lifecycle revision plus current publication and active working summaries, visible text badges, allowed first-publication actions, semantic status, and loading/error states in `client/src/components/ScheduleLifecyclePanel.tsx`
- [X] T025 [US1] Implement the accessible first-publication prepare/confirm dialog with all server-derived non-blocking conditions in `client/src/components/PublicationConfirmationDialog.tsx`
- [X] T026 [P] [US1] Add explicit working/historical context labels, captured-context rendering, and read-only omission of teaching and exam edit/delete actions in `client/src/components/DraftSchedulePanel.tsx`
- [X] T027 [US1] Load lifecycle with teaching/exam state, orchestrate explicit Start Draft from current saved content including an empty semester, keep publication and scheduled-occurrence mutations unavailable until it succeeds, pass the active `scheduleRevisionId` to every scheduled-occurrence mutation including exam generation, orchestrate direct publication, show immutable Published content, and freeze writes after incomplete authoritative refresh in `client/src/pages/CourseSchedulePage.tsx` and `client/src/components/ExamGenerationPanel.tsx`
- [X] T028 [US1] Add lifecycle card, state/designation, warning list, read-only context, live-status, and publication-dialog styles using existing visual patterns in `client/src/App.css`

**Checkpoint**: User Story 1 is a deployable MVP: one semester Draft can be explicitly published and remains immutable until a later feature increment supplies replacement.

---

## Phase 4: User Story 2 — Revise Without Disturbing the Published Schedule (Priority: P1)

**Goal**: Create a successor Draft from the current publication, keep the old publication visible during edits, and replace it only through one atomic explicit publication.

**Independent Test**: Publish revision 1, start revision 2 from it, edit revision 2 while revision 1 stays current, cancel and stale one replacement attempt, then publish revision 2 and verify revision 1 becomes immutable superseded history only when revision 2 becomes current.

### Tests for User Story 2 (write and confirm failing first)

- [X] T029 [P] [US2] Add failing service tests for successor origin/number allocation, published snapshot materialization, current-publication preservation during working edits, course projection, explicit atomic replacement with immediately ordered `superseded` then `published` events, rollback injection, and superseded immutability in `backend/tests/services/test_schedule_lifecycle.py`
- [X] T030 [P] [US2] Add failing API tests for successor creation, working/current summaries, on-demand content, replacement preparation/consequence, cancelled/stale replacement, and authoritative replacement responses in `backend/tests/api/test_schedule_lifecycle.py`
- [ ] T031 [P] [US2] Add failing file-backed SQLite tests for competing replacement publications, immediate `superseded`-then-`published` event ordering, supersede/publish rollback, and exactly-one-current-publication integrity in `backend/tests/services/test_schedule_lifecycle_concurrency.py`
- [X] T032 [P] [US2] Add failing working/current view selection, current-publication persistence, origin, and superseded-history tests in `client/src/components/ScheduleLifecyclePanel.test.tsx`
- [X] T033 [P] [US2] Add failing replacement consequence, prior-publication identity, cancel, stale-token, and renewed-confirmation tests in `client/src/components/PublicationConfirmationDialog.test.tsx`
- [X] T034 [US2] Add failing successor creation, independent working edits, published/working switching, course-filter projection, cancelled replacement, explicit replacement, and last-complete-view preservation tests in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 2

- [X] T035 [US2] Implement successor creation from the current Published snapshot, source-reference validation, live workspace replacement, origin/number allocation, and atomic supersede/publish with immediately ordered `superseded` then `published` events and single-transaction rollback in `backend/app/services/schedule_lifecycle.py`
- [X] T036 [US2] Return successor/replacement authority, on-demand captured content, and refreshed conflict state through existing lifecycle endpoints in `backend/app/api/schedule_lifecycle.py` and `backend/app/schemas/schedule_lifecycle.py`
- [X] T037 [P] [US2] Add successor creation and selected-revision content helpers plus replacement result typing in `client/src/api/scheduleLifecycle.ts`
- [X] T038 [US2] Add accessible Working/Current publication selection, origin display, and superseded revision selection in `client/src/components/ScheduleLifecyclePanel.tsx`
- [X] T039 [US2] Extend the publication dialog with replacement consequence and prior-current-publication context in `client/src/components/PublicationConfirmationDialog.tsx`
- [X] T040 [US2] Orchestrate successor creation, on-demand historical content, working/published switching, course projection, cancelled/stale replacement, and atomic post-publication refresh in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: User Stories 1 and 2 provide the completion outcome: a current publication stays stable until a successor is explicitly published as its replacement.

---

## Phase 5: User Story 3 — Use an Informative Review-Ready State (Priority: P2)

**Goal**: Let the planner explicitly move the active working revision Draft ↔ Ready for review, continue editing in either state, and publish from either state without approval or feedback gates.

**Independent Test**: Move one working revision Draft → Ready, edit teaching/exam content while it remains Ready, return it to Draft, mark it Ready again, and publish without providing approval or feedback.

### Tests for User Story 3 (write and confirm failing first)

- [X] T041 [P] [US3] Add failing allowed/rejected Draft↔Ready transition, row-version/token, event, content-retention, edit-in-Ready, and publish-from-Ready service tests in `backend/tests/services/test_schedule_lifecycle.py`
- [X] T042 [P] [US3] Add failing mark-ready/return-to-draft transition contract, stale response, and no-approval-field API tests in `backend/tests/api/test_schedule_lifecycle.py`
- [X] T043 [P] [US3] Add failing Ready badge, Mark ready/Return to Draft action matrix, text-state, and edit-authority tests in `client/src/components/ScheduleLifecyclePanel.test.tsx`
- [X] T044 [US3] Add failing Ready round-trip, Ready editing, no automatic state reset, publish-from-Ready, and no approval/feedback gate page tests in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 3

- [X] T045 [US3] Implement compare-and-set Draft→Ready and Ready→Draft transitions, ordered events, stable identity/content, and Ready publication eligibility in `backend/app/services/schedule_lifecycle.py`
- [X] T046 [US3] Add Mark ready/Return to Draft actions, semantic announcements, and Ready edit authority in `client/src/components/ScheduleLifecyclePanel.tsx`
- [X] T047 [US3] Wire Ready/Draft transitions into authoritative refresh while keeping teaching and exam controls editable for the same active revision in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: Ready for review is useful status information without becoming an approval workflow.

---

## Phase 6: User Story 4 — Abandon, Restore, and Inspect Revision History (Priority: P2)

**Goal**: Preserve abandoned work, restore the same revision when no other working revision exists, and expose complete ordered revision/event history without disturbing the current publication.

**Independent Test**: Create and change a successor, abandon it, create and abandon another revision, restore the first revision, and verify the current publication never changes while every revision/event remains ordered and reviewable.

### Tests for User Story 4 (write and confirm failing first)

- [X] T048 [P] [US4] Add failing abandon snapshot, restore same identity/content, competing-working rejection, repeated action, superseded restore rejection, materialization failure rollback, exact replacement-event ordering, and complete ordered history service tests in `backend/tests/services/test_schedule_lifecycle.py`
- [X] T049 [P] [US4] Add failing abandon/restore/history/detail, structured missing-reference, stale state, and authoritative overview API tests in `backend/tests/api/test_schedule_lifecycle.py`
- [ ] T050 [P] [US4] Add failing file-backed SQLite create-versus-restore, restore-versus-restore, and abandon-versus-mutation race tests in `backend/tests/services/test_schedule_lifecycle_concurrency.py`
- [X] T051 [P] [US4] Add failing snapshot-only academic/resource reference protection and deactivation-versus-hard-delete tests in `backend/tests/services/test_academic_catalog.py` and `backend/tests/services/test_resource_catalog.py`
- [X] T052 [P] [US4] Add failing ordered history, lifecycle event, origin/time rendered with machine-readable offset-bearing `<time dateTime>` values and explicit Europe/Vienna interpretation, abandoned Restore action, duplicate-event suppression, and selected historical revision tests in `client/src/components/ScheduleLifecyclePanel.test.tsx`
- [X] T053 [P] [US4] Add failing identified semester/revision consequence, unchanged-publication copy, confirm/cancel, busy, focus trap, Escape, and focus-return tests in `client/src/components/AbandonRevisionDialog.test.tsx`
- [X] T054 [US4] Add failing abandon, start-another, restore-old, restore-conflict, history selection, stale refresh, and current-publication preservation page tests in `client/src/pages/CourseSchedulePage.test.tsx`

### Implementation for User Story 4

- [X] T055 [US4] Implement confirmed abandonment capture, same-revision restoration, live workspace materialization, materialization rollback, stable event sequencing, complete history summaries, and historical detail reads in `backend/app/services/schedule_lifecycle.py`
- [X] T056 [P] [US4] Include source identifiers retained by inactive snapshots in protected-delete/deactivation assessment without joining them for display in `backend/app/services/academic_catalog.py` and `backend/app/services/resource_catalog.py`
- [X] T057 [US4] Expose abandon/restore outcomes and snapshot-materialization conflicts through the existing transition/detail contracts in `backend/app/api/schedule_lifecycle.py` and `backend/app/schemas/schedule_lifecycle.py`
- [X] T058 [P] [US4] Add typed abandon/restore helpers and missing-reference/conflict parsing in `client/src/api/scheduleLifecycle.ts`
- [X] T059 [US4] Add semantic ordered history, event timestamps, origin/current/working designations, historical selection, and conditional Restore actions in `client/src/components/ScheduleLifecyclePanel.tsx`
- [X] T060 [US4] Implement the accessible consequence-aware abandon confirmation in `client/src/components/AbandonRevisionDialog.tsx`
- [X] T061 [US4] Orchestrate abandon/restore dialogs, historical content loading, stale recovery, current-publication preservation, and focus/live announcements in `client/src/pages/CourseSchedulePage.tsx`

**Checkpoint**: All four stories are functional; revision history is complete and abandoned work is recoverable without weakening publication stability.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Prove scale, accessibility, regression safety, and final scope compliance across all stories.

- [ ] T062 Add failing reference-scale and bounded-query tests for preparation, publication, successor materialization, current-publication content, and 100-revision history in `backend/tests/performance/test_schedule_lifecycle_performance.py`
- [ ] T063 Make the smallest eager/bulk loading and canonical serialization changes needed to pass T062 without new dependencies in `backend/app/services/schedule_lifecycle.py`
- [X] T064 Run migration, focused lifecycle, guard-regression, concurrency, full backend, focused client, full client, lint, build, and runtime OpenAPI checks from `specs/013-versioned-review-publication-lifecycle/quickstart.md` and record commands/results in `specs/013-versioned-review-publication-lifecycle/validation/automated-tests.md`
- [ ] T065 [P] Execute direct publication, warning-confirmed publication, safe replacement, abandon/restore, captured-context immutability, history, stale recovery, keyboard, 200%-zoom, and narrow-width scenarios and record evidence in `specs/013-versioned-review-publication-lifecycle/validation/quickstart-results.md`
- [ ] T066 [P] Run one moderated acceptance test with at least 10 representative planner users using the same prepared-semester script; record participant profile, shared script, raw completion times, assistance, first-attempt direct/replacement publication results, working-versus-current mistakes, and the rounded-up 90% threshold calculation in `specs/013-versioned-review-publication-lifecycle/validation/usability-results.md`
- [X] T067 Review the completed diff against the constitution, Simplicity Check, FS-013 scope exclusions, contracts, and all 32 functional requirements, documenting traceability and any justified test exception in `specs/013-versioned-review-publication-lifecycle/validation/final-review.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; confirms the implementation starts after FS-012 on the required feature branch.
- **Foundational (Phase 2)**: Depends on Setup and blocks every user story.
- **User Story 1 (Phase 3)**: Depends on Foundational and establishes the MVP lifecycle, publication, snapshot, and mutation authority used by later stories.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because successor and replacement behavior require a current publication.
- **User Story 3 (Phase 5)**: Its Draft↔Ready transitions can be developed after Foundational, but its full independent acceptance test depends on User Story 1 publication behavior.
- **User Story 4 (Phase 6)**: Its abandon/restore core can be developed after Foundational, but full preservation/history acceptance depends on User Story 1 snapshots and may proceed in parallel with User Stories 2 and 3 after User Story 1.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Completion Order

```text
Setup → Foundation → US1 (MVP publication)
                         ├──→ US2 (successor/replacement)
                         ├──→ US3 (informative Ready state)
                         └──→ US4 (abandon/restore/history)
US2 + US3 + US4 → Polish and final verification
```

### Within Each User Story

- Write and run the phase's failing tests before production changes.
- Complete backend state/snapshot behavior before exposing its endpoint.
- Complete typed client API behavior before UI orchestration.
- Preserve existing row revisions and snapshot tokens in addition to the new `scheduleRevisionId` guard.
- Treat every stale or failed action as no-write and refresh authoritative state before retry.
- Finish the phase checkpoint before calling that story complete.

## Parallel Opportunities

### User Story 1

- T007, T008, T009, T010, T011, T012, T013, and T014 can be written in parallel in separate test files after Foundation.
- T020, T021, and T022 can implement separate teaching, generation, and exam guard families in parallel after T017 provides the guard.
- T023 and T026 can proceed in parallel with backend endpoint work from the approved contracts.

### User Story 2

- T029, T030, T031, T032, and T033 can be written in parallel; T034 owns the shared page test file and integrates their expectations.
- T037 can proceed in parallel with T035; T038 and T039 can then proceed in separate component files.

### User Story 3

- T041, T042, and T043 can be written in parallel before implementation; T044 integrates the journey at page level.
- Backend T045 and component T046 can proceed in parallel before T047 page integration.

### User Story 4

- T048, T049, T050, T051, T052, and T053 can be written in parallel; T054 integrates the full page journey.
- T056 and T058 can proceed in parallel with T055 because they modify separate catalog and client API files; T059 and T060 can then proceed in separate component files.

### Cross-Story Team Strategy

After US1 is complete, US2, US3, and US4 may be implemented concurrently by separate owners, provided shared edits to `backend/app/services/schedule_lifecycle.py`, `client/src/components/ScheduleLifecyclePanel.tsx`, and `client/src/pages/CourseSchedulePage.tsx` are coordinated and merged in story order.

## Parallel Execution Examples

### User Story 1

```text
Task T007: Service publication/snapshot tests in backend/tests/services/test_schedule_lifecycle.py
Task T008: Lifecycle contract/API tests in backend/tests/api/test_schedule_lifecycle.py
Task T010: Client lifecycle API tests in client/src/api/scheduleLifecycle.test.ts
Task T012: Publication dialog tests in client/src/components/PublicationConfirmationDialog.test.tsx
Task T014: Read-only schedule review tests in client/src/components/DraftSchedulePanel.test.tsx
```

### User Story 2

```text
Task T029: Successor/replacement service tests in backend/tests/services/test_schedule_lifecycle.py
Task T030: Successor/replacement API tests in backend/tests/api/test_schedule_lifecycle.py
Task T032: Working/current selector tests in client/src/components/ScheduleLifecyclePanel.test.tsx
Task T033: Replacement confirmation tests in client/src/components/PublicationConfirmationDialog.test.tsx
```

### User Story 3

```text
Task T041: Draft/Ready service tests in backend/tests/services/test_schedule_lifecycle.py
Task T042: Draft/Ready API tests in backend/tests/api/test_schedule_lifecycle.py
Task T043: Ready action-matrix tests in client/src/components/ScheduleLifecyclePanel.test.tsx
```

### User Story 4

```text
Task T048: Abandon/restore/history service tests in backend/tests/services/test_schedule_lifecycle.py
Task T049: Abandon/restore API tests in backend/tests/api/test_schedule_lifecycle.py
Task T051: Historical reference-protection tests in backend/tests/services/test_academic_catalog.py and backend/tests/services/test_resource_catalog.py
Task T053: Abandon dialog accessibility tests in client/src/components/AbandonRevisionDialog.test.tsx
```

## Implementation Strategy

### MVP First — User Story 1

1. Complete Setup and Foundation.
2. Write all US1 tests and confirm the intended failures.
3. Implement initial Draft identity, immutable first publication, server-prepared non-blocking confirmation, read-only Published display, and working-revision mutation guards.
4. Run the US1 service, API, concurrency, client API, component, page, and FS-006/FS-012 guard-regression tests.
5. Stop and demonstrate direct publication independently before successor, Ready, or abandon/restore behavior.

### Incremental Delivery

1. **US1**: Deliver deliberate stable first publication.
2. **US2**: Add safe successor editing and explicit replacement publication.
3. **US3**: Add optional informative Ready for review transitions.
4. **US4**: Add reversible abandonment and complete lifecycle history.
5. **Polish**: Prove reference scale, accessibility, usability thresholds, regression safety, and scope compliance.

## Notes

- `[P]` tasks use separate files or independent contract surfaces; coordinate tasks that converge on shared lifecycle service, panel, or page files.
- Semester `revisionNumber`, lifecycle `revisionVersion`, per-course `DraftSchedule.revision`, and `ExamSession.revision` are distinct values and must remain distinctly named in tests, schemas, and UI.
- Published and historical views use captured snapshot values and never current-catalog enrichment.
- Generation constraints and exam configurations remain current planning inputs; only scheduled teaching/exam occurrences are lifecycle-guarded and published.
- No task may add authentication, approvals, lecturer feedback, external/automatic publication, course-level publication, revision diffs, field-level audit, generic workflow infrastructure, or FS-014 workspace redesign.
- Commit after each task or coherent test-first group, and do not mark a phase complete without its independent test checkpoint.
