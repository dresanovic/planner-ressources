# Quickstart: Review Generated Schedule In Planner UI

## Prerequisites

- Backend dependencies installed from `backend/requirements.txt`.
- Client dependencies installed with `npm install` in `client/`.
- Slice 1 draft schedule generation is available.

## Backend Validation

From the repository root:

```text
cd backend
python -m pytest
```

Expected outcomes:

- Existing generation tests pass.
- New or updated API tests confirm `GET /api/courses/{course_id}/draft-schedule` returns schedule context for course, Cohort, lecturer, room, and study type.
- New or updated API tests confirm generated sessions include filterable IDs for course, Cohort, lecturer, room, and study type.
- A missing generated schedule still returns `404` for the frontend no-schedule state.

## Frontend Validation

From the repository root:

```text
cd client
npm run lint
npm run build
```

Expected outcomes:

- TypeScript accepts the enriched draft schedule response shape.
- The schedule review UI builds without lint errors.
- The generated schedule can be reviewed in list mode and weekly mode.
- Switching view modes preserves the visible filtered session set.
- Filters for current course, Cohort, lecturer, room, and study type combine using match-all behavior.
- Clearing filters restores the visible sessions for the current selected course.
- No-schedule and no-filter-results states are visually distinct.
- No manual edit action is present for session date, start time, room, or length.

## Manual Review Scenario

1. Start the backend service using the project's normal FastAPI command.
2. Start the client development server from `client/`.
3. Open the planner schedule page.
4. Generate or load a draft schedule for course `Planning 101`.
5. Confirm every visible session shows date, time, units, course, Cohort, lecturer, room, and study type.
6. Switch between list and weekly views and confirm the same filtered sessions remain visible.
7. Apply each available filter and confirm visible sessions match all active filters.
8. Apply filters that produce no visible sessions and confirm the no-results state appears.
9. Confirm there is no control for editing session date, start time, room, or length.
