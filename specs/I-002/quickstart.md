# Quickstart: Validate FS-022 Consistent Labels, European Dates, and Actionable Messages

## Purpose

Use this guide after implementation to prove that one startup-selected German terminology catalog serves both interfaces, every human calendar date uses `DD.MM.YYYY`, known problems are precise and actionable, and existing business/machine behavior is unchanged. Review [the terminology API contract](contracts/ui-terminology-api.md), [the presentation contract](contracts/presentation-contract.md), and [the transient data model](data-model.md) before recording acceptance evidence.

## Prerequisites

- Install the repository's locked backend and client dependencies.
- Use representative FS-019 planner data containing teaching sessions, exams inside and outside recommended ranges, revisions, holidays, resource availability, stale snapshots, and multi-problem validation outcomes.
- Prepare an accountless lecturer review whose safe visible findings include at least one known warning and one generic fallback.
- Prepare three terminology configurations: no override, a valid partial override with umlauts and a long phrase, and invalid files covering an unknown key and a blank value.
- For container checks, mount the customer file read-only and set `CUSTOMER_TERMINOLOGY_FILE` to its in-container absolute path. Leave the variable unset for shipped defaults.
- Use the latest stable Microsoft Edge, Google Chrome, and Mozilla Firefox on Windows and record every exact version. Test the responsive layout at 320 CSS pixels in each browser. Use NVDA with Firefox on Windows for the assistive-technology pass and record both versions. Separate mobile-OS browser certification is not part of this slice.

## Test-first implementation order

Before each production group, add or update a focused test that fails for the intended behavior:

1. Backend default/override loading and startup rejection.
2. Public catalog endpoint and secret-safe client bootstrap.
3. Typed catalog access and representative multi-surface terminology migration.
4. Strict date-only/timestamp utilities and institution-local today.
5. European date-field validity, conversion, accessibility, and reset behavior.
6. Date display and entry migration by inventoried surface.
7. Problem model/renderer, safe fallback, separate items, and field association.
8. Domain-local warning/failure mappings, including outside-window and accountless safe projection.

Any behavior that cannot be automated must record why and the exact manual scenario used instead.

## Automated verification by implementation checkpoint

The groups below are intentionally independent: no checkpoint references a test file introduced by a later story.

### Shared foundation

Run from `client/`:

```text
npm test -- src/utils/datePresentation.test.ts
```

Expected: strict date-only conversion, range behavior, leap/century/year boundaries, Vienna timestamp/DST behavior, and institution-local today pass without changing a calendar-only day.

### User Story 1: actionable problems

Run from the repository root:

```text
python -m pytest backend/tests/services/test_lecturer_review.py backend/tests/api/test_lecturer_review.py
```

Run from `client/`:

```text
npm test -- src/utils/userProblems.test.ts src/components/ActionableProblemList.test.tsx src/components/DraftSchedulePanel.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/SessionPane.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/ExamGenerationPanel.test.tsx src/components/ExamRequirementEditor.test.tsx src/components/ExamManualSessionEditor.test.tsx src/components/TeachingSessionEditor.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/components/BatchResultSummary.test.tsx src/components/PublicationConfirmationDialog.test.tsx src/pages/AcademicDataPage.test.tsx src/components/AcademicRecordEditor.test.tsx src/components/HolidayAdministration.test.tsx src/components/ResourceAdministration.test.tsx src/components/ResourceAvailabilityEditor.test.tsx src/components/CourseResourceEligibilityEditor.test.tsx src/components/ProtectedDeleteDialog.test.tsx src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx
```

Expected: known conditions and failures are contextual German problem items, field associations are complete, the two dialogs do not render raw blocker/condition messages, multiple issues remain separate, and secrets/diagnostics never leak.

### User Story 2: European dates

Run from the repository root:

```text
python -m pytest backend/tests/api/test_calendar_workspace.py backend/tests/api/test_lecturer_review.py
```

Run from `client/`:

```text
npm test -- src/utils/datePresentation.test.ts src/components/EuropeanDateField.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/ScheduleOccurrenceList.test.tsx src/components/SessionPane.test.tsx src/components/calendarWorkspaceUtils.test.ts src/components/DraftSchedulePanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/TeachingSessionEditor.test.tsx src/components/ExamManualSessionEditor.test.tsx src/components/ExamRequirementEditor.test.tsx src/components/MultiCourseGenerationPanel.test.tsx src/components/AcademicRecordEditor.test.tsx src/components/HolidayAdministration.test.tsx src/components/ResourceAvailabilityEditor.test.tsx src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx src/components/ScheduleLifecyclePanel.test.tsx src/components/ExamDeletionDialog.test.tsx src/components/ScheduleDeletionDialog.test.tsx src/components/BatchResultSummary.test.tsx src/components/scheduleReviewUtils.test.ts src/api/calendarWorkspace.test.ts src/api/draftSchedule.test.ts src/api/examScheduling.test.ts src/api/lecturerReview.test.ts src/pages/CourseSchedulePage.snapshot.test.ts
```

Expected: visible dates and entries use `DD.MM.YYYY`, timezone/date boundaries pass, and API payloads, snapshots, ordering, and public transport remain ISO.

### User Story 3: terminology

Run from the repository root:

```text
python -m pytest backend/tests/services/test_terminology.py backend/tests/api/test_ui_terminology.py backend/tests/test_main.py
```

Run from `client/`:

```text
npm test -- src/config/terminology.test.ts src/main.test.tsx src/App.test.tsx src/components/ApplicationNavigation.test.tsx src/pages/AcademicDataPage.test.tsx src/components/AcademicRecordEditor.test.tsx src/components/ResourceAdministration.test.tsx src/components/CourseResourceEligibilityEditor.test.tsx src/components/HolidayAdministration.test.tsx src/pages/CourseSchedulePage.test.tsx src/components/DraftSchedulePanel.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/SessionPane.test.tsx src/components/ExamGenerationPanel.test.tsx src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx
```

Expected: schema/backend/client key sets match exactly, direct component tests initialize deterministic defaults, override tests remain isolated, one terminology GET occurs per bootstrap attempt, Retry adds one request, normal interaction adds none, and the endpoint performs no database work.

### Complete release regression

Run from the repository root and then `client/` respectively:

```text
python -m pytest backend/tests
npm test
npm run lint
npm run build
```

Expected: every command exits successfully. Every inventoried surface has migrated labels, dates, and messages while domain decisions, response statuses, ISO fields, persistence, authorization, privacy, and exports remain unchanged.

## Scenario 1: Shipped German application

1. Start the application with `CUSTOMER_TERMINOLOGY_FILE` unset.
2. Open every primary planner navigation destination and representative lists/forms/dialogs.
3. Open an accountless lecturer review using a fresh secret link.

Expected:

- The document language and ordinary application copy are German.
- Every approved configurable occurrence uses the shipped German default; no English migrated label, blank, or raw key appears.
- Planner and lecturer surfaces use the same effective terminology.
- The lecturer fragment disappears before any visible wait or network request and the review still loads normally.

## Scenario 2: Customer terminology without rebuild

1. Use the same built image and mount a valid partial file that changes Course labels in every supported context and one Lecturer table heading. Include umlauts, punctuation, and one long institutional phrase.
2. Set `CUSTOMER_TERMINOLOGY_FILE` and restart the service without rebuilding.
3. Visit navigation, heading, form, table, planner, and accountless locations from the migration inventory.
4. Inspect stored course/lecturer/room names and ordinary German sentences.

Expected:

- Every occurrence for each overridden exact key changes after restart.
- Omitted keys retain shipped defaults.
- Singular/plural/navigation/heading/field/table values appear only in their exact contexts; no automatic grammar or prose substitution occurs.
- Stored/dynamic record values and ordinary copy remain unchanged.
- Long values wrap and controls remain operable.

## Scenario 3: Invalid deployment configuration

Repeat startup with a missing configured file, malformed JSON, duplicate property, unknown property, blank value, non-string value, and control character.

Expected:

- Each configured invalid case prevents the service from becoming ready and therefore serves no affected UI.
- Operator diagnostics identify the configuration category/file/key when safe but do not print the customer value, secret, or internal data.
- With the variable unset, defaults start successfully; a configured-but-missing file is never silently treated as absent.
- A simulated catalog fetch/response failure in the browser shows fixed German copy and a safe Retry, with no partly rendered app, raw key, or raw error.

## Scenario 4: Date display inventory

Inspect lists, week/day/month calendar modes, cards, detail panes, summaries, dialogs, confirmations, notices, messages, accessibility labels, lecturer review/management, lifecycle history, availability, holidays, and exam recommendation/final-teaching text. Include `2026-09-11`, leap day, month/year boundaries, and Vienna DST boundaries.

Expected:

- Every explicit human numeric date is zero-padded `DD.MM.YYYY`; every range endpoint is formatted and direction is clear.
- Weekday/month words are German where present.
- Date-only values never shift to an adjacent day.
- Timestamps keep their established 24-hour time and Vienna meaning.
- Machine values in network requests/responses, URLs, sorting, snapshots, database checks, logs, and exports remain ISO/current-standard.

## Scenario 5: Date entry and correction

Using pointer only and keyboard only, exercise semester start/end, calendar anchor, schedule generation start/end, teaching/exam session date, exam recommendation start/end, holiday date, availability start/end, manual session date, and the comma-separated unavailable-date control.

For each, enter/paste a valid value, clear optional/required values, type an incomplete form, `31.04.2026`, non-leap `29.02.2027`, a valid leap day, a min/max violation, and reversed ranges.

Expected:

- The visible field always displays and accepts `DD.MM.YYYY` with persistent `TT.MM.JJJJ` help.
- Valid values submit the same ISO day through the existing API.
- Invalid values are retained for correction but never submit the previous valid value or a normalized different day.
- On attempted continuation, the first affected field receives focus, is invalid programmatically, and references a German correction describing the expected format/rule.
- Multi-date errors identify the individual bad token rather than reject with one generic sentence.

## Scenario 6: Outside recommended window

Open the Courses overview for `KI Grundlagen` with an exam scheduled on `2026-09-11` and a known recommended range. Exercise an editable saved placement, a not-yet-saved state if supported by the current workflow, and a read-only/accountless view.

Expected:

- The warning identifies the actual course/exam, scheduled `11.09.2026`, and both recommended dates in European form.
- It explicitly says the condition is non-blocking and accurately states whether the placement remains saved.
- The editable row points to its adjacent `Bearbeiten` control and explains that intentional retention is possible; it does not add a duplicate action.
- Read-only/accountless wording offers only its real review/feedback/retain path.
- The rule, dates, severity, and placement are not recalculated or changed by presentation.

## Scenario 7: Problem-category matrix

Trigger one representative field validation, known domain warning, safe load failure, stale update, permission failure, mutation-time connectivity failure, and unexpected service failure. For safe reads use Retry; for ambiguous mutations simulate a lost response after submission. Include a record with a very long name and inject a fake bearer/stack/database string into a raw exception fixture.

Expected:

- Every known message names the action/condition and affected context, explains known reasons/values, states blocking and saved/input status when known, and gives a real next step.
- Stale and ambiguous mutation failures direct refresh/verification before repeating.
- Unexpected fallback acknowledges the unavailable cause and never displays injected diagnostics.
- Direct actions appear only when safe/currently available; existing adjacent controls are identified rather than duplicated.

## Scenario 8: Multiple problems and accessibility

1. Trigger at least three simultaneous validation issues, including two with the same category.
2. Navigate the problem list and related fields/actions by keyboard.
3. Repeat in the latest stable Edge, Chrome, and Firefox on Windows at 320 CSS pixels, 200% text zoom, and with long catalog/record values.
4. Inspect the accessibility tree in each browser and repeat announcements with NVDA/Firefox.

Expected:

- Each issue is a distinct list item with stable identity and its own guidance; none are joined into one sentence.
- A newly presented blocking result is announced once as an alert region; non-blocking warnings are identified politely and are not announced as blocking alerts.
- Field errors are associated with their controls; focus goes to the first invalid field only after attempted continuation and is not stolen by background refresh.
- Severity is understandable without color; actions have visible focus; text wraps and no control is obscured.

## Scenario 9: Inventory and source-boundary audit

Review the completed surface inventory and the changed-source scan.

Expected:

- Every current planner/accountless surface has an explicit label/date/problem disposition and matching automated or manual evidence.
- Selected configurable terms have no migrated literal consumer outside the catalog accessor.
- Human date presentation has no raw ISO occurrence.
- Known user failures do not directly render raw `Error.message`, backend `message`, or code as their primary explanation.
- Remaining ISO literals are classified as machine values, fixtures, logs, URLs, or exports; remaining German concept words in fixed prose are classified as intentionally nonconfigurable.

## Scenario 10: Representative-user outcome

Present the motivating warning to at least 10 representative planners or designated acceptance reviewers without coaching. Ask each person to state what happened, whether the schedule remains usable/saved, the recommended interval, and one valid next action. Record time to a correct answer.

Expected: at least 9 of 10 answer correctly within 30 seconds. Implementation may be technically complete before this session, but FS-022 cannot be declared fully accepted until real results are recorded; do not fabricate participants or outcomes.

## Evidence to retain

- Output from every focused and complete verification command.
- Terminology startup/default/override/failure matrix and effective-response sample.
- Completed surface inventory with automated/manual test links.
- Network evidence that human entry submits ISO and existing API/export contracts are unchanged.
- Browser matrix for date entry/display, 320px, 200% zoom, and long text.
- Keyboard/focus/accessibility-tree findings and NVDA/Firefox versions/announcements.
- Screenshots of representative German defaults, customer overrides, corrected date displays/fields, outside-window message, multiple problems, and safe fallback.
- Security test evidence showing secret/diagnostic non-disclosure.
- Actual representative-user count, timing, and outcome for SC-006.
