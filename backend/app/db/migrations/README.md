# Alembic migrations

This directory is reserved for Alembic migration scripts. The first implementation uses
SQLAlchemy metadata for local test setup and keeps migration-ready model definitions in
`backend/app/models/planning.py`.

## FS-014 calendar workspace

Migration `0008_calendar_workspace_outcomes.py` adds revision-scoped retained
planning outcomes. The unique `(schedule_revision_id, course_id,
operation_kind)` key stores only the newest reliable completion for that
context; request validation, confirmation cancellation, and unclassified
operation failures do not fabricate outcome rows. Foreign keys remove outcomes
with their revision or course.

New publications use schedule snapshot schema version 2. Each captured course
includes the effective planning period and teaching-window constraint profile
used at publication. Version 1 snapshots remain readable; readers report an
affected validation category as unavailable when its required captured context
does not exist instead of borrowing mutable Working constraints.

The calendar workspace is a read-only endpoint:

```text
GET /api/semesters/{semester_id}/calendar-workspace
GET /api/semesters/{semester_id}/calendar-workspace?revisionId={revision_id}
```

With no explicit revision it selects Active Working first, then Current
Published. Explicit selection accepts only those two contexts and never blends
their courses, occurrences, outcomes, findings, or summaries.
