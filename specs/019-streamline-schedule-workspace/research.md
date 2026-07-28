# Research: FS-019 Streamlined Schedule Workspace

## Decision 1: Keep `App` as the application navigation owner

**Decision**: Extend `App` with a current Schedule child, Schedule expansion, and the wide navigation pin preference. `App` proposes destination changes, while the mounted `CourseSchedulePage` owns the single pending dirty-transition intent and approves the eventual application commit.

**Rationale**: `App` already owns the single application hierarchy, responsive navigation state, Academic Data category, and destination focus handoff. Adding a second shell owner or router would duplicate established responsibility and risk breaking the mounted Schedule/catalog refresh contract.

**Alternatives considered**:

- Add client routes for Calendar, Versions, and Exams: rejected because the current application has no router and FS-019 does not require URL/history redesign.
- Put Schedule child state inside `CourseSchedulePage`: rejected because primary navigation semantics and top-level Academic transitions are application-shell concerns.
- Add a global state store: rejected because two existing mounted owners can coordinate the bounded state directly.

## Decision 2: Use one Schedule page and three mounted workspace regions

**Decision**: Pass `calendar | versions | exams` into `CourseSchedulePage`. Render the three existing compositions from the page's one loaded state, keep their regions mounted, and hide every inactive wrapper from layout, focus, and accessibility exposure.

**Rationale**: `CourseSchedulePage` already owns semester, course, revision, schedule, lifecycle, exam, busy/error, mutation, and coherent refresh state. Mounted regions provide the cheapest safe restoration of Calendar mode/filters/clean pane and Exam selection without duplicating reads or lifting every child field.

**Alternatives considered**:

- Create three route/page data owners: rejected because duplicated fetch and refresh ownership can show mixed revision state and increases request churn.
- Unmount every inactive workspace: rejected because Calendar restoration is explicit and exam-preparation state would be lost unnecessarily.
- Render three independent page instances: rejected because mutations and shared context would diverge.

## Decision 3: Extract one compact shared context header

**Decision**: Add a controlled `ScheduleContextHeader` that presents semester plus destination-meaningful revision/course context. Keep the full Planning inputs surface only in Calendar and control its visibility independently.

**Rationale**: The same context must remain understandable and editable across all three destinations, while repeating the large Planning inputs column defeats the requested focus. A single header prevents selector behavior from drifting.

**Alternatives considered**:

- Leave selectors only in Calendar: rejected because Versions and Exams would lose direct context and violate FR-009.
- Repeat complete Planning inputs in every destination: rejected because it reproduces the space problem.
- Put context in global browser storage: rejected because same-use mounted state is sufficient and only pin persistence is required.

## Decision 4: Preserve Calendar state by reconciliation, not refresh remount

**Decision**: Remove the `key={workspaceToken}` remount on `CalendarPlanningWorkspaceContent`. Retain the semester key for a genuine semester reset and explicitly reconcile filters, selection, and pane references against refreshed revision data.

**Rationale**: The current workspace token changes after coherent refresh and erases filters, selection, drilldown, and detail even when the semester/revision identity is unchanged. FS-019 requires those values to survive a successful in-place edit.

**Alternatives considered**:

- Lift all Calendar fields immediately into `CourseSchedulePage`: rejected as a much larger refactor than stable mounting plus explicit reconciliation.
- Keep the token key and reconstruct state after every mount: rejected because it creates a second restoration mechanism and can restore stale references.
- Never reset anything: rejected because removed revisions, unavailable filters, and deleted sessions must be reconciled accurately.

## Decision 5: Use one controlled pane for teaching and exam sessions

**Decision**: Add one `SessionPane` whose state is controlled by the Schedule orchestrator. It shows FS-014 detail and composes a teaching or exam editor according to the stable occurrence reference.

**Rationale**: The current teaching path forces List mode and the exam path opens a separate page-level dialog. One pane directly satisfies the placement and preservation requirements while allowing both domain-specific editors to retain their own rules.

**Alternatives considered**:

- Keep teaching in List mode: rejected by FR-012 and FR-017.
- Keep a separate exam dialog: rejected because exam detail and correction must remain in the same pane.
- Create one generic teaching/exam editor or generic backend endpoint: rejected because the payloads, validation, resources, snapshots, and lifecycle rules differ.

## Decision 6: Extract established editor seams rather than duplicate them

**Decision**: Extract the teaching edit view-model mapper and `TeachingSessionEditor` fields from `DraftSchedulePanel`, then reuse them in deliberate List mode and the pane. Adapt `ExamManualSessionEditor` for controlled draft/dirty reporting and pane-friendly composition.

**Rationale**: The current List editor already maps saved sessions, eligible rooms/lecturers, and payload fields. The exam editor already contains exam-specific recommendations and validation. Reuse avoids rule and error-message drift.

**Alternatives considered**:

- Copy editor JSX into the pane: rejected because two active correction paths would diverge.
- Remove List editing: rejected because FS-019 explicitly preserves deliberate List mode.
- Rewrite both editors behind one generic form engine: rejected as unjustified abstraction.

## Decision 7: Centralize dirty transition intent

**Decision**: Derive dirty state by comparing normalized draft and saved baseline. Route every context-replacing action through one `CourseSchedulePage`-owned pending-intent union and one focused Keep editing / Discard changes dialog; `App` never stores a second pending intent.

**Rationale**: Close, another occurrence, Schedule/Academic navigation, and semester/revision/course replacement all threaten the same unsaved draft. One request/commit gate prevents partial coverage and keeps navigation semantics aligned with displayed content.

**Alternatives considered**:

- Scatter `window.confirm` calls: rejected because focus/default-action behavior would vary and be hard to test.
- Maintain an independent dirty boolean: rejected because it can drift from the actual draft.
- Autosave on navigation: rejected because it changes the established explicit-save contract.

## Decision 8: Keep one pane DOM across responsive presentations

**Decision**: Use a deterministic container-aware Calendar/pane layout: above an 820px viewport, dock at a Calendar pane container width of at least 70rem and use the right overlay below 70rem; at or below an 820px viewport, use narrow modal semantics. Do not conditionally render or portal a different pane per breakpoint.

**Rationale**: Available Calendar width changes when navigation or Planning inputs are hidden without a viewport change, so a viewport-only dock rule is insufficient. A single mounted pane preserves draft, errors, selection, and dirty state across presentation changes.

**Alternatives considered**:

- Use only viewport breakpoints: rejected because the 220px navigation and 260-340px inputs materially change available workspace width.
- Render desktop and mobile pane copies: rejected because duplicate DOM creates state, focus, and accessibility divergence.
- Use a modal at every width: rejected because it removes useful Calendar spatial context on wide layouts.

## Decision 9: Separate wide pin preference from temporary navigation state

**Decision**: Store one exception-safe versioned local preference for whether wide navigation is pinned. When unpinned at wide sizes, the labeled opener uses the existing temporary modal-navigation mechanics with backdrop, focus containment, background blocking, Escape/close restoration, and an additional Pin action. Keep narrow navigation open/close transient, omit Pin there, and never overwrite the wide preference at the narrow breakpoint.

**Rationale**: The current responsive effect closes `navigationOpen` on wide layouts, so that value cannot also represent persistent pinning. The spec requires only one same-device preference and no account-level settings.

**Alternatives considered**:

- Persist all navigation and workspace state: rejected because stale identifiers and dirty drafts are unsafe and not required.
- Add a backend user preference: rejected because there is no new identity/settings requirement.
- Use one boolean for pin and narrow drawer: rejected because the meanings conflict during breakpoint changes.

## Decision 10: Reuse all existing HTTP and domain contracts

**Decision**: Continue using the current calendar workspace, draft schedule, exam scheduling, and schedule lifecycle client modules and FastAPI endpoints. Add only an FS-019 UI contract.

**Rationale**: The current APIs already supply every detail and mutation required. The usability problem is ownership, placement, state preservation, and information hierarchy, not missing domain behavior.

**Alternatives considered**:

- Add a composite Schedule workspace endpoint: rejected because the page already coordinates coherent reads and no data is missing.
- Add a generic session mutation endpoint: rejected because teaching and exam contracts intentionally differ.
- Change lifecycle or eligibility rules: rejected as outside scope and prohibited by FR-045/046.

## Decision 11: Make Versions a focused lifecycle composition

**Decision**: Render the existing lifecycle panel and handlers only in Versions and disclose detailed ordered event history on demand.

**Rationale**: FS-013 behavior is complete, but permanent event expansion and grid stretching consume excessive page height. Focused placement and disclosure solve the usability issue without altering lifecycle state.

**Alternatives considered**:

- Summarize or truncate history: rejected because complete ordered history remains required.
- Create a new lifecycle read model: rejected because existing overview data is sufficient.
- Keep lifecycle below Calendar: rejected by the focused-destination requirement.

## Decision 12: Make Exams eligibility-first and keep action context visible

**Decision**: Compose requirements, generation constraints, eligible course selection, unavailable courses, action, confirmation, and result in Exams. Determine selectability from `generationEligibility.eligible`, group eligible courses first, and keep selected count/action outside the scrolling list.

**Rationale**: The current panel interleaves unavailable explanations and considers some ineligible states selectable because it excludes only two status codes. The existing eligibility boolean and reason are the authoritative presentation inputs.

**Alternatives considered**:

- Add a new eligibility calculation: rejected because FS-012 and the backend already own eligibility.
- Hide unavailable courses entirely: rejected because planners need the reason.
- Leave the action after the full list: rejected because FR-037 requires it to remain available.

## Decision 13: Refresh teaching and exam saves coherently

**Decision**: After either correction mutation succeeds, refresh Calendar and affected schedule/exam/lifecycle summaries through the established orchestration. Distinguish a successful mutation followed by refresh failure from a failed mutation.

**Rationale**: Teaching currently calls the broader refresh, but exam correction refreshes only exam overview, which can leave Calendar stale. Reporting a persisted save as failed encourages duplicate actions.

**Alternatives considered**:

- Optimistically patch every local projection: rejected because several summaries and validation states are server-authoritative.
- Refresh only the edited editor: rejected because Calendar and operational summaries must reflect the change.
- Reload the entire application: rejected because it destroys required context.

## Decision 14: Combine automated semantic tests with browser evidence

**Decision**: Use Vitest/jsdom for state, ordering, semantic attributes, dirty requests, reconciliation, focus targets, and API orchestration. Use browser/NVDA checks for actual dock/overlay/full-screen layout, inert behavior, focus containment, 320px, 200% zoom, and long-label reachability.

**Rationale**: jsdom does not perform real layout or prove screen-reader announcements, but most state and accessibility contracts are deterministic and should not rely only on manual testing.

**Alternatives considered**:

- Manual-only verification: rejected because navigation, persistence, dirty gating, and editor behavior are automatable.
- Add a new end-to-end framework: rejected because the project has none and the remaining visual/AT matrix is bounded.

## Baseline findings

- `App.tsx` already owns one application navigation and keeps Schedule mounted while Academic Data is current.
- `ApplicationNavigation.tsx` uses one DOM hierarchy and `max-width: 820px` modal navigation, but Schedule is still a leaf and no pin preference exists.
- `CourseSchedulePage.tsx` is the one schedule orchestrator and currently stacks Planning inputs, Calendar, lifecycle, Exams, feedback, and List content.
- `CalendarPlanningWorkspace.tsx` stores mode/anchor in the outer component, filters/selection in a token-keyed inner component, renders inline detail, forces teaching edit to List, and hands exam edit to a page modal.
- `DraftSchedulePanel.tsx` contains private teaching edit fields and eligible-resource mapping already used by deliberate List editing.
- `ExamManualSessionEditor.tsx` is reusable but its draft is local and it does not report dirty state.
- `ExamGenerationPanel.tsx` interleaves course eligibility and uses an incomplete status-code test instead of the authoritative eligibility boolean.
- Existing client API modules and backend tests cover all required scheduling, lifecycle, calendar, and exam operations.
- React 19.2.7, TypeScript 6.0.2, Vite 8.1.1, Vitest 4.0.16, Python 3.12.8, FastAPI 0.139.0, and pytest 9.1.1 are already present.
- No router, global state library, focus-management package, or client persistence helper exists.
- No technical unknown or `NEEDS CLARIFICATION` remains after research.
