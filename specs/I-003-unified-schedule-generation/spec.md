# Feature Specification: Unified Teaching Schedule Generation

**Working Branch**: `master`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "Create the unified teaching schedule generation feature described in docs/architecture/unified-teaching-schedule-generation.md. Replace the separate single-course and multi-course generation behavior with one conflict-aware workflow, include existing teaching sessions and exams as fixed occupancy, preserve transactional custom constraints, correct the List table grid, and render precise lecturer, room, and cohort conflict warnings."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-08-11

- Q: Which saved exams affect teaching generation? → A: Only active/upcoming exams; past exams are ignored for occupancy and teaching deadlines.
- Q: When do edited course constraints become active? → A: Immediately when saved, before generation; they revalidate the existing schedule and remain active if generation later fails.
- Q: What happens to the legacy single-course and independent batch generators? → A: Retire them immediately; they perform no scheduling and direct callers to unified generation.
- Q: Where do course date and weekly time constraints come from? → A: Each course-semester may override start/end dates inherited from the semester; weekly windows are always derived from the course's study type and cannot be edited per course.
- Q: Where are course-semester start/end dates edited? → A: Only in Calendar Planning inputs for the focused course; Academic Data manages the course's study type but does not duplicate date editing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Conflict-Safe Teaching Plan (Priority: P1)

A planner selects one or more courses and generates or regenerates their teaching
plans through one workflow. The system coordinates all selected courses while
protecting every unselected teaching session and active exam, so the result does
not introduce lecturer, room, or cohort overlaps regardless of selection size.

**Why this priority**: A generator that creates avoidable conflicts undermines
the planner's core purpose and makes previously valid semester plans unreliable.

**Independent Test**: Start from a semester containing Mathematics 1 sessions
and an active Data Visualization exam, configure the Data Visualization study
type with mapped weekly windows that include the occupied Mathematics times,
select only Data Visualization, and verify that any saved teaching result avoids
all protected teaching and exam occupancy and keeps the exam after the course's
final teaching session without accepting a course-specific window input.

**Acceptance Scenarios**:

1. **Given** one selected course has feasible slots outside unselected-course occupancy, **When** the planner generates its teaching plan, **Then** the saved result uses only conflict-free slots and leaves every unselected session unchanged.
2. **Given** several selected courses compete for the same cohort, lecturer, or room, **When** the planner generates their plans together, **Then** the saved combination schedules the greatest permitted total teaching coverage without introducing overlaps among selected or protected occurrences.
3. **Given** an active exam uses a lecturer, room, or cohort during an otherwise eligible teaching slot, **When** teaching candidates are evaluated, **Then** that exam remains unchanged and the conflicting teaching candidate is not saved.
4. **Given** the selected course already has an active exam, **When** its teaching plan is regenerated, **Then** no saved teaching session ends after that exam begins.
5. **Given** the active constraints leave no complete conflict-free arrangement, **When** generation finishes, **Then** the planner receives the best permitted partial or unchanged result with precise course-specific blocking reasons and no invalid result is saved.
6. **Given** identical unchanged planning inputs, **When** generation is repeated with the same selected courses, **Then** the resulting arrangement and reported outcomes are consistent.

---

### User Story 2 - Configure and Replace Plans Safely (Priority: P1)

A planner may edit and save course-specific start and end dates before
generation. They initially inherit the semester boundaries and belong to that
course in that semester. Weekly teaching windows are always derived from the
course's current study type. Saved date overrides and current study-type windows
become active immediately, revalidate the existing schedule, and remain active
independently of the later generation outcome. The planner then reviews which
existing drafts will be replaced and confirms generation.

**Why this priority**: Configured constraints express current planning intent and
must govern both the existing schedule and every subsequent generation attempt
without weakening replacement confirmation or stale-state protection.

**Independent Test**: Save a Data Visualization course-semester date override
while an older draft exists, verify that it immediately becomes current and any
violating sessions are identified, and verify that weekly candidates still come
only from the Full-time study-type windows. Then exercise successful, cancelled,
infeasible, and stale generation attempts and verify that every attempt uses
those active sources without rolling back the date override or replacing the
draft after failure.

**Acceptance Scenarios**:

1. **Given** a course initially inherits its semester dates, **When** the planner saves course-specific start and end dates within that semester, **Then** they become active immediately for that course-semester and the current saved schedule is revalidated without being regenerated automatically.
2. **Given** active constraints were saved before generation, **When** generation fails, times out, becomes stale, or is cancelled, **Then** those constraints remain active while the prior draft and manual edits remain unchanged.
3. **Given** one or more selected courses already have drafts, **When** preparation finishes, **Then** the planner is shown the exact courses whose drafts will be replaced and generation requires explicit confirmation.
4. **Given** the planner declines replacement confirmation, **When** the dialog closes, **Then** no schedule, exam, constraint, or planning record changes.
5. **Given** relevant teaching, active-exam, active-constraint, holiday, resource, semester, or revision state changes after preparation, **When** generation is submitted, **Then** no result based on stale inputs is saved and the planner is directed to review the current state.
6. **Given** the selected revision is not the active editable revision, **When** generation is attempted, **Then** the attempt is rejected without changing saved planning state.
7. **Given** a course is assigned to the Full-time study type, **When** its plan is generated, **Then** candidate weekdays and times come from the current Full-time time-window mappings and no per-course weekly-window override is used.

---

### User Story 3 - Use One Understandable Generation Workflow (Priority: P2)

A planner uses one course-selection and generation surface rather than choosing
between a single-course generator and a separate semester optimizer. Selecting
one course or many changes only the scope, not the safety rules or meaning of the
action.

**Why this priority**: Users should not need to know which internal workflow is
safe, and the same input must not produce different guarantees depending on the
button used.

**Independent Test**: Open Planning inputs, select one course, edit its
course-semester date range, then select additional courses and inspect their
active dates and derived study-type windows. Verify there is one generation
action, one preparation/confirmation flow, and no reachable independent
generator or per-course weekly-window editor.

**Acceptance Scenarios**:

1. **Given** an editable working revision, **When** Planning inputs opens, **Then** the planner sees one course selection and one teaching-plan generation action without separate single and multiple generation modes.
2. **Given** exactly one course is selected, **When** the planner reviews its inputs, **Then** its inherited or overridden start/end dates can be edited and its derived study-type windows can be reviewed but not edited before using the same generation action available to larger selections.
3. **Given** several courses are selected, **When** the planner reviews the selection, **Then** each selected course's active date range, study type, and derived weekly windows are identifiable before generation and unsaved date edits are not presented as active generation input.
4. **Given** a retired single-course or independent batch generation operation is invoked, **When** the request is received, **Then** it performs no scheduling and returns explicit guidance to use unified generation.
5. **Given** any supported teaching-generation action is used, **When** generation completes, **Then** it uses the unified conflict guarantees, preservation rules, and outcome semantics.

---

### User Story 4 - Understand Every Conflict Warning (Priority: P2)

A planner reviewing a saved or manually edited session can immediately tell
whether a warning concerns a lecturer, room, or cohort. When several conflict
types involve the same related session, each warning has a distinct title and
explanation rather than appearing duplicated.

**Why this priority**: Generic repeated warnings make planners distrust the
feedback and obscure which resource or group must be corrected.

**Independent Test**: Create two overlapping sessions that share a room and
cohort but use different lecturers. Verify that the affected sessions show one
Room conflict and one Cohort conflict, each with its related session details, and
do not show two identical generic messages.

**Acceptance Scenarios**:

1. **Given** two sessions overlap and share only a room, **When** warnings are displayed, **Then** the warning is titled "Room conflict" and explains that the room is assigned to overlapping sessions.
2. **Given** two sessions overlap and share only a cohort, **When** warnings are displayed, **Then** the warning is titled "Cohort conflict" and explains that the cohort has overlapping sessions.
3. **Given** two sessions overlap and share only a lecturer, **When** warnings are displayed, **Then** the warning is titled "Lecturer conflict" and explains that the lecturer is assigned to overlapping sessions.
4. **Given** the same pair shares a room and cohort, **When** warnings are displayed, **Then** two visibly different warnings identify those two conflict types and both identify the related course, date, and interval.
5. **Given** a conflict is no longer present after authoritative refresh, **When** the schedule is reviewed, **Then** its corresponding warning is absent.

---

### User Story 5 - Review an Aligned and Responsive List (Priority: P2)

A planner switches Calendar to List mode and can associate every value with the
correct header. Wide, zoomed, and narrow presentations remain understandable
without values silently wrapping into unrelated columns or visual rows.

**Why this priority**: A schedule table that places course, lecturer, room, or
cohort values under the wrong headings can cause incorrect planning decisions.

**Independent Test**: Review teaching sessions with and without multiple
warnings at 1280, 820, and 320 CSS pixels at 100% browser zoom and at a
1280-pixel viewport with 200% browser zoom. Verify that every value remains
associated with its field and all actions and warning details remain reachable.

**Acceptance Scenarios**:

1. **Given** List mode at 1280 CSS pixels and 100% browser zoom, **When** teaching rows are displayed, **Then** date, time, duration, course, cohort, lecturer, room, study type, and actions align with their respective headers.
2. **Given** a teaching session has one or more warnings, **When** the row is displayed, **Then** the warnings remain associated with that session without shifting later values into different columns.
3. **Given** List mode at 200% text zoom, **When** the planner reviews the table, **Then** every field remains identifiable and no required action or warning is clipped or assigned to the wrong header.
4. **Given** a 320- or 820-CSS-pixel presentation where the wide header is not practical, **When** sessions are displayed, **Then** each value has an explicit field label and the row does not rely on implicit grid wrapping to communicate meaning.

### Edge Cases

- The selection is empty, contains a duplicate course, exceeds the supported
  maximum, includes a course outside the semester, or includes an unavailable
  course.
- A selected course has no previous draft, a complete draft, a partial draft,
  manual edits, an over-scheduled draft, or a known pre-existing conflict.
- A selected course inherits the semester boundaries, has a saved date override,
  has an edited but unsaved date override, or has a period with no feasible date.
- A course's study type has several valid weekly windows, no active window,
  duplicate mappings, or mappings that cannot host its minimum session length.
- The course's study type or one of its mapped weekly windows changes. The new
  mapping becomes authoritative, the existing draft is revalidated without
  automatic movement, and prepared generation using the prior mapping becomes
  stale.
- Newly saved constraints invalidate one or more sessions in the existing draft.
  The draft remains unchanged, current warnings reflect the active constraints,
  and the planner may then regenerate or edit the affected sessions.
- An unselected teaching session touches a candidate boundary exactly; adjacent
  non-overlapping intervals remain permitted.
- An active exam touches a teaching candidate boundary exactly, shares one or
  several resources, belongs to the selected course, or belongs to another
  course in the same semester.
- A selected course has past exams and one active exam. Past exams remain stored
  and unchanged but do not reserve occupancy or limit generated teaching; only
  the active exam supplies fixed occupancy and a same-course teaching deadline.
- Existing selected drafts conflict with protected occupancy. Retaining them may
  be reported as unchanged, but no generated replacement may introduce a known
  conflict and an equal-coverage conflict reduction may qualify as improvement.
- A resource, holiday, exam, teaching session, constraint, or lifecycle state
  changes during preparation, solving, or saving.
- A complete arrangement cannot be proven within the operation deadline.
- One related session causes lecturer, room, and cohort conflicts at once. Each
  conflict dimension appears once per affected session with a distinct label.
- Warning reference data is incomplete. The UI distinguishes missing validation
  context from a substantiated lecturer, room, or cohort conflict.
- Long course/resource names and localized labels are displayed at wide, zoomed,
  and narrow widths without changing field association.
- A published or historical revision is selected. Generation controls are not
  presented as usable and direct mutation attempts remain rejected.
- A caller invokes a retired generation operation. The response identifies the
  unified replacement and no preparation, solving, constraint change, or
  schedule mutation occurs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one user-visible teaching-plan generation workflow for one to twenty distinct selected courses in one semester.
- **FR-002**: Selecting one course MUST use the same generation rules, preparation, confirmation, conflict guarantees, outcome meanings, and preservation behavior as selecting multiple courses.
- **FR-003**: The system MUST NOT expose or execute an independent teaching generator with weaker conflict guarantees through any supported user workflow.
- **FR-004**: The legacy single-course and independent batch generation operations MUST be retired when this feature becomes active, MUST perform no preparation or scheduling, and MUST return actionable guidance directing callers to unified generation.
- **FR-005**: The planner MUST be able to select and deselect eligible semester courses and see the current selection count before generation.
- **FR-006**: The system MUST reject empty, duplicate, oversized, cross-semester, missing, or currently unavailable course selections without changing saved state.
- **FR-007**: The system MUST evaluate all selected courses together and maximize total permitted scheduled teaching coverage before applying established deterministic secondary preferences.
- **FR-008**: Every generated teaching session MUST remain within its semester, active course-semester planning period, and a current weekly window mapped to the course's study type and MUST avoid institution-wide holidays and planner-supplied unavailable dates.
- **FR-009**: Every generated teaching session MUST use current active, eligible, available resources and a room with sufficient capacity for the applicable cohort.
- **FR-010**: Existing sessions for unselected courses MUST remain unchanged and MUST act as fixed lecturer, room, and cohort occupancy.
- **FR-011**: Every active exam in the selected semester MUST remain unchanged and MUST act as fixed lecturer, room, and cohort occupancy for teaching generation; past exams MUST remain unchanged but MUST NOT reserve occupancy.
- **FR-012**: For a selected course with an active exam, no generated teaching session MAY end after that active exam begins; past exams MUST NOT impose a teaching deadline.
- **FR-013**: Exact-boundary adjacency MUST be allowed when two occurrences share no positive duration.
- **FR-014**: Generated sessions for selected courses MUST NOT overlap one another when they share a lecturer, room, or cohort.
- **FR-015**: A generated replacement MUST NOT introduce a known lecturer, room, or cohort conflict, even when the current selected draft already contains conflicts.
- **FR-016**: Existing known conflicts MAY distinguish otherwise equal-coverage arrangements in favor of conflict reduction, but MUST NOT authorize a newly generated conflict.
- **FR-017**: The system MUST preserve the established deterministic ordering among otherwise permitted arrangements so unchanged inputs produce a consistent result.
- **FR-018**: The Calendar's course-focused Planning inputs MUST be the sole editing surface where the planner can review, edit, and explicitly save course-semester start and end dates before generation; other surfaces MAY display those dates read-only, and weekly windows MUST be reviewable there but MUST NOT be editable per course.
- **FR-019**: Saving valid course-semester start and end dates MUST make them active immediately and MUST revalidate the existing saved schedule without automatically moving, replacing, or deleting sessions.
- **FR-020**: Generation MUST use each selected course's active saved start/end dates or inherit the semester boundaries when no override exists; unsaved date edits MUST NOT be treated as active generation input.
- **FR-021**: Preparation MUST capture the active course-semester date range, course study type, and current mapped weekly-window state used for every selected course, and generation MUST NOT create, update, delete, or roll back those constraint sources.
- **FR-022**: A failed, cancelled, rejected, stale, timed-out, or unproven generation operation MUST leave prior drafts, manual edits, active constraints, teaching sessions, exams, and unrelated planning data unchanged; constraints deliberately saved before the operation remain active.
- **FR-023**: Preparation MUST identify every selected course with an existing draft that would be replaced.
- **FR-024**: Existing draft replacement MUST require explicit planner confirmation identifying the affected courses.
- **FR-025**: Cancelling replacement confirmation MUST cause no planning mutation.
- **FR-026**: Prepared generation input MUST become stale when any relevant selected or protected teaching session, active exam, constraint, holiday, resource, course, semester, or schedule-revision state changes; a change limited to an ignored past exam MUST NOT by itself invalidate preparation.
- **FR-027**: A stale prepared result MUST NOT save any arrangement that is no longer valid against current protected occupancy or planning rules.
- **FR-028**: Generation MUST be permitted only for the active editable working revision of the selected semester.
- **FR-029**: When a complete plan is infeasible, the system MUST preserve or save only the greatest permitted proven result that satisfies non-worsening replacement rules and MUST provide a course-specific outcome for every selected course.
- **FR-030**: Every incomplete, unchanged, failed, or stale course outcome MUST identify substantiated blocking categories and the course to which they apply.
- **FR-031**: The system MUST distinguish lecturer occupancy, room occupancy, cohort occupancy, resource eligibility, resource availability, capacity, holiday, date/window, exam-boundary, stale-input, and invalid-input reasons when substantiated; an occupancy reason MUST retain its lecturer, room, or cohort category and MUST additionally identify whether the protected source is a teaching session or active exam when that evidence is available.
- **FR-032**: A result that cannot be proven within the established operation deadline MUST save no uncommitted candidate and MUST provide an actionable failure.
- **FR-033**: Conflict validation MUST retain distinct lecturer-overlap, room-overlap, and cohort-overlap categories.
- **FR-034**: Each distinct overlapping session pair MUST contribute at most one warning per shared conflict category to each affected session.
- **FR-035**: Lecturer-overlap warnings MUST use the visible title "Lecturer conflict" and explain which lecturer is assigned to overlapping occurrences.
- **FR-036**: Room-overlap warnings MUST use the visible title "Room conflict" and explain which room is assigned to overlapping occurrences.
- **FR-037**: Cohort-overlap warnings MUST use the visible title "Cohort conflict" and explain which cohort has overlapping occurrences.
- **FR-038**: Every overlap warning MUST identify the related course, date, and interval and SHOULD identify the related lecturer, room, and cohort where that context is available.
- **FR-039**: When several conflict categories involve the same related session, each warning MUST remain visibly distinguishable and MUST NOT use identical generic overlap wording.
- **FR-040**: Resolved warnings MUST disappear after authoritative schedule refresh, while unresolved warnings remain associated with the affected occurrence.
- **FR-041**: The teaching List header and every wide teaching row MUST use the same ordered fields: date, time, duration, course, cohort, lecturer, room, study type, and actions when actions are permitted.
- **FR-042**: Warning content inside a date or session field MUST NOT alter the column placement of any subsequent teaching value.
- **FR-043**: From 320 through 820 CSS pixels, teaching rows MUST display explicit field labels when the wide header is absent and MUST NOT rely on implicit wrapping to communicate field meaning.
- **FR-044**: List content, warnings, and required actions MUST remain reachable and correctly associated throughout the defined 1280-, 820-, and 320-CSS-pixel acceptance matrix and the 1280-pixel viewport at 200% browser zoom.
- **FR-045**: Long localized names and warning text MUST wrap within their own field without entering or being interpreted as another field.
- **FR-046**: Existing exams, unselected teaching schedules, manual session management, lifecycle history, publication state, resource data, and academic data MUST NOT be moved or deleted by this feature.
- **FR-047**: The feature MUST preserve existing valid exam-generation and manual exam-management behavior while extending teaching generation to respect active exams without using past exams as generation constraints.
- **FR-048**: The feature MUST NOT introduce planner-selectable generation algorithms, automatic exam movement, automatic repair of unselected schedules, or silent conflict acceptance.
- **FR-049**: A course-specific planning period MUST belong to one course in one semester and MUST NOT change the same course's planning period in another semester.
- **FR-050**: A course without a saved course-semester date override MUST inherit the selected semester's start and end dates; an override MUST remain within those semester boundaries.
- **FR-051**: Weekly generation windows MUST be derived exclusively from the course's current study type and its current mapped time windows; the system MUST NOT copy or persist course-specific weekly-window overrides.
- **FR-052**: Changing a course's study type or a study type's mapped windows MUST immediately revalidate affected existing schedules without moving them automatically and MUST invalidate any prepared generation that used the previous mapping.
- **FR-053**: A course whose study type has no active mapped window capable of hosting its minimum session length MUST be unavailable for automatic generation with a precise study-type-window reason.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Service and end-to-end behavior MUST verify one-course and multi-course conflict avoidance against unselected teaching and active exams, past-exam exclusion, exact-boundary handling, same-course active-exam boundaries, semester/default and overridden course periods, study-type-derived windows, deterministic outcomes, and mixed feasible/infeasible selections.
- **TR-003**: State-transition tests MUST verify immediate course-date activation and existing-schedule revalidation, study-type-window derivation and change handling, generation against the captured active sources, draft preservation after cancellation, rejection, failure, timeout, or unproven results, and stale rejection after any captured input changes.
- **TR-004**: Contract tests MUST verify one unified selection/preparation/generation behavior and confirm that every retired generation operation performs no scheduling or mutation and returns the defined migration guidance.
- **TR-005**: Component and UI tests MUST verify the single generation surface, focused course-semester date editing, read-only derived study-type windows, replacement confirmation, course-specific outcomes, precise conflict titles and details, and removal of resolved warnings.
- **TR-006**: Layout tests and visual review MUST verify field association across the defined teaching List acceptance matrix: 1280 CSS pixels at 100% zoom, 820 CSS pixels at 100% zoom, 320 CSS pixels at 100% zoom, and a 1280-pixel browser viewport at 200% text zoom, each with zero, one, and multiple warnings and long labels.
- **TR-007**: Regression coverage MUST verify manual teaching management, exam management, lifecycle actions, publication immutability, calendar modes, resource administration, and academic-data behavior remain unchanged outside the specified integration points.
- **TR-008**: Performance coverage MUST verify the established supported workload and operation deadline remain satisfied when protected active-exam occupancy and active course constraints are included.
- **TR-009**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities

- **Unified Teaching Generation Preparation**: The read-only, time-bounded planning intent for one semester, one editable revision, one to twenty selected courses, their active constraints, protected occupancy, replacement requirements, and freshness evidence.
- **Selected Course Planning Input**: One selected course's requested teaching coverage, current draft state, inherited or overridden course-semester planning period, current study type and derived weekly windows, eligible resources, and cohort context.
- **Protected Schedule Occupancy**: Every teaching session or active exam that generation is not authorized to move, including its date, interval, lecturer, room, cohort, and course relationship; past exams are excluded from occupancy.
- **Teaching Generation Outcome**: The complete, partial, unchanged, failed, or stale result for one selected course, including scheduled and remaining coverage, whether anything was saved, and precise blocking reasons.
- **Conflict Warning**: A current finding for one affected occurrence and one conflict category—lecturer, room, or cohort—with the related occurrence context needed to understand and correct it.
- **Teaching List Row**: The visible representation of one teaching occurrence whose ordered values and warnings remain associated with stable field meanings across supported presentations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance datasets, a generated teaching replacement introduces zero lecturer, room, or cohort overlaps with selected teaching, unselected teaching, or active exams.
- **SC-002**: In 100% of same-course active-exam acceptance cases, every saved generated teaching session ends no later than the active exam start, while past exams do not alter the result.
- **SC-003**: In 100% of cancelled, rejected, failed, stale, timed-out, or unproven generation operations, previously saved drafts, manual edits, active constraints, teaching sessions, exams, and unrelated planning records remain unchanged.
- **SC-004**: In 100% of valid constraint-save acceptance cases, the new constraints become active and the existing schedule's current validity is refreshed before any generation attempt; subsequent generation uses exactly those active constraints whether it succeeds or fails.
- **SC-005**: For unchanged inputs, selecting one course through the supported unified workflow produces the same conflict guarantees and observable outcome as the one-course case of a larger selection, while 100% of retired generation-operation requests perform no scheduling mutation.
- **SC-006**: In an unaided usability review with at least ten representative semester planners whose responsibilities include semester or course scheduling, at least 90% of participants MUST, on their first attempt, select one or more courses, locate the focused course's active date constraints and derived study-type windows, and initiate unified preparation without using a legacy workflow or receiving procedural help.
- **SC-007**: In 100% of warning acceptance cases, planners can distinguish lecturer, room, and cohort conflicts from the visible title without expanding warning details, including when several categories concern the same related session.
- **SC-008**: In 100% of inspected List rows across the defined 1280-, 820-, and 320-CSS-pixel presentations at 100% zoom and the 1280-pixel presentation at 200% text zoom, every displayed value can be correctly associated with its intended field and every required action and warning remains reachable.
- **SC-009**: In the documented acceptance environment, after one unmeasured warm-up operation, twenty sequential measured operations using fresh copies of the reference workload of up to twenty selected courses, six hundred requested teaching units, and five hundred protected occurrences MUST each present a complete saved-state result or actionable failure within sixty seconds, and at least nineteen of the twenty MUST do so within thirty seconds. Evidence MUST record the application version, processor allocation, memory allocation, operating system or container environment, and every measured duration and outcome.
- **SC-010**: In 100% of regression acceptance cases, unselected teaching sessions and saved exams remain unchanged and established manual management, lifecycle, publication, calendar, resource, and academic-data outcomes remain valid.
- **SC-011**: In 100% of generation acceptance cases, every candidate weekday and time comes from the selected course's current study-type mappings, while every candidate date remains within the course's inherited or overridden semester-bounded planning period.

## Assumptions

- For teaching List acceptance, a wide presentation is a viewport of at least
  821 CSS pixels and a narrow presentation is 320 through 820 CSS pixels. The
  required matrix uses 1280 CSS pixels at 100% browser zoom, 820 CSS pixels at
  100% zoom, 320 CSS pixels at 100% zoom, and a 1280-pixel browser viewport at
  200% text zoom. Browser chrome and operating-system display scaling are
  recorded separately and do not replace browser zoom.

- The existing planner audience and authorization model remain unchanged; only
  an active working revision may be generated or regenerated.
- One authoritative generator means one placement decision process and one
  user-visible workflow. The previous single-course and independent batch
  generation operations are retired immediately and provide migration guidance
  without acting as compatibility schedulers.
- Only active exams in the semester are protected occupancy. For the same
  selected course, its active exam is also the latest permissible teaching
  boundary. Past exams remain stored and unchanged but are ignored when
  evaluating occupancy, teaching deadlines, and preparation freshness.
- Adjacent intervals that share only an endpoint do not overlap.
- Course-specific generation constraints are limited to optional start and end
  date overrides for one course-semester and are saved independently from
  generation. They are edited only through the Calendar's course-focused
  Planning inputs. Academic Data continues to manage the course's study type and
  does not provide a second date-editing surface. All selected courses use the
  same generation action and safety rules.
- Start and end dates inherit the selected semester boundaries until overridden
  within those boundaries. Weekly candidate windows always come from the
  course's current study type and are never copied into or overridden by a
  course-specific generation configuration.
- Existing data can support the unified workflow without requiring planners to
  recreate courses, schedules, constraints, or exams.
- Manual teaching edits remain deliberate planner actions and may continue to
  surface non-blocking current warnings; this feature makes those warnings
  precise but does not silently move manually edited sessions.
- English requirement labels such as "Room conflict" correspond to localized
  user-facing equivalents in the active interface language, including
  "Raumkonflikt", "Kohortenkonflikt", and "Lehrpersonenkonflikt" in German.
