# Client Test Evidence

**Date**: 2026-07-28  
**Environment**: Node.js v26.4.0, npm 11.13.0, Vitest 4.1.10  
**Result**: PASS

Exact focused commands from `quickstart.md`:

| Focus | Result | Duration |
|---|---:|---:|
| ApplicationNavigation + App | 2 files, 21 passed | 2.17s |
| Context header + pane + Calendar | 3 files, 29 passed | 2.55s |
| Page + deliberate List + exam placement editor | 3 files, 68 passed | 4.36s |
| Lifecycle + requirement + exam generation | 3 files, 8 passed | 1.93s |

Complete post-review `npm run test`: **41 files, 250 tests passed**, 8.96s.

The corrective accessibility/state matrix covering actionable warning details, single-modal dirty decisions across resize, committed-context focus, and temporary-navigation opener isolation passed **7 files, 91 tests** in 5.15s.

The final focus-timing correction passed **3 files, 45 tests** in 3.91s. Its integration test verifies that Keep editing restores focus only after React removes `inert` from the session pane. A Chromium interaction check confirmed the decision closes, the pane becomes operable, the dirty draft remains, and focus returns inside the editor.

The follow-up review correction matrix passed **3 files, 47 tests** in 4.27s. It covers stale cross-semester refresh suppression, explicit retained-course mismatch labeling, and removal of nonfunctional session-pane actions when editable backing data is unavailable.

The final targeted correction matrix passed **3 files, 49 tests** in 4.57s. It verifies that a mutation resolving after a semester change cannot start a stale shared refresh and that an active edit returns to accurate detail with an explanation when its editable backing model disappears.

The initial preimplementation and one final sandboxed launch could not spawn Vite's helper (`spawn EPERM`). Identical commands passed through the approved project script; these were environment restrictions before test loading, not assertions.

Coverage includes retained deliberate List editing, Academic Data shell/navigation behavior, stable same-context Calendar refresh, pane dirty decisions, lifecycle actions, and exam generation/requirement rules.
