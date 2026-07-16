# UI Contract: Unified Application Navigation

This contract defines the user-visible and semantic interface shared by the Schedule and Academic Data views. It adds no HTTP or backend contract.

## Hierarchy contract

The primary navigation exposes one hierarchy in this order:

1. Schedule — leaf destination
2. Academic Data — disclosure-only parent
   1. Semesters — leaf destination
   2. Cohorts — leaf destination
   3. Courses — leaf destination
   4. Study types — leaf destination
   5. Time windows — leaf destination
   6. Lecturers — leaf destination
   7. Rooms — leaf destination

Dashboard, Help & Support, duplicate Schedule links, hash placeholders, and any unimplemented destination are not part of this contract.

All seven Academic Data children are fixed implemented destinations. The navigation contract has no runtime availability flag, child filtering, or fallback destination.

## Control contract

| Control | Role | Activation result | Semantic state |
|---|---|---|---|
| Schedule | Leaf navigation control | Displays existing Schedule content | Current only while Schedule is displayed |
| Academic Data | Disclosure button | Changes expansion only when collapse is permitted | Exposes expanded/collapsed; active-parent styling only while a child is current |
| Academic child | Leaf navigation control | Displays the corresponding existing category | Exactly one child is current while Academic Data content is displayed |
| Open navigation | Narrow-only button | Opens temporary panel | Exposes that it controls/opens navigation with an understandable label |
| Close navigation | Narrow-panel button | Closes panel without changing destination | Understandable close label |

All controls use native keyboard activation. Academic Data activation never chooses a child or opens a landing page.

## Current and active-state contract

- Exactly one leaf exposes semantic current-page state.
- On Schedule, Schedule is current and no Academic child is current.
- On an Academic child, that child is current and Academic Data is visibly active and expanded but is not a second current page.
- Current leaf, active parent, hover, and focus have distinguishable treatments.
- Current and focus communication uses at least one indicator in addition to color; icons and connector lines are supplementary.
- The visible focus indicator reaches at least 3:1 contrast against adjacent colors in every navigation state.

## Expansion contract

- A new application use starts with Schedule current and Academic Data collapsed.
- Selecting an Academic child expands Academic Data and makes collapse unavailable while that child remains current.
- Returning to Schedule retains the most recent permitted expansion state.
- On Schedule, Academic Data may be expanded or collapsed without changing the displayed content or stored category.
- If focus would become hidden by a permitted collapse, focus moves to the Academic Data disclosure.

## Wide presentation contract

- Above the existing 820px boundary, navigation is a persistent left sidebar.
- The sidebar and page content occupy separate shell columns.
- Navigation does not cover the page header, filters, metadata, forms, or scheduling controls.
- No narrow open-navigation control or second navigation copy is operable.

## Narrow presentation contract

- At or below the existing 820px boundary, the sidebar is absent while closed and a consistently placed labeled control opens it as a temporary overlay.
- The overlay contains the exact same hierarchy, labels, order, current leaf, active parent, and expansion state as the wide sidebar.
- While open, the panel has an understandable accessible name, behaves as a modal interaction region, and makes underlying content unavailable for interaction.
- Initial focus enters the panel. Tab and Shift+Tab remain within it.
- Escape and explicit close dismiss it without changing destination and restore focus to the opener.
- Selecting a different leaf dismisses it and moves focus to the selected content start after render.
- Selecting the current leaf dismisses the panel without resetting the page; focus moves only as needed to avoid remaining on hidden panel content.
- Transitioning to wide presentation clears temporary modal state and background blocking while retaining destination, category, and expansion.
- The complete contract remains operable at 320 CSS pixels and up to 200% text zoom.

## Page-content contract

- One application-level content region contains the current view and provides a programmatically focusable start target.
- Schedule remains mounted while hidden so its established client state and catalog-refresh behavior remain intact.
- Academic Data receives the application-selected category and performs the same category-specific loading, cleanup, editing, filtering, and resource behavior as before.
- Switching navigation never creates, updates, deletes, validates, or schedules domain data.
- Re-selecting the current leaf does not remount content, reset filters/forms, or trigger a navigation-induced domain request.
- Existing page headings and header controls remain in document flow and unobstructed at all supported states.

## Failure and boundary contract

- Dashboard, Help & Support, hash placeholders, and any destination outside the confirmed hierarchy are not rendered as operable primary navigation.
- Icons, decorative markers, or connector lines may fail without removing text labels, hierarchy, current state, expansion state, or visible focus.
- Repeated responsive transitions never leave duplicate operable navigation, inert visible content, hidden focus, or a stale overlay.
