# Phase 0 Research: Lecturer iCalendar Export

## 1. Compatibility boundary

**Decision**: Treat RFC 5545 as the portability contract, use RFC 7986 `NAME` plus the widely recognized `X-WR-CALNAME` compatibility property, and formally accept one institution-designated Outlook environment through manual static-file import.

**Rationale**: `.ics` is standardized, so the core syntax and semantics are client-independent. Calendar products still differ in optional-property handling, import UX, repeated-import behavior, and supported account/import paths. A standards validator proves syntax and structure; only an actual Outlook import can prove the institution's chosen client accepts the resulting file as intended. This matches the clarified scope without implying support certification for every Outlook edition or email/calendar client.

**Alternatives considered**:

- Test every Outlook edition and other calendar clients: rejected as an unbounded compatibility program outside FS-020.
- Build for one Outlook-specific format: rejected because it weakens portability and is unnecessary for static `.ics` import.
- Claim RFC validity alone proves Outlook behavior: rejected because client import behavior is not fully specified by RFC 5545.

**Primary references**: [RFC 5545](https://www.rfc-editor.org/info/rfc5545/), [RFC 7986](https://www.rfc-editor.org/info/rfc7986/), [Microsoft static import guidance](https://support.microsoft.com/en-US/Outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web), and [Microsoft classic Outlook calendar import training](https://support.microsoft.com/en-us/outlook/training/import-calendars-into-outlook).

## 2. Serialization dependency

**Decision**: Add and pin `icalendar==7.2.2` as the one new runtime dependency. Use its typed component/property APIs and `Calendar.to_ical(sorted=True)` rather than constructing content lines by hand.

**Rationale**: Correct UTF-8 escaping, CRLF serialization, 75-octet folding, typed date-times, parameters, and `VTIMEZONE` observances are all present requirements. The focused package supports Python 3.12, is specifically maintained for RFC 5545 data, and its required date/time dependencies already exist in this repository. Pinning makes the serializer behavior reviewable and deterministic.

**Alternatives considered**:

- Hand-written serializer: rejected because it duplicates standards-sensitive escaping, byte folding, parameters, and time-zone generation and creates unnecessary security/compatibility risk.
- A general calendar/provider SDK: rejected because FS-020 has no provider API, account, or synchronization behavior.
- Frontend generation: rejected because the browser does not own authoritative scope, effective server terminology, or the coherent transaction.

**Primary references**: [`icalendar` package](https://pypi.org/project/icalendar/), [`icalendar` component API](https://icalendar.readthedocs.io/en/stable/reference/api/icalendar.cal.component.html), and [`VTIMEZONE` API](https://icalendar.readthedocs.io/en/stable/reference/api/icalendar.cal.timezone.html).

## 3. Calendar profile and deterministic bytes

**Decision**: Emit one `VCALENDAR` with `VERSION:2.0`, a fixed non-secret `PRODID`, `CALSCALE:GREGORIAN`, matching `NAME` and `X-WR-CALNAME`, exactly one bounded `VTIMEZONE`, and deterministically ordered `VEVENT` components. Serialize component and property insertion consistently and use the library's sorted output. Do not include `METHOD`, `SOURCE`, refresh/subscription properties, calendar UID, organizer, attendee, alarms, invitations, provider metadata, `CREATED`, `LAST-MODIFIED`, `SEQUENCE`, `STATUS`, or `CLASS`.

**Rationale**: This is the smallest standards-valid static import profile that carries the required human context and explicit Busy status. Excluding volatile or workflow-oriented metadata narrows disclosure and prevents download time from changing bytes.

**Determinism rules**:

- Sort events by start instant, end instant, then UID.
- Use the revision's immutable `created_at`, normalized to a UTC whole-second value, as every event's `DTSTAMP`; never use the download clock. `updated_at` is unsuitable because ordinary session edits do not consistently advance it.
- Build the `VTIMEZONE` for the deterministic semester interval from 366 days before semester start through 366 days after semester end. Use the same interval for an empty projection.
- Treat effective terminology, semester/revision labels, the configured TZID and rules, the stable UID key, pinned serializer version, and pinned `tzdata` version as deterministic inputs. Upgrade either package only with golden-fixture and Outlook revalidation.
- Reject ambiguous/nonexistent local source times or an end that cannot be proven later than its start; do not guess an offset or emit a partial file.

**Alternatives considered**:

- Current download time for `DTSTAMP`: rejected because repeated unchanged exports would differ.
- Unbounded time-zone history: rejected because it increases file size and platform variability without improving the semester snapshot.
- Floating times or UTC-only presentation: rejected because the specification requires institution-local TZID semantics and a complete `VTIMEZONE`.

## 4. Stable opaque event UIDs

**Decision**: Use the UTF-8 bytes returned by `source_fingerprint_key_from_environment()` as the base key. Derive `uid_key = HMAC-SHA256(base_key, b"fs020-calendar-uid-key-v1")`. Sign the exact message `b"fs020-calendar-event-v1\0" + ascii_decimal(revision_id) + b"\0" + ascii(session_kind) + b"\0" + ascii_decimal(session_id)`, where IDs are positive decimal integers without leading zeros and `session_kind` is exactly `teaching` or `exam`. Emit the complete lowercase hexadecimal HMAC-SHA-256 digest plus `@resource-planner.invalid`. Never place the tuple or raw IDs in the output.

**Rationale**: The same scheduled session in the same revision receives a stable UID even when display fields change; distinct sessions and revisions remain distinct. HMAC prevents low-cardinality database identifiers from being exposed or feasibly enumerated. Domain separation avoids reusing the existing key for the same purpose while adding no second production secret or persistence layer. Infrastructure already requires this key to remain stable.

**Operational constraint**: A rotation of the source-fingerprint key intentionally changes FS-020 UIDs and therefore requires documented compatibility impact plus renewed deterministic/import evidence. Normal deployments must preserve it.

**Alternatives considered**:

- Raw database IDs, UUIDs, or concatenated source references: rejected by the privacy requirements.
- Plain hash/UUIDv5 of database IDs: rejected because small integer identities are dictionary-enumerable.
- Persisted export UUIDs: rejected because it requires a migration and export state solely for a deterministic derivation.
- Link secret as key/input: rejected because UID identity would change with replacement and risks coupling output to bearer material.

## 5. Authorization, projection, and non-mutation

**Decision**: Add one fixed `GET /api/public/lecturer-review/calendar` route with bearer authorization and no query parameters or request body. Inside one database transaction, use a read-only export-specific entry point in the existing FS-015 review service to lock/re-read the semester, evaluate the same validity and active-revision predicates, build the current complete public projection, validate it strictly, and serialize it before the transaction closes.

**Rationale**: The browser cannot influence scope, and one transaction prevents a mixture of assignment states. Reusing FS-015's projection preserves the established authorization/data-minimization boundary. A separate public projection DTO or browser-provided snapshot would risk divergence.

**Non-mutation rule**: A valid export does not add an export record, count as a successful page view, consume a limit, shorten validity, or materialize an expiry/revision transition. It changes no schedule, feedback, revision, publication, link-lifecycle, or provider data. Existing privacy-safe invalid-source abuse controls may record malformed/unknown attempts; those are security controls, not an export business record, and must reveal no scoped data.

**Completeness hardening**: Published snapshot parsing must require the arrays and required values expected by the FS-015 public projection. Missing keys, invalid types, invalid local times, unresolvable time zone, or inconsistent events map to the same safe no-file outcome; absence must not silently become an empty schedule. A valid explicitly empty session collection remains exportable.

**Alternatives considered**:

- Reuse the existing page GET response in the browser: rejected because it can be stale and cannot reauthorize at confirmation.
- Post filtered/visible session IDs: rejected because it enables partial or manipulated scope.
- A prepare/preview token and second endpoint: rejected as unnecessary state and race complexity. The dialog explicitly labels its count as the complete unfiltered projection currently displayed and warns that confirmation re-evaluates scope, so the confirmed file remains authoritative and may have a different count if assignments change meanwhile.
- Reuse the current page-access method unchanged: rejected because it records successful view activity and can materialize lifecycle state, contrary to FS-020 non-mutation requirements.

## 6. Time-zone authority

**Decision**: Replace the FS-015 hard-coded `Europe/Vienna` constant with startup-validated `INSTITUTION_TIMEZONE` configuration, defaulting to `Europe/Vienna` for the existing deployment. The export consumes the authoritative projection's TZID and resolves it with `zoneinfo`/pinned `tzdata`.

**Rationale**: Other scheduling code already recognizes `INSTITUTION_TIMEZONE`; the export must not declare a time zone that differs from the projection. Startup validation fails safely before serving invalid schedules and avoids introducing a new configuration framework.

**Alternatives considered**:

- Keep an export-only hard-coded time zone: rejected because two authorities can drift.
- Accept a client-provided TZID: rejected because institution time is authoritative and client input could alter event instants.
- Add a new general settings service: rejected as unjustified for one existing environment value.

## 7. HTTP delivery and browser handling

**Decision**: Return `Content-Type: text/calendar; charset=utf-8`, `Content-Disposition: attachment` with the fixed ASCII fallback `resource-planner-calendar.ics` plus RFC 6266 `filename*` containing the deterministic Unicode name, the existing public no-store/privacy headers, and `X-Content-Type-Options: nosniff`. The Unicode algorithm is defined byte-for-byte in the iCalendar profile. The React client performs one fixed relative-path fetch with `Authorization: Bearer`, `Accept: text/calendar`, and `credentials: 'omit'`; it validates the safe `.ics` filename and media type, creates a temporary object URL/link, clicks once, removes it, and revokes the URL.

**Rationale**: The bearer never enters a URL, cookie, history, storage, filename, or DOM text. The server remains authoritative for scope, naming, and bytes. Browser navigation is unsuitable because it cannot safely attach the in-memory authorization header.

**Alternatives considered**:

- Secret in query string or cookie: rejected by the existing FS-015 boundary.
- Filename built by the frontend: rejected because labels and safe deterministic normalization are server responsibilities.
- Data URL: rejected because object URLs are the established safe browser pattern for potentially larger binary/text downloads.

**Primary reference**: [RFC 6266](https://www.rfc-editor.org/info/rfc6266/).

## 8. Workspace interaction

**Decision**: Add an optional neutral context-header action slot to `CalendarPlanningWorkspace`, supplied only by `LecturerReviewPage`. A new `LecturerCalendarDownloadDialog` provides the notice, unfiltered opened-projection event count, explicit cancel/continue controls, focus containment/restoration, busy state, retryable safe error, and terminal FS-015 clearing. Confirmation sends only the secret.

**Rationale**: The context header visually associates export with the fixed lecturer/revision workspace while keeping it separate from display filters and date navigation. A dedicated dialog is clearer than reusing destructive/discard semantics. Page-local orchestration preserves existing filter, selection, mode, visible period, and feedback-draft state.

**Alternatives considered**:

- Put the action in the filter/date toolbar: rejected because it implies filtered or visible-period export.
- Put it inside the fixed lecturer identity block: rejected because that block is read-only identity context.
- Reuse the discard dialog: rejected because destructive wording and button semantics are incorrect.
- Add global state/router parameters: rejected because the page already owns the in-memory token and workspace state.

## 9. Validation strategy

**Decision**: Use three complementary levels: runtime-library parse plus explicit byte/profile tests, independent iCal4j CLI validation, and manual import into the representative Outlook environment. Retain checksummed fixtures and evidence.

**Rationale**: Self-parsing alone can reproduce a library's own defect. An independent validator covers standards structure; Outlook covers the actual target's import behavior. Automated tests cover every-and-only scope, privacy, lifecycle, concurrency, determinism, and performance without relying on manual review.

**Fixture constraint**: Cross-midnight and missing-location serializer cases use synthetic serializer-level `CalendarEvent` values. The cross-midnight value carries explicit complete start and following-day end date-times; no rollover is inferred from an end time alone. Current production models enforce same-day end times and generally require rooms, and FS-020 does not expand that scheduling model merely to manufacture conformance cases.

**Independent-tool pinning**: Before validator evidence is produced, record the institution-approved exact iCal4j release, official artifact URL, SHA-256 checksum, and install/validation commands in `validation/toolchain.md`. Every retained fixture is validated only after the downloaded artifact matches that checksum, so evidence cannot silently drift between validator releases.

**Performance evidence**: Measure the deterministic 100-session projection in the release backend container constrained to 2 vCPU and 2 GiB RAM, with one application process, release dependency pins, debug instrumentation disabled, container-local SQLite, and no concurrent requests. After 10 untimed warm-ups, record 100 complete-response samples and retain the container image digest, host CPU model, Docker version, samples, and percentile calculation. Acceptance requires p95 at or below three seconds and maximum at or below ten seconds.

**Primary references**: [iCal4j validation](https://www.ical4j.org/validation/) and [iCal4j calendar CLI](https://www.ical4j.org/command/calendar/).

## Resolved Questions

All Phase 0 questions are resolved and no planning clarification remains open. The Outlook distinction is now explicit: the file format is standardized, while import UX and optional behavior vary; formal support is therefore RFC conformance plus one representative institutional Outlook acceptance environment.
