# Research: Multi-Course Draft Generation

## Decision: Reuse Independent Single-Course Generation

The existing `generate_schedule()` domain function will be called once for each selected course. It will receive that course's own plan, selected semester, and active course-semester constraints. The placement algorithm will not receive schedules from other courses.

**Rationale**: The function is already deterministic, side-effect free, and covered by unit tests. Reuse satisfies the Slice 6 goal while ensuring cross-course conflict avoidance remains Slice 7.

**Alternatives considered**:

- Extend the placement algorithm with existing semester occupancy. Rejected because that is conflict-aware multi-course scheduling.
- Build one combined semester solver. Rejected as optimization scope and unnecessary complexity.
- Invoke the existing single-course HTTP endpoint repeatedly from the browser. Rejected because it cannot provide operation-wide rollback, canonical confirmation, or one coherent result.

## Decision: Add Preparation And Execution Contracts

Use a read-only preparation operation followed by execution. Preparation validates semester, operation kind, count, and duplicate selection; returns one canonical course snapshot per requested ID; and identifies selected same-semester schedules requiring replacement. The client stores the returned immutable snapshot while showing confirmation. Execution submits that snapshot plus explicit confirmation.

**Rationale**: Confirmation must be based on backend state, not only the cached semester overview. Returning draft IDs and revisions without persisting a preparation record keeps cancellation write-free and lets execution detect schedules changed or created after confirmation.

**Alternatives considered**:

- Use only cached frontend schedule data. Rejected because it cannot safely detect replacement changes between overview load and confirmation.
- Persist a Batch Operation or opaque server-side preparation token. Rejected because batch history is explicitly transient and a durable operation model adds lifecycle and cleanup work.
- Use one execution endpoint with no preparation. Rejected because the backend would discover replacement targets only after the user was expected to confirm them.

## Decision: Make Draft Schedule Identity Course-Semester Scoped

Replace global `course_id` uniqueness with a composite unique constraint on `(course_id, semester_id)`. All repository reads and replacements will require both identifiers. The single-course read contract will require `semesterId`.

**Rationale**: The specification requires schedules for the same course to coexist across semesters. The current globally unique `course_id` deletes another semester's schedule during regeneration.

**Alternatives considered**:

- Keep one Draft Schedule per course and archive semester history elsewhere. Rejected because it adds a second storage model and contradicts direct course-semester retention.
- Return the most recent schedule when semester is omitted. Rejected because it is ambiguous and unsafe once multiple schedules exist.
- Add semester-specific Course copies. Rejected because course-semester eligibility administration is out of scope.

## Decision: Add Optimistic Revisions

Add integer `revision` fields to Draft Schedule and Generation Constraint Set. Draft revision starts at 1 and increments whenever its sessions are manually edited or regenerated. Constraint revision starts at 1 and increments whenever a saved constraint set changes. Preparation exposes Draft Schedule revision; execution snapshots active constraints at operation start. Conditional writes compare the expected IDs/revisions before replacing data.

**Rationale**: Revision integers are deterministic concurrency tokens and directly support the clarified stale-data rules. They are safer than timestamp precision and work where SQLite row locking is limited.

**Alternatives considered**:

- Use `created_at`/`updated_at` timestamps only. Rejected because Draft Schedule has no update timestamp and timestamp precision can make equality fragile.
- Depend on `SELECT ... FOR UPDATE`. Rejected because SQLite does not provide effective row-level locking.
- Ignore concurrent changes during the foreground operation. Rejected because the spec requires newer drafts and constraints to be preserved.

## Decision: Use Conditional Upserts With Nested Savepoints

Generate and validate course candidates before persistence. Persist expected successful candidates inside one outer transaction, with a nested savepoint for each course. A known generation or stale precondition failure rolls back only that course's savepoint and becomes a failed outcome. Any unexpected infrastructure or persistence exception escapes the orchestration service and rolls back the entire outer transaction.

**Rationale**: This provides expected partial success and unexpected atomic rollback at the same time. Conditional updates also close the race between a preliminary comparison and the actual write.

**Alternatives considered**:

- Commit after every successful course. Rejected because an unexpected later failure would leave an operation-wide partial state contrary to clarification.
- Roll back all courses for any expected generation failure. Rejected because partial success is a core requirement.
- Persist results while generating each course. Rejected because it complicates rollback and lets late failures affect earlier writes.

## Decision: Move Transaction Ownership Out Of Repository Functions

Repository mutation functions will flush but not commit. Single-course API handlers and the new orchestration service will explicitly commit or roll back their unit of work. Existing single-course generation will save its Draft Schedule and constraints in one transaction rather than the current two commits.

**Rationale**: Repository-level commits prevent an outer batch transaction from guaranteeing rollback. Boundary-owned transactions are also easier to test with injected failures.

**Alternatives considered**:

- Add `commit=True/False` flags to repository methods. Rejected because optional transaction behavior is easy to misuse and obscures ownership.
- Duplicate batch-only repository functions. Rejected because schedule replacement and constraint persistence rules would diverge.

## Decision: Preserve Unchanged Saved Constraints And Persist Defaults On First Success

For a course with saved active constraints, batch generation reads and uses them without rewriting unchanged rows. For a course using defaults because no saved set exists, successful generation persists the normalized active defaults, matching established single-course behavior. Constraint changes during execution are detected before persistence and produce a stale outcome.

**Rationale**: Unchanged saved constraints are already durable and should not gain a false revision solely because a schedule was regenerated. Persisting defaults on first success preserves the exact rule set that generated the saved draft.

**Alternatives considered**:

- Rewrite every saved constraint set after every batch success. Rejected because it creates artificial revisions and larger concurrency windows.
- Never persist defaults. Rejected because it would diverge from single-course generation and allow later default changes to alter the active rule associated with an existing draft.

## Decision: Return Compact Outcomes And Refresh The Overview Separately

Execution returns aggregate counts and exactly one success or failure outcome per requested course. It does not embed all Draft Schedules or validation alerts. After every normal 200 response, including all-expected-failure results, the client reloads the selected semester overview once.

**Rationale**: The existing overview endpoint already computes validation alerts across the complete semester. A separate refresh avoids duplicating large schedule data in the batch response and ensures alerts include pre-existing courses.

**Alternatives considered**:

- Return the entire refreshed semester from the execution response. Rejected because it duplicates the overview contract and response mapping.
- Return only aggregate counts. Rejected because failures must be course-specific and retryable.
- Compute alerts in the client. Rejected because Slice 5 already owns authoritative backend validation.

## Decision: Keep Batch Results In React State Only

The result summary and failed-course set live in page-level React state. No database table, local storage, or session storage is added. A reload or remount clears the result while saved schedules and constraints remain.

**Rationale**: This directly implements the clarification and avoids accidental batch-history or dashboard scope.

**Alternatives considered**:

- Persist the latest result per semester. Rejected because the user explicitly selected current-session retention.
- Persist full operation history. Rejected as dashboard/audit workflow scope.

## Decision: Add A Separate Several-Courses UI Mode

Keep the current one-course selector, summary, constraint editor, and Generate action intact. Add a separate several-courses mode with a scrollable checkbox list, selected count, 2-50 validation, clear selection, course-specific constraint explanation, confirmation dialog, transient result summary, and failed-only retry. Place the potentially large result summary above the semester overview rather than in the narrow input column.

**Rationale**: Separate modes prevent batch selection from mutating the focused single-course editor and make it explicit that unsaved local constraint edits are not batch inputs.

**Alternatives considered**:

- Replace the current course selector with one multi-select control. Rejected because it would entangle single-course editing with batch inputs.
- Use a native multi-select. Rejected because checkbox selection is more discoverable and does not depend on modifier keys.
- Add a new application page. Rejected because the existing semester overview and planning context already provide the necessary workflow.

## Decision: Reset Overview Interaction State After Batch Refresh

After a completed batch response and successful overview reload, clear active overview filters and any open session edit state so newly generated schedules and alerts are immediately visible. Keep the previous overview mounted and marked busy while refreshing. If refresh fails, preserve the result and last known overview and offer a refresh retry.

**Rationale**: Existing filters can otherwise hide newly generated schedules, making a successful operation look incomplete. Preserving old data during refresh prevents a blank or misleading intermediate state.

**Alternatives considered**:

- Preserve filters unconditionally. Rejected because the completion scenario requires the complete refreshed semester to be reviewable immediately.
- Unmount the overview during every request. Rejected because it loses useful context and creates avoidable empty states.

## Decision: Scope Async State By Operation

Replace the page's shared loading flag and shared error list with state dedicated to option loading, constraint loading, overview refresh, single-course generation, batch preparation, and batch execution. Disable only actions that conflict with the active write. Keep the last completed batch result until another normal batch result or page remount, and show an operation-wide error separately.

**Rationale**: The current effects run concurrently, so one request can clear another request's loading or error state. Batch preparation, confirmation, execution, and overview refresh make that race more visible and can otherwise show false status text or erase actionable failures.

**Alternatives considered**:

- Keep one shared `isLoading` and `errors` pair. Rejected because unrelated reads and writes overwrite each other's state.
- Add a global state-management library. Rejected because page-local scoped state is sufficient and no cross-page persistence is required.
- Block the entire page for every read. Rejected because the current overview should remain reviewable during unrelated loading.

## Decision: Add No New Dependency Or Background Infrastructure

Use existing FastAPI, SQLAlchemy, Alembic, React, and Vitest facilities. Generation remains synchronous and bounded to 50 courses.

**Rationale**: The 10-second foreground target and current scale do not justify a queue, worker, progress stream, state library, or new UI/test package.

**Alternatives considered**:

- Background jobs with polling. Rejected by scope and current scale.
- WebSocket progress updates. Rejected because they add infrastructure without a specified user need.
- New frontend form or state libraries. Rejected because page-local state and small focused components are sufficient.
