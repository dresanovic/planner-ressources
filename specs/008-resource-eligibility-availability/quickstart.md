# Quickstart Validation: FS-008 Resource Eligibility and Availability

## Purpose

Validate the implementation against [spec.md](spec.md), [data-model.md](data-model.md), and [the HTTP contract](contracts/resource-eligibility-availability.openapi.yaml). This guide proves the slice end to end; it does not contain implementation code or replace test-first tasks.

## Prerequisites

- Work on a `codex/` feature branch before changing production code.
- Python 3.12 with `backend/requirements.txt` installed.
- Node.js with `client/package-lock.json` installed through `npm ci`.
- A disposable SQLite acceptance database plus a copy of an FS-007 database for upgrade testing.
- Tests for each scenario written before its production change.

## Automated verification

From `backend/`:

```text
python -m pytest tests/services/test_resource_catalog.py tests/services/test_resource_rules.py tests/api/test_resource_catalog.py tests/db/test_migrations.py
python -m pytest tests/services/test_schedule_generation.py tests/services/test_draft_schedule_validation.py tests/api/test_draft_schedule.py tests/api/test_planning_options.py tests/api/test_academic_catalog.py
python -m pytest
```

From `client/`:

```text
npm test
npm run lint
npm run build
```

## Scenario 1: Clean schema and FS-007 upgrade

1. Start once with an empty disposable database.
2. Confirm all FS-008 tables, constraints, and foreign keys exist.
3. Upgrade a copy of an FS-007 database containing Courses and DraftSessions.
4. Compare every pre/post DraftSession Lecturer and Room ID.
5. Inspect migrated resource codes and Course eligibility.

Expected:

- Clean creation succeeds without trying to rerun migration-owned table creation.
- Each legacy Lecturer has `LECT-<id>` and each legacy Room has `ROOM-<id>`, editable by the planner.
- Every Course has its previous Lecturer and Room in its initial eligibility sets.
- Every DraftSession assignment and saved academic snapshot remains unchanged.
- Unknown partial schemas stop with an actionable error.

## Scenario 2: Duplicate names and unique codes

1. Create two Lecturers with the same display name and different codes.
2. Create two Rooms with the same display name and different codes.
3. Attempt codes that differ from existing codes only by case or surrounding whitespace.
4. Search and select each same-named resource.

Expected:

- Duplicate display names are accepted.
- Normalized duplicate codes are rejected with field-addressable feedback.
- Lists, eligibility, usage, assignment, and retirement views show `Name · CODE` and select the intended stable ID.

## Scenario 3: Retirement, deletion, and reactivation

1. Request removal of a resource used by an active Course and a DraftSession.
2. Confirm the removal dialog lists active Course identities and session counts.
3. Confirm the operation and inspect its actual disposition.
4. Reactivate the resource after ensuring its current fields are valid.
5. Separately request removal of a resource linked only to inactive Courses and no DraftSession.

Expected:

- The protected resource is inactivated, not deleted; all relationships and sessions remain.
- It disappears from default active and new-assignment choices but remains visible through Inactive/All and historical context.
- Valid reactivation restores active choices and makes preserved relationships usable only where hard rules pass.
- The unprotected resource is deleted after inactive-Course links and owned unavailability are cleaned up.
- The server result, not a stale preflight, determines the message shown.

## Scenario 4: Recurring and dated unavailability

1. Add one recurring rule with several weekdays and one dated rule spanning dates.
2. Attempt an exact duplicate and a partially overlapping rule.
3. Validate sessions that overlap, end exactly when unavailability starts, and start exactly when it ends.
4. Open two views, save one rule edit, then attempt a stale edit from the other.

Expected:

- Exact duplicates are rejected; partial overlaps are accepted and unioned.
- Every positive-duration overlap produces the resource-specific alert.
- Touching boundaries do not overlap.
- The stale write returns 409, preserves the local draft, and offers current-value review.

## Scenario 5: Atomic Course eligibility

1. Configure one Course with two Lecturers and two capacity-sufficient Rooms.
2. Attempt duplicate IDs, an inactive resource, an undersized new Room, and removal of the final Lecturer or Room.
3. Cause a concurrent Course revision and retry the older eligibility update.
4. Inspect fixed preference guidance.

Expected:

- Both sets save atomically or not at all.
- Invalid additions and final-resource removal are rejected with actionable errors.
- Stale replacement changes no relationship.
- Preference guidance states that Lecturer changes and Room changes are minimized with no switch, rank, quota, or global scope.

## Scenario 6: Capacity asymmetry

1. Reduce a Room capacity below the Cohort size of a currently eligible Course.
2. Confirm the relationship remains visible but unusable and sessions remain unchanged.
3. Restore the database, then instead increase the Cohort size past several eligible Room capacities.

Expected:

- Room capacity reduction preserves the relationship and adds capacity validation to affected sessions.
- Cohort growth removes every newly insufficient eligibility relationship atomically, increments affected Course revisions, and reports Courses left without Rooms.
- Existing DraftSessions remain assigned and show capacity plus ineligibility alerts where applicable.

## Scenario 7: Course-local assignment and preference behavior

1. Configure a Course whose sessions require multiple Lecturers or Rooms because of unavailability.
2. Generate the Course repeatedly with identical inputs.
3. Run multi-Course generation with overlapping eligible resources.

Expected:

- Every generated session has exactly one active eligible available Lecturer and capacity-sufficient available Room.
- Within the Course, assignments minimize unnecessary Lecturer and Room changes and are deterministic.
- Hard constraints override preferences.
- Different Courses are still generated independently; FS-005 reports conflicts and no FS-010 global maximization occurs.

## Scenario 8: Existing session editing and validation

1. Edit an existing session's Lecturer and Room to active eligible choices.
2. Attempt changing to inactive, ineligible, or undersized choices.
3. Make an existing assigned resource ineligible or unavailable after saving.
4. Perform an unrelated edit while retaining a pre-existing invalid assignment.

Expected:

- Valid changed assignments save with exactly one Lecturer and Room.
- Invalid new assignment choices are rejected according to the contract.
- Source changes never move or delete the session; separate eligibility, availability, and capacity alerts appear together.
- Unrelated edits do not force silent reassignment or erase existing alerts.

## Scenario 9: Active-default and accessibility behavior

1. Create enough inactive resources to exceed the first active result page.
2. Open Lecturer and Room administration without changing filters.
3. Find an inactive resource through the explicit filter and reactivate it.
4. Repeat create, availability, eligibility, retirement, and stale-review flows using only the keyboard at wide and narrow layouts.

Expected:

- Default lists contain active records only; search covers name and code.
- Inactive resources remain deliberately discoverable without distorting active selection lists.
- Labels, fieldsets, dialogs, focus return/trapping, announced errors/status, and responsive stacking remain usable.

## Scenario 10: Regression boundary

Run every existing FS-001 through FS-007 backend and client test plus representative single-course generation, semester review, generation constraints, manual editing, conflict detection, multi-course generation, and academic administration flows.

Expected:

- Existing workflows remain usable with migrated and newly maintained resources.
- DraftSession still has exactly one Lecturer and Room.
- The slice introduces no holiday, exam, authentication, external synchronization, lecturer-access, or global-optimization behavior.

## Scenario 11: Refresh failure and last-known state

1. Load a selected resource with unavailable periods and a Course with saved eligibility.
2. Make the next resource and eligibility refresh fail.
3. Inspect the warning, selection, last-known saved values, and unsaved controlled-form input.
4. Restore connectivity and retry the refresh.

Expected:

- An actionable warning explains that displayed resource data may be stale.
- The selected resource and Course remain selected.
- Last-known saved content and unsaved input remain visible.
- No eligibility relationship, resource record, unavailable period, or DraftSession changes.
- A successful retry replaces stale content with current saved values.

## Performance acceptance

Record operating system, CPU, RAM, storage, browser/version, database type, and build identifier. Use exactly 100 Lecturers, 100 Rooms, 100 Courses, and 1,000 unavailability periods in a warmed local acceptance environment with no artificial network latency.

1. Run 20 representative list, detail, availability, eligibility, retirement, and save trials. At least 19 must become usable within 2 seconds.
2. Run 10 successful mutations requiring resource/planning/validation refresh. All 10 must show current values within 2 seconds.
3. Record raw durations, failures, and excluded runs with reasons under `specs/008-resource-eligibility-availability/validation/performance-results.md`.

## Usability acceptance

With at least 10 representative planner users or acceptance reviewers familiar with the planner, record role, first-attempt outcome, time, and non-identifying blockers under `specs/008-resource-eligibility-availability/validation/usability-results.md`.

1. Create coded Lecturer and Room records and associate two of each with a Course within 5 minutes.
2. Add recurring and dated unavailability and correctly identify interpreted times within 3 minutes.
3. Attempt protected removal and identify the disposition, affected Courses, and next action within 2 minutes.

At least 9 of 10 participants must pass each protocol without assistance.
