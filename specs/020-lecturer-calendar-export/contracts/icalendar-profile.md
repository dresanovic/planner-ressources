# FS-020 iCalendar Profile

This is the normative serialized-file contract for FS-020. RFC 5545 remains authoritative where this profile is silent. RFC 7986 supplies `NAME`; `X-WR-CALNAME` is the single documented compatibility property.

## Media and bytes

- Media type: `text/calendar; charset=utf-8`; no `method` parameter.
- Encoding: valid UTF-8 without a byte-order mark.
- Content lines end with CRLF, including the final `END:VCALENDAR` line.
- Lines are folded at no more than 75 octets according to RFC 5545 and unfolded values preserve the complete Unicode text.
- Text values escape backslash, comma, semicolon, and embedded newline as required by RFC 5545.
- Exactly one `VCALENDAR` is returned per successful request.

## Calendar component

Required properties:

| Property | Value |
|---|---|
| `VERSION` | `2.0` |
| `PRODID` | `-//Resource Planner//Lecturer Calendar Export 1.0//EN` |
| `CALSCALE` | `GREGORIAN` |
| `NAME` | `<effective schedule label> – <semester label> – <revision label>` |
| `X-WR-CALNAME` | Exactly the same value as `NAME` |

Required components:

- Exactly one `VTIMEZONE` for the institution TZID.
- Zero or more `VEVENT` components, exactly one per authorized teaching/exam session.
- No other component type.

Forbidden calendar properties/components include `METHOD`, `SOURCE`, refresh/subscription URLs or intervals, calendar-level UID, provider/account metadata, `VTODO`, `VJOURNAL`, `VFREEBUSY`, and `VALARM`.

## Time-zone component

- `TZID` exactly equals the startup-validated `INSTITUTION_TIMEZONE` and the FS-015 projection `timeZone`.
- The definition covers the deterministic range from semester start minus 366 days through semester end plus 366 days, including all applicable STANDARD/DAYLIGHT transitions.
- The same range and component are emitted for an empty projection.
- Every event `DTSTART` and `DTEND` has a matching `TZID` parameter. Floating and all-day values are forbidden.
- Ambiguous or nonexistent local source times invalidate the complete export unless source data already disambiguates the instant; the exporter does not guess.

## Event component

Each `VEVENT` contains only these properties, in a consistent insertion/serialization order:

| Property | Cardinality | Rule |
|---|---:|---|
| `UID` | 1 | Lowercase ASCII HMAC digest plus fixed non-routable domain; stable for revision/kind/session tuple; no raw input value |
| `DTSTAMP` | 1 | Revision `created_at` in UTC, whole seconds, `Z` form |
| `DTSTART` | 1 | Exact complete institution-local start date-time with `TZID` |
| `DTEND` | 1 | Exact complete institution-local end date-time with `TZID`; later than start as an instant |
| `SUMMARY` | 1 | `<course code> – <course title> – <session type>`; absent code segment omitted cleanly |
| `LOCATION` | 0..1 | Authorized room plus available site/location context; omit when absent |
| `DESCRIPTION` | 1 | Separately readable labeled lines defined below |
| `TRANSP` | 1 | `OPAQUE` |

`DESCRIPTION` lines appear in this stable semantic order, omitting only optional absent values:

1. Session type
2. Course code and title (code omitted cleanly if unavailable)
3. Cohort
4. Study type
5. Teaching units for teaching, or exam duration for an exam
6. Semester label
7. Revision label

Visible labels use effective I-002 terminology. Machine property names, TZID, date-time values, and `OPAQUE` remain standards values.

Forbidden event properties include `ORGANIZER`, `ATTENDEE`, `CONTACT`, `URL`, invitation/participation data, alarms, feedback/comments, validation findings, planner warnings/notes, access state, raw internal identifiers, `CREATED`, `LAST-MODIFIED`, `SEQUENCE`, `STATUS`, and `CLASS`.

## Identity and ordering

UID derivation is byte-exact:

```text
base_key = UTF-8 bytes returned by source_fingerprint_key_from_environment()
uid_key = HMAC-SHA256(base_key, b"fs020-calendar-uid-key-v1")

message =
  b"fs020-calendar-event-v1\0" +
  ascii_decimal(revision_id) + b"\0" +
  ascii(session_kind) + b"\0" +
  ascii_decimal(session_id)

UID = lowercase_hex(HMAC-SHA256(uid_key, message))
      + "@resource-planner.invalid"
```

Both IDs are positive decimal integers encoded without leading zeros;
`session_kind` is exactly ASCII `teaching` or `exam`; the full 32-byte digest is
encoded as 64 lowercase hexadecimal characters without truncation. The stable
production `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` supplies the base key through
the existing configuration function. Link secret, lecturer identity, names,
labels, and other display fields never enter the UID.

Events sort by:

1. UTC start instant
2. UTC end instant
3. UID using ordinal ASCII comparison

Source retrieval order must not affect output. Repeated serialization of unchanged source/configuration inputs with pinned serializer and `tzdata` versions must be byte-identical.

## Filename and response disposition

The Unicode filename is:

```text
<schedule-label>-<semester-label>-<revision-label>.ics
```

For each displayed segment:

1. Normalize to Unicode NFC and trim surrounding whitespace.
2. Replace each maximal run of characters that is neither a Unicode letter,
   Unicode number, period, underscore, nor hyphen with one hyphen.
3. Collapse repeated hyphens and trim leading or trailing periods, underscores,
   and hyphens.
4. Reject the export if any required segment is empty.

Join the three segments with hyphens. Limit the joined stem to 180 Unicode
scalar values at a scalar boundary, then repeat the boundary trim and reject an
empty result. If the result case-insensitively equals `CON`, `PRN`, `AUX`,
`NUL`, `COM1` through `COM9`, or `LPT1` through `LPT9`, prefix `calendar-`.
Append `.ics`. The name contains neither lecturer name nor bearer secret.

`Content-Disposition` supplies:

- the fixed ASCII fallback `resource-planner-calendar.ics`; and
- `filename*=UTF-8''...` with RFC 6266 percent encoding for the authoritative Unicode filename.

The browser must reject missing, malformed, path-containing, control-character-containing, or non-`.ics` names rather than reconstructing one from page state.

Current production sessions have same-day start and end date-times. A synthetic
cross-midnight conformance event carries an explicit following-day `DTEND`; the
serializer never infers date rollover solely because an end clock time is
earlier than or equal to a start clock time.

## Required fixtures and assertions

The retained corpus covers teaching-only, exam-only, mixed multi-course, explicit zero-event, DST transition, cross-midnight, missing optional location, identical displayed sessions, 100 events, Unicode/reserved punctuation, embedded newline, and long folded lines.

For each applicable fixture:

- export three times and compare filename and bytes;
- parse and assert every property/component/cardinality rule above;
- independently validate with the pinned iCal4j CLI;
- inspect the full bytes and unfolded values against the privacy deny-list;
- compare source session count and every expected event field;
- import manually in the representative Outlook environment as required by the acceptance matrix.
