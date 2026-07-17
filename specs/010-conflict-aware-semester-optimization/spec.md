# Feature Specification: Conflict-Aware Semester Optimization

**Working Branch**: `codex/fs-010-semester-optimization`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Create FS-010 so a planner can optimize selected courses together for one semester, maximize scheduled teaching units without lecturer, room, or cohort overlaps, retain useful partial results, explain remaining units, and never silently worsen an existing plan."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-16

- Q: Should a fairness or minimum-allocation guardrail constrain total-unit maximization? → A: No. Maximize total scheduled units strictly; a course may receive zero units and must then show accurate remaining units and blocking reasons.
- Q: Which deterministic priorities apply after total scheduled units? → A: Prefer fewer conflicts in the resulting selected-course arrangement, then the applicable defined soft preferences, preservation of current schedules, and finally a stable deterministic tie-break; the preference tiers are refined below.
- Q: What workload and response target must the initial optimizer support? → A: Up to 20 selected courses, 600 requested teaching units, and 500 fixed semester sessions, with a 30-second target and 60-second maximum under documented reference conditions.
- Q: How should the previously unspecified teaching-time preference tier be handled? → A: Remove it. Allowed teaching windows remain hard constraints; after conflict reduction, compare lecturer continuity, room continuity, current-schedule preservation, and then the stable tie-break.
- Q: How are existing conflicts counted when equal-unit arrangements are compared? → A: Count each distinct conflicting session pair once per conflict type: lecturer, room, and cohort.
- Q: How are lecturer and room continuity compared across an arrangement? → A: Sum assignment changes between chronologically adjacent sessions within each individual course; minimize lecturer changes first, then room changes.
- Q: What happens to unaffected course results when another course or material input becomes stale? → A: Preserve the stale course and save only unaffected planned results that remain valid against the refreshed semester state; do not silently re-optimize.
- Q: How is current-schedule preservation measured in the final comparison tier? → A: Prefer the arrangement that leaves the greatest number of current course-semester Draft Schedules completely unchanged.
- Q: How is optimality described when stale input is detected after solving? → A: The proof applies to the unchanged prepared snapshot only. Exact unaffected results may still save after current-state validation, but the operation must not claim that the refreshed final semester state is globally optimal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate the Best Conflict-Free Semester Result (Priority: P1)

A planner selects courses for one semester and generates them as one coordinated planning problem so the saved result schedules the greatest permitted total number of teaching units without introducing known lecturer, room, or cohort overlaps.

**Why this priority**: Coordinated conflict avoidance and maximum scheduled coverage are the core value that distinguishes this slice from independent multi-course generation.

**Independent Test**: Prepare selected courses with competing time and resource choices, run generation, and verify that the saved selected-course result is conflict-free, respects every hard planning rule and fixed semester occupancy, and schedules the maximum total units required by the approved observable priorities.

**Acceptance Scenarios**:

1. **Given** selected courses can all be completed using eligible available resources without conflicting with one another or fixed semester sessions, **When** the planner confirms and starts generation, **Then** every selected course is saved complete and no generated session introduces a lecturer, room, or cohort overlap.
2. **Given** independently generating courses in request order would block a higher-coverage combination, **When** the same courses are generated together, **Then** the saved result uses the feasible combination with the greatest total scheduled units under the approved objective priorities.
3. **Given** a lecturer or room is ineligible, unavailable, below capacity, outside its active period, or already occupied by a fixed session, **When** candidates are evaluated, **Then** that resource is not assigned for the conflicting occurrence.
4. **Given** a selected course has multiple eligible lecturers or rooms, **When** more than one maximum-unit conflict-free result exists, **Then** the system applies the approved deterministic comparison priorities and reports the selected result consistently for the same unchanged inputs.
5. **Given** an unavailable-date input contains a date in the selected semester, **When** generation runs, **Then** no generated session is placed on that date; this slice does not create or administer the dates.

---

### User Story 2 - Keep and Understand a Useful Partial Plan (Priority: P2)

When all requested units cannot be placed, a planner receives the best permitted partial result, with scheduled and remaining units and understandable blocking reasons for each selected course.

**Why this priority**: Real semester constraints can make full completion impossible; retaining explainable progress lets planners act instead of losing all valid work.

**Independent Test**: Create an intentionally infeasible selected-course set, run generation, and verify that the greatest permitted conflict-free partial result is saved where it improves the current plan and that every incomplete course shows accurate remaining units and one or more relevant reasons.

**Acceptance Scenarios**:

1. **Given** no complete conflict-free result exists but at least one permitted improvement exists, **When** generation completes, **Then** the improving complete or partial course results are saved atomically per course, unchanged courses retain their prior data, and the operation summary distinguishes each outcome.
2. **Given** a selected course remains incomplete, **When** results are shown, **Then** its scheduled units, remaining units, completion state, and relevant blocking-reason categories are visible without requiring the planner to inspect another screen.
3. **Given** several constraints prevent a course's remaining units from being placed, **When** results are shown, **Then** the system presents all reason categories substantiated by the final planning attempt rather than an unsupported single cause or a claim that completion is impossible for one uniquely proven reason.
4. **Given** no new unit can be placed for a selected course and its current schedule cannot be improved under the approved comparison priorities, **When** generation completes, **Then** the course is reported as unchanged with its current schedule and accurate remaining-unit reasons; no empty replacement is stored.
5. **Given** a selected course has no current Draft Schedule and receives zero scheduled units, **When** generation completes, **Then** no empty Draft Schedule is created and the course is reported unchanged with all units remaining and understandable reasons.

---

### User Story 3 - Prevent Schedule Regression During Replacement (Priority: P3)

A planner can review and confirm the consequences of regenerating selected courses with existing drafts, knowing that an inferior or stale candidate will not overwrite current work.

**Why this priority**: Global generation is only safe to use on reviewed semester data when current coverage and concurrent changes are protected.

**Independent Test**: Run confirmed generation against selected courses with existing drafts, exercise worse, equal, better, cancelled, and stale outcomes, and verify that replacement occurs only when the candidate is allowed by the comparison priorities and current confirmation.

**Acceptance Scenarios**:

1. **Given** one or more selected courses have existing Draft Schedules, **When** generation is prepared, **Then** the planner sees which course-semester drafts and manual edits may be replaced and must explicitly confirm before the operation starts.
2. **Given** the planner cancels replacement confirmation, **When** the operation closes, **Then** no selected or unselected schedule, session, constraint, or planning input changes.
3. **Given** a candidate schedules fewer units for a course than that course's current draft, **When** results are compared, **Then** the current course draft remains unchanged even if the candidate has better preference compliance.
4. **Given** a candidate schedules the same units as a course's current draft, **When** it has no improvement under the approved comparison priorities, **Then** the current draft remains unchanged.
5. **Given** a same-unit candidate is strictly better under the approved comparison priorities, **When** the confirmed operation saves it, **Then** only that course's selected-semester draft is replaced and the improvement is identified in the result.
6. **Given** a replacement target, resource rule, availability input, saved generation constraint, or other material planning input changes after confirmation or after the operation starts, **When** saving would rely on the older state, **Then** every affected course is reported stale, its current data remains unchanged, and retry requires evaluation and confirmation against current state.

---

### User Story 4 - Review One Coordinated Operation (Priority: P4)

A planner receives one understandable summary that separates complete, improved partial, unchanged, failed, and stale course outcomes and reflects the saved semester state.

**Why this priority**: A global operation can produce different safe outcomes by course; an accurate summary is necessary for follow-up planning.

**Independent Test**: Run an operation constructed to produce every supported outcome and verify the summary, remaining units, reasons, saved schedules, and refreshed semester alerts against the final persisted state.

**Acceptance Scenarios**:

1. **Given** an operation produces mixed course outcomes, **When** it completes, **Then** each selected course appears exactly once as complete, improved partial, unchanged, failed, or stale, with scheduled and remaining units from the saved state.
2. **Given** valid results are saved, **When** the summary appears, **Then** the semester overview and validation alerts reflect the complete saved semester state without manual reload.
3. **Given** the operation cannot produce or save any valid improvement, **When** it ends, **Then** every existing schedule remains unchanged and the summary explains the unchanged, failed, or stale outcome for every selected course.
4. **Given** one or more inputs become stale after an optimal arrangement was proven, **When** exact unaffected results remain valid and are saved without re-optimization, **Then** the summary identifies that optimality was proven for the prepared snapshot and does not describe the refreshed final semester state as globally optimal.

### Edge Cases

- A selection contains one course. The coordinated workflow still applies the same conflict, comparison, explanation, and stale-data rules without requiring another selected course.
- The same lecturer, room, or cohort is needed by several selected courses at the same viable times. The result never double-books that resource and reports relevant remaining-unit reasons.
- A selected course has zero remaining units before generation. Its current coverage cannot be reduced and it is unchanged unless an allowed same-unit improvement is found and confirmed.
- Current scheduled units exceed current course units because source data changed. The current draft is treated as fully covered for non-worsening comparison, remaining units display zero, and generation does not silently delete the excess.
- A current selected-course schedule contains a known conflict. It remains the comparison baseline; a same-unit conflict reduction may qualify as an improvement, but no candidate may introduce a known conflict.
- Two overlapping sessions share the same lecturer, room, and cohort. Their relationship contributes three conflicts to arrangement comparison—one for each conflict type—even though each resulting alert may be visible from both sessions.
- Existing sessions outside the selected set, in another selected course's current alternative, or explicitly retained within a candidate consume their lecturer, room, cohort, and time occupancy during comparison.
- An unavailable or ineligible resource is the only resource associated with a course. The course remains incomplete or unchanged and receives relevant reasons.
- A resource becomes unavailable or another session is saved while generation is in progress. Affected results fail stale validation rather than overwriting current data.
- One course becomes stale while other planned course results remain valid against the refreshed semester state. The stale course is preserved, the still-valid unaffected results may save, and the system does not silently run a new optimization with changed inputs.
- A course has no eligible resource combination, no allowed date, or insufficient room capacity. Other selected courses may still improve, and the blocked course retains its current state.
- Two or more results remain equal after all user-visible comparison priorities. A stable final tie-break produces the same result for the same unchanged inputs.
- Two equal arrangements retain different portions of existing work. Current-schedule preservation counts complete course-semester Draft Schedules left unchanged, not individual sessions or the number of fields that remain similar.
- The unavailable-date input is empty. Generation proceeds with all other rules unchanged.
- An unavailable date is outside the selected semester or appears more than once. Outside-semester values have no scheduling effect, and duplicate values are canonically deduplicated rather than rejected or applied more than once.
- The planner submits duplicate course identifiers or a course outside the selected semester context. Invalid selection entries do not cause a partial unreviewed operation.
- A save fails after planning but before all affected course changes are committed. No course is left with a partially replaced Draft Schedule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a planner to initiate one conflict-aware generation operation for one semester and one or more distinct selected courses.
- **FR-002**: The system MUST evaluate the selected courses together rather than finalize them independently in selection or request order.
- **FR-003**: The primary objective MUST be to maximize the sum of scheduled teaching units across all selected courses, subject to hard rules, fixed occupancy, and non-worsening replacement. No per-course fairness or minimum-allocation guardrail may reduce that maximum; a course may receive zero units and MUST then show accurate remaining units and blocking reasons.
- **FR-004**: Every newly generated session MUST avoid known lecturer, room, and cohort time overlaps with every session retained in the candidate semester result and every fixed session outside the replaceable candidate scope.
- **FR-005**: Generation MUST enforce established semester boundaries, course date rules, course same-date rules, Study Type Time Windows, room capacity, resource eligibility, resource availability, active periods, and saved course-semester generation constraints as blocking rules where defined by their owning slices.
- **FR-006**: Existing Draft Sessions in unselected courses and semesters outside the replacement scope MUST remain unchanged and MUST act as fixed occupancy when relevant to the selected semester.
- **FR-007**: For each selected course with a current draft, the system MUST compare an alternative that retains the current draft with any regenerated alternative, so another course cannot gain units by silently worsening or discarding that current course.
- **FR-008**: A selected course's current sessions, including manual edits or creations, MUST be retained unless the planner explicitly confirms that successful regeneration may replace that course-semester draft and an allowed improvement is saved.
- **FR-009**: The system MUST consider all eligible lecturers and rooms that satisfy hard rules rather than relying only on a legacy single assignment or the first feasible resource.
- **FR-010**: After maximizing total scheduled units, the system MUST compare otherwise eligible results in this order: fewer conflicts in the resulting selected-course arrangement, greater lecturer continuity, greater same-room continuity, preservation of more current course schedules, and finally a stable deterministic tie-break. For conflict comparison, each distinct pair of overlapping sessions MUST count once for each shared conflict type—lecturer, room, and cohort—and MUST NOT be duplicated because the same alert is displayed on both sessions. Current-schedule preservation MUST count the number of current course-semester Draft Schedules retained completely unchanged; it MUST NOT use retained-session counts or field-level similarity. Allowed teaching windows remain hard constraints and are not a separate preference tier.
- **FR-011**: Preference compliance MUST NOT justify a result with fewer total scheduled units or replacement of a course by a candidate with fewer units.
- **FR-012**: Lecturer continuity MUST be measured as the total number of lecturer-assignment changes between chronologically adjacent sessions within each individual selected course and minimized across the arrangement. Same-room continuity MUST then be measured and minimized in the same way using room-assignment changes. Neither measure crosses course boundaries, and both preferences apply only after hard rules and higher approved comparison priorities are satisfied.
- **FR-013**: The same unchanged inputs MUST produce the same selected result and course outcome classifications.
- **FR-014**: The generation boundary MUST accept zero or more unavailable dates and MUST prevent new sessions on those dates without requiring this feature to create, name, edit, or delete holiday records.
- **FR-015**: When a complete selected-course plan is impossible, the system MUST retain the permitted result with the greatest scheduled coverage under the approved priorities rather than discard all valid partial work.
- **FR-016**: For every selected course, the system MUST calculate scheduled units from its saved Draft Sessions and remaining units as current course units minus scheduled units, displayed with a minimum of zero.
- **FR-017**: An incomplete course MUST receive one or more understandable blocking-reason categories supported by constraints encountered while seeking additional placements; explanations MUST distinguish applicable categories such as occupied resources, resource unavailability, no eligible resource, insufficient room capacity, date or time-window limits, course constraints, and stale or invalid planning data.
- **FR-018**: Blocking reasons MUST be presented as evidence about why units remain, not as a claim that one displayed reason is the unique mathematical cause unless that conclusion is established by the accepted result.
- **FR-019**: A zero-placement course with no allowed improvement MUST be represented as unchanged; the system MUST NOT create an empty Draft Schedule or store an empty replacement.
- **FR-020**: The system MUST NOT replace a course's existing Draft Schedule with a candidate containing fewer scheduled units.
- **FR-021**: The system MUST replace an equal-unit current draft only when the candidate is strictly better under the approved comparison priorities; otherwise it MUST retain the current draft unchanged.
- **FR-022**: Before an operation that may replace any existing selected-semester Draft Schedule, the system MUST identify every replacement target, state that its generated and manually adjusted sessions may be replaced, and require explicit confirmation covering the complete operation.
- **FR-023**: Cancelling replacement confirmation MUST leave all schedules, sessions, saved constraints, resource data, and other planning records unchanged.
- **FR-024**: The system MUST validate at save time that every material input used for each course result remains current, including replacement targets, semester sessions affecting occupancy, selected-course data, saved constraints, resource eligibility, availability, capacity, active periods, and unavailable dates.
- **FR-025**: When stale data affects a course result, the system MUST preserve that course's current draft and constraints, classify it as stale, and require a new operation and confirmation against refreshed state before replacement.
- **FR-026**: A stale or failed course MUST NOT prevent planned results for unaffected selected courses from being saved when those exact results remain valid against the refreshed complete semester state. The system MUST NOT silently re-optimize unaffected courses using changed inputs within the same operation; any result that no longer remains valid MUST also be preserved and reported stale or failed as applicable.
- **FR-027**: Each course save MUST be all-or-nothing: the system MUST NOT retain a partially created or partially replaced Draft Schedule for a failed or stale course.
- **FR-028**: The operation summary MUST classify every selected course exactly once as complete, improved partial, unchanged, failed, or stale and MUST show its saved scheduled units, remaining units, applicable reasons, and optimization proof scope. When stale input is detected after solving, the summary MAY state that the prepared snapshot was proven optimal but MUST NOT claim that the refreshed final semester state is globally optimal.
- **FR-029**: After saving, the semester overview and validation alerts MUST refresh from the complete saved semester state without requiring a manual reload.
- **FR-030**: The feature MUST preserve schedules in other semesters and source academic/resource records. Existing saved custom generation constraints MUST remain unchanged. When a successfully generated course had no saved constraint set, the system MUST preserve the established generation behavior by saving the exact active default constraints used for that result; failed, stale, unchanged, or cancelled outcomes MUST NOT create or modify a constraint set.
- **FR-031**: Under documented reference conditions, the system MUST support conflict-aware generation for up to 20 selected courses, 600 requested teaching units, and 500 fixed semester sessions; at least 95% of operations MUST show a complete saved-state result or actionable failure within 30 seconds, and every operation MUST do so within 60 seconds.
- **FR-032**: The feature MUST NOT create or administer public holidays, generate exams, automatically move or delete unselected or unconfirmed existing sessions, guarantee optimality beyond the approved measurable objective and supported workload, or expose an algorithm choice to the planner.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each implemented user story where automated testing is practical.
- **TR-002**: Automated coverage MUST verify maximum-unit selection on bounded reference cases with independently established expected results, including cases where request-order generation is inferior.
- **TR-003**: Automated coverage MUST verify lecturer, room, and cohort conflict avoidance; eligibility; availability; active periods; capacity; semester/date limits; time windows; saved constraints; fixed occupancy; and unavailable-date inputs.
- **TR-004**: Automated coverage MUST verify complete, improved partial, unchanged, failed, stale, zero-placement, cancelled, worse-candidate, equal-candidate, and strictly better equal-unit outcomes.
- **TR-005**: Automated coverage MUST verify deterministic results for repeated unchanged inputs and every approved comparison priority.
- **TR-006**: Automated coverage MUST verify stale detection for every material input category, unaffected-course continuation, per-course all-or-nothing saves, and cross-course/cross-semester preservation.
- **TR-007**: Automated coverage MUST verify remaining-unit calculations, substantiated blocking-reason categories, operation summaries, and post-save overview and alert refreshes.
- **TR-008**: Automated coverage MUST verify the approved workload and planner-visible completion target under documented reference conditions.
- **TR-009**: Existing single-course generation, independent multi-course generation where still exposed, manual editing and creation/deletion, semester review, resource administration, and validation-alert acceptance behavior MUST remain verified.
- **TR-010**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Conflict-Aware Generation Operation**: One planner-confirmed attempt for a selected semester and distinct course set, including the input snapshot, replacement scope, outcome summary, and unavailable-date input.
- **Planning Input Snapshot**: The versions or equivalent current-state evidence for selected courses, current semester sessions, saved constraints, eligible resources, availability, capacity, active periods, and unavailable dates used to evaluate and safely save results.
- **Course Candidate Result**: A complete, partial, retained-current, failed, or stale alternative for one selected course, including sessions, assigned resources, scheduled units, remaining units, preference measures, and reasons.
- **Fixed Semester Occupancy**: Existing sessions that a candidate does not have confirmed authority to replace, including unselected-course sessions and any current session retained by a selected-course alternative.
- **Operation Summary**: The saved-state account of every selected course's classification, scheduled units, remaining units, improvements, and blocking or failure reasons.
- **Blocking Reason**: A substantiated category describing a constraint encountered while attempting to place a course's remaining units without asserting unsupported uniqueness.
- **Unavailable Date Input**: A set of dates on which this operation may not create sessions; administration and holiday meaning are outside this slice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of bounded acceptance cases whose prepared inputs remain unchanged through save, the saved result schedules the independently established best permitted total and introduces no new lecturer, room, or cohort overlap; pre-existing conflicts in a retained unchanged draft do not count as newly introduced overlaps.
- **SC-002**: In 100% of tested infeasible cases, every saved session satisfies all hard rules, every selected course reports accurate scheduled and remaining units, and every incomplete course reports at least one substantiated reason category.
- **SC-003**: In 100% of tested replacement cases, no course is saved with fewer scheduled units than its current draft, and equal-unit replacement occurs only when the candidate is strictly better under the approved comparison priorities.
- **SC-004**: In 100% of cancelled, failed, stale, and non-improving course outcomes, protected current schedules and planning data remain unchanged.
- **SC-005**: Repeating any documented reference case at least 20 times with unchanged inputs produces the same sessions, resource assignments, and course classifications every time.
- **SC-006**: In an unaided usability review with at least 10 representative planners or acceptance reviewers familiar with the existing planner, at least 90% can identify which courses completed, which remain partial or unchanged, and one reason for each incomplete course within two minutes of seeing the operation summary.
- **SC-007**: In the same usability-review protocol, 100% of participants can identify that confirmed existing drafts may be replaced before starting the operation, and at least 90% can distinguish an improved partial result from an unchanged result afterward.
- **SC-008**: Under documented reference conditions with up to 20 selected courses, 600 requested teaching units, and 500 fixed semester sessions, at least 95% of conflict-aware generation operations show a complete saved-state result or actionable failure within 30 seconds, and 100% do so within 60 seconds.
- **SC-009**: In 100% of tested post-save cases, the visible semester overview, remaining units, and validation alerts match the complete saved semester state without a manual reload.
- **SC-010**: All applicable acceptance scenarios from FS-008 resource eligibility/availability and FS-009 manual session management, plus existing generation, review, editing, and alert workflows, continue to pass after this feature is delivered.

## Assumptions

- The planner already has access to the established planning workflow; this slice adds no authentication, role, or permission behavior.
- FS-008 supplies authoritative eligible-resource, availability, capacity, and active-period data. FS-009 supplies remaining-unit behavior and manual-session source records.
- Current selected-course drafts are candidate baselines: the optimizer may evaluate confirmed replacements, but an alternative retaining each current draft remains available so another course cannot gain units through silent regression.
- Maximizing total scheduled units takes precedence over balancing allocation across selected courses. No course is guaranteed a minimum allocation in this slice.
- The observable comparison order after total units is conflict reduction, lecturer continuity, same-room continuity, preservation of current schedules, and a stable final tie-break. Allowed teaching windows are hard constraints rather than soft teaching-time preferences.
- Lecturer and room continuity are course-local transition measures aggregated across the selected arrangement: chronologically order each course's sessions, count changes between adjacent assignments, sum those changes across courses, minimize lecturer changes first, and then minimize room changes.
- Current-schedule preservation is measured only by the number of complete current course-semester Draft Schedules retained unchanged, not by individual retained sessions or field-level similarity.
- Existing manual sessions are not moved or deleted individually. They change only as part of an explicitly confirmed replacement of their complete course-semester Draft Schedule that also satisfies the non-worsening rules.
- Known conflicts in current data do not authorize new conflicts. Conflict reduction can distinguish equal-unit results only according to the approved comparison priorities.
- Zero newly placed units is an unchanged outcome, not a stored partial plan or empty schedule.
- Blocking reasons describe constraints encountered during the accepted planning attempt and need not constitute a formal proof that no other arrangement exists beyond the approved objective and supported workload.
- An `OPTIMAL` solver result proves the arrangement for the prepared input snapshot. If later stale input prevents some course results from saving, exact unaffected results may still save after revalidation, but no global-optimality claim is made for the refreshed final semester state.
- Unavailable dates are supplied to the scheduling boundary by callers. FS-011 will add holiday administration without changing the observable optimization contract.
- Public-holiday data, exam scheduling, bulk deletion, automatic repair of unselected schedules, and planner-selectable algorithms remain out of scope.
