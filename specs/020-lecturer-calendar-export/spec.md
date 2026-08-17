# Feature Specification: Lecturer iCalendar Export

**Working Branch**: `codex/fs-020-lecturer-calendar-export`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "FS-020 lets an accountless lecturer download one
Outlook-compatible static iCalendar file containing the complete FS-015
token-scoped teaching and exam schedule for one semester revision."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-08-14

- Q: Which Outlook clients must FS-020 formally support? → A: Standards-first
  RFC 5545 conformance plus one manual import test in the institution's
  representative Outlook environment; no edition-by-edition or multi-client
  compatibility guarantee.
- Q: Should imported teaching and exam sessions block the lecturer's Outlook
  availability? → A: Yes. Every exported teaching and exam event is explicitly
  Busy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download the Complete Personal Schedule (Priority: P1)

An accountless lecturer opens a valid FS-015 review link and downloads one
calendar file containing every current teaching and exam assignment across all
courses in the link's semester revision. The export always represents the
complete authorized schedule, even when the lecturer is viewing only one week,
has active filters, or has selected one session.

**Why this priority**: The slice delivers value only when the lecturer can take
the complete personal schedule into a calendar without manually reconstructing
it or accidentally omitting hidden assignments.

**Independent Test**: Use a valid link whose authoritative projection contains
teaching and exam sessions across several courses, apply restrictive filters
and navigate away from some event dates, download the file, and verify that it
contains exactly one event for every and only the currently scoped session.

**Acceptance Scenarios**:

1. **Given** a valid review link with assigned teaching and exam sessions across
   several courses, **When** the lecturer confirms Download calendar, **Then**
   one `.ics` file is downloaded with exactly one event for every and only the
   sessions currently assigned to the link's lecturer in the bound revision.
2. **Given** active course, room, session-type, lifecycle, or validation filters,
   a limited visible period, calendar or list mode, and a selected session,
   **When** the lecturer downloads the calendar, **Then** none of those display
   choices reduces or expands the exported event set.
3. **Given** a session has entered or left the lecturer's authorized assignment
   scope since the review page was opened, **When** the download is evaluated,
   **Then** the file uses the current complete authoritative projection rather
   than the stale visible result.
4. **Given** the valid, complete projection displayed in the notice has no
   assigned sessions and remains authoritative through confirmation, **When**
   the lecturer proceeds after being told that the displayed schedule contains
   zero events, **Then** the lecturer receives a valid empty calendar file and
   no event from another scope is substituted.

---

### User Story 2 - Import Recognizable Events into Outlook (Priority: P1)

The lecturer manually imports the downloaded standards-valid file into the
institution's representative Outlook environment and can recognize each
assignment from its course, session type, timing, location, and relevant
academic context. Event times remain correct in the institution's local time
zone, including across daylight-saving changes.

**Why this priority**: A complete file is not useful if Outlook rejects it or
if imported events are ambiguous or appear at the wrong time.

**Independent Test**: Validate conformance fixtures covering teaching, exams,
multiple courses, daylight-saving transitions, non-ASCII text, missing optional
locations, and long values against RFC 5545, then manually import the fixture
set in the institution's representative Outlook environment and compare every
imported event with its source session.

**Acceptance Scenarios**:

1. **Given** a standards-valid file with teaching and exam events, **When** it is
   imported in the institution's representative Outlook environment, **Then**
   every event is accepted and shows the source session's local date, start
   time, end time, course, session type, location when assigned, and relevant
   context.
2. **Given** sessions on both sides of a daylight-saving transition, **When** the
   file is imported on a device in any time zone, **Then** Outlook represents
   the sessions at the correct institution-local instants without treating the
   source times as floating values.
3. **Given** course, cohort, room, or study-type values containing umlauts,
   punctuation, line breaks, commas, semicolons, or long text, **When** the file
   is validated and imported, **Then** the values remain readable and do not
   corrupt the calendar structure or adjacent fields.
4. **Given** a session with no assigned room or other optional context, **When**
   it is imported, **Then** the event remains valid and recognizable without an
   invented location or placeholder being mistaken for schedule data.
5. **Given** any exported teaching or exam session, **When** it is imported in
   the representative Outlook environment, **Then** the event is shown as Busy
   rather than relying on a client-specific availability default.

---

### User Story 3 - Understand and Preserve the Privacy Boundary (Priority: P1)

Before downloading, the lecturer learns that the file is a static personal
snapshot outside product control. An ended link prevents any later download,
and an incomplete or unauthorized projection never produces a partial or
cross-lecturer file.

**Why this priority**: The file contains personal schedule information and
cannot be revoked after it has left the product; safe authorization and clear
expectations are therefore part of the primary outcome.

**Independent Test**: Exercise valid, expired, revoked, replaced, abandoned,
superseded, malformed, and unknown links; force complete and incomplete
projection results; and verify the notice, absence of partial downloads,
minimum disclosure, and zero cross-lecturer data.

**Acceptance Scenarios**:

1. **Given** a valid review link, **When** the lecturer chooses Download
   calendar, **Then** a notice appears before file delivery explaining that the
   snapshot will not be updated or removed when the link or revision later
   changes and that the lecturer must protect and manually manage the file.
2. **Given** that notice, **When** the lecturer cancels, **Then** no file is
   delivered and no schedule, feedback, revision, link, or provider data
   changes.
3. **Given** the link expires, is revoked or replaced, or its revision becomes
   inaccessible before the download is authoritatively evaluated, **When** a
   download is attempted, **Then** no file is delivered and the response
   reveals no schedule or event data.
4. **Given** the authorized projection cannot be proven complete, **When** a
   download is attempted, **Then** no `.ics` file is delivered and the lecturer
   receives a safe, actionable failure state rather than a partial calendar.
5. **Given** a file was downloaded while the link was valid, **When** the link
   later ends or the schedule changes, **Then** the product makes no claim that
   it can alter, recall, or delete the downloaded or imported copy.

---

### User Story 4 - Receive a Deterministic Snapshot (Priority: P2)

The lecturer can download the same complete snapshot again and receive the same
calendar and event identities. If the current projection changes, a later file
reflects the changed snapshot while keeping the identity of the same session
stable within the bound revision. The lecturer is warned that the calendar
client, not this product, controls whether a repeated manual import updates,
ignores, or duplicates previously imported events.

**Why this priority**: Stable output makes the file testable and recognizable,
but a static import must not imply synchronization or duplicate prevention that
the product cannot control.

**Independent Test**: Export one unchanged snapshot repeatedly and compare its
filename, bytes, calendar metadata, event order, and UIDs; then change, add, and
remove sessions within the same revision and verify the defined identity and
snapshot behavior without relying on Outlook to reconcile imports.

**Acceptance Scenarios**:

1. **Given** the same authoritative projection, effective terminology, and
   institution time-zone definition, **When** the calendar is downloaded more
   than once, **Then** the filename and file bytes are identical.
2. **Given** the same scheduled session in the same revision has displayable
   details changed, **When** a later snapshot is downloaded, **Then** its event
   fields reflect the current session while its UID remains unchanged.
3. **Given** two distinct sessions have identical course, date, time, and room
   values, **When** they are exported, **Then** they remain two events with
   different UIDs.
4. **Given** the lecturer may import a file more than once, **When** the static-
   file notice is shown, **Then** it states that repeated import can create
   duplicates and that updating or removing earlier imports is the lecturer's
   responsibility.

### Edge Cases

- The link is valid when the notice opens but expires, is revoked, is replaced,
  or loses access to the revision before the confirmed download is evaluated;
  the later authorization state wins and no file is delivered.
- The visible FS-015 page is stale after assignment changes; the export uses a
  newly evaluated complete projection, excludes sessions reassigned away, and
  includes sessions newly assigned to the scoped lecturer.
- The projection changes while the export is being formed; the result must be
  one coherent authoritative snapshot and never a mixture of two states.
- The complete unfiltered projection currently displayed contains zero events;
  the notice states that displayed count. If the projection remains unchanged,
  an explicitly confirmed download is a standards-valid calendar with no
  `VEVENT` components; if assignments change first, the confirmed download uses
  the newer authoritative projection and may contain a different event count.
- The projection, required time-zone definition, or any required event field is
  incomplete or internally inconsistent; no file is delivered.
- Two distinct sessions have otherwise identical displayed fields; both are
  exported and remain distinguishable by stable event identities.
- A session crosses midnight or a daylight-saving boundary; its end remains
  later than its start and represents the source duration correctly.
- Optional room or context data is absent; the file omits the unavailable value
  rather than inventing or leaking a planner-only value.
- User-facing text contains Unicode, reserved iCalendar punctuation, embedded
  newlines, or values long enough to require standards-compliant folding; the
  complete value survives validation and Outlook import.
- A download is interrupted by the browser or local network; the product
  reports no domain-data change, and the lecturer may retry while the token
  remains valid. A corrupt or truncated local file is never presented as a
  successful product snapshot.
- A previously exported session is later changed or removed, or the revision is
  superseded; already downloaded and imported copies remain unchanged.
- The same or a later static file is imported repeatedly; Outlook may create
  duplicates despite stable UIDs, and the product neither promises de-
  duplication nor modifies the lecturer's calendar.

## Scope Boundaries

### In Scope

- One Download calendar action in the reused FS-015 lecturer calendar/list
  workspace.
- One static `.ics` file for the complete current teaching and exam projection
  of the link's one lecturer and one semester revision across all courses.
- Export behavior independent of calendar/list mode, visible period, active
  filters, selected session, or transient feedback state.
- Human-recognizable course, session-type, timing, room, cohort, study-type,
  teaching-unit or exam-duration, semester, and revision context where present
  in the authorized FS-015 projection.
- Institution-local time-zone metadata, deterministic calendar metadata,
  stable event UIDs, standards-valid iCalendar content, and manual import into
  the institution's representative Outlook environment.
- A pre-download static-file, privacy, and repeat-import notice.
- Complete empty projections, safe failures, accessibility of the new action
  and notice, and conformance fixtures for the supported boundary.

### Out of Scope

- Calendar subscription URLs, live feeds, refresh, synchronization, two-way
  exchange, Outlook or calendar-provider APIs, account connection, and calendar
  account discovery.
- Planner-side export, export for more than one lecturer, filtered export,
  visible-period export, selected-event export, and any other partial export.
- Feedback, comments, impossible-session flags, planner-only validation or
  warnings, planner notes, internal security or link data, student-level data,
  and another lecturer's identity or assignments.
- Creating, editing, moving, deleting, accepting, publishing, or otherwise
  changing product schedule data through export.
- Guaranteed update, merge, or de-duplication behavior when a static file is
  imported repeatedly or imported after a later revision is issued.
- Remote recall, expiry, revocation, update, or deletion of a downloaded or
  imported file.
- Automated email delivery, attachments, calendar invitations, attendees,
  responses, reminders, and organizer workflows.
- Selection of an iCalendar generation library or other implementation design.

## Requirements *(mandatory)*

### Functional Requirements

#### Scope, Authorization, and Completeness

- **FR-001**: The reused FS-015 lecturer workspace MUST offer a Download
  calendar action only within the fixed lecturer and revision context of a
  schedule-review link.
- **FR-002**: Before delivering a file, the product MUST authoritatively
  re-evaluate every FS-015 condition required for the link to access its bound
  revision, including validity, expiry, revocation, replacement, and revision
  availability; a previously loaded page MUST NOT authorize a later download.
- **FR-003**: A successful export MUST use one complete, current, authoritative
  FS-015 schedule projection for the link's lecturer and bound revision and
  MUST contain every and only the teaching and exam sessions in that
  projection across all courses.
- **FR-004**: Calendar/list mode, visible date range, active filters, selected
  session, scroll position, and transient feedback state MUST NOT reduce,
  expand, or otherwise change the exported event set.
- **FR-005**: Assignment changes since the page was opened MUST be reflected at
  download evaluation: newly assigned sessions MUST be included and sessions
  no longer assigned to the scoped lecturer MUST be excluded.
- **FR-006**: The exported file MUST represent one coherent projection state.
  If the product cannot establish one complete state or any required source
  value is inconsistent, it MUST deliver no calendar file.
- **FR-007**: A complete projection containing zero sessions MUST be treated as
  complete and MUST produce a valid zero-event calendar after explicit
  confirmation when it remains authoritative. Before confirmation, the notice
  MUST identify the event count in the complete unfiltered projection currently
  displayed and MUST explain that the confirmed download is re-evaluated and
  may reflect newer assignments and therefore a different event count.
- **FR-008**: An unsuccessful export MUST present an actionable state consistent
  with FS-015 and I-002 without exposing whether any particular lecturer,
  revision, course, or session exists outside the authorized context.
- **FR-009**: Export and cancellation MUST NOT create, edit, or delete schedule,
  feedback, revision, publication, token-lifecycle, or calendar-provider data
  and MUST NOT consume or shorten the review link's validity.

#### Download Interaction and Privacy Notice

- **FR-010**: Choosing Download calendar MUST show a notice before any file is
  delivered and MUST require an explicit Continue download or Cancel decision;
  merely opening the notice MUST NOT start a download.
- **FR-011**: The notice MUST state that the file is a static personal snapshot;
  remains outside product control; is not updated or removed by later schedule,
  revision, token-expiry, revocation, or replacement changes; may expose the
  schedule if copied; and must be stored, shared, and deleted by the recipient
  with appropriate care.
- **FR-012**: The notice MUST state that repeated manual import can create
  duplicate calendar items and that the product does not update, reconcile, or
  remove previously imported events.
- **FR-013**: Cancelling the notice MUST return focus to the Download calendar
  action, deliver no file, preserve the lecturer's workspace context and
  transient feedback state, and make no domain-data change.
- **FR-014**: Success, cancellation, and failure MUST leave calendar/list mode,
  visible period, active filters, eligible selection, and unsent feedback
  unchanged unless current FS-015 scope independently requires their removal.
- **FR-015**: The action, notice, decision controls, event-count statement, and
  failure state MUST be operable and understandable by keyboard and supported
  assistive technology, at 200% text zoom, and at a viewport equivalent to 320
  CSS pixels without horizontal page scrolling.
- **FR-016**: New user-facing labels and messages MUST follow the effective
  I-002 terminology and message rules; standards-mandated machine values in
  the file are not human-visible date-format exceptions.

#### Calendar and File Identity

- **FR-017**: Each successful request MUST deliver exactly one file with the
  `.ics` extension and the deterministic filename pattern
  `<schedule-label>-<semester-label>-<revision-label>.ics`. Each displayed
  segment MUST be normalized to Unicode NFC and trimmed. Each maximal run of
  characters that is neither a Unicode letter, Unicode number, period,
  underscore, nor hyphen MUST become one hyphen; repeated hyphens MUST collapse;
  and leading or trailing periods, underscores, and hyphens MUST be removed. If
  a required segment becomes empty, no file MUST be delivered. The joined stem
  MUST be limited to 180 Unicode scalar values, then trimmed by the same boundary
  rule; a stem equal case-insensitively to `CON`, `PRN`, `AUX`, `NUL`, `COM1`
  through `COM9`, or `LPT1` through `LPT9` MUST receive the `calendar-` prefix.
  The authoritative Unicode name MUST be carried
  in `filename*`, while the ASCII fallback MUST be the fixed
  `resource-planner-calendar.ics`. Neither name may contain the link secret or a
  lecturer name.
- **FR-018**: The calendar display name MUST be the effective schedule label
  followed by the bound semester and revision labels, separated by ` – `. It
  MUST be represented in the RFC 7986 `NAME` property and the Outlook-
  compatible `X-WR-CALNAME` property with the same human-readable value.
- **FR-019**: The file's product identifier MUST identify the Resource Planner
  and export format without containing a link secret, lecturer identity, host
  path, or environment-specific confidential value.
- **FR-020**: Repeated exports from identical authoritative projection data,
  effective terminology, semester/revision labels, institution time-zone
  definition, stable UID derivation key, pinned serializer version, and pinned
  time-zone-data version MUST produce an identical filename and byte-for-byte
  identical file content, including calendar metadata, event ordering, UIDs,
  and time metadata.
- **FR-021**: Events MUST be ordered deterministically by start instant, then end
  instant, then stable UID so that source-record retrieval order cannot change
  the file.

#### Event Content and Privacy

- **FR-022**: The file MUST contain exactly one `VEVENT` for each scheduled
  teaching or exam session and MUST NOT combine distinct sessions even when all
  their displayed fields are equal.
- **FR-023**: Every event summary MUST use the recognizable pattern
  `<course code> – <course title> – <session type>` using effective user-facing
  terminology. If no course code exists, the summary MUST omit that segment
  without leaving an empty separator.
- **FR-024**: Every event MUST contain the source session's exact start and end
  date-times, a summary, a stable UID, and a deterministic `DTSTAMP` derived
  from the authoritative source state rather than the download clock. Any
  optional creation or last-modified metadata MUST be deterministic as well.
  Every event MUST declare `TRANSP:OPAQUE` so it imports as Busy rather than
  depending on a calendar client's default availability status.
- **FR-025**: When an authorized room or location value exists, the event
  location MUST contain its user-facing room name plus its available site or
  location context. When none exists, the location field MUST be omitted rather
  than populated with invented schedule data.
- **FR-026**: The event description MUST present, on separately readable lines,
  the session type, course code and title, cohort, study type, teaching units or
  exam duration as applicable, and the bound semester and revision labels,
  omitting only optional values absent from the authorized projection.
- **FR-027**: Exported text MUST preserve Unicode and MUST escape and fold values
  as required by the iCalendar standard so that punctuation, embedded line
  breaks, and long values cannot change the file structure or another field.
- **FR-028**: The file MUST NOT contain another lecturer's identity or sessions,
  lecturer contact data, student-level data, feedback or comment content,
  validation details, planner-only warnings, planner notes, link secrets,
  access-control state, internal security data, or raw internal identifiers.
  The UID is an opaque calendar identity subject to FR-029 and is not a license
  to expose a raw internal identifier.
- **FR-029**: Each event UID MUST be globally unique, opaque, and deterministic;
  stable for the same scheduled session within the same revision across repeat
  exports and display-field changes; distinct for every different session and
  revision; and free of tokens, names, course/location text, contact data, and
  other personally identifying values.
- **FR-030**: UID continuity across different revisions is not guaranteed by
  this slice, and the file MUST NOT claim that Outlook or another consumer will
  update or de-duplicate earlier imports based on UID.
- **FR-031**: The file MUST contain no organizer, attendee, invitation,
  participation-status, alarm, feedback, or calendar-provider account data.

#### Time Zone, Standards, and Outlook Compatibility

- **FR-032**: The file MUST be a valid iCalendar 2.0 calendar conforming to RFC
  5545 and the RFC 7986 calendar-name usage in FR-018, encoded as UTF-8 with
  standards-compliant content lines, delimiters, escaping, folding, and line
  endings.
- **FR-033**: The calendar MUST declare iCalendar version 2.0, a product
  identifier, and the Gregorian calendar scale and MUST include only
  standards-valid components and properties plus documented compatibility
  properties that do not change the standard meaning.
- **FR-034**: Every event start and end MUST be represented in the institution's
  configured local time zone using a time-zone identifier; timed sessions MUST
  NOT be exported as floating local times or all-day events.
- **FR-035**: The file MUST include one complete `VTIMEZONE` definition for the
  institution time zone covering every exported event instant and all relevant
  standard/daylight transitions. A zero-event file MUST include the same
  definition covering the bound semester period.
- **FR-036**: Imported event instants and durations MUST remain equal to their
  source sessions on both sides of daylight-saving transitions and when the
  importing device uses a different display time zone.
- **FR-037**: The file MUST import without repair prompts or rejected events in
  the institution's representative Outlook environment, and the imported
  summary, start, end, location, description, and event count MUST match the
  source fixture. This acceptance test MUST NOT create an edition-by-edition or
  multi-client compatibility guarantee.
- **FR-038**: The same file MUST pass the release's independent RFC 5545
  conformance validation with no syntax or structural errors; compatibility
  properties MUST NOT cause a validation error or replace required standard
  properties.
- **FR-039**: Calendar delivery and import MUST remain a manual file exchange.
  The export MUST initiate no account connection, Outlook or provider request,
  subscription, synchronization, invitation delivery, or provider-side data
  mutation.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for
  each implemented user story wherever automated testing is practical; any
  exception MUST be justified with a manual verification path in the plan.
- **TR-002**: Scope and authorization tests MUST cover at least three
  lecturers, two revisions, multi-course assignments, teaching and exam
  sessions, active filters, restricted visible periods, assignment changes,
  and a complete empty projection, verifying every-and-only scope with no
  cross-lecturer or cross-revision disclosure.
- **TR-003**: Lifecycle tests MUST attempt download before and at expiry and
  after revocation, replacement, abandonment, and supersession, including a
  state change between notice display and confirmed download.
- **TR-004**: Completeness tests MUST force unavailable, partial, inconsistent,
  and concurrently changing projections and verify that the result is either
  one coherent complete file or no file, never a partial snapshot.
- **TR-005**: Determinism tests MUST compare at least three repeated exports of
  each unchanged fixture byte for byte, then cover session edits, additions,
  removals, identical displayed sessions, and source-order variation to verify
  filename, ordering, metadata, and UID rules.
- **TR-006**: The conformance fixture set MUST include teaching-only, exam-only,
  mixed multi-course, zero-event, daylight-saving transition, cross-midnight,
  missing optional location, identical displayed sessions, 100-event,
  Unicode/reserved-character, embedded-newline, and long-line calendars.
- **TR-007**: Every fixture MUST pass an independent RFC 5545 validator with no
  syntax or structural errors. Validation evidence and the exact fixture set
  MUST be retained for release review.
- **TR-008**: Every non-empty fixture MUST be manually imported in the
  institution's representative Outlook environment, and imported event count,
  summary, start, end, time zone, Busy status, location, and description MUST
  be compared with expected source values. The empty fixture MUST import or
  open without repair or fabricated events. Other Outlook editions and calendar
  clients are not part of the formal acceptance matrix.
- **TR-009**: Privacy tests MUST inspect the filename, calendar metadata, every
  event field, UIDs, notices, and failure states for tokens, another
  lecturer's identity or assignments, contacts, student data, feedback,
  validation details, planner warnings or notes, and internal security data.
- **TR-010**: Non-mutation tests MUST verify success, cancellation, validation
  failure, authorization failure, and interrupted retry without changes to
  schedule, feedback, revision, publication, token lifecycle, or provider data.
- **TR-011**: Interaction and accessibility tests MUST verify explicit notice
  confirmation, cancellation focus restoration, workspace-context retention,
  keyboard-only use, supported assistive technology, 200% text zoom, and a
  viewport equivalent to 320 CSS pixels.
- **TR-012**: Scope regression tests MUST confirm the absence of subscriptions,
  synchronization, provider or Outlook account access, planner export,
  filtered or selected-event export, invitations, reminders, guaranteed repeat-
  import reconciliation, and remote deletion.

### Key Entities

- **Lecturer Schedule Projection**: The complete current FS-015 read-only set of
  teaching and exam sessions assigned to the link's one lecturer in the bound
  semester revision, containing only fields authorized for lecturer review.
- **Calendar Snapshot**: The deterministic static representation of one
  complete projection, including its display name, institution time zone,
  ordered event set, and non-secret product metadata. It is not retained as a
  synchronized calendar by this slice.
- **Calendar Event**: One exported teaching or exam session with a stable UID,
  recognizable summary, exact start/end, explicit Busy status, optional
  authorized location, and authorized descriptive context.
- **Event UID**: An opaque globally unique calendar identity that distinguishes
  sessions and revisions while remaining stable for the same session within
  one revision and revealing no token, name, contact, or domain text.
- **Institution Time-Zone Definition**: The configured local time-zone identity
  and its applicable standard/daylight observances required to interpret every
  exported event instant correctly.
- **Download Decision Context**: The transient valid-link, bound lecturer and
  revision, complete-projection, notice, and confirm/cancel state evaluated for
  one attempted file delivery; it creates no new domain record.

### Dependencies

- **FS-015 — Accountless Lecturer Token Review** supplies the valid bearer-link
  lifecycle, fixed lecturer and revision scope, complete current teaching/exam
  projection, restricted lecturer workspace, safe failure behavior, and
  accessibility baseline. Its projection remains authoritative at download
  evaluation.
- **FS-013 — Versioned Review and Publication Lifecycle**, through FS-015,
  supplies revision identity and the abandonment, publication, and supersession
  conditions that affect continued review access.
- **I-002 — Consistent Labels, European Dates, and Actionable Messages**
  supplies effective terminology and user-facing message conventions. The
  iCalendar standard's machine-readable date-time representation remains an
  allowed standards-based export format.
- Existing schedule data supplies stable session identity, course, cohort,
  study type, room/location, teaching units or exam duration, date, start/end,
  and assignment data already authorized by FS-015.
- The institution supplies one configured local time zone and one
  representative Outlook environment, including the account type and import
  path used for acceptance testing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of an acceptance matrix containing at least three
  lecturers, two revisions, 20 mixed teaching/exam sessions, multiple courses,
  active filters, restricted visible periods, assignment changes, and an empty
  projection, every successful file contains exactly one event for every and
  only the current sessions in its one authorized projection.
- **SC-002**: In 100% of expired, revoked, replaced, abandoned, superseded,
  malformed, unknown, incomplete, and inconsistent-projection cases, zero
  calendar files and zero schedule or event fields are delivered.
- **SC-003**: One hundred percent of the required conformance fixtures pass the
  independent RFC 5545 validation with zero syntax or structural errors.
- **SC-004**: One hundred percent of non-empty conformance fixtures import in
  the institution's representative Outlook environment without a repair
  prompt, rejected event, or count difference, and every checked event matches
  its source summary, local start/end, duration, Busy status, location, and
  description. The empty fixture produces zero events.
- **SC-005**: Across all daylight-saving, cross-midnight, and different-device-
  time-zone fixtures, 100% of imported event instants and durations match their
  source sessions.
- **SC-006**: Under identical FR-020 deterministic inputs, three consecutive
  exports of every unchanged fixture produce byte-for-byte identical files and
  filenames; 100% of same-session events in the same revision retain their UID
  after display-field changes, and 100% of distinct sessions and revisions have
  distinct UIDs.
- **SC-007**: Inside the release backend container constrained to 2 vCPUs and
  2 GiB memory, using one application process, release dependency pins, disabled
  debug instrumentation, SQLite on container-local storage, the deterministic
  seeded 100-session projection, and no concurrent requests, 100 measured
  complete-response exports after 10 untimed warm-ups have a p95 of at most
  three seconds and a maximum of at most ten seconds. The image digest, host
  CPU, Docker version, every sample, and percentile calculation are retained as
  acceptance evidence.
- **SC-008**: In an unaided usability review with at least 10 total
  participants, each either a representative lecturer or designated acceptance
  reviewer, `ceil(0.90 * participant_count)` can find the action, understand the
  notice, download the complete file, and import it in the institution's
  representative Outlook environment within five minutes.
- **SC-009**: In the same review, 100% of participants can state that the file
  is a static snapshot that remains available after the link ends, and
  `ceil(0.90 * participant_count)` correctly identify that repeat import may
  duplicate events and that later updates or removal are manual.
- **SC-010**: In 100% of privacy inspections, the filename, calendar metadata,
  events, UIDs, notices, and failures contain no link secret, other lecturer
  identity or assignment, contact data, student-level data, feedback,
  planner-only warning or note, or internal security data.
- **SC-011**: In 100% of success, cancel, authorization-failure, projection-
  failure, and retry cases, schedule, feedback, revision, publication, token-
  lifecycle, and provider data remain unchanged and no calendar-provider
  connection or request occurs.
- **SC-012**: In 100% of keyboard, supported assistive-technology, 200% text-
  zoom, and 320-CSS-pixel acceptance paths, the action, notice, event count,
  continue/cancel controls, and outcome remain understandable and operable
  without horizontal page scrolling or loss of the prior workspace context.

## Assumptions

- FS-015 has been revised as described in `docs/planning/Feature_slices.md`, and
  its complete current projection is the sole authority for event scope and
  permitted schedule fields.
- One scheduled teaching or exam session has exactly one assigned lecturer in
  the current scheduling model. Multi-lecturer sessions require a separate
  scheduling-model change and are not introduced here.
- The institution has one configured local time zone with sufficient
  standard/daylight rules for the full semester. All exported sessions use that
  institutional time zone even if the lecturer downloads elsewhere.
- The current production scheduling model creates same-day sessions. The
  cross-midnight conformance case uses a synthetic serializer-level event with
  explicit complete start and following-day end date-times; it does not expand
  the production scheduling model or infer rollover from an end time alone.
- Outlook is the primary manual-import target, but RFC 5545 conformance is the
  portability contract. The institution will identify one representative
  Outlook environment that permits manual `.ics` import for acceptance;
  successful acceptance does not imply an edition-by-edition, Outlook web,
  mobile, Mac, or other-client compatibility guarantee.
- Calendar and file labels use the effective I-002 terminology available at
  export time. Because terminology and time-zone definitions are deterministic
  inputs, changing either may intentionally change a later file.
- `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` remains stable in normal operation
  because it is an FR-020 deterministic UID input. Approved rotation of that
  key, or an approved serializer or `tzdata` upgrade, intentionally changes the
  deterministic input set and requires regenerated conformance fixtures and
  renewed Outlook evidence.
- The filename and calendar display name omit the lecturer name to reduce
  incidental disclosure when files are listed or shared. The event set itself
  remains personal schedule information and is covered by the notice.
- A valid complete projection may contain zero sessions. Allowing an explicit
  empty-calendar download preserves complete-scope semantics without implying
  that a partial or missing projection is empty.
- Stable UID behavior is guaranteed only for the same session within the same
  revision. This slice makes no cross-revision identity or calendar-client
  reconciliation promise.
- Static Outlook import behavior is controlled by Outlook. Stable UIDs improve
  event identity but do not guarantee that a repeated import updates or
  de-duplicates prior events.
- The downloaded snapshot is outside product control as soon as delivery
  succeeds. Token expiry, revocation, replacement, revision changes, and
  schedule edits affect future downloads only.
- A reference scope of 100 sessions is sufficient for one lecturer's complete
  teaching and exam assignments in one semester revision and aligns with the
  FS-015 lecturer-workspace acceptance boundary.
- No new persistence, provider account, calendar account, notification,
  invitation, or remote-cleanup capability is required for this slice.
