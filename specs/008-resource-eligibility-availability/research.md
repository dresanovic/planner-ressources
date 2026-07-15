# Phase 0 Research: FS-008 Resource Eligibility and Availability

## Existing architecture and dependency boundary

**Decision**: Implement FS-008 with the existing Python 3.12, FastAPI, Pydantic, SQLAlchemy/Alembic, SQLite, React, TypeScript, Vite, pytest, and Vitest stack. Add no runtime dependency.

**Rationale**: The repository already provides revisioned catalog mutations, normalized uniqueness, protected deletion, SQLAlchemy migrations, controlled React forms, accessible dialogs, and structured JSON errors. Weekly recurrence and half-open overlap need only existing date/time primitives.

**Alternatives considered**: A recurrence library adds capability outside the indefinite weekday pattern; a client state/form library and router add churn without solving a slice requirement; a background scheduler or external service is outside scope.

## Resource identity and lifecycle

**Decision**: Extend Lecturer and Room with `reference_code`, its normalized unique form, `is_active`, and `revision`; keep display names non-unique and Room capacity positive. Normalize reference codes with surrounding whitespace removed and case folded within each resource catalog.

**Rationale**: This mirrors FS-007 lifecycle and concurrency patterns while implementing the clarified duplicate-name behavior. Separate catalog constraints allow the same normalized code once for a Lecturer and once for a Room.

**Alternatives considered**: Unique display names contradict clarification; system IDs are not planner-maintained or sufficiently meaningful; a shared inheritance/resource table complicates existing foreign keys and offers no current value.

## Eligibility source of truth and legacy migration

**Decision**: Use composite-key CourseEligibleLecturer and CourseEligibleRoom junctions as the sole eligibility source. Migration 0004 creates one row in each set from every legacy Course scalar assignment, then removes the scalar Course lecturer/room columns after all services and contracts move to sets. DraftSession assignments remain unchanged.

**Rationale**: Keeping scalar defaults would create a hidden ranking and two competing truths. Junctions enforce distinct membership, support atomic replacement, and let every session retain exactly one concrete assignment.

**Alternatives considered**: Retaining hidden default fields preserves old code temporarily but conflicts with no-ranking semantics and makes deletion/capacity cleanup ambiguous; arrays on Course weaken relational integrity; per-link revisions create race windows around the last-resource rule.

## Migration and startup ordering

**Decision**: Add sequential migration `0004_resource_eligibility_availability`. Generate deterministic, collision-free, editable legacy codes (`LECT-<id>`, `ROOM-<id>`), set active/revision defaults, backfill eligibility before dropping scalar Course columns, create unavailability structures, and preserve all DraftSession foreign keys. Detect an empty database before `Base.metadata.create_all`; migrate recognized existing schemas before creating/verifying current metadata.

**Rationale**: Current startup calls `create_all` before migration. Once current metadata includes new tables, doing that against FS-007 would pre-create objects that migration 0004 also creates. Explicit empty-versus-existing ordering makes clean creation and upgrade deterministic.

**Alternatives considered**: Conditional create logic inside the migration is brittle; a destructive rebuild loses schedules; requiring immediate manual legacy-code repair would make migrated courses unusable.

## Availability representation and overlap

**Decision**: Store a revisioned ResourceUnavailabilityPeriod with exactly one Lecturer or Room owner and a `recurring` or `dated` kind. Recurring rules own one or more weekday child rows plus same-day start/end times; dated rules own start/end local date/time boundaries and may span dates. Validate the shape by kind, reject exact per-owner duplicates, allow partial overlaps, union every applicable rule, and evaluate `[start, end)` overlap.

**Rationale**: One owner table avoids duplicated Lecturer/Room logic while retaining real foreign keys. A weekday child set keeps one multi-weekday planner entry atomic. Half-open overlap matches existing conflict logic and the clarified boundary rule.

**Alternatives considered**: A string resource type plus ID loses referential integrity; separate availability tables duplicate behavior; one row per weekday breaks one recurring entry into unrelated revisions; positive overrides contradict the specification.

## Course-local generation and fixed preferences

**Decision**: Refactor course generation to consume complete eligibility and availability inputs. Temporal placement requires at least one feasible Lecturer and Room for each session. Assign resources within one Course Draft Schedule using deterministic dynamic programming that independently minimizes lecturer changes and room changes; normalized code and stable ID are tie-breakers. Do not coordinate between courses or maximize semester-wide scheduled units.

**Rationale**: Multiple eligible resources must be usable before FS-010, and the clarified preferences are always considered. A small course-local assignment pass satisfies hard rules and minimizes switches without creating resource ranking or global optimization.

**Alternatives considered**: Always using a legacy scalar ignores maintained alternatives; selecting the first feasible resource greedily can cause avoidable later switches; a cross-course solver is FS-010; persisting preference flags, weights, quotas, or ranks contradicts clarification.

## Resource retirement, deletion, and reactivation

**Decision**: Implement one revisioned transactional removal command. Recheck usage at mutation time. If active-course eligibility or any DraftSession reference exists, set the resource inactive and return active course identities plus session counts. Otherwise remove inactive-course eligibility and owned unavailability before permanent deletion. Reactivation validates current data and makes preserved relationships usable only where current hard rules pass.

**Rationale**: This directly represents the clarified delete-or-inactivate outcome, prevents inactive-only catalog growth, preserves history, and does not trust a stale preflight assessment.

**Alternatives considered**: Always inactivate causes the stated usability problem; a disabled delete plus separate archive action does not implement the requested outcome; cascading sessions violates protected history.

## Eligibility concurrency and capacity changes

**Decision**: Treat both resource sets as one Course aggregate replaced atomically with `expectedRevision`. Compute relationship usability rather than storing it. Reject planner removal of the last resource, inactive additions, duplicates, and newly undersized rooms. Room capacity reduction preserves links as invalid; Cohort growth removes newly insufficient room links, increments affected Course revisions, preserves sessions, and returns an impact summary.

**Rationale**: One aggregate write prevents transient empty sets and stale-checkbox races. Computed usability cannot drift. The asymmetric capacity behavior is explicitly clarified in FR-022 and FR-043.

**Alternatives considered**: One request per checkbox can partially apply; stored validity becomes stale; blocking cohort growth or automatically removing links on Room shrink contradicts the specification.

## Validation and manual editing

**Decision**: Add separate lecturer/room ineligibility and unavailability alert codes and retain capacity alerts. Load display identity from each DraftSession assignment. Extend existing session PATCH with optional `lecturerId`; a changed assignment must be active and eligible, while unchanged legacy-invalid assignments may survive unrelated edits. Capacity remains a blocking edit rule; availability and cross-session conflicts remain non-blocking alerts consistent with existing planner-controlled edits.

**Rationale**: Current validation already accumulates read-time, non-blocking alerts but assumes Course-level Lecturer context. Per-session loading supports multiple assignments and preserves existing invalid schedules for repair.

**Alternatives considered**: One generic resource alert is not actionable; blocking every unrelated edit until all existing alerts are repaired breaks preservation behavior; rewriting FS-007 academic snapshots changes historical facts.

## HTTP and transaction boundaries

**Decision**: Keep resource CRUD, usage, removal/reactivation, and nested availability on a focused resource router under `/api/resources`; keep Course eligibility under `/api/academic/courses/{id}/resource-eligibility`; extend planning options, Cohort mutation effects, generation responses, and DraftSession PATCH additively. Use canonical camelCase DTOs, `errors[]`, 409 stale conflicts, 422 validation, API-owned commits, and service-owned flushes.

**Rationale**: Resource lifecycle is cohesive and distinct from generic academic CRUD, while Course eligibility belongs to the existing academic aggregate. Existing transaction and error conventions remain recognizable.

**Alternatives considered**: A generic polymorphic resource endpoint weakens typed validation; per-link endpoints create race windows; embedding availability in Course duplicates resource-owned data.

## Client information architecture

**Decision**: Extend the existing Academic Data workspace with Lecturer and Room categories instead of adding a router or third top-level application view. Default resource lists to Active, allow All/Inactive and name/code search, show `Name · CODE`, and use a detail panel for fields, availability, usage, retirement, and reactivation. Edit Course eligibility atomically with typed checkbox/search groups and read-only preference guidance.

**Rationale**: The current page already supplies administration navigation, responsive list/editor layout, revisioned mutation feedback, and a catalog-change callback that refreshes Schedule. Active-default filtering directly addresses inactive-item usability.

**Alternatives considered**: A separate Resources application view fragments Course configuration; modal-only forms obscure correction context; a flat global availability list loses resource ownership; extending the stringly generic editor for every behavior would reduce type safety and maintainability.

## Accessibility, stale recovery, and testing

**Decision**: Reuse semantic labelled controls, fieldsets for weekdays/eligibility, focus-managed dialogs, `role=alert`/`role=status`, retained last-known content, and responsive stacking. Every mutation sends an expected revision. On 409, keep the local draft and offer explicit review of current values. Test first at pure rule, service, API, migration, client API, component, page, performance, and regression layers.

**Rationale**: These patterns already exist and are needed for measurable first-attempt completion, stale-write safety, and keyboard operation. Layered tests localize transactional and boundary failures.

**Alternatives considered**: Automatic retry risks overwrites; automatic form reset loses entered values; snapshot-only or end-to-end-only tests miss rule and transaction defects; adding a component/testing library solely for this slice is unnecessary.

