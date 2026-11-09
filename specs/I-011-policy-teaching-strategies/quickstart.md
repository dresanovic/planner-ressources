# I-011 Validation Guide

Future validation only: explicit plan/task approval and human-started Goal 3 required.

## Setup and commands

Use existing Python 3.12 backend virtualenv and Node 24 locks. If absent create backend/.venv, install backend/requirements.txt; npm --prefix client ci. Use temporary databases/policies only, never live plan restore/migration/policy edits. Before code record branch/HEAD/preexisting dirty paths/environment and approved artifact hashes in validation.md. Run concrete [plan verification commands](plan.md#verification-plan), write intended failing tests before each production change and record outcomes. See [contract](contracts/teaching-strategies.md) and [model](data-model.md).

## Story acceptance

1. US1/SC-001–002: each selector actually dispatches for 1 and 20 courses; identity read-only everywhere. Normal different-cwd path and explicit deployment path. Omission → Standard, budget omission →300/1800. Invalid/null/types/unknown/duplicate/malformed/missing/unreadable policy or request overrides reject without save; health still works, German remediation. Pre-Start material edit requires prepare; formatting does not. Change/delete file after Start and verify frozen compute/review/accept and idempotent replay; fresh retry captures new policy. Restart status preserves identity.
2. US2/SC-003: capture Standard deterministic sessions/resources/coverage/objectives/proofs before wrapping; completed results match. Bounded validity/checkpoints preserved without timing-race equality. Exams unchanged; production direct teaching entry points dispatch or reject.
3. US3/SC-004–005: exact 22 LE → seven consecutive feasible ordinary weeks, six 3 plus one 4 anywhere. All spec preference fixtures: staggered cohort [3,3,3,3] cost36 vs [6,6,0,0] cost72; intensive weights [1,2,1] yield cost36 vs40.5. Verify partial/zero-opportunity weeks, fixed teaching/exams, overlap/break accounting, size redistribution, two intensive dates plus another course, additional ordinary/intensive days for coverage, no duplicate LV/date. Inject invalid candidates; reject independently. Failed cross-group repair restores all state.
4. US4/SC-005/010: identical distinct-owner snapshot gives Cohort week2/Lecturer week1; rhythm outranks lecturer smoothing. Derivations 22→11/11,24→8/8/8,23→12/11,22→8/7/7; single/zero shares, explicit precedence, reversed lists/code ties, incompatible shares/unavailable predecessor. Successors wait for predecessor completion and chronological end. Reject transfer/alternation/overallocation independently. Changed code/eligibility/explicit shares stale; policy-only edits do not. Accessible ordered share/blocker facts.
5. US5/SC-006–009: early full/unproven, partial including zero course, repair cap and deadline show separate truthful termination/coverage/proof/save facts. Explicit whole-selection acceptance for nonempty valid review, never heuristic finalize. Whole zero no action. Cancel in enumeration/checks/scoring/repair/finalization; navigation/context loss, invalid/stale/failure before commit save nothing. Compare protected teaching/exams/publications/unrelated rows. Lost-response/cancel races reconcile saved receipt atomically. All selected totals reconcile.

## Runtime and manual evidence

Isolated local app using existing backend/client README startup commands, disposable DATABASE_URL and temporary TEACHING_OPTIMIZATION_POLICY_FILE. Provision normal local logical file in an isolated installation; preserve this installation's live 900/1800. Test isolated compose instance/volume using directory policy mount, including host atomic replacement and missing-file behavior. Operator delivery docs must describe provisioning and mount migration; never use live plan.

Record actual browser keyboard/dialog focus, screen-reader speech/announcements, German/European-date text, narrow viewport and 200% zoom. Automated semantics/focus checks still required; mocks do not prove real speech/layout. Unavailable checks are limitations, not passes.

Run real spawned-worker comparisons: single, cohort competition, shared lecturers across cohorts, intensive, partial-week, near-limit20; identical snapshot hash/budget for all three. Record coverage/weekly measures/remaining LE/elapsed time/termination/proofs and environment/trade-offs. Measure real Start/cancel <=1s/status<=5s, phase cancellation and deadline overshoot; controlled fake-clock tests supplement these, not replace them. No universal improvement claim.

## Finish

Record all concrete plan commands/results and current code/artifact identity in validation.md. Task/checklist markers alone do not prove implementation. Preserve reviewer-owned checklists. Manual writing is Goal5; no commit/push/merge without separate approval.
