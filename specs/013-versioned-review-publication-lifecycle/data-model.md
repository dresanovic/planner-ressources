# Data Model: FS-013 Versioned Review and Publication Lifecycle

## Model boundary

FS-013 versions the complete teaching and exam schedule for one semester. It adds revision identity and lifecycle history around the existing mutable scheduling rows. It does not version academic catalog records, generation constraints, exam configurations, authentication actors, lecturer feedback, or external publication state.

The model has three layers:

1. `ScheduleRevision` identifies one semester revision and its current lifecycle authority.
2. Existing `DraftSchedule`/`DraftSession` and `ExamSession` rows form the one mutable live materialization when a revision is Draft or Ready for review.
3. An inactive revision retains one canonical `SemesterScheduleSnapshot` document, while `ScheduleRevisionEvent` retains every lifecycle transition independently of schedule edits.

## Persisted entities

### ScheduleRevision

Represents one stable version identity within a semester.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `id` | integer | Yes | Stable primary identity; never reused; future feedback may associate to it. |
| `semester_id` | integer reference | Yes | References the owning semester. |
| `revision_number` | positive integer | Yes | Monotonic within the semester; unique with `semester_id`. |
| `state` | enum | Yes | `draft`, `ready_for_review`, `published`, `superseded`, or `abandoned`. |
| `origin_revision_id` | integer reference | No | Revision whose content was copied when this revision began; normally the then-current publication. Must not reference itself and must belong to the same semester. |
| `row_version` | positive integer | Yes | Optimistic transition version, distinct from the business-facing `revision_number`; increments once for each completed state or snapshot change. |
| `snapshot_schema_version` | positive integer | No | Required when `snapshot_document` exists; initial value `1`. |
| `snapshot_document` | JSON document | No | Canonical inactive content. Required for Published, superseded, and abandoned states. Not authoritative while the revision is active Draft or Ready. |
| `created_at` | UTC timestamp | Yes | Time the revision identity was created. |
| `state_changed_at` | UTC timestamp | Yes | Time of the most recent completed lifecycle transition. |
| `published_at` | UTC timestamp | No | First successful publication time; required for Published and superseded states and never changed afterward. |
| `updated_at` | UTC timestamp | Yes | Last metadata/snapshot update time. |

#### Database constraints and indexes

- Unique `(semester_id, revision_number)`.
- Check `revision_number > 0` and `row_version > 0`.
- Check `state` is one of the five approved values.
- Partial unique index on `semester_id` where `state IN ('draft', 'ready_for_review')`.
- Partial unique index on `semester_id` where `state = 'published'`.
- Published and superseded rows require `published_at` and a snapshot document.
- Abandoned rows require a snapshot document and no publication time unless a future spec changes the lifecycle; under FS-013 an already published revision cannot become abandoned.
- Draft and Ready rows have no publication time. Any retained inactive checkpoint in an active row is non-authoritative and is cleared after successful materialization.
- `origin_revision_id` is immutable after creation. Same-semester origin is enforced in the service because a simple self-reference does not prove equal semester IDs.

### ScheduleRevisionEvent

Represents one completed lifecycle action. It does not record teaching/exam field edits.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `id` | integer | Yes | Primary identity. |
| `semester_id` | integer reference | Yes | Denormalized owner used for stable semester ordering. |
| `schedule_revision_id` | integer reference | Yes | Revision affected by the event. |
| `event_sequence` | positive integer | Yes | Monotonic within the semester; unique with `semester_id`. |
| `event_type` | enum | Yes | `created`, `marked_ready`, `returned_to_draft`, `published`, `superseded`, `abandoned`, or `restored`. |
| `from_state` | enum/null | No | Null only for `created`; otherwise the state before the transition. |
| `to_state` | enum | Yes | Resulting state for the affected revision. |
| `occurred_at` | UTC timestamp | Yes | Completed transition time. |

#### Event rules

- Events are append-only.
- Unique `(semester_id, event_sequence)` supplies one deterministic history order even when replacement publication adds events for two revisions in one transaction.
- A replacement publication appends `superseded` for the former current publication immediately before `published` for the successor in the same transaction; no other lifecycle event may be sequenced between them.
- Rejected, cancelled, stale, failed, rolled-back, or duplicate requests append no event.
- No actor field is stored because authentication and attributable audit are outside FS-013.

#### Timestamp semantics

- Persist every lifecycle timestamp as a UTC instant.
- Serialize API timestamps as RFC 3339 values with an explicit offset.
- Render planner-facing lifecycle and publication times in Europe/Vienna with both a machine-readable value and an explicit visible timezone indication.
- Compare and order lifecycle timestamps by their instants; daylight-saving offset changes do not alter event-sequence authority.

## Existing live schedule materialization

The following existing records remain structurally unchanged and represent only the content currently loaded into the semester workspace:

- `DraftSchedule` and `DraftSession` for teaching schedule content.
- `ExamSession` for saved exam occurrences.
- Existing per-row `revision` values continue protecting row-level edits; they are not semester revision numbers.

### Workspace authority rules

- When one ScheduleRevision is Draft or Ready for review, live rows are its authoritative mutable content.
- When no active working revision exists, live rows may remain as a locked mirror of the last Published or abandoned materialization. Existing read paths must not label that mirror as an editable draft.
- Every teaching or exam session mutation verifies an active working revision for that semester before changing live rows.
- Every teaching or exam occurrence mutation carries the intended `scheduleRevisionId`; the service rejects an ID that is no longer the semester's active working revision. Existing draft/exam row revisions and material snapshot tokens remain in force.
- Ready for review remains editable and does not automatically return to Draft.
- Generation constraints and exam configurations remain current planning inputs. They are not part of the immutable publication, though their scheduled exam results are.
- Restoring or starting from a snapshot restores scheduled exam occurrences, not an earlier exam-configuration definition. Any FS-012 consumed/current marker derived from the presence of a restored active exam is reconciled without rolling back the planner's current configuration values.

## Canonical inactive snapshot document

`SemesterScheduleSnapshot` is serialized with deterministic object keys and stable array ordering before token generation. The exact HTTP representation is defined in [contracts/schedule-lifecycle.openapi.yaml](contracts/schedule-lifecycle.openapi.yaml).

```text
SemesterScheduleSnapshot
|-- schemaVersion
|-- capturedAt
|-- semester
|   |-- sourceId
|   |-- name
|   |-- startDate
|   `-- endDate
|-- courses[]                         # ordered by stable course identity
|   |-- sourceCourseId
|   |-- name
|   |-- cohort { sourceId, name, size }
|   |-- studyType { sourceId, name }
|   |-- totalUnits
|   |-- scheduledUnits
|   |-- remainingUnits
|   |-- draftStatus
|   `-- teachingSessions[]            # date, time, then stable source ID
|       |-- sourceSessionId
|       |-- date, startTime, endTime, units
|       |-- time-window context
|       |-- lecturer { sourceId, name, referenceCode }
|       |-- room { sourceId, name, referenceCode, capacity }
|       `-- capturedValidationAlerts[]
|-- examSessions[]                    # date, time, then stable source ID
|   |-- sourceExamId
|   |-- course/cohort/lecturer/room captured context
|   |-- date, startTime, endTime, source
|   |-- configuration identifier/revision and exam details
|   |-- recommendation and final-teaching context
|   `-- capturedValidityIssues[]
`-- capturedConditions[]              # publication/abandon decision context
```

### Snapshot content rules

- All display labels and resource reference codes are values, not live joins.
- Source IDs remain historical references used for course projection and possible restore; they do not control published display text.
- Every scheduled teaching and exam occurrence in the semester is included, including past FS-012 exam sessions retained for that semester.
- Every relevant semester course is included even when it has zero teaching sessions, so the snapshot retains total, scheduled, and remaining units.
- Teaching validation alerts and exam validity/recommendation issues are captured as the conditions known at the transition time. They remain descriptive and non-blocking.
- Generation constraints and exam configuration definitions are excluded. Their scheduled results and any enabled-but-unscheduled exam condition are represented without publishing the mutable configuration.
- Snapshot arrays use canonical stable ordering so repeated capture of identical content produces the same material token.
- Published and superseded snapshot documents are immutable. An abandoned snapshot may be consumed by restore; if that restored revision is abandoned again, its snapshot is replaced with the newly saved content in the new completed transition.

## Transient models

### ScheduleLifecycleOverview

Authoritative read model for one semester:

- Semester identity and current captured name.
- Opaque `state_token` representing all revision identities, states, row versions, and current/working designations.
- Active working revision summary or null.
- Current publication summary or null.
- Ordered summaries for every revision, each with its lifecycle events.
- Allowed action indicators derived from current state.
- Whether unversioned existing content needs an initial Draft (migration normally resolves existing content).

The overview contains history metadata only; historical snapshot bodies are loaded separately.

### PublicationPreparation

Server-derived decision context for one active Draft or Ready revision:

- Preparation token.
- Semester and target revision identity/state/row version.
- Current publication identity or null.
- Consequence: `first_publication` or `replacement_publication`.
- Course total, scheduled, and remaining-unit summary.
- Count and details of teaching validation alerts.
- Enabled-but-unscheduled exam conditions.
- Saved exam validity and recommendation conditions.
- Captured-context summary.
- Preparation time.

All listed conditions are non-blocking. Confirmation is still required.

### State token

Opaque digest over canonical lifecycle authority:

- Semester ID.
- Every revision ID, state, revision number, and row version.
- Current publication and active working IDs.
- Latest semester event sequence.

It detects lifecycle changes but does not replace the publication token's material-content coverage.

### Publication token

Opaque digest over:

- State-token inputs.
- Target working revision ID/row version/state.
- Current publication ID/row version if present.
- Canonical live teaching and exam content, including row revisions.
- Captured semester/course/cohort/study-type/resource labels and references.
- Publication conditions returned to the planner.

Feedback is deliberately absent from the token because later feedback never blocks publication.

## Relationships

```text
Semester 1 ---- * ScheduleRevision
ScheduleRevision 0..1 ---- * successor ScheduleRevision (origin)
ScheduleRevision 1 ---- * ScheduleRevisionEvent

Semester 1 ---- * DraftSchedule ---- * DraftSession       (live materialization)
Semester 1 ---- * ExamSession                              (live materialization)

Inactive ScheduleRevision 1 ---- 1 SemesterScheduleSnapshot document
```

The live materialization has a logical, state-controlled relationship to the one active revision rather than a new foreign key. The lifecycle service is the sole authority that maps live content to revision identity and guards mutation.

## Lifecycle transitions

| From | Action | To | Content behavior | Required safeguards |
| --- | --- | --- | --- | --- |
| None | Establish initial working revision | Draft | Adopt current live semester content; migration does this for existing populated semesters. | No active working revision; allocate next revision number; append `created`. |
| Published current, no working | Start successor | New Draft | Replace live mirror from current Published snapshot; origin points to publication. | Expected state token; no active working; source snapshot materializable; append `created`. |
| Draft | Mark ready | Ready for review | Live content unchanged and remains editable. | Expected row version and state token; append `marked_ready`. |
| Ready for review | Return to Draft | Draft | Live content unchanged. | Expected row version and state token; append `returned_to_draft`. |
| Draft or Ready | Prepare publication | Same | No write; return conditions and publication token. | Current material and context read consistently. |
| Draft or Ready | Confirm first publication | Published | Capture immutable snapshot; live rows become locked mirror. | Confirmation, expected versions/tokens; append `published`; one transaction. |
| Draft or Ready with prior current publication | Confirm replacement | Published; prior becomes superseded | Capture successor snapshot; supersede old current atomically; live rows become locked mirror. | Confirmation, expected versions/tokens; append both events in one transaction. |
| Draft or Ready | Abandon | Abandoned | Capture saved live content; live rows become locked. Current publication, if any, is untouched. | Explicit confirmation; expected versions/tokens; append `abandoned`. |
| Abandoned | Restore | Draft | Replace live materialization from the abandoned snapshot; clear its inactive authority after success. | No other active working; expected versions/tokens; referenced inputs materializable; append `restored`. |
| Published or superseded | Any edit/restore/state reversal | Rejected | No content/state/event change. | Return structured current state. |

## Transaction and concurrency rules

- State mutations claim the semester write boundary using the established backend convention, then re-read revision and live content inside the transaction.
- Compare-and-set includes revision ID, expected `row_version`, allowed source state, and relevant token.
- Partial unique indexes remain the final authority for competing create/restore and publication operations.
- Replacement publication captures the new snapshot, supersedes the old current publication, publishes the target, appends both events, and increments affected row versions in one commit.
- Any exception or stale/integrity failure rolls back snapshot, state, and events together.
- Repeated completed actions either return authoritative already-achieved state without a new event when safely identifiable or return stale/invalid transition; they never duplicate revisions or events.
- File-backed SQLite tests with independent sessions verify race behavior; in-memory shared-session tests are insufficient for concurrency evidence.

## Validation rules

### Revision creation

- Semester exists.
- No active Draft/Ready revision exists.
- If a current publication exists, successor content comes from that publication automatically.
- If no current publication exists, initial content is the existing live semester materialization, which may be empty.
- Next revision number and event sequence are allocated inside the semester write boundary.

### State transitions

- Only the transition table above is accepted.
- Expected row version and state token match current authoritative state.
- Ready remains editable; content edits do not create lifecycle events or change state.
- Published/superseded revisions never return to a working state.
- Restore keeps the same stable revision ID and number.

### Publication

- Target is the one active Draft/Ready revision.
- Explicit confirmation is true.
- Publication token matches a fresh recomputation.
- Missing units, validation alerts, enabled-but-unscheduled exams, exam validity issues, recommendation deviations, and missing/pending/negative future feedback do not reject publication.
- Captured snapshot passes schema validation and contains all live semester schedule content.
- Replacement leaves exactly one current publication at commit.

### Historical references

- Current catalog mutations may change published source records without changing captured snapshot values.
- Hard delete assessment includes source IDs retained by inactive snapshots so a restorable revision does not lose required identities.
- If restoration nevertheless cannot materialize a required source identity, the operation is rejected without changing live content or lifecycle state and identifies the missing reference.

## Migration and backfill

Migration `0007_versioned_schedule_lifecycle.py`:

1. Creates `schedule_revisions` and `schedule_revision_events` with checks, foreign keys, and indexes.
2. Finds every distinct semester represented in `draft_schedules` or `exam_sessions`.
3. Inserts Draft revision number 1 with row version 1 and no snapshot for each represented semester.
4. Inserts one `created` event with event sequence 1 for each backfilled revision.
5. Leaves all teaching, exam, configuration, constraint, catalog, resource, and holiday rows byte-for-byte equivalent in domain values.
6. Updates schema recognition so repeated initialization is idempotent and unsupported partial states are rejected.

Empty semesters receive no backfilled history. A downgrade is permitted only while lifecycle data can safely collapse to the pre-FS-013 model; if multiple or inactive revisions contain history that cannot be represented, downgrade must refuse with a clear preservation message rather than silently discard it.
