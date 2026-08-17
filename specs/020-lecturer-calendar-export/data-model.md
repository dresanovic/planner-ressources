# Data Model: Lecturer iCalendar Export

FS-020 adds no persistent entity and no database migration. The model below describes the authoritative read model and transient export values used within one confirmed request.

## Existing authoritative entities

### LecturerReviewLink

Existing FS-015 bearer-link record that binds exactly one lecturer to one schedule revision.

Relevant inputs:

- Opaque secret digest used only for server-side resolution
- Lecturer identity and schedule-revision relationship
- Status, expiry, revocation/replacement/end state
- Existing access-block state

Rules:

- The plaintext secret is request-only and never enters the calendar model.
- A confirmed export re-evaluates validity; page load is not proof of later access.
- Successful export does not mutate link state, consume view allowance, or extend/shorten validity.

### ScheduleRevision

Existing authoritative revision bound to the link.

Relevant inputs:

- Stable internal revision identity, used only inside opaque UID derivation
- User-facing revision label
- Lifecycle state and current-revision relationship
- Semester relationship
- Immutable `created_at`, used as deterministic event `DTSTAMP`
- Published snapshot when the revision is published

Rules:

- The revision must remain accessible under FS-015 at download evaluation.
- `created_at` is normalized to a UTC whole-second value; the request clock is never emitted.
- Internal identity is never serialized directly.

### Semester

Existing semester bound to the revision.

Relevant inputs:

- User-facing semester label
- Start and end dates
- Current working/published revision relationships used by FS-015

Rules:

- Dates bound deterministic `VTIMEZONE` generation, including for zero events.
- Internal identity is never serialized directly.

### Scheduled teaching/exam session

Existing working-session rows or published-snapshot session entries already projected by FS-015.

Relevant authorized fields:

- Stable internal session identity and kind, used only inside opaque UID derivation
- Local date, start, and end
- Public course display code and title
- Effective session-type label
- Optional authorized room/site or location context
- Cohort and study type
- Teaching units or exam duration, as applicable
- Lecturer assignment used to establish membership, not displayed

Rules:

- One scheduled teaching or exam session maps to one event.
- Every and only sessions assigned to the link's lecturer in the bound revision are included.
- The established FS-015 public `course.code` is an authorized display value, even where the current scheduling model synthesizes it; it may appear in visible event text but never in the UID.
- Missing required fields, invalid time-zone localization, or internally inconsistent times invalidate the entire export.
- Missing optional location/context is omitted, not invented.

## Existing read model reused

### LecturerScheduleProjection

The strictly validated complete FS-015 `PublicReview` projection freshly built within the confirmed export transaction.

Fields consumed by FS-020:

| Field | Export use | Disclosure rule |
|---|---|---|
| `revision.label` | Filename, calendar name, description | User-facing only |
| `semester.label/start/end` | Filename, calendar name, description, TZ range | User-facing label; dates only drive metadata |
| `timeZone` | `TZID`, localization, `VTIMEZONE` | Must equal configured institution zone |
| `courses[].code/title/cohort/studyType` | Summary/description | Already authorized by FS-015 |
| `courses[].sessions[]` | One event per teaching/exam session | Complete unfiltered collection only |
| lecturer identity | Scope membership only | Never serialized in filename/calendar/event |
| filters/facets/findings/feedback | None | Never serialized |

Completeness states:

- `complete-nonempty`: all required projection values validate; one or more events are emitted.
- `complete-empty`: all required envelope values validate and the authoritative session collection is explicitly empty; zero events are emitted.
- `unprovable`: missing/corrupt arrays, invalid required values, inconsistent session, invalid TZID/local time, or concurrent state that cannot be made coherent; no file is emitted.

## Transient export value objects

### CalendarSnapshot

One in-memory deterministic representation created and returned within the request.

| Field | Type | Derivation/validation |
|---|---|---|
| `filename` | string | Exact Unicode algorithm from the iCalendar profile; no lecturer/token; fixed ASCII fallback `resource-planner-calendar.ics` |
| `display_name` | string | `<schedule> – <semester> – <revision>` using effective terminology |
| `product_id` | string | Fixed `-//Resource Planner//Lecturer Calendar Export 1.0//EN` |
| `time_zone` | IANA TZID | Exact configured/projected institution zone resolvable by `zoneinfo` |
| `timezone_start` | date | Semester start minus 366 days |
| `timezone_end` | date | Semester end plus 366 days |
| `events` | ordered tuple | All CalendarEvents sorted by start instant, end instant, UID |
| `bytes` | bytes | UTF-8 RFC 5545 output with CRLF and deterministic folding/order |

No snapshot is persisted, cached, queued, or sent to a calendar provider.

### CalendarEvent

One in-memory event for one authorized session.

| Field | Required | Source/rule |
|---|---:|---|
| `uid` | Yes | Exact domain-separated HMAC vector from the iCalendar profile; 64 lowercase hex characters plus fixed non-routable domain |
| `dtstamp` | Yes | Revision `created_at`, UTC, whole seconds |
| `start` | Yes | Complete timezone-aware source start date-time using the institution TZID |
| `end` | Yes | Complete timezone-aware source end date-time; must be later as an instant |
| `summary` | Yes | `<course code> – <course title> – <session type>`; omit absent code segment cleanly |
| `location` | No | Authorized room plus available site/location context; omit if absent |
| `description_lines` | Yes | Labeled authorized context lines; optional absent values omitted |
| `transparency` | Yes | Constant `OPAQUE` (Busy) |

Forbidden fields include lecturer names/contact data, other assignments, students, feedback, validation findings, planner notes/warnings, bearer/access state, raw IDs, organizer/attendee, alarms, invitations, and provider data.

Current production FS-015 sessions map start and end to their same source date because the scheduling model permits only same-day sessions. The synthetic cross-midnight conformance fixture supplies an explicit following-day `end` directly at this serializer-level boundary. The exporter never interprets an earlier or equal end time as an implicit next day.

### DownloadDecisionContext

Browser-only transient state for the notice interaction.

| Field | Type | Rule |
|---|---|---|
| `open` | boolean | Opening causes no request/download |
| `displayed_event_count` | non-negative integer | Count of all sessions in the currently opened unfiltered `PublicReview`, never derived from workspace filters |
| `busy` | boolean | Prevents duplicate confirmation and Escape cancellation during the request |
| `error_kind` | none/retryable/terminal | Safe mapped outcome; never raw server text |
| `opener` | element reference | Restores focus on cancel/retry close/success when still present |

The displayed count describes the currently opened complete unfiltered projection, not a reservation or a guarantee about the later file. The notice states that the confirmed request reauthorizes and may export a newer complete projection with a different count. No preview token or client snapshot ID is created.

### CalendarDownloadResponse

Validated browser transport value:

| Field | Type | Rule |
|---|---|---|
| `blob` | `Blob` | Accepted only from successful contracted `text/calendar` response |
| `filename` | string | Server-provided safe deterministic `.ics` name; reject missing/unsafe values |

## State transitions

```text
Valid loaded workspace
  -> notice open (no request, no mutation)
      -> cancel -> valid loaded workspace, prior context preserved
      -> confirm -> pending (one bearer request; controls disabled)
          -> success -> browser file handoff, prior context preserved
          -> retryable failure -> notice open with safe error, retry allowed
          -> terminal authorization/scope failure -> FS-015 unavailable state,
             protected review and transient dialog data cleared
```

The downloaded file is outside the product model after successful browser handoff. Later link/revision/schedule changes create no transition for an earlier file.

## Validation invariants

1. Exactly one lecturer/revision scope is resolved from the bearer secret; no client field can alter it.
2. Projection validation distinguishes explicit empty data from missing/corrupt data.
3. Event count equals the authoritative session count at serialization.
4. Event UIDs are unique within the file and stable for the same revision/session tuple.
5. Every start/end uses the one institution TZID and has a strictly positive instant duration.
6. Filename, calendar name, events, UID, and failures satisfy the privacy deny-list.
7. Same authoritative projection, terminology, labels, TZID/rules, stable UID key, pinned serializer, and pinned `tzdata` inputs yield the same filename and bytes.
8. No export entity, provider entity, or lifecycle mutation is committed.
