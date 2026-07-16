# Quickstart: Validate FS-018 Unified Application Navigation

## Purpose

Use this guide after implementation to prove the shared navigation works end to end without changing Schedule or Academic Data behavior. The canonical behavior is defined in [the UI contract](contracts/application-navigation.md), and permitted client state is defined in [the data model](data-model.md).

## Prerequisites

- Run commands from `client/`.
- Install the repository's locked client dependencies.
- For manual workflow checks, start the existing backend with representative FS-007/FS-008 data and configure the client as described in `client/README.md`.
- Use a browser with developer tools capable of viewport emulation, text zoom, accessibility-tree inspection, keyboard focus inspection, and color-contrast measurement.

## Automated verification

Create or update the relevant failing test before production code, then run:

```text
npm test -- src/components/ApplicationNavigation.test.tsx src/App.test.tsx
npm test -- src/pages/AcademicDataPage.test.tsx src/pages/CourseSchedulePage.test.tsx
npm test
npm run lint
npm run build
```

Expected result: every command exits successfully. The focused tests prove hierarchy/state/accessibility behavior; the complete suite proves existing scheduling and administration regressions remain green.

## Scenario 1: One hierarchy reaches every destination

1. Open the application at a viewport wider than 820px.
2. Confirm Schedule is current and one left sidebar is visible.
3. Confirm the fixed top switcher and Schedule page's Dashboard/Courses/Cohorts/Rooms hash links are absent.
4. Expand Academic Data and inspect its children.
5. Select Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms in order.
6. Return to Schedule.

Expected:

- The child labels and order exactly match the UI contract.
- Academic Data activation changes expansion only and never opens a landing page.
- Each leaf opens the existing workflow; no duplicate or dead primary destination is present.
- Schedule remains mounted across the round trip and reflects catalog revision changes as before.

## Scenario 2: Current location and expansion are unambiguous

1. Start a fresh application use on Schedule.
2. Confirm Academic Data starts collapsed.
3. Expand Academic Data and select Courses.
4. Inspect visual state and the accessibility tree.
5. Attempt to collapse Academic Data while Courses is current.
6. Select Schedule, inspect retained expansion, collapse it, and select Courses again.

Expected:

- Only Schedule is semantically current initially.
- Courses becomes the sole semantic current page; Academic Data is visibly active and reports expanded without becoming current.
- Active parent/current leaf/focus are distinguishable without color alone.
- Collapse is refused while Courses is current.
- Expansion persists on return to Schedule; a selected Academic child always forces expansion.

## Scenario 3: Keyboard and focus behavior

1. Do not use a pointer.
2. Tab into navigation and move forward/backward through every visible control.
3. Activate Academic Data with Enter and Space as supported by the native control.
4. Activate a different child.
5. Re-enter navigation and activate the current child again.

Expected:

- Focus order follows the visible hierarchy and never enters collapsed children.
- Every focused control has a visible indicator distinct from current/active state.
- Selecting a different leaf places focus at the selected content start/heading.
- Re-selecting the current leaf does not reset the page or create an unexpected content focus jump.
- Contrast measurement confirms the focus indicator is at least 3:1 against adjacent colors in inactive, active, and current states.

## Scenario 4: Narrow temporary panel

1. Set the viewport to 820px or narrower.
2. Confirm the persistent sidebar is absent and a labeled navigation trigger is available.
3. Open the panel using the keyboard.
4. Tab forward past the final panel control and backward before the first.
5. Press Escape.
6. Reopen, close with the explicit close control, then reopen and select Rooms.

Expected:

- Only one navigation hierarchy is operable.
- Initial focus enters the named modal panel and Tab/Shift+Tab remain contained.
- Underlying page content cannot be operated while the panel is open.
- Escape and explicit close preserve the destination and restore the opener.
- Selecting Rooms closes the panel, opens the existing Rooms workflow, and focuses content.

## Scenario 5: Responsive and zoom boundaries

1. Open the narrow panel near the 820px boundary, then resize above 820px.
2. Cross the boundary repeatedly with Academic Data expanded and with an Academic child current.
3. Test a viewport width of 320 CSS pixels.
4. Repeat at 200% text zoom.
5. Use long Schedule metadata and Academic Data header controls.

Expected:

- Destination, selected category, and permitted expansion state never reset.
- No stale overlay, background blocking, duplicate navigation, or hidden focus remains after a transition.
- All eight leaves and all page-header controls stay visible or reachable and operable.
- Navigation does not overlap or clip header controls; content reflows within the viewport.

## Scenario 6: Existing workflow regression

1. On Schedule, select planning inputs, switch generation mode, use filters/review mode, and exercise an existing session workflow supported by the current test data.
2. On Academic Data, exercise list/filter/create/edit/lifecycle behavior for a catalog category.
3. Exercise search, edit, availability, and lifecycle behavior for Lecturers or Rooms.
4. Navigate away and back according to the UI contract.

Expected:

- Existing APIs, validation, loading, error, dialog, catalog-revision, and domain-data behavior are unchanged.
- Navigation interactions alone issue no domain mutation and do not reset the current page when its current leaf is re-selected.
- All applicable FS-007 and FS-008 regression scenarios pass.

## Evidence to retain

- Output from the five verification commands.
- Browser/viewport matrix including wide, 820px, 320px, and 200% text zoom.
- Keyboard/focus and accessibility-tree results for Schedule and one Academic child.
- Focus-indicator contrast measurements.
- Screenshots showing the authoritative wide hierarchy and unobstructed headers in wide and narrow states.
- Notes confirming all eight leaves and the existing Schedule/Academic Data workflows were exercised.
