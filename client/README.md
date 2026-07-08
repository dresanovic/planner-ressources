# Resource Planner Client

React/Vite frontend for the resource planner.

## Draft Schedule Page

The schedule page lets an admin trigger draft schedule generation for one course and review the current generated sessions before editing is introduced in a later slice.

The page calls the backend draft schedule endpoints:

- `GET /api/planning-options`
- `GET /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `POST /api/courses/{course_id}/draft-schedule/generate`
- `DELETE /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `GET /api/courses/{course_id}/draft-schedule`

Course and semester controls are loaded from backend planning data instead of being hardcoded in the client. The generation constraints panel loads defaults from the selected semester and course study type, then lets office staff override the planning period and allowed weekly teaching windows before generation. Those controls affect the next generated draft; they are separate from review filters.

Set `VITE_API_BASE_URL` when the FastAPI backend is served from a different origin. Leave it empty when the client is served behind the same origin or dev proxy.

The review panel supports:

- generation constraints for the next draft schedule, including planning period and weekly allowed windows
- chronological list review with date, time, units, course, Cohort, lecturer, room, and study type context
- weekly grouped review mode
- filters for the current course context, Cohort, lecturer, room, and study type
- distinct no-schedule, zero-session, and no-results states

Manual session editing, conflict warnings, holiday warnings, exam controls, dashboard summaries, and semester-wide multi-course review are intentionally not available in this slice.

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
