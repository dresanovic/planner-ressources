# Implementation Plan: FS-015 Accountless Lecturer Token Review

**Working Branch**: `master` | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`specs/015-lecturer-token-review/spec.md`

## Summary

Add one accountless review vertical slice on top of FS-013. A planner opens a
dedicated **Lecturer reviews** schedule destination, selects a lecturer in the
active Working revision, chooses one, two, or three days, and receives a
one-time bearer URL to copy and send manually. The public review shell uses
only the token held in memory to load that lecturer's current teaching and exam
assignments for the bound revision and to append advisory revision comments,
session comments, or impossible-session flags. The planner can revoke or
replace access, review retained feedback, filter prominently by impossible
flags, and open the existing session workflow without changing FS-013
publication rules.

The implementation stays inside the existing FastAPI, SQLAlchemy, React, and
Vite application. It adds one migration, three durable domain records, one
short-lived persisted misuse-state record, one backend service/router/schema
slice, one client API module, one planner workspace, and one isolated public
page. Tokens are random opaque values, stored only as digests and delivered in
a URL fragment. The trusted gateway protects planner pages and APIs, exposes
only the fixed public review page and two public API operations, and supplies
the authoritative client address used for invalid-token limits. No new
package, application authentication system, router, mail integration, approval
workflow, or multi-lecturer session model is introduced.

## Technical Context

**Language/Version**: Python 3.12 backend; TypeScript ~6.0 and React 19 frontend

**Primary Dependencies**: FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0,
Alembic 1.18, Uvicorn 0.49 trusted proxy-header support, React 19.2, Vite 8.1;
Python standard-library `secrets`, `hashlib`, `hmac`, `uuid`, and `asyncio`

**Storage**: Existing configurable SQLAlchemy database, SQLite by default;
schema migration `0009_lecturer_token_review.py`, including short-lived
restart-safe misuse state

**Testing**: pytest 9.1 backend service/API/migration/concurrency/performance
tests; Vitest 4/jsdom client API/component/page tests; fixed 20-operation
end-to-end response-time acceptance; ESLint and Vite build; manual keyboard,
assistive-technology, 200% zoom, and 320-CSS-pixel checks

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

**Constraints**: FS-013 lifecycle remains authoritative; gateway authorization
is a required deployment boundary and no in-application account redesign is
added; the backend has no direct public path; only `/lecturer-review/`, its
required static assets, `GET /api/public/lecturer-review`, and
`POST /api/public/lecturer-review/feedback` are public; caller forwarding
headers are discarded/overwritten; Uvicorn proxy trust is restricted to the
configured gateway and never wildcard; production public APIs are relative,
same-origin, and omit credentials; the protected source-fingerprint HMAC secret
contains at least 256 bits of random key material and is stable across
application restarts, and short-lived misuse state is stored in the existing
database; one lecturer per current schedule session; bearer secret
never persisted or logged in full; one-time secret reveal; exact expiry; generic
fail-closed unusable response; no schedule mutation; no third-party assets or
analytics on the public shell; all public responses are non-cacheable; misuse
limits must be exact; feedback is immutable and advisory; no new runtime
dependency

**Scale/Scope**: One semester revision and lecturer per link, one active link
per pair, one to three days of reuse, all of that lecturer's teaching and exam
sessions across courses, 2,000-character plain-text comments, up to 100 scoped
sessions and 200 retained feedback items in the acceptance reference set

## Constitution Check

*GATE: Passed before research and passed again after design.*

- **Spec-first — PASS**: `spec.md` defines this slice, its dependency on
  FS-013, explicit exclusions, 63 functional requirements, technical test
  requirements, edge cases, and measurable success criteria.
- **Acceptance criteria — PASS**: Four independently testable user stories
  include Given/When/Then scenarios. Planning reconciled the earlier shared
  session case with the repository's existing one-lecturer-per-session model
  and made multi-lecturer session modeling explicitly out of scope. The trusted
  gateway authorization and client-address boundaries are now explicit and
  testable.
- **Test-first — PASS**: Backend and client suites named below are written or
  updated before production behavior. Real assistive-technology, zoom, and
  moderated usability checks retain explicit manual paths because they cannot
  be established reliably in jsdom.
- **Simplicity and KISS — PASS**: The design uses existing stacks, source
  layout, lifecycle reads, calendar occurrence references, transaction
  patterns, and test tools. It adds no package, generic repository, event bus,
  worker, mailer, router, account model, or new scheduling cardinality.
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

Post-design re-check: the model and contracts preserve every gate. The three
new durable domain entities, one short-lived persisted misuse-state record, and
dedicated service are justified by link lifecycle, immutable retained feedback,
required activity evidence, and restart-safe enforcement of FR-054. The
gateway boundary is an external deployment contract, not a new application auth
layer. The misuse-state record uses the existing database, stores no raw network
address, and is physically removed within the required retention bound; no
additional cache or limiting service is introduced.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Extend the existing application with one
   lecturer-review vertical slice. Generate a 256-bit opaque token, persist
   only its digest, return the raw secret once, and let the planner client build
   `/lecturer-review/#/{secret}`. The public page passes the secret to fixed
   public API endpoints in an authorization header. The trusted gateway
   protects every planner surface, exposes only the public review surface, and
   supplies the client address trusted by Uvicorn. Derive the review from
   FS-013 content on every protected request, append immutable feedback, and
   expose a single planner workspace for links and feedback. Use existing
   occurrence references to open the current planner session workflow.
2. **Necessary abstractions**: One `lecturer_review` backend service centralizes
   secret validation, scope projection, concurrency, feedback capture, and
   misuse enforcement because both planner and public endpoints depend on the
   same security boundary. One client API module separates transport DTOs from
   the planner workspace and public page. Three retained domain entities are
   required separately for secret lifecycle, immutable business feedback, and
   privacy-safe activity evidence. One additional short-lived security-state
   entity is required only to keep the exact unusable-link limit authoritative
   across application restarts and is physically removed within 15 minutes.
3. **Deliberately excluded**: React Router, Redis, Celery, a general token
   framework, application-level planner accounts/authentication packages,
   application parsing of untrusted forwarding headers, email or messaging
   adapters, rich text, feedback threads/resolution, polling or live updates,
   arbitrary expiry dates, a new course-code field, multi-lecturer session
   relations, approval/deadline workflow, feedback-driven publication changes,
   independent feedback purge, and reusable generic repository or event-bus
   layers.

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
|   |-- db/
|   |   |-- migrations/
|   |   |   `-- 0009_lecturer_token_review.py
|   |   `-- schema.py
|   |-- models/
|   |   `-- planning.py
|   |-- schemas/
|   |   `-- lecturer_review.py
|   |-- services/
|   |   |-- lecturer_review.py
|   |   `-- schedule_lifecycle.py
|   `-- main.py
`-- tests/
    |-- api/
    |   `-- test_lecturer_review.py
    |-- db/
    |   `-- test_migrations.py
    |-- performance/
    |   `-- test_lecturer_review_performance.py
    |-- services/
    |   |-- test_lecturer_review.py
    |   `-- test_lecturer_review_concurrency.py
    `-- lecturer_review_fixtures.py

client/
|-- index.html
|-- src/
|   |-- api/
|   |   |-- lecturerReview.ts
|   |   `-- lecturerReview.test.ts
|   |-- components/
|   |   |-- ApplicationNavigation.tsx
|   |   |-- CourseSchedulePage.tsx
|   |   |-- LecturerReviewManagement.tsx
|   |   `-- LecturerReviewManagement.test.tsx
|   |-- pages/
|   |   |-- LecturerReviewPage.tsx
|   |   `-- LecturerReviewPage.test.tsx
|   |-- test/
|   |   `-- lecturerReviewFixtures.ts
|   |-- App.css
|   |-- App.tsx
|   `-- main.tsx
```

**Structure Decision**: Keep the established full-stack layout. Link models
remain in the existing planning model module, business and security rules stay
in one focused service, FastAPI schemas and routes follow current lifecycle
patterns, and the React client adds one planner destination plus a public-only
entry branch. The public page does not reuse planner calendar DTOs or
components, preventing accidental planner-data disclosure.

## Complexity Tracking

No constitution violations require exceptions.

## Verification Plan

Tests are added before their corresponding production changes. The focused
backend run must cover migration shape and upgrade, exact scope, generic
failure equivalence, secret canaries, one-time reveal, expiry boundaries,
idempotent feedback, lifecycle coupling, misuse thresholds, and file-backed
SQLite races. It must also prove that application code keys limits only from
`request.client.host`, caller forwarding headers do not alter that source,
trusted proxy-header handling yields independent source buckets, untrusted
peers cannot spoof the source, and the application exposes exactly the two
public API operations:

```powershell
Set-Location C:\Codex\planner-resource\backend
python -m pytest tests/services/test_lecturer_review.py tests/services/test_lecturer_review_concurrency.py tests/api/test_lecturer_review.py tests/performance/test_lecturer_review_performance.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_lifecycle.py tests/services/test_schedule_lifecycle_concurrency.py tests/api/test_schedule_lifecycle.py
python -m pytest
```

The focused client run must cover fragment parsing/removal, authorization
headers, isolated public rendering, one-time URL handling, clipboard outcomes,
duration/revoke/replace actions, exact flag-item counts, distinct session
groups, unavailable data, guarded Calendar navigation, inert comment text,
submission retry identity, generic ended-link states, throttling, accessible
names/status, and keyboard behavior. It must also prove exact
`/lecturer-review/` path selection before dynamically importing either surface,
preservation of that path after fragment removal, client construction of the
one-time URL from the returned secret, fixed relative public endpoints, and
`credentials: "omit"`:

```powershell
Set-Location C:\Codex\planner-resource\client
npm test -- src/api/lecturerReview.test.ts src/components/LecturerReviewManagement.test.tsx src/pages/LecturerReviewPage.test.tsx
npm test
npm run lint
npm run build
```

Manual acceptance uses `quickstart.md` and `contracts/gateway-boundary.md` to
verify that public requests can reach only `/lecturer-review/`, required static
assets, `GET /api/public/lecturer-review`, and
`POST /api/public/lecturer-review/feedback`; planner pages/APIs and direct
backend access are rejected; caller forwarding headers cannot select the
limiter source; and two distinct gateway-supplied client addresses receive
independent limits. It also verifies HTTPS URL copying, absence of the fragment
secret after bootstrap, no secret in network request URLs, browser history,
server logs, errors, or external referrers, a 320-CSS-pixel viewport, 200% zoom,
keyboard-only operation, supported screen-reader announcements, and the
moderated SC-006/SC-007 study. Verification evidence must record the environment
and result; participant criteria cannot be marked passed without the required
real reviewers.
