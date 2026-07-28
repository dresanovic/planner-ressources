# Implementation Plan: FS-019 Streamlined Schedule Workspace

**Working Branch**: `master` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/019-streamline-schedule-workspace/spec.md`

**Note**: Planning is being completed on `master` in an existing dirty working tree. Before production files are edited, isolate this customer-facing shell and workflow change on a `codex/019-streamline-schedule-workspace` feature branch or an equivalent clean worktree.

## Summary

Replace the single vertically stacked Schedule page with three focused child workspaces: Calendar, Versions, and Exams. `App` remains the application-navigation owner and gains the current Schedule child plus a guarded, same-device wide-navigation pin preference. `CourseSchedulePage` remains the sole schedule data and mutation orchestrator; it renders the three workspace regions from the same loaded state and keeps them mounted but exposes only the current region. A compact shared context header serves all three destinations, while the complete Planning inputs surface remains independently collapsible in Calendar.

Selecting a teaching or exam occurrence opens one controlled `SessionPane` within the Calendar workspace. The same mounted pane changes presentation through CSS and narrow-screen semantics: docked when space permits, right overlay when constrained, and full-screen modal at the established narrow boundary. The implementation extracts and reuses the established teaching editor fields and adapts the existing exam editor, while all save, validation, lifecycle, snapshot, conflict, capacity, and stale-state behavior continues through the existing APIs. No backend endpoint, schema, database migration, router, global state library, or new runtime dependency is required.

## Technical Context

**Language/Version**: TypeScript 6.0.2 with JSX and React 19.2.7; Python 3.12.8 for unchanged backend regression coverage

**Primary Dependencies**: Existing React 19 and React DOM 19 client built with Vite 8.1.1; existing FastAPI 0.139.0 backend; no new runtime dependency

**Storage**: Existing server-side schedule, lifecycle, and exam storage is unchanged. One exception-safe, versioned `localStorage` boolean stores only the same-device wide-navigation pinned preference; all Schedule workspace and edit state remains mounted client state.

**Testing**: Vitest 4.0.16 with jsdom, TypeScript production build, and ESLint 10.6.0 for client behavior; existing pytest 9.1.1 API/service regression tests for exercised scheduling, lifecycle, calendar, and exam behavior; manual browser and NVDA/Firefox checks for actual layout, focus containment, zoom, and responsive presentation

**Target Platform**: Existing modern-browser planner client on wide and narrow layouts, including 320 CSS pixels and up to 200% text zoom

**Project Type**: Frontend-focused slice within the existing FastAPI/React web application; no backend or HTTP contract change

**Performance Goals**: Schedule-child and pin/visibility changes perform no network mutation and expose the requested already-mounted workspace on the next client render; opening or resizing a pane does not reload its draft; existing schedule refresh behavior remains the only network cost after a mutation

**Constraints**: Preserve FS-012 through FS-014 domain rules and FS-018 Academic Data navigation; Calendar is the default Schedule child; no session selection may force List mode; dirty edits block context replacement; one pane DOM/state must survive presentation changes; wide navigation pin state is the only new persisted value; Calendar context is reconciled rather than blankly reset after same-revision refresh; no router, Redux/global store, new modal/focus package, generic session API, or backend redesign

**Scale/Scope**: One planner role; three Schedule child destinations; teaching and exam occurrence detail/edit flows; one application navigation hierarchy; one shared context header; three adaptive pane presentations; existing semester/course/revision and exam course volumes

**External Acceptance Dependency**: The product owner supplies at least 10 representative planners or designated acceptance reviewers for SC-003 and SC-005. Implementation can finish beforehand, but FS-019 cannot be marked complete until the required usability outcomes are recorded without fabricated participants or results.

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first - PASS**: The clarified FS-019 specification exists with five independently testable stories, 49 functional requirements, explicit accessibility/responsive requirements, scope boundaries, and four recorded product decisions.
- **Acceptance criteria - PASS**: Given/When/Then scenarios cover in-pane teaching and exam correction, focused destinations, shared context, independent left-surface visibility, lifecycle and exam parity, dirty transitions, same-use restoration, persistence, and responsive behavior.
- **Test-first - PASS**: Component, application-shell, page-integration, API regression, and manual accessibility/responsive checks are identified before production work. Visual and assistive-technology checks complement rather than replace automatable behavior.
- **Simplicity and KISS - PASS**: The design extends existing owners, keeps one mounted page orchestrator, extracts only editor/pane seams with multiple immediate uses, and reuses all API modules. It adds no router, state library, backend aggregation layer, or generalized layout framework.
- **Technology fit - PASS**: Production work stays in the existing React/Vite client. Existing FastAPI and JSON contracts remain authoritative and are regression-tested; the changed user-facing behavior is documented in `contracts/schedule-workspace-ui.md`.
- **Delivery workflow - PASS WITH REQUIRED ACTION**: Planning is on `master` with pre-existing and current documentation changes. Implementation must be isolated on `codex/019-streamline-schedule-workspace` or an equivalent clean worktree before production files are changed.
- **Verification before commit - PASS**: Focused tests, complete client checks, targeted and complete backend regression tests, and bounded manual acceptance evidence are listed below and in `quickstart.md`.

### Post-design re-check

Phase 1 introduces no constitution violation. `App` remains the established shell owner, `CourseSchedulePage` remains the established schedule-data owner, and the three destinations reuse one loaded domain state rather than duplicating services. `SessionPane`, `TeachingSessionEditor`, and the small edit-model mapper are justified by the immediate teaching/exam pane requirement and continued deliberate List editing. The only new persisted value is the required navigation preference, guarded locally. The UI contract explicitly leaves all FastAPI operations and domain rules unchanged.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Extend the existing application navigation and mounted Schedule page. Pass a `calendar | versions | exams` destination into `CourseSchedulePage`, place existing Calendar/lifecycle/exam compositions in mutually hidden mounted regions, extract the existing selectors into one context header, and compose the existing teaching/exam edit behavior inside one controlled pane.
2. **Necessary abstractions**: `ScheduleContextHeader` is required for one consistent context surface across three destinations. `SessionPane` is required to compose teaching and exam detail/edit, dirty-transition handling, focus, and three responsive presentations without duplicate DOM. `TeachingSessionEditor` plus a small edit-model mapper is required so Calendar-pane and deliberate List editing use the same established fields and eligible-resource mapping. A focused discard-changes dialog is required because close, selection, destination, and context changes all replace one dirty edit.
3. **Deliberately excluded**: Client routing or URL redesign, global context/store, new persistence service, persisted filters or drafts, separate data owners for each Schedule child, new backend endpoint or composite response, database migration, generic teaching/exam persistence abstraction, generalized modal/focus/layout framework, third-party accessibility package, duplicate desktop/mobile pane DOM, new lifecycle state, new exam eligibility rule, and visual redesign outside the Schedule slice.

Implementation MUST NOT begin until all three answers remain consistent with the approved FS-019 vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/019-streamline-schedule-workspace/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- schedule-workspace-ui.md
|-- checklists/
|   `-- requirements.md
|-- validation/                                   # implementation and acceptance evidence
`-- tasks.md                                      # generated by /speckit-tasks
```

### Source Code (repository root)

```text
client/
|-- src/
|   |-- App.tsx                                  # Schedule destination, guarded navigation, pin preference
|   |-- App.test.tsx                             # shell, persistence, navigation guard, mount regression
|   |-- App.css                                  # shell pinning, focused workspaces, adaptive pane
|   |-- components/
|   |   |-- ApplicationNavigation.tsx            # Schedule hierarchy and wide pin controls
|   |   |-- ApplicationNavigation.test.tsx
|   |   |-- ScheduleContextHeader.tsx            # compact shared semester/revision/course context
|   |   |-- ScheduleContextHeader.test.tsx
|   |   |-- SessionPane.tsx                      # teaching/exam detail/edit and responsive semantics
|   |   |-- SessionPane.test.tsx
|   |   |-- DiscardChangesDialog.tsx             # one safe pending-intent decision surface
|   |   |-- DiscardChangesDialog.test.tsx
|   |   |-- TeachingSessionEditor.tsx            # shared established teaching edit fields
|   |   |-- sessionEditModel.ts                  # draft/list record to teaching edit view model
|   |   |-- CalendarPlanningWorkspace.tsx        # stable calendar state and controlled occurrence selection
|   |   |-- CalendarPlanningWorkspace.test.tsx
|   |   |-- DraftSchedulePanel.tsx               # deliberate List mode reuses teaching editor
|   |   |-- DraftSchedulePanel.test.tsx
|   |   |-- ExamManualSessionEditor.tsx          # pane-compatible controlled draft/dirty callbacks
|   |   |-- ExamManualSessionEditor.test.tsx
|   |   |-- ScheduleLifecyclePanel.tsx            # focused Versions composition/disclosed history
|   |   |-- ScheduleLifecyclePanel.test.tsx
|   |   |-- ExamGenerationPanel.tsx              # eligible/unavailable groups and persistent action context
|   |   |-- ExamGenerationPanel.test.tsx
|   |   |-- ExamRequirementEditor.tsx
|   |   `-- ExamRequirementEditor.test.tsx
|   `-- pages/
|       |-- CourseSchedulePage.tsx                # single data/mutation owner and three workspace regions
|       `-- CourseSchedulePage.test.tsx
`-- package.json                                  # existing commands; no dependency change

backend/
`-- tests/
    |-- api/                                      # unchanged contract regression
    `-- services/                                 # unchanged rule/concurrency regression
```

**Structure Decision**: Use the existing frontend structure and keep application-shell state in `App` and schedule domain orchestration in `CourseSchedulePage`. Add focused view components only where the same behavior is immediately reused or where pane interaction must remain isolated and testable. Existing client API modules and all backend production directories remain unchanged; backend appears only because current contracts and rules are regression-tested.

**Agent Context Update**: No `.specify/scripts/*/update-agent-context` script and no repository `AGENTS.md` are present in this Spec Kit installation. The prescribed updater location was checked after design; no context file is invented or modified.

## Design Decisions

### Navigation ownership and guarded destination changes

- `App` adds `ScheduleDestination = 'calendar' | 'versions' | 'exams'`, keeps Calendar as the default, and extends the one `ApplicationNavigation` hierarchy so Schedule becomes a disclosure parent with the three ordered children.
- Academic Data labels, order, expansion, current-state behavior, and mounted-Schedule catalog refresh remain unchanged from FS-018.
- Application navigation is request/commit based while a session edit is dirty. `App` requests navigation changes but does not own the unsaved-change dialog. `CourseSchedulePage` owns the single pending-intent union and discard decision because it owns the pane baseline and draft. After a clean transition or confirmed discard, it calls an application callback that commits the requested destination. At most one pending intent and one discard dialog can exist, and navigation current semantics change only after commit.
- Re-selecting the current child is a no-op. Navigation-only changes issue no domain mutation.

### Wide pin preference and narrow navigation

- Separate the persisted wide `navigationPinned` preference from the existing temporary `navigationOpen` state. The current narrow media effect must no longer conflate a wide presentation with a closed preference.
- Default to pinned when storage is missing, invalid, or unavailable. Read and write a namespaced/versioned boolean (`resource-planner.navigation.pinned.v1`) inside exception-safe helpers.
- At wide sizes, Unpin removes the 220px shell column and leaves a compact labeled Open navigation control. Opening unpinned navigation presents the same hierarchy as a temporary left modal overlay with a backdrop, contained focus, Escape/close restoration, and background interaction blocking. Unlike narrow navigation, the wide temporary overlay includes Pin navigation; pinning converts it to the persistent column without changing destination or planning context.
- At or below the existing 820px boundary, retain the established modal temporary navigation, omit Pin/Unpin controls, and never overwrite the stored wide preference.

### Shared context and workspace composition

- `CourseSchedulePage` remains the single owner of semester, course, lifecycle revision, all reads, all mutations, busy/error state, and coherent refresh coordination.
- `ScheduleContextHeader` receives controlled values and destination-meaningful controls. Semester is always identified; Calendar includes working/current revision and course context; Versions emphasizes semester and lifecycle revision; Exams emphasizes semester and the course whose requirements are being reviewed.
- Full Planning inputs are rendered only in Calendar and have page-local, nonpersisted visibility. Their toggle is independent of navigation pin/open state.
- Calendar, Versions, and Exams remain mounted below neutral wrapper elements but only the current wrapper is exposed. Use the wrapper's `hidden` state (and `inert` where needed during transitions), never a `hidden` attribute on a class whose authored `display` could override it. This preserves same-use Calendar and exam-preparation state without creating three data owners.

### Calendar state reconciliation

- Keep the Calendar subtree mounted across Schedule-child navigation and retain the existing semester key as a hard reset for a genuine semester change.
- Remove the `key={workspaceToken}` remount of `CalendarPlanningWorkspaceContent`. Same-context refreshes update data without erasing mode, anchor, filters, selection, pane, edit state, or Calendar scroll position.
- Reconcile each retained filter and selected occurrence against the refreshed semester/revision response. Remove unavailable filter facets, close or downgrade an unavailable/noneditable session accurately, and announce recovery rather than displaying mixed data.
- Resolve editable teaching and exam records from the authoritative draft/exam collections using stable `teaching:{id}` and `exam:{id}` occurrence references. Do not change the shared selected course merely to edit an exam.

### One adaptive session pane

- Lift controlled pane state to `CourseSchedulePage`: closed, detail, or editing for one occurrence reference, with origin reference, saved baseline, draft, validation/server feedback, and saving state. Derive dirty by comparing normalized draft to baseline.
- `CalendarPlanningWorkspace` owns projection/mode/filter layout but requests selection and closure through controlled callbacks. The existing occurrence detail becomes `SessionPane` detail content.
- Extract the teaching edit view-model builder and fields from `DraftSchedulePanel`; reuse them in both List and the pane. Adapt `ExamManualSessionEditor` for controlled draft/dirty reporting and pane-friendly composition while retaining create/manual placement use in Exams.
- Keep one pane DOM mounted while open. At a viewport width of 820px or below, the pane uses narrow full-screen modal semantics. Above 820px, a Calendar pane container width of at least 70rem uses the docked right column; a container below 70rem uses the right overlay. These rem-based, container-aware thresholds account for navigation pinning, Planning-input visibility, and text zoom. Do not portal or remount based on presentation.
- Docked and overlay panes are named complementary regions and do not trap focus. Narrow full-screen pane is a named modal dialog, contains focus, prevents interaction with obscured Calendar, and restores origin/result focus on close.

### Dirty intent, saving, and refresh

- `CourseSchedulePage` owns one pending-intent gate covering pane close, selecting another session, requested Schedule or Academic destination changes, and replacement of semester, revision, or course context. `App` only proposes external destinations and commits an approved callback; it never renders a second discard dialog. Pinning navigation, resizing, and hiding Planning inputs do not replace edit context and therefore do not trigger the guard.
- The discard dialog defaults focus to Keep editing. Escape keeps editing. Discard resets to baseline and then commits the queued intent.
- Cancel resets the draft and returns to accurate saved detail. Failed validation or save retains entered values and feedback. A stale response exits edit mode only after authoritative refresh proves the target missing or noneditable.
- Teaching and exam saves both use the established mutation functions and then a coherent refresh that includes Calendar plus affected summaries. A persisted mutation followed by refresh failure is reported as saved with refresh recovery needed, never as if the save itself failed.

### Focused Versions

- Render `ScheduleLifecyclePanel` only through the Versions workspace and preserve every FS-013 designation, transition, confirmation, concurrency, and refresh handler.
- Present active Working and Current Published identities without stretching to match neighboring content. Revision lifecycle events remain ordered but use disclosure or a selected-revision expansion so every event is not permanently open.
- Empty, working-only, published-only, both, stale, rejected, and failure states continue through the existing lifecycle data and dialogs.

### Focused Exams

- Compose exam requirements, manual placement, generation constraints, course eligibility, selection, preparation, result, and confirmation in the Exams workspace using existing state and API handlers.
- Determine selectability from `generationEligibility.eligible`, not from an incomplete list of status codes. Group eligible courses first and unavailable courses second, with the exact reason available per unavailable course.
- Keep selected count, constraints summary, and Prepare exams action outside the internally scrolling course list and keep the action disabled with an explanatory message when selection is empty.
- Preserve selection while Exams is mounted, prune newly ineligible courses after refresh with an announcement, and retain all FS-012 active-exam, recommendation, snapshot, partial-result, confirmation, and stale-state behavior.

### Contract boundary

- No FastAPI endpoint, request/response schema, persistence model, migration, lifecycle transition, exam eligibility rule, or schedule validation rule changes.
- Existing `calendarWorkspace`, `draftSchedule`, `examScheduling`, and `scheduleLifecycle` client modules remain the only HTTP seams.
- `contracts/schedule-workspace-ui.md` supersedes FS-014 and FS-018 only for Schedule hierarchy, focused workspace placement, wide pinning, and teaching/exam in-pane correction.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Write or update the relevant failing test before each production behavior.

Run from the repository root:

```text
python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_exam_scheduling.py backend/tests/api/test_schedule_lifecycle.py
python -m pytest backend/tests/services/test_calendar_workspace.py backend/tests/services/test_draft_schedule_validation.py backend/tests/services/test_exam_scheduling.py backend/tests/services/test_schedule_lifecycle.py backend/tests/services/test_schedule_lifecycle_concurrency.py
python -m pytest backend/tests
```

Run from `client/`:

```text
npm test -- src/components/ApplicationNavigation.test.tsx src/App.test.tsx
npm test -- src/components/ScheduleContextHeader.test.tsx src/components/SessionPane.test.tsx src/components/CalendarPlanningWorkspace.test.tsx
npm test -- src/pages/CourseSchedulePage.test.tsx src/components/DraftSchedulePanel.test.tsx src/components/ExamManualSessionEditor.test.tsx
npm test -- src/components/ScheduleLifecyclePanel.test.tsx src/components/ExamRequirementEditor.test.tsx src/components/ExamGenerationPanel.test.tsx
npm test
npm run lint
npm run build
```

Manual acceptance evidence must cover wide pinned navigation, the wide unpinned temporary modal overlay, independent Planning-input visibility, all three current child destinations, context propagation, clean Calendar/pane restoration, Calendar scroll-position preservation, teaching and exam detail/edit/save/cancel/failure/stale paths, dirty Keep editing/Discard decisions for every replacing intent, deliberate List mode, Versions empty/normal/history/action states, Exams eligible/unavailable/selection/prepare/result states, no stacked inactive workspace, the 70rem docked/overlay container boundary, the 820px full-screen boundary, long labels, 320 CSS pixels, 200% text zoom, keyboard-only operation, focus return/fallback, visible focus, inert obscured content, and NVDA with Firefox announcing navigation hierarchy/current state, pane/dialog purpose, expanded state, errors, and save/reconciliation results. Evidence must record that session edit controls and each Schedule destination are reachable within their respective two-action limits. Record the required representative-planner usability results separately before declaring FS-019 complete.
