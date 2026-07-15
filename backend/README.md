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
- `GET /api/courses/{course_id}/draft-schedule?semesterId={semester_id}`
- `GET /api/draft-schedules?semesterId={semester_id}`
- `PATCH /api/draft-sessions/{session_id}`
- `POST /api/draft-schedules/batch/prepare`
- `POST /api/draft-schedules/batch/generate`

The planning options endpoint returns the database-backed courses, semesters, and study type time windows that the UI can select from. The generation-constraints endpoint returns the active course-semester constraints: semester dates and study type time windows by default, or the last successfully generated custom planning period and weekly windows.

Generation requires existing planning data for one course, lecturer, room, Cohort, semester, study type, and at least one allowed teaching window. The request body includes `semesterId`, `planningPeriod`, and `allowedTeachingWindows`; each window includes `weekday`, `startTime`, `endTime`, and optional `sourceTimeWindowId`. Invalid requests return a `422` response with all detected generation errors in an `errors` array. Successful generation replaces the previous generated draft for that course and saves the submitted constraint set for the course-semester pair. Failed generation leaves the previous draft and saved constraints unchanged.

The single-course draft schedule response includes review context for the selected course:

- course, Cohort, lecturer, room, and study type names and IDs
- generated session date, start/end time, units, filterable planning IDs, optional source `timeWindowId`, and `constraintWindowIndex`
- non-blocking `validationAlerts` on each session, including alert code, message, and related conflicting sessions for overlap alerts

The semester-scoped draft schedule endpoint returns all generated schedules for the selected semester so the planner UI can power the Courses overview filters.

Manual Draft Session editing is available through `PATCH /api/draft-sessions/{session_id}`. The request body accepts `date`, `startTime`, `endTime`, and `roomId`; a successful edit returns the refreshed parent Draft Schedule so the Courses overview can replace its saved schedule data. The endpoint rejects out-of-semester dates, end times that are not after start times, duplicate session dates within the same Draft Schedule, missing rooms, and rooms whose capacity is below the session Cohort size. Room occupancy conflicts are reported as non-blocking validation alerts after save; public holidays, exams, dashboard alerts, and source planning-record edits remain deferred to later slices.

Conflict detection adds non-blocking validation alerts to generated Draft Sessions returned by generation, single-course reads, semester overview reads, and manual edit responses. Alerts are derived at read time from the selected-semester schedule set and planning data. They currently cover lecturer, room, and Cohort overlaps; room capacity violations; sessions outside the currently active course-semester generation constraints; sessions outside Study Type Time Windows when no custom active generation constraints exist; and missing validation reference data. Alerts never block generation or otherwise valid manual edits.

## Multi-Course Generation

Multi-course generation is a two-step operation. Preparation validates an ordered `initial` selection of 2-50 distinct Course IDs or a `retry` selection of 1-50 IDs, returns canonical Course availability, and snapshots any same-semester Draft Schedule IDs and revisions. Preparation is read-only. Execution submits those immutable snapshots and requires explicit replacement confirmation whenever a prepared same-semester schedule exists.

Every available Course is generated independently with its own saved Course-Semester constraint set or normalized Semester and Study Type defaults. Expected Course failures produce ordered, course-local outcomes and do not prevent other valid Courses from being saved. Failed Courses keep their existing Draft Schedule, manual edits, and saved constraints. Successful replacements increment the Draft Schedule revision and never affect the same Course in another Semester.

Execution uses one outer transaction and a nested savepoint per successful Course candidate. Repository mutation helpers flush but do not commit; API boundaries own commit and rollback. Changed Draft Schedule or active constraint snapshots return stale Course failures. Any unexpected orchestration or persistence exception rolls back the complete attempt and returns `BATCH_OPERATION_FAILED` without uncommitted success outcomes. Batch results and retry sets are response/UI state only and are not persisted.

## Migrations

Migration scripts live in `backend/app/db/migrations/`. Migration `0002_course_semester_drafts` backfills optimistic revisions and changes Draft Schedule identity from Course-only to the `(course_id, semester_id)` pair using SQLite-compatible table recreation.

At application startup, the backend creates a new database schema when needed and applies the supported pre-Slice-6 to Slice-6 upgrade automatically. Existing Draft Schedules, sessions, generation constraints, and manual edits are retained. If a database is in an unknown partially migrated state, startup stops with an actionable error instead of silently modifying it.

Migration `0003_academic_catalog_administration` adds lifecycle state, optimistic revisions, canonical normalized names, each Course's current Semester assignment, and immutable academic snapshots on saved Draft Schedules. Supported legacy name collisions remain visible with `nameRepairRequired`; they must be uniquely renamed before edit or reactivation. A legacy Course assignment is inferred only when one saved Semester is unambiguous. Unknown partial schemas still stop startup with a diagnostic.

## Academic Data Administration

Planner users can maintain Semesters, Cohorts, Courses, Study Types, and nested Study Type Time Windows through `/api/academic`. Each named collection supports paginated list, create, detail, revisioned patch, usage, archive/reactivate, and protected permanent deletion. Time Window item operations use `/api/academic/time-windows/{recordId}`. Validation and conflict responses use an `errors` array with stable codes, field names, and metadata.

Usage is rechecked atomically before deletion. Course and required dependent references, generation constraints, and immutable saved-schedule references prevent destructive deletion. Archive/reactivate never cascades to dependent records. Lecturer and Room records remain read-only planning options in this slice; they are selectable when creating or editing a Course but are not administered by these endpoints.

Planning options accept an optional `semesterId`, return active academic chains, include Lecturer/Room options, and retain an otherwise eligible Course without an active Study Type Time Window as unavailable with `MISSING_ACTIVE_TIME_WINDOW`. Generation additionally verifies the Course's current Semester assignment and academic lifecycle state.

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
Seeded academic names are canonicalized, lifecycle fields remain valid, and every seeded Course is assigned to Fall 2026.
