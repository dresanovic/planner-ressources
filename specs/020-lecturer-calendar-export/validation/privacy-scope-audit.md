# FS-020 Privacy and Scope Audit

Date: 2026-08-14. Result: **automated/static audit passed**.

- The only new public operation is exact `GET /api/public/lecturer-review/calendar`; route and gateway tests reject query scope, alternate paths, alternate verbs, and missing/malformed bearers.
- The browser sends the secret only in `Authorization`; it sends no course, lecturer, revision, filter, date, selection, filename, body, cookie, or credentials.
- The server re-resolves the link and current revision under the semester claim, then projects every and only the linked lecturer's assignments.
- Filename, `NAME`, `X-WR-CALNAME`, summaries, descriptions, UIDs, and retained bytes were inspected by tests. No lecturer identity/contact, other lecturer assignment, student data, feedback, validation finding, planner warning/note, access state, token, URL, or raw identifier is serialized.
- Event property allowlisting excludes `ORGANIZER`, `ATTENDEE`, `CONTACT`, `URL`, `VALARM`, invitations, provider/account metadata, `SEQUENCE`, `STATUS`, and `CLASS`.
- Static search of the production delta found no Outlook, Microsoft Graph, Exchange, subscription, provider, email, or background-sync call. The only new browser fetch is the fixed same-origin calendar path.
- Success uses `no-store`, `no-cache`, `no-referrer`, `noindex,nofollow`, and `nosniff`. Failures have safe JSON, no attachment disposition, no calendar media type, and no partial bytes.
- Database snapshots and concurrency tests show no schedule, feedback, publication, link lifecycle, access-view, export-record, or provider mutation from export. The response transaction is rolled back after serialization.
- `git diff --check` reported no whitespace error; only repository line-ending notices were emitted.

No provider fake was added because FS-020 performs no provider integration.
