# Resource Planner Client

React/Vite frontend for the resource planner.

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

Course and semester controls are loaded from backend planning data instead of being hardcoded in the client. The generation constraints panel lives in the planning input sidebar, loads defaults from the selected semester and course study type, then lets office staff override the planning period and allowed weekly teaching windows before generation. Those controls affect the next generated draft for the selected planning input; they are separate from overview filters.

Set `VITE_API_BASE_URL` when the FastAPI backend is served from a different origin. Leave it empty when the client is served behind the same origin or dev proxy.

The review panel supports:

- a central Courses overview for generated plans in the selected semester
- chronological list review with date, time, units, course, Cohort, lecturer, room, and study type context
- weekly grouped review mode
- compact filters derived from all generated course, Cohort, lecturer, room, and study type values in the selected semester
- manual editing of an existing Draft Session's date, start time, end time, and room
- derived session length display from the edited start and end time
- room choices with capacity metadata, with insufficient-capacity room edits rejected by the backend
- non-blocking validation alerts for lecturer, room, and Cohort overlaps, room capacity issues, active generation-constraint violations, and Study Type Time Window violations
- alert details that identify related conflicting sessions when an overlap is detected
- distinct no-semester-schedules and no-results states

Manual edits update the saved draft schedule returned to the overview, so changed sessions and validation alerts remain visible while switching filters or list/weekly review modes. Validation alerts do not block generation or otherwise valid manual edits.

The page has separate **One course** and **Several courses** modes. Batch selection never changes the focused Course editor or sends its unsaved local values. Staff can select 2-50 Courses, see the selected count, and clear the selection. The UI explains that every selected Course uses its own saved constraints or defaults.

Before replacing same-semester Draft Schedules, the client shows the canonical preparation result and warns that manual edits will be lost. Cancel closes the dialog without an execution request. A normal execution displays aggregate counts and one ordered result row per Course, including all understandable failure reasons. **Retry failed courses** performs a fresh retry preparation for failed IDs only, including a single failed Course, without regenerating successes.

Batch results are retained only in mounted React state. After every normal result, the complete selected-semester Courses overview refreshes once so existing non-blocking conflict alerts are recalculated across generated and pre-existing schedules. During refresh the last known overview remains mounted; a failed refresh preserves both the result and previous overview and offers a retry. A successful refresh resets overview filters and any open edit so new schedules are visible.

Automatic conflict resolution, conflict-aware generation, room occupancy blocking, holiday warnings, exam controls, dashboard summaries, source planning-record editing, session creation/deletion/splitting/merging, persisted batch history, and background processing remain out of scope.

## Academic Data Administration

Use the top-level **Academic Data** view to create, review, edit, archive/reactivate, and safely delete Semesters, Cohorts, Courses, Study Types, and Time Windows. Category lists retain last-known content during refresh, support active/inactive filtering, and use controlled forms so entered values survive backend validation. Course forms select academic relationships plus the existing read-only Lecturer and Room options.

Each record exposes usage-aware actions. Permanent deletion opens a keyboard-operable dialog that separates dependent-record blockers from saved-schedule blockers and offers Archive without changing dependent lifecycle state. Revision conflicts and validation failures are announced without silently replacing local form input. Legacy name-repair records show rename guidance.

Returning to **Schedule** remounts and refetches planning options. Course choices are limited to the selected current Semester; invalid prior selections are retained and flagged, and visible unavailable Courses show their reason. Generation remains disabled until the planner selects an eligible Course. No client router, form library, or external state library is required.

The academic administration client uses the `/api/academic` contract documented by the backend. Lecturer/Room administration, availability calendars, authentication, and imports remain outside this slice.

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
