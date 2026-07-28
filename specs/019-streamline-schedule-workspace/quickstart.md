# Quickstart: Validate FS-019 Streamlined Schedule Workspace

## Purpose

Use this guide after implementation to prove Schedule is split into focused workspaces, teaching and exam correction remains in one adaptive pane, and all prior domain behavior is unchanged. The canonical interaction behavior is in [the UI contract](contracts/schedule-workspace-ui.md), and permitted state/persistence is in [the data model](data-model.md).

## Prerequisites

- Install the repository's locked backend and client dependencies.
- For manual checks, start the existing FastAPI backend with representative FS-012 through FS-014 data and configure the client as documented in `client/README.md`.
- Include semesters with no revision, Working only, Current Published only, and both; teaching and exam sessions; eligible and unavailable exam courses; lifecycle history; and a stale-action fixture.
- Use a browser with viewport, zoom, accessibility-tree, keyboard focus, container-size, and contrast inspection.
- Use NVDA with Firefox on Windows for assistive-technology acceptance and record both product versions.

## Test-first sequence

Before each production behavior, add or update the focused failing test:

1. Application navigation hierarchy, pin persistence, and dirty request/commit.
2. Focused workspace composition and shared context.
3. Stable Calendar refresh/reconciliation.
4. Teaching/exam pane detail, edit, dirty decision, and focus.
5. Versions disclosure/action parity.
6. Exams grouping, selection/action context, and result parity.

Any exception must record why automation is impractical and the exact manual evidence that replaces it.

## Automated backend regression

Run from the repository root:

```text
python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_exam_scheduling.py backend/tests/api/test_schedule_lifecycle.py
python -m pytest backend/tests/services/test_calendar_workspace.py backend/tests/services/test_draft_schedule_validation.py backend/tests/services/test_exam_scheduling.py backend/tests/services/test_schedule_lifecycle.py backend/tests/services/test_schedule_lifecycle_concurrency.py
python -m pytest backend/tests
```

Expected: every command exits successfully. These are regression checks only; FS-019 adds no backend behavior.

## Automated client verification

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

Expected: every command exits successfully. Focused tests prove the changed contract; the complete suite proves Schedule and Academic Data regressions remain green.

## Scenario 1: Focused navigation and shared context

1. Start a fresh application use wider than 820px.
2. Expand Schedule and inspect its children.
3. Open Calendar, Versions, and Exams in order.
4. Change semester and each destination-meaningful revision/course control.
5. Open Academic Data and visit one existing child.

Expected:

- Calendar is the default and the three Schedule children have the required order.
- While Schedule is current, each Schedule destination is reachable through primary navigation in no more than two intentional actions; record the action count for each.
- Exactly one leaf is current; Schedule is active/expanded without becoming a second current leaf.
- Only the selected Schedule workspace is exposed; complete Versions and Exams are absent below Calendar.
- The compact context header remains present and committed context is consistent across children.
- Navigation alone creates no schedule or academic mutation.
- Academic Data hierarchy and behavior are unchanged.

## Scenario 2: Pin navigation and hide Planning inputs independently

1. On a wide Calendar, note the current semester, revision, mode, filters, and pane state.
2. Unpin primary navigation and reopen it.
3. Verify the reopened navigation is a temporary modal left overlay, then Pin it again.
4. Hide and show full Planning inputs.
5. Leave navigation unpinned, reload the application, and then cross to narrow and back to wide.

Expected:

- Unpinning reclaims the persistent shell width and leaves a labeled opener.
- Reopening wide unpinned navigation shows a backdrop, contains focus, makes background content unavailable, supports Escape/close restoration, and includes Pin navigation.
- Pinning restores the shell without changing Schedule context.
- Planning-input visibility changes only the Calendar inputs surface.
- The compact context header remains available.
- The valid wide pin preference restores on the same device, survives narrow presentation, and narrow navigation never exposes Pin/Unpin.
- Storage disabled, throwing, or containing an invalid value falls back to pinned without breaking navigation.

## Scenario 3: Teaching detail and correction in place

1. Open an editable Working revision in Week mode, apply at least two filters, and record the Calendar scroll position.
2. Select a teaching occurrence and inspect every detail/warning.
3. Choose Edit session, change a valid field, and save.
4. Repeat and cancel.
5. Repeat with invalid data and with a stale/noneditable fixture.

Expected:

- The pane opens without switching to List or changing period, filters, semester, or revision.
- Edit controls are reached in exactly two intentional actions from the visible occurrence.
- Opening, editing, cancelling, saving, and closing preserve the active Calendar scroll position unless the edited item legitimately leaves the visible result.
- Valid save refreshes the Calendar item and summaries, returns to current detail, and retains Calendar context.
- Cancel leaves saved data unchanged.
- Validation/save failure keeps the entered draft and actionable feedback.
- A persisted save followed by refresh failure is identified as saved with recovery required.
- A stale target stays editable with its draft unless authoritative refresh proves it missing or noneditable.

## Scenario 4: Exam detail and correction in the same pane

1. Select an editable exam occurrence from Week, Day, or Month.
2. Inspect exam detail, recommendation, capacity, revision/lifecycle, and warnings.
3. Edit valid values and complete any established confirmation.
4. Exercise invalid, partial/stale, and Published read-only states.

Expected:

- Exam correction replaces/extends detail in the same pane; no separate page editor appears.
- Shared course context is not silently changed merely to edit the selected exam.
- Save uses existing recommendation, override, capacity, snapshot, validation, and lifecycle rules.
- Calendar and exam summaries refresh coherently.
- Published detail is complete and provides a textual reason editing is unavailable.

## Scenario 5: Unsaved-change protection

With a dirty teaching or exam draft, attempt each action:

1. Close the pane.
2. Select another occurrence.
3. Open Versions or Exams.
4. Open an Academic Data child.
5. Change semester, revision, and course.

For each action, test Keep editing, Escape, and Discard changes.

Expected:

- Current navigation/context does not change before a decision commits.
- Keep editing and Escape return to the exact draft and focus context.
- Discard resets only unsaved draft state and then performs exactly the requested action.
- Resizing, pinning/unpinning navigation, and hiding/showing Planning inputs never prompt and never lose the draft.

## Scenario 6: Clean Calendar restoration and reconciliation

1. In each Calendar mode, set period/anchor, filters, and a nonzero Calendar scroll position, then open a clean session pane.
2. Visit Versions and Exams and return.
3. Trigger a same-revision refresh.
4. Repeat after removing the selected session, a filter option, or the selected revision in the fixture.

Expected:

- Valid mode, period, filters, scroll position, selection, and clean pane reopen on return.
- A same-context refresh does not reset Calendar because a freshness token changed.
- Removed references are cleared or replaced explicitly, with an announcement and predictable focus.
- No stale/mixed revision detail remains.

## Scenario 7: Versions workspace

Exercise no-revision, Working-only, Published-only, and Working-plus-Published semesters.

Expected:

- Working and Current Published identities, states, designations, and available FS-013 actions are accurate.
- Ordered event history is complete but detailed events can be disclosed on demand.
- Start Draft, review, publish, abandon, restore, confirmation, rejection, stale, and refresh behavior matches FS-013.
- The panel sizes to its content and does not stretch to Calendar or exam height.

## Scenario 8: Exams workspace

Use a semester with eligible courses, active exams, missing-final-teaching or other unavailable states, and enough courses to scroll.

Expected:

- Eligible courses appear first and only authoritative eligible courses can be selected.
- Unavailable courses are grouped separately with exact reasons.
- Selected count, constraints, and Prepare exams action remain available outside the scrolling list.
- With no selection, nearby text explains why preparation is unavailable.
- An eligibility refresh prunes invalid selections and announces the change.
- Requirement edit, manual placement, prepare/generate, confirmation, partial results, stale state, and per-course success/failure match FS-012.

## Scenario 9: Adaptive pane, keyboard, zoom, and assistive technology

1. Open a clean and then dirty pane with navigation pinned/unpinned and Planning inputs shown/hidden.
2. Above an 820px viewport, resize the Calendar pane container across 70rem and verify docked at or above 70rem and right overlay below 70rem.
3. Resize the viewport across 820px and then to 320px.
4. Repeat at 200% text zoom and with long course/resource labels.
5. Operate all controls by keyboard.
6. Repeat semantic checks using NVDA with Firefox.

Expected:

- One pane changes presentation at the defined 70rem container and 820px viewport boundaries without losing selection, draft, errors, or dirty state.
- Docked and overlay panes are named complementary regions and do not trap focus.
- Narrow full-screen pane is a named modal, contains focus, makes obscured Calendar unavailable, and supports clean Escape close.
- Dirty Escape opens the Keep editing / Discard decision; the decision does not create an inaccessible nested modal.
- Close restores the origin occurrence or a predictable Calendar results target.
- All navigation, context, close, edit, save, cancel, lifecycle, and preparation controls remain reachable and unobscured.
- NVDA announces navigation purpose/current state, expanded state, pane/dialog purpose, errors, and save/reconciliation results accurately.

## Scenario 10: Deliberate List and domain regression

1. Choose List mode intentionally and edit a teaching session.
2. Exercise existing schedule generation/clear behavior.
3. Exercise lifecycle and exam actions through their focused workspaces.
4. Exercise existing Academic Data workflows.

Expected:

- Deliberate List mode remains available and reuses the same teaching edit fields/validation.
- Calendar selection never forces List mode.
- Existing scheduling, conflict, capacity, holiday, validation, lifecycle, publication, exam, and catalog rules remain unchanged.

## Evidence to retain

- Output from every focused and complete verification command.
- Wide pinned and wide unpinned temporary-overlay states, the 70rem docked/overlay container boundary, the 820px full-screen boundary, 320px, and 200%-zoom browser matrix.
- Recorded session-edit and Schedule-navigation action counts plus Calendar scroll positions before and after pane operations.
- Keyboard/focus, accessibility-tree, and long-label results.
- NVDA and Firefox versions plus announced hierarchy, current/expanded state, pane/dialog, errors, and status results.
- Screenshots of Calendar without stacked workspaces, focused Versions, focused Exams, and each pane presentation.
- Dirty-transition matrix for all replacement intents and both decisions.
- Notes for no-revision/read-only/stale/disappearing-session/eligibility-refresh cases.
- Results from at least 10 representative planners or designated acceptance reviewers for SC-003 and SC-005 before FS-019 is declared complete.
