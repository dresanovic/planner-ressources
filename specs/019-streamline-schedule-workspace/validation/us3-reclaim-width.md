# US3 Reclaimed Width Evidence

**Date**: 2026-07-27  
**Result**: PASS

- Wide navigation defaults to pinned and persists only the valid `resource-planner.navigation.pinned.v1` preference.
- Invalid, unavailable, or throwing storage falls back safely to pinned.
- Unpinned navigation opens as a modal left overlay with backdrop, focus containment, Escape/close restoration, background inert state, and Pin conversion.
- Narrow navigation omits Pin/Unpin while retaining the stored wide preference.
- Planning inputs hide/show independently, remain nonpersisted, and do not alter semester, revision, course, destination, pane, or dirty draft.
- CSS reclaims the navigation column and Planning-input column without remounting the Calendar or pane.
- Navigation/application tests are included in the 21-test focused navigation pass.
- Live Chromium checks confirmed the modal overlay closes on destination selection and the unpinned/hidden-input layout expands the Calendar container enough to use the docked pane presentation.
