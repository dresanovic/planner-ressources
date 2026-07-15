# Phase 0 Research: FS-009 Manual Session Management

## Decision: Reuse the Existing Draft Persistence Model

**Decision**: Store manual sessions in the existing `DraftSession` table and use the existing `DraftSchedule` course-semester parent. When manual creation starts from an empty course-semester, create the parent with the same current source snapshots used by generation. Do not add a manual-session table, provenance column, or migration.

**Rationale**: Generated, edited, and manually created sessions have the same identity, fields, validation alerts, review behavior, and deletion semantics in this slice. The existing parent already enforces one schedule per course and semester and cascades session deletion.

**Alternatives considered**:

- Add a separate manual-session entity: rejected because it would duplicate review, validation, and persistence paths.
- Add a provenance flag: rejected because FS-009 does not filter, audit, preserve, or otherwise behave differently by origin.
- Retain an empty Draft Schedule: rejected by clarification; absence plus course progress is the canonical empty state.

## Decision: Derive Remaining Units

**Decision**: Calculate `scheduled_units` as the sum of current Draft Session units and `remaining_units` as `max(current Course.total_units - scheduled_units, 0)`. Return progress in mutation results and derive semester course indicators from current planning options plus the complete schedule set. Do not persist counters.

**Rationale**: Session units and the current course total are authoritative. Derived values cannot drift after create, edit, delete, regeneration, source-unit changes, or rollback.

**Alternatives considered**:

- Persist remaining units on Draft Schedule: rejected because every session and course-unit mutation would need counter synchronization.
- Use `course_total_units_snapshot`: rejected because the clarified spec says current course units determine remaining work.
- Permit negative remaining values: rejected; the spec requires a minimum of zero and manual creation blocks exceeding the current remainder.

## Decision: Use Draft Schedule Revision for Stale Deletion Protection

**Decision**: Confirmation captures the current `DraftSchedule.id` and `DraftSchedule.revision`. Both deletion requests submit them as `expectedDraftScheduleId` and `expectedDraftRevision`. The repository atomically claims the expected parent with a conditional revision update in the same transaction as deletion; a missing identity or zero-row revision claim returns `409 STALE_DRAFT`, changes nothing after rollback, and causes the client to refresh and require a new confirmation.

**Rationale**: Every existing edit and replacement already increments the parent revision. Manual creation and surviving single deletion will do the same, so the aggregate token detects changes to the target session or any sibling session without a new field. Including parent identity also prevents an old confirmation from matching a newly recreated draft whose revision restarted at 1.

**Alternatives considered**:

- Compare only session fields: rejected because complete-draft confirmation must detect any changed session and single deletion also becomes stale when its displayed parent scope changes.
- Add per-session revisions: rejected because the parent revision already represents the confirmed aggregate and avoids a migration.
- Lock the draft while a dialog is open: rejected because UI-lived locks add failure and cleanup complexity.
- Delete only the original confirmation snapshot: rejected by clarification because the planner must reconfirm current scope.

## Decision: Keep Mutations Atomic and Constraints Separate

**Decision**: Validate against the latest database state and perform each create/delete plus revision change in one transaction. Roll back the full action on validation, stale state, missing data, or persistence failure. Never query for deletion or mutate `GenerationConstraintSet`, source Course, Semester, Lecturer, Room, Cohort, or Study Type records.

**Rationale**: Atomic repository functions preserve the existing no-partial-write behavior and make source/constraint preservation structural rather than dependent on UI behavior.

**Alternatives considered**:

- Multiple commits followed by alert refresh: rejected because failure could leave partial schedule changes.
- Recreate a draft after complete deletion solely to retain constraints: rejected because constraints already have an independent course-semester identity.
- Bulk-delete the parent row directly: rejected because the current foreign keys do not declare database-level delete cascade; delete the ORM parent so the existing relationship cascade removes sessions safely.

## Decision: Add a Consistent Mutation Result Contract

**Decision**: Return a `DraftScheduleMutationResponse` from all three operations with `courseId`, `semesterId`, `scheduledUnits`, `remainingUnits`, and nullable `draftSchedule`. A deleted-last or cleared draft returns `draftSchedule: null`. Use structured error arrays for validation and a distinct `409 STALE_DRAFT` response with the current revision when available.

**Rationale**: One shape lets the UI update the affected course immediately across create and both deletion outcomes, including the no-parent state. It also keeps stale conflicts distinguishable from invalid input and missing targets.

**Alternatives considered**:

- Return `204` for deletion: rejected because it provides no authoritative remaining-unit result.
- Return only Draft Schedule: rejected because no Draft Schedule exists after last-session or complete deletion.
- Return the entire semester overview from every mutation: rejected because the existing page already owns overview refresh and unrelated schedules would make mutation responses unnecessarily large.

## Decision: Reuse Existing Alert Derivation and Overview Refresh

**Decision**: Use the current `collect_validation_alerts` response mapping for a surviving affected draft, then have `CourseSchedulePage` reload the complete semester overview after success or stale rejection.

**Rationale**: Alerts are already derived from current semester sessions rather than persisted. Reloading the existing overview updates alerts on both the affected session and related sessions in other course drafts.

**Alternatives considered**:

- Persist alerts during mutation: rejected because it conflicts with the established derived-alert model.
- Patch only the changed schedule into client state: rejected because alerts on related surviving sessions could remain stale.

## Decision: Calculate a Default End Time but Persist the Planner Override

**Decision**: In the creation form, calculate end time as `start + units × 45 minutes + (units - 1) × 10 minutes` whenever start or units changes. Keep end time editable. Submit and persist the final start, end, and unit values; backend validation requires only a same-day positive time range and does not infer or alter units from elapsed duration.

**Rationale**: This implements the clarification exactly: the default follows established teaching/break conventions, while a shorter merged-unit session or longer paused session remains possible and units continue to drive progress.

**Alternatives considered**:

- Derive end time on the server and make it read-only: rejected because it prevents the confirmed override use cases.
- Derive units from duration: rejected because remaining units must follow the explicit unit count.
- Reject a duration mismatch: rejected because planned pauses and merged teaching intentionally create mismatches.

## Decision: Extend Existing Planner Components

**Decision**: Keep selected-course progress, manual-create controls, complete-draft clearing, orchestration, and semester refresh in `CourseSchedulePage`; extend `DraftSchedulePanel` only with per-session delete triggers beside existing Edit actions; add one small schedule-specific deletion dialog that reuses the accessible focus-management behavior established by `ProtectedDeleteDialog`. Extend planning-option Course data with current `cohortSize` so the first manual session can offer capacity-valid rooms before a Draft Schedule exists.

**Rationale**: The current page already owns planning options, selected course/semester, writes, and overview refresh. The panel already owns sessions, filters, edit actions, rooms, and alerts. Keeping progress limited to the selected course delivers FS-009 without pre-building FS-014's semester dashboard. `cohortSize` is the smallest additive context needed for client-side room filtering when no draft exists.

**Alternatives considered**:

- Build the future calendar workspace now: rejected as FS-014 scope.
- Build a semester-wide unscheduled-course list: rejected as broader operational-dashboard scope.
- Add drag/drop: rejected explicitly by FS-009.
- Reuse `ProtectedDeleteDialog` unchanged: rejected because it describes source-record blockers/archive behavior rather than returned units, course-semester scope, and stale reconfirmation.
