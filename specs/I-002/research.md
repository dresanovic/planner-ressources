# Research: FS-022 Consistent Labels, European Dates, and Actionable Messages

## Decision 1: Load customer terminology in FastAPI at startup

**Decision**: Ship one complete flat German JSON catalog inside `backend/app/config/`, optionally merge a partial file selected by `CUSTOMER_TERMINOLOGY_FILE`, and fail FastAPI startup when a configured file or value is invalid. Store the immutable effective map in application state and expose it through one public same-origin endpoint.

**Rationale**: Customer terminology must change without rebuilding the application and invalid configuration must be detected before users receive an affected interface. FastAPI already owns process startup and serves the compiled SPA. Standard-library JSON plus the existing lifespan gives the operator a deterministic failure, works with a read-only bind mount, and needs no database, administration UI, or new dependency.

**Alternatives considered**:

- A Vite environment variable or imported customer file was rejected because it is embedded at build time and requires a customer-specific build.
- A file in `client/public/` fetched directly by the browser was rejected because browser-time validation cannot fail server startup or reliably report a deployment error before the service is considered ready.
- A database-backed settings page was rejected because it adds records, migrations, permissions, and runtime administration that are explicitly out of scope.
- Per-request HTML injection was rejected because template encoding and cache behavior add more moving parts than one bootstrap read.

## Decision 2: Use a typed immutable label accessor, not an i18n framework

**Decision**: React fetches and validates the complete effective map before importing either application entry. A small set-once module exposes a `TerminologyKey` union and `label(key)`; it never falls back to displaying the key. Initial configuration is limited to Course, Lecturer, Cohort, Room, Schedule, and Academic Data contexts enumerated by the contract.

The test environment initializes the shipped defaults once for direct component tests. Tests that exercise alternative catalogs or bootstrap failure isolate/reset the terminology module through Vitest module isolation; production code retains set-once behavior. Contract tests compare the exact key names in the JSON Schema, backend defaults, and client expected-key set.

**Rationale**: The installation has one German language and one catalog for its full process lifetime. There is no runtime switching, translation negotiation, pluralization, interpolation, or administration. A context/provider and localization package would solve requirements that do not exist. Dynamic imports already occur in `main.tsx`, so boot initialization prevents mixed defaults and overrides without re-render orchestration.

**Alternatives considered**:

- A full i18n library was rejected because multiple languages, message catalogs, locale switching, and plural rules are out of scope.
- React context was rejected for immutable boot data because it would add providers and test wrapping without a current runtime-change use case.
- Passing labels through component props was rejected because the same selected terms occur across many unrelated planner and accountless surfaces.
- Using display labels as category values was rejected because customer wording must never change routing, filtering, stored values, or API identities.

## Decision 3: Use flat context-specific keys and strict validation

**Decision**: Keys follow `<concept>.<context>` and each value is a complete UI label. The override is a partial top-level JSON object, all keys are allowlisted, and all supplied values must be nonblank single-line Unicode strings without control characters. Duplicate JSON properties, malformed JSON, unknown keys, non-string values, and configured unreadable files fail startup. Defaults are separately verified as complete.

**Rationale**: Flat keys are easy for deployment operators to review and override. Independent values for singular, plural, navigation, heading, field, and table contexts respect German grammar without implementing inflection. Strict allowlisting catches spelling mistakes and ensures blank or raw identifiers never reach users.

**Alternatives considered**:

- Nested concept objects were rejected because they make partial validation and operator diffing less direct without reducing the number of configured values.
- Automatically deriving plural or grammatical forms was rejected because German forms and institutional wording are context-sensitive.
- Token replacement inside sentences was rejected because it can produce grammatically broken German; complete messages remain fixed copy.
- Silently ignoring unknown or empty overrides was rejected because it conceals deployment mistakes and violates the no-blank/no-raw-key requirement.

## Decision 4: Fetch terminology only after lecturer-secret removal

**Decision**: On the accountless route, `main.tsx` extracts and removes the URL fragment before its first awaited operation. It then requests `/api/public/ui-terminology` through the existing `VITE_API_BASE_URL` convention, with no credentials or authorization, validates the full response, and imports the selected surface. Production remains same-origin. Each bootstrap attempt performs exactly one GET, ordinary interaction performs none, and an explicit Retry performs one additional GET. The endpoint sends `Cache-Control: no-store` and reads only immutable application state, without database work. A fixed German bootstrap failure with Retry is independent of the catalog.

**Rationale**: The current secret is fragment-based and must not be leaked in requests, browser history, errors, or telemetry. Removing it first preserves the existing security boundary. A no-store response avoids an old customer catalog surviving a service restart and costs only one small local request per page load.

**Alternatives considered**:

- Reusing domain API clients was rejected because they may attach authentication or domain error behavior and are unnecessary for public boot configuration.
- Caching the catalog indefinitely was rejected because the installation contract applies new values on restart and stale customer terms are confusing.
- Rendering defaults while loading was rejected because it produces a mixed-language/customer flash and could expose labels before override validation completes.

## Decision 5: Preserve ISO date-only values and format them arithmetically

**Decision**: `YYYY-MM-DD` remains canonical inside domain/API models. Shared pure functions strictly validate and split date-only strings, format them as `DD.MM.YYYY`, and parse exact European input back to ISO. Date-only helpers never call `new Date('YYYY-MM-DD')`. ISO values remain the basis for comparisons, ordering, payloads, URLs, persistence, logs, tests, and standards exports.

**Rationale**: Date-only values identify calendar days, not instants. Arithmetic validation and string conversion are reversible and cannot cross a timezone boundary. Keeping machine values unchanged confines the slice to presentation and protects existing contracts and sort behavior.

**Alternatives considered**:

- Constructing JavaScript `Date` instances from ISO dates was rejected because UTC/local conversion can shift the displayed day.
- Globally replacing ISO-looking text was rejected because it would corrupt logs, identifiers, user-entered text, URLs, fixtures, and export payloads.
- Changing API or database formats was rejected as out of scope and unnecessary.
- A date library was rejected because the required date-only transformations are small, strict, and covered by pure tests.

## Decision 6: Use one accessible text date field and omit a picker

**Decision**: Replace user-facing native date inputs with `EuropeanDateField`, a labelled text field using `inputMode="numeric"`, persistent `TT.MM.JJJJ` help, strict parsing, associated submit-time errors, and ISO output only while valid. Preserve required/min/max/range rules after conversion. The comma-separated unavailable-date input accepts European tokens and reports invalid tokens separately.

**Rationale**: Browser/operating-system native `type=date` controls do not guarantee that their visible editable value uses `DD.MM.YYYY`. A plain text field is the smallest cross-browser control that guarantees the required display and accepted syntax, remains keyboard/paste friendly, and can preserve existing ISO payloads. A picker is optional in the specification.

**Alternatives considered**:

- Native `type=date` with `lang="de"` was rejected because locale hints do not guarantee a consistent visible order across browsers.
- A third-party calendar picker was rejected because it adds a dependency and a substantial keyboard/focus/accessibility surface without being required.
- Three day/month/year inputs were rejected because they add tab stops, cross-field validation, and a less direct paste/edit experience.
- Input masks were rejected because caret manipulation commonly impedes editing and assistive technology; strict validation is sufficient.

## Decision 7: Distinguish date-only values from timestamps

**Decision**: For real instants, format with explicit `de-AT` two-digit date parts, 24-hour time, and the established `Europe/Vienna` timezone. Retain the machine instant in `<time dateTime>`. Derive institution-local today from a known instant in the configured timezone instead of UTC string slicing.

**Rationale**: Timestamps do require timezone interpretation; date-only values do not. Separate helpers preserve the current time meaning while making the calendar part consistent and removing browser-locale variability.

**Alternatives considered**:

- One universal date function was rejected because a date-only value and a timestamp have different semantics.
- Browser-default locale and timezone were rejected because output would vary by user device.
- Converting timestamp storage was rejected because timezone/data-contract changes are outside this presentation slice.

## Decision 8: Use a small problem model with domain-local mapping

**Decision**: Define a UI-only `UserProblem` with stable key, blocking/warning tone, title, detail lines, optional field association, and optional safe action. Domain-local pure mappers turn known status/code/field/safe metadata plus caller-known operation, record, saved/draft state, and available recovery into German problem items. One shared component renders separate items and accessibility semantics.

**Rationale**: Current components join multiple messages and often display `reason.message` or raw codes. A small common value/rendering shape solves the demonstrated repetition while leaving cause and recovery decisions close to the domain that knows them. Surface-owned callbacks prevent the presentation layer from inventing actions.

**Alternatives considered**:

- Translating all backend exception messages was rejected because backend text lacks surface-specific saved state, controls, and recovery context.
- One giant global code-to-message table was rejected because codes and safe actions vary by domain and caller context.
- A universal backend error-envelope redesign was rejected because existing typed status/code/field/meta data is sufficient for most cases and contract expansion is out of scope.
- Rendering arbitrary backend or exception messages was rejected because they are inconsistent, may expose diagnostics, and cannot be trusted as primary German copy.

## Decision 9: Recovery actions remain explicit and safe

**Decision**: A problem includes a direct button/link only when the current surface already exposes a safe callback. Loads may offer Retry. Stale writes require refresh and review. A connection loss during an ambiguous create/update/delete must tell the user to verify current state before retrying. If an adjacent Edit/Refresh control already exists, the message points to it instead of duplicating it.

**Rationale**: The UI cannot safely infer whether a failed network response means a mutation did or did not occur. Explicit caller-owned actions meet the actionable requirement without duplicating operations or creating a speculative recovery framework.

**Alternatives considered**:

- Automatic retry was rejected for mutation ambiguity and duplicate-operation risk.
- A global action registry was rejected because action availability is local and already represented by component callbacks.
- Adding buttons to every message was rejected because it can duplicate clearer adjacent controls or promise unavailable behavior.

## Decision 10: Preserve the accountless contract with a safe contextual projection

**Decision**: Keep the existing accountless lecturer response shape. Improve the backend's existing safe validation projection so allowlisted finding categories generate fixed German contextual messages from public-visible course/session context and validated supporting values. Client presentation may combine those safe messages with already public record context, but never receives or displays raw internal findings.

**Rationale**: The current public projection intentionally removes internal details but its generic English messages cannot satisfy the slice. Generating safe contextual copy at the established privacy boundary preserves the response contract and security intent while providing the facts the accountless UI is allowed to reveal.

**Alternatives considered**:

- Forwarding internal finding messages/metadata was rejected because it crosses the privacy boundary and may expose diagnostics.
- Adding a generic `safeDetails` transport object was rejected because it changes the public schema when the existing projection can generate safe user text.
- Leaving lecturer warnings generic was rejected because that surface is explicitly in scope.

## Decision 11: Drive breadth through an explicit inventory and layered tests

**Decision**: Create a reviewed migration matrix for every current planner/accountless surface with its configurable terms, display dates, date entries, problem states, owner, and test. Write pure and focused component tests before each migration, then run complete frontend/backend regressions and manual cross-browser/accessibility scenarios. Source checks are boundary-aware rather than banning all English or ISO literals.

**Rationale**: The behavior is cross-cutting and infrequent failure states are easy to miss. An inventory makes 100% success criteria reviewable. Boundary-aware checks avoid false positives in API models, fixtures, logs, exports, and fixed German prose.

**Alternatives considered**:

- Updating only the screenshot path was rejected because the approved scope covers all current surfaces.
- A repository-wide regex ban on ISO or noncatalog words was rejected because machine representations and ordinary prose intentionally remain.
- Manual-only verification was rejected because most conversion, mapping, and rendering behavior is deterministic and automatable; manual checks are reserved for browser and assistive-technology behavior.
