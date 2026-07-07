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

- `POST /api/courses/{course_id}/draft-schedule/generate`
- `GET /api/courses/{course_id}/draft-schedule`

Generation requires existing planning data for one course, lecturer, room, Cohort, semester, study type, and study type time windows. Invalid requests return a `422` response with all detected generation errors in an `errors` array. Successful generation replaces the previous generated draft for that course.

## Migrations

Migration placeholders live in `backend/app/db/migrations/`. The initial planning-table migration mirrors the SQLAlchemy models for this slice and should be wired into the project Alembic environment before production deployment.

## Verification

Run backend tests from this directory:

```text
python -m pytest
```
