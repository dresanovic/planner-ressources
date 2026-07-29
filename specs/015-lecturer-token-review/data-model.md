# FS-015 Data Model

## Model boundary

FS-015 adds link, feedback, activity, and short-lived misuse-state records
without changing FS-013 revision ownership or the existing schedule schema.
`ScheduleRevision.id` and `Lecturer.id` are the stable scope identities. A
current scheduled occurrence is identified by the pair
`(session_kind, source_session_id)` because teaching and exam IDs may overlap.

The current product assigns one lecturer to each teaching or exam session.
Courses may have several eligible lecturers, but multi-lecturer assignment of
one session is outside this model.

## Entity: LecturerReviewLink

One durable record for each issued or replacement credential.

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Primary key; safe internal identifier |
| `schedule_revision_id` | integer | Required FK to `schedule_revisions.id`; immutable |
| `lecturer_id` | integer | Required FK to `lecturers.id`; immutable |
| `intended_lecturer_name` | string(200) | Required issue-time display snapshot; not an authentication claim |
| `secret_digest` | char(64) | Required unique SHA-256 hex digest; never returned |
| `duration_days` | integer | Required; one of `1`, `2`, `3` |
| `issued_at` | UTC datetime | Required |
| `expires_at` | UTC datetime | Required; exactly `issued_at + duration_days × 24 hours` |
| `status` | enum string | `active`, `expired`, `revoked`, `replaced`, or `revision_ended` |
| `ended_at` | UTC datetime/null | Null only while active; expiry uses the exact expiry instant |
| `end_reason` | enum string/null | `expired`, `revoked`, `replaced`, `abandoned`, or `superseded` |
| `replaced_by_id` | integer/null | Self-FK to the successful replacement |
| `access_blocked_until` | UTC datetime/null | Valid-link view throttle only; never changes expiry |

### Constraints and indexes

- Unique `secret_digest`.
- Partial unique index on `(schedule_revision_id, lecturer_id)` where
  `status = 'active'`.
- `expires_at > issued_at`.
- `duration_days IN (1, 2, 3)`.
- Active rows have null `ended_at`, `end_reason`, and `replaced_by_id`.
- Ended rows have non-null `ended_at` and matching `end_reason`.
- `replaced_by_id` is present only for `status = 'replaced'`.
- Indexes support revision/lecturer history, status/expiry inspection, and
  digest lookup.
- Links are retained with revision history and are never cascade-deleted
  independently by FS-015.

### Effective validity

A record is usable only when all conditions are true at the authoritative
request check:

1. `status = active`;
2. current UTC time is strictly before `expires_at`;
3. the revision is Draft or Ready for review in the active Working slot, or is
   the Current Published revision;
4. the link has never been terminalized by abandonment or supersession; and
5. the applicable misuse limit is not active.

An empty current assignment projection does not end an otherwise valid link.
The persisted status may be materialized as `expired` when expiry is observed,
but validity always uses the time comparison and never waits for that write.

### State transitions

```text
                exact expiry
              +--------------> expired
              |
active -------+--------------> revoked
              |
              +--------------> replaced ----> points to new active link
              |
              +--------------> revision_ended
                                 reason: abandoned | superseded
```

- No ended state returns to `active`.
- Publishing the bound Working revision as Current Published is not a link
  transition.
- Restoring an abandoned revision does not reactivate a
  `revision_ended` link.
- Replacement terminalizes all earlier active rows for the pair and creates
  exactly one new active row in the same transaction.

## Entity: LecturerReviewFeedback

One immutable advisory item. A deliberate repeated submission creates another
record; a retry of the same logical submission does not.

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Primary key |
| `review_link_id` | integer | Required FK to `lecturer_review_links.id`; immutable |
| `kind` | enum string | `revision_comment`, `session_comment`, or `impossible_session` |
| `session_kind` | enum string/null | `teaching` or `exam` for session-specific items |
| `source_session_id` | integer/null | Stable source ID within the bound revision |
| `comment_text` | text/null | Trimmed plain text; required for comment kinds, optional for impossible flag |
| `session_context` | JSON/null | Required minimum submission-time snapshot for session-specific items |
| `client_submission_id` | UUID string | Required logical browser submission identity |
| `request_fingerprint` | char(64) | SHA-256 of the canonical accepted request, excluding the bearer secret |
| `submitted_at` | UTC datetime | Required authoritative acceptance time |

### Constraints and validation

- Unique `(review_link_id, client_submission_id)`.
- `revision_comment` has no session fields and requires a non-blank comment.
- `session_comment` requires both session identity fields, a session context,
  and a non-blank comment.
- `impossible_session` requires both session identity fields and a session
  context; its comment may be null.
- Present comment text is trimmed, contains at least one visible non-whitespace
  character, and contains no more than 2,000 characters.
- Comment content remains plain text. Markup-looking content is stored as text
  and is never interpreted as HTML.
- The link relation supplies the immutable revision ID, intended lecturer ID,
  intended lecturer display name, issuance, and expiry attribution.
- Reusing a client submission ID with the same fingerprint returns the
  existing item. Reusing it with a different fingerprint is rejected as a
  conflict and changes no record.
- No update or delete operation is exposed in this slice.

### Session context

The JSON document uses the same minimum fields as the public session contract:

```text
sessionRef
sessionKind
sourceSessionId
courseSourceId
courseCode
courseTitle
date
startTime
endTime
timeZone
roomName
cohortName
```

It contains no lecturer contact data, other lecturer identity, student data,
planner note, lifecycle history, internal finding, or token value.

## Entity: LecturerReviewActivityEvent

Append-only, privacy-safe evidence for link operations and protected requests.

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Primary key |
| `event_type` | enum string | One of the event types below |
| `review_link_id` | integer/null | Link FK when a usable internal link was resolved |
| `schedule_revision_id` | integer/null | Present when safely known |
| `lecturer_id` | integer/null | Intended lecturer when safely known |
| `feedback_id` | integer/null | Present for accepted/idempotently returned feedback |
| `reason_code` | bounded enum/null | Internal fixed code; never returned by generic public failure |
| `occurred_at` | UTC datetime | Required; indexed |

### Event types

- `link_issued`
- `link_expired`
- `link_revoked`
- `link_replaced`
- `revision_ended`
- `access_accepted`
- `access_rejected`
- `feedback_accepted`
- `feedback_rejected`
- `misuse_limit_activated`

No event field may contain a raw token, token digest, comment body, arbitrary
request/response data, schedule snapshot, header, raw network address, or
network fingerprint.

The combination of link issuance/expiry fields and events is sufficient to
verify the exact lifecycle boundary. At most one `link_expired` event is
created per link even when expiry is observed repeatedly.

## Ephemeral persisted invalid-source state

`LecturerReviewInvalidSourceState` is short-lived security state rather than a
retained domain-history entity.

| Field | Type | Rules |
|---|---|---|
| `source_fingerprint` | char(64) | Primary key; lowercase SHA-256 HMAC hex of the authoritative client address |
| `attempt_timestamps` | JSON array of UTC datetimes | Required; ordered oldest to newest; contains at most 20 entries and only attempts in the current rolling five-minute window |
| `blocked_until` | UTC datetime/null | Null when not blocked; once set by the 20-attempt boundary, cannot be shortened |
| `last_relevant_at` | UTC datetime | Required; latest unusable or blocked request used to enforce retention |

An index on `last_relevant_at` supports bounded cleanup. Per-source updates,
including pruning expired timestamps, recording the next attempt, and
activating a block, occur atomically in one database transaction.

Raw network identifiers are never stored. The HMAC secret contains at least 256
bits of random key material, is supplied through protected deployment
configuration, and remains stable across application restarts. State changes
are atomic per source. A one-minute cleanup physically removes each record no
later than 15 minutes after its latest relevant attempt, but never while
`blocked_until` is still in the future. The record is never retained as
lecturer feedback or activity history.

`request.client.host` is the only address value consumed by feature code. It is
authoritative because the trusted gateway removes caller forwarding headers,
sets the client address, and is the only backend peer accepted by Uvicorn's
restricted proxy-header trust configuration. The feature service never reads
`Forwarded` or `X-Forwarded-*` directly.

## External gateway boundary

The gateway is not a persisted entity, but it is part of the security model:

- Anonymous traffic may reach only the public review shell and the two fixed
  public review API operations.
- Planner page entry points and every non-public API operation require the
  gateway's existing planner authorization.
- The backend listener is not directly publicly reachable.
- The gateway discards caller `Forwarded`/`X-Forwarded-*` values and writes one
  authoritative client address.
- Uvicorn accepts proxy headers only from the configured gateway address or
  bounded gateway network, never from a wildcard peer set.

These statements are validated as deployment behavior rather than represented
by database rows.

## Existing entity relationships

```text
ScheduleRevision 1 --- * LecturerReviewLink * --- 1 Lecturer
                               |
                               +--- * LecturerReviewFeedback
                               |
                               +--- * LecturerReviewActivityEvent

LecturerReviewLink 0..1 --- replaced_by ---> 1 LecturerReviewLink
```

- `ScheduleRevision` owns the lifecycle and content semantics.
- `Lecturer` owns the stable intended identity.
- The link anchors retained feedback even after it ends.
- Link deletion is not a FS-015 operation.

## Projection model

The public schedule is computed, not persisted as another aggregate:

- **Working Draft/Ready**: query current `DraftSession` and `ExamSession` rows
  in the revision's semester and filter by the bound `lecturer_id`.
- **Current Published**: read the bound revision's FS-013 snapshot and filter
  teaching/exam entries by the bound lecturer source ID.
- **Abandoned/Superseded/Historical**: return the generic unavailable result.

Group the complete result by course. Use `COURSE-{sourceCourseId}` as the stable
display code because the existing Course model has no institution code. An
empty filtered set returns a valid explicit empty schedule. Any incomplete or
unconfirmable projection fails closed and returns no partial public data.

## Planner feedback read model

The planner overview is a query result, not a persisted aggregate:

- revision identity and lifecycle state;
- lecturer eligibility/assignment summaries supplied by the server;
- non-secret link histories and effective statuses;
- `feedbackAvailability`: `complete`, `partial`, or `unavailable`;
- total feedback items;
- exact impossible flag-item count only when complete;
- feedback grouped by revision and session;
- distinct flagged session groups, each with its flag-item count;
- captured submission context;
- an optional authoritative current `occurrenceRef` when the existing planner
  session workflow can still open the session.

The client never infers completeness or treats missing data as zero.

## Transaction boundaries

### Issue

Claim semester, reload the revision/lecturer/assignments, materialize due
expiry, verify no active pair, insert link and issuance event, then commit.
Only after commit may the one-time secret be returned.

### Revoke or replace

Claim semester then link, reload, terminalize the correct row(s), append events,
and commit as one unit. Replacement inserts the new active link before commit
and returns its one-time secret only after success.

### Lifecycle end

FS-013 abandonment and publication replacement terminalize affected active
links and append `revision_ended` events in the same lifecycle transaction.

### Feedback

Resolve digest, claim semester then link, recheck expiry/lifecycle/misuse, verify
the current session assignment when applicable, capture the current permitted
context, insert feedback and activity, and commit together. A concurrent
ending or reassignment operation either happens before this authoritative
check and causes rejection or happens after the accepted feedback commit.

## Retention

- Feedback, ended link metadata, and activity evidence follow FS-013 revision
  history retention.
- Ended public links can never read retained feedback.
- FS-015 adds no independent purge, edit, resolution, or anonymization
  workflow.
- Short-lived invalid-source state is the only separately timed data and its
  database rows are physically removed within the required 15-minute bound.
