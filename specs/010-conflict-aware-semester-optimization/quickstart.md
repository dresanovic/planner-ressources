# Validation Quickstart: FS-010 Conflict-Aware Semester Optimization

## Purpose

Use this guide after implementation to validate the conflict-aware optimizer end to end. It proves the specification and [HTTP contract](contracts/conflict-aware-optimization.openapi.yaml) without duplicating implementation tasks.

## Prerequisites

- Python 3.12 environment with `backend/requirements.txt` installed, including pinned OR-Tools.
- Node.js environment with `client/package-lock.json` installed.
- A disposable SQLite database or isolated test database.
- FS-001 through FS-009 migrations and seed/test fixtures available.
- Reference workload fixture documentation identifying hardware, 20 selected courses, 600 requested units, and 500 fixed sessions.

## Setup and Baseline

From `backend/`:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

From `client/`:

```powershell
npm ci
npm test
npm run lint
npm run build
```

Start the application only after the baseline passes:

```powershell
# backend/
python -m uvicorn app.main:app --reload

# client/ in another terminal
npm run dev
```

## Scenario 1: Request-Order Counterexample

1. Create Course A with 2 units and valid Monday/Tuesday choices.
2. Create Course B with 4 units and only a Monday choice.
3. Give both the same sole suitable Room; keep Tuesday viable for A.
4. Prepare and confirm optimization for both courses.

**Expected**:

- B uses Monday and A uses Tuesday.
- Six total units are scheduled.
- No Lecturer, Room, or Cohort overlap is introduced.
- Reversing selection order produces the identical result.

## Scenario 2: Eligible Resource Choice

1. Give a course two eligible Lecturers and two capacity-sufficient eligible Rooms.
2. Occupy one Lecturer and one Room during otherwise viable times.
3. Optimize with another selected course sharing some choices.

**Expected**:

- Only active, eligible, available, capacity-sufficient resources are assigned.
- The alternate valid resources are selected when they enable greater total coverage.
- No legacy scalar or first-listed resource overrides the eligible set.

## Scenario 3: Fixed Occupancy and Existing Conflicts

1. Add unselected and manually created semester sessions.
2. Include a selected current draft that has a known overlap.
3. Optimize equal-unit alternatives.

**Expected**:

- Unselected sessions never move and block new conflicting candidates.
- A newly generated session never conflicts with retained occupancy.
- Each current overlapping pair counts once per Lecturer, Room, and Cohort conflict type.
- An equal-unit conflict reduction can replace only after confirmation; an equal non-improvement remains unchanged.

## Scenario 4: Best Partial Result and Reasons

1. Constrain resources/windows so not all selected units fit.
2. Ensure at least two courses compete for one viable resource interval.
3. Optimize.

**Expected**:

- The proven maximum total units are saved.
- Each incomplete course shows accurate scheduled and remaining units.
- Reasons include applicable occupied/unavailable/eligibility/capacity/window/competition categories.
- Reasons are phrased as evidence and not a unique-cause proof.
- A zero-placement course has no empty Draft Schedule and is `unchanged`.

## Scenario 5: Strict Objective Order

Use independently established small fixtures for each tier while holding higher tiers equal:

1. Total scheduled units.
2. Distinct conflict relationship count.
3. Adjacent Lecturer changes per course, summed globally.
4. Adjacent Room changes per course, summed globally.
5. Number of complete current Draft Schedules preserved unchanged.
6. Canonical stable order.

**Expected**: Each fixture selects the arrangement required by the first differing tier; no lower tier worsens a higher tier.

## Scenario 6: Non-Worsening Replacement

1. Prepare current drafts with complete and partial coverage plus manual edits.
2. Exercise a fewer-unit candidate, equal non-improvement, equal strict improvement, and higher-unit candidate.
3. Include a current draft whose scheduled units exceed the course's current total.
4. Cancel confirmation once, then repeat and confirm.

**Expected**:

- Cancellation changes nothing.
- A fewer-unit candidate never replaces.
- The over-scheduled current draft remains unchanged because no generated candidate capped at the current course total can match its actual scheduled units.
- An equal non-improvement remains unchanged.
- An equal strict improvement or higher-unit result may replace.
- Other semesters and unselected courses remain unchanged.
- Existing saved custom generation constraints and source academic/resource records remain unchanged. A successfully generated course with no saved constraint set retains the exact active defaults through the established generation behavior; failed, stale, unchanged, and cancelled outcomes do not change constraints.

## Scenario 7: Unavailable-Date Boundary

1. Send a unique unavailable date inside the semester.
2. Also send dates outside the semester in a separate valid request.

**Expected**:

- No generated session uses the in-semester unavailable date.
- Outside-semester dates have no scheduling effect.
- The feature exposes no holiday name or CRUD behavior.
- Duplicate request dates are accepted, canonically deduplicated, and have the same effect as one occurrence.

## Scenario 8: Stale Input Without Re-optimization

1. Prepare and confirm an operation.
2. While solving, change one selected Draft Schedule or material resource/constraint input.
3. Leave at least one exact unaffected planned result valid against refreshed state.

**Expected**:

- The changed course is `stale` and remains unchanged.
- Only exact unaffected results that remain valid may save.
- No second optimization silently runs.
- A now-invalid planned result is also preserved and reported stale/failed.
- The result reports optimality for the prepared snapshot only and does not claim that refreshed final semester state is globally optimal.
- Retry starts with fresh preparation and confirmation.

## Scenario 9: Solver Proof and Failure Safety

1. Run a bounded fixture that returns `OPTIMAL` at every stage.
2. In an isolated test, force deadline/`FEASIBLE`, `UNKNOWN`, and model-invalid paths.

**Expected**:

- Only the fully proven result reaches persistence.
- Every unproven/invalid path returns an actionable no-save operation failure.
- No course has a partially created or partially replaced Draft Schedule.

## Scenario 10: Determinism

Run the same reference fixture at least 20 times with unchanged database and request inputs.

**Expected**: Every run returns identical sessions, resource assignments, course statuses, objective measures, and reason codes.

## Scenario 11: Mixed Summary and Refresh

Construct one operation with complete, improved partial, unchanged, failed, and stale outcomes.

**Expected**:

- Every selected course appears exactly once.
- Summary counts equal the outcome list.
- Scheduled and remaining units match final saved state.
- `optimalForPreparedSnapshot` is true only when the solver completed every proof stage; stale mixed results do not present refreshed final state as globally optimal, while a pre-solve stale operation reports false.
- Retry targets failed/stale courses through fresh preparation.
- The Courses overview and validation alerts refresh without manual reload and contain no speculative/deleted session references.

## Scenario 12: Reference Performance

Run the documented fixture with 20 selected courses, 600 requested units, and 500 fixed semester sessions under recorded reference hardware.

**Expected**:

- At least 95% of repeated operations return a saved-state result or actionable failure within 30 seconds.
- Every operation returns within 60 seconds.
- Saved results are still proven optimal; timeout does not silently save `FEASIBLE` output.

Record raw timing, solver-stage status, fixture seed, application version, OR-Tools version, Python version, database type, and hardware under `specs/010-conflict-aware-semester-optimization/validation/`.

## Usability Acceptance Protocol (SC-006 and SC-007)

1. Recruit at least 10 representative planners or acceptance reviewers familiar with the existing planner and provide no optimization-summary coaching.
2. Give each participant a prepared result containing complete, improved partial, and unchanged courses with at least one incomplete-course reason.
3. Measure whether, within two minutes, the participant identifies each outcome group and one reason for every incomplete course.
4. Before a separate confirmed replacement run, ask the participant to identify that existing drafts/manual edits may be replaced.
5. After the run, ask the participant to distinguish an improved partial outcome from an unchanged outcome.

**Expected**:

- At least 90% identify completion/partial/unchanged groups and one reason per incomplete course within two minutes.
- 100% identify the replacement consequence before confirmation.
- At least 90% distinguish improved partial from unchanged afterward.

Record anonymized participant results, timing, prompts, failures, and aggregate percentages in `specs/010-conflict-aware-semester-optimization/validation/usability-results.md`.

## Focused Verification Commands

From `backend/`:

```powershell
python -m pytest tests/services/test_semester_optimization.py
python -m pytest tests/services/test_conflict_aware_generation.py tests/api/test_conflict_aware_generation.py
python -m pytest tests/performance/test_semester_optimization_performance.py
python -m pytest
```

From `client/`:

```powershell
npm test -- conflictAwareGeneration MultiCourseGenerationPanel BatchResultSummary CourseSchedulePage
npm test
npm run lint
npm run build
```

## Completion Evidence

Before implementation is considered complete, store results for all twelve scenarios and the usability acceptance protocol under `specs/010-conflict-aware-semester-optimization/validation/`, including the independently established optimal fixture totals and the reference performance protocol.
