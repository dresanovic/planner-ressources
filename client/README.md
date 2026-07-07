# Resource Planner Client

React/Vite frontend for the resource planner.

## Draft Schedule Page

The current first slice mounts a course schedule page that lets an admin trigger draft schedule generation for one course and review either the generated sessions or all returned failure reasons.

The page calls the backend draft schedule endpoints:

- `POST /api/courses/{course_id}/draft-schedule/generate`
- `GET /api/courses/{course_id}/draft-schedule`

Set `VITE_API_BASE_URL` when the FastAPI backend is served from a different origin. Leave it empty when the client is served behind the same origin or dev proxy.

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
npm run build
```
