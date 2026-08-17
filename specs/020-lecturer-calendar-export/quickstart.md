# Quickstart and Acceptance Guide: Lecturer iCalendar Export

Use this guide after `/speckit-tasks` has produced test-first implementation tasks. It is a verification path, not permission to skip the failing-test step.

## 1. Prepare an isolated implementation workspace

FS-020 is customer-facing and security-sensitive. Start implementation on a clean isolated branch/worktree named `codex/fs-020-lecturer-calendar-export`. Transfer only `.specify/feature.json` and `specs/020-lecturer-calendar-export/` through a user-approved scoped commit or reviewed patch; do not switch the dirty planning workspace or move unrelated changes.

Confirm the effective configuration includes:

- a valid, stable `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY`;
- a resolvable `INSTITUTION_TIMEZONE` (default deployment value `Europe/Vienna`);
- pinned runtime dependencies including `icalendar==7.2.2` and the repository's pinned `tzdata`;
- the exact FS-020 public gateway path.

Read [spec.md](./spec.md), [data-model.md](./data-model.md), and all files under [contracts](./contracts/) before changing production code.

## 2. Write the failing backend tests

Create the focused service/API tests first. Cover:

- at least three lecturers, two revisions, several courses, and at least 20 total mixed teaching/exam sessions;
- every-and-only assignment scope and no cross-lecturer/revision disclosure;
- explicit complete empty projection versus missing/corrupt/incomplete snapshot;
- expired, revoked, replaced, abandoned, superseded, malformed, and unknown links;
- assignment/lifecycle changes after page load and during confirmed export;
- one coherent result under concurrency, never mixed or partial bytes;
- deterministic filename, calendar metadata, event order, DTSTAMP, `VTIMEZONE`, UIDs, and three byte-identical repeats;
- stable UID after display edits and distinct UID for identical-looking sessions/different revisions;
- all required text/time-zone/conformance fixtures and the full privacy deny-list;
- no schedule, feedback, revision, publication, link-lifecycle, view-limit, or provider mutation on a valid export;
- 100-event performance thresholds and safe 404/429/503 response contracts.

The 100-event performance test runs in the release backend container constrained to 2 vCPU and 2 GiB RAM, with one application process, release dependency pins, debug instrumentation disabled, container-local SQLite, the deterministic 100-session projection, and no concurrent requests. Use 10 untimed warm-ups followed by 100 measured complete-response exports. Retain the container image digest, host CPU model, Docker version, every sample, and the percentile calculation; require p95 at or below three seconds and maximum at or below ten seconds.

Current models need not be expanded for conformance-only cross-midnight or missing-location cases. Construct strictly typed synthetic serializer-level `CalendarEvent` fixtures; the cross-midnight fixture must supply complete start and explicit following-day end date-times rather than rely on clock-time rollover inference.

Run the intended tests and record the expected failures before production changes:

```powershell
python -m pytest backend/tests/services/test_lecturer_calendar_export.py backend/tests/api/test_lecturer_calendar_export.py backend/tests/services/test_lecturer_review_concurrency.py backend/tests/api/test_lecturer_bearer_authorization.py backend/tests/performance/test_lecturer_calendar_export_performance.py
```

## 3. Write the failing client tests

Before UI/API production changes, test:

- the action is present only in a valid complete lecturer workspace and remains outside filter/date controls;
- opening displays the complete unfiltered currently displayed count, explains that confirmation may re-evaluate to a different count, and shows the full static/privacy/repeat-import notice without making a request;
- cancel/Escape/focus trap/focus restoration and busy behavior;
- confirmation calls the API once with only the in-memory secret;
- active filters, visible period, mode, selection, scroll position, and unsent feedback do not affect the call and survive cancel/success/retryable failure;
- blob/media type/filename validation, exactly one temporary anchor activation, removal, and object-URL revocation;
- safe network/429/5xx retry and terminal 404 protected-DOM clearing;
- secret absence from URL, browser-visible messages, rejected metadata, and logged exceptions;
- zero events, long effective labels, narrow viewport structure, and accessible announcements.

```powershell
Set-Location client
npm test -- src/api/lecturerReview.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/LecturerCalendarDownloadDialog.test.tsx src/pages/LecturerReviewPage.test.tsx
Set-Location ..
```

## 4. Implement the smallest vertical slice

Implement in this order while keeping the new tests focused:

1. Pin the serializer dependency and validate the institution TZID at startup.
2. Add strict read-only export authorization/projection acquisition inside one transaction; harden published projection completeness.
3. Implement deterministic UID, filename, calendar/event/time-zone construction in the focused serializer service.
4. Add the exact FastAPI route, public allowlist entry, safe errors, and attachment/privacy headers.
5. Add the fixed-path client blob helper and strict response metadata validation.
6. Add the neutral workspace context-action slot, dedicated notice dialog, and page-local download orchestration.
7. Add only the CSS needed for wrapping, target size, focus, dialog errors, and narrow layouts.

Do not add an export record, preview endpoint, filter arguments, planner action, provider call, generic export framework, global store, or new terminology request.

## 5. Inspect deterministic calendar output

For every retained fixture, assert:

- one `VCALENDAR`, one bounded institution `VTIMEZONE`, and exactly the expected `VEVENT` count;
- the exact properties and forbidden-property absence in [icalendar-profile.md](./contracts/icalendar-profile.md);
- correct DST/cross-midnight instants and duration from a different device time zone;
- UTF-8 preservation, reserved-character escaping, embedded newline behavior, CRLF endings, and 75-octet folding;
- the exact NFC/Unicode-category/180-scalar/reserved-device filename algorithm plus fixed `resource-planner-calendar.ics` ASCII fallback;
- no lecturer identity/contact, another assignment, student data, feedback, planner warning/note, security state, token, URL, or raw identifier;
- three identical filenames/files from unchanged projection, terminology, label, TZID/rule, stable UID-key, serializer-version, and `tzdata` inputs.

Store the exact input manifest, expected fields, emitted `.ics`, SHA-256 checksum, serializer/tzdata versions, and test result under `specs/020-lecturer-calendar-export/validation/` for release review.

## 6. Run independent RFC validation

Before validation, record the institution-approved exact iCal4j release, official artifact URL, SHA-256 checksum, and install/validation commands in `specs/020-lecturer-calendar-export/validation/toolchain.md`. Download the artifact from that URL, verify its checksum, and use only that pinned CLI outside the application runtime. Then run every retained `.ics` fixture through:

```text
ical4j calendar validator -file=<fixture.ics>
```

Record the validator version, command, fixture checksum, date, and zero syntax/structural errors. A successful parse by Python `icalendar` is not a substitute for this independent check.

## 7. Verify the representative Outlook import

Document the designated environment before testing:

- Outlook product/edition and exact build;
- Windows version;
- account type;
- manual import/open path used;
- tester and date.

Import every required non-empty fixture and the explicit empty fixture. For each, record:

- no repair prompt or rejected event;
- imported count equals expected count;
- summary, local start/end, duration, Busy status, location, and description match;
- DST fixtures remain correct when the device display time zone differs;
- empty calendar creates no fabricated event.

Repeated import behavior is observational only: note what happens, but do not turn it into a product guarantee. No other Outlook edition or email/calendar client is part of formal acceptance unless the specification is amended.

## 8. Verify privacy and lifecycle behavior end to end

In a valid loaded workspace, apply restrictive filters, navigate to a date that excludes assignments, switch mode, select a session, and retain an unsent feedback draft. Open the notice, cancel once, then confirm:

- cancel delivers nothing and restores focus/context;
- the request URL/body contains no scope or secret and the Authorization header is the only bearer carrier;
- the file includes the entire current projection, not the visible subset;
- the server-provided filename contains no lecturer/token;
- no schedule/feedback/revision/publication/link-lifecycle/provider data changes.

Repeat with assignment removal/addition, link expiry/revocation/replacement, revision abandonment/supersession, incomplete projection, retryable interruption, and terminal unavailability between notice and confirmation. Expect a complete current file or a safe no-file outcome only.

## 9. Verify accessibility and responsive behavior manually

Use latest stable Edge, Chrome, and Firefox on Windows plus NVDA with Firefox:

- keyboard-only discovery and activation;
- one announced dialog name and description;
- announced event count, privacy notice, busy state, error, and success;
- Tab/Shift+Tab containment, Cancel default focus, Escape behavior, and opener focus restoration;
- no accidental backdrop confirmation or double modal with the narrow session pane;
- 200% text zoom and 320 CSS-pixel viewport with wrapped text/buttons and no horizontal page scrolling;
- long terminology and record values without truncating essential meaning.

Run the complete usability path with at least 10 representative lecturers. Require `ceil(0.90 * participant_count)` participants to find the action, understand the notice, download the file, and complete the designated manual Outlook import within five minutes. Apply the same threshold to correctly report repeat-import behavior and the need for manual removal; require every participant to understand that the file is a static snapshot. Retain anonymized participant counts, timings, outcomes, and calculation evidence.

## 10. Run regression and release commands

From the repository root:

```powershell
python -m pytest backend/tests/services/test_lecturer_calendar_export.py backend/tests/api/test_lecturer_calendar_export.py backend/tests/services/test_lecturer_review_concurrency.py backend/tests/api/test_lecturer_bearer_authorization.py backend/tests/performance/test_lecturer_calendar_export_performance.py
python -m pytest backend/tests/api/test_lecturer_review.py backend/tests/services/test_lecturer_review_concurrency.py
python -m pytest
Set-Location client
npm run lint
npm run build
npm test
```

Acceptance is complete only when the automated suite, independent validator evidence, designated Outlook import matrix, privacy/non-mutation checks, performance threshold, and manual accessibility/responsive checks all pass. Record any unavailable external environment as an explicit residual risk; do not silently downgrade it to a unit test.
