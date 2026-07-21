# Quickstart Validation: FS-013 Versioned Review and Publication Lifecycle

## Purpose

Validate the migration, semester lifecycle, immutable snapshots, safe replacement, working-revision guards, abandon/restore, ordered history, stale-state behavior, client accessibility, and reference performance defined by [spec.md](spec.md), [data-model.md](data-model.md), and [the HTTP contract](contracts/schedule-lifecycle.openapi.yaml).

This is a runnable validation guide, not implementation code or a substitute for test-first tasks.

## Prerequisites

- FS-012 is integrated and its migration `0006_conflict_aware_exam_scheduling.py` is the recognized schema head before FS-013.
- Python dependencies from `backend/requirements.txt` are installed.
- Client dependencies are installed in `client/`.
- Use a disposable database for migration, concurrency, and manual validation.
- Set `DATABASE_URL` only to the verified disposable database path; do not point lifecycle validation at planner data that must be retained.
- Backend and client commands are run from the repository locations stated below.

## 1. Artifact and contract review

Confirm before implementation:

1. [spec.md](spec.md) has no unresolved clarification markers.
2. [data-model.md](data-model.md) defines one active working revision, one current publication after first publication, inactive snapshot content, and every permitted transition.
3. [contracts/schedule-lifecycle.openapi.yaml](contracts/schedule-lifecycle.openapi.yaml) defines exactly these FS-013 operation groups:
   - lifecycle/history overview;
   - working-revision creation;
   - selected-revision content;
   - publication preparation;
   - explicit lifecycle transition.
4. [contracts/working-revision-guards.md](contracts/working-revision-guards.md) binds every existing teaching/exam occurrence mutation to its intended `scheduleRevisionId` without versioning planning-input administration.
5. Runtime FastAPI OpenAPI assertions verify path templates, camel-case request/response aliases, lifecycle/action enums, expected revision versions, opaque state/publication tokens, required working-revision identities, and structured 404/409/422 envelopes.
6. No contract introduces course-level publication, approval, authentication, lecturer feedback, automatic publication, external delivery, or field-edit audit.

## 2. Migration validation

Run from the repository root:

```powershell
python -m pytest backend/tests/db/test_migrations.py
```

The migration tests must prove:

- A clean database creates the FS-013 schema and repeated initialization is idempotent.
- An exact FS-012 database upgrades through `0007_versioned_schedule_lifecycle.py`.
- Every semester already containing teaching drafts or exam sessions receives Draft revision 1 and one `created` event.
- A semester without schedule content receives no invented revision history.
- Existing teaching sessions, exam sessions, exam configurations, generation constraints, catalog records, resource data, holidays, and stored snapshot fields retain their domain values.
- Revision-number, row-version, lifecycle-state, one-working, one-current-publication, and event-sequence constraints reject invalid direct writes.
- An unknown partial schema is rejected rather than guessed.
- Downgrade succeeds only when lifecycle history can be represented safely by the prior schema; otherwise it refuses instead of discarding history silently.

## 3. Backend test-first validation

Write the focused tests before production behavior, confirm they fail for the intended missing behavior, then implement the smallest passing change.

Run:

```powershell
python -m pytest backend/tests/services/test_schedule_lifecycle.py backend/tests/services/test_draft_schedule_repository.py backend/tests/services/test_exam_scheduling.py
python -m pytest backend/tests/api/test_schedule_lifecycle.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py backend/tests/api/test_exam_scheduling.py
python -m pytest backend/tests/performance/test_schedule_lifecycle_performance.py
python -m pytest backend/tests
```

Focused service and API coverage must include:

- Initial Draft establishment for empty content and migration-adopted existing content.
- Draft → Ready for review → Draft with the same revision identity and saved content.
- Editing in Ready for review without an automatic state change.
- Direct Draft publication and Ready publication.
- Complete publication preparation for missing units, teaching alerts, enabled-but-unscheduled exams, exam validity issues, and recommendation deviations.
- Explicit publication despite every listed non-blocking condition.
- First publication and replacement publication in one transaction.
- Injected failure between superseding the old revision and publishing the new revision, proving full rollback.
- Published/superseded content unchanged after teaching, exam, course, cohort, study type, lecturer, room, availability, capacity, and label changes.
- Published detail using captured values rather than current catalog joins.
- Starting a successor from current publication while the old publication remains current.
- Abandon and restore of the same revision identity and content.
- Restore rejection while another active working revision exists.
- Superseded and Published restoration/edit rejection.
- Complete stable revision and event ordering across repeated Ready/Draft and abandon/restore cycles.
- Repeated, cancelled, failed, stale, and duplicate actions creating no extra revision or event.
- Course-specific reads retaining the semester publication identity.
- Existing teaching generation/manual mutations and FS-012 exam session mutations rejected without an active working revision, then accepted after successor creation.
- Generation constraints and exam configuration inputs remaining outside the immutable publication while their scheduled results are captured.
- Hard-delete assessment protecting source identities referenced only by inactive snapshots.

## 4. Concurrency and integrity validation

Use a file-backed disposable SQLite database, separate sessions/connections, and coordinated threads. Do not use one shared in-memory session as concurrency evidence.

Validate at least:

1. Two requests create the first working revision simultaneously.
2. A new-revision request races restoration of an abandoned revision.
3. Two requests publish the same prepared working revision.
4. A stale replacement publish races another completed replacement.
5. A teaching or exam edit opened before publication attempts to save after publication.

After each race, assert:

- At most one revision is Draft or Ready for review.
- After the first successful publication, exactly one revision is current Published.
- Supersession never commits without its replacement publication.
- Losing requests return structured conflict/stale results and write no event or partial snapshot.
- Historical snapshots remain byte-for-byte equivalent to their pre-race canonical form.

## 5. Client test-first validation

Run from `client/`:

```powershell
npm run test -- src/api/scheduleLifecycle.test.ts src/components/ScheduleLifecyclePanel.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/components/AbandonRevisionDialog.test.tsx src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx
npm run test
npm run lint
npm run build
```

Client coverage must prove:

- Exact lifecycle URLs, methods, expected versions/tokens, confirmation, aliases, and structured stale overview parsing.
- Current publication and active working revision are always textually distinct.
- Draft and Ready show the correct allowed actions; Ready remains editable.
- Published, superseded, and abandoned views omit teaching and exam edit/delete/generation controls.
- Working and current-publication selection remains semester-wide while course selection filters content only.
- Published and historical rendering uses captured labels even after current catalog fixtures change.
- History uses stable revision order, exact `superseded`-then-`published` replacement-event order, origin, machine-readable offset-bearing timestamps displayed in Europe/Vienna with an explicit timezone indication, and current/working designation.
- Publication confirmation identifies semester, revision, state, first-versus-replacement consequence, prior publication, totals, and every known non-blocking condition.
- Warnings remain visible while the confirmation action remains available.
- Cancel writes nothing and returns focus.
- A stale action closes its dialog, refreshes teaching/exam/lifecycle state together, announces the change, and requires reopening.
- Failed authoritative refresh preserves the last complete display and blocks all schedule writes until retry succeeds.
- Duplicate transition responses do not duplicate visible history.

## 6. End-to-end scenario A — direct first publication

1. Open a semester with saved teaching and exam content but no lifecycle revision and confirm publication and scheduled-occurrence mutations are unavailable.
2. Choose Start Draft and confirm the lifecycle panel names the semester, revision 1, Draft, and Active working revision without changing the saved content.
3. Repeat the initial establishment case for an empty semester and verify it creates an empty Draft.
4. Choose Publish without marking Ready.
5. Review the publication decision context and confirm.
6. Verify revision 1 is current Published with a publication time and no active working revision.
7. Attempt teaching/exam edits through both UI and direct API requests.

Expected:

- Direct Draft publication succeeds.
- Exactly one current publication exists.
- Mutation controls are absent in the Published view.
- Direct stale editor/API attempts are rejected and the snapshot remains unchanged.

## 7. End-to-end scenario B — optional Ready state

1. Start with one Draft revision.
2. Mark it Ready for review.
3. Edit one teaching session and confirm the revision stays Ready.
4. Return it to Draft, then mark it Ready again.
5. Publish it.

Expected:

- Each explicit state action adds exactly one ordered event.
- Schedule edits add no lifecycle event and do not change Ready automatically.
- No approval, feedback, or waiting field appears.
- Publication succeeds from Ready.

## 8. End-to-end scenario C — publish with known conditions

Prepare a working revision containing:

- at least one course with remaining teaching units;
- one non-blocking teaching validation alert;
- one enabled but unscheduled exam;
- one saved exam validity issue;
- one exam outside its recommendation.

Open publication confirmation.

Expected:

- Every substantiated condition appears with the affected course/session context.
- The dialog says the conditions do not prevent planner publication.
- Confirmation remains available.
- Publishing captures the shown conditions and succeeds if the token is still current.
- Changing any material condition before confirmation returns a stale preparation conflict and retains the prior publication.

## 9. End-to-end scenario D — safe replacement publication

1. With revision 1 current Published, choose Start new revision.
2. Verify revision 2 is Draft with origin revision 1 and initially matching content.
3. Edit teaching and exam content in revision 2.
4. Switch between Active working revision and Current publication.
5. Cancel one replacement publication attempt.
6. Prepare again and explicitly publish revision 2.

Expected:

- Revision 1 remains current and unchanged through creation, edits, switching, and cancellation.
- Course filtering never changes the publication identity.
- Completed replacement makes revision 2 current Published and revision 1 superseded in one refreshed outcome.
- Both revision contents remain independently reviewable with captured labels.

## 10. End-to-end scenario E — abandon and restore

1. Start revision 3 from the current publication and make visible changes.
2. Abandon revision 3 after confirming the identified semester/revision and unchanged current publication consequence.
3. Start and abandon a different revision 4.
4. Restore revision 3 when no working revision exists.

Expected:

- The current publication never changes.
- Revisions 3 and 4 remain in history.
- Restoration returns revision 3 itself to Draft with its saved changed content.
- Prior abandon history remains visible and a new restore event is appended.
- Restoration is rejected without data loss if another working revision is active.

## 11. End-to-end scenario F — source-context immutability

1. Publish a revision and record its displayed semester, course, cohort, study type, lecturer, room, capacity, reference codes, teaching alerts, and exam context.
2. Change or deactivate every applicable current catalog/resource record and alter availability/validation inputs.
3. Reopen the Published revision.

Expected:

- The Published view displays the exact captured values and conditions.
- Current changes do not add/remove/rewrite Published issues.
- Starting a successor uses the captured schedule content but subjects later working edits/generation to current planning rules.
- Hard-delete actions do not remove a source identity still required by a restorable inactive snapshot.

## 12. History and on-demand content validation

Create at least 100 revisions containing a mix of Ready/Draft, publication/supersession, and abandon/restore events.

Expected:

- Lifecycle overview returns every revision summary and event in stable documented order.
- The overview does not contain every historical schedule body.
- Selecting one revision loads only that revision's active or captured content.
- Identical schedule bodies still have distinct revision identities.
- No rejected or repeated action creates an extra event.

## 13. Accessibility and usability validation

Keyboard-only review must verify:

- Lifecycle is a named region and states/designations are readable text, not color alone.
- Working/current selection uses native controls or equivalent pressed/selected semantics.
- History is a semantic ordered list; timestamps use machine-readable `<time>` values.
- Publication and abandon confirmations are labelled modal dialogs with descriptive consequences.
- Initial focus lands on a safe control, Tab and Shift+Tab remain contained, Escape cancels only when not busy, and focus returns to the trigger.
- Busy state prevents duplicate confirmation without trapping focus incorrectly.
- Success uses a polite live status; stale/error messages use alerts.
- At 200% zoom and supported narrow widths, revision identity, state, actions, conditions, and dialog controls remain reachable without overlap.

For the specification's user outcomes, record planner acceptance evidence showing:

- Use one moderated test with at least 10 representative planner users and the same prepared-semester script for every participant.
- At least 90%, rounded up to the next whole participant, identify the current publication, active working revision, and latest event within 30 seconds without assistance.
- In the same cohort, at least 90%, rounded up to the next whole participant, complete both direct first publication and safe replacement publication on the first attempt without mistaking working content for the current publication.
- Record the participant profile, shared script, raw completion times, assistance, first-attempt outcomes, working-versus-current mistakes, and threshold calculation.

## 14. Reference performance validation

Run `backend/tests/performance/test_schedule_lifecycle_performance.py` against a deterministic file-backed SQLite fixture containing:

- 100 semester courses;
- 500 teaching sessions;
- 100 exam sessions;
- a separate history case containing 100 revision summaries and their lifecycle events.

After a warm-up operation, record each result separately:

- publication preparation under 2 seconds;
- completed first/replacement publication under 2 seconds;
- successor materialization under 2 seconds;
- current-publication content read under 2 seconds;
- 100-revision history-summary read under 2 seconds.

Also verify read paths use bounded eager/bulk loading and do not perform one query per course/session/revision. Do not report a percentile claim from this deterministic test.

## 15. Final regression and scope check

Before commit, confirm:

- All backend tests pass.
- All client tests, lint, and build pass.
- FS-006 multi-course generation and FS-012 exam workflows behave unchanged inside an active working revision.
- Published-only semesters reject every schedule mutation until the planner starts a working revision.
- Current publication survives every failed, cancelled, stale, abandoned, and unconfirmed action.
- No mandatory approval, lecturer access/feedback collection, authentication, automatic publication, external delivery, course-level publication, field-level audit, or FS-014 workspace redesign was introduced.
