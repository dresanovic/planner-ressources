# Implementation Plan: FS-022 Consistent Labels, European Dates, and Actionable Messages

**Working Branch**: `master` | **Date**: 2026-08-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/I-002/spec.md`

**Note**: Planning is being completed on `master` in a working tree that already contains unrelated changes. Before production implementation begins, isolate this customer-facing cross-application slice on `codex/I-002-consistent-presentation` or an equivalent clean worktree and preserve the existing user changes.

## Summary

Deliver one German presentation layer across the existing planner and accountless lecturer surfaces without introducing a general localization system. FastAPI loads a complete source-controlled German terminology catalog and an optional customer override file once during startup, validates it before serving the application, and exposes the immutable effective labels through one public bootstrap endpoint. React removes any lecturer secret fragment first, fetches that catalog through the existing API-base convention before importing or rendering either application surface, and accesses selected context-specific terms through a small typed accessor. Ordinary German copy and complete messages remain fixed code.

Keep ISO calendar strings at API, persistence, sorting, URL, log, and export boundaries. At the UI boundary, strict pure helpers format date-only values as `DD.MM.YYYY`, parse only valid zero-padded European input back to ISO, and format timestamps in the established Europe/Vienna timezone. One reusable text-based date field replaces browser-native date inputs so the visible and accepted format is consistent across browsers; the optional calendar picker is deliberately omitted.

Represent user-visible failures and warnings as small structured problem items, map known domain/API conditions to truthful German content near the owning surface, and render multiple items with one accessible shared component. Existing recovery callbacks remain owned by each surface. The motivating outside-recommended-window condition uses existing scheduled and recommended dates and states that the placement is non-blocking and saved, with adjacent-edit or intentional-retain guidance. Existing domain decisions, severity, storage, and machine contracts remain authoritative.

## Technical Context

**Language/Version**: Python 3.12.8 for FastAPI; TypeScript 6.0.2 with JSX and React 19.2.7; Node 24 in the production image

**Primary Dependencies**: Existing FastAPI 0.139, Pydantic 2.13, React 19, React DOM 19, Vite 8.1, and standard-library JSON/Unicode/date capabilities; no new runtime dependency or i18n/date-picker library

**Storage**: One shipped UTF-8 German terminology JSON file plus one optional read-only deployment override file; effective labels live only in FastAPI application state and React memory. Existing SQLite business data and all user-entered records are unchanged.

**Testing**: pytest 9 for startup loader, public endpoint, safe lecturer projection, and backend regression; Vitest 4 with jsdom for catalog bootstrap/access, date helpers and fields, problem mapping/rendering, and affected surfaces; existing ESLint and TypeScript/Vite production build; manual verification on the latest stable Microsoft Edge, Google Chrome, and Mozilla Firefox on Windows, including 320 CSS pixels, 200% zoom, keyboard interaction, and NVDA with Firefox

**Target Platform**: Existing containerized Linux FastAPI service and the latest stable Microsoft Edge, Google Chrome, and Mozilla Firefox on Windows; layouts remain responsive to 320 CSS pixels without claiming separate mobile-OS browser certification. German document language and institution timezone are `de` and `Europe/Vienna`.

**Project Type**: Cross-stack presentation slice in the existing FastAPI/React/Vite web application

**Performance Goals**: Each browser bootstrap attempt performs exactly one terminology GET; an explicit Retry performs exactly one additional GET; normal navigation and interaction perform no further terminology request. Serving terminology reads immutable application state and performs no database query. Date formatting and message mapping are synchronous local operations that add no network request.

**Constraints**: German only; one immutable effective catalog per process; no rebuild for a customer override; fail startup for a configured invalid override; no blank/raw keys; `DD.MM.YYYY` visible and accepted everywhere; no calendar-day shift; preserve ISO machine contracts and existing 24-hour/timezone semantics; no invented causes/actions or diagnostic leakage; no automatic retry for ambiguous mutations; no new business rules, persistence, or external systems

**Scale/Scope**: All 35 current production TSX files across the planner and accountless lecturer React surfaces, 13 native date fields plus the multi-date entry, all inventoried raw date displays, and representative known validation/operation failure paths; one customer catalog per installation

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first - PASS**: The clarified specification is confined to `specs/I-002/` and defines the German terminology boundary, European date behavior, actionable-message taxonomy, exclusions, assumptions, edge cases, and measurable outcomes before production work.
- **Acceptance criteria - PASS**: Three prioritized stories are independently testable and contain Given/When/Then scenarios for configuration, every date boundary, known/unknown failures, multiple problems, and the motivating warning.
- **Test-first - PASS**: Loader/contract, pure utility, component, surface integration, backend regression, and manual accessibility/cross-browser checks are identified below. Tasks must place the failing automated test before each corresponding production change.
- **Simplicity and KISS - PASS**: The plan uses standard-library JSON, one startup loader, one bootstrap endpoint, one typed label accessor, pure date helpers, one date field, and one problem renderer. It adds no i18n framework, date library, global recovery registry, runtime switch, or administration UI.
- **Technology fit - PASS**: Backend changes remain inside FastAPI and frontend changes inside React/Vite. The only new HTTP interface and the deployment override format are defined under `contracts/`; every existing business API remains unchanged.
- **Delivery workflow - PASS WITH REQUIRED ACTION**: This is a broad customer-facing change and the current `master` worktree is not clean. Implementation must move to `codex/I-002-consistent-presentation` or an equivalent isolated clean worktree before production files are edited.
- **Verification before commit - PASS**: Focused and complete backend/client commands plus manual acceptance evidence are listed in this plan and `quickstart.md`.

### Post-design re-check

Phase 1 introduces no constitution violation. Startup loading is necessary to validate customer configuration before any UI is served; the single public endpoint is necessary because the same runtime catalog serves both React entry paths. The typed label accessor avoids a context/provider migration solely for immutable boot data. Shared date and problem presentation primitives have multiple immediate consumers identified by the inventory. Domain-specific message construction remains local instead of creating a speculative universal error framework. The accountless safe-warning projection retains its existing public response shape and exposes only allowlisted, user-visible context.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Load and validate one flat JSON override over shipped German defaults during the existing FastAPI lifespan; fetch the full effective map before React renders; use direct typed lookups for selected labels. Convert ISO dates only at UI boundaries with strict functions and a text date field. Convert known failures into small problem objects at their owning surfaces and render them as an accessible list with only the recovery action that surface already supports.
2. **Necessary abstractions**: A startup terminology loader plus typed client accessor is required for one runtime-selected catalog across both entry paths. Pure calendar helpers and `EuropeanDateField` are required because date rendering and entry are currently repeated broadly and native controls cannot guarantee the visible format. `UserProblem` plus `ActionableProblemList` is required to keep multiple problems distinct and provide consistent accessible semantics while domain mappers supply context-specific facts.
3. **Deliberately excluded**: Translation/i18n libraries, multiple languages, runtime locale switching, per-user catalogs, database-backed settings, terminology administration, automatic German inflection, template-token substitution in prose, a date or calendar-picker dependency, masked typing, three-part date inputs, global regex replacement, a universal backend error envelope, a global recovery/action registry, automatic mutation retry, new notification/support systems, diagnostic reference identifiers, API/storage/export date changes, and business-rule or severity changes.

Implementation MUST NOT begin until all three answers remain consistent with the approved FS-022 vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/I-002/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- terminology-overrides.schema.json
|   |-- ui-terminology-api.md
|   |-- presentation-contract.md
|   `-- surface-inventory.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md                                  # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- config/
|   |   `-- terminology.de.json              # complete shipped German defaults
|   |-- terminology.py                       # startup load, strict merge, app-state access
|   |-- main.py                              # lifespan validation and public router registration
|   |-- api/
|   |   `-- ui_terminology.py                # public immutable catalog response
|   |-- schemas/
|   |   `-- ui_terminology.py                # full effective-catalog response contract
|   `-- services/
|       `-- lecturer_review.py               # safe contextual German public projection
`-- tests/
    |-- api/
    |   `-- test_ui_terminology.py
    |-- services/
    |   |-- test_terminology.py
    |   `-- test_lecturer_review.py
    `-- test_main.py                          # invalid configured override blocks startup

client/
|-- index.html                               # German document metadata
|-- src/
|   |-- main.tsx                             # secret stripping, catalog bootstrap, safe failure/retry
|   |-- config/
|   |   |-- terminology.ts                   # exact-key validation and set-once typed accessor
|   |   `-- terminology.test.ts
|   |-- test/
|   |   `-- setup.ts                         # deterministic default catalog initialization for direct component tests
|   |-- utils/
|   |   |-- datePresentation.ts              # strict ISO/display parsing and zoned timestamps
|   |   |-- datePresentation.test.ts
|   |   |-- userProblems.ts                  # small model, common safe categories/fallback
|   |   `-- userProblems.test.ts
|   |-- components/
|   |   |-- EuropeanDateField.tsx            # visible/accepted DD.MM.YYYY entry
|   |   |-- EuropeanDateField.test.tsx
|   |   |-- ActionableProblemList.tsx         # separate accessible problem rendering/actions
|   |   |-- ActionableProblemList.test.tsx
|   |   `-- *.tsx                            # current date, term, and message consumers
|   |-- pages/
|   |   `-- *.tsx                            # planner/accountless inventory and domain mappers
|   `-- api/
|       `-- *.ts                             # existing ISO/domain contracts retained
`-- package.json                             # existing commands; no dependency change

compose.yaml                                 # optional read-only override path/environment
.env.example                                 # optional CUSTOMER_TERMINOLOGY_FILE example
infrastructure/docker/README.md              # operator setup and startup-failure behavior
```

**Structure Decision**: Keep the established FastAPI/React application boundary. FastAPI owns deployment configuration and validates the immutable catalog during its existing lifespan; React owns presentation. Shared frontend primitives cover proven repeated behavior, while domain-specific message mappers remain beside their current API/page owners. No database, new application, new package, or external service is introduced.

**Agent Context Update**: No `.specify/scripts/*/update-agent-context` script and no repository `AGENTS.md` are present in this Spec Kit installation. The prescribed updater location was checked after Phase 1; no context file was invented or modified.

## Design Decisions

### Runtime terminology configuration

- Ship a complete UTF-8 flat map of German defaults. Stable keys use `<concept>.<context>` and every context is an independently authored complete label; display values never drive identifiers, routing, filtering, or API values.
- `CUSTOMER_TERMINOLOGY_FILE` is optional. When unset, startup uses only defaults. When set, the referenced read-only JSON object may override any subset of known keys. Missing files, malformed/duplicate JSON keys, unknown keys, non-string or blank values, control characters, and unresolved defaults fail startup with operator-safe diagnostics that name the file/key but never log customer values.
- The effective catalog is merged once and stored immutably on `app.state`. `GET /api/public/ui-terminology` returns the complete map with `Cache-Control: no-store`; it requires no planner or lecturer credential and returns no secrets.
- `main.tsx` removes a lecturer secret fragment before any awaited request, resolves the fixed public path through the existing `VITE_API_BASE_URL` convention (same-origin in production), fetches it without credentials or authorization, validates the exact full key set, initializes the set-once catalog, and only then dynamically imports the planner or lecturer entry. One bootstrap attempt performs one GET; only the explicit Retry starts another. A fixed German bootstrap error names the configuration/load problem, exposes Retry, and never displays a raw key.
- Automated contract tests compare the property names in `contracts/terminology-overrides.schema.json`, the backend default JSON, and the client expected-key set. Direct component tests initialize deterministic defaults through `client/src/test/setup.ts`; override/bootstrap tests use isolated module state so the production set-once rule is not weakened.
- Initial configurable concepts are Course, Lecturer, Cohort, Room, Schedule, and Academic Data. Only contexts enumerated in the deployment schema are configurable. Ordinary German sentences, full messages, record values, and dynamically supplied names remain outside the catalog.

### European date boundary

- ISO `YYYY-MM-DD` remains the canonical client model for date-only business values. Formatting splits and validates components arithmetically; it never constructs a JavaScript `Date` from a date-only string.
- `formatCalendarDate`, `formatCalendarDateRange`, and `parseEuropeanDate` enforce exact zero-padding, leap-year/month validity, and reversible same-day conversion. Comparisons and sorting continue on validated ISO values.
- `EuropeanDateField` uses a labelled text input with `inputMode="numeric"`, persistent `TT.MM.JJJJ` help, stable hint/error IDs, `aria-invalid`, and no caret-moving mask. It maintains visible draft text separately, emits no stale prior ISO value while invalid, applies required/min/max checks after strict parsing, blocks button-driven submissions, and focuses/announces the field error only on attempted continuation.
- The current comma-separated unavailable-date control retains one text field but accepts `DD.MM.YYYY` tokens, identifies each invalid token separately, and converts valid tokens to ISO before calling the existing API.
- Timestamp formatting uses explicit `de-AT` two-digit date parts, 24-hour time, and the established `Europe/Vienna` meaning. `<time dateTime>` keeps the machine value. Institution-local “today” is derived from the configured timezone, not UTC slicing.
- The optional picker is omitted. Manual verification covers visible format and entry in the latest stable Edge, Chrome, and Firefox on Windows because browser-native date controls cannot guarantee `DD.MM.YYYY`; responsive behavior is additionally checked at 320 CSS pixels.

### Actionable problem presentation

- Use `UserProblem { key, tone, title, details, fieldId?, action? }` as a UI-only value. `tone` distinguishes blocking failures from non-blocking warnings; each problem has stable identity and separate text. `action` is present only when the current surface has a safe existing callback.
- A shared list renderer provides one newly presented blocking alert region, labelled non-blocking warning/status lists, keyboard-operable actions, focus visibility, wrapping, and field associations. It does not decide causes or recovery.
- Domain-local pure mappers combine typed status/code/field/safe metadata with caller-known operation, record, draft/saved state, and available callbacks. Raw backend messages, exception text, and codes are never primary copy. Unknown failures name only the attempted action and known state; ambiguous create/update/delete outcomes direct refresh/verification before retry.
- Preserve existing API envelopes and domain semantics. Replace joined message strings with arrays. Add backend facts only where already safely present in domain data; do not redesign error transport.
- The outside-window planner warning names the course/exam, scheduled date, recommended range, non-blocking/saved state, and the adjacent Edit control or intentional-retain path. The public lecturer projection retains its response shape but builds allowlisted contextual German text from public-visible occurrence/course data and validated safe finding values; it never forwards raw internal diagnostic content.

### Inventory and migration control

- Use the reviewed baseline in `contracts/surface-inventory.md` and complete its implementation evidence columns for every current planner/accountless surface: configurable-term keys, human-visible date fields/ranges/timestamps, problem categories, owning mapper, and automated/manual coverage.
- Migrate presentation only. API models, ISO payloads, database values, sort/comparison logic, URLs, logs, snapshots, and iCalendar/standards exports remain machine-formatted and are explicitly regression-tested.
- Source checks target approved catalog consumers and known raw-message/date presentation sites. They do not ban German nouns in fixed prose or ISO strings in API models, fixtures, tests, logs, and exports.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

Implementation must run focused tests first and then the complete suites. From the repository root:

```text
python -m pytest backend/tests/services/test_terminology.py backend/tests/api/test_ui_terminology.py backend/tests/test_main.py
python -m pytest backend/tests/services/test_lecturer_review.py backend/tests/api/test_lecturer_review.py
python -m pytest backend/tests
```

From `client/`:

```text
npm test -- src/config/terminology.test.ts src/utils/datePresentation.test.ts src/utils/userProblems.test.ts
npm test -- src/components/EuropeanDateField.test.tsx src/components/ActionableProblemList.test.tsx
npm test -- src/components/DraftSchedulePanel.test.tsx src/components/CalendarPlanningWorkspace.test.tsx src/components/SessionPane.test.tsx src/pages/CourseSchedulePage.test.tsx
npm test -- src/pages/LecturerReviewPage.test.tsx src/components/LecturerReviewManagement.test.tsx
npm test
npm run lint
npm run build
```

Expected: every command exits successfully; focused tests prove startup validation, exact label coverage, European conversion/input, safe distinct problems, and the motivating warning. Complete suites prove no change to domain, authorization, persistence, ISO transport/sorting/export, save/block, or severity behavior. Manual checks in `quickstart.md` additionally cover real browser date entry, 320 CSS pixels, 200% zoom, long labels/messages, keyboard focus, and NVDA with Firefox. If any command cannot run, implementation evidence must record the exact reason, unverified acceptance scenarios, and residual risk before commit.
