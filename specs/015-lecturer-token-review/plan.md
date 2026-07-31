# Implementation Plan: FS-015 Accountless Lecturer Token Review

**Working Branch**: `master` | **Date**: 2026-07-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`specs/015-lecturer-token-review/spec.md`

## Summary

Extend the implemented secure-link and immutable-feedback baseline without
changing its persistence, token lifecycle, gateway, or publication semantics.
The accountless page will adapt its already privacy-scoped projection into the
shared FS-014/FS-019 calendar/list workspace, suppress the lecturer selector in
favor of fixed context, expose only the permitted filter facets, and render the
shared adaptive session pane with feedback actions instead of planner actions.
The projection is refreshed only by browser reload or reopening the link;
feedback submission still revalidates current scope authoritatively.

Rename the existing planner **Lecturer reviews** destination to **Lecturer
coordination** and extend its current link-management and feedback grouping
with client-visible filters and counters that are all recomputed from the same
active filter scope. Current affected sessions continue to open through the
FS-019 Schedule navigation path; unavailable sessions retain captured
submission context. The extension stays inside the existing FastAPI,
SQLAlchemy, React, and Vite application, reuses the existing FS-015 endpoints
and records, and adds no migration, package, background refresh, router,
authentication model, generic Action Center, export, availability workflow, or
parallel lecturer schedule components.

## Technical Context

**Language/Version**: Python 3.12 backend; TypeScript ~6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0,
Alembic 1.18, Uvicorn 0.49 trusted proxy-header support, React 19.2, Vite 8.1;
Python standard-library `secrets`, `hashlib`, `hmac`, `uuid`, and `asyncio`

**Storage**: Existing configurable SQLAlchemy database, SQLite by default. The
implemented `0009_lecturer_token_review.py` link, feedback, activity, and
restart-safe misuse tables remain unchanged; this extension requires no new
table or migration.

**Testing**: pytest 9.1 backend service/API/privacy/projection/performance tests;
Vitest 4/jsdom API, adapter, shared-workspace, restricted-pane, coordination,
navigation, and public-page tests; existing migration/concurrency/security
regression; fixed 20-operation end-to-end response-time acceptance; ESLint and
Vite build; manual keyboard, assistive-technology, 200% zoom, 320-CSS-pixel,
and representative-reviewer checks

**Target Platform**: Modern browsers and FastAPI/Uvicorn reachable only through
a trusted HTTPS gateway; the gateway protects planner surfaces, exposes the
minimum public review surface, overwrites forwarding headers, and is the only
proxy address trusted by Uvicorn

**Project Type**: Existing full-stack web application and JSON API

**Performance Goals**: At the reference scope of 100 sessions and 200 retained
feedback items, at least 95% of valid review loads complete within three
seconds and feedback responses within two seconds; every load resolves to
usable or safe state within ten seconds and every submission within five
seconds

**Constraints**: FS-013 lifecycle and the implemented FS-015 security boundary
remain authoritative; FS-014/FS-019 components must be reused through an
explicit lecturer-review access profile; the public response must contain only
safe schedule fields and safe validation summaries, never planner-only data
that is merely hidden; the backend has no direct public path; only
`/lecturer-review/`, its required static assets,
`GET /api/public/lecturer-review`, and
`POST /api/public/lecturer-review/feedback` are public; caller forwarding
headers are discarded/overwritten; Uvicorn proxy trust is restricted to the
configured gateway and never wildcard; production public APIs are relative,
same-origin, and omit credentials; one lecturer per current schedule session;
bearer secret never persisted or logged in full; one-time reveal; exact expiry;
generic fail-closed unusable response; no schedule mutation; all public
responses are non-cacheable; misuse limits remain exact; feedback stays
immutable and advisory; filter/count changes are non-mutating; unsubmitted
feedback is transient; no timer, background polling, or separate in-workspace
refresh action; a non-public API request is classified as a lecturer request
only when its exact 43-character FS-015 bearer shape and digest resolve to a
stored active or ended lecturer-review link; unrelated bearer values remain
subject to the gateway's planner-authorization decision; no new runtime
dependency

**Scale/Scope**: One semester revision and lecturer per link, one active link
per pair, one to three days of reuse, all of that lecturer's teaching and exam
sessions across courses, 2,000-character plain-text comments, up to 100 scoped
sessions and 200 retained feedback items in the acceptance reference set

## Constitution Check

*GATE: Passed before research and passed again after design.*

- **Spec-first — PASS**: `spec.md` defines the implemented baseline and
  extension, dependencies on FS-013/FS-014/FS-019, explicit exclusions, 95
  functional requirements, 16 test requirements, edge cases, and 21 measurable
  success criteria.
- **Acceptance criteria — PASS**: Five independently testable user stories
  include Given/When/Then scenarios. Clarification fixes counter scope,
  unsubmitted-feedback protection, and reload-only projection refresh. The
  one-lecturer-per-session, gateway authorization, client-address, and
  restricted-component boundaries are explicit and testable.
- **Test-first — PASS**: Backend and client suites named below are written or
  updated before production behavior. Real assistive-technology, zoom, and
  moderated usability checks retain explicit manual paths because they cannot
  be established reliably in jsdom.
- **Simplicity and KISS — PASS**: The design extends the existing public DTO,
  derives an access-safe client presentation model, extracts only the neutral
  list renderer genuinely shared by planner and lecturer modes, and adds an
  access profile to the existing calendar and session pane. It reuses current
  endpoints, records, occurrence references, transactions, navigation, and
  test tools. It adds no package, table, generic repository, event bus, worker,
  mailer, router, account model, background polling, or new scheduling
  cardinality.
- **Technology fit — PASS**: FastAPI remains the API boundary, React/Vite
  remains the single client, and the cross-stack contract is recorded under
  `contracts/`.
- **Delivery workflow — PASS WITH PRE-IMPLEMENTATION ACTION**: Planning is on
  `master`. Because implementation is customer-facing and security-sensitive,
  implementation should begin on `codex/fs-015-lecturer-token-review`; this is
  a recommended delivery action, not a design gate.
- **Verification before commit — PASS**: Focused and full backend/client
  commands, contract review, security canaries, races, performance checks, and
  manual accessibility evidence are defined below and in `quickstart.md`.

Post-design re-check: the model and contracts preserve every gate. The existing
three durable domain entities and short-lived misuse-state record remain the
implemented security and feedback baseline; no extension persistence is added.
The revised public contract adds only fields required for the scoped
calendar/list projection and omits planner summaries, other lecturers,
mutation inputs, and unsafe validation context. Shared UI reuse uses explicit
access composition and a safe adapter rather than a second workspace or a
public call to planner APIs. The existing gateway boundary remains unchanged.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Keep the implemented token, endpoint,
   persistence, and gateway baseline. Extend the public projection with only
   semester dates, study type, teaching units or exam duration, safe lifecycle
   context, and sanitized current validation findings. Normalize that DTO to a
   small access-neutral presentation model, then render it through the existing
   `CalendarPlanningWorkspace`, a neutral list renderer extracted from the
   established list path, and `SessionPane` in a lecturer-review access profile.
   Rename the planner destination label and compute its filters, groups, and
   counters from the already loaded revision overview.
2. **Necessary abstractions**: The existing `lecturer_review` service remains
   the only backend security/projection boundary. The existing FS-014
   validation derivation is exposed as one internal reusable function rather
   than copied. Transport validation remains in `api/lecturerReview.ts`; the
   sole public-to-presentation adapter lives in
   `components/calendarWorkspaceUtils.ts`. One discriminated access profile on
   the calendar workspace and session pane makes permitted context, facets,
   fields, and actions explicit. One neutral occurrence-list renderer is
   extracted because both planner List mode and lecturer List mode now need the
   same selectable occurrence behavior.
   Existing records remain responsible for link lifecycle, immutable feedback,
   privacy-safe activity evidence, and restart-safe misuse enforcement.
3. **Deliberately excluded**: A public call to the planner calendar endpoint,
   fake planner DTO values, a parallel lecturer calendar or list, planner data
   fetched and hidden with CSS, React Router, Redis, Celery, a new migration,
   a general token framework, account/authentication packages, email or
   messaging adapters, rich text, feedback resolution, polling, live updates,
   an in-workspace refresh action, saved feedback drafts, arbitrary expiry
   dates, multi-lecturer session relations, approval workflow, export,
   availability submission, generic Action Center, and generic repository or
   event-bus layers.

Implementation MUST NOT begin until all three answers remain consistent with
the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/015-lecturer-token-review/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- gateway-boundary.md
|   |-- lecturer-review.openapi.yaml
|   `-- lecturer-review-ui.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- api/
|   |   `-- lecturer_review.py
|   |-- schemas/
|   |   `-- lecturer_review.py
|   |-- services/
|   |   |-- calendar_workspace.py
|   |   `-- lecturer_review.py
|   `-- main.py
`-- tests/
    |-- api/
    |   |-- test_lecturer_bearer_authorization.py
    |   `-- test_lecturer_review.py
    |-- performance/
    |   `-- test_lecturer_review_performance.py
    |-- services/
    |   |-- test_calendar_workspace.py
    |   `-- test_lecturer_review.py
    `-- lecturer_review_fixtures.py

client/
|-- index.html
|-- src/
|   |-- api/
|   |   |-- lecturerReview.ts
|   |   `-- lecturerReview.test.ts
|   |-- components/
|   |   |-- ApplicationNavigation.tsx
|   |   |-- CalendarPlanningWorkspace.tsx
|   |   |-- DraftSchedulePanel.tsx
|   |   |-- DiscardChangesDialog.tsx
|   |   |-- LecturerReviewManagement.tsx
|   |   |-- ScheduleOccurrenceList.tsx
|   |   |-- SessionPane.tsx
|   |   `-- calendarWorkspaceUtils.ts
|   |-- pages/
|   |   |-- CourseSchedulePage.tsx
|   |   `-- LecturerReviewPage.tsx
|   |-- test/
|   |   |-- calendarWorkspaceFixtures.ts
|   |   `-- lecturerReviewFixtures.ts
|   |-- App.css
|   |-- App.tsx
|   `-- main.tsx
```

Existing baseline files that are expected to remain unchanged except for
regression tests include:

```text
backend/app/db/migrations/0009_lecturer_token_review.py
backend/app/models/planning.py
backend/app/services/schedule_lifecycle.py
backend/tests/db/test_migrations.py
backend/tests/services/test_lecturer_review_concurrency.py
backend/tests/services/test_schedule_lifecycle*.py
```

**Structure Decision**: Keep the established full-stack layout. Link models
and migration remain unchanged, while business/security projection rules stay
in the focused service and existing routes. The public DTO is expanded but
remains separate from the planner calendar DTO. The client normalizes the safe
DTO into a shared presentation model only in `calendarWorkspaceUtils.ts`;
`lecturerReview.ts` remains responsible for transport types and exact-key
validation. The existing calendar validation service exposes one reusable
internal derivation so the lecturer projection can validate the full revision
before sanitization without duplicating FS-014 logic. Explicit restricted props
omit planner-only controls from the DOM, and one neutral occurrence list is
shared by planner and lecturer List modes. The public bootstrap may load those
shared presentation modules but never the planner App, planner API adapters, or
mutation callbacks.

## Complexity Tracking

No constitution violations require exceptions.

## Verification Plan

Tests are added before their corresponding production changes. The focused
backend run must preserve the implemented token, lifecycle, feedback,
idempotency, misuse, privacy, and concurrency baseline. Extension tests must
also prove that the public projection contains every and only current teaching
and exam assignment for the bound lecturer and revision; includes only
lecturer-safe calendar, facet, lifecycle, and validation fields; updates on a
new GET after assignment changes; rejects stale feedback against current scope;
and sanitizes full-revision validation results before returning them. A request
whose exact-shape bearer resolves to any stored lecturer-review link must be
rejected before validation or service execution on representative non-public
planner APIs, while unrelated bearer values and requests without lecturer
credentials must remain available to the gateway-authorized planner path.
Existing migration tests remain regression coverage; no migration is added.

```powershell
Set-Location C:\Codex\planner-resource\backend
python -m pytest tests/services/test_calendar_workspace.py tests/services/test_lecturer_review.py tests/services/test_lecturer_review_concurrency.py tests/api/test_lecturer_review.py tests/performance/test_lecturer_review_performance.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_lifecycle.py tests/services/test_schedule_lifecycle_concurrency.py tests/api/test_schedule_lifecycle.py
python -m pytest
```

The focused client run must preserve fragment removal, fixed relative public
requests, one-time URL handling, link lifecycle behavior, immutable feedback,
safe failures, and retry identity. Extension tests must cover the shared
calendar/list workspace in its restricted access profile, fixed lecturer
context, applicable filter intersection, authoritative-empty versus filtered
no-match states, exact teaching/exam selection, the restricted responsive
session pane, omission of planner actions from the DOM, and the unsubmitted
feedback discard guard. They must prove there is no polling or in-workspace
refresh, successful feedback is appended locally without reloading the
projection, and stale-target rejection provides reload/reopen guidance.

Planner tests must cover the `Lecturer coordination` label, item-first
intersection of all four filters, recomputation of all four counters from the
same active set, exact comment/impossible/distinct-session semantics,
partial/unavailable count qualification, and exact affected-session
navigation:

```powershell
Set-Location C:\Codex\planner-resource\client
npm test -- src/api/lecturerReview.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/LecturerReviewManagement.test.tsx src/components/SessionPane.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/LecturerReviewPage.test.tsx
npm test
npm run lint
npm run build
```

Manual acceptance uses `quickstart.md` and `contracts/gateway-boundary.md` to
verify that public requests can reach only `/lecturer-review/`, required static
assets, `GET /api/public/lecturer-review`, and
`POST /api/public/lecturer-review/feedback`; planner pages/APIs and direct
backend access are rejected; lecturer bearer credentials cannot access any
planner API; caller forwarding headers cannot select the limiter source; and
two distinct gateway-supplied client addresses receive independent limits. It
also verifies the familiar Week/Day/Month/List experience; filter and
responsive context preservation; restricted pane focus behavior;
full-reload-only assignment updates; safe draft-discard behavior; HTTPS URL
copying; absence of the fragment secret from browser and server surfaces; a
320-CSS-pixel viewport; 200% zoom; keyboard-only operation; supported
screen-reader announcements; and the moderated SC-006/SC-007 study.
Verification evidence must record the environment and result; participant
criteria cannot be marked passed without the required real reviewers.
