# Baseline Inventory: FS-022 Current User-Facing Surfaces

## Purpose

This is the reviewed implementation baseline for the current React/Vite planner and accountless lecturer interfaces. A file may appear in more than one section. Implementation tasks must check every listed surface and add any newly discovered current consumer before claiming the corresponding 100% success criterion.

The inventory is intentionally boundary-aware: ISO values in API modules, fixtures, snapshots, logs, URLs, sorting, persistence, and exports are not human presentation and must remain unchanged. Ordinary German prose is not configurable terminology.

## Configurable terminology consumers

The initial selected concepts are Course, Lecturer, Cohort, Room, Schedule, and Academic Data. Inspect these current presentation owners for exact context keys:

| Surface/file | Expected contexts or responsibility |
|---|---|
| `client/src/App.tsx` | Schedule and Academic Data application headings/destinations |
| `client/src/components/ApplicationNavigation.tsx` | Navigation labels; stable category IDs must remain independent of display values |
| `client/src/pages/AcademicDataPage.tsx` | Academic Data heading plus Course/Lecturer/Cohort/Room child context |
| `client/src/components/AcademicRecordEditor.tsx` | Course/Cohort field labels and headings where present |
| `client/src/components/AcademicCatalogList.tsx` | Course/Cohort table/list headings |
| `client/src/components/ResourceCatalogList.tsx` | Lecturer/Room table/list headings |
| `client/src/components/ResourceEditor.tsx` | Lecturer/Room field and heading labels |
| `client/src/components/CourseResourceEligibilityEditor.tsx` | Course/Lecturer/Room headings and fields |
| `client/src/pages/CourseSchedulePage.tsx` | Schedule/Course context headings and controls |
| `client/src/components/DraftSchedulePanel.tsx` | Course/Lecturer/Cohort/Room list/table labels |
| `client/src/components/CalendarPlanningWorkspace.tsx` | Schedule/Course/Lecturer/Cohort/Room filters, headings, and accessible names |
| `client/src/components/SessionPane.tsx` | Course/Lecturer/Cohort/Room detail and field labels |
| `client/src/pages/LecturerReviewPage.tsx` | Accountless Course/Lecturer/Room labels and accessible names |
| `client/src/components/LecturerReviewManagement.tsx` | Planner management labels referring to Lecturer/Course/Schedule |
| Exam editors, panels, and dialogs under `client/src/components/` | Selected Course/Lecturer/Cohort/Room labels only; exam terminology itself remains fixed German copy in this slice |

Implementation evidence must map each migrated occurrence to one exact schema key. Repeated fixed nouns inside complete German sentences remain nonconfigurable unless the specification is amended first.

## Date-entry consumers

| File | Current date entry |
|---|---|
| `client/src/components/AcademicRecordEditor.tsx` | Semester start/end fields created through its input helper |
| `client/src/components/CalendarPlanningWorkspace.tsx` | Calendar anchor date |
| `client/src/components/DraftSchedulePanel.tsx` | Generation start/end dates |
| `client/src/components/ExamManualSessionEditor.tsx` | Exam scheduled date |
| `client/src/components/ExamRequirementEditor.tsx` | Recommended start/end dates |
| `client/src/components/HolidayAdministration.tsx` | Holiday date |
| `client/src/components/ResourceAvailabilityEditor.tsx` | Availability start/end dates |
| `client/src/components/TeachingSessionEditor.tsx` | Teaching session date |
| `client/src/pages/CourseSchedulePage.tsx` | Manual session date |
| `client/src/components/MultiCourseGenerationPanel.tsx` | Comma-separated unavailable dates |

Every native date field and the multi-value control must use the European-entry contract while continuing to pass ISO to existing APIs.

## Date-display consumers

Inspect visible text, tables, headings, summaries, dialogs, messages, `aria-label`/descriptions, and live regions in:

- `client/src/components/CalendarPlanningWorkspace.tsx`
- `client/src/components/ScheduleOccurrenceList.tsx`
- `client/src/components/SessionPane.tsx`
- `client/src/components/DraftSchedulePanel.tsx`
- `client/src/pages/CourseSchedulePage.tsx`
- `client/src/components/ExamRequirementEditor.tsx`
- `client/src/components/HolidayAdministration.tsx`
- `client/src/components/ExamDeletionDialog.tsx`
- `client/src/components/ScheduleDeletionDialog.tsx`
- `client/src/utils/calendarFindingLabel.ts`
- `client/src/utils/resourceAvailability.ts`
- `client/src/pages/LecturerReviewPage.tsx`
- `client/src/components/LecturerReviewManagement.tsx`
- `client/src/components/ScheduleLifecyclePanel.tsx`
- `client/src/components/BatchResultSummary.tsx`
- any message mapper introduced for the problem inventory

Also inspect `client/src/utils/calendarWorkspaceUtils.ts` and `client/src/pages/scheduleReviewUtils.ts`: retain safe ISO comparisons/date arithmetic, but remove host-timezone-dependent presentation calculations. `client/src/api/calendarWorkspace.ts` keeps ISO transport but should use strict calendar-date validation rather than permissive normalization when practical without changing its contract.

## Warning and failure consumers

### Motivating and validation-warning paths

| File | Current issue |
|---|---|
| `client/src/components/DraftSchedulePanel.tsx` | Bare outside-window text, ISO recommended/final-teaching dates, raw validity codes/messages, generic affected-record banner |
| `client/src/utils/calendarFindingLabel.ts` | Short generic labels and raw-code fallback without record/value/action context |
| `client/src/components/SessionPane.tsx` | Consumes generic finding label in focused details |
| `client/src/components/CalendarPlanningWorkspace.tsx` | Consumes generic finding label in calendar/list/detail/accessibility states |
| `backend/app/services/lecturer_review.py` | Public safe projection currently removes context and emits generic English finding messages |
| `client/src/components/ProtectedDeleteDialog.tsx` | Renders backend blocker messages directly without contextual correction/archive guidance |
| `client/src/components/PublicationConfirmationDialog.tsx` | Renders non-blocking condition messages directly without the complete saved/blocking/action context |

### Joined/raw failure paths

At minimum inspect and migrate known states in:

- `client/src/pages/CourseSchedulePage.tsx`
- `client/src/components/ExamGenerationPanel.tsx`
- `client/src/components/ExamRequirementEditor.tsx`
- `client/src/components/AcademicRecordEditor.tsx`
- `client/src/components/BatchResultSummary.tsx`
- `client/src/pages/AcademicDataPage.tsx`
- `client/src/components/HolidayAdministration.tsx`
- `client/src/components/ResourceEditor.tsx`
- `client/src/components/ResourceAvailabilityEditor.tsx`
- `client/src/components/CourseResourceEligibilityEditor.tsx`
- `client/src/pages/LecturerReviewPage.tsx`
- `client/src/components/LecturerReviewManagement.tsx`
- `client/src/components/ProtectedDeleteDialog.tsx`
- `client/src/components/PublicationConfirmationDialog.tsx`

Search for `reason.message`, backend `message` display, `errors.join`, `map(...).join`, and `replaceAll('_', ' ')`. Each occurrence must be classified as a known mapper, safe fixed fallback, technical-only value, or explicitly justified exclusion. Multiple domain errors must remain separate items.

### Field-validation association baseline

In addition to the files above, explicitly inventory every control-level validation path in `client/src/components/AcademicRecordEditor.tsx`, `client/src/components/ExamRequirementEditor.tsx`, `client/src/components/HolidayAdministration.tsx`, `client/src/components/ResourceEditor.tsx`, `client/src/components/ResourceAvailabilityEditor.tsx`, `client/src/components/CourseResourceEligibilityEditor.tsx`, `client/src/components/TeachingSessionEditor.tsx`, `client/src/components/ExamManualSessionEditor.tsx`, `client/src/components/MultiCourseGenerationPanel.tsx`, `client/src/components/DraftSchedulePanel.tsx`, and `client/src/pages/CourseSchedulePage.tsx`. Every field-specific problem must have a stable message ID, `aria-invalid`, `aria-describedby`, first-invalid focus after attempted continuation, and a test; aggregate operation failures remain in the problem list rather than being falsely attached to one field.

## Accessibility and responsive evidence

For every migrated field/problem component, record:

- programmatic label, hint, and field-error relationships;
- alert versus polite warning semantics;
- keyboard operation and focus after submit/action/retry;
- visible focus and non-color-only severity;
- 320 CSS pixel, 200% text zoom, long terminology/name/message wrapping;
- accessible names/live text containing dates in `DD.MM.YYYY`;
- manual NVDA/Firefox result where jsdom cannot prove announcement/focus behavior.

## Completion record

During implementation, append or link a matrix that records for every item above: exact production change, failing-first test, final automated result, and any manual evidence. No listed surface may be silently omitted; a nonapplicable item needs a reason tied to the presentation/machine boundary.
