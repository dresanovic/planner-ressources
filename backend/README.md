# Resource Planner Backend

FastAPI backend for the resource planner.

## Setup

Install dependencies from `backend/requirements.txt`.

```text
pip install -r requirements.txt
```

The first implementation slice uses SQLite through SQLAlchemy. By default, the backend reads and writes `planner.db` in the backend working directory:

```text
DATABASE_URL=sqlite:///./planner.db
```

Set `DATABASE_URL` to a different SQLAlchemy URL when running against another database. The current model layer is SQLAlchemy-based so the same feature code can later move to PostgreSQL with migrations instead of a rewrite.

## Draft Schedule Slice

The draft schedule API supports explicit generation for one course:

- `GET /api/planning-options`
- `GET /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `POST /api/courses/{course_id}/draft-schedule/generate`
- `DELETE /api/courses/{course_id}/generation-constraints?semesterId={semester_id}`
- `GET /api/courses/{course_id}/draft-schedule`
- `GET /api/draft-schedules?semesterId={semester_id}`
- `PATCH /api/draft-sessions/{session_id}`

The planning options endpoint returns the database-backed courses, semesters, and study type time windows that the UI can select from. The generation-constraints endpoint returns the active course-semester constraints: semester dates and study type time windows by default, or the last successfully generated custom planning period and weekly windows.

Generation requires existing planning data for one course, lecturer, room, Cohort, semester, study type, and at least one allowed teaching window. The request body includes `semesterId`, `planningPeriod`, and `allowedTeachingWindows`; each window includes `weekday`, `startTime`, `endTime`, and optional `sourceTimeWindowId`. Invalid requests return a `422` response with all detected generation errors in an `errors` array. Successful generation replaces the previous generated draft for that course and saves the submitted constraint set for the course-semester pair. Failed generation leaves the previous draft and saved constraints unchanged.

The single-course draft schedule response includes review context for the selected course:

- course, Cohort, lecturer, room, and study type names and IDs
- generated session date, start/end time, units, filterable planning IDs, optional source `timeWindowId`, and `constraintWindowIndex`
- non-blocking `validationAlerts` on each session, including alert code, message, and related conflicting sessions for overlap alerts

The semester-scoped draft schedule endpoint returns all generated schedules for the selected semester so the planner UI can power the Courses overview filters.

Manual Draft Session editing is available through `PATCH /api/draft-sessions/{session_id}`. The request body accepts `date`, `startTime`, `endTime`, and `roomId`; a successful edit returns the refreshed parent Draft Schedule so the Courses overview can replace its saved schedule data. The endpoint rejects out-of-semester dates, end times that are not after start times, duplicate session dates within the same Draft Schedule, missing rooms, and rooms whose capacity is below the session Cohort size. Room occupancy conflicts are reported as non-blocking validation alerts after save; public holidays, exams, dashboard alerts, and source planning-record edits remain deferred to later slices.

Conflict detection adds non-blocking validation alerts to generated Draft Sessions returned by generation, single-course reads, semester overview reads, and manual edit responses. Alerts are derived at read time from the selected-semester schedule set and planning data. They currently cover lecturer, room, and Cohort overlaps; room capacity violations; sessions outside the currently active course-semester generation constraints; sessions outside Study Type Time Windows when no custom active generation constraints exist; and missing validation reference data. Alerts never block generation or otherwise valid manual edits.

## Migrations

Migration placeholders live in `backend/app/db/migrations/`. The initial planning-table migration mirrors the SQLAlchemy models for this slice and should be wired into the project Alembic environment before production deployment.

## Verification

Run backend tests from this directory:

```text
python -m pytest
```

## Dummy Planning Data

Seed local test data from the backend directory:

```text
python scripts/seed_dummy_planning_data.py
```

The script is idempotent: it updates or reuses records by name, so it can be run more than once without creating duplicate dummy courses. It adds three courses across two lecturers, with cohorts, rooms, study types, time windows, and a Fall 2026 semester.
