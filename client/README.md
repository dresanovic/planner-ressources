# Resource Planner Client

React/Vite frontend for the resource planner.

## Draft Schedule Page

The schedule page lets an admin trigger draft schedule generation for one selected course, review generated sessions across the selected semester, and manually correct already generated Draft Sessions.

The page calls the backend draft schedule endpoints:

- `GET /api/planning-options`
- `GET /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `POST /api/courses/{course_id}/draft-schedule/generate`
- `DELETE /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `GET /api/courses/{course_id}/draft-schedule`
- `GET /api/draft-schedules?semesterId={semester_id}`
- `PATCH /api/draft-sessions/{sessionId}`

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

Manual edits update the saved draft schedule returned to the overview, so changed sessions and validation alerts remain visible while switching filters or list/weekly review modes. Validation alerts do not block generation or otherwise valid manual edits. Automatic conflict resolution, conflict-aware generation, room occupancy blocking, holiday warnings, exam controls, dashboard summaries, source planning-record editing, session creation/deletion/splitting/merging, and multi-course generation are intentionally not available in this slice.

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
