# Research: Unified Teaching Schedule Generation

## Decision 1: Make the existing conflict-aware optimizer the only generator

**Decision**: Keep `conflict_aware_generation` and `semester_optimization` as the
single preparation/solve/save path for selections of one to twenty courses. A
one-course selection is not a special case.

**Rationale**: This path already evaluates selected courses together, protects
unselected teaching sessions, supports replacement confirmation, checks stale
snapshots, and saves proven results atomically. Extending it is smaller and safer
than introducing a third engine or teaching the legacy generators the same rules.

**Alternatives considered**:

- Route one-course requests through the legacy `generate_schedule` function:
  rejected because that function does not protect other schedules.
- Merge the independent batch service with the optimizer behind an abstraction:
  rejected because two implementations would still encode scheduling policy and
  could diverge.
- Create a new optimizer service and migrate both current implementations:
  rejected because the existing optimizer already provides the required base.

## Decision 2: Retire legacy scheduling operations with an explicit 410 contract

**Decision**: The former single-course generate operation and independent batch
prepare/generate operations remain routable only to return `410 Gone` with the
stable code `GENERATION_ENDPOINT_RETIRED` and the supported unified prepare and
generate paths. They perform no preparation and no mutation. The client removes
all calls and controls that use them.

**Rationale**: Immediate retirement satisfies the clarified requirement without
leaving hidden weaker behavior. A structured 410 response provides actionable
migration guidance to direct API callers.

**Alternatives considered**:

- Transparently forward old requests: rejected because their request shapes do
  not contain the unified preparation snapshot and confirmation semantics.
- Return a generic 404: rejected because it provides no migration guidance.
- Keep legacy operations temporarily: rejected by the clarified specification.

## Decision 3: Persist only the course-semester date override

**Decision**: Reuse `GenerationConstraintSet` as the persisted optional
course-semester planning-period override. Change reads and generation so weekly
windows always come from the course's current active `StudyTypeTimeWindow` rows.
Existing `GenerationConstraintWindow` copies are ignored; a save or reset clears
obsolete copies. No new database table or schema migration is required.

**Rationale**: The existing record already has the required unique course and
semester identity, planning dates, and revision. Ignoring copied windows restores
the study type as the sole source of truth while minimizing persistence change.

**Alternatives considered**:

- Add a new planning-period table and migrate data: rejected because it duplicates
  an existing entity without adding behavior.
- Continue copying study-type windows into each course constraint: rejected
  because copies become stale and violate the clarified ownership rule.
- Store windows in the client only: rejected because generation and validation
  require an authoritative server-side mapping.

## Decision 4: Save date overrides before and independently of generation

**Decision**: Add an explicit authenticated/lifecycle-checked update operation on
the existing course generation-constraints resource. It validates the active
working revision, semester membership, date ordering, semester boundaries, and
the expected constraint revision. A successful save commits immediately and the
returned draft/calendar state is refreshed from current validation. The optimizer
only reads the active saved state; it never saves, updates, deletes, or rolls back
constraints.

**Rationale**: The user creates a new constraint because it should govern both the
current schedule and all later generation attempts. Separating save from generate
makes failure behavior unambiguous: a solver failure preserves both the prior
draft and the deliberately saved constraint.

**Alternatives considered**:

- Save constraints in the generation transaction: rejected because a failed solve
  would incorrectly discard current planning intent.
- Pass unsaved overrides to preparation: rejected because the same course would
  have different active rules depending on entry point.
- Automatically move invalid existing sessions on save: rejected because save is
  a constraint mutation, not authorization to replace a schedule.

## Decision 5: Treat active exams as immutable protected occupancy and deadlines

**Decision**: During preparation, load every exam in the selected semester whose
date is greater than or equal to `institution_today()` from the exam-scheduling
service. Add each as fixed lecturer, room, and cohort occupancy. For a selected
course, its active exam start is also an inclusive latest teaching-end boundary:
`teaching_end <= exam_start`. Past exams are excluded from occupancy, deadlines,
and freshness tokens. Exam occupancy retains the blocked resource category
(`LECTURER_OCCUPIED`, `ROOM_OCCUPIED`, or `COHORT_OCCUPIED`) and carries
`source_kind=active_exam` plus the exam identifier. `ACTIVE_EXAM_BOUNDARY` is
used only for the same-course teaching deadline.

**Rationale**: This uses the application's existing institution-local definition
of active/past and prevents the teaching generator from invalidating a saved exam.
The half-open overlap rule permits exact adjacency while rejecting positive
duration overlap.

**Alternatives considered**:

- Protect all exams: rejected by clarification because past exams must not affect
  current generation.
- Protect only exams belonging to selected courses: rejected because exams for
  any course can occupy shared resources or cohorts.
- Move exams to accommodate teaching: rejected as outside feature scope.

## Decision 6: Extend the prepared snapshot rather than adding locks

**Decision**: Include active exam occupancy, course planning-period revision or
inherited semester dates, course study type, mapped active window rows, protected
teaching state, resources, holidays, unavailable dates, semester, and active
working revision in the existing preparation tokens. Recompute and compare tokens
before solve/save. Past-exam-only changes do not affect the token.

**Rationale**: Optimistic freshness is already the established workflow. Extending
its evidence avoids database locks during an operation that may take up to sixty
seconds and ensures stale prepared input never saves.

**Alternatives considered**:

- Lock every relevant row through optimization: rejected due to contention and
  long transaction duration.
- Validate only after solving: rejected because it wastes work and risks unclear
  replacement confirmation when inputs changed.

## Decision 7: Use one Calendar generation surface with a focused course editor

**Decision**: Replace the single/batch mode split with one selection-based panel.
It supports one to twenty courses, shows the selection count, prepares every
selection through the same API, and displays per-course outcomes. The focused
course exposes an explicit save/reset editor for start/end dates and read-only
study-type windows. Unsaved date edits are never sent to preparation; generation
is disabled while the focused edit is dirty or saving.

**Rationale**: A single surface makes the actual engine visible and prevents the
old semantic split. Focusing one course keeps course-owned date overrides clear
without inventing a bulk override rule that the clarified spec does not require.

**Alternatives considered**:

- Keep single and multi tabs backed by one API: rejected because two visible
  workflows would preserve user confusion.
- Add per-course weekly-window editing: rejected because windows are owned by
  study type.
- Duplicate date editing in Academic Data: rejected because Calendar Planning is
  the sole editing surface.

## Decision 8: Give teaching rows a dedicated layout contract

**Decision**: Use a teaching-specific row class and a shared nine-column CSS grid
definition for the List header and teaching rows. Scope generic occurrence-list
styles to their component so they cannot override teaching rows. At narrow widths,
hide the wide header and render explicit field labels through row markup; warnings
stay inside the owning occurrence field.

**Rationale**: The observed misalignment is a CSS cascade collision, not a data
ordering problem. Component-scoped selectors and one ordered field contract fix
the defect without introducing a table library.

**Alternatives considered**:

- Tune individual column widths while retaining colliding selectors: rejected
  because the later five-column rule would continue to override the grid.
- Add a data-grid dependency: rejected as unnecessary complexity.

## Decision 9: Preserve conflict codes and map each to precise visible copy

**Decision**: Keep the existing `LECTURER_OVERLAP`, `ROOM_OVERLAP`, and
`COHORT_OVERLAP` validation codes. Render code-specific localized titles and
sentences naming the shared lecturer, room, or cohort, followed by related course,
date, and interval evidence. Dedupe by affected session, related session, and
conflict code—not by generic message text.

**Rationale**: The backend already distinguishes the conflict categories. The UI
currently collapses their meaning into generic copy, which creates the appearance
of duplicate warnings.

**Alternatives considered**:

- Merge all overlap types into one warning: rejected because planners need to
  know which resource must change.
- Suppress repeated related sessions regardless of conflict type: rejected because
  one pair may have multiple independently actionable conflicts.

## Decision 10: Preserve the established stack and operation envelope

**Decision**: Use the existing FastAPI, SQLAlchemy, Pydantic, OR-Tools, React,
TypeScript, Vite, Vitest, and pytest stack. Keep the one-to-twenty course and
sixty-second operation limits; add active exams to the existing reference workload
instead of adding a second solver phase.

**Rationale**: No new dependency or architectural layer is required. The current
optimizer and test infrastructure directly support the feature.
