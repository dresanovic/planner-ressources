# Research: FS-018 Unified Application Navigation

## Decision 1: Make `App` the single navigation owner

**Decision**: Move current view, selected Academic Data category, expansion state, narrow-panel state, and content-focus handoff to `App`. Remove navigation ownership from both pages.

**Rationale**: The current fixed switcher is already owned by `App`, while each page owns a competing sidebar. A single application owner directly eliminates those three navigation sources and can preserve the selected child while moving between views.

**Alternatives considered**:

- Keep navigation inside each page and synchronize it through callbacks: rejected because it retains duplicate shells and makes cross-view state coordination indirect.
- Introduce a global state store: rejected because one mounted application component can own four small ephemeral values.
- Add client routing: rejected because URL/deep-link redesign is explicitly outside FS-018.

## Decision 2: Use one focused navigation component and one DOM hierarchy

**Decision**: Add `ApplicationNavigation` to render the shared hierarchy and handle disclosure, current/active semantics, narrow overlay behavior, and local focus management. Render that hierarchy once and change only its presentation responsively.

**Rationale**: Wide and narrow navigation must have identical labels, order, state, and keyboard semantics. A single component and DOM hierarchy prevent divergence and duplicate operable controls while keeping the logic isolated from scheduling/catalog pages.

**Alternatives considered**:

- Duplicate desktop and mobile navigation markup: rejected because hidden copies create semantic/focus risks and two sources for order/state.
- Keep all navigation JSX directly in `App`: viable for static links but rejected because overlay focus containment, resize cleanup, and semantic tests would make `App` responsible for unrelated interaction detail.
- Add a navigation or focus-management package: rejected because the required bounded behavior can be expressed directly with existing platform/React capabilities.

## Decision 3: Keep Academic Data as a controlled disclosure hierarchy

**Decision**: Schedule is the sole top-level leaf; Academic Data is a disclosure-only parent; its seven children are controlled leaf destinations in this exact order: Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, Rooms.

**Rationale**: This implements the clarification without inventing a landing view or default navigation side effect. Passing the selected category into `AcademicDataPage` lets the application navigation be authoritative while preserving the page's existing category-specific loading and editors.

**Alternatives considered**:

- Open Semesters when the parent is activated: rejected by clarification and would combine disclosure with navigation.
- Restore the last child on parent activation: rejected by clarification and creates a hidden navigation side effect.
- Create an Academic Data landing page: rejected as new workflow and content outside the slice.

## Decision 4: Preserve current mount behavior and required state only

**Decision**: Keep Schedule mounted while hidden, as today, and retain the selected Academic Data category/expansion in `App`. Do not add persistence across application sessions and do not broaden FS-018 into preserving every unsaved page form when switching top-level views.

**Rationale**: The existing `App` test relies on Schedule remaining mounted so catalog mutations trigger an in-place refresh. The spec limits navigation data to current view, category, and expansion, and explicitly excludes longer-term preference storage.

**Alternatives considered**:

- Remount Schedule on every return: rejected because it changes established workflow state and breaks the existing refresh contract.
- Keep every page permanently mounted: rejected because it changes Academic Data lifecycle beyond the specified navigation state and adds hidden interactive-content management.
- Persist state in browser storage or backend preferences: rejected as longer-lived persistence outside scope.

## Decision 5: Reuse the existing 820px responsive boundary

**Decision**: Use the existing `max-width: 820px` client boundary for wide sidebar versus narrow temporary panel, then validate the required 320 CSS-pixel and 200% text-zoom cases.

**Rationale**: The current layout already changes its planner/catalog grids at 820px. Reusing that established boundary aligns shell and content transitions, minimizes CSS churn, and gives acceptance tests a deterministic state boundary.

**Alternatives considered**:

- Add a new independent navigation breakpoint: rejected because mismatched shell/content boundaries increase intermediate overlap states.
- Calculate obstruction continuously from element measurements: rejected as unnecessary runtime complexity for a fixed application shell.
- Keep the current narrow stacked sidebar: rejected because the clarified presentation requires a temporary overlay.

## Decision 6: Use direct accessible disclosure and modal-panel behavior

**Decision**: Use native buttons for Schedule, Academic Data disclosure, children, open, and close controls; expose `aria-expanded` on the parent and `aria-current="page"` only on the active leaf. In narrow mode, expose the temporary panel as a named modal region containing the primary navigation, contain focus directly, support Escape, and make underlying content unavailable for interaction.

**Rationale**: Native button semantics supply standard keyboard activation. Explicit expanded/current states and one modal focus boundary satisfy the spec without depending on icon recognition, color, or a third-party interaction layer.

**Alternatives considered**:

- Use a composite tree widget with arrow-key navigation: rejected because the hierarchy is a short disclosure navigation, and adding tree keyboard semantics is unnecessary complexity.
- Use anchors with fragment URLs: rejected because the existing hash links are dead and broader routing is out of scope.
- Hide background visually without disabling interaction: rejected because keyboard and assistive-technology users could escape into covered content.

## Decision 7: Focus a shared content target only after actual destination changes

**Decision**: After a different leaf is chosen, close any temporary panel and focus a shared content target associated with the rendered view. Closing without selection restores the opener. Re-selecting the current leaf performs no state reset or focus jump.

**Rationale**: This gives keyboard users predictable confirmation of location while preserving FR-029 and existing local workflow state.

**Alternatives considered**:

- Leave focus on a navigation item after every selection: rejected because the narrow panel closes and would hide the focused control.
- Focus the document body: rejected because it provides no meaningful destination context.
- Refocus on repeated current selection: rejected because it creates an avoidable context jump and violates the no-op expectation.

## Decision 8: Keep all backend and HTTP contracts unchanged

**Decision**: Implement FS-018 entirely in the client. Document a UI interaction contract, but add no API endpoint, schema, migration, or domain entity.

**Rationale**: Navigation state is ephemeral and the specification explicitly forbids domain-data behavior changes and integrations. All eight views already exist.

**Alternatives considered**:

- Persist navigation preferences through an API: rejected as unnecessary persistence and cross-stack scope expansion.
- Encode navigation in domain/catalog responses: rejected because destination availability is fixed by the implemented application slice, not domain records.

## Decision 9: Verify visual requirements with automated semantics plus browser evidence

**Decision**: Use Vitest/jsdom for state, DOM order, semantic attributes, keyboard event handling, focus placement, and regression behavior. Use browser acceptance checks for actual layout, 3:1 focus-indicator contrast, non-color visual distinctions, zoom/reflow, and header obstruction.

**Rationale**: jsdom can prove interaction and semantics but does not perform layout or render pixels. Combining focused automated tests with a bounded visual matrix covers the specification without adding a browser-automation dependency in this slice.

**Alternatives considered**:

- Rely only on manual testing: rejected because most navigation and accessibility behavior is deterministically automatable.
- Add a new end-to-end testing framework: rejected because the project has no such dependency and the visual remainder is small and explicitly enumerable.

## Baseline findings

- `App.tsx` owns a fixed two-button view switcher and keeps Schedule mounted while hidden.
- `CourseSchedulePage.tsx` owns dead hash links for Dashboard, Courses, Cohorts, Rooms, and Schedule.
- `AcademicDataPage.tsx` owns the seven implemented category buttons and category state.
- `App.css` already uses a 220px two-column shell and changes layout at 820px; the fixed switcher is positioned over the page header area.
- React 19.2.7, TypeScript 6.0.3, Vite 8.1.3, Vitest 4.1.10, and jsdom are installed; no client router, state library, or accessibility interaction library is present.
- The focused baseline suite passed 22 tests across `App`, `AcademicDataPage`, and `CourseSchedulePage` on 2026-07-16.
- No technical unknown or `NEEDS CLARIFICATION` remains after research.
