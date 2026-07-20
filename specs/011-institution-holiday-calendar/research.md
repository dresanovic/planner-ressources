# Research: FS-011 Institution-Wide Holiday Calendar and Avoidance

## Decision 1: Model one logical calendar as current holiday rows

**Decision**: Add one `InstitutionHoliday` entity with stable ID, unique full date, trimmed readable name, and optimistic revision. The institution-wide calendar is the ordered collection of those rows; there is no persisted calendar owner or singleton.

**Rationale**: The feature requires exactly one calendar and current-state CRUD. A singleton adds locking and lifecycle concepts without user value. Unique date directly enforces one current holiday per day, and stable ID/revision supports safe edits and future import work without committing to provider identity.

**Alternatives considered**:

- Reuse `ResourceUnavailabilityPeriod`: rejected because it requires a Lecturer/Room owner and time ranges.
- Add a `HolidayCalendar` singleton: rejected because no current requirement needs calendar metadata or multiple calendars.
- Key holidays only by date: rejected because edit forms and stale-write detection benefit from stable identity.

## Decision 2: Retain no holiday history or archive state

**Decision**: Successful edits replace current values and increment revision; confirmed deletion physically removes the row. Do not add history, soft-delete, archive, provider, or timestamp fields.

**Rationale**: This directly implements the clarification that changed/removed holiday facts need not be retained. Saved sessions are independent rows and therefore remain untouched. FS-013 must solve any publication-specific need without relying on FS-011 holiday history.

**Alternatives considered**:

- Immutable or versioned holiday records: rejected by clarification and KISS.
- Archive/reactivate: rejected because removed holidays must stop affecting current generation/alerts and no historical discovery requirement remains.
- Event log: rejected as speculative.

## Decision 3: Use a focused holiday API/service instead of generic catalog lifecycle code

**Decision**: Add `holiday_calendar` API, schema, and service modules with `/api/holidays` CRUD endpoints and the established structured error envelope.

**Rationale**: Existing academic/resource administration assumes active/inactive lifecycle, dependency usage, archive, or resource ownership. Holidays have a smaller current-state lifecycle and are also consumed directly by generation and validation. A focused module is clearer and smaller than widening generic registries with exceptions.

**Alternatives considered**:

- Add holidays to `academic_catalog.py`: rejected because its status/usage/protected-delete assumptions do not apply.
- Add holidays to resource administration: rejected because holidays have no resource owner.
- Put CRUD directly in the router: rejected because generation/validation need the same canonical query and snapshot behavior.

## Decision 4: Extend the sequential migration chain with 0005

**Decision**: Add `0005_institution_holidays.py`, recognize the current 0004 schema as a valid predecessor, and require the holiday table/constraints in the new schema-head check.

**Rationale**: The application uses custom sequential Alembic operations in `backend/app/db/schema.py`. Clean databases use current metadata; existing databases must upgrade in the established order. No legacy holiday backfill exists.

**Alternatives considered**:

- Create the table opportunistically at runtime: rejected because it would bypass supported-schema verification.
- Add an external Alembic CLI workflow: rejected because the repository has a working migration loader and no need for a second mechanism.

## Decision 5: Load maintained holidays only on the server

**Decision**: Each generation/review request loads relevant current holidays directly from storage. Browsers never fetch and merge holidays into generation payloads.

**Rationale**: Holidays are hard constraints. Server-side loading prevents stale or manipulated client state from weakening them and gives every existing generation mode one authoritative calendar.

**Alternatives considered**:

- Client-supplied holiday arrays: rejected as non-authoritative and race-prone.
- Cache holidays in session records: rejected because edits/removals must refresh alerts without rewriting sessions.

## Decision 6: Preserve FS-010 caller unavailable dates as a distinct input

**Decision**: Keep public `unavailableDates` semantics unchanged. Internally union those dates with maintained holiday dates for exclusion, while preserving distinct evidence codes and never echoing maintained holidays as caller input.

**Rationale**: FS-010 already supports arbitrary planner unavailable dates. Removing or repurposing that contract would regress an implemented dependency. Echoing holidays into the caller array would make a later-removed holiday persist as an unrelated exclusion.

**Alternatives considered**:

- Replace `unavailableDates` with holidays: rejected as an FS-010 regression.
- Return the effective union to the client: rejected because echoed holidays would acquire the wrong ownership/lifecycle.
- Treat both sources as generic dates: rejected because FS-011 requires holiday name/date explanations.

## Decision 7: Carry structured named-holiday evidence

**Decision**: Add `INSTITUTION_HOLIDAY` plus optional `holidayDate` and `holidayName` fields to generation failure/reason items. Produce one item per substantiated holiday and deduplicate by code plus date.

**Rationale**: Structured context makes the required date/name verifiable and avoids brittle message parsing. It also allows several holidays to be shown without key collisions while retaining existing outcome classifications and generic renderers.

**Alternatives considered**:

- Message text only: rejected because tests and future consumers would need to parse prose.
- One reason containing an array: rejected because current contracts and renderers already operate on independent reason items.
- List every semester holiday: rejected because reasons must be substantiated by the attempted planning space.

## Decision 8: Revalidate the complete relevant holiday set before persistence

**Decision**: Canonically snapshot holidays as `(id, date, name, revision)` and reload them inside the generation persistence boundary. FS-010 folds the snapshot into existing opaque tokens; single and legacy multi perform final current-calendar validation before replacement.

**Rationale**: Row revision alone cannot detect a different holiday being inserted or deleted during generation. Final reload prevents a newly added/re-dated holiday from receiving a generated session and ensures names in explanations are current. Existing semester write-barrier and stale-result patterns provide the safest direct fit.

**Alternatives considered**:

- Add a singleton calendar revision solely for locking: rejected until a real cross-database need justifies it.
- Ignore changes during synchronous generation: rejected by FR-015.
- Automatically rerun generation: rejected because the spec requires review/retry and forbids silent changes.

## Decision 9: Derive alerts on schedule reads

**Decision**: Extend `collect_validation_alerts` with a date-keyed holiday map and append a non-blocking `INSTITUTION_HOLIDAY` alert containing the date/name. Persist no alert rows or holiday snapshots on sessions.

**Rationale**: Existing alerts are derived centrally when schedule responses are built. Reusing this boundary makes create/edit/delete visible after a normal reload and guarantees calendar maintenance never mutates sessions.

**Alternatives considered**:

- Persist alerts and update them on every holiday mutation: rejected because it duplicates derivable state and creates bulk-update failure modes.
- Block manual sessions on holidays: rejected by the explicit manual-warning rule.
- Add special holiday properties to sessions: rejected because the current generic alert contract is sufficient.

## Decision 10: Add focused administration but no standalone review entries

**Decision**: Add Holidays as an Academic Data navigation leaf with a small dedicated list/editor/delete confirmation. Reuse generic session alert rendering in list/weekly review and do not pass standalone holiday data into schedule components.

**Rationale**: The clarification defers standalone review display to FS-014. Current generic catalog components encode archive/status semantics that holidays lack, while existing alert components already satisfy affected-session review.

**Alternatives considered**:

- Reuse the generic Academic Record editor/list unchanged: rejected because dates would be hidden and status/archive behavior would be misleading.
- Add a new page/route: rejected because the established Academic Data shell already owns planner administration.
- Render empty holiday days/cards in weekly review: rejected by clarification.

## Decision 11: Refresh the selected semester after holiday mutations

**Decision**: Use the existing catalog revision notification, but extend `CourseSchedulePage` so an external administration change reloads both planning options and current semester schedules without resetting selection, filters, or view mode.

**Rationale**: Current external revision handling reloads planning options only, so holiday alerts would otherwise remain stale. Existing manual/generation mutations already use the authoritative overview reload and last-known-state error pattern.

**Alternatives considered**:

- Push events or WebSockets: rejected because one planner and explicit mutations do not justify background infrastructure.
- Mutate current client alerts locally: rejected because server-derived validation is authoritative.
- Force the planner to leave/reopen Schedule: rejected by the 2-second refresh requirement.

## Decision 12: Add no import abstraction in FS-011

**Decision**: Leave CSV/iCalendar formats, external identity, matching, ownership, batch atomicity, and synchronization policy to FS-017.

**Rationale**: Unique date, stable ID, and revision are enough current foundations. A re-dated iCalendar event may require provider UID matching, while CSV may use date matching; choosing now would violate the explicit out-of-scope boundary and constitution's no-hypothetical-complexity rule.

**Alternatives considered**:

- Add nullable provider/source fields now: rejected because the provider and ownership rules are unknown.
- Build an importer alongside CRUD: rejected as direct scope expansion.

## Resolved Technical Context

- **Runtime**: Python 3.12.8; TypeScript 6.0; React 19; Node.js 26.4.0 for the current local toolchain.
- **Storage**: SQLite through SQLAlchemy with custom sequential Alembic migrations.
- **Interfaces**: Synchronous JSON HTTP endpoints and existing derived Draft Schedule response alerts.
- **Dependencies**: No new package.
- **Limits**: Reference acceptance dataset of 50 holidays and 500 sessions; load holidays once per request/range.
- **Outstanding clarifications**: None. Import and publication behavior are intentionally deferred, not unresolved within FS-011.
