# Resource Planner Backend

FastAPI backend for the resource planner.

## Resource Eligibility and Availability (FS-008)

Planner-maintained Lecturers and Rooms have stable reference codes, active/inactive lifecycle state, optimistic revisions, and protected deletion. Resource endpoints under `/api/resources` provide catalog CRUD, usage-aware removal/reactivation, and nested recurring or dated unavailability CRUD. Course eligibility is maintained atomically through `GET` and `PUT /api/academic/courses/{courseId}/resource-eligibility`.

Each active Course can have multiple eligible Lecturers and Rooms. Room capacity is a hard generation/edit rule. Cohort growth removes newly insufficient Room relationships and reports affected Courses without changing saved Draft Sessions; shrinking a Room preserves the relationship so current validation can show the impact. Existing assignments also remain unchanged when eligibility, availability, or lifecycle changes.

Single- and multi-Course generation load active eligible resources, reject unavailable or undersized candidates, assign exactly one Lecturer and Room per session, and deterministically minimize Lecturer and Room transitions within each Course. Reference code then resource ID resolves equal choices. The batch workflow continues to generate Courses independently: FS-008 does not perform cross-Course conflict optimization, ranking, quotas, holidays, exams, authentication, or external synchronization.

Draft Session responses include coded per-session Lecturer/Room identities and separate eligibility, availability, and capacity alerts. `PATCH /api/draft-sessions/{sessionId}` accepts `lecturerId` and `roomId`; a changed assignment must currently be valid, while an unchanged legacy-invalid assignment can be retained and remains visible through validation.

## Setup

### Local SQLite backup and restore

From the repository root, create a consistent, integrity-checked backup:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/backup_sqlite_db.py --database C:/Codex/planner-resource/backend/planner.db --output-dir C:/Codex/planner-resource/backend/backups
```

Keep local and downloaded backups in `backend/backups`. Preview a restore:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/restore_sqlite_db.py --backup backend/backups/planner-20261103-125742.db --database C:/Codex/planner-resource/backend/planner.db
```

Stop every backend or other process using the target database before applying:

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/restore_sqlite_db.py --backup backend/backups/planner-20261103-125742.db --database C:/Codex/planner-resource/backend/planner.db --apply --backend-stopped
```

The restore validates the SQLite backup and planner tables, prepares a standalone
candidate, saves the previous database in a unique `backend/backups/before-restore-*`
directory, and replaces the target atomically. The source backup stays unchanged.
Without `--apply`, no files change. `--backend-stopped` is your confirmation of an
offline restore: a lock check cannot detect every idle application connection.
Existing WAL, SHM, or journal files cause an abort; stop the backend cleanly and
resolve SQLite state rather than deleting files that may contain unsaved data.
Restart the backend after success and verify login and semester data. Accounts,
passwords, sessions, and links revert to their state in the backup as well.

Both scripts default to `DATABASE_URL`, or to `backend/planner.db` when it is
unset. The application itself defaults to `./planner.db` relative to its startup
directory, so prefer the explicit absolute database path shown above. For another
checkout, adjust that path. Restore supports local SQLite files only and does not
start or stop the application automatically.

Run restore checks with Python's standard library:

```powershell
.\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests/scripts -p test_restore_sqlite_db.py
```

Install the development and test dependencies from `backend/requirements.txt`.

```text
pip install -r requirements.txt
```

Production container builds install only `requirements-runtime.txt`; test
clients and pytest are deliberately excluded from the final image.

The first implementation slice uses SQLite through SQLAlchemy. By default, the backend reads and writes `planner.db` in the backend working directory:

```text
DATABASE_URL=sqlite:///./planner.db
```

Set `DATABASE_URL` to a different SQLAlchemy URL when running against another database. The current model layer is SQLAlchemy-based so the same feature code can later move to PostgreSQL with migrations instead of a rewrite.

## Planner authentication and first setup (FS-016)

All planner pages, API reads, and mutations require an active named local
planner account. Authentication is application-owned: it does not use VPN
identity, institutional SSO, email, or another identity provider. Existing
public lecturer review, calendar, and feedback capabilities remain anonymous
and cannot authorize planner operations.

Generate a one-time bootstrap value with a cryptographically secure 32-byte
generator and pass its 64-character hexadecimal representation only at
startup:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

```text
PLANNER_BOOTSTRAP_CREDENTIAL=<64 different hexadecimal characters>
```

Open `/bootstrap/`, enter that value, and establish the first named system
administrator. Bootstrap is available only while no administrator exists and
does not sign the new administrator in automatically. Remove the redeemed
value from deployment configuration and sign in normally at `/login/`.

The sole administrator creates inactive planner accounts and manually delivers
the one-time link shown immediately after creation, reset, or reactivation.
The link expires after 24 hours, is replaced by a later issuance, and is
consumed by the first successful password setup. It is never reproduced by an
account listing. Passwords are 12–128 characters and must not equal the
case-insensitive trimmed login name.

Each account has at most one opaque server-side session. A later successful
login replaces it; a failed login does not. The non-persistent `HttpOnly`
cookie uses `SameSite=Strict`, expires after 60 minutes without deliberate
planner activity, and has a 12-hour absolute lifetime. Logout, password change
or reset, disablement, and administrator recovery invalidate it. A browser
configured to restore a prior session may restore a session cookie, so the
server timeouts remain authoritative.

For emergency recovery, generate a value different from every bootstrap value
and start once with:

```text
PLANNER_ADMIN_RECOVERY_CREDENTIAL=<64 different hexadecimal characters>
```

Open `/administrator-recovery/` and set a new password for the current sole
administrator. There is no account selector and no operator account. Recovery
consumes the startup value and ends the administrator's prior session. Remove
the redeemed value from configuration and use normal login. To rotate an
unused startup value, configure a newly generated value; the application
persists the old value as replaced. Removing an unused value does not retire
it, and a consumed or replaced value cannot be made current again by restarting
with the same value.

Production planner authentication requires HTTPS. In production the cookie is
named `__Host-planner_session` and is `Secure`; local development permits only
the exact `localhost:5173` and `127.0.0.1:5173` credentialed CORS origins, while
production permits no cross-origin planner frontend. Authentication and
protected responses use `Cache-Control: no-store`.

Accounts, password hashes, startup anti-replay records, one-time-access
digests, and current-session digests are stored in SQLite. Back up and restore
the complete database as one unit. Raw passwords and usable startup, access,
or session secrets are not recoverable from it. Treat a database restore as a
security-state restore: it also restores the recorded credential consumption
and any session that was current at backup time; disable/reset affected access
or rotate to a new startup value when that is not acceptable.

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

Generation requires existing planning data for one Course, at least one active eligible Lecturer and capacity-sufficient Room, a Cohort, Semester, Study Type, and at least one allowed teaching window. The request body includes `semesterId`, `planningPeriod`, and `allowedTeachingWindows`; each window includes `weekday`, `startTime`, `endTime`, and optional `sourceTimeWindowId`. Invalid requests return a `422` response with all detected generation errors in an `errors` array. Successful generation replaces the previous generated draft for that Course and saves the submitted constraint set for the Course-Semester pair. Failed generation leaves the previous draft and saved constraints unchanged.

The single-course draft schedule response includes review context for the selected course:

- course, Cohort, lecturer, room, and study type names and IDs
- generated session date, start/end time, units, filterable planning IDs, optional source `timeWindowId`, and `constraintWindowIndex`
- non-blocking `validationAlerts` on each session, including alert code, message, and related conflicting sessions for overlap alerts

The semester-scoped draft schedule endpoint returns all generated schedules for the selected semester so the planner UI can power the Courses overview filters.

Manual Draft Session editing is available through `PATCH /api/draft-sessions/{session_id}`. The request body accepts `date`, `startTime`, `endTime`, `lecturerId`, and `roomId`; a successful edit returns the refreshed parent Draft Schedule so the Courses overview can replace its saved schedule data. The endpoint rejects out-of-semester dates, invalid ranges, duplicate dates, and changed resource assignments that are inactive, ineligible, unavailable, or capacity-insufficient. Resource occupancy conflicts are reported as non-blocking validation alerts after save.

Conflict detection adds non-blocking validation alerts to generated Draft Sessions returned by generation, single-course reads, semester overview reads, and manual edit responses. Alerts are derived at read time from the selected-semester schedule set and planning data. They currently cover lecturer, room, and Cohort overlaps; room capacity violations; sessions outside the currently active course-semester generation constraints; sessions outside Study Type Time Windows when no custom active generation constraints exist; and missing validation reference data. Alerts never block generation or otherwise valid manual edits.

## Multi-Course Generation

Multi-course generation is a two-step operation. Preparation validates an ordered `initial` selection of 2-50 distinct Course IDs or a `retry` selection of 1-50 IDs, returns canonical Course availability, and snapshots any same-semester Draft Schedule IDs and revisions. Preparation is read-only. Execution submits those immutable snapshots and requires explicit replacement confirmation whenever a prepared same-semester schedule exists.

Every available Course is generated independently with its own saved Course-Semester constraint set or normalized Semester and Study Type defaults. Expected Course failures produce ordered, course-local outcomes and do not prevent other valid Courses from being saved. Failed Courses keep their existing Draft Schedule, manual edits, and saved constraints. Successful replacements increment the Draft Schedule revision and never affect the same Course in another Semester.

Execution uses one outer transaction and a nested savepoint per successful Course candidate. Repository mutation helpers flush but do not commit; API boundaries own commit and rollback. Changed Draft Schedule or active constraint snapshots return stale Course failures. Any unexpected orchestration or persistence exception rolls back the complete attempt and returns `BATCH_OPERATION_FAILED` without uncommitted success outcomes. Batch results and retry sets are response/UI state only and are not persisted.

## Conflict-Aware Semester Optimization (FS-010, I-004 and I-006)

Teaching optimization for one to twenty selected courses uses short authenticated operation requests. Existing independent single-course and FS-006 batch routes retain their separate behavior. The optimization endpoints are:

- `POST /api/draft-schedules/optimization/prepare`
- `POST /api/draft-schedules/optimization/operations`
- `GET /api/draft-schedules/optimization/operations/{operationId}`
- `POST /api/draft-schedules/optimization/operations/{operationId}/accept`
- `POST /api/draft-schedules/optimization/operations/{operationId}/finalize`
- `POST /api/draft-schedules/optimization/operations/{operationId}/cancel`

Preparation accepts 1–20 distinct courses in one semester's active editable Working revision and optional canonically deduplicated unavailable dates. It returns shared/per-course snapshots and the effective operator budget/fingerprint, shown before explicit start. Start captures one preparation/search deadline and returns an operation identity promptly. A spawned solver receives detached planning values and never writes schedules; passive short status polls keep the interface responsive. Unselected teaching and active exams remain fixed occupancy. Every offered candidate is independently checked against dates, windows, units/breaks, holidays/unavailable dates, eligibility/activity/availability/capacity, exam boundaries and joint lecturer/room/cohort conflicts.

Objective priorities remain total units, conflicts, weekly distribution/session size, lecturer changes, room changes, retained drafts, then canonical temporal/resource ordering. Current saved units are comparison facts; they do not impose a replacement floor. A planner may explicitly accept lower coverage for the whole selection, including replacement of manual sessions. Existing constraints, unselected/protected sessions, academic/resource records and exams retain their protections.

A hard-valid nonempty candidate lacking any required objective proof remains provisional and requires explicit operation-wide acceptance, even for new or fully covered courses. Review separates coverage, ordered preference evidence, sound unit bounds or unknown gap, and prepared-selection scope. Individual zero-unit courses remain in a nonempty joint decision. Entirely empty unproven results offer no acceptance; timeout alone is not proof of infeasibility. Fully proven wholly unplanned selections use live-client automatic finalize; existing saved sessions still require comparison and acceptance.

Accept/finalize apply the exact retained candidate without solving again, after fresh revision/input/hard-rule validation. All selected replacements/creations/deletions and the durable saved receipt commit atomically and at most once. Any relevant stale change rejects the entire candidate; there is no unaffected-course partial application. Precommit failure/cancellation preserves saved work. Cancellation after commit returns the actual saved receipt. Refresh, authentication/context loss or restart permits outcome-only reconciliation, never restored review authority. The old synchronous `/generate` and replay `/accept` routes return `409 OPERATION_API_REQUIRED`. See [the operation contract](../specs/I-006-optimization-incumbent-acceptance/contracts/optimization-operation.md) and the operator-budget section below.

Install the pinned solver runtime with `pip install -r requirements.txt`. Run focused verification from `backend/` with:

```text
python -m pytest tests/services/test_semester_optimization.py
python -m pytest tests/services/test_conflict_aware_generation.py tests/api/test_conflict_aware_generation.py
python -m pytest tests/performance/test_semester_optimization_performance.py
```

## Migrations

Migration scripts live in `backend/app/db/migrations/`. Migration `0002_course_semester_drafts` backfills optimistic revisions and changes Draft Schedule identity from Course-only to the `(course_id, semester_id)` pair using SQLite-compatible table recreation.

At application startup, the backend creates a new database schema when needed and applies the supported pre-Slice-6 to Slice-6 upgrade automatically. Existing Draft Schedules, sessions, generation constraints, and manual edits are retained. If a database is in an unknown partially migrated state, startup stops with an actionable error instead of silently modifying it.

Migration `0003_academic_catalog_administration` adds lifecycle state, optimistic revisions, canonical normalized names, each Course's current Semester assignment, and immutable academic snapshots on saved Draft Schedules. Supported legacy name collisions remain visible with `nameRepairRequired`; they must be uniquely renamed before edit or reactivation. A legacy Course assignment is inferred only when one saved Semester is unambiguous. Unknown partial schemas still stop startup with a diagnostic.

## Academic Data Administration

Planner users can maintain Semesters, Cohorts, Courses, Study Types, and nested Study Type Time Windows through `/api/academic`. Each named collection supports paginated list, create, detail, revisioned patch, usage, archive/reactivate, and protected permanent deletion. Time Window item operations use `/api/academic/time-windows/{recordId}`. Validation and conflict responses use an `errors` array with stable codes, field names, and metadata.

Usage is rechecked atomically before deletion. Course and required dependent references, generation constraints, and immutable saved-schedule references prevent destructive deletion. Archive/reactivate never cascades to dependent records. Lecturer and Room records are administered separately under `/api/resources`; Course creation establishes their initial eligibility and later eligibility changes use the Course resource endpoint.

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
## FS-009 manual Draft Session management

The planner uses three focused mutations:

- `POST /api/courses/{course_id}/draft-schedule/sessions` creates one manual Draft Session from `semesterId`, `date`, `startTime`, `endTime`, explicit whole `units`, and `roomId`.
- `DELETE /api/draft-sessions/{session_id}` deletes one session and requires `expectedDraftScheduleId` plus `expectedDraftRevision`.
- `DELETE /api/courses/{course_id}/draft-schedule` clears one course-semester draft and requires `semesterId`, `expectedDraftScheduleId`, and `expectedDraftRevision`.

Each success returns `courseId`, `semesterId`, authoritative `scheduledUnits`, authoritative `remainingUnits`, and a nullable `draftSchedule`. Remaining units are derived from the current Course total minus saved Draft Session units and are never persisted. Deleting the last session or clearing the draft returns `draftSchedule: null`.

Manual creation accepts explicit `lecturerId`, `cohortId`, and `roomId` values and returns structured `422` errors for date, time, whole-unit, remaining-unit, duplicate-date, and selected-Cohort room-capacity rules. A missing or inactive selected source record returns `404`. Confirmed deletions return `409 STALE_DRAFT` when the target, parent identity, or revision no longer matches; no deletion occurs and the client must refresh and obtain a new confirmation.

All mutations preserve Course, Semester, Lecturer, Room, Cohort, Study Type, and saved Generation Constraint Set records. Manual creation defaults Lecturer, Cohort, and Room from the Course in the planner UI, persists any active-record overrides only on the new session, accepts active Rooms that are capacity-valid for the selected Cohort, and retains established non-blocking validation alerts.
# Teaching optimization time policy

Teaching generation uses short operation requests and a separate solver process.
The operator may set `TEACHING_OPTIMIZATION_POLICY_FILE` to a JSON file containing
`defaultSeconds` and `ceilingSeconds`. Missing keys use 300 and 1800 respectively;
an unset path uses both defaults. Values must be finite positive whole seconds,
excluding strings and booleans, with default no greater than ceiling. Unknown or
duplicate keys, malformed/unreadable files, and invalid values block new
preparation with `OPTIMIZATION_CONFIGURATION_INVALID`; unrelated health/startup
remains available. Correct the file and prepare again; no rebuild is required.

Copy `config/optimization/policy.example.json` to an operator-owned `policy.json`.
For containers, mount host `./config/optimization` read-only at
`/config/optimization`, and set the policy path to
`/config/optimization/policy.json`. Mount the directory, never the individual
file: replacing a single-file mount can leave the container reading its old inode.
Write the replacement beside the original, then atomically rename it over
`policy.json` on the host filesystem (for example Python `os.replace`). The next
preparation reads the new values while a running operation retains its captured
budget. A change between preparation and start requires preparation again.

The planner has no per-run budget override or configuration editor. More time
does not guarantee a better result; reducing the selected courses is another
recovery option. Keep the supported single application process/SQLite deployment;
this operation registry is not a distributed queue. A restart interrupts live
work and review; outcome receipts preserve committed saves without restoring
candidate authority. Use isolated databases for acceptance trials.

