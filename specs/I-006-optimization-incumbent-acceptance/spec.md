# Feature Specification: I-006 — Configurable Optimization Time and Valid Incumbent Acceptance

**Working Branch**: `master` (specification-only work)

**Created**: 2026-11-04

**Status**: Draft — specification validated; ready for planning; not implemented

**Input**: Explicit request to use `$speckit-specify` for I-006: allow longer configurable teaching optimization and conscious acceptance of hard-valid candidates when optimality is unproven. This explicit request authorizes specification work; the requirements-only backlog did not authorize it by itself.

**Product authority**: [I-006 in Feature_slices.md](../../docs/planning/Feature_slices.md#i-006-configurable-optimization-time-and-valid-incumbent-acceptance). Dependencies: I-003, I-004, FS-013, FS-019. Independent of I-005.

**Evidence context**: The user reports larger first-plan selections for 2027 S on 03.11.2026 returned `OPTIMAL_RESULT_NOT_PROVEN`, objective `total_units`, and `saved: false`, while smaller selections succeeded. This motivates the change without proving a fixed feasible course count or invalid source data. Existing generation, result, and I-004 comparison surfaces are the interaction baseline.

## Clarifications

### Session 2026-11-04

- Q: If optimization times out with a valid assignment that schedules zero units across the entire selection, should the planner be allowed to accept it? → A: No. An unproven timeout result must schedule at least one teaching unit across the selection to be offered for acceptance; an entirely empty result preserves saved work and offers recovery. Individual courses may still have zero scheduled units.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Give the Selected Problem More Time (Priority: P1)

The installation operator configures the default budget and ceiling. The planner sees the effective budget and understandable running status without developer tools.

**Why this priority**: A longer usable budget addresses the demonstrated cutoff while keeping installation resource policy with the operator.

**Independent Test**: With shipped settings, start a problem that computes beyond sixty seconds. Verify a five-minute budget, continued search past sixty seconds, responsive controls, and elapsed status.

**Acceptance Scenarios**:

1. **Given** no overrides, **When** generation is prepared, **Then** the effective budget is 300 seconds and the configured ceiling is 1,800 seconds; the planner cannot override the budget per run.
2. **Given** operator settings of 600-second default and 1,200-second ceiling, **When** configuration takes effect, **Then** the next operation shows and uses 600 seconds; an existing operation retains its captured budget.
3. **Given** an invalid supplied setting, **When** configuration is evaluated, **Then** non-positive, non-finite, non-whole-second values or a default above the ceiling block new generation with actionable operator feedback; missing overrides alone use shipped values.
4. **Given** incomplete search after sixty seconds with budget remaining, **When** search continues, **Then** no inherited sixty-second cutoff terminates it, and connected elapsed/status updates occur at least every five seconds.
5. **Given** budget exhaustion with checking still pending, **When** status is shown, **Then** it states that optimization time ended and the result is being checked, without implying more search or a completed save.

---

### User Story 2 - Review and Accept a Feasible-Only Timeout Result (Priority: P1)

The planner reviews a hard-valid candidate with unproven maximum coverage and accepts or cancels the whole selection, including previously unplanned courses.

**Why this priority**: Missing proof should neither discard useful valid work nor authorize an automatic save.

**Independent Test**: Use two unplanned courses requiring 40 and 60 units. End search with a validated candidate scheduling 32 and 48 units and no optimality proof. Check review arithmetic, no save before acceptance, and atomic accept/cancel outcomes.

**Acceptance Scenarios**:

1. **Given** that feasible-only timeout, **When** review opens, **Then** scheduled/required/remaining counts are 80/100/20 overall and 32/40/8 and 48/60/12 per course; coverage optimality is unproven, nothing is saved, and `Neu erzeugten Stundenplan übernehmen` and `Abbrechen` are available.
2. **Given** that candidate and a trustworthy unit upper bound of 90 for the same prepared problem, **When** reviewed, **Then** it shows at most 10 additional possible units, distinct from 20 required units remaining, without promising 90 is achievable.
3. **Given** no trustworthy unit bound, **When** reviewed, **Then** the gap is explicitly unknown, with no invented bound/percentage or claim that remaining units cannot be scheduled.
4. **Given** selected saved sessions include manual work, **When** a valid unproven alternative is reviewed, **Then** I-004's current/generated comparison includes all selected courses, identifies manual-session replacement, and permits lower coverage without per-course acceptance.
5. **Given** an unchanged valid joint candidate, **When** accepted, **Then** fresh validation succeeds and all selected results save once atomically; unselected teaching, exams, constraints, and publication remain unchanged.
6. **Given** unresolved review, **When** cancelled, dismissed, or left, **Then** the entire candidate is discarded, including results for unplanned courses, and saved state is unchanged.
7. **Given** a course with zero scheduled units in a candidate scheduling at least one teaching unit elsewhere in the selection, **When** reviewed, **Then** it remains in the decision with all its units remaining and is not omitted or silently restored from another result.

---

### User Story 3 - Understand Exactly What Was Proven (Priority: P1)

The planner distinguishes coverage completeness from preference optimality and understands the selected-problem scope of proof.

**Why this priority**: A preference timeout must not hide proven coverage or imply that every objective or the semester is optimal.

**Independent Test**: Review proven maximum coverage with a later-objective timeout, then fully proven results for new and existing selections.

**Acceptance Scenarios**:

1. **Given** maximum coverage of 80/100 is proven and a later preference stage times out, **When** a hard-valid candidate is reviewed, **Then** coverage is identified as proven for the prepared selection, 20 remaining units are separate, unfinished/unattempted objectives are identified, and explicit acceptance is required.
2. **Given** 100/100 units but unfinished arrangement proof, **When** reviewed, **Then** coverage is complete, preference optimality is unproven, and no auto-save occurs.
3. **Given** an unproven earlier objective, **When** later proof applies only under its fixed candidate value, **Then** it is labeled conditional, not proof under the full priority order.
4. **Given** every required objective is proven and all selected courses are unplanned, **When** final validation succeeds before registered cancellation, **Then** established direct save applies and the result clearly states it was saved.
5. **Given** every required objective is proven and a selected course has saved sessions, **When** generation completes, **Then** I-004 comparison and explicit operation-wide acceptance still apply.
6. **Given** any proof/bound, **When** shown before or after acceptance, **Then** it refers to the prepared selection and fixed occupancy, without claiming global semester optimality, independent course maxima, or optimal later runs.
7. **Given** an earlier-stage candidate but no new assignment in the timed-out later stage, **When** the earlier candidate remains valid for the same prepared problem, **Then** it remains eligible for validation/review with evidence applying to that candidate.

---

### User Story 4 - Preserve Saved Work When No Result Can Be Accepted (Priority: P1)

The planner receives an honest no-result, stale, cancelled, or failed outcome without losing saved work.

**Why this priority**: More computation time widens the opportunity for interruption and changed inputs; preservation must remain intact.

**Independent Test**: Exercise no-candidate timeout, invalid assignment, stale acceptance, running cancellation, and failed joint save; compare saved state before and after.

**Acceptance Scenarios**:

1. **Given** no validated candidate at budget exhaustion, **When** the operation concludes, **Then** it reports timeout without a valid candidate, states nothing was saved, offers recovery, and offers neither acceptance nor an infeasibility claim.
2. **Given** an invalid or unchecked assignment at timeout, **When** a result is considered, **Then** it cannot be offered; an earlier hard-valid candidate may be checked, otherwise there is no valid candidate.
3. **Given** a provisional candidate, **When** relevant revision, selected/protected teaching, active-exam, constraint, holiday, course, semester, resource, eligibility, capacity, or availability state changes, **Then** acceptance rejects the whole candidate as stale without mutation and directs regeneration, even if it still appears feasible.
4. **Given** running computation without a commit, **When** cancellation or deliberate navigation away registers, **Then** provisional work is discarded and late responses cannot save or reopen its review.
5. **Given** any selected-course save cannot finish, **When** acceptance is attempted, **Then** no selected course changes or is partly created and actionable failure feedback appears.
6. **Given** repeated acceptance or an interrupted completion response, **When** reconciled, **Then** at most one complete result exists and actual saved state is shown; uncertainty is not described as confirmed cancellation or unsaved failure.
7. **Given** a commit completed before cancellation registered, **When** cancellation is attempted, **Then** the application reports the actual saved outcome instead of claiming cancellation or rolling it back.
8. **Given** optimization times out without complete objective proof and every available assignment schedules zero teaching units across the entire selection, **When** the operation concludes, **Then** it reports no usable timetable found within the time limit, offers no acceptance, preserves all saved work, and offers a fresh attempt or return to selection without claiming scheduling is impossible.

---

### User Story 5 - Start a Fresh Attempt With Clear Expectations (Priority: P2)

The planner can retry after timeout. An operator may increase the installation budget; the planner may reduce the selection.

**Why this priority**: Recovery must be actionable without implying resume or guaranteed improvement.

**Independent Test**: From timeout review, retry after an operator budget change; verify the new budget, old-candidate invalidation, and unchanged saved state until a permitted save.

**Acceptance Scenarios**:

1. **Given** timeout review, **When** fresh retry is invoked, **Then** the interface explains before starting that it discards the candidate, starts from current saved inputs, and may produce a worse result or none; returning to review without discarding is possible.
2. **Given** confirmed retry, **When** it starts, **Then** the previous candidate becomes unacceptable, the current configured budget is captured, and discard/retry alone saves nothing.
3. **Given** more time is desired, **When** recovery guidance appears, **Then** operator configuration is identified as the way to change time, no planner override appears, and smaller-selection recovery remains available.
4. **Given** no candidate, **When** recovery appears, **Then** fresh attempt or return to selection is available without guaranteeing optimality or timely completion.

### Edge Cases

- One to twenty courses, mixed planned/unplanned courses, and rejection above twenty; no new course-count guarantee.
- Timeout in the first objective, between stages, or in later stages; an earlier valid candidate is not lost solely because the later stage found none.
- Complete coverage without preference proof, partial coverage with proven maximum units, and conditional later evidence.
- Bounds equal to candidate units, above required units, absent, contradictory, non-finite, or associated with another stage/snapshot.
- No assignment, invalid assignment, and proven inability to add units are distinct claims. An entirely empty unproven timeout result is not usable for acceptance; zero scheduled units for one course remain permissible when another selected course has scheduled teaching.
- Warned/manual/over-scheduled current sessions; current excess units are not candidate optimality evidence.
- Protected occupancy changes during computation; publication, abandonment, or a new Working revision during review.
- Only ignored past exams or unrelated records change; I-003 relevance rules still apply.
- Configuration changes mid-operation; captured budgets remain stable.
- Cancellation races with timeout, late results, direct save, or acceptance; terminal reporting follows the actual commit boundary.
- Refresh, browser closure, disconnection, or reconnection; no provisional work becomes saved through interruption and uncertainty remains explicit.
- Long names/reasons, twenty-course review, keyboard-only use, narrow screens, and 200% zoom.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Teaching generation MUST retain one unified workflow for one to twenty selected courses in one semester's active editable Working revision, with established hard rules and objective priorities. Exam generation is outside this change.
- **FR-002**: The shipped default budget MUST be 300 seconds and initial ceiling 1,800 seconds. The installation operator MUST be able to configure both without source edits or rebuilding. This slice MUST NOT offer planner per-run overrides or a new configuration editor.
- **FR-003**: Values MUST be finite positive whole seconds with default no greater than ceiling. Missing overrides use shipped values; invalid supplied settings block new generation with actionable operator diagnostics, without silent clamping. The operator may change the ceiling; thirty minutes is not an immutable product maximum.
- **FR-004**: Operations MUST capture and show their effective budget before start. Configuration changes affect new operations only. No inherited sixty-second application/deployment cutoff may prevent use of the effective budget.
- **FR-005**: The budget MUST be one allowance for generation preparation and optimization from operation start, not per objective. At exhaustion, new optimization MUST stop. Checking/delivery may finish afterward with distinct status; human review/acceptance consume no optimization budget. Total elapsed time remains visible. The budget is not a guaranteed completion deadline.
- **FR-006**: Connected running status MUST show semester/revision, selection count, effective budget, elapsed time, and phase, updating at least every five seconds. Controls MUST remain operable and start/cancel visibly acknowledged within one second under acceptance conditions. Unconfirmed updates MUST show interrupted/unknown status rather than fabricated progress.
- **FR-007**: Status MUST distinguish preparing, optimizing, checking, awaiting decision, saving, saved, cancelled, timeout without candidate, and failed as applicable. Objective names appear only when known. Elapsed-budget percentage MUST NOT imply solution completion or probability of optimality. No finish estimate is required.
- **FR-008**: Exhaustion MUST distinguish a validated hard-valid candidate eligible for review, no usable candidate, and actual failure. An unproven timeout result scheduling zero teaching units across the entire selection MUST follow the no-usable-candidate outcome, preserve saved work, and offer recovery without acceptance. Timeout alone MUST NOT be called invalid input or proof of infeasibility.
- **FR-009**: Every offered candidate MUST satisfy all active semester/course dates, study-type windows, teaching-unit/session-size and break rules, holiday/unavailable-date rules, eligibility/availability, capacity, selected-course rules, lecturer/room/cohort non-overlap, fixed unselected teaching and active-exam occupancy, and same-course exam boundaries required by I-003. No planner choice waives a hard rule.
- **FR-010**: Candidates MUST pass hard validation before review even if the optimizer reports feasibility. Invalid/incomplete assignments MUST NOT be offered. A timeout candidate lacking complete objective proof MUST schedule at least one teaching unit across the selection to be offered for acceptance. An earlier-stage candidate MAY survive a later-stage timeout; its values and evidence MUST describe that same candidate and prepared problem.
- **FR-011**: Any candidate lacking proof through every required objective MUST remain provisional and require explicit operation-wide acceptance, including wholly unplanned selections and full-coverage candidates. It MUST NOT appear as saved Working-revision data before acceptance.
- **FR-012**: Review MUST show required/scheduled/remaining units and complete/partial coverage for the selection and every course. Remaining units retain established non-negative arithmetic. Courses with zero scheduled units remain in the decision when the offered timeout candidate schedules at least one teaching unit elsewhere in the selection. Substantiated reasons retain established categories; missing evidence MUST be stated. Encountered constraints MUST NOT imply further units are impossible when search is unproven.
- **FR-013**: Existing sessions MUST receive I-004 current/generated comparison, resolved-warning evidence, manual-replacement disclosure, and permission to accept lower coverage. For wholly unplanned selections, review MUST identify no saved teaching sessions and that acceptance creates candidate schedules.
- **FR-014**: Review MUST explain possible avoidable remaining units, improvable weekly/lecturer/room preferences, and constraints on later runs when accepted sessions become fixed occupancy. Complete coverage MUST NOT imply optimal preferences.
- **FR-015**: Each established objective MUST appear in priority order as proven, unproven/unfinished, not attempted, or conditional as applicable, with understandable labels and available values. Full-priority proof requires all preceding priorities proven. Scope MUST remain the prepared selection and fixed occupancy, never global semester optimality or independent per-course maxima.
- **FR-016**: A displayed unit upper bound MUST be trustworthy for the same prepared problem and coverage objective, not a preference-stage bound or heuristic estimate. Required total units MAY tighten a sound bound above them. Bounds below candidate units, non-finite evidence, or uncertain scope MUST be excluded and gap marked unknown. Required-unit arithmetic alone MUST NOT masquerade as optimizer progress.
- **FR-017**: For sound bound U and candidate units S, review MUST explain at most U minus S additional achievable units, separately from required minus scheduled, without promising U is attainable. Without such evidence the gap MUST be explicitly unknown, with no invented percentage. Proven maximum units establish zero coverage gap even when preference proof remains absent.
- **FR-018**: Review MUST retain `Neu erzeugten Stundenplan übernehmen` and `Abbrechen`. Dismissal/leaving unresolved review means cancellation. Acceptance MUST cover all selected courses, without per-course choices, mixing, or mandatory justification.
- **FR-019**: Immediately before atomic application, acceptance MUST freshly validate the active editable revision, candidate hard validity, and relevant planning/comparison inputs. Relevant changes since preparation MUST reject the entire candidate as stale and direct regeneration even if it appears feasible. Ignored past exams/unrelated changes alone MUST NOT invalidate it.
- **FR-020**: Acceptance MUST replace/create the whole selected result atomically and at most once. Failed/rejected application changes nothing. Unselected/protected sessions, exams, constraints, academic data, lifecycle, and publication MUST retain existing protections; partial selected-course salvage is prohibited.
- **FR-021**: A candidate MUST remain reviewable without fixed elapsed-time expiry during its current uninterrupted review while relevant inputs remain unchanged. Cancellation, dismissal, leaving context, confirmed retry, or loss of review context MUST invalidate acceptance. Refresh/reconnection MUST NOT silently restore an actionable discarded review; regeneration is required. Freshness is determined by relevant inputs and validation, not elapsed review time alone.
- **FR-022**: Running cancellation and deliberate navigation away MUST register cancellation, discard provisional work, and prevent late saves/reopened review. Changing semester/revision, leaving the Schedule generation surface, or closing its running surface counts as leaving; changes retaining the operation context need not cancel. Recognized browser closure/context loss MUST carry the same non-saving intent; abrupt interruption follows FR-023 reconciliation.
- **FR-023**: Cancellation registered before commit MUST preserve saved work. After accepted or fully proven direct save commits, late cancel/lost response MUST NOT be reported as confirmed cancellation or unsaved failure; actual outcome MUST be reconciled and shown. Repetition MUST NOT duplicate results. Pending reconciliation MUST communicate uncertainty and prevent contradictory decisions.
- **FR-023a (cancellation regression correction, 09.11.2026)**: A delayed or failed status request alone MUST NOT cancel a running optimization or discard its unchanged in-memory context. Show unconfirmed status and disable decisions until the same operation is freshly confirmed by the server. Retry using the same operation identity; never restore authority discarded by refresh, authentication loss or deliberate navigation. Confirmed cancellations MUST retain their actual trigger for diagnostic feedback rather than listing hypothetical causes.
- **FR-024**: No-candidate timeout, pre-commit failure, invalid candidate, stale rejection, and confirmed cancellation MUST preserve saved sessions/manual work/exams/constraints/unrelated records. No-candidate feedback MUST show elapsed time/budget, state nothing was saved, give available substantiated reasons, and offer fresh-attempt/smaller-selection recovery without acceptance.
- **FR-025**: Timeout review MUST offer a clearly labeled fresh-run action, such as `Erneut optimieren`, separate from the two decisions. Before discarding the candidate it MUST explain fresh start from current saved inputs, current configured budget, and no resume/improvement guarantee. The planner can return to review without discard. If called `Weiter optimieren`, fresh-run semantics MUST be explicit. Genuine continuation is excluded.
- **FR-026**: Longer retries MUST require operator configuration, without planner budget overrides. Confirmed retry MUST invalidate the previous candidate and freshly prepare inputs. Discard/retry alone saves nothing; selection remains capped at twenty.
- **FR-027**: Fully proven hard-valid results MUST retain established behavior after fresh validation: direct save for wholly unplanned selections, otherwise I-004 comparison/acceptance. Exhaustion after all proofs but before checking finishes MUST NOT waive validation or relabel genuinely complete proof as unproven.
- **FR-028**: Messages MUST follow established actionable German terminology/date conventions, distinguish provisional/saved and timeout/failure, and explain facts and next actions without developer tools.
- **FR-029**: Controls/evidence MUST be keyboard-accessible with visible focus, programmatic names/statuses, course associations, and current/generated relationships. Review follows I-004 focus behavior; progress MUST NOT repeatedly steal focus and terminal states MUST be announced. Meaning MUST NOT rely on color. At 320/820/1,280 CSS-pixel widths and 200% text zoom all evidence/actions MUST remain reachable and associated correctly.

### Test Requirements *(mandatory)*

This specification requests test-first delivery under the constitution. These requirements govern later implementation, not production work in this phase.

- **TR-001**: Create/update tests before practical automated production changes; record exceptions and manual verification in the plan.
- **TR-002**: Verify defaults/ceiling, invalid settings, no planner overrides, captured budgets, one allowance across stages, and computation beyond sixty seconds. Include a real elapsed-time acceptance run with documented conditions, not only simulated time.
- **TR-003**: Deterministically cover feasible-only timeout with/without bounds, no-candidate timeout, entirely empty unproven timeout results, non-empty candidates with zero scheduled units for individual courses, invalid assignments, earlier-stage retention, later-objective timeout, full coverage without preference proof, conditional proof, and fully proven branches. Verify arithmetic and evidence associations independently of unpredictable search timing.
- **TR-004**: Cover all FR-009 hard rules, changes to every relevant state category, ignored past exams, review invalidation, atomic failure, repeated acceptance, and no per-course mixing.
- **TR-005**: Cover cancellation, dismissal, navigation, late results, retry discard/back-out, context loss, commit races, and interrupted reconciliation. Compare saved state on all non-saving paths.
- **TR-006**: Verify matching running/result/acceptance facts across backend/frontend: candidate identity, budget, elapsed time, coverage, evidence, freshness, actual outcome. Document cross-stack contracts during planning without prescribing transport here.
- **TR-007**: Use project FastAPI-compatible tests, normally pytest in `backend/tests/`, and relevant React/TypeScript/Vite build/type/lint/component/UI checks in `client/`. Retain I-003/I-004, exam, manual-work, lifecycle, publication, and untouched-record regression coverage.
- **TR-008**: Manually verify keyboard/focus, assistive status, progress usability, narrow layouts, and 200% zoom where needed. Check five-second updates and one-second acknowledgement under documented connected conditions.
- **TR-009**: Exercise a representative larger 2027 S-style selection within twenty courses; record selection size, units, occupancy, installation conditions, configured/effective budget, duration, candidate/proof availability, and saved outcome. Do not infer a universal threshold or guaranteed completion.

### Key Entities

- **Budget Policy**: Operator-owned default/ceiling, shipped as 300/1,800 seconds, supplying each new operation's effective budget.
- **Optimization Operation**: Prepared selection, Working revision, fixed occupancy, captured time allowance, elapsed time, phase, cancellation intent, and saved/non-saving outcome.
- **Provisional Joint Candidate**: One hard-validated selected-course assignment with coverage/reasons for every course and no saved authority before acceptance.
- **Objective Evidence**: Priority, available value, proof status, trustworthy bound, and associated prepared problem/candidate.
- **Review/Freshness Context**: One indivisible comparison, input basis, decisions, and invalidation conditions; no new revision state or permanent decision log.

### Scope Boundaries and Relationships

- I-003 governs selection/preparation/hard rules/objective priorities/protected occupancy; I-004 governs comparison/indivisible acceptance; FS-013 governs editability/publication; FS-019 supplies Schedule placement. I-005 is not a dependency.
- For explicitly accepted hard-valid candidates only, this supersedes FS-010's all-stages-optimal-or-no-save baseline and I-003 FR-022/FR-029/FR-032 where they prohibit timeout/unproven saving. I-004 FR-027/FR-028, TR-003/TR-007, and SC-004/SC-007 no longer imply direct saving of unproven first plans or unconditional rejection of accepted timeout candidates. Protections remain before acceptance and for rejected/cancelled results. I-004's permission to accept lower coverage remains.
- Configured runs replace conflicting fixed time requirements in FS-010 FR-031/SC-008, I-003 SC-009/deadline verification, and I-004 SC-010. No thirty-/sixty-second result guarantee overrides the effective budget. Responsiveness and truthful status remain required.
- Priorities are unchanged. Fully proven deterministic behavior remains; unproven retries need not produce identical or improved candidates.
- No external integration. Deployment must support the budget; solver, parallelism, architecture, storage, and transport are later design choices.
- Excluded: invalid candidates, weaker constraints, unproven auto-save, guaranteed optimum/completion, increased course limit, guaranteed joint 94-course solve, automatic batching, moving unselected/protected sessions, genuine resume, planner budget overrides, publication changes, new approval roles, and mandatory decision comments/history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Shipped operations show 300 seconds and a controlled problem computes past sixty seconds. Changing default to 600 seconds affects the next operation without changing one already running.
- **SC-002**: All connected start/cancel actions are acknowledged within one second; elapsed/status updates are no more than five seconds apart; exhaustion and checking are distinguishable without developer tools.
- **SC-003**: Every feasible-only/later-objective timeout with a validated candidate scheduling at least one teaching unit across the selection yields review and zero saved changes before acceptance, including wholly unplanned selections.
- **SC-004**: Every accepted joint result saves once in full or not at all; accepted sessions satisfy every hard rule and change zero unselected/protected sessions or exams.
- **SC-005**: Every no-candidate, entirely empty unproven timeout, confirmed-cancellation, dismissed-review, pre-commit-failure, stale-rejection, or failed-application case changes zero saved records. Registered cancellation prevents late saves/reopened review.
- **SC-006**: All evidence cases distinguish coverage/preferences, selection/semester scope, and remaining units/possible improvement. The 80/100 candidate bounded by 90 shows 20 remaining and at most 10 additional; without evidence the gap is unknown.
- **SC-007**: All fully proven regression cases retain direct save for new selections and I-004 acceptance for existing selections, subject to validation/cancellation ordering.
- **SC-008**: At least four of five representative planners or reviewers, unaided within two minutes of review opening, identify saved/provisional state, distinguish validity/proof, explain one quality trade-off, and make their intended decision.
- **SC-009**: Every keyboard/defined-width/200%-zoom acceptance path preserves readable budget, coverage, uncertainty, course associations, and reachable cancel/accept/retry actions without lost focus.
- **SC-010**: A documented larger-selection run demonstrates the longer workflow and accurate actionable outcome within twenty courses; success is honest candidate/no-candidate handling and saved-state integrity, not a promised optimum or course-count threshold.

## Assumptions

### Preparation identity correction (2026-11-05)

Changing selected courses or unavailable-date input after preparation MUST discard
that preparation and require fresh preparation before starting. A late preparation
response for superseded inputs MUST NOT restore the start action. Starting MUST
use the current prepared selection and dates, including after clearing selection
or entering an invalid date; stale preparation must never dispatch an operation.

- Confirmed on 04.11.2026: five-minute default, thirty-minute initial ceiling, both operator-configurable, no planner override. Longer retry requires operator configuration.
- Confirmed on 04.11.2026: retry starts fresh and discards its old candidate; running cancellation and deliberate navigation away cancel while preserving saved work.
- Product defaults adopted here: five-second connected status updates, one-second acknowledgement under acceptance conditions, and no fixed review expiry during uninterrupted review. These specify behavior without selecting an execution mechanism.
- A valid incumbent is a produced, hard-validated assignment, never assumed to exist at timeout. Missing proof does not weaken validity. Required-unit arithmetic alone is not search evidence.
- Existing definitions remain: 45-minute units, saved constraints, active/past exams, fixed unselected occupancy, and remaining units. No external provider is needed.
- Cancellation may retain warned current work; validation never silently repairs it. Stale rejection preserves newer saved work that caused rejection.
- Execution/storage/transport are planning choices. This request authorizes specification artifacts and matching product-ground-truth updates only; implementation, plans, and tasks are separate phases.
