# Feature Specification: Dated Windows, Copying and Intensive-Week Scheduling

**Working Branch**: `master`

**Created**: 2026-11-06

**Status**: Draft — validated for planning

**Slice ID**: I-009

**Input**: User description: "Specify I-009 from docs/planning/Feature_slices.md: administer date-specific additional teaching windows for exactly one Studienform, copy independent editable windows, and prioritize total teaching LE, marked-intensive LE, then daily LV variety without weakening constraints or saved-work protection. Specification only."

**Product source**: [I-009 in Feature_slices.md](../../docs/planning/Feature_slices.md#i-009-dated-windows-copying-and-intensive-week-scheduling). LV means one course; LE means the existing teaching-unit measure. The numbered artifact directory does not change the product slice identifier I-009.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open One Specific Teaching Date (Priority: P1)

A planner whose Berufsbegleitend Studienform normally permits Friday/Saturday teaching adds a specific Monday without opening other Mondays. Weekly and dated opportunities remain distinguishable and independently maintainable in Stammdaten > Zeitfenster.

**Why this priority**: Concrete extra dates enable intensive teaching without changing the ordinary semester pattern.

**Independent Test**: With otherwise eligible courses, add a Monday within their planning period, generate teaching on that date, and inspect adjacent Mondays and another Studienform. Edit and remove an unused entry and reload administration.

**Acceptance Scenarios**:

1. **Given** Friday/Saturday weekly windows, **When** a planner saves a dated Monday with one Studienform and valid hours, **Then** the dated record persists, the weekly records remain unchanged, and only that exact additional date becomes permitted for that form.
2. **Given** a dated window, **When** the list and editor are opened, **Then** kind, full date including year, hours, Studienform and Intensivwoche state are identifiable, and dated entries cannot be mistaken for weekly recurrence.
3. **Given** a dated Monday, **When** another Monday, the same month/day next year, or a course using a different Studienform is evaluated, **Then** this record grants no opportunity there.
4. **Given** six individually saved Monday-through-Saturday dated windows, **When** the planner generates eligible teaching, **Then** all six dates are available independently, without requiring a session on each date or creating a week entity.
5. **Given** a window missing its Studienform, valid date/weekday or hours, an impossible date, an end no later than its start, or a same-form exact duplicate, **When** save is attempted, **Then** it is rejected with field-specific German feedback, entered values remain editable, and saved records are unchanged.
6. **Given** identical dates/hours for two different Studienformen, **When** each is saved, **Then** both independent records are accepted; partially overlapping entries for one form are also accepted with informative overlap feedback.
7. **Given** a saved window, **When** a valid edit or confirmed permitted deletion succeeds, **Then** only that record changes; cancelling deletion, a protected deletion, or a stale edit changes nothing and explains any blocker or required refresh.

---

### User Story 2 - Generate Teaching That Uses Intensive Opportunities (Priority: P1)

A planner marks selected dated windows Intensivwoche and generates through the existing workflow. Generation prefers intensive teaching and varied cohort days without sacrificing teaching coverage or validity.

**Why this priority**: Merely permitting the dates does not ensure the intensive opportunities are used ahead of ordinary placement preferences.

**Independent Test**: Use small arrangements whose feasible alternatives can be independently compared. Verify total LE first, intensive LE second, the defined daily-variety score third, and unchanged lower preferences thereafter. Exercise one-LV fallback and more than one teaching day for an LV in a week.

**Acceptance Scenarios**:

1. **Given** otherwise valid alternatives with total/intensive LE of 12/4 and 10/10, **When** generation completes with the priority order proven, **Then** it chooses 12/4 because total teaching coverage ranks first.
2. **Given** alternatives with equal total LE of 12 and intensive LE of 4 versus 8, **When** compared, **Then** 8 intensive LE is preferred even if the other arrangement better meets once-per-week, midpoint-size, weekly-concentration or continuity preferences.
3. **Given** equal total and intensive LE for one cohort across two intensive dates, with A alone on Monday and B alone on Tuesday versus A and B on each date, **When** compared, **Then** the mixed arrangement scores 2 instead of 0 and is preferred, even though each LV meets more than once that week.
4. **Given** equal total and intensive LE, **When** an additional LV belongs only to an unrelated cohort, **Then** it does not raise the first cohort's daily-variety score.
5. **Given** only one LV can validly occupy an intensive day at the best higher-priority coverage, **When** generation finishes, **Then** the single-LV day remains valid and usable; no LE is discarded or hard rule relaxed to obtain a mix.
6. **Given** a variety improvement would lower total LE or intensive LE, **When** alternatives are compared, **Then** the higher-coverage arrangement is preferred even if it has single-LV days.
7. **Given** equal total LE, intensive LE and variety score, **When** alternatives are compared, **Then** the existing lower-priority preferences resolve the tie in their established relative order, followed by the existing stable tie-break; no extra preference for a particular intensive date is introduced.
8. **Given** no applicable intensive markers, including markers only for another form or dates outside the selected planning periods, **When** unchanged inputs are generated, **Then** the existing preference order and deterministic result are retained.
9. **Given** a wider ordinary window overlapping marked dated windows, **When** intensive LE and daily variety are evaluated, **Then** only actual teaching time inside the applicable marked union contributes, each minute counts once, breaks count zero, and source-window selection cannot change the score.
10. **Given** an LV taught partly in intensive windows and partly elsewhere, **When** coverage is evaluated, **Then** all its permitted teaching counts toward total LE and only its intensive portion counts toward intensive LE; complete placement of the LV in that week is unnecessary.

---

### User Story 3 - Keep Generation, Alerts and Saved Work Consistent (Priority: P1)

A planner changes windows and sees refreshed current draft validation without sessions being silently changed. Any later regeneration and replacement still follows the established review, freshness and publication rules.

**Why this priority**: Extra dates must not create conflicting generation/validation answers or compromise deliberately saved work.

**Independent Test**: Keep a saved Monday session outside the weekly windows. Add, shorten, unmark and remove its dated opportunity while checking current Calendar/List/detail alerts and saved session facts. Prepare a generation candidate, then change relevant window values before acceptance.

**Acceptance Scenarios**:

1. **Given** an otherwise valid Monday session outside ordinary weekly hours, **When** an applicable dated window covering its complete interval is saved, **Then** the current window alert disappears after refresh, other alerts remain, and session facts do not change.
2. **Given** that saved session and no other covering window, **When** its dated opportunity is shortened, removed where deletion is permitted, or made unavailable through existing lifecycle controls, **Then** the current draft receives a window alert without the session being moved or deleted.
3. **Given** a dated opportunity on a holiday or conflicting with an active exam, course restriction or unavailable resource, **When** generation is attempted, **Then** the dated opportunity does not override that rule and no invalid candidate is offered.
4. **Given** a dated window is the only opportunity capable of hosting a course's minimum session within its active period, **When** planning choices and generation are evaluated, **Then** the course is not excluded merely because no weekly window qualifies; if no applicable usable window exists, actionable unavailability remains.
5. **Given** preparation or a provisional candidate used a dated window, **When** its date, form, hours, active state or intensive marker changes before submission/save/acceptance, **Then** that prepared result becomes stale, saves nothing, and directs the planner to generate from current state, even if only a preference changed.
6. **Given** a provisional replacement for existing selected sessions, **When** the planner cancels, leaves review, or acceptance fails, **Then** all saved selected sessions, manual edits, unselected teaching and exams remain unchanged; successful explicit acceptance replaces the entire selected result atomically and at most once.
7. **Given** a published or historical revision, **When** source windows change, **Then** its saved facts, publication and historical evidence remain immutable; refreshed current draft findings are not written into that revision.
8. **Given** an otherwise saveable manual session outside the applicable windows, **When** it is explicitly saved, **Then** existing warning severity and manual-save behavior remain in force; a preference for more intensive teaching or variety never becomes a validity warning.
9. **Given** window save succeeds but current validation cannot be refreshed, **When** the affected schedule is shown, **Then** it indicates unavailable/outdated validation with retry guidance rather than presenting stale alerts as current; no session mutation occurs.
10. **Given** a course or semester selection changes and its generation constraints cannot be loaded, **When** the focused editor is shown, **Then** constraints from the former selection cannot be saved or reset against the new selection, validation reports the failure with retry guidance, and successful retry loads the selected course/semester's own constraints.
11. **Given** the focused course is unavailable or belongs to another semester, **When** the current semester workspace has refreshed, **Then** other eligible courses remain selectable and can be generated without requiring a constraint request for the unavailable focused course.
12. **Given** unsaved date edits for the same course/semester and a failed catalog-context refresh, **When** the editor remains open, **Then** entered dates remain visible but save/reset are disabled until that same selection's constraints refresh successfully.
13. **Given** saved date limits exclude the only usable teaching opportunity, **When** the planner inspects, broadens or resets those limits, **Then** those recovery actions remain available with the existing revision and lifecycle guards; generation remains unavailable until usable opportunities exist, and other eligible courses remain independently generatable.
14. **Given** intensive optimization produces subminute session boundaries, **When** draft/calendar facts are read and a session is edited without changing its times, **Then** its exact timestamps, instructional intersections and conflict status are preserved; changing LE preserves the start's fractional precision when deriving the end.

---

### User Story 4 - Reuse Values Through Independent Copies (Priority: P2)

A planner uses Kopieren beside an existing weekly or dated window, adjusts an unsaved new entry, and explicitly saves one independent record. Repeating the action avoids retyping unchanged values for other dates or Studienformen.

**Why this priority**: Copying reduces repetitive administration while preserving the chosen single-form, independent-record model.

**Independent Test**: Copy a weekly record and a marked dated record. Inspect prefilled values, change the target form/date/hours and marker, cancel one copy, save another, then edit/delete source and copy separately.

**Acceptance Scenarios**:

1. **Given** a weekly source, **When** Kopieren is chosen, **Then** a clearly identified unsaved new weekly entry opens with the same weekday, hours and Studienform, and no record or session is yet created.
2. **Given** a marked dated source, **When** Kopieren is chosen, **Then** date, hours, Studienform and intensive state are prefilled in an unsaved dated entry; each value can be changed independently before save.
3. **Given** a copy editor, **When** the planner chooses another form or date/weekday and explicitly saves valid values, **Then** exactly one new independent record is created, its kind matches the source, the source is unchanged, and no session, course, cohort or resource assignment is copied.
4. **Given** a copy with unchanged identifying values for the same form, **When** save is attempted, **Then** duplicate feedback identifies the conflict, retains the unsaved entry and permits correction or cancellation; changing only the intensive marker does not bypass duplicate detection.
5. **Given** any unsaved creation/copy, **When** it is cancelled or dismissed, **Then** no window or other planning record is created or changed, and focus returns to the originating action or a logical list location.
6. **Given** a saved source and copy, **When** either is edited or permissibly deleted, **Then** the other record's values and identity remain unchanged; neither is protected merely because the other was copied from it.
7. **Given** the source was changed or deleted after opening a copy editor, **When** the unsaved values are saved, **Then** they are treated as a new entry and validated against current form availability and duplicates; no late source synchronization occurs.

---

### User Story 5 - Understand and Operate the Controls Accessibly (Priority: P2)

A planner can distinguish weekly/dated opportunities, explicitly mark intensive windows, correct errors and understand generation outcomes using the existing German interface, keyboard and assistive technology.

**Why this priority**: The added date and marker must be understandable and usable through the same administration and review workflows.

**Independent Test**: Complete create/copy/edit/cancel with keyboard only and an assistive-technology review. Inspect German dates, list ordering, overlap/error feedback, result facts and proof labels where supported at narrow width and enlarged text.

**Acceptance Scenarios**:

1. **Given** the window list, **When** it is opened, **Then** the labeled weekly group precedes the dated group, weekly entries are ordered Monday-to-Sunday then by start/end, dated entries by ascending full date then start/end, and Studienform and existing stable ordering break remaining ties.
2. **Given** a new dated entry, **When** it opens, **Then** Intensivwoche defaults off; toggling it applies only to that record, and neither its whole week nor another form is implicitly marked.
3. **Given** keyboard or assistive-technology use, **When** create, edit, copy, delete, marker or save/cancel controls are used, **Then** labels, states, error associations, visible focus and outcome announcements expose the same facts available visually; no required action relies on color or pointer input alone.
4. **Given** an editor opens, **When** focus is placed, **Then** creation starts at the kind choice, copying starts at the Studienform field, and edit starts at the first editable field; an invalid save takes focus to the first invalid field and exposes all detected errors without discarding values.
5. **Given** a generation result or existing comparison involving applicable intensive windows, **When** it is reviewed, **Then** total LE, intensive LE and per-cohort/date distinct-LV counts explain the preference outcome without implying that a single-LV day is invalid or that marking guarantees placement.
6. **Given** the installed generation workflow supports objective proof status, **When** intensive-use and variety evidence is shown, **Then** each objective appears in its correct priority with its actual proven, unproven, not-attempted or conditional status; lower-stage proof is not represented as full-priority proof when an earlier stage remains unproven.
7. **Given** a 320-pixel-wide presentation or 200% text enlargement, **When** administration and the affected result facts are used, **Then** field associations, dates, marker states, errors and required actions remain readable and reachable without clipping or lost information.

### Edge Cases

- A leap-day date is valid only in its stated year. Impossible dates, missing years, midnight-spanning intervals and zero/negative durations are rejected; no implicit next day is inferred.
- A valid date lies outside all current semesters or in the past. It can be maintained as catalog data but grants no opportunity outside a course's active semester/period and triggers no retroactive session change.
- Sunday is not implicitly added by a Monday-through-Saturday intensive setup. An explicitly entered Sunday follows the same dated rules and inherited restrictions; no new weekday ban is introduced.
- Multiple partially overlapping marked windows, a contained marked window, adjacent windows and weekly/dated overlap do not multiply capacity or LE. Exact endpoint contact has zero overlapping duration.
- A session fits no single applicable window although several adjacent/overlapping windows together cover it. It remains outside the permitted session windows; this slice does not introduce stitching of separate records into a longer session opportunity.
- A weekly-covered session crosses an intensive boundary during teaching or during a break. Only marked instructional minutes count, not the whole session or break duration.
- The same form/date/hours is submitted twice with different marker values. It is an exact duplicate; the existing record's marker must be edited instead.
- The only suitable dated window is for another form, outside the course period, inactive, on a holiday, too short for the minimum session including breaks, or excluded by a narrower explicit course restriction. No valid candidate is manufactured.
- Several LVs for one cohort versus several unrelated cohorts occur on a date. Variety is per cohort/date, never a date-wide pool. Multiple windows for the same cohort/date do not count the same LV twice.
- One LV appears on several intensive dates. This is permitted despite the lower once-per-week preference, but at most one session of that LV per date and all hard session sizes remain binding.
- A fixed unselected teaching session already contributes to a cohort's intensive-day mix. Its qualifying LV may contribute to that day's variety, but it remains fixed occupancy and cannot be moved to improve the score.
- An intensive marker is removed without changing hours. Permitted teaching and window validity are unchanged; preference evidence/prepared results must refresh.
- A required form is archived while a new/copy editor is open, two planners submit the same new entry, or a record changes before edit/delete. Current validation prevents unavailable selections, duplicates and stale overwrite with no partial save.
- No feasible placement, incomplete coverage, no proven result, failed refresh and interrupted acceptance use established recovery and preservation paths. An empty intensive day is not itself a constraint violation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Stammdaten > Zeitfenster MUST support create, view, edit and request-delete for dated windows alongside existing weekly windows. A saved dated window MUST contain one full calendar date including year, start/end hours, exactly one Studienform and an explicit Intensivwoche state.
- **FR-002**: Dated windows MUST add teaching permission only on their recorded date for courses using that Studienform through existing course/cohort relationships. They MUST NOT recur by weekday, week or year or change recurring weekly windows.
- **FR-003**: Existing weekly records MUST retain their identity, recurrence, hours and single-form mapping. Existing data MUST remain usable without planner re-entry. Weekly records MUST NOT acquire an intensive marker or become dated through copying.
- **FR-004**: Create/edit/copy-save MUST reject missing or unavailable required relationships, invalid full dates or weekdays, missing hours, and end times no later than start on the same day. Errors MUST identify all detected corrections in German and retain entered values. Dates MUST use European day-month-year presentation/entry and times the existing 24-hour convention.
- **FR-005**: Exact duplicates MUST be rejected within the same form and kind: weekday/start/end for weekly, full date/start/end for dated, ignoring the dated intensive marker. Existing inactive entries participate in duplicate checks under catalog conventions. Identical values for different forms or different kinds MUST be allowed. Partial overlaps MUST be allowed with an informative message that overlap creates no extra capacity.
- **FR-006**: Weekly and dated entries MUST be clearly labeled and grouped, displaying their applicable weekday/date, hours and Studienform; dated entries MUST display marker state in both list and editor without relying on color. Ordering MUST follow Story 5 scenario 1 and MUST NOT itself confer scheduling priority.
- **FR-007**: New dated entries MUST default Intensivwoche to off. Changing it MUST affect only that record. Weekly and unmarked dated windows MUST remain ordinary opportunities, including those in the same week or on the same date as a marked record.
- **FR-008**: Kopieren MUST be available with each existing window's actions and open an explicitly unsaved new entry retaining the source kind and prefilling its scheduling values and Studienform; dated copies MUST also prefill the marker. The target form, applicable date/weekday, hours and dated marker MUST be editable before explicit save.
- **FR-009**: Opening/editing a copy MUST create no saved record. Successful explicit save MUST create exactly one independent record; cancel/dismiss MUST change nothing. Copies MUST contain window values only and MUST neither copy planning records nor retain a maintenance/synchronization relationship to their source.
- **FR-010**: Source and copy MUST be independently editable/deletable under the same current validation and protection rules. Source changes after copy-editor opening MUST NOT update unsaved values. Saving those values MUST validate them as a new record against current relationships and uniqueness.
- **FR-011**: Deletion MUST require explicit confirmation and preserve existing dependent-record/saved-reference protections. A protected deletion MUST identify blocker types/counts and the existing prerequisite or inactive alternative where applicable. Source/copy ancestry alone MUST NOT be a blocker; no deletion may cascade into sessions or other window records.
- **FR-012**: Existing inactive/reactivation behavior MUST apply consistently to dated windows and their required relationships. Concurrent edit/delete and conflicting create requests MUST NOT overwrite newer state or save a duplicate; failures MUST retain recoverable input and give actionable refresh/correction guidance.
- **FR-013**: Teaching generation and current window validation MUST consider applicable active weekly and dated windows using the same date/form/hours rules. A course with a usable dated-only opportunity within its active period MUST NOT be unavailable merely for lacking a weekly opportunity. No usable opportunity MUST retain a precise unavailable/window reason rather than an invented default.
- **FR-014**: A generated session's complete interval, including required breaks, MUST fit at least one applicable permitted weekly or dated window and satisfy any narrower explicit active course restriction. Separate records MUST NOT be stitched into a longer session window. Overlap grants no extra room, lecturer or cohort capacity; exact-boundary adjacency remains non-overlap.
- **FR-015**: All existing hard semester/course periods, holidays/unavailable dates, resource activity/eligibility/availability, capacity, selected-course limits, fixed unselected teaching and active-exam occupancy, same-course exam boundaries, teaching-unit/session-size/break rules and lecturer/room/cohort non-overlap MUST remain binding. A marked opportunity MUST NOT relax them, raise course limits or change exam-window policy. At most one session per LV/date remains a hard rule.
- **FR-016**: Windows MUST permit rather than require teaching. Saving, copying, marking, editing, archiving or deleting them MUST NOT generate, move, replace, delete or rescale any saved session, including manual sessions; unfilled dates MUST NOT produce a missing-session violation.
- **FR-017**: Generation MUST compare permitted alternatives in this strict order: maximize total selected-course teaching LE; maximize selected-course teaching LE in applicable marked dated windows; maximize the daily-variety score in FR-020; then apply the existing lower-priority preferences in their current relative order. No weighted trade-off may sacrifice an earlier objective for a later one.
- **FR-018**: Intensive LE MUST measure instructional time only. For each selected teaching session, intersect its actual teaching intervals with the union of active marked dated intervals applicable to its form/date, count each instructional minute once, and divide by the existing duration of one LE. Exclude breaks, ordinary-only teaching and endpoint-only contact. Keep exact proportional LE for partial boundary overlaps without rounding up to whole sessions/LE. Scheduled session-unit requirements remain unchanged; this accounting does not authorize fractional-unit sessions.
- **FR-019**: Intensive scoring MUST depend on the actual date/time/form intersection, not which source window is associated with the session. Two marked windows covering the same teaching time or a marked window overlapping a weekly/unmarked one MUST NOT double-count total or intensive LE. An LV MAY earn intensive LE for only part of its teaching and need not be completed inside the intensive week.
- **FR-020**: For each cohort/calendar date, let K be the number of distinct LVs with positive instructional time in an applicable marked window on that date in the resulting arrangement. The daily-variety contribution MUST be max(0, K - 1); the objective MUST maximize the sum across cohort/date pairs. Count a given LV once per pair regardless of windows/LE and include qualifying fixed teaching for that same cohort without changing it. Exams, breaks and unrelated cohorts contribute nothing to that pair. No date, form or cohort receives an additional weight.
- **FR-021**: Zero/one-LV days MUST remain valid and contribute zero variety points. Higher variety MUST NOT reduce total LE or intensive LE. At equal three leading objective values, existing once-per-week, session-size-midpoint, weekly-concentration and resource-continuity preferences MUST retain their existing relative order and stable final tie-break, without an additional intensive-date distribution tie-break. With no applicable markers, the existing preference order and outcomes MUST remain unchanged.
- **FR-022**: Multiple teaching dates for an LV in one Monday-based week MUST be eligible when intensive use or daily variety prefers them at equal higher-priority values; the lower once-per-week preference MUST NOT defeat that outcome. Hard session-size and at-most-one-session-per-LV/date rules MUST still apply.
- **FR-023**: Successful window changes MUST refresh affected current planning inputs, course availability, derived-window displays and current draft alerts on Calendar, List and session detail without changing filters, unrelated selections, entered editor values or sessions. Already open affected views MUST refresh within two seconds under the acceptance conditions in SC-008; revisited views MUST obtain current context before presenting it as current.
- **FR-024**: If refresh fails, affected validation MUST be labeled unavailable/outdated with retry guidance; stale findings MUST NOT appear as authoritative current validity. Refresh MUST remove resolved window alerts and retain other applicable alerts with their correct session association. A marker-only edit MUST NOT introduce a window violation.
- **FR-025**: Relevant changes to window kind/date/weekday, hours, form, active availability or marker MUST invalidate prepared generation and provisional comparison evidence that used that context, including otherwise valid candidates after marker-only changes. Submission, direct save and acceptance MUST apply existing freshness checks; stale results MUST change no saved planning state and require fresh generation.
- **FR-026**: Generation MUST remain the existing unified one-to-twenty-course workflow for the active editable Working revision. I-004's explicit operation-wide comparison/acceptance for existing selected sessions, atomic at-most-once replacement, permitted conscious acceptance of lower coverage, cancellation and failure preservation MUST remain intact. Existing first-plan direct-save rules MUST remain; no new acceptance bypass is introduced.
- **FR-027**: Current manual-save warning severity MUST remain unchanged: otherwise valid explicit manual placement may retain a window warning under existing rules, while generated candidates MUST satisfy hard rules. Intensive use and variety MUST NOT become hard validation or publication conditions. Published revisions and historical schedule facts MUST remain immutable after source changes.
- **FR-028**: Where applicable intensive windows exist, existing generation result/comparison surfaces MUST identify total LE, intensive LE and the summed variety value with per-cohort/date distinct-LV counts, associated with the actual saved or provisional arrangement. Existing current/generated comparison MUST identify each side separately. Explain the priority and allowed single-LV fallback in German without guaranteeing that every marked date is used. No separate dashboard is required.
- **FR-029**: Where the installed workflow exposes objective proof/evidence, intensive LE and variety MUST be included in the proper priority order with truthful values and proven, unproven/unfinished, not-attempted or conditional status. Proof applies only to the same prepared selected problem and fixed occupancy. Complete coverage or a single-LV day MUST NOT imply preference optimality or invalidity. Missing proof MUST NOT be invented; existing unproven-candidate acceptance boundaries, when present, MUST remain intact.
- **FR-030**: Create/copy/edit/delete and affected result facts MUST be keyboard operable with visible focus, programmatic labels/states and error associations, announced success/failure, and no color-only distinctions. Focus behavior MUST follow Story 5 scenario 4 and return logically on close; existing modal focus containment MUST be preserved. At 320 CSS pixels and 200% text enlargement, required facts and actions MUST remain reachable with field associations intact.
- **FR-031**: This slice MUST NOT introduce multi-form records, shared/linked copies, inheritance, synchronization, a dedicated week entity, annual recurrence, bulk creation, compulsory daily teaching, automatic regeneration/replacement, new exam policy, break exceptions, capacity diagnostics/proposals, larger course selections, external integrations, roles or student workflows.

### Authorized search/report corrections — 2026-11-09

- Given a course whose preferred session size would strand a remainder smaller than the minimum (for example 34 LE, 2–4 LE per session, preferred 3), constructive first-search guidance should try a complete representable partition when permitted opportunities allow it, rather than offer 33 LE solely because preferred-size choices came first. This guidance is advisory, uses the existing candidate domain, and must not impose a coverage floor, fairness objective, lecturer quota or new hard constraint.
- Constructive guidance must respect joint cohort/lecturer/room occupancy and the already validated candidate rules, use the same deadline/cancellation control, and permit the native search to proceed when guidance is absent or incomplete. A seed never proves coverage or preferences; only existing solver proof stages do. Fully proven priorities, canonical ranks and acceptance authority remain unchanged.
- Objective values on an unproven/not-attempted stage must be explained as measurements of the candidate, not as optimized outcomes. The schedule-shape value is a composite penalty, not LE, minutes or a count of invalid sessions. The room objective combines within-LV room transitions with additional rooms per cohort/date; it must not be described as only a count of transitions. No new blocker/capacity-diagnostics capability is included.

### Test Requirements *(mandatory)*

This specification requests test-first delivery under the project constitution. These are future implementation acceptance requirements; this specification task does not start tests or production changes.

- **TR-001**: Create/update failing acceptance tests before production changes for each story wherever practical; record any justified exception and its manual verification in the plan. Deliver and verify independently useful increments in priority order.
- **TR-002**: Verify dated/weekly administration, persistence, required fields, duplicate identity including marker-only duplicates, cross-form equality, overlaps, inactive relationships, stale edits, protected deletion and source/copy independence. Verify cancel/dismiss, explicit save and source-change-during-copy outcomes.
- **TR-003**: Independently compare feasible alternatives on small known datasets to verify the strict objective order, both coverage-sacrifice prohibitions, same-cohort variety, fixed teaching contribution, cross-date score ties, single-LV fallback, multi-day LV preference over once-per-week, unchanged unmarked behavior and stable ties.
- **TR-004**: Verify exact intensive accounting for whole/partial instructional intervals, break-only overlap, endpoint contact, overlapping marked windows, wider weekly windows and different source associations. Include a case with 90 instructional minutes covered once by multiple markers: intensive coverage is exactly 2 LE under the existing 45-minute LE, never 4 or session elapsed time divided by 45. With teaching at 09:00–09:45 and 09:55–10:40 and a marked interval 09:30–10:10, only 30 instructional minutes qualify: exactly two-thirds LE, regardless of the intervening break or permitting source.
- **TR-005**: Verify dated-only course availability and generation/validation agreement, no stitching, holidays, explicit narrower constraints where supported, periods, eligibility, availability, capacity, protected teaching/exams, hard session sizes/breaks and same-LV/date limits. No marker may legalize an otherwise invalid generated candidate.
- **TR-006**: Verify refresh across open/revisited Calendar/List/detail/planning views, marker-only changes, stale preparation/candidate rejection, refresh failure, manual-warning severity, immutable publication/history and no silent session mutation. Cover accepted, cancelled, failed, repeated and interrupted operation-wide replacement.
- **TR-007**: Verify German field/error/overlap messages, ordering, unsaved-copy presentation, default focus, keyboard flows, assistive-technology labels/announcements, color independence, narrow width and enlarged text. Verify intensive result counts and current/provisional associations and proof labels only where supported.
- **TR-008**: Verify backend behavior with the project's FastAPI-compatible tests, normally pytest under backend/tests/, and frontend behavior through the relevant React/TypeScript/Vite build, type, lint and component/UI checks in client/. Planning MUST document shared contract impacts for window kind/date/marker, copy/save outcomes, derived opportunities, freshness and objective/result evidence; verify cross-stack agreement before delivery. This section does not prescribe a new interface design.
- **TR-009**: Regression verification MUST preserve I-003/I-004 generation/acceptance, ordinary weekly windows, manual editing, exam behavior and lifecycle protections. Test I-009 without dependence on I-006/I-007/I-008; when their capabilities are present, verify the same windows/objective order and their existing approval/proof boundaries without adding those capabilities here. Record conditions for timing and planner acceptance measures.

### Key Entities

- **Weekly Time Window**: An existing recurring weekday interval for exactly one Studienform, with its established identity and active availability.
- **Dated Time Window**: One independently maintained full-date interval for one Studienform, with hours, active availability and explicit intensive state. It neither represents a week nor owns sessions.
- **Unsaved Copy**: Editable values taken from a weekly/dated source at action time, retaining kind and dated marker, becoming an independent window only on successful save.
- **Applicable Teaching Opportunity**: A permitted dated or weekly interval selected through the existing course/form relationships and bounded by other active constraints; overlapping opportunities add no physical capacity.
- **Intensive Teaching Coverage**: Exact instructional LE inside the union of applicable marked dated intervals for the selected generated teaching arrangement, separately from total coverage and excluded break time.
- **Cohort/Date Variety**: Distinct qualifying LVs for one cohort on one marked date and their contribution above the first LV, aggregated only after total and intensive coverage.
- **Current Validation and Prepared Generation Context**: Current applicable windows and findings or captured generation/comparison evidence whose freshness must reflect changes to permission and preference inputs without rewriting saved sessions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every acceptance case, an eligible Friday/Saturday form can use an explicitly added Monday, while zero additional Mondays, later-year dates or unrelated forms gain permission from that record.
- **SC-002**: In all weekly/dated copy cases, opening or cancelling saves zero records; a successful save creates exactly one independent record. Subsequent edits/deletions change zero source/copy peers and zero saved sessions.
- **SC-003**: In every independently comparable proven-outcome dataset, the result achieves the greatest total LE, then greatest intensive LE at that total, then greatest defined variety score at both fixed coverage values. All three equalities pass to the established lower preferences; no acceptance case sacrifices an earlier objective.
- **SC-004**: Every tested single-LV fallback remains valid; qualifying multi-day LV alternatives can outrank once-per-week placement. In every no-applicable-marker regression case, the established preference outcome is retained.
- **SC-005**: Across all overlap/boundary cases, intensive LE equals the instructional intersection with applicable marked intervals exactly, with zero double-counted minutes, zero credited breaks and no cross-cohort variety credit. Daily variety counts match FR-020 in every case.
- **SC-006**: Generation and current window validation agree in every tested dated/weekly permission case. All generated saved sessions satisfy inherited hard rules; window maintenance changes zero session facts, unselected sessions, exams, published revisions or historical facts.
- **SC-007**: Every relevant stale, rejected, cancelled or unsuccessfully applied result preserves the prior saved planning state. Interrupted acceptance resolves to either the prior state or the complete explicitly accepted joint result, never a partial application; a committed result is applied at most once even after retry.
- **SC-008**: In a documented normal acceptance dataset containing 100 weekly/dated windows, 20 courses and 100 current teaching sessions, twenty sequential successful window changes each refresh affected already open current planning/alert views within two seconds of save acknowledgement. Failed refresh is visibly non-current in every failure case; no session is moved to meet this target.
- **SC-009**: At least four of five representative planners or acceptance reviewers, unaided, can add one marked date, copy it to another form, cancel an extra copy and explain the independent/non-recurring behavior within five minutes. All five can identify from the result facts that total LE outranks intensive LE and that a single-LV day is permitted.
- **SC-010**: Every required create/copy/edit/cancel flow is completable with keyboard only. At 320 CSS pixels and 200% text enlargement, all checked field labels, dates, marker states, errors and actions retain readable associations; assistive-technology review exposes the same required information.

## Assumptions

- The authoritative scope is I-009 in Feature_slices.md and the supplied prompt, including decisions confirmed on 05.11.2026. This specification fills its named detail topics without changing product scope or initiating implementation. Only one feature is created.
- Dependencies are FS-007, FS-005, FS-011, FS-019, I-003 and I-004, including their inherited resource/course/revision protections. I-006's timeout extension and I-007/I-008 are not prerequisites. Their installed behavior, if present, retains its own approvals and truthful unproven-result rules.
- This slice extends I-003's weekly-only window eligibility/derived-window rules to include applicable dated opportunities and inserts intensive-use/variety ahead of I-003 FR-054's existing preferences. It does not restore retired generators, introduce per-course weekly editors or change I-004 acceptance authority. Deliberately narrower course restrictions, if present, remain binding through their existing controls.
- **Daily-variety default**: one point for each distinct qualifying LV after the first on each cohort/date rewards a daily mix without rewarding a mere isolated single-LV day. Two dates with two LVs each and one date with three LVs both score 2; this is an intentional tie, resolved by existing lower preferences rather than a new distribution objective. All cohorts/dates have equal weight.
- **Fixed teaching default**: qualifying fixed teaching for the same cohort can complement selected LVs in the daily mix. It never adds selected-course coverage, moves, changes validity or removes fixed occupancy. Fixed exams do not add variety.
- **Overlap default**: preserve the existing single-containing-window session rule; adding dated records does not merge adjacent/overlapping records into longer permitted sessions. For intensive credit, instructional intersections use the marked union independently of the permitting source, with exact proportional LE and no rounded partial-unit bonus. Existing LE duration and required-break placement are unchanged.
- **Administration defaults**: kind is chosen for new creation and retained during editing/copying; switching kind uses a new entry. Weekly and dated groups use the explicit ordering above. Duplicate handling extends the existing same-form weekly rule to dated identity, regardless of marker; a marker change is an edit to that record. No bulk actions or ongoing source link is inferred.
- **Lifecycle default**: dated records use the existing catalog's inactive and protected-deletion conventions. A saved reference can block deletion, but merely having permitted a session does not authorize changing it; removing an allowed opportunity otherwise produces current alerts under existing rules. Dates outside an active planning period can remain catalog data without granting out-of-period permission.
- **Freshness default**: a successful window save activates the new context independently of future generation success. A marker-only change invalidates dependent generation evidence although it does not change session-window validity. Current validation may change after source edits; historical/published evidence is not rewritten.
- **Presentation default**: intensive facts use existing generation result/comparison surfaces and German wording, including Intensivwoche and LE. Proof reporting extends only capabilities already present; I-009 neither implements a timeout extension nor permits acceptance that the installed workflow otherwise prohibits. Supported generation workload and time-budget policy remain inherited; no additional universal solve-time promise is introduced.
- No authentication, role, individual-student workflow, external source or integration is added. The planner remains responsible for deliberate saving and replacement decisions; any visual design follows the existing application patterns rather than a new mockup.
