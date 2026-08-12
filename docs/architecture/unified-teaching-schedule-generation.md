# Architecture Exploration: Unified Teaching Schedule Generation

## Status

Implemented by feature I-003

## Context

The planner currently exposes two user-visible ways to generate teaching schedules
with different safety guarantees. The single-course flow accepts unsaved custom
planning constraints and runs the legacy independent generator. The semester
optimization flow accepts one or more courses and runs the conflict-aware solver.
As a result, regenerating one course through the single-course flow can replace a
previously valid draft with sessions that overlap an unselected course. The saved
result is then annotated with non-blocking validation alerts even though another
generation path could have prevented the conflicts.

The Calendar List view has two additional presentation defects. Teaching rows
receive both `session-row` and `schedule-occurrence-row`; a later five-column CSS
rule overrides the intended nine-column teaching-table grid. Separate room,
lecturer, and cohort overlap alert codes are also rendered with one generic
overlap sentence, making distinct findings appear duplicated.

## Previous system

- `POST /api/courses/{course_id}/draft-schedule/generate` calls the independent
  `generate_schedule` service. It knows the selected course, submitted planning
  period and weekly windows, holidays, and eligible resources, but it does not
  receive fixed semester teaching or exam occupancy.
- `POST /api/draft-schedules/optimization/prepare` and
  `POST /api/draft-schedules/optimization/generate` call the OR-Tools semester
  optimizer. The workflow accepts one to twenty selected courses and treats
  unselected teaching schedules as fixed occupancy.
- The older independent batch endpoints remain available but are not the current
  primary Calendar batch workflow.
- The optimizer loads saved course-semester constraints. It does not currently
  accept unsaved constraint overrides from the single-course editor.
- Teaching optimization currently builds fixed occupancy from Draft Sessions
  only. Existing Exam Sessions are absent from its fixed occupancy even though
  exam generation treats teaching and exams as hard occupancy.
- Validation creates separate `LECTURER_OVERLAP`, `ROOM_OVERLAP`, and
  `COHORT_OVERLAP` findings. The list renderer deliberately renders each finding,
  but its shared fallback text removes the conflict type.
- The List header uses a nine-column `.session-row` grid. Teaching rows also
  match the later generic `.schedule-occurrence-row` five-column rule, while the
  header does not, so header and data use different grids.

## Goals

- Expose one teaching-schedule generation workflow for selections of one or more
  courses.
- Apply the same hard conflict rules regardless of selection size or where the
  generation action is initiated.
- Preserve course-specific start/end dates with explicit immediate save/reset.
  Weekly windows are read-only effective inputs owned by the course study type.
- Treat unselected teaching sessions and existing exams as immutable occupancy.
- Prevent regeneration of a course with an existing exam from silently making
  that exam precede the course's new final teaching session.
- Preserve replacement confirmation, stale-input protection, deterministic
  optimization, partial outcomes, lifecycle guards, and atomic persistence.
- Keep teaching table headers and data in the same columns at supported widths.
- Give lecturer, room, and cohort conflicts distinct, understandable warning
  titles and explanations.

## Constraints

- The Resource Planner Constitution requires specification-first and test-first
  delivery.
- FastAPI, React/Vite, SQLAlchemy, SQLite compatibility, and the existing pinned
  OR-Tools runtime remain the technology boundary.
- The active working revision remains the only mutable schedule state.
- Unselected drafts, manual edits, exams, constraints, and academic/resource
  records must not be moved or changed by generation.
- A failed, stale, timed-out, or unproven optimization must not save a candidate.
- Existing API consumers need an explicit migration path; compatibility routes
  must not retain an independent scheduling algorithm.
- No new solver, database, queue, or background processing system is justified.

## Decision drivers

1. Conflict safety and preservation of existing schedule state.
2. One consistent user mental model and one authoritative scheduling algorithm.
3. Preservation of custom per-course constraints.
4. Testability and stale-state reliability.
5. Simplicity and incremental migration.
6. Performance within the existing one-to-twenty-course optimizer envelope.

## Assumptions

- "One generator" means one authoritative teaching optimization service and one
  user-visible generation workflow. Transitional HTTP routes may remain only as
  adapters to that service until callers migrate.
- Existing exams are not automatically moved or deleted by teaching generation.
- For an existing exam belonging to a selected course, a teaching candidate that
  ends after the exam begins would invalidate the exam's final-teaching rule and
  therefore must not be saved automatically.
- Distinct conflict dimensions should remain distinct findings; the UI should
  explain them instead of deduplicating away useful information.

## Options considered

### Option 1: Add conflict checks to the legacy single-course generator

#### Description

Pass existing teaching and exam occupancy into `generate_schedule`, exclude
conflicting slots, and keep the current optimizer for multi-course selections.

#### Benefits

- Smallest immediate backend change.
- Keeps the current single-course request and constraint-saving behavior.

#### Disadvantages

- Leaves two scheduling algorithms and two comparison behaviors.
- Duplicates conflict, resource, holiday, stale-input, and persistence rules.
- A selection of one course could still produce a different answer depending on
  which endpoint or UI control invoked it.
- Does not satisfy the requested single-generator model.

#### Risks

- The paths will drift again as exam and scheduling rules evolve.
- Fixing one path may not fix compatibility or batch callers.

### Option 2: Route the current single-course UI through the optimizer only

#### Description

Keep the existing UI modes and APIs, but make the single-course action prepare
and execute a one-course optimization. Add a way to persist or pass its edited
constraints before optimization.

#### Benefits

- Reuses the proven conflict-aware solver.
- Removes the reported conflict behavior from the current Calendar UI.
- Smaller client migration than a fully unified workflow.

#### Disadvantages

- The product continues to present different generation modes.
- Legacy single and independent batch APIs remain alternate behavior unless
  separately removed or delegated.
- Saving constraints before a failed generation would change the established
  rule that failed generation preserves the previously saved constraints.

#### Risks

- A partial migration can leave hidden or future callers on unsafe behavior.
- A separate constraint-save operation can create a new stale-state boundary.

### Option 3: Introduce one unified preparation/generation contract backed by the optimizer

#### Description

Create one authoritative teaching-generation application service and contract
for one to twenty selected courses. Preparation accepts the selection and
unavailable dates. It fingerprints the currently active saved date overrides,
live study-type windows, current schedules, resources, holidays, active exams,
semester, and lifecycle state. Generation echoes that prepared input, requires
replacement confirmation where applicable, and invokes the existing semester
optimizer for every selection size.

Unselected Draft Sessions and active Exam Sessions are fixed occupancy. Past
exams are excluded from occupancy and freshness evidence. An active exam for a
selected course also supplies a latest permissible
teaching boundary so that a generated teaching schedule cannot make the exam
occur before the course's final teaching session. A successful result saves the
selected drafts atomically. Constraint mutation is deliberately outside the
optimizer transaction: date edits activate immediately through optimistic
PUT/DELETE operations and remain active when preparation is cancelled or a
solve fails, times out, is unproven, or becomes stale.

The React workspace exposes one selection surface and one generation action.
Selecting one course exposes its editable constraint inputs; selecting multiple
courses uses each course's saved constraints and can provide deliberate access
to per-course inputs without changing algorithms. Existing routes are either
removed after migration or temporarily delegate to the unified application
service; they do not retain independent generation logic.

#### Benefits

- One algorithm, rule set, snapshot boundary, and user mental model.
- One-course and multi-course requests have identical conflict guarantees.
- Course date overrides activate immediately and are never rolled back by generation.
- Teaching generation respects both teaching and exam occupancy.
- Existing optimization, confirmation, deterministic ordering, and stale-state
  protections are reused rather than reimplemented.
- Compatibility can be migrated incrementally without retaining unsafe logic.

#### Disadvantages

- Requires a cross-stack contract change and a client workflow consolidation.
- Snapshot material and exact-result validation must include exams and submitted
  constraint overrides.
- Tests that intentionally assert independent single-course overlap behavior
  must be replaced with conflict-avoidance acceptance tests.

#### Risks

- Large custom constraint domains may increase solver candidates; existing
  workload limits and deadline behavior must remain enforced.
- A compatibility adapter that cannot faithfully express preparation and
  confirmation semantics must fail explicitly rather than silently generate.
- Exam temporal-boundary behavior must be specified precisely for active and
  past exams.

## Comparison

| Driver | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| One authoritative generator | Poor | Partial | Strong |
| Conflict safety | Partial | Strong for current UI | Strong across callers |
| Custom constraint integrity | Strong | Moderate | Strong |
| Exam-aware teaching safety | Requires duplicate work | Can be added | Built into one occupancy model |
| Migration effort | Low | Medium | Medium-high |
| Long-term maintainability | Poor | Moderate | Strong |
| Constitution/KISS fit | Poor because rules remain duplicated | Moderate | Strong despite the contract migration |

## Recommendation

Choose Option 3. Extend the existing conflict-aware semester optimizer rather
than creating a new scheduling engine. The unified application service should
be the only production path that decides teaching placements. One selected
course is simply the smallest valid optimization selection, not a separate mode.

The focused-course editor saves only course-semester start/end dates. Semester
dates are inherited by default. Active weekly windows are always resolved from
the course's current study type and cannot be copied or edited on the course.
The shared snapshot includes date-override revisions, study-type/window
revisions, current protected occupancy, and active exams. Changing any material
input invalidates preparation without moving existing sessions.

The legacy single-course generate route and both independent batch routes return
HTTP 410 with `GENERATION_ENDPOINT_RETIRED` and the unified prepare/generate
paths. They perform no scheduling or persistence work.

For the List view, give teaching table rows a dedicated grid class or CSS custom
property shared by the header and its rows. Scope the generic occurrence-list
selector beneath `.schedule-occurrence-list` so it cannot override table rows.
At narrow widths, use an explicit stacked-row presentation with field labels
rather than relying on implicit grid wrapping.

For warnings, preserve separate backend findings and render code-specific titles:

- `LECTURER_OVERLAP` -> `Lehrendenkonflikt`
- `ROOM_OVERLAP` -> `Raumkonflikt`
- `COHORT_OVERLAP` -> `Kohortenkonflikt`

Each warning should identify the affected resource type and list the related
course, date, and interval. If the same related session causes several conflict
types, the cards remain distinct and visibly named; optional visual grouping may
place them under one affected-session section without merging their meanings.

## Consequences

- The legacy `generate_schedule` placement decision is retired from HTTP
  generation flows. It may remain temporarily only for isolated unit tests or be
  removed after all callers migrate.
- The independent batch routes are deprecated or adapted to the unified service;
  the current UI no longer exposes an independent batch generator.
- The unified contract and client types replace the current split between
  `draftSchedule`, `multiCourseDraftGeneration`, and
  `conflictAwareGeneration` generation calls.
- Existing saved data requires no schema migration.
- Backend tests must invert the current expectation that single-course generation
  may save overlaps.
- Exam-aware fixed occupancy and same-course exam boundaries become part of
  teaching generation snapshot and exact-result validation.
- CSS selectors become component-scoped, preventing unrelated occurrence-row
  styles from changing List-table column contracts.

## Validation required

- One selected course with overlapping unselected Mathematics sessions produces
  no new lecturer, room, or cohort conflict.
- The same selection and unchanged inputs produce the same result through every
  supported entry point.
- Submitted custom constraints are saved only with a successful schedule result
  and remain unchanged on failure, timeout, stale input, or cancellation.
- Existing teaching sessions and exams remain unchanged and block overlapping
  lecturer, room, and cohort candidates.
- A selected course with an existing exam cannot receive a teaching session that
  ends after the exam begins; infeasibility produces a precise course outcome.
- Replacement confirmation and active-working-revision guards still apply.
- A stale exam, teaching, constraint, holiday, resource, or lifecycle change
  prevents an invalid prepared result from saving.
- List headers and all row values align at wide widths, 200% zoom, and supported
  narrow widths.
- Room, cohort, and lecturer overlaps render different titles and explanations,
  including when two or three apply to the same pair of sessions.
- Focused backend, frontend, contract, build, lint, and performance suites pass.

## Open questions

- Whether past exams should impose the same latest-teaching boundary as active
  exams, or only fixed resource/cohort occupancy. The specification should choose
  explicitly; the recommended safe default is to preserve the temporal validity
  of every saved exam.
- Whether transitional legacy HTTP routes are required by any external consumer.
  Repository inspection shows current first-party client callers can migrate,
  but external deployment consumers are not discoverable from the codebase.
- Whether multi-course constraint editing needs to expose every selected course
  inline in the first delivery slice or may initially use already-saved
  per-course constraints while one-course editing remains directly visible.

## Handoff to specification

Create a new feature specification rather than modifying FS-010 in place because
FS-010 explicitly preserved the independent workflows and excluded exams. The
new specification should supersede those boundaries for teaching generation and
amend the applicable FS-012 and FS-019 integration behavior. It should define:

- the one-to-twenty-course unified preparation/generation workflow;
- optional transactional per-course constraint overrides;
- teaching and exam fixed occupancy and same-course exam boundaries;
- replacement, stale, failure, partial-result, and lifecycle behavior;
- migration/deprecation behavior for legacy routes;
- the single user-visible generator and selection/constraint interaction;
- the List table's responsive column contract; and
- code-specific warning wording and related-session detail.
