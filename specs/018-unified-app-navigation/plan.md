# Implementation Plan: FS-018 Unified Application Navigation

**Working Branch**: `master` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-unified-app-navigation/spec.md`

**Note**: Planning is being completed on `master` in an existing dirty working tree. Create a `codex/` feature branch or otherwise isolate the implementation before production code changes because this is a customer-facing shell change spanning both implemented workflows.

## Summary

Replace the fixed top Schedule/Academic Data switcher and both page-owned sidebars with one application-owned navigation shell. `App` will own the current view, selected Academic Data category, expansion state, narrow-panel state, and destination-focus handoff. A focused `ApplicationNavigation` component will render the same semantic hierarchy as a persistent wide sidebar or temporary narrow overlay, while `CourseSchedulePage` and `AcademicDataPage` retain their existing workflow behavior as content-only views. The change is frontend-only, adds no router or runtime dependency, makes no API or persistence change, and preserves the existing Schedule mount behavior used for in-place catalog refresh.

## Technical Context

**Language/Version**: TypeScript 6.0.3 with JSX; React 19.2.7

**Primary Dependencies**: Existing React 19 and React DOM 19 application built with Vite 8.1.3; no new runtime dependency

**Storage**: N/A for persistent storage; current view, selected category, expansion state, and narrow-panel state remain in mounted client state for the current application use

**Testing**: Vitest 4.1.10 with jsdom for component/page behavior; TypeScript production build and ESLint 10; manual browser checks for layout, zoom, focus visibility, and responsive transitions; NVDA with Firefox on Windows for announced navigation purpose, expanded state, and current destination

**Target Platform**: Existing modern-browser planner client, including the specified 320 CSS-pixel narrow acceptance case and text zoom through 200%

**Project Type**: Frontend slice within an existing FastAPI/React web application; no backend or HTTP contract change

**Performance Goals**: Navigation state changes require no network request and expose the selected mounted view on the next client render; opening, closing, expanding, and collapsing navigation must not introduce a loading state or delay operation of page controls

**Constraints**: Preserve FS-007/FS-008 workflows and all current API behavior; retain Schedule state while it is hidden; keep Academic Data category order exact; Academic Data is disclosure-only; do not add a Dashboard, router, deep-link redesign, state library, focus-management library, icon package, backend work, or persisted preference; use the authoritative navigation image for the wide shell; ensure one operable navigation, semantic current/expanded state, non-color location/focus indicators, contained narrow-panel focus, Escape/close behavior, and unobstructed headers

**Scale/Scope**: One planner role; one Schedule leaf destination plus seven Academic Data leaf destinations; one disclosure parent; two responsive presentations of the same navigation; two existing page workflows; client-only state with no domain-data volume impact

**External Acceptance Dependency**: The product owner supplies at least 10 representative planners or designated acceptance reviewers for SC-003 and SC-004. Automated implementation may finish beforehand, but FS-018 cannot be marked complete until T032 passes. Results must be recorded without fabricated participants or outcomes; reviewer unavailability is a completion blocker.

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The clarified FS-018 specification exists with 4 independently testable user stories, 32 functional requirements, explicit accessibility/responsive requirements, 10 measurable outcomes, bounded exclusions, and 2 recorded product decisions.
- **Acceptance criteria — PASS**: Given/When/Then scenarios cover hierarchy, disclosure behavior, all destinations, active context, keyboard operation, narrow presentation, focus handoff, state persistence, and regression safety.
- **Test-first — PASS**: Component, shell-integration, page-regression, responsive, semantic, and focus tests are identified before production work. Visual browser verification complements rather than replaces automatable checks.
- **Simplicity and KISS — PASS**: The design moves existing navigation ownership to `App`, adds one focused navigation component, and reuses the current 820px responsive boundary and existing React state. No router, state library, new service, backend layer, persistence, or generalized design system is introduced.
- **Technology fit — PASS**: The work stays inside the existing React/Vite client. FastAPI and all JSON HTTP contracts remain unchanged; the user-facing UI contract is documented in `contracts/application-navigation.md`.
- **Delivery workflow — PASS WITH REQUIRED ACTION**: Planning is on `master` with unrelated and pre-existing changes present. Implementation should be isolated on a `codex/` feature branch or equivalent clean worktree before production files are edited.
- **Verification before commit — PASS**: Focused tests, complete client tests, lint, build, and manual responsive/accessibility checks are listed below and in `quickstart.md`.

### Post-design re-check

The Phase 1 design introduces no constitution violation. Navigation has one owner and one rendered hierarchy; the extracted component is justified by the required wide and narrow interaction modes, semantic state, focus containment, and reuse across both views. The controlled Academic Data category removes the duplicate page-local navigation source without introducing routing or persistence. Data modeling remains limited to ephemeral navigation state, the UI contract adds no backend boundary, and all existing domain operations stay inside the existing pages.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Keep the current two-view React application and its existing data APIs. Move shell and navigation state into `App`, render one `ApplicationNavigation`, pass the selected category into `AcademicDataPage`, and remove page-local navigation markup. Use CSS plus small direct focus/event handling for the responsive overlay and keyboard contract.
2. **Necessary abstractions**: One `ApplicationNavigation` component is required because the same exact hierarchy, state, accessibility semantics, and focus behavior must serve Schedule and Academic Data in both wide and narrow states. Its exported Academic Data category type/list is the single source of truth used by the navigation and controlled Academic Data page.
3. **Deliberately excluded**: Client routing, URL/deep-link changes, global state/store, persisted preferences, navigation service, generic shell framework, reusable modal/focus library, new icons or design-system dependency, backend endpoints, telemetry infrastructure, Dashboard behavior, page-content redesign, and changes to Schedule or catalog domain logic.

Implementation MUST NOT begin until these choices remain consistent with the approved FS-018 slice.

## Project Structure

### Documentation (this feature)

```text
specs/018-unified-app-navigation/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- application-navigation.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                      # generated by /speckit-tasks
```

### Source Code (repository root)

```text
client/
|-- src/
|   |-- App.tsx                                  # owns shell and navigation state
|   |-- App.test.tsx                             # cross-view/state/regression coverage
|   |-- App.css                                  # wide shell, narrow overlay, state/focus styles
|   |-- components/
|   |   |-- ApplicationNavigation.tsx            # one hierarchy, disclosure, drawer, focus behavior
|   |   `-- ApplicationNavigation.test.tsx       # hierarchy, semantics, keyboard, responsive behavior
|   `-- pages/
|       |-- AcademicDataPage.tsx                 # controlled category; page-local sidebar removed
|       |-- AcademicDataPage.test.tsx            # existing workflows under controlled category
|       |-- CourseSchedulePage.tsx               # content-only Schedule view; dead sidebar removed
|       `-- CourseSchedulePage.test.tsx           # existing scheduling workflow regression
`-- package.json                                 # existing commands; no dependency change
```

**Structure Decision**: Use the existing frontend structure and make `App` the single application-shell owner. Add only `ApplicationNavigation` under the existing components directory. Keep current page and API modules in place, stripping only shell/navigation markup from the two pages and making Academic Data category selection controlled by the application shell. No backend directory is affected.

**Agent Context Update**: No `.specify/scripts/*/update-agent-context` script and no repository `AGENTS.md` are present in this Spec Kit installation. The prescribed script location was checked after design; no context file is invented or modified.

## Design Decisions

### Application ownership and page lifecycle

- `App` becomes the sole owner of `schedule` versus `academic`, the selected Academic Data category, Academic Data expansion, narrow-panel visibility, and content focus handoff.
- Schedule remains mounted and hidden while Academic Data is active so the current catalog-revision refresh and Schedule working-state behavior remain intact. Academic Data retains the current mount lifecycle across child selections; moving away to Schedule need preserve only the selected category/expansion state required by FS-018, not unsaved domain form state.
- `AcademicDataPage` receives the selected category instead of rendering its own category buttons. A category change performs the same selection/editor/resource cleanup that the current local `selectCategory` action performs before loading the selected existing workflow.
- Re-selecting the current leaf does not update navigation state, refocus content, remount a page, or reset page-local state.

### One hierarchy and active-state semantics

- Render Schedule as the sole top-level content destination and Academic Data as a disclosure button followed by exactly seven child buttons in the specified order.
- Treat all seven confirmed Academic Data children as fixed, implemented destinations; do not introduce a runtime availability flag, filter, or fallback destination.
- Activating Academic Data only changes expansion while Schedule is current. When an Academic Data child is current, Academic Data stays expanded and a collapse request is ignored so parent/child context cannot be hidden.
- Apply semantic current state only to Schedule or the current Academic Data child. The Academic Data parent exposes `aria-expanded` and a distinct active-parent visual treatment, but never a second current-page state.
- Use text, weight/shape or a leading marker, and spacing/hierarchy in addition to color. Use a separate high-contrast focus outline so focus and current location are distinguishable.

### Responsive navigation and focus

- Reuse the existing `max-width: 820px` boundary: above it the single navigation element is a persistent left sidebar; at and below it a labeled trigger opens the same element as a fixed temporary overlay. The acceptance guide additionally verifies 320 CSS pixels and 200% text zoom.
- Keep only one navigation DOM hierarchy rather than separate desktop/mobile copies. CSS changes its presentation, preventing duplicate operable destinations or divergent semantic state.
- When the narrow panel opens, remember the trigger, focus the first meaningful panel control, contain Tab/Shift+Tab within the panel, mark background content unavailable for interaction, and expose dialog/modal naming in addition to the contained primary navigation.
- Escape, explicit close, or leaf selection closes the panel. Cancellation restores the trigger; successful selection focuses the shared current-content target after the destination renders. Crossing to wide state closes temporary-panel mode and leaves a valid focused element.
- A resize listener tied to the same media condition prevents stale open/inert state when crossing the responsive boundary. It is direct component behavior, not a general viewport service.

### Styling and header protection

- Replace `.view-navigation` and the two existing `.sidebar` implementations with the ground-truth shell spacing, a fixed-width wide navigation column, and a content column whose minimum width can shrink without covering header controls.
- Preserve the existing `.workbench`, `.page-header`, catalog, planner, form, and schedule styles except for shell ownership and responsive stacking needed to avoid overlap.
- At narrow widths, the page header and its controls wrap/stack within the content flow; the overlay is absent when closed and blocks background interaction only while intentionally open.

### Tests and regression boundary

- Add failing component tests first for labels/order, disclosure-only behavior, initial/persisted expansion, one current leaf, active parent, semantic state, focus loop, Escape, close, and destination selection.
- Expand `App.test.tsx` before production changes to prove Schedule remains mounted, all eight leaves are reachable, catalog revision still refreshes Schedule, repeated selection is inert, selected category persists, and content focus moves only on an actual destination change.
- Adapt existing page tests to controlled Academic Data category input and verify no local sidebar/dead Schedule links remain while all FS-007/FS-008 operations still pass.
- Use browser checks for focus styling, grayscale/non-color indicators, header overlap, 320px/200% behavior, and repeated 820px boundary transitions that jsdom cannot visually prove.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Run all commands from `client/` after adding the relevant failing test before each production behavior. The focused baseline currently passes 22 tests across `App`, `AcademicDataPage`, and `CourseSchedulePage`.

```text
npm test -- src/components/ApplicationNavigation.test.tsx src/App.test.tsx
npm test -- src/pages/AcademicDataPage.test.tsx src/pages/CourseSchedulePage.test.tsx
npm test
npm run lint
npm run build
```

Manual acceptance evidence must cover the authoritative wide shell, exact label order, all eight leaf destinations, absence of duplicate/dead navigation, active parent/current child distinction without color, visible focus, keyboard-only traversal, NVDA with Firefox on Windows announcing primary-navigation purpose, Academic Data expanded state, and the sole current destination, 3:1 focus-indicator contrast measurement, initial and retained expansion, unchanged current-leaf activation, narrow open/close/Escape/focus containment, focus restoration and destination handoff, background interaction blocking, repeated wide/narrow transitions around 820px, a 320 CSS-pixel viewport, 200% text zoom, long header controls, and unchanged Schedule/Academic Data workflows. Record the completed acceptance matrix under this feature directory before completion.
