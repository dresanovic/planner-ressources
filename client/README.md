# Resource Planner Client

React/Vite frontend for the resource planner.

## Unified Application Navigation (FS-018)

The application exposes one primary left navigation hierarchy. **Schedule** is a top-level destination. **Academic Data** is a disclosure with, in order, Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, and Rooms. The current leaf and its Academic Data parent context are conveyed semantically and with text/shape treatments in addition to color. The former fixed top switcher and page-owned sidebars are removed.

On screens wider than 820px the hierarchy remains in a persistent sidebar. At 820px and below, **Menu** opens the same hierarchy as a named modal panel. Focus enters the panel, remains contained while it is open, and returns to the opener when dismissed with Escape or **Close menu**. Selecting a destination closes the panel and moves focus to the resulting content; selecting the already-current leaf closes it without resetting page state. All controls are native keyboard-operable controls with visible focus indicators.

FS-018 changes only the client shell and the current view/category/expansion state. It adds no route, dependency, backend endpoint, API contract, authentication behavior, scheduling rule, or catalog rule.

## Resource Eligibility and Availability (FS-008)

The **Academic Data** workspace includes coded Lecturer and Room administration. Active resources are shown by default; planners can search by name/code, inspect inactive records, maintain Room capacity and recurring/dated unavailable periods, review usage before removal, and reactivate retired resources. Unreferenced resources are permanently deleted; resources used by active Courses or saved sessions are retained inactive with the affected Courses explained.

Course editing includes searchable eligible Lecturer and Room sets. Invalid preserved relationships stay visible, while inactive or newly undersized choices cannot be added. The fixed guidance explains that generation always prefers contiguous Lecturer blocks and Room reuse where hard eligibility, availability, and capacity rules allow. Cohort growth feedback lists automatic insufficient-Room cleanup and Courses left without a usable Room.

Generated session rows show `Name Â· CODE` for the actual per-session Lecturer and Room. Manual editing changes exactly one eligible Lecturer and Room and retains simultaneous eligibility, availability, capacity, and overlap alerts. These preferences and assignments are Course-local; there is no global resource optimizer in this slice.

## Draft Schedule Page

The schedule page lets an admin trigger draft schedule generation for one selected course, review generated sessions across the selected semester, and manually correct already generated Draft Sessions.

The page calls the backend draft schedule endpoints:

- `GET /api/planning-options`
- `GET /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `POST /api/courses/{course_id}/draft-schedule/generate`
- `DELETE /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `GET /api/courses/{course_id}/draft-schedule?semesterId={semester_id}`
- `GET /api/draft-schedules?semesterId={semester_id}`
- `PATCH /api/draft-sessions/{sessionId}`
- `POST /api/draft-schedules/batch/prepare`
- `POST /api/draft-schedules/batch/generate`
- `POST /api/draft-schedules/optimization/prepare`
- `POST /api/draft-schedules/optimization/generate`

Course and semester controls are loaded from backend planning data instead of being hardcoded in the client. The generation constraints panel lives in the planning input sidebar, loads defaults from the selected semester and course study type, then lets office staff override the planning period and allowed weekly teaching windows before generation. Those controls affect the next generated draft for the selected planning input; they are separate from overview filters.

Set `VITE_API_BASE_URL` when the FastAPI backend is served from a different origin. Leave it empty when the client is served behind the same origin or dev proxy.

The review panel supports:

- a central Courses overview for generated plans in the selected semester
- chronological list review with date, time, units, course, Cohort, lecturer, room, and study type context
- weekly grouped review mode
- compact filters derived from all generated course, Cohort, lecturer, room, and study type values in the selected semester
- manual editing of an existing Draft Session's date, start time, end time, Lecturer, and Room
- derived session length display from the edited start and end time
- room choices with capacity metadata, with insufficient-capacity room edits rejected by the backend
- non-blocking validation alerts for lecturer, room, and Cohort overlaps, room capacity issues, active generation-constraint violations, and Study Type Time Window violations
- alert details that identify related conflicting sessions when an overlap is detected
- distinct no-semester-schedules and no-results states

Manual edits update the saved draft schedule returned to the overview, so changed sessions and validation alerts remain visible while switching filters or list/weekly review modes. Validation alerts do not block generation or otherwise valid manual edits.

The page has separate **One course** and **Several courses** modes. The several-course mode now exposes **Optimize selected courses** for 1-20 Courses and optional comma-separated future unavailable dates. Selection remains visible during preparation, confirmation, solving, errors, and retry. Duplicate unavailable dates are deduplicated before the backend preparation is echoed.

Before replacing same-semester Draft Schedules, the client shows the canonical preparation result and warns that manual edits will be lost. Cancel closes the dialog without an execution request. A normal execution displays aggregate counts and one ordered result row per Course, including all understandable failure reasons. **Retry failed courses** performs a fresh retry preparation for failed IDs only, including a single failed Course, without regenerating successes.

Batch results are retained only in mounted React state. After every normal result, the complete selected-semester Courses overview refreshes once so existing non-blocking conflict alerts are recalculated across generated and pre-existing schedules. During refresh the last known overview remains mounted; a failed refresh preserves both the result and previous overview and offers a retry. A successful refresh resets overview filters and any open edit so new schedules are visible.

The optimized result shows complete, improved partial, unchanged, failed, and stale counts; scheduled/remaining units; arrangement improvements; all returned blocking reasons; elapsed time; and prepared-snapshot proof wording. Existing/manual drafts are listed in a confirmation dialog and cannot lose units. Failed and stale retry always starts a fresh preparation. The complete semester overview and validation alerts refresh after a result while current review filters remain usable.

Holiday administration, exams, automatic movement/deletion of unselected sessions, persisted optimization history, algorithm selection, fairness quotas, and background processing remain out of scope. The legacy FS-006 independent batch API remains available and unchanged even though the primary several-course screen uses conflict-aware optimization.

## Academic Data Administration

Use the **Academic Data** navigation hierarchy to create, review, edit, archive/reactivate, and safely delete Semesters, Cohorts, Courses, Study Types, Time Windows, Lecturers, and Rooms. Category lists retain last-known content during refresh, support active/inactive filtering, and use controlled forms so entered values survive backend validation. Course forms establish initial resources and expose the complete maintained eligibility sets while editing.

Each record exposes usage-aware actions. Permanent deletion opens a keyboard-operable dialog that separates dependent-record blockers from saved-schedule blockers and offers Archive without changing dependent lifecycle state. Revision conflicts and validation failures are announced without silently replacing local form input. Legacy name-repair records show rename guidance.

Returning to **Schedule** keeps its mounted state and applies catalog-revision refreshes after Academic Data mutations. Course choices are limited to the selected current Semester; invalid prior selections are retained and flagged, and visible unavailable Courses show their reason. Generation remains disabled until the planner selects an eligible Course. No client router, form library, or external state library is required.

The academic administration client uses `/api/academic` for Courses and eligibility and `/api/resources` for Lecturer/Room lifecycle and unavailable periods. Authentication, imports, and external synchronization remain outside this slice.

## Development

Install dependencies:

```text
npm install
```

Run the local dev server:

```text
npm run dev
```

Run verification:

```text
npm run lint
npm run test
npm run build
```
## FS-009 manual session workflow

In the selected-course Planning Summary, scheduled and remaining units are derived from the complete saved course-semester draft, independent of active overview filters. A course without a Draft Schedule remains visible with zero scheduled units and all current course units remaining.

The **Add one Draft Session** form inherits the selected Course lecturer and cohort and offers current rooms with sufficient capacity. Start time plus explicit units proposes an end time using 45 minutes per unit and 10 minutes between units. The planner may move the end time earlier for merged teaching or later for a pause; the explicit unit count remains authoritative for progress.

Every session in list and weekly views has an action-specific **Delete** control. The selected-course section also provides **Clear course draft** when a draft exists. Both actions require a modal confirmation describing the exact course-semester scope, removed scheduled coverage, resulting remaining units, and—for complete clearing—preservation of source records and saved generation constraints.

Successful mutations refresh the complete semester overview without resetting filters. If the backend returns `STALE_DRAFT`, the obsolete confirmation closes, current schedules, progress, and alerts refresh, and the planner must open the action and confirm again. Network, validation, and persistence failures remain visible and are never presented as successful changes.
