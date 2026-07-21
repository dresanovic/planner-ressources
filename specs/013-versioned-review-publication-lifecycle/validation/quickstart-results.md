# Quickstart results — FS-013

Runtime validation used a disposable SQLite database and the local backend/client on 2026-07-20.

## Browser acceptance evidence

- With no revision, the lifecycle region showed `Start Draft`, no active working revision, no current publication, and disabled scheduled-occurrence controls.
- Starting Draft created revision 1 as the active Draft and enabled working schedule controls.
- Direct publication showed all three seeded courses' remaining-unit conditions as non-blocking and required `Publish explicitly`.
- After publication, revision 1 was the current Published revision, there was no active working revision, and occurrence controls were disabled.
- `Start new revision` created revision 2 with origin revision 1 while revision 1 stayed current.
- Revision 2 moved to Ready for review without an approval field or gate and remained editable.
- Abandon confirmation identified revision 2, Fall 2026, and stated that current publication revision 1 would remain unchanged.
- Abandonment retained revision 2 in history; selecting it exposed `Restore revision`. Restoration returned the same revision identity to Draft and kept revision 1 current.
- Explicit replacement publication made revision 2 current Published, revision 1 Superseded, and left no active working revision. History showed supersession immediately before publication.
- At a 640×800 effective viewport, the named lifecycle region, revision identities, states, action, origin, and complete event history remained reachable and readable. The viewport override was reset after validation.
- Publication and abandon dialogs were exercised with safe initial focus and Escape/cancel behavior; automated tests additionally verify Tab containment, busy-state duplicate prevention, and focus return.

## Defect found and resolved

The first replacement attempt after abandon/restore returned HTTP 500 because both same-transaction events were assigned the same semester event sequence. The event allocator now considers pending events in the SQLAlchemy session. The identical browser flow then succeeded, and a regression test asserts the authoritative replacement outcome and event order.

## Scenarios primarily covered by automation

Stale preparation recovery, direct-API mutation rejection, captured-label immutability after source changes, empty-semester Draft creation, duplicate requests, race integrity, and failed authoritative refresh write-freeze are covered by backend/client automated tests rather than repeated destructive browser manipulation.

## Not claimed

- A literal browser zoom control at 200% was not applied; a narrow effective viewport and automated responsive/accessibility checks were used.
- The full 100-course/500-session/100-exam reference-scale fixture was not run.
- Representative-user usability evidence is tracked separately and has not been fabricated.
