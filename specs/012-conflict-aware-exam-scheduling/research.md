# Phase 0 Research: FS-012 Conflict-Aware Exam Scheduling

## Decision 1: Persist exams separately from teaching drafts

**Decision**: Add `CourseExamConfiguration` and `ExamSession` persistence. Do not add exam variants to `DraftSchedule` or `DraftSession`.

**Rationale**: Teaching drafts are whole-replacement aggregates with unit counts, teaching-window metadata, and one draft per course-semester. Exams need one current configuration, unlimited past occurrences, one date-derived active occurrence, independent edit/delete, no teaching units, and preserved configuration snapshots. Separate tables avoid nullable teaching-only fields and prevent teaching draft deletion/replacement from affecting exams.

**Alternatives considered**:

- Add `session_kind` and nullable exam fields to `DraftSession`: rejected because teaching progress, uniqueness, replacement, deletion, and alert semantics would leak into exams.
- Create a generic base session hierarchy: rejected because it adds an abstraction before a third concrete session type or proven shared persistence need exists.

## Decision 2: Use one mutable current configuration plus saved session snapshots

**Decision**: Store at most one revisioned current configuration per course-semester. Copy all defining configuration and source context required for review into each saved exam session. A configuration may be enabled before teaching exists but remains unplaceable without a final teaching anchor. Once it produces an active exam, the consumed configuration is read-only; when the exam becomes past, the planner prepares a freshly replaced current configuration while past session snapshots remain independent.

**Rationale**: This satisfies early explicit configuration, fresh-next-configuration, and past-exam preservation with two tables. Making a consumed active-exam configuration read-only removes ambiguous edits that could neither affect the saved exam nor validly prepare a second one. Historical configuration rows, event sourcing, or a version table are unnecessary because the exam session itself is the historical planning record.

**Alternatives considered**:

- Preserve every configuration version as a child table: rejected as unnecessary lifecycle and foreign-key complexity.
- Keep past sessions joined to the mutable current configuration: rejected because later edits would rewrite historical context.

## Decision 3: Derive active/past from an injected institution clock

**Decision**: Derive `active` when `exam_date >= institution_today` and `past` otherwise. Centralize `institution_today()` using Python `zoneinfo`, with `INSTITUTION_TIMEZONE` defaulting to `Europe/Vienna`; tests inject or patch the clock.

**Rationale**: The rule is date-relative and cannot be represented safely by a permanent `is_active` flag. A backend clock prevents browser/UTC disagreement and makes midnight/DST tests deterministic without adding a dependency.

**Alternatives considered**:

- Browser-derived status: rejected because clients may use different timezones.
- Persisted `is_active`: rejected because it becomes stale when the date changes.
- Server `date.today()` without an explicit boundary: rejected because it is hard to test and may not represent institution-local time.

## Decision 4: Enforce the one-active invariant transactionally

**Decision**: Before generated/manual insert or correction to today/future, claim the affected semester write boundary, re-read same-course-semester exams using the current institution date, and reject any second active exam. Recheck immediately before flush/commit together with expected revisions and material-input snapshots.

**Rationale**: A database uniqueness constraint cannot contain a moving `today` predicate. The existing SQLite no-op Semester update/revision-claim patterns provide a serialization boundary compatible with the project.

**Alternatives considered**:

- Static partial unique index: rejected because database predicates cannot advance with the current date.
- Best-effort service query without a write boundary: rejected because concurrent mutations could both pass.
- Persist a separate active-slot row: rejected because it duplicates a date-derived state and needs rollover maintenance.

## Decision 5: Reuse established planning windows only as automatic proposal times

**Decision**: For each course, automatic generation uses the start times of every applicable active Study Type Time Window as the finite, deterministic time-of-day proposal set. This automatic proposal domain is explicit feature behavior, not a hard constraint on manual placement. When no active window supplies a proposal time, generation returns `AUTOMATIC_START_TIME_UNAVAILABLE`. A planner may manually place an exam at another time if every approved hard constraint passes.

**Rationale**: Reusing maintained window starts supplies bounded, institution-relevant proposal times with no new setting or dependency, matching the existing teaching optimizer's deterministic candidate convention while preserving planner control. Naming the proposal domain and its missing-input failure prevents generation from implying that every clock time was searched.

**Alternatives considered**:

- Every minute or fixed 15/30-minute grid across 24 hours: rejected as arbitrary, potentially producing midnight exams and inflating the 100-course candidate set.
- New exam-hours administration: rejected as unapproved scope.
- Treat Study Type windows as hard exam rules: rejected because the specification names only the final-teaching and semester timing boundaries as hard.

## Decision 6: Build a focused deterministic exam optimizer

**Decision**: Add `exam_optimization.py` beside the teaching optimizer. Use current OR-Tools CP-SAT patterns with canonical ordering, one worker, fixed seed, and staged objectives: (1) maximize scheduled exams, (2) maximize placements inside each recommended date window, and (3) minimize canonical date/time/room rank.

**Rationale**: Joint optimization is required to prevent proposed exams from conflicting. Exams have fixed duration, one configured lecturer, room choices, and no teaching-unit distribution or draft-replacement objective, so adapting the full teaching model would be more complex.

**Alternatives considered**:

- Run one greedy course at a time: rejected because order could create avoidable failures and would not jointly enforce the best mixed outcome.
- Extend `semester_optimization.py` with exam branches: rejected because it couples unrelated unit-distribution and replacement objectives.
- Introduce a generic solver framework: rejected because only two concrete models exist and their inputs/objectives differ materially.

## Decision 7: Reuse hard constraint sources, not teaching mutation semantics

**Decision**: Reuse FS-008 resource eligibility/capacity/unavailability, half-open overlap helpers, FS-011 holiday snapshots, and FS-010 fixed occupancy/snapshot patterns. Treat every teaching session and saved exam as fixed occupancy. Exam manual mutations enforce these constraints as blocking errors rather than teaching-style non-blocking alerts.

**Rationale**: The authoritative data and interval semantics already exist, while FS-012 explicitly upgrades conflicts, availability, holidays, capacity, and eligibility to hard exam rules.

**Alternatives considered**:

- Duplicate availability/holiday logic: rejected because it risks semantic drift.
- Reuse manual DraftSession validation unchanged: rejected because teaching overlap/availability alerts are intentionally non-blocking.

## Decision 8: Keep the recommended date range soft and explicit

**Decision**: Store nullable planner overrides for recommended start/end dates. When a final teaching anchor exists and overrides are absent, derive the effective recommendation as final teaching date +7 through +14 calendar days. When the anchor is absent, retain the enabled configuration but return null effective recommendation dates and mark it ineligible for placement. Automatic generation prefers the effective window but may place elsewhere after final teaching and inside the semester. Manual placement outside it is accepted and flagged without changing the saved recommendation.

**Rationale**: This matches clarification: the range guides automatic placement and never becomes a hard boundary. Nullable overrides prevent derived defaults from silently becoming stale stored values when teaching changes.

**Alternatives considered**:

- Store only concrete default dates: rejected because a teaching change would make them look planner-authored or silently stale, and no dates can be derived before a teaching anchor exists.
- Reject configuration enablement until teaching exists: rejected because explicit exam configuration is useful before placement inputs are complete and the specification requires an understandable missing-anchor state.
- Reject automatic/manual placement outside the range: rejected by clarification.
- Automatically expand the range after manual placement: rejected because it silently changes planner configuration.

## Decision 9: Preserve exact configuration and anchor context on ExamSession

**Decision**: Persist on each exam the configuration identifier, duration, free-text type, required capacity, effective recommended dates and override marker, final-teaching anchor used, configured responsible lecturer, assigned lecturer/room/cohort, and generated/manual source, together with date/time and revision.

**Rationale**: Past exams must remain understandable after the current configuration or source records change. Stored snapshots are also needed to show recommendation deviation and deletion consequences.

**Alternatives considered**:

- Store only foreign keys to current configuration: rejected because past context would change.
- Full audit/event log: rejected because audit and publication history are outside FS-012.

## Decision 10: Use prepare/generate snapshots without replacement confirmation

**Decision**: Add exam-specific preparation and generation endpoints. Preparation returns per-course configuration revisions/tokens plus a shared semester token. Generation echoes them, solves jointly, revalidates material inputs and the exact arrangement inside the write boundary, then returns scheduled/failed/stale/skipped-active outcomes. Existing exams are never replacement candidates.

**Rationale**: FS-010 already proves opaque snapshot and exact-result revalidation in this codebase. FS-012 needs the stale protection but not teaching draft replacement confirmation.

**Alternatives considered**:

- One unversioned generation POST: rejected because teaching/resource/holiday/exam inputs can change during a 60-second operation.
- Reuse teaching optimization routes/DTOs: rejected because units, replacement, unavailable-date input, and outcome language are teaching-specific.
- Persist generation operations or failure history: rejected because current project generation outcomes are transient and the spec does not require audit history.

## Decision 11: Protect manual mutations with row revisions and material snapshots

**Decision**: Configuration saves carry `expectedRevision`; exam edits/deletes carry the exam revision and an input snapshot token covering relevant teaching/exam occupancy, resource state, holidays, semester, final teaching anchor, and institution date. Stale actions return `409`, refresh current state, and require renewed review.

**Rationale**: Target-row revision alone cannot detect a newly created conflict, holiday, or changed availability. This matches the specification's stronger related-state stale rule and existing refresh/reopen UI convention.

**Alternatives considered**:

- Last-write-wins: rejected because it could persist an invalid exam.
- Target revision only: rejected because related planning inputs determine validity.
- Long-lived database locks while the user edits: rejected as impractical and unnecessary.

## Decision 12: Derive validity issues on reads

**Decision**: Re-evaluate every saved exam against current final teaching, semester, eligibility, capacity, availability, holidays, and teaching/exam occupancy when reading semester exam state. Return structured validity issues and a separate `outsideRecommendedWindow` flag; do not persist alerts or auto-repair sessions.

**Rationale**: This follows the existing holiday/teaching alert pattern and satisfies preservation after later input changes.

**Alternatives considered**:

- Persist validation rows: rejected because they become stale and require broad update fan-out.
- Automatically move/delete invalid exams: rejected by planner-control requirements.

## Decision 13: Use additive exam-specific APIs and a unified review view

**Decision**: Add dedicated exam schemas/router/service and `client/src/api/examScheduling.ts`. Keep configuration/generation controls inside Schedule. Extend the current review panel with a discriminated teaching/exam view model, visible text badges, active/past status, hard issues, and soft recommendation deviation.

**Rationale**: Dedicated write contracts preserve type safety; unified review is required to understand teaching/exam conflicts. No navigation or Academic Data expansion is needed.

**Alternatives considered**:

- Add nullable exam fields to teaching APIs: rejected because it weakens both contracts.
- Add a new top-level or Academic Data destination: rejected as outside FS-018 navigation and disconnected from schedule review.
- Build the FS-014 calendar workspace now: rejected as downstream scope.

## Decision 14: Keep type entry free-form and bounded by existing text conventions

**Decision**: Accept a trimmed, required free-text exam type using the existing 1–200 character catalog text convention. Do not add an enum or catalog.

**Rationale**: Clarification explicitly selects free text; a reasonable length boundary makes validation and storage testable while matching current names.

**Alternatives considered**:

- Fixed written/oral/practical enum: rejected because institutional taxonomy is unconfirmed.
- Planner-managed type catalog: rejected as a separate administration feature.

## Decision 15: Extend the existing migration chain without changing earlier rows

**Decision**: Add migration `0006_conflict_aware_exam_scheduling.py`, update schema-state detection from the FS-011 head to FS-012, and test clean creation plus recognized 0005→0006 upgrade/downgrade. Prior academic/resource/holiday/teaching data is unchanged.

**Rationale**: The application uses explicit sequential migration discovery at startup; bypassing it would leave supported existing databases behind.

**Alternatives considered**:

- Rely only on `Base.metadata.create_all`: rejected because it does not alter existing schemas safely.
- Rewrite prior migrations: rejected because they are already released project history.
