# Phase 0 Research: FS-013 Versioned Review and Publication Lifecycle

## Decision 1: Keep one relational working materialization and snapshot only inactive revisions

**Decision**: Continue using the existing `DraftSchedule`/`DraftSession` and `ExamSession` rows as the only mutable semester workspace. Add `ScheduleRevision` metadata for identity/state and capture a canonical versioned JSON snapshot when a revision becomes Published, superseded, or abandoned. Active Draft and Ready for review content remains relational and uses all existing scheduling, validation, occupancy, and editing behavior.

**Rationale**: Existing scheduling logic is built around one current course-semester draft and current semester exam rows. Adding a parent revision to every schedule row would require changing teaching uniqueness constraints, exam occupancy queries, generation inputs, catalog checks, and nearly every existing fixture. A hybrid model preserves those proven write paths while making historical content immutable and self-contained. Inactive revision content is always read or restored as a whole, so a canonical document is a better fit than queryable temporal rows.

**Alternatives considered**:

- Parent every `DraftSchedule` and `ExamSession` under a relational semester revision: rejected for this slice because it forces invasive query scoping and a SQLite table rebuild despite historical sessions never needing independent relational queries.
- Add separate normalized snapshot tables for courses, teaching sessions, and exams: rejected because it multiplies models, migrations, joins, and restore mapping without a requirement to query historical children independently.
- Use only the current live rows and record state metadata: rejected because a successor edit would change the content of the current publication and abandoned revisions could not retain their saved content.

## Decision 2: Add revision metadata and ordered lifecycle events as two persisted concepts

**Decision**: Add `ScheduleRevision` for semester-scoped stable identity, monotonic revision number, state, origin, optimistic row version, timestamps, and inactive snapshot document. Add `ScheduleRevisionEvent` for a stable semester-wide event sequence covering creation, Ready for review, return to Draft, publication, supersession, abandonment, and restoration.

**Rationale**: State on a course-level `DraftSchedule` cannot represent a semester publication. The revision row enforces current authority and future feedback association; the event rows are required because the specification retains every lifecycle transition, including repeated Ready/Draft and abandon/restore cycles. This is lifecycle history, not field-level edit audit.

**Alternatives considered**:

- Reuse `DraftSchedule.status`: rejected because it is per course and currently describes generation, while publication is semester-wide.
- Store only current-state timestamps on the revision: rejected because repeated transitions would overwrite earlier history.
- Introduce event sourcing: rejected because schedule edits remain normal current-state mutations and only seven lifecycle event types need durable history.

## Decision 3: Resolve initial lifecycle through deterministic migration and explicit empty-semester creation

**Decision**: Migration `0007` creates one Draft revision numbered 1 and one `created` event for each semester that already has a teaching draft or exam session, leaving all current schedule rows in place as that revision's live materialization. Semesters without schedule content remain without a revision until the planner explicitly chooses Start Draft, which establishes Draft revision 1 from the current empty saved content. Scheduling writes and publication remain unavailable before that action succeeds.

**Rationale**: Existing saved schedules must remain editable after upgrade without a manual conversion step. Creating empty revisions for every catalog semester would invent schedule history where none exists. This resolves the specification's “establish a working Draft from current schedule content” boundary without changing existing content.

**Alternatives considered**:

- Create revisions lazily on first read: rejected because a GET would mutate state and concurrent first reads could create duplicate history.
- Require the planner to adopt every existing schedule manually: rejected because it breaks the implemented FS-006/FS-012 workflow after upgrade.
- Create a Draft for every semester regardless of content: rejected because it conflates catalog existence with a created schedule revision.

## Decision 4: Define the immutable snapshot as the complete schedule, not its planning inputs

**Decision**: Snapshot every course represented in the semester publication decision, its scheduled/remaining teaching-unit summary, every teaching session, every saved exam session for the semester, semester/course/cohort/study-type/resource labels and reference codes needed for display, applicable schedule metadata, and conditions shown at publication. Generation constraints and mutable exam configurations remain planning inputs and are not published schedule content.

**Rationale**: The spec publishes the teaching and exam schedule and requires stable planner-visible context. Constraints and exam configurations guide future work but are not scheduled occurrences. Captured values prevent catalog renames, deactivation, availability changes, or later validation changes from rewriting a Published view.

**Alternatives considered**:

- Snapshot only dates and foreign keys: rejected because labels would change with current catalog data and violate immutable identifying context.
- Snapshot generation constraints and exam configuration rows: rejected as scope expansion into versioned planning inputs.
- Recompute published validation against current inputs: rejected because historical schedule meaning would drift; current validation applies only to active working content.

## Decision 5: Derive a complete non-blocking publication decision on the server

**Decision**: Publication preparation aggregates existing course remaining-unit gaps, teaching validation alerts, enabled-but-unscheduled exam conditions, saved exam validity issues, and soft recommendation deviations. It returns the semester, revision identity/state, first-versus-replacement consequence, prior current publication, all known conditions, and an opaque publication token. The token covers the active revision state, live schedule materialization, current publication, and captured identifying values.

**Rationale**: The planner must see all known conditions but may always publish. Server preparation avoids torn client-side warning calculations from independently loaded teaching and exam views. Rechecking the token at confirmation prevents the planner from publishing different content or context than was reviewed.

**Alternatives considered**:

- Publish immediately from the lifecycle overview: rejected because warnings or content can change between overview load and confirmation.
- Let the client combine teaching and exam warnings: rejected because separate refreshes can produce an inconsistent publication decision.
- Block on selected warning codes: rejected by planner control and the non-blocking specification.

## Decision 6: Use explicit state actions with optimistic and material-input protection

**Decision**: Lifecycle mutations carry the stable revision ID, expected revision row version, and opaque semester state token. Publication additionally carries the server-issued publication token and explicit confirmation. The service uses compare-and-set state checks, the existing semester transaction-claim convention, database uniqueness, and refreshed 409 responses.

**Rationale**: Row version detects changes to the target revision; the state token detects a different working/current publication; the publication token detects schedule, warnings, or catalog context changed after review. Long-lived locks are unnecessary and unsuitable for user confirmations.

**Alternatives considered**:

- Last-write-wins transitions: rejected because stale dialogs could supersede a newer publication or restore beside another working revision.
- Revision row version only: rejected because teaching/exam content and publication warnings can change without a lifecycle-state change.
- Hold a transaction open while the dialog is visible: rejected because it creates lock and failure risks across user think time.

## Decision 7: Enforce one working and one current publication at both service and database boundaries

**Decision**: Add a unique `(semester_id, revision_number)` constraint, a partial unique index for states `draft`/`ready_for_review`, and a partial unique index for state `published`. State check constraints and positive version/number constraints reject malformed rows. The service claims the semester boundary, performs allowed-state compare-and-set changes, translates integrity/stale conflicts into structured 409 responses, and never treats a repeated request as a new event.

**Rationale**: UI disabling and application prechecks cannot prevent two independent requests from racing. The partial indexes are the final SQLite-compatible integrity authority. Atomic transactions make the old publication remain current until its replacement succeeds.

**Alternatives considered**:

- Application-only uniqueness: rejected because concurrent create/restore or publish requests can both pass a precheck.
- Current revision pointers on `Semester`: rejected because they introduce cyclic references and couple academic catalog concurrency to schedule lifecycle.
- A new generic lock table: rejected because the existing semester claim plus database uniqueness is sufficient.

## Decision 8: Materialize and lock revision content according to lifecycle state

**Decision**: Existing schedule writes call `require_active_working_revision(semester_id)` before mutation. Draft and Ready for review permit writes; Published-only, superseded, and abandoned contexts reject them with `WORKING_REVISION_REQUIRED` or `REVISION_NOT_EDITABLE`. Publishing captures the snapshot and leaves the live rows as a locked mirror. Starting a successor replaces that live mirror from the current Published snapshot; abandonment captures the working snapshot and locks the live rows; restoration replaces the live materialization from the abandoned snapshot and returns the same revision to Draft.

**Rationale**: Leaving a locked mirror preserves existing foreign-key protection and avoids clearing/recreating rows immediately after publication. Explicit successor creation prevents any existing generation/edit endpoint from silently modifying the publication. Restoration remains exact even if another revision used the workspace in between.

**Alternatives considered**:

- Clear live rows after publish or abandon: rejected because it needlessly removes referential protection and complicates current-publication display fallback.
- Automatically create a successor on the first edit after publication: rejected because the specification requires explicit working revision creation and clear state visibility.
- Allow Ready edits to return automatically to Draft: rejected because Ready is informative and the planner alone controls state transitions.

## Decision 9: Protect source records referenced only by inactive snapshots

**Decision**: Academic/resource hard-delete assessment must treat source identifiers retained by Published, superseded, and abandoned snapshot documents as historical schedule references. Referenced records remain protected or are deactivated under existing catalog rules. Published display always uses captured values, not joins. Restore/start operations revalidate that required source identities are still materializable and report a clear conflict rather than silently substituting resources.

**Rationale**: An older abandoned revision may be restored after a newer workspace has replaced the live mirror. Without historical-reference protection, a hard-deleted course/resource could make the required restore impossible. Existing planner-controlled deletion paths are the correct place to preserve this invariant without adding polymorphic reference tables.

**Alternatives considered**:

- Add normalized foreign-key rows for every snapshot reference: rejected because it recreates much of the normalized snapshot schema solely for deletion protection.
- Recreate deleted catalog records during restore: rejected because it silently changes academic data ownership.
- Allow partial restore: rejected because the specification requires saved revision content to be retained.

## Decision 10: Expose lifecycle summaries separately from selected revision content

**Decision**: `GET /api/semesters/{semester_id}/schedule-lifecycle` returns active-working/current-publication summaries, complete ordered revision/event metadata, state token, and allowed actions. `GET /api/schedule-revisions/{revision_id}` returns one active live or inactive snapshot body. Creation, preparation, and transition endpoints return authoritative refreshed lifecycle state.

**Rationale**: Complete retained history can grow, while a planner normally needs only metadata until selecting one revision. Separating history summaries from content keeps overview responses bounded and avoids loading every past semester body.

**Alternatives considered**:

- Embed all snapshot bodies in lifecycle overview: rejected because retained history would make every refresh progressively larger.
- Reuse teaching-only and exam-only APIs for historical content: rejected because they resolve current state and cannot guarantee one coherent immutable revision.
- Add course-level lifecycle routes: rejected because publication scope is semester-wide.

## Decision 11: Integrate lifecycle UI into the existing Schedule page

**Decision**: Add a dedicated lifecycle client API, `ScheduleLifecyclePanel`, `PublicationConfirmationDialog`, and focused abandon confirmation. `CourseSchedulePage` owns authoritative refresh and selected revision context. `DraftSchedulePanel` gains a dynamic context label and read-only mode; historical rendering uses captured snapshot values and omits all teaching and exam mutation controls.

**Rationale**: The Schedule page already owns semester selection, teaching/exam orchestration, stale refresh, and write locks. Focused components keep lifecycle presentation out of the already-dense page without adding global state. Reusing the review panel preserves list/week/filter behavior.

**Alternatives considered**:

- Build a separate publication page: rejected because it duplicates semester schedule review and conflicts with incremental FS-014 delivery.
- Add lifecycle state to Academic Data: rejected because publication is an operational schedule action.
- Add Redux or another client state library: rejected because one page remains the state owner.

## Decision 12: Preserve captured labels and freeze writes across incomplete refreshes

**Decision**: Active working views may continue enriching live data through current catalog context. Published/superseded/abandoned views must explicitly use captured values and never pass through current-catalog enrichment. Lifecycle refresh joins the existing teaching/exam authoritative refresh; if it fails, the last complete view remains visible but all writes stay disabled until retry succeeds. A 409 closes the dialog, refreshes all semester state, and requires the planner to reopen the action.

**Rationale**: Current `DraftSchedulePanel` replaces saved lecturer/room labels with current catalog values, which would violate snapshot immutability. Lifecycle state determines edit authority, so a page that cannot refresh it safely cannot allow further schedule writes. This matches existing stale confirmation and refresh-failure behavior.

**Alternatives considered**:

- Trust client state after a mutation: rejected because current publication authority may have changed.
- Keep buttons enabled while lifecycle refresh is unavailable: rejected because the client cannot know whether it is editing a working or locked revision.
- Disable rather than omit historical edit controls: rejected because controls would imply unsupported actions and complicate accessibility.

## Decision 13: Extend the migration chain and backfill without rewriting schedule content

**Decision**: Add `0007_versioned_schedule_lifecycle.py` after FS-012 migration `0006`, create the two new tables/indexes, and backfill revision/event metadata from existing semester schedule presence. Update sequential schema recognition and test clean creation, 0006→0007 upgrade, data preservation, repeated initialization, malformed partial schema rejection, integrity constraints, and safe downgrade behavior.

**Rationale**: The hybrid design requires no change to existing teaching/exam row shape or uniqueness and therefore avoids an SQLite table rebuild. Supported databases gain lifecycle identity without moving current content.

**Alternatives considered**:

- Rewrite prior migrations: rejected because they are project history and FS-012 is a dependency.
- Rely on `Base.metadata.create_all`: rejected because it cannot upgrade an existing FS-012 database.
- Backfill snapshot bodies for active Draft revisions: rejected because active content remains authoritative in relational rows; a snapshot is created only when the revision becomes inactive.

## Decision 14: Use bounded reference-scale verification without a new observability layer

**Decision**: Validate publication preparation, publication, successor materialization, current-publication detail, and a 100-revision history summary under 2 seconds for 100 courses, 500 teaching sessions, and 100 exams using file-backed SQLite. Keep history summary and body reads separate and assert bounded query behavior. Use existing tests and manual evidence rather than adding runtime metrics infrastructure.

**Rationale**: Lifecycle work is transaction/copy/read work rather than optimization. The target is comfortably user-facing and catches accidental N+1 history or snapshot construction. A production telemetry stack is outside this slice.

**Alternatives considered**:

- Reuse the FS-012 60-second solver target: rejected because lifecycle operations should not inherit solver latency.
- Add monitoring/telemetry dependencies: rejected as unrelated infrastructure.
- Claim percentile latency from one unit-test run: rejected because the repository lacks a representative production benchmark environment.

## Decision 15: Use unambiguous lifecycle instants and explicit local display

**Decision**: Persist lifecycle timestamps as UTC instants and serialize them as RFC 3339 offset-bearing values. Render planner-facing lifecycle and publication times in the institution timezone, Europe/Vienna for this slice, with a machine-readable value and an explicit visible timezone indication.

**Rationale**: Publication and event history must keep one stable chronological meaning across daylight-saving changes, clients, and later inspection, while planners need locally meaningful times.

**Alternatives considered**:

- Store or exchange timezone-free local values: rejected because repeated or skipped daylight-saving times are ambiguous.
- Display an unlabeled browser-local time: rejected because two planners could interpret the same lifecycle event differently.
