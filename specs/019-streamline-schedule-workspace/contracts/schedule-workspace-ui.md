# UI Contract: Streamlined Schedule Workspace

This contract defines the user-visible and semantic FS-019 interface. It amends the FS-014 Calendar and FS-018 application-navigation contracts only where stated. It adds no HTTP endpoint, request/response schema, lifecycle rule, exam eligibility rule, or persistence model.

## Primary navigation hierarchy

The primary navigation exposes this hierarchy:

1. Schedule - disclosure parent
   1. Calendar - leaf and default Schedule destination
   2. Versions - leaf
   3. Exams - leaf
2. Academic Data - existing disclosure parent
   1. Semesters
   2. Cohorts
   3. Courses
   4. Study types
   5. Time windows
   6. Lecturers
   7. Rooms

### Hierarchy rules

- Exactly one leaf exposes `aria-current="page"`.
- While Schedule content is current, Schedule remains visibly active and expanded but is not a second current page.
- Academic Data order, labels, disclosure behavior, and current-state rules remain unchanged.
- Activating Schedule as a parent changes disclosure only where permitted; it never creates a mutation or silently chooses a noncurrent child.
- When Schedule is opened without a retained child, Calendar becomes current.
- Selecting the already-current leaf is a no-op for domain and workspace state.
- While a Schedule child is current, Calendar, Versions, and Exams are each reachable through primary navigation in no more than two intentional navigation actions.

## Wide navigation pin contract

| Control/state | Result |
|---|---|
| Pinned wide navigation | Navigation occupies its persistent shell column |
| Unpin navigation | Persistent column leaves layout and main content gains width |
| Open navigation while unpinned | Opens the same hierarchy as a temporary modal left overlay from a compact labeled control |
| Pin navigation | Restores the persistent column without changing destination/context |

- Pin and Unpin are textually understandable, keyboard operable, and visible only where wide pinning is supported.
- The most recent valid wide pin choice is restored on the same device.
- Storage failure or invalid stored data defaults safely to pinned and does not block the application.
- The wide unpinned overlay has a backdrop and understandable modal name, contains focus, makes background content unavailable for interaction, supports Escape and explicit close with opener restoration, and includes Pin navigation.
- Pinning from the wide temporary overlay converts it to the persistent column without changing destination, hierarchy state, or planning context.
- Narrow temporary navigation never exposes a nonfunctional pin control and never overwrites the stored wide choice.
- Pinning/unpinning does not close, save, cancel, or reset a session pane or Planning inputs.

## Schedule workspace exposure

- Calendar, Versions, and Exams share one page/data owner but only the current destination is visible and exposed to focus or assistive technology.
- Complete Versions and Exams content is never permanently stacked after Calendar.
- Switching among children does not issue a domain mutation.
- A clean Calendar selection/pane and Calendar mode, period, filters, and scroll context are restored on return when still valid.
- Hidden workspace content cannot receive keyboard focus or be announced as current content.
- After destination selection, focus moves to the selected workspace heading/start target. A blocked dirty transition does not move focus or current semantics.

## Shared context header

Every Schedule destination starts with a compact shared context header.

| Destination | Required context |
|---|---|
| Calendar | Semester, selected Working/Current Published revision, and applicable course context |
| Versions | Semester and lifecycle/revision context |
| Exams | Semester and the course whose exam requirement is being reviewed, when applicable |

- Controls use the one page-owned context and propagate a committed change consistently to all children.
- A removed semester, revision, or course produces an explicit accurate fallback or recovery choice.
- The compact header remains available when Calendar Planning inputs are hidden.
- The header does not expose a revision or course control with no meaning for its destination.

## Planning inputs contract

- The full Planning inputs surface exists only in Calendar.
- A labeled Hide Planning inputs / Show Planning inputs control changes only that surface.
- Planning-input visibility is independent from primary-navigation pin/open state.
- Hiding or showing inputs preserves destination, context, Calendar view, selected session, and edit draft.
- Planning-input visibility is not required to persist after the mounted application use ends.

## Session selection and detail

- Selecting a teaching or exam occurrence in Week, Day, or Month opens the session pane without switching Calendar mode.
- The pane identifies kind, course, date, time, lecturer/room or exam resources, revision/lifecycle context, and current warnings required by FS-012 through FS-014.
- Selection preserves visible period, filters, semester, revision, Calendar scroll position, and deliberate mode.
- From a visible Week, Day, or Month occurrence, the planner reaches its edit controls in no more than two intentional actions: select the occurrence, then activate Edit session.
- Published or otherwise noneditable sessions provide complete detail and a textual reason editing is unavailable.
- If refreshed data no longer contains the selected occurrence, the pane closes or presents an accurate recovery state and announces the change.

## Session edit contract

| Pane state | Required actions/behavior |
|---|---|
| Teaching detail, editable | Edit session opens the established date/time/lecturer/room fields in the pane |
| Exam detail, editable | Edit session opens the established exam correction fields in the pane |
| Editing | Save and Cancel remain reachable inside the pane |
| Save succeeds | Refresh Calendar and affected summaries, then show current detail/completed status |
| Cancel | Reset draft and return to saved detail without mutation |
| Validation/save fails | Retain draft and show actionable field/server feedback |
| Target becomes missing/noneditable | Leave edit only after authoritative refresh establishes accurate state and explain the result |

- Teaching editing uses the same fields, eligible resources, payload, and validation as deliberate List editing.
- Exam editing uses the existing exam payload, recommendation, override, capacity, snapshot, lifecycle, confirmation, and stale-state rules.
- Neither edit path opens List mode or a separate editor dialog.
- A successful mutation followed by a refresh failure is announced as saved with refresh recovery needed, not as a failed save.
- Deliberate List mode remains available and retains its established behavior.

## Unsaved-change contract

The following intents replace edit context and must use one guard when the draft is dirty:

- close the pane;
- select another occurrence;
- select a different Schedule or Academic Data destination;
- change semester, revision, or course context.

The decision presents:

- **Keep editing**: default/safe action; clears the pending intent and returns to the unchanged draft;
- **Discard changes**: resets the unsaved draft and applies exactly the queued intent.

Escape from the decision is equivalent to Keep editing. Resize, navigation pin/open changes, and Planning-input visibility do not replace edit context and do not open the decision.

## Adaptive pane presentation

One mounted pane and one edit state are used at all sizes.

### Docked

- Above an 820px viewport, when the Calendar pane container is at least 70rem wide, the pane occupies a right column beside Calendar.
- Calendar remains visible and operable.
- The pane is a named complementary region; it is not modal and does not trap focus.

### Right overlay

- Above an 820px viewport, when the Calendar pane container is below 70rem wide, the same pane overlays Calendar from the right.
- Required close/edit/save/cancel controls remain reachable.
- The pane remains a named complementary region; obscured content is not falsely presented as pane content.

### Narrow full-screen

- At an 820px viewport width or below, the same pane becomes a named full-screen modal dialog.
- Focus enters the pane, Tab/Shift+Tab remain within it, and obscured Calendar content is unavailable for interaction.
- Escape closes a clean pane. Escape with dirty changes invokes the unsaved decision.
- Closing restores the originating occurrence when present, otherwise a predictable Calendar results heading/start target.

Crossing the 70rem container boundary or the 820px viewport boundary never remounts the pane or loses selection, draft, validation, error, saving, or dirty state.

## Versions workspace

- Versions shows active Working and Current Published designations when present, with stable identities, lifecycle states, and all FS-013-permitted actions.
- Calendar and complete Exams content are absent from its exposed workspace.
- Complete ordered lifecycle event history is available on demand; every event detail need not remain expanded.
- Empty, working-only, published-only, and working-plus-published states use content-sized surfaces rather than stretching to unrelated workspace height.
- Existing confirmation, stale, rejected, refresh, and failure semantics remain authoritative.

## Exams workspace

- Exams exposes requirements, manual placement where applicable, generation constraints, course eligibility, course selection, preparation/confirmation, and results.
- A course is selectable only when its authoritative `generationEligibility.eligible` value is true.
- Eligible courses appear before a separately labelled unavailable group.
- Every unavailable course retains a specific reason; unavailable courses cannot be selected.
- Selected count, applicable constraints, and Prepare exams action remain outside the internally scrolling course list.
- With no selection, Prepare exams is disabled and nearby text explains the required next action.
- Eligibility refresh removes newly unavailable selections, explains the change, and leaves authoritative data intact.
- Existing active-exam, recommendation, snapshot, capacity, partial-result, confirmation, stale, and per-course success/failure rules remain unchanged.

## Focus and announcement contract

- Every new control uses native keyboard activation and has visible focus distinguishable from current/active state without color alone.
- Opening a pane focuses its heading or first meaningful control.
- Closing a clean pane restores the originating occurrence or a predictable Calendar result fallback.
- Workspace navigation focuses the newly visible workspace start only after a committed destination change.
- Save, cancel, validation failure, stale recovery, disappeared selection, eligibility pruning, and refresh failure are announced in text and through an appropriate status/error mechanism.
- Long labels, 320 CSS pixels, and 200% text zoom do not hide required close, pin, context, edit, save, cancel, lifecycle, or preparation actions.

## Existing HTTP contract boundary

FS-019 continues to use the existing client and server contracts for:

- calendar workspace reads;
- draft teaching-session updates;
- exam planning, requirements, preparation/generation, updates, and deletion;
- schedule lifecycle reads and actions.

No new HTTP operation, schema field, database migration, lifecycle value, validation rule, or independently publishable schedule is part of this contract.
