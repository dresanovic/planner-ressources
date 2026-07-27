# Research: FS-014 Calendar Planning Workspace

**Date**: 2026-07-23  
**Specification**: [spec.md](spec.md)

This research resolves the technical choices required to plan FS-014. It does
not add product behavior beyond the specification.

## Decision 1: Use one coherent revision-scoped workspace read

**Decision**: Add one composite read contract,
`GET /api/semesters/{semester_id}/calendar-workspace`, with an optional
`revisionId`. The response identifies exactly one active Working or Current
Published revision and contains the bounded courses, occurrences, holidays,
current findings, retained outcomes, authoritative full-scope summaries,
filter facets, and section availability needed by every workspace mode.

**Rationale**: Calendar cards, summaries, details, and revision labels must
describe the same atomic context. A single response prevents independently
loaded panels from mixing revision data and gives the client one token with
which to reject stale refreshes.

The contract uses distinct loaded and no-revision response variants. A
no-revision response has no revision-owned records or filter facets and exposes
only not-applicable summaries with `no_revision` scope, preventing it from
being interpreted as a loaded empty schedule.

**Alternatives considered**:

- Several panel-specific endpoints were rejected because independently
  completing requests could produce torn revision context and false totals.
- Reusing only the existing schedule endpoints was rejected because they do not
  provide retained outcomes, cross-record traceability, section availability,
  or Current Published validation as one coherent read.
- A generic reporting/read-model framework was rejected as unnecessary for one
  bounded vertical slice.

## Decision 2: Persist only the latest applicable planning outcome

**Decision**: Add one `planning_outcomes` table keyed uniquely by revision,
course, and operation kind. Store the latest completed per-course outcome using
the canonical operation kinds `single_course_generation`,
`multi_course_generation`, `semester_optimization`, and `exam_generation`.
Classifications are `successful`, `failed`, `stale`, `unchanged`, and
`skipped`. A retry uses its underlying operation kind rather than creating a
fifth kind.

Every reliable completed per-course outcome is upserted, including successful
and unchanged outcomes, so a later non-failure can supersede an older failure.
Request validation failures, confirmation-required responses, cancellations,
and operation-level failures with no reliable per-course result are not
retained.

**Rationale**: The clarified requirement needs cross-reload availability and
precise supersession, but not an audit history. Persisting only failures would
leave an older failure visible after a later success.

**Alternatives considered**:

- Client memory or response-only outcomes were rejected because reloads and
  later visits must preserve the latest applicable result.
- An append-only outcome history was rejected because the workspace needs only
  current operational state and FS-014 does not request audit history.
- A semester-level outcome blob was rejected because per-course/per-kind
  supersession and traceability would become ambiguous.

## Decision 3: Keep outcome retention transactionally aligned with operations

**Decision**: When an operation mutates a schedule successfully, retain its
per-course outcome in the same transaction. For an expected completed
per-course result that intentionally makes no schedule mutation, recheck the
active revision and commit the outcome-only upsert. Never retain an outcome
against a revision that became stale during the operation.

**Rationale**: The workspace must not show an outcome for a mutation that rolled
back or associate a completed attempt with the wrong successor revision.

**Alternatives considered**:

- Fire-and-forget or a separate background write was rejected because it could
  diverge from the saved schedule and adds infrastructure outside this slice.
- Treating every HTTP error as a retained course failure was rejected because
  transport and request failures do not always establish a reliable
  course-level outcome.

## Decision 4: Revalidate Published sessions without mutating their snapshot

**Decision**: For Current Published, parse only the selected Published
snapshot's teaching and exam occurrences and evaluate those occurrences against
current holidays, rooms, resources, and other applicable planning facts.
Expose those results as `current` validation overlays. Do not load Working or
historical occurrences into that evaluation and do not write into the snapshot.

New publications use snapshot schema version 2, extending the captured course
context with the constraint data needed to interpret Published occurrences.
Version 1 snapshots remain readable. If a version 1 snapshot lacks facts needed
for a particular current validation category, that category is explicitly
`unavailable`; mutable Working constraints are not substituted.

**Rationale**: This preserves FS-013 immutability while satisfying FS-014's
clarification that Published warnings reflect current planning data.

**Alternatives considered**:

- Showing only captured publication-time warnings was rejected by the
  clarification.
- Revalidating live Working rows was rejected because it mixes revisions.
- Rewriting Published snapshots with new warnings was rejected because
  Published content is immutable.

## Decision 5: Share pure validation evaluators across live and snapshot data

**Decision**: Extract the established conflict, capacity, holiday, and
exam-validity evaluation logic into small pure evaluators over typed validation
records. Adapt live ORM rows and Published snapshot records into those records.
Keep the owning rule definitions unchanged.

**Rationale**: The same concrete rules now have two required inputs: live
Working records and immutable Published snapshot records. A shared evaluator
prevents rule drift while keeping persistence and HTTP concerns out of rule
logic.

**Alternatives considered**:

- Duplicating Published-specific validation was rejected because it would
  create two sources of truth for existing rules.
- A generic validation engine or plug-in framework was rejected as speculative.

## Decision 6: Use canonical finding identities and contributor sets

**Decision**: The backend owns finding definitions, stable typed references,
deduplication, and full-revision summary values. Teaching and exam occurrence
references use `teaching:{id}` and `exam:{id}`.

- Conflict identity is conflict type plus a sorted unordered pair of occurrence
  references.
- Capacity identity is the affected occurrence reference.
- Remaining-work contributors carry total, scheduled, and remaining units;
  minutes are `remaining_units * 45`.
- Failure contributors are retained outcome identifiers.
- Needs-review contributors are distinct course references with all qualifying
  reason references.

Availability (`available`, `partial`, `unavailable`, `not_applicable`) is
separate from numeric value. Planning-outcome coverage is measured across the
included eligible courses: no eligible courses is not applicable, no covered
eligible course is unavailable, some covered eligible courses is partial, and
all covered eligible courses is available. A course is covered by at least one
reliable completed retained outcome in the selected revision; unattempted
operation kinds are not failures and do not separately reduce course coverage.
The other applicability universes are included courses for unscheduled work and
needs review, included scheduled occurrences for conflicts, and included
capacity-evaluable occurrences for capacity issues. No applicable records is
not applicable; complete evaluation with no contributors is available zero;
no verifiable source data is unavailable; and incomplete verifiable coverage is
partial with known incomplete values.

**Rationale**: Every metric must reconcile to affected records, repeated alert
messages must not inflate counts, and zero must not stand in for unavailable.

**Alternatives considered**:

- Counting rendered alert strings was rejected because the same finding can
  appear on multiple sessions.
- Client-side inference of conflicts from calendar cards was rejected because
  rule ownership would leak into presentation.

## Decision 7: Apply presentation filters client-side to one bounded response

**Decision**: The server returns canonical records, finding associations,
contributors, facets, and authoritative complete-revision summaries. The
client applies the documented filter intersection rules to those bounded
records and derives filtered summaries with pure tested functions over the same
canonical contributor sets. Filters, modes, visible dates, selections, and
drilldowns do not issue mutations.

**Rationale**: At the acceptance scale of 100 courses and 500 occurrences, a
single bounded response makes filters and calendar modes immediate while
preserving one revision context. Client code derives scope, not business-rule
findings.

**Alternatives considered**:

- A new request for each filter or mode was rejected because it increases
  latency and context-race risk without a scale need.
- A global state library was rejected; state belongs to the existing Schedule
  page and can use current React patterns.

## Decision 8: Adapt the existing Courses overview into the only List mode

**Decision**: `CourseSchedulePage` remains the orchestration owner. Introduce a
calendar-centered workspace component for Week, Day, Month, summaries, and
detail coordination, and adapt `DraftSchedulePanel`'s existing Courses overview
as its List branch. Preserve its filters, alerts, result summaries, session
review, edit/delete, and editor handoffs until parity tests pass. Then remove
only the separate legacy presentation boundary, not its behavior.

**Rationale**: This exactly implements the clarification and protects existing
work. A planner sees one Schedule workspace and one list representation.

**Alternatives considered**:

- Building a new list alongside the current overview was rejected as duplicate
  behavior.
- Deleting the existing implementation and rebuilding it was rejected because
  it adds risk without product value.
- Adding a Dashboard destination was rejected by scope and FS-018 navigation.

## Decision 9: Use native React, CSS Grid, and UTC-safe ISO date helpers

**Decision**: Implement Week, Day, and Month layouts with semantic React markup,
CSS Grid, and small pure ISO-date utilities using UTC-safe arithmetic. Do not
add a calendar, date, routing, animation, or state-management dependency.

**Rationale**: The required scale and interactions are bounded. Existing
dependencies are sufficient, while UTC-safe helpers avoid local-time daylight
saving transitions changing calendar dates.

**Alternatives considered**:

- A calendar library was rejected because drag/drop, resize, recurrence, and
  external synchronization are out of scope.
- A date library was rejected because only bounded date navigation and
  formatting are required.
- Virtualization was rejected at 500 occurrences; indexed and memoized
  derivations are sufficient.

## Decision 10: Preserve context atomically through loading and failure

**Decision**: Identify each workspace response with its semester, revision, and
workspace token. On a context switch, show the intended context as loading
without presenting previous records under its label. On refresh failure,
retain a complete prior response only as explicitly `last known`; mark failed
sections and never merge a partially completed new response into it. A
successful response replaces the prior response atomically.

**Rationale**: This directly enforces the no-mixed-revision and false-zero
requirements.

**Alternatives considered**:

- Incrementally replacing independent panel data was rejected because summary
  and record provenance would become unclear.
- Blanketing all partial errors as complete failure was rejected because the
  specification requires verified sections to remain usable.

## Decision 11: Use semantic responsive disclosure, not a blocking drawer

**Decision**: On wide screens, calendar, summaries, filters, and detail may
coexist. At 820 CSS pixels and below, and at 200% zoom, use normal document flow
with the calendar first and clearly labeled expandable/filter/detail regions.
Use native controls, `aria-pressed` mode buttons, programmatic date headings,
status announcements, focus transfer into detail/drilldown, and deterministic
focus return.

**Rationale**: Sequential regions keep all required controls reachable at 320
CSS pixels and avoid covering the FS-018 navigation.

**Alternatives considered**:

- A fixed full-height side drawer was rejected because it risks obscuring
  navigation and content at narrow widths.
- Pointer-dependent spatial interaction was rejected by accessibility and
  scope requirements.

## Decision 12: Migrate without fabricated history and verify deterministically

**Decision**: Migration `0008` creates the outcome table with no backfill.
Previously response-only outcomes are unrecoverable and therefore outcome
coverage is unavailable until a new applicable completed operation occurs.
Use deterministic fixtures containing 100 courses, 500 total teaching/exam
occurrences, 50 holidays, mixed findings, and mixed retained outcomes.

Automated unit, service, API, UI, regression, migration, and performance tests
are supplemented by real-browser keyboard/screen-reader/zoom/contrast checks,
visual comparison to the two supplied reference images, and moderated
acceptance with at least 10 representative reviewers. Human success criteria
must not be reported as passed without actual participants.

**Rationale**: Fabricating old outcome records would create false operational
history. Deterministic scale tests make the measurable timing criteria
repeatable without introducing telemetry infrastructure.

**Alternatives considered**:

- Backfilling inferred successes or failures was rejected because no reliable
  persisted source exists.
- Adding a browser E2E, accessibility scanner, or telemetry dependency solely
  for this slice was rejected; current Vitest/pytest coverage plus required
  manual acceptance is sufficient.

## Cross-slice compatibility

FS-014 deliberately supersedes two earlier implementation assumptions while
preserving their domain behavior:

- FS-010/FS-012 response-only operation results become latest retained
  per-course outcomes for FS-014 traceability.
- FS-013's immutable Published snapshot remains immutable, but FS-014 adds a
  separately labeled current-validation overlay calculated from Published
  occurrences only.

All correction, confirmation, stale-state, validation, optimization, exam, and
lifecycle ownership remains with FS-009 through FS-013. FS-018 remains the
single application navigation authority.
