# US1 Session Pane Evidence

**Date**: 2026-07-27  
**Result**: PASS

- Teaching and exam occurrences resolve through canonical `teaching:{id}` / `exam:{id}` references and open one controlled pane without changing Calendar mode.
- Detail to editing is two intentional actions: select the visible occurrence, then choose **Edit session**.
- Teaching editing reuses the extracted List view model and form; exam editing reuses the established placement payload and validation.
- One page-owned pending intent protects close, selection, semester, revision, course, Schedule-child, and Academic Data changes. Escape and **Keep editing** preserve the draft; **Discard changes** commits exactly one pending action.
- Mutation success is separated from refresh failure, and validation/stale failures retain the draft unless authoritative refresh proves the target unavailable.
- Focused pane/editor/page/application suite: 7 files, 67 tests passed in 4.09s.
- Live Chromium checks confirmed no forced List transition, in-pane Save/Cancel actions, the 320×700 full-screen modal, inert background controls, no horizontal overflow, and origin-occurrence focus restoration.

Calendar is no longer keyed by freshness data, so same-context refresh retains mode, anchor, filters, valid selection, and DOM scroll state. Semester replacement remains the intentional hard reset.
