# Schedule Workspace Browser Acceptance

**Date**: 2026-07-27  
**Automated browser**: Codex in-app Chromium runtime  
**Result**: PARTIAL — automated browser scenarios pass; NVDA/Firefox, 200% zoom, and durable screenshot capture remain manual

## Completed evidence

- Calendar, Versions, and Exams are ordered Schedule children; Calendar is default. Each child is reached in two primary-navigation actions while wide navigation is unpinned: open navigation, select child.
- Selecting Versions/Exams closes the wide modal navigation, clears background inert state, and focuses the Schedule content.
- Only the selected workspace is exposed. Exams shows authoritative Eligible/Unavailable groups; Versions shows content-sized lifecycle summaries and collapsed history.
- Teaching editing is exactly two actions from a visible occurrence: select occurrence, choose **Edit session**. Week context remains in place and no List transition occurs.
- Wide constrained Calendar uses a right overlay; after unpinning navigation and hiding Planning inputs, the reclaimed container uses the docked pane at/above 70rem.
- At 820×900 and 320×700 the same pane is a viewport-sized modal dialog. At 320px, Save/Cancel remain reachable, background controls are inert, focus stays inside the pane, and the document has no horizontal overflow.
- Cancel returns to detail. Clean close removes the pane and restores focus to the originating occurrence without scrolling.
- A dirty editor close produced the safe-default **Keep editing / Discard changes** decision while retaining the draft; the complete dirty-intent matrix is additionally covered by component/page/application tests.
- Storage fallback, pin conversion, narrow pin omission, removed selection/filter reconciliation, mutation/refresh failure, stale state, read-only state, List regression, and Academic Data regression are covered by automated tests.

## Bounded manual work still required

The available in-app browser is Chromium and does not provide an NVDA+Firefox session or reliable browser-level 200% text-zoom instrumentation. No compatible durable screenshot capture was retained. Therefore the following portions of T059 are explicitly not claimed:

- NVDA announcements and Firefox accessibility behavior;
- keyboard-only observation under NVDA;
- the full 200% text-zoom/long-label matrix;
- screenshot evidence for every presentation;
- manual numeric Calendar scroll-position recordings for every open/edit/cancel/save/close operation.

These items require a Windows acceptance session using the versions and protocol in `quickstart.md`.
