# Phase 0 Research: Academic Planning Data Administration

## Decision 1: Use a focused academic catalog boundary

**Decision**: Add a dedicated FastAPI academic catalog router, schemas, and service while retaining the existing model module and transaction convention.

**Rationale**: CRUD, lifecycle, usage, and deletion rules are cohesive and substantially different from schedule generation. A focused service prevents `draft_schedule_repository.py` from becoming a generic data-access layer while keeping the current small-project structure.

**Alternatives considered**: Add CRUD directly to planning-options or draft-schedule modules (rejected because reads, revisioned writes, and deletion blockers would become coupled); introduce a generic repository framework (rejected as unnecessary abstraction).

## Decision 2: Persist normalized names and enforce uniqueness across active and inactive records

**Decision**: Trim display names, derive a Unicode case-folded canonical normalized value, and enforce one database unique constraint per named record category for every new or repaired row. A supported legacy collision temporarily has a null canonical unique value, a deterministic collision-safe internal key, and `name_repair_required = true`; inactive records retain their name reservation.

**Rationale**: This implements the accepted clarification consistently on SQLite and a future PostgreSQL deployment, closes concurrent duplicate-create races for steady-state data, and allows legacy conflicts to remain usable until the planner repairs them.

**Alternatives considered**: Application-only duplicate checks (race-prone); database-specific lower/trim expression indexes (less portable); allowing inactive-name reuse (contradicts the clarification).

## Decision 3: Use explicit lifecycle state and integer revisions

**Decision**: Every administrable academic record receives `is_active` and an integer `revision`. Edit, archive, reactivate, and delete require the expected revision and increment it on successful mutation.

**Rationale**: The spec requires reversible inactivity, non-cascading status, and stale-write protection. Integer revisions match the existing Draft Schedule approach and are deterministic across SQLite timestamp precision.

**Alternatives considered**: Timestamp comparison (precision and clock ambiguity); automatic retry/last-write-wins (silently overwrites newer work); event sourcing (far beyond slice needs).

## Decision 4: Calculate usage explicitly and restrict deletion

**Decision**: A usage query reports dependent academic records separately from saved schedule references. Delete rechecks these blockers in the same transaction and succeeds only with no blockers.

**Rationale**: The planner needs actionable reasons, and SQLite foreign-key behavior cannot replace domain feedback. This also removes reliance on the current Study Type delete-orphan cascade.

**Alternatives considered**: Database error translation only (incomplete and not actionable); cascading delete/archive (forbidden); soft-delete only (spec permits permanent deletion of unused records).

## Decision 5: Model one current semester directly on Course

**Decision**: Course has one `current_semester_id`; reassignment replaces that value atomically. Draft Schedules retain their own historical `semester_id`.

**Rationale**: This is the simplest representation of clarification option C and keeps saved schedules from earlier assignments intact without a many-to-many eligibility model.

**Alternatives considered**: Course-semester join table (unnecessary for exactly one current relationship); infer from the selected planner screen (not durable); allow every course in every semester (rejected clarification).

## Decision 6: Preserve legacy data through an explicit repair state

**Decision**: Migration infers a current semester from the newest Draft Schedule, then newest Generation Constraint Set, then the sole Semester when only one exists. If none is authoritative, the legacy Course remains visible with `current_semester_id = null`, cannot be used for new generation, and is assignable by the planner through administration. New and successfully updated courses cannot remain unassigned.

**Rationale**: Existing databases contain no authoritative current assignment and may contain the same Course in several Semester drafts. An explicit planner repair avoids silently inventing business data, does not block application startup, and preserves every saved schedule.

**Alternatives considered**: Assign an arbitrary first/latest Semester (silent business-data corruption); halt startup (requires developer intervention); keep every legacy pairing eligible (contradicts the clarified steady state).

## Decision 7: Snapshot academic facts on Draft Schedule

**Decision**: Store immutable course, cohort, study-type, and semester facts on each Draft Schedule when generated/replaced. Backfill legacy schedules from current source rows once. Response mapping and academic validation use snapshots; source foreign keys remain for traceability and deletion protection.

**Rationale**: Current responses and room-capacity/study-type validations traverse mutable source records. Snapshotting only labels would still let cohort-size or relationship edits silently change historical behavior.

**Alternatives considered**: Continue live joins (violates FR-024); snapshot names only (incomplete); event/history tables (unnecessary); separate one-to-one snapshot entity (adds joins without lifecycle benefit for this aggregate).

## Decision 8: Keep existing Lecturer and Room assignment compatibility without administering resources

**Decision**: Course create/edit continues to select one existing Lecturer and Room from read-only planning resource options because FS-001 through FS-006 require them. FS-007 does not create, edit, archive, schedule availability, or add multiple eligibility for these resources.

**Rationale**: A newly created Course must remain usable by the existing generator, but resource administration belongs to FS-008. This preserves the current single-resource model without expanding the slice.

**Alternatives considered**: Invent placeholder resources (invalid authoritative data); make required foreign keys silently nullable (breaks generator assumptions); add Lecturer/Room CRUD (scope expansion).

## Decision 9: Provide resource-specific REST contracts with uniform domain errors

**Decision**: Use resource collections/items, explicit archive/reactivate commands, a usage endpoint, paginated lists, canonical mutation responses, and `{errors:[{code,message,field?,meta?}]}` failures. Use 422 for validation and 409 for stale revision, normalized conflict, reactivation conflict, and protected deletion.

**Rationale**: The client needs field feedback, blocker categories, and reliable action outcomes. Explicit lifecycle commands are easier to test and explain than overloaded status patches.

**Alternatives considered**: One polymorphic catalog endpoint (weak typing and complex validation); generic PATCH for lifecycle (less clear action feedback); unstructured FastAPI detail strings (harder client behavior).

## Decision 10: Refresh through canonical refetch, not real-time infrastructure

**Decision**: Successful admin mutation returns the canonical record, then the client refetches affected catalog data and planning options. Returning to Schedule also refreshes options. The server independently enforces availability.

**Rationale**: This meets the 2-second criterion at the specified scale and prevents stale selectors without adding polling, push delivery, or a cache library.

**Alternatives considered**: WebSockets/polling (unneeded); optimistic cache mutation (risky with blockers and relationship-derived availability); page restart (fails success criteria).

## Decision 11: Add a single reusable administration workspace

**Decision**: Add a lightweight Schedule/Academic Data view switch. Academic Data uses tabs for four named categories, a reusable list/editor layout, and nested Time Windows under Study Type.

**Rationale**: The project has no router and only two top-level workflows. Reusable controlled forms fit existing React patterns, preserve correction context, and follow the reference image gradually without building the deferred calendar workspace.

**Alternatives considered**: React Router (new dependency for two views); separate page per type (duplicate CRUD behavior); modal forms for every edit (poor correction context); calendar-oriented administration (scope expansion).

## Decision 12: Treat accessibility and failure recovery as acceptance-level UI behavior

**Decision**: Use semantic tabs/forms/tables, labelled controls, keyboard-operable actions, focus-managed confirmation dialogs, live validation/success announcements, responsive stacking, last-known-data retention, and Retry on refresh failure.

**Rationale**: These decisions make the administration workflows testable and usable without choosing a new UI framework. They close the accessibility/operational details deferred by clarification.

**Alternatives considered**: Mouse-only custom controls (not acceptable); clearing content on request failure (risks silent selection loss); adopting a component framework (not justified).

## Decision 13: Migrate sequentially and fail safely on unrecoverable conflicts

**Decision**: Add migration `0003`, extend startup detection for 0001→0002→0003, backfill activity/revision/normalized keys/snapshots, enable SQLite foreign-key enforcement, and convert supported legacy normalized-name duplicates into visible repair states without stopping startup. Stop with actionable diagnostics only for an unknown partial schema that cannot be upgraded safely.

**Rationale**: `create_all` does not alter existing tables, and the current startup migrator recognizes only FS-006 states. A repair state preserves authoritative display values and existing use without silently renaming, merging, or requiring developer intervention.

**Alternatives considered**: Recreate the database (destroys existing data); depend on `create_all` (does not migrate); silently merge duplicates (unsafe); stop startup for a supported data conflict (breaks existing usability and requires developer intervention).
