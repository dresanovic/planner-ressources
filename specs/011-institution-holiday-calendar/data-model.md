# Data Model: FS-011 Institution-Wide Holiday Calendar and Avoidance

## Entity: InstitutionHoliday

Represents one current full-day institution-wide holiday.

| Field | Meaning | Rules |
|---|---|---|
| `id` | Stable holiday identity | Positive generated integer primary key |
| `date` | Institution-local calendar date | Required valid date; unique across all current holidays |
| `name` | Planner-readable holiday name | Required after trimming; 1–200 characters; need not be unique |
| `revision` | Optimistic concurrency token | Positive integer; starts at 1 and increments on each successful edit |

Database invariants:

- Unique constraint `uq_institution_holidays_date` prevents two current holidays on the same date.
- Check constraint `ck_institution_holidays_revision_positive` requires `revision > 0`.
- Mapper-level version protection prevents a stale update/delete from overwriting a newer mutation.
- There is no `calendar_id`: all rows belong to the one logical institution calendar.
- There is no `is_active`, deleted flag, provider identity, source, timestamp, or history relationship.
- There is no foreign key to Semester, DraftSchedule, or DraftSession.

Normalization and validation:

- Input dates use ISO `YYYY-MM-DD` at the interface and become date-only values.
- Valid past, future, and leap-day dates are accepted.
- Surrounding name whitespace is removed before validation/storage.
- Blank/whitespace-only names and names longer than 200 characters are rejected.
- Names may repeat on different dates. If several observances share one date, the planner stores one combined readable name.

## Derived Aggregate: InstitutionHolidayCalendar

The single institution-wide calendar is not stored as its own row. It is the canonical ordered set of current InstitutionHoliday records.

| Derived property | Meaning |
|---|---|
| `holidays` | All current rows ordered by `date`, then `id` |
| `by_date` | Date-keyed lookup used by generation and validation |
| `snapshot` | Canonical ordered tuples `(id, date, name, revision)` for stale detection |

Rules:

- List administration returns the complete current set at the accepted 50-record scale.
- Generation and semester review may query only their inclusive relevant date range.
- The aggregate contains current state only. Editing/removing a row leaves no prior aggregate member.
- Snapshot comparison is derived; no calendar-version row or snapshot table is stored.

## Derived Value: HolidayReference

Carries verifiable holiday context in generation failures and blocking reasons.

| Field | Meaning |
|---|---|
| `holidayDate` | Substantiated holiday's ISO date |
| `holidayName` | Current readable name for that date |

Rules:

- Both values are present together only for `INSTITUTION_HOLIDAY` evidence.
- One reason item represents one relevant holiday.
- Several items with the same code are distinguished and deduplicated by date.
- A holiday is substantiated only when it lies inside the active planning period, matches an allowed teaching weekday/window, and removed an otherwise considered placement for remaining units.
- If a maintained holiday also appears in FS-010 caller-supplied unavailable dates, it produces one named holiday reason rather than duplicate generic and named reasons.

## Derived Value: HolidayCalendarSnapshot

Represents the exact relevant holiday input observed by a generation operation; it is not persisted separately.

| Field | Meaning |
|---|---|
| `range_start` | Inclusive earliest date relevant to the operation/course |
| `range_end` | Inclusive latest date relevant to the operation/course |
| `entries` | Canonical `(id, date, name, revision)` tuples in the range |
| `token` | Opaque deterministic fingerprint used by existing stale-input boundaries |

Rules:

- Add, delete, redate, rename, or revision change affects the relevant snapshot.
- FS-010 includes this state in existing shared/per-course opaque snapshot tokens; it is not exposed as a holiday list in optimization requests.
- Single and legacy multi-course generation reload current holidays within their persistence boundary and validate exact results before replacement.
- A result containing a newly generated session on a current holiday cannot be saved.
- Existing schedule rows remain unchanged on stale/failure outcomes.

## Existing Entity: DraftSession

No stored fields or relationships are added.

FS-011 rules:

- `date` is matched against the current InstitutionHolidayCalendar during validation.
- A current matching holiday produces a derived `INSTITUTION_HOLIDAY` alert.
- Generated, manually created, and manually edited sessions use the same alert rule.
- A holiday mutation never changes the session's date, time, resources, cohort, units, or existence.
- A session saved on a holiday remains valid under manual structural rules and is flagged rather than blocked.

## Derived Value: HolidayValidationAlert

Uses the existing ValidationAlert response shape.

| Existing field | FS-011 value |
|---|---|
| `code` | `INSTITUTION_HOLIDAY` |
| `message` | Readable text containing current holiday name and ISO date |
| `relatedSessions` | Empty list |

The alert is recomputed when schedules are loaded. It is neither persisted nor copied into a session.

## Modified Generation Models

### Single-course ScheduleGenerationResult

- Accepts the current named holiday map as an input.
- Excludes holiday dates in both placement and feasibility/failure analysis.
- Retains existing all-or-nothing success/failure behavior.
- May return several `INSTITUTION_HOLIDAY` GenerationFailure items, each with `holidayDate` and `holidayName`, alongside the established primary failure.

### Legacy CourseGenerationOutcome

- Retains existing `succeeded`/`failed` statuses and replacement semantics.
- A course invalidated by a current/stale holiday retains its prior Draft Schedule and receives a holiday or `STALE_HOLIDAY_CALENDAR` error.
- Unaffected course outcomes retain current batch behavior.

### FS-010 BlockingReason

Existing fields remain:

| Field | Meaning |
|---|---|
| `code` | Stable reason category |
| `message` | Planner-readable explanation |
| `relatedCount` | Existing evidence count |

FS-011 adds optional `holidayDate` and `holidayName`. The existing caller `UNAVAILABLE_DATE` reason remains distinct and leaves both fields absent.

## State Transitions

### Create

```text
Absent date --valid create--> Current holiday (revision 1)
Absent date --duplicate/invalid create--> No change
```

### Edit

```text
Current holiday (revision N)
  --valid expected revision--> Updated current holiday (revision N+1)
  --duplicate/invalid/stale--> Unchanged current holiday
```

The former date/name is not retained as holiday history.

### Delete

```text
Current holiday --confirmed matching revision--> No holiday record
Current holiday --unconfirmed/stale--> Unchanged current holiday
```

Deletion never cascades to schedules or sessions.

## Cross-Entity Behavior

1. Holiday CRUD mutates only InstitutionHoliday rows.
2. Generation queries current holidays and treats their dates as hard exclusions for new candidates.
3. Schedule response construction queries current holidays and derives alerts for matching saved sessions.
4. Client review reloads the selected semester after successful holiday CRUD and receives newly derived alerts.
5. No reverse relationship or background update is required.

## Migration 0005

Upgrade from the recognized current FS-008-through-FS-010 schema:

1. Create `institution_holidays` with `id`, `date`, `name`, and `revision`.
2. Add the unique-date and positive-revision constraints.
3. Perform no backfill because no earlier holiday source exists.
4. Verify every existing academic/resource/schedule table and row remains unchanged.
5. Recognize the new table and constraints as current schema head.

Clean databases are created directly from current model metadata. Downgrade removes only `institution_holidays`; it does not touch sessions or other planning data.
