# Feature Specification: Unified Application Navigation

**Working Branch**: `master`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Create FS-018 so a planner can move consistently between Schedule and Academic Data through one accessible navigation hierarchy, replacing competing sidebars and the overlapping fixed top switcher without changing scheduling or administration workflows."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-16

- Q: How should activating the Academic Data parent behave? → A: Expand or collapse its children only; it does not open a content view.
- Q: What should Academic Data's initial expansion state be when no state has yet been established? → A: Collapsed on Schedule and expanded on any Academic Data child.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navigate Through One Application Hierarchy (Priority: P1)

A planner uses one shared application navigation to move between Schedule and any Academic Data category without encountering duplicate, unavailable, or competing destinations.

**Why this priority**: A single reliable hierarchy is the core user outcome and removes the current ambiguity between the sidebars and fixed top switcher.

**Independent Test**: Starting in Schedule, use only the shared navigation to visit every Academic Data category in the confirmed order and return to Schedule; verify that each selection opens the existing destination and that no second primary navigation model or dead destination is presented.

**Acceptance Scenarios**:

1. **Given** the planner is viewing Schedule at a wide supported viewport, **When** the application view is displayed, **Then** one left sidebar presents Schedule as a top-level destination and Academic Data as the only expandable top-level parent, and no separate fixed Schedule/Academic Data switcher is present.
2. **Given** Academic Data is collapsed, **When** the planner expands it, **Then** Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms appear once, in that order, beneath Academic Data.
3. **Given** Academic Data is expanded or collapsed, **When** the planner activates the Academic Data parent, **Then** only its expansion state changes and no content view opens.
4. **Given** the Academic Data children are visible, **When** the planner selects each child in turn, **Then** the corresponding existing administration view opens without changing its established data or workflow behavior.
5. **Given** an Academic Data category is active, **When** the planner selects Schedule, **Then** the existing Schedule view opens through the same sidebar and no non-working Schedule destination remains elsewhere in the navigation.
6. **Given** a destination is unavailable because its underlying view is not part of the implemented product, **When** the navigation is displayed, **Then** that destination is not presented as an operable navigation choice.

---

### User Story 2 - Understand Current Location (Priority: P2)

A planner can identify the active top-level destination and, within Academic Data, the active category without relying on color alone.

**Why this priority**: Consistent location context prevents disorientation when the planner moves between several visually similar administration views.

**Independent Test**: Open Schedule and every Academic Data category, then verify visually and through semantic state that the correct top-level and child context is exposed at every destination.

**Acceptance Scenarios**:

1. **Given** Schedule is active, **When** the planner inspects the navigation, **Then** Schedule is identified as the current destination by a visible treatment that includes at least one non-color indicator and by a semantic current-state announcement.
2. **Given** Courses is active, **When** the planner inspects the navigation, **Then** Academic Data is visibly identified as the active parent, Courses is visibly identified as the active child, both states include a non-color indicator, and Courses is semantically exposed as current.
3. **Given** an Academic Data child is active, **When** the planner attempts to collapse Academic Data, **Then** the active parent and child context remains visible rather than hiding the current location.
4. **Given** the planner moves from an Academic Data child to Schedule and later returns to Academic Data, **When** the navigation is shown, **Then** the Academic Data expansion state retained from the earlier view is restored and the destination matching the current view is identified.

---

### User Story 3 - Navigate with a Keyboard and Assistive Technology (Priority: P2)

A planner operates the complete hierarchy without a pointer and receives clear focus, expansion, and current-location feedback.

**Why this priority**: The unified navigation is the entry point to all in-scope workflows and must not exclude keyboard or assistive-technology users.

**Independent Test**: With pointer input unavailable, traverse, expand, collapse, activate, and leave the navigation; verify visible focus, logical focus order, standard activation behavior, and announced expanded/current states.

**Acceptance Scenarios**:

1. **Given** keyboard focus enters the navigation, **When** the planner advances and reverses focus, **Then** focus follows the visible hierarchy in a predictable order and every operable destination receives a visible focus indicator distinguishable from its active state.
2. **Given** focus is on Academic Data, **When** the planner activates it using a standard keyboard activation key, **Then** its children expand or collapse as permitted and the changed expanded state is communicated semantically.
3. **Given** focus is on a destination, **When** the planner activates it using the keyboard, **Then** the corresponding view opens and focus is placed predictably at the start of the destination content or its primary heading.
4. **Given** an Academic Data child is current, **When** assistive technology inspects the navigation, **Then** the navigation has an identifiable primary-navigation purpose, the Academic Data expanded state is available, and the current child is announced as current.
5. **Given** focus is visible on an inactive or active navigation item, **When** the item is viewed in any supported interaction state, **Then** focus remains perceivable without requiring color perception and is not obscured by another element.

---

### User Story 4 - Reach Every Destination on a Narrow Screen (Priority: P3)

A planner using a supported narrow viewport opens the same navigation hierarchy from a clearly labeled control and reaches every destination without navigation covering required page controls after selection.

**Why this priority**: Responsive access preserves the unified model where a permanently visible wide sidebar would leave insufficient room for existing page content and controls.

**Independent Test**: At each supported narrow viewport, open the temporary navigation panel, visit Schedule and all seven Academic Data categories with pointer and keyboard input, dismiss the panel by every supported method, and verify that page headers and controls remain usable.

**Acceptance Scenarios**:

1. **Given** the viewport is too narrow to show the wide sidebar and page content together without obstruction, **When** the page is displayed, **Then** a consistently placed, clearly labeled navigation control is available and the sidebar is not displayed over the content until requested.
2. **Given** the planner activates the narrow-screen navigation control, **When** the temporary navigation panel opens, **Then** it exposes Schedule, Academic Data, all seven children in the confirmed order, and the same active, expanded, and current-location context as the wide sidebar.
3. **Given** the temporary navigation panel is open, **When** the planner uses the keyboard, **Then** focus moves into the panel, remains within the panel until it closes, and the panel can be dismissed with Escape without changing destination.
4. **Given** the temporary navigation panel is open, **When** the planner selects a destination, **Then** that destination opens, the panel closes, and focus moves predictably to the destination content.
5. **Given** the temporary navigation panel is open, **When** the planner dismisses it without selecting a destination, **Then** the current view remains unchanged and focus returns to the control that opened it.
6. **Given** the viewport changes between wide and narrow responsive states, **When** the navigation presentation changes, **Then** the current destination, selected Academic Data category, and expansion context are preserved.

### Edge Cases

- The current view is Schedule while Academic Data is expanded. Schedule remains the sole current destination; the expanded children do not imply that an Academic Data child is active.
- The current view is Schedule and no expansion state has yet been established. Academic Data starts collapsed.
- The current view is an Academic Data child while the saved expansion state is collapsed or absent. Academic Data opens automatically so the active parent and child remain visible.
- The current Academic Data category becomes unavailable. The navigation does not show it as active or operable, and the application exposes the nearest valid top-level context without inventing a new destination.
- The viewport crosses repeatedly between wide and narrow states. Only one presentation of the primary navigation is operable at a time, and current, selected, and expanded state do not reset.
- A page title or header contains long content or controls. Navigation never covers, clips, or prevents operation of those controls at any supported viewport.
- The planner opens the narrow-screen panel and then changes viewport size. The resulting navigation remains operable, preserves location context, and does not leave focus trapped in hidden content.
- Focus is on an item that becomes hidden because Academic Data is permissibly collapsed. Focus moves to Academic Data rather than becoming lost.
- The planner selects the destination that is already current. The current view remains stable and no domain data, filters, forms, or unsaved work are reset solely because of the repeated selection.
- Navigation icons, decorative markers, or color styling fail to render. Text labels, hierarchy, current location, expansion state, and focus remain understandable.
- Existing illustrative items in the authoritative image, including mock records, table contents, forms, and Help & Support, do not become required destinations or domain behavior through this slice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST expose one primary application navigation model shared by Schedule and every Academic Data view.
- **FR-002**: At wide supported viewports, the primary navigation MUST appear as a persistent left sidebar that does not cover page content or header controls.
- **FR-003**: Schedule MUST be the sole top-level content destination and Academic Data MUST be the sole expandable top-level parent within this navigation slice.
- **FR-004**: Academic Data MUST be expandable; activating it MUST change only its permitted expansion state and MUST NOT open a content view or choose a child destination; it MUST contain exactly these child destinations in this order: Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms.
- **FR-005**: Each navigation destination MUST open its corresponding existing Schedule or Academic Data view without altering the established workflow or domain-data behavior of that view.
- **FR-006**: The separate fixed Schedule/Academic Data switcher MUST be removed from every in-scope view.
- **FR-007**: Duplicate or non-working Schedule links and any unavailable placeholder destination MUST NOT be presented as operable primary navigation.
- **FR-008**: Exactly one destination matching the displayed view MUST be identified as current at a time.
- **FR-009**: When Schedule is current, Schedule MUST have a visible and semantic current state and no Academic Data child MUST be identified as current.
- **FR-010**: When an Academic Data child is current, Academic Data MUST remain visibly identified as its active parent, the child MUST remain visible and identified as current, and Academic Data MUST be expanded.
- **FR-011**: Active parent, current destination, and keyboard focus MUST each use a perceivable indicator in addition to color, and the focus indicator MUST be visually distinguishable from the active/current indicator.
- **FR-012**: The navigation MUST have a semantically identifiable primary-navigation purpose.
- **FR-013**: Academic Data MUST communicate its expanded or collapsed state semantically whenever it can be expanded or collapsed.
- **FR-014**: The current destination MUST communicate its current state semantically; parent context that is not itself the current page MUST NOT be announced as a second current page.
- **FR-015**: Every navigation control and destination MUST be reachable and operable using a keyboard without requiring pointer input.
- **FR-016**: Keyboard focus MUST follow the visible navigation hierarchy in a predictable sequence, remain visible in every supported state, and never move to a hidden navigation item.
- **FR-017**: After keyboard activation of a different destination, focus MUST move predictably to the start of that destination's content or its primary heading.
- **FR-018**: While an Academic Data child is current, the planner MUST NOT be able to hide the active child context by collapsing its parent.
- **FR-019**: When no expansion state has yet been established, Academic Data MUST start collapsed on Schedule and expanded on any Academic Data child; during the current application use, it MUST retain its most recent permitted expansion state when the planner moves to Schedule and back; opening an Academic Data child MUST override a collapsed or absent state by expanding the parent.
- **FR-020**: At supported narrow viewports where the wide sidebar would obstruct content or controls, the product MUST replace the always-visible presentation with a clearly labeled control that opens the same hierarchy in a temporary navigation panel.
- **FR-021**: Only one presentation of the primary navigation MUST be operable at a time.
- **FR-022**: The narrow-screen panel MUST expose the same labels, order, destination availability, active parent, current child, and expanded state as the wide sidebar.
- **FR-023**: When the narrow-screen panel opens, keyboard focus MUST enter it and remain within it until the panel closes.
- **FR-024**: The narrow-screen panel MUST close when the planner selects a destination, activates its explicit close control, or presses Escape.
- **FR-025**: Closing the narrow-screen panel without selecting a destination MUST preserve the current view and return focus to the control that opened it.
- **FR-026**: Selecting a destination from the narrow-screen panel MUST close the panel and place focus predictably in the selected destination's content.
- **FR-027**: Moving between supported wide and narrow responsive states MUST preserve current view, selected Academic Data category, and permitted expansion state.
- **FR-028**: At every supported viewport and content state, navigation MUST NOT cover, clip, disable, or prevent access to page-header controls.
- **FR-029**: Re-selecting the current destination MUST NOT reset domain data, form contents, filters, or unsaved work solely because the current navigation item was activated again.
- **FR-030**: Navigation actions MUST change only current view, selected Academic Data category, and expansion state; they MUST NOT create, edit, delete, validate, schedule, or otherwise modify academic or scheduling domain data.
- **FR-031**: This feature MUST NOT add Dashboard functionality, new Academic Data categories, scheduling or catalog behavior, calendar-workspace redesign, authentication, integrations, or a broader URL-routing or deep-linking redesign.
- **FR-032**: The hierarchy and shell shown in `docs/designs/resource-planner-unified-navigation-ground-truth.png` MUST govern the in-scope wide navigation, while illustrative content and mock data in that image MUST NOT add requirements.

### Accessibility Requirements

- **AR-001**: All navigation text, current-location indicators, expansion controls, focus indicators, and narrow-screen controls MUST remain perceivable at up to 200% text zoom and at a viewport width equivalent to 320 CSS pixels without loss of destinations or actions.
- **AR-002**: The visible focus indicator MUST have a contrast ratio of at least 3:1 against adjacent colors in inactive, active, expanded, and current states.
- **AR-003**: Navigation labels and semantic states MUST provide an understandable hierarchy without relying on icons, indentation, connector lines, or color alone.
- **AR-004**: The narrow-screen navigation panel MUST expose an understandable name and open/closed state to assistive technology.
- **AR-005**: Opening, closing, expanding, collapsing, and selecting navigation MUST not cause unexpected focus loss or move focus to content hidden from the planner.
- **AR-006**: Motion or visual transition used to reveal navigation MUST not be required to understand location, expansion, or completion of a navigation action.

### Responsive States

- **RS-001 — Wide**: When the left sidebar and current page can coexist without covering or materially constraining required content and header controls, the sidebar remains visible and the page does not require a separate navigation-opening action.
- **RS-002 — Narrow, closed**: When that coexistence is not possible, the sidebar is replaced by a clearly labeled navigation control; the current page remains visible and operable with no navigation overlay present.
- **RS-003 — Narrow, open**: Activating the narrow control opens a temporary panel containing the complete hierarchy above the page, makes the underlying page unavailable for interaction until dismissal, and preserves visible and semantic current-location context.
- **RS-004 — State transition**: Moving among responsive states preserves the current view, selected category, and expansion context, with one operable navigation presentation and valid focus placement.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each user story where automated testing is practical.
- **TR-002**: Automated coverage MUST verify the exact top-level destinations, exact Academic Data child labels and order, successful access to all eight destinations, and absence of the fixed top switcher, duplicate Schedule links, and unavailable placeholders.
- **TR-003**: Automated coverage MUST verify Schedule current state and every Academic Data parent/child active-state combination, including semantic current and expanded states.
- **TR-004**: Automated coverage MUST verify keyboard traversal, expansion, permitted collapse, activation, focus visibility, destination focus placement, and protection against focus entering hidden items.
- **TR-005**: Automated coverage MUST verify the initial collapsed state on Schedule, initial and automatic expansion for an active Academic Data child, expansion persistence when moving to Schedule, and state preservation across wide/narrow transitions.
- **TR-006**: Automated coverage MUST verify narrow-panel opening, contained focus, explicit close, Escape dismissal, selection dismissal, focus restoration, and prevention of interaction with covered page content while open.
- **TR-007**: Verification MUST cover representative supported viewport sizes, text zoom, long header content, and header-control combinations and confirm that all destinations and controls remain unobstructed and operable.
- **TR-008**: Regression coverage MUST verify that established Schedule and Academic Data workflows and their domain data remain unchanged by navigation-only actions.
- **TR-009**: Any exception to automated test-first work MUST document the reason and manual verification path in the implementation plan.

### Key Entities

- **Navigation Destination**: One reachable application location. For this slice, destinations are Schedule plus the seven confirmed Academic Data categories, with a label, hierarchy position, availability, and current-state relationship.
- **Navigation Hierarchy**: The single primary structure containing Schedule as a content destination and Academic Data as a disclosure-only parent with its ordered child destinations.
- **Navigation State**: The non-domain state consisting only of current view, selected Academic Data category, permitted Academic Data expansion state, and current responsive presentation.
- **Responsive Navigation Presentation**: The wide persistent sidebar or narrow temporary panel through which the same hierarchy and state are exposed; only one is operable at a time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance cases, Schedule and all seven Academic Data categories are reachable from the single primary navigation and open the correct existing view.
- **SC-002**: In 100% of inspected in-scope views, no fixed Schedule/Academic Data switcher, duplicate non-working Schedule link, or unavailable placeholder destination is presented as operable navigation.
- **SC-003**: In an unaided usability review with at least 10 representative planners or acceptance reviewers familiar with the product, at least 90% can move from Schedule to a named Academic Data category and back to Schedule on their first attempt without using browser controls or receiving guidance.
- **SC-004**: In the same review, at least 90% of participants can correctly identify their current top-level destination and, for Academic Data, their current child category within five seconds at every tested destination.
- **SC-005**: In 100% of keyboard acceptance paths, a planner can open the navigation when necessary, reach and activate every destination, expand Academic Data, dismiss the narrow panel, and continue into page content without a pointer or focus loss.
- **SC-006**: In 100% of assistive-technology acceptance checks, the primary-navigation purpose, Academic Data expanded state, and single current destination are communicated accurately.
- **SC-007**: At every supported viewport in the acceptance matrix, including a width equivalent to 320 CSS pixels, and at text zoom up to 200%, all eight destinations and all existing page-header controls remain visible or reachable, unobstructed, and operable.
- **SC-008**: In 100% of transitions between supported wide and narrow states, the current view, selected Academic Data category, and permitted expansion context are preserved and exactly one navigation presentation is operable.
- **SC-009**: In 100% of navigation regression cases, selecting, re-selecting, expanding, collapsing, opening, or dismissing navigation causes no academic or scheduling domain-data change and does not reset existing workflow state solely due to navigation interaction.
- **SC-010**: All applicable acceptance scenarios from FS-007 and FS-008 for existing Schedule and Academic Data workflows continue to pass after this feature is delivered.

## Dependencies

- **FS-007 — Academic Planning Data Administration**: Provides the existing Academic Data workflows and the Semesters, Cohorts, Courses, Study types, and Time windows categories preserved by this navigation.
- **FS-008 — Resource Eligibility and Availability**: Provides the existing Lecturers and Rooms administration categories preserved by this navigation.
- No external integration, external service, or new domain-data capability is required.

## Assumptions

- FS-007 and FS-008 provide the implemented Schedule view and all seven named Academic Data category views; FS-018 changes how they are reached, not what they do.
- The planner-only product context remains authoritative; this slice introduces no authentication, role differences, or permission-dependent navigation.
- Academic Data's most recent permitted expansion state persists for the duration of the current application use, including while Schedule is active. Longer-term preference storage is not required.
- Before an expansion state exists in the current application use, Academic Data starts collapsed on Schedule and expanded when an Academic Data child is current.
- An active Academic Data child always forces its parent open because visible parent/child location context takes precedence over a previously collapsed state.
- The exact narrow-screen presentation is a temporary overlay navigation panel opened by a consistently placed, clearly labeled control. The panel closes after destination selection or dismissal and does not introduce a second hierarchy.
- The product's supported viewport and text-zoom acceptance matrix defines the precise points at which wide and narrow states apply; this specification defines required behavior in each state without expanding the browser/device support policy.
- The authoritative image governs navigation hierarchy, relative shell placement, and active-context treatment. Its page content, mock records, forms, statuses, Help & Support item, and decorative details are illustrative unless required elsewhere.
- Existing page titles, filters, create/edit controls, tables, calendars, and forms remain behavioral references and must not be moved, removed, or redesigned beyond what is necessary to keep them unobstructed by navigation.
- Broader URL structure, direct deep-link creation, browser-history redesign, and restoration across a new application session remain outside this slice.
