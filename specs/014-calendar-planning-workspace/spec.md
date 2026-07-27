# Feature Specification: FS-014 Calendar Planning Workspace and Operational Dashboard

**Working Branch**: `master`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "Give planner users one calendar-centered semester workspace for schedules, remaining units, alerts, failures, and lifecycle state while preserving existing correction workflows and revision semantics."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-23

- Q: How long should generation and optimization failures remain available in FS-014? → A: Persist the latest applicable outcome per course, operation kind, and revision until a newer applicable outcome supersedes it.
- Q: When viewing the Current Published revision, which validation information should the workspace show? → A: Revalidate Published sessions against current planning data and label the resulting warnings as current; Published session content remains unchanged.
- Q: Should the existing Courses overview be reused as the List view inside the unified Schedule workspace, rather than building another list? → A: Yes. The existing Courses overview becomes the List view, preserves its required behavior, and is not duplicated by a second list.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the Semester at a Glance (Priority: P1)

A planner opens one selected semester and sees its teaching sessions, exams,
remaining teaching work, current alerts, recent planning failures, lifecycle
state, and schedules needing attention in one coherent workspace.

**Why this priority**: The feature succeeds only if the planner can establish
the semester's operational state without reconciling several disconnected
screens.

**Independent Test**: Prepare a semester with teaching and exam sessions,
remaining units, several validation conditions, an applicable failed planning
outcome, an active working revision, and a current publication. Open the
workspace and verify that each category is visible, accurately aggregated, and
derived from one clearly identified revision context.

**Acceptance Scenarios**:

1. **Given** a semester has an active working revision, **When** the planner opens the workspace for that semester, **Then** the working revision is the default context and its stable identity, Draft or Ready for review state, and working designation are visible.
2. **Given** a semester has no active working revision but has a current Published revision, **When** the planner opens the workspace, **Then** the current Published revision is the default context and is visibly identified as read-only.
3. **Given** the selected revision contains teaching sessions, exams, holidays, remaining teaching units, validation findings, and applicable planning outcomes, **When** the workspace finishes loading, **Then** its calendar and operational summaries describe that same revision and selected semester.
4. **Given** a working revision and current Published revision both exist, **When** the planner switches between them, **Then** the complete calendar, summaries, detail context, and available actions switch together without mixing records from the two revisions.
5. **Given** one or more course schedules meet the defined needs-review conditions, **When** the operational summary is displayed, **Then** each affected course is counted once and the planner can identify the condition or conditions that caused its inclusion.
6. **Given** no applicable planning outcome data is available for the selected revision, **When** the workspace displays planning failures, **Then** it identifies the metric as unavailable rather than reporting a misleading zero.
7. **Given** an applicable planning outcome was completed and retained for the selected revision, **When** the planner reloads or revisits the workspace before a newer applicable outcome supersedes it, **Then** the same latest outcome remains available to the operational summary.
8. **Given** current holiday, room, resource, or other applicable planning data changes after publication, **When** the planner views the Current Published revision, **Then** its captured sessions and identifying context remain unchanged while current validation warnings and affected summaries are recalculated, labeled as current, and derived only from the Published sessions.

---

### User Story 2 - Navigate and Filter the Calendar (Priority: P1)

A planner moves through the semester in week, day, or month mode, can retain the
existing list-oriented review option, and narrows the workspace by planning,
resource, session, lifecycle, or validation context without changing schedule
data.

**Why this priority**: A semester-scale workspace is useful only when the
planner can reach the relevant dates and reduce visual density while preserving
the meaning of the full plan.

**Independent Test**: Open a semester whose sessions span its full date range,
navigate in every supported mode, apply each filter separately and in
combination, clear the filters, and verify that the matching calendar items and
summaries change while all saved schedule and planning records remain
unchanged.

**Acceptance Scenarios**:

1. **Given** a selected semester and revision, **When** the planner first opens the calendar, **Then** Week is the default calendar mode and the visible date range is clearly identified.
2. **Given** the planner is in Week, Day, or Month mode, **When** the planner moves to the previous or next period or chooses a date in the selected semester, **Then** the calendar shows the corresponding period without changing the semester or revision context.
3. **Given** the planner changes among Week, Day, Month, and List, **When** the new mode appears, **Then** active filters, selected semester, selected revision, and any still-visible selected session are preserved.
4. **Given** the selected revision contains teaching and exam sessions, **When** they appear in any calendar mode, **Then** teaching and exam items are distinguishable without relying only on color and expose enough identifying context to select the intended item.
5. **Given** available records span several courses, cohorts, lecturers, rooms, study types, session types, lifecycle states, and validation states, **When** the planner applies one or more corresponding filters, **Then** only matching records are presented and the active filter context remains visible.
6. **Given** filters produce no matching records, **When** the result is displayed, **Then** the workspace explains that no records match, preserves the selected semester and revision, and provides a direct way to clear the active filters.
7. **Given** a planner applies, clears, or combines filters, **When** the visible result changes, **Then** no schedule, session, lifecycle, planning outcome, holiday, or source record is created, changed, or removed.
8. **Given** the calendar period includes dates outside the selected semester at a Week or Month boundary, **When** those dates are shown for orientation, **Then** they are identified as outside the semester and do not introduce records from another semester.
9. **Given** the planner selects List in the unified Schedule workspace, **When** the List view appears, **Then** it is the existing Courses overview adapted into that view with its required filters, review information, alerts, and correction paths preserved rather than a second list being presented.

---

### User Story 3 - Trace Summaries and Alerts to Affected Records (Priority: P1)

A planner follows any operational metric, remaining-work indicator, or alert to
the courses, sessions, exams, or planning outcomes responsible for it and can
return to the unfiltered semester view.

**Why this priority**: Summary numbers are actionable only when the planner can
verify their composition and reach the work behind them.

**Independent Test**: For every defined operational summary, create a semester
with multiple contributing and non-contributing records, activate the summary,
and verify that the resulting record set accounts for the displayed aggregate
without unrelated or missing contributors.

**Acceptance Scenarios**:

1. **Given** the workspace reports unscheduled units and hours, **When** the planner activates that summary, **Then** the planner sees every contributing course, each course's total, scheduled, and remaining units, and a path to its applicable existing planning or manual-session workflow.
2. **Given** the workspace reports conflict findings, **When** the planner activates that summary, **Then** every distinct counted finding can be traced to its conflict type and all affected sessions.
3. **Given** the workspace reports room-capacity issues, **When** the planner activates that summary, **Then** every counted session can be identified with required capacity, assigned room, and current room capacity.
4. **Given** the workspace reports planning failures, **When** the planner activates that summary, **Then** every counted failed course outcome is visible with its operation kind, course, and all available substantiated reasons.
5. **Given** the workspace reports schedules needing review, **When** the planner activates that summary, **Then** each counted course appears once with every current condition that caused it to be included.
6. **Given** an alert-driven view or summary drilldown is active, **When** the planner clears that context, **Then** the complete selected revision returns with the original semester, revision, and calendar mode preserved.
7. **Given** an affected record is outside the currently visible date period, **When** the planner follows a metric or alert to that record, **Then** the calendar moves to the relevant date or presents the applicable non-calendar course or outcome detail without losing revision context.

---

### User Story 4 - Inspect and Correct a Session Through Existing Workflows (Priority: P2)

A planner selects a teaching or exam item, understands its full scheduling and
warning context, and invokes the existing planner-authorized correction action
without the calendar inventing a second set of scheduling rules.

**Why this priority**: The workspace must turn awareness into action while
preserving the validated manual creation, editing, deletion, and lifecycle
behavior delivered by earlier slices.

**Independent Test**: Select representative teaching and exam items in an
editable working revision, open their detail, complete and cancel each
applicable existing correction workflow, and verify that the workspace refreshes
from saved state while the same actions are unavailable in Published context.

**Acceptance Scenarios**:

1. **Given** a teaching session is selected, **When** its detail is opened, **Then** the planner can identify its date, time, teaching units, course, cohort, lecturer, room, study type, source where available, revision context, and all current validation findings.
2. **Given** an exam session is selected, **When** its detail is opened, **Then** the planner can identify the exam details and validity context already required by FS-012, including its course, type, duration, timing, resources, capacity, recommendation context, lifecycle, and current issues.
3. **Given** a session belongs to the active working revision, **When** the planner chooses an available edit or deletion action, **Then** the established action opens with its existing validation, confirmation, stale-state, and preservation rules unchanged.
4. **Given** a course has remaining teaching units in the active working revision, **When** the planner follows its remaining-work action, **Then** the existing manual creation or planning workflow opens in that course-semester and revision context.
5. **Given** an established correction succeeds, **When** the planner returns to the workspace, **Then** the calendar item, operational summaries, alerts, and remaining-unit context refresh from the saved selected revision without requiring the planner to reopen the semester.
6. **Given** a correction is cancelled, fails, or becomes stale, **When** the planner returns to or remains in the workspace, **Then** saved data is unchanged, no success is implied, and the planner receives the established actionable feedback.
7. **Given** the current Published revision is selected, **When** the planner inspects any session or exam, **Then** the detail remains available but mutation actions are unavailable and the workspace explains that Published content is immutable.

---

### User Story 5 - Compare Working and Published Operational Context (Priority: P2)

A planner can tell whether the workspace shows unpublished work or the current
publication, switch between those contexts when both exist, and understand that
Ready for review is informative rather than an approval gate.

**Why this priority**: FS-013 protects a stable publication; the calendar must
not cause planners to mistake working changes for the schedule currently
published.

**Independent Test**: Publish a semester, start and edit a successor working
revision, mark it Ready for review, and switch repeatedly between Working and
Current Published. Verify distinct identity, state, content, summaries, and
action availability in each context.

**Acceptance Scenarios**:

1. **Given** Working and Current Published contexts coexist, **When** either context is displayed, **Then** a persistent label communicates its stable revision identity, lifecycle state, and working or current-publication designation using more than color.
2. **Given** the working revision differs from the current publication, **When** the planner switches contexts, **Then** changed, added, or removed sessions and their derived summaries appear only in the revision to which they belong.
3. **Given** the working revision is Ready for review, **When** the planner views it, **Then** that state is visible but is not described as approved, locked, or required for publication.
4. **Given** a lifecycle action is needed, **When** the planner follows it from the workspace, **Then** the established FS-013 lifecycle workflow opens and the workspace does not create an alternative transition rule.
5. **Given** a superseded, abandoned, or other historical revision exists, **When** the main workspace revision control is displayed, **Then** it does not mix that historical content into Working or Current Published; complete history remains available through the established lifecycle history workflow.

---

### User Story 6 - Continue Safely Through Responsive and Failure States (Priority: P3)

A planner can use the complete workspace with keyboard or assistive technology,
at supported narrow or zoomed views, and when some or all workspace data cannot
be loaded.

**Why this priority**: Operational decisions must remain understandable and
safe when space is constrained, data arrives gradually, or a refresh fails.

**Independent Test**: Exercise the workspace at the supported narrowest width
and text zoom, with keyboard and assistive technology, and with delayed,
partially unavailable, failed, and retried data sources; verify access to every
required record and action without false counts or mixed revision context.

**Acceptance Scenarios**:

1. **Given** the workspace is viewed at a supported narrow width or up to 200% text zoom, **When** the planner navigates its calendar, summaries, filters, and session details, **Then** every required item and action remains reachable without navigation or controls obscuring one another.
2. **Given** the planner uses only a keyboard, **When** they change mode or date, apply filters, activate a summary, select a calendar item, open detail, and return, **Then** every action is operable in a logical focus order with visible focus and no focus loss.
3. **Given** workspace data is loading, **When** incomplete new context is not yet ready, **Then** the workspace identifies the loading state and does not combine a new semester or revision label with calendar or summary data from a previous context.
4. **Given** one summary source is unavailable while other revision data is usable, **When** the workspace displays partial data, **Then** affected metrics are marked unavailable, available records remain identifiable, and no unavailable value is represented as zero.
5. **Given** the initial workspace load fails, **When** the failure state appears, **Then** the selected semester and intended revision context remain identifiable, no unverified metric is shown as current, and a retry is available.
6. **Given** a refresh fails after a previously successful load, **When** the failure is shown, **Then** any retained information is clearly identified as last known, the failed portions are marked, saved data is not changed, and the planner can retry.
7. **Given** a retry succeeds, **When** current data appears, **Then** failure messaging clears and the calendar, summaries, details, and action availability all reflect one refreshed revision context.

### Edge Cases

- The selected semester has no lifecycle revision. The workspace presents an
  explicit no-revision state and the established Start Draft path; it does not
  present an empty calendar as if it were a loaded working or published
  revision.
- The selected semester has a working revision but no current publication. The
  Working context remains fully usable and no Published context is implied.
- The selected semester has a current publication but no working revision. The
  Published context is the default, all schedule content is read-only, and the
  established start-new-revision action remains available where authorized.
- Current planning data changes after publication. The Published sessions,
  captured course totals, and identifying context remain unchanged, while
  current validation warnings update and are explicitly distinguished from
  captured Published content.
- A Working revision coexists with the Current Published revision and contains
  sessions that conflict with Published sessions. Published validation does not
  compare against or count the Working sessions; switching to Working evaluates
  that revision independently.
- The selected revision has courses but no scheduled teaching or exam sessions.
  The calendar shows a genuine empty schedule, while course-level remaining
  units and applicable failures remain visible and traceable.
- The selected revision has sessions but no current issues or remaining units.
  Zero-valued summaries are distinguishable from unavailable summaries, and the
  workspace does not invent a needs-review record.
- A course's saved teaching units exceed the total units represented by the
  selected revision. Remaining units are zero rather than negative, and the
  workspace does not alter or hide the excess sessions.
- The same two sessions overlap for lecturer, room, and cohort. The conflict
  summary counts three distinct findings, one per conflict type, while each
  finding remains traceable to the same affected pair.
- The same validation finding is attached to both affected sessions. It is
  counted once in the aggregate and remains visible from both sessions.
- One session has several validation conditions. It contributes once to each
  applicable issue category and only once to the needs-review course count.
- A room-capacity issue and a resource conflict concern the same session. Both
  remain visible and traceable without combining their meanings.
- A saved teaching session or exam falls on a current institution holiday. The
  holiday date context and affected-session warning are visible, but the
  session is not moved or deleted.
- A current holiday has no scheduled session. It may appear as non-session date
  context in the calendar without being counted as a schedule alert or
  needs-review course.
- A saved exam becomes invalid after teaching, holiday, resource, capacity, or
  timing context changes. It remains visible and is included in applicable
  issue and needs-review results without being altered automatically.
- A planning operation has complete, improved partial, unchanged, failed, and
  stale course outcomes. Only failed outcomes contribute to the failure count;
  stale and applicable incomplete outcomes can still cause a course to need
  review and remain separately identified.
- A newer planning operation exists for only some courses. Each course uses its
  latest applicable outcome for the selected revision; an older failure is not
  counted after a newer applicable non-failed outcome supersedes it for that
  course.
- A newer planning operation covers the same course but a different operation
  kind. It supersedes only the retained outcome for that operation kind; the
  latest outcomes for other operation kinds remain available.
- Filters exclude one member of a conflict pair. The filtered result identifies
  the visible affected session and preserves a path to the related session so
  the displayed finding remains understandable.
- A room filter includes a course with sessions in that room. Any displayed
  remaining units still mean course-level unassigned work and are not presented
  as work already assigned to the filtered room.
- A selected or focused session disappears after a successful deletion or no
  longer matches active filters after an edit. Focus moves to a predictable
  nearby result or the result-set heading, and the workspace explains the
  changed result rather than leaving focus on hidden content.
- Today falls before or after the selected semester. Current-period navigation
  uses the nearest semester boundary for Day, Week, or Month, communicates that
  substitution, and remains not applicable in List mode.
- A date contains more simultaneous sessions than can be shown legibly in Month
  mode. The mode exposes an understandable count or continuation path to all
  sessions without silently omitting them.
- Changing the visible date period, mode, filter, selected session, or summary
  drilldown must not discard unsaved work inside a separately opened correction
  workflow without using that workflow's established confirmation behavior.

### Scope Boundaries

This slice includes one calendar-centered operational workspace within the
existing Schedule destination; Week, Day, Month, and retained List review
modes; semester and date navigation; filters for course, cohort, lecturer, room,
study type, teaching or exam session type, working or current-published
lifecycle context, and validation state; teaching and exam items; institution
holiday context; operational summaries; summary-to-record navigation; session
detail; links into existing planner-authorized correction and lifecycle actions;
clear Working versus Current Published context; and responsive, accessible,
empty, loading, partial-data, and failure states.

This slice does not add a separate Dashboard destination, lecturer access,
authentication, new scheduling or optimization behavior, new conflict or
capacity rules, new correction semantics, external synchronization, external
publication delivery, historical revision comparison in the main calendar,
pixel-perfect reproduction of either visual reference, automatic repairs,
session duplication, a second session-list presentation, or drag, drop, resize,
split, or merge interactions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST provide one calendar-centered operational workspace for one selected semester within the existing Schedule destination and MUST reuse the shared application navigation established by FS-018.
- **FR-002**: The workspace MUST NOT introduce a separate Dashboard destination, second global navigation model, or replacement navigation hierarchy.
- **FR-003**: The workspace MUST require one selected semester and MUST identify that semester and its full date range wherever calendar or summary data is presented.
- **FR-004**: The workspace MUST operate against exactly one selected semester revision context at a time: the active Working revision or the Current Published revision.
- **FR-005**: When an active Working revision exists, it MUST be the default workspace context; otherwise the Current Published revision MUST be the default when one exists; when neither exists, the workspace MUST present the established no-revision and Start Draft state. That no-revision state MUST have a null selected revision, no revision-owned courses, occurrences, holidays, validation findings, planning outcomes, or filter facets, and only not-applicable operational summaries identified with no-revision scope; it MUST NOT be represented as a loaded empty schedule.
- **FR-006**: When Working and Current Published both exist, the planner MUST be able to switch between them, and the calendar, summaries, selected detail, warnings, and action availability MUST switch together before the new context is presented as current.
- **FR-007**: Every displayed revision context MUST visibly identify its stable revision identity, lifecycle state, and whether it is the active Working revision or Current Published revision using text or another non-color indicator.
- **FR-008**: Current Published content MUST be read-only in the workspace; all mutation actions MUST be unavailable in that context without hiding the session and issue details needed for review.
- **FR-009**: Draft and Ready for review Working revisions MUST retain the editability and lifecycle behavior established by FS-013; Ready for review MUST NOT be represented as approval, immutability, or a publication prerequisite.
- **FR-010**: Superseded, abandoned, and other historical revisions MUST NOT be combined with Working or Current Published content in the main workspace; established revision history remains the path for historical review.
- **FR-011**: Week MUST be the default calendar mode. The planner MUST also be able to use Day and Month calendar modes, and the existing Courses overview MUST become the unified workspace's single List review mode with its required behavior preserved; the feature MUST NOT build or retain a second session-list presentation.
- **FR-012**: The workspace MUST provide previous-period, next-period, current-period, and in-semester date navigation appropriate to the selected mode, while preserving the selected semester, revision, and active filters. In Day, Week, or Month mode, the current-period action MUST show the period containing today when today is inside the selected semester; when today is before the semester, it MUST show the period containing the semester start date; and when today is after the semester, it MUST show the period containing the semester end date. The workspace MUST communicate when the nearest semester boundary was used instead of today. In List mode, current-period navigation is not applicable and MUST NOT change the result position.
- **FR-013**: Week and Month boundary dates outside the selected semester MAY be shown for orientation but MUST be visibly distinguished and MUST NOT display records from another semester.
- **FR-014**: Changing calendar mode or visible date period MUST NOT create, edit, delete, move, resize, regenerate, validate, publish, or otherwise mutate schedule or planning data.
- **FR-015**: Every scheduled teaching session in the selected context MUST be represented in the applicable date and time position or chronological list position.
- **FR-016**: Every scheduled exam in the selected context MUST be represented and MUST be distinguishable from teaching sessions through a textual, symbolic, or structural indicator in addition to any color treatment.
- **FR-017**: A calendar item MUST expose or lead directly to its session kind, date, time, course, cohort, lecturer, room, revision context, and current warning state; a teaching item MUST expose its teaching-unit context, and an exam item MUST expose its existing FS-012 exam and validity context.
- **FR-018**: Current institution holidays relevant to the selected semester MUST be available as date context, and teaching or exam sessions affected by a holiday MUST retain their current session-specific warning without being moved, deleted, or repaired.
- **FR-019**: The workspace MUST offer filters for course, cohort, lecturer, room, study type, session type, lifecycle context, and validation status when corresponding choices exist in the selected semester context.
- **FR-020**: Course, cohort, lecturer, and study-type filters MUST be able to include course-semester contexts that have remaining units but no scheduled session; room filters MUST NOT imply that unscheduled units are assigned to the selected room.
- **FR-021**: Session-type filtering MUST distinguish at least teaching and exam records; unscheduled teaching units MUST be included only in teaching or all-session operational scope, not exam-only scope.
- **FR-022**: Lifecycle filtering MUST select or retain one permitted revision context and MUST NOT display a blended calendar containing Working and Current Published records.
- **FR-023**: Validation filtering MUST allow the planner to isolate no-current-issue records or records affected by current conflict, capacity, holiday, exam-validity, planning-failure, stale-outcome, or other established validation categories that exist in the selected context.
- **FR-024**: Active filters MUST remain visible, combine predictably as intersections of their applicable record conditions, and provide one action that clears the complete filter and drilldown context.
- **FR-025**: Filter choices MUST change only the presented result set and derived summaries; they MUST NOT modify any domain data or discard records from the selected revision.
- **FR-026**: Every operational summary MUST state whether it describes the complete selected revision or a filtered subset and MUST use the same selected semester and revision context as the presented records.
- **FR-027**: For each included course, unscheduled teaching units MUST equal the greater of zero and the course total teaching units represented by the selected revision minus the sum of teaching units in all its teaching sessions in that revision; a Published view MUST use its captured revision context rather than substituting a later source-record value.
- **FR-028**: Unscheduled instructional time MUST equal unscheduled teaching units multiplied by 45 minutes; inter-unit breaks and elapsed session duration MUST NOT be included in that conversion. The displayed hours MUST preserve the exact total, including remaining minutes where the total is not a whole hour.
- **FR-029**: The unscheduled-work summary MUST expose total unscheduled units, equivalent instructional time, and the number of contributing courses; its detail MUST expose each contributing course's total, scheduled, and remaining units.
- **FR-030**: The conflict summary MUST count each distinct overlapping unordered session pair once per established conflict type, including lecturer, room, and cohort; the same pair MAY therefore contribute once to each applicable type but MUST NOT be double-counted because the finding is attached to both sessions.
- **FR-031**: Every counted conflict MUST be traceable to its conflict type and all affected sessions, including their course, date, time, and conflicting resource or cohort context.
- **FR-032**: The room-capacity summary MUST count each distinct scheduled teaching or exam session once when its current assigned room capacity is below its applicable required capacity; repeated alerts for the same session MUST NOT increase the count.
- **FR-033**: Every counted capacity issue MUST be traceable to the affected session, its course and session kind, its required capacity, its assigned room, and that room's current capacity.
- **FR-034**: The product MUST retain the latest applicable completed planning outcome for each course, operation kind, and revision across reloads and later workspace visits until a newer applicable completed outcome for that same course, operation kind, and revision supersedes it.
- **FR-035**: The planning-failure summary MUST use those retained latest applicable outcomes, MUST count only outcomes classified as failed, and MUST identify stale and unchanged outcomes separately rather than counting them as failures.
- **FR-036**: When a newer applicable outcome supersedes an older outcome for the same course, operation kind, and revision, the older outcome MUST NOT remain in the current failure total; an outcome for a different course, operation kind, or revision MUST NOT supersede it.
- **FR-037**: For the selected revision and current filter scope, the planning-outcome coverage universe MUST contain every included course-semester context eligible for at least one established planning operation. A course has outcome coverage when at least one reliable completed outcome is retained for that course and revision. The failure summary MUST be not applicable when the coverage universe contains no eligible courses; unavailable when eligible courses exist but none has retained outcome coverage; partial when some but not all eligible courses have retained outcome coverage; and available when every eligible course has retained outcome coverage. A partial count MUST be identified as a known incomplete count. Zero failures MUST be shown only when coverage is available and no retained applicable outcome is failed. The failure count MUST count retained failed outcome records rather than distinct courses. An operation kind that was never attempted MUST NOT be treated as failed and MUST NOT independently reduce coverage after its course has outcome coverage. An outcome that cannot be associated reliably with the selected revision MUST NOT contribute to coverage or counts, and an outcome from another revision MUST NOT be reused.
- **FR-038**: A course schedule MUST be classified as needing review when, in the selected revision, it has one or more remaining teaching units, a current conflict, a current room-capacity issue, a holiday-affected session, a current exam-validity issue, an applicable failed or stale planning outcome, or another current actionable validation condition established by an earlier slice.
- **FR-039**: The needs-review summary MUST count each affected course-semester planning context once regardless of how many qualifying conditions it has and MUST expose every condition responsible for each course's inclusion.
- **FR-040**: Draft, Ready for review, or Published lifecycle state by itself MUST NOT cause a course to be classified as needing review; Ready for review remains the informative semester-revision state defined by FS-013 and does not mean reviewed or approved.
- **FR-041**: Zero values MUST be used only when the relevant data is available and no contributing record exists; unavailable, not applicable, loading, stale, and failed-to-load states MUST be visibly distinct from zero. Applicability MUST be determined after applying the selected revision and current filter scope. Unscheduled work is not applicable when no course-semester context is included and is available with zero when included courses have complete teaching-unit data and none has remaining units. Conflicts are not applicable when no scheduled occurrence is included and are available with zero when at least one included occurrence was evaluated and no conflict exists. Capacity issues are not applicable when no included scheduled occurrence requires capacity evaluation and are available with zero when every included applicable occurrence was evaluated and none exceeds room capacity. Needs review is not applicable when no course-semester context is included and is available with zero when included courses were evaluated and none has a qualifying reason. A metric is unavailable when none of its required source data can be verified and partial when only some included applicable records can be verified; every partial numeric value MUST be labelled as a known incomplete value.
- **FR-042**: Activating any summary value, alert category, remaining-unit indicator, or needs-review item MUST present the complete set of records that contributes to it or apply an equivalent traceable view whose displayed record set reconciles with the aggregate.
- **FR-043**: A summary or alert drilldown MUST preserve the selected semester, revision context, calendar mode, and unrelated active filters, and clearing it MUST restore the prior un-drilled result context.
- **FR-044**: When a contributing session is outside the visible date period, trace navigation MUST move to its date or otherwise present its full detail without changing revision context.
- **FR-045**: When a contributing record is course-level or outcome-level and has no scheduled date, trace navigation MUST present a non-calendar detail or list context rather than assigning a fabricated date.
- **FR-046**: Selecting a teaching or exam item MUST open an inspectable detail that retains all current warnings and supplies only the correction, deletion, creation, planning, or lifecycle actions already authorized and defined by FS-009 through FS-013.
- **FR-047**: The workspace MUST NOT redefine validation, confirmation, stale-state, preservation, capacity, eligibility, availability, conflict, holiday, exam, remaining-unit, optimization, or lifecycle rules owned by earlier slices.
- **FR-048**: After a successful existing correction or lifecycle action, the workspace MUST refresh the calendar, summaries, remaining work, warnings, selected revision identity, and action availability from saved state without requiring the planner to leave and reopen the semester.
- **FR-049**: A cancelled, rejected, failed, or stale action MUST leave saved state unchanged, MUST NOT be presented as successful, and MUST retain or refresh enough workspace context for the planner to understand the current state and retry where appropriate.
- **FR-050**: While new semester or revision context is loading, the workspace MUST NOT combine its identifying label or summaries with calendar records retained from a different context.
- **FR-051**: If only part of the workspace data is unavailable, the workspace MUST identify each affected section or metric, preserve usable verified context, and prevent unavailable values from contributing to totals or being shown as current.
- **FR-052**: If an initial load or later refresh fails, the workspace MUST preserve the intended semester and revision selection, identify whether any visible data is last known rather than current, and provide a retry without mutating schedule data.
- **FR-053**: The workspace MUST provide distinct states for no semester selected, no lifecycle revision, a loaded revision with no scheduled sessions, no active issues, no matching filter results, loading, partial data, initial failure, and refresh failure.
- **FR-054**: At supported narrow or zoomed presentations, the planner MUST retain access to every calendar mode, date control, filter, operational summary, session detail, trace path, and existing correction or lifecycle action without navigation or controls covering one another.
- **FR-055**: This feature MUST NOT add pointer-only drag, drop, resize, duplicate, split, merge, or automatic placement interactions. Existing explicit correction actions remain the only in-scope path for schedule mutation.
- **FR-056**: The workspace MUST introduce concepts from `docs/designs/resource-planner-calendar-screen-reference.png` gradually and adapt them to the product's established terminology and behavior; visual resemblance MUST NOT override requirements or add unsupported controls.
- **FR-057**: The shared shell and application navigation MUST remain consistent with `docs/designs/resource-planner-unified-navigation-ground-truth.png`. During gradual migration, the existing Courses overview MUST remain usable until it becomes the unified workspace's List view and its filters, List and Weekly review outcomes, alerts, summaries, and correction paths pass parity verification; after that point, no separate legacy overview presentation remains.
- **FR-058**: The feature MUST NOT add lecturer access, authentication, new optimization or exam-generation behavior, external synchronization, external delivery, new source-data administration, independent course publication, or changes to Published immutability.
- **FR-059**: When Current Published is selected, the workspace MUST recalculate applicable validation against current holiday, room, resource, and other planning data while preserving the revision's captured sessions, course totals, relationships, and identifying context unchanged.
- **FR-060**: Current Published validation and affected operational summaries MUST evaluate only the teaching and exam sessions contained in the Current Published revision and MUST NOT include, compare against, or count sessions from an active Working or historical revision.
- **FR-061**: Every warning produced by revalidating Current Published MUST be identified as current validation rather than captured Published content and MUST NOT imply that the Published snapshot was modified.

### Accessibility Requirements

- **AR-001**: Every calendar mode, date control, filter, summary, calendar item, detail control, retry action, and available correction or lifecycle action MUST be reachable and operable with a keyboard without requiring pointer input.
- **AR-002**: Keyboard focus MUST follow a predictable sequence, remain visibly identifiable, move into opened detail or drilldown context, and return to a predictable initiating or nearby element when that context closes or its initiating record disappears.
- **AR-003**: Teaching sessions, exam sessions, holidays, selected revision state, current-publication designation, warnings, active filters, selected items, and focus MUST each be distinguishable without relying on color alone.
- **AR-004**: Text and essential identifying information MUST have a contrast ratio of at least 4.5:1 against its background, and focus indicators, boundaries, warning symbols, and other essential non-text controls or states MUST have a contrast ratio of at least 3:1 against adjacent colors.
- **AR-005**: The workspace MUST remain understandable and operable at up to 200% text zoom and at a viewport width equivalent to 320 CSS pixels without loss of records, summaries, or actions.
- **AR-006**: Calendar dates, times, visible ranges, session kinds, item names, warnings, selected state, and revision context MUST be exposed with understandable text and programmatic relationships so spatial position is not the only way to interpret a session.
- **AR-007**: Overlapping or simultaneous sessions MUST remain individually discoverable and distinguishable by keyboard and assistive technology even when their visual positions overlap or are condensed.
- **AR-008**: Operational summaries MUST expose an understandable metric name, value or unavailable state, scope, and activation purpose; after drilldown, the relationship between the aggregate and contributing records MUST be communicated.
- **AR-009**: Loading, partial-data, failure, successful refresh, and action-result messages that materially change the operational context MUST be communicated without unexpectedly moving focus or requiring visual observation alone.
- **AR-010**: Calendar navigation and state changes MUST not depend on motion, and any motion used MUST not be necessary to understand the selected date, mode, revision, item, warning, or completed action.
- **AR-011**: The FS-018 primary navigation MUST remain keyboard-operable, semantically current, and unobstructed while the workspace and any narrow-screen detail or filter presentation is open.

### Responsive and Failure States

- **RS-001 — Wide workspace**: The calendar, operational summaries, filters, and selected detail may be visible together when space permits, while the FS-018 navigation and page controls remain unobstructed.
- **RS-002 — Narrow workspace**: Calendar content takes a readable primary position; summaries, filters, and detail remain reachable through clearly labeled controls or sequential regions, with the same data, revision context, and actions as the wide state.
- **RS-003 — Dense calendar**: When a date contains more items than fit legibly, the workspace exposes the total and a keyboard-operable path to every item rather than clipping or silently omitting records.
- **RS-004 — Loading**: The intended semester and revision are identified, progress is communicated, and previous-context data is not represented as belonging to the pending context.
- **RS-005 — Empty**: No-semester, no-revision, no-session, no-issue, and no-filter-match states use distinct explanations and only the actions valid for that state.
- **RS-006 — Partial data**: Verified sections remain available, each unavailable section is identified, totals exclude unavailable contributions, and the workspace states that the complete semester status cannot yet be confirmed.
- **RS-007 — Initial failure**: No unverified records or zero summaries are presented as current; the intended context and retry path remain available.
- **RS-008 — Refresh failure**: Retained information is labeled last known, failed portions are identified, the selected context is preserved, and retry does not change domain data.
- **RS-009 — Recovery**: A successful retry replaces last-known or unavailable states as one coherent refreshed context and removes obsolete failure messaging.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for each implemented user story where automated testing is practical.
- **TR-002**: Revision-context coverage MUST verify all no-revision, Working-only, Published-only, and coexisting Working/Current Published cases, including default selection, complete context switching, read-only publication, Ready for review semantics, current revalidation of Published sessions without changing captured content, exclusion of Working sessions from Published validation, and prevention of mixed-revision displays.
- **TR-003**: Calendar coverage MUST verify Week, Day, Month, and List modes; semester-bound date navigation; boundary dates; every teaching and exam occurrence; holiday context; dense dates; and preservation of context across mode changes.
- **TR-004**: Filter coverage MUST verify each filter independently and in combination, active-filter communication, course contexts without sessions, room-filter treatment of remaining units, exam-only treatment, no-match and clear behavior, and absence of domain-data mutation.
- **TR-005**: Aggregation coverage MUST verify unscheduled unit and 45-minute-hour conversion, distinct conflict-pair/type counting, distinct capacity-session counting, retention of latest applicable failure outcomes across reloads and later visits, supersession only by the same course, operation kind, and revision, zero versus unavailable, and distinct-course needs-review counting against independently prepared expected results.
- **TR-006**: Traceability coverage MUST verify that every count reconciles with its contributing records, including off-screen dated sessions, non-dated course outcomes, conflict pairs, multi-condition courses, and restoration after clearing a drilldown.
- **TR-007**: Detail and action coverage MUST verify teaching and exam information, Working-versus-Published action availability, invocation of established correction and lifecycle workflows, refreshed saved-state results, and preservation after cancel, failure, or stale actions.
- **TR-008**: State coverage MUST verify every empty, loading, partial-data, initial-failure, refresh-failure, last-known, retry, and recovery state without false zero values or cross-context data mixing.
- **TR-009**: Accessibility coverage MUST verify keyboard completion of every primary workflow, logical and visible focus, non-color distinctions, programmatic calendar and metric context, simultaneous-session access, message communication, 200% text zoom, and a width equivalent to 320 CSS pixels.
- **TR-010**: Responsive coverage MUST verify that all records and actions remain reachable in wide, narrow, and dense-calendar states while the FS-018 navigation and page controls remain unobstructed.
- **TR-011**: Regression coverage MUST verify that FS-009 remaining units and manual actions, FS-010 outcomes, FS-011 holiday behavior, FS-012 exam behavior, FS-013 lifecycle and immutable publication, FS-018 navigation, and required existing Courses overview outcomes remain unchanged when that overview becomes the unified workspace's List view.
- **TR-012**: Scope coverage MUST verify the absence of a second session-list presentation, drag, drop, resize, duplicate, split, merge, automatic repair, new optimization, lecturer access, external synchronization, a second Dashboard destination, and independent course publication.
- **TR-013**: Any exception to automated test-first work MUST document the reason and manual verification path in the implementation plan.

### Key Entities

- **Semester Workspace Context**: The selected semester together with exactly one selected revision context, visible date period, calendar mode, active filters, selected operational drilldown, and selected session or course detail.
- **Revision View Context**: Either the one active Working revision or the one Current Published revision for the semester, including stable identity, lifecycle state, working/current designation, mutability, schedule content, and applicable validation context. Current Published retains its captured content while exposing a clearly labeled validation view recalculated from current planning data.
- **Calendar Occurrence**: A teaching session or exam positioned by its scheduled date and time and associated with its course, cohort, lecturer, room, revision, session kind, and current validation context.
- **Course-Semester Operational Context**: One course's planning state within the selected revision, including total teaching units, scheduled teaching units, remaining units, related sessions and exam, latest applicable planning outcomes, current issues, and needs-review reasons.
- **Operational Summary**: A revision- and filter-scoped aggregate for unscheduled work, conflicts, capacity issues, planning failures, or schedules needing review, including its availability state and complete set of contributing records.
- **Validation Finding**: A current established conflict, capacity, holiday, exam-validity, or other validation condition associated with one or more affected records; the workspace presents and aggregates it without redefining its owning rule.
- **Planning Outcome Reference**: The retained latest applicable completed generation, optimization, or exam-planning outcome for a course, operation kind, semester, and revision context, including classification and substantiated reasons where available; it remains available across visits until a newer applicable outcome for the same course, operation kind, and revision supersedes it.
- **Filter Context**: The non-mutating combination of planning, resource, session, lifecycle, validation, and drilldown conditions used to derive the visible result set and filtered summaries.
- **Trace Target**: A course, session, exam, validation finding, or planning outcome that contributes to a metric and can be reached from that metric without changing revision context.

## Dependencies

- **FS-009 — Manual Session Creation, Deletion, and Remaining Units** supplies authoritative teaching-unit progress and existing manual creation and deletion workflows.
- **FS-010 — Conflict-Aware Semester Optimization** supplies coordinated planning outcomes, failure and stale classifications, blocking reasons, and distinct conflict-pair/type semantics.
- **FS-011 — Institution-Wide Holiday Calendar and Avoidance** supplies current named holidays and holiday-affected session warnings.
- **FS-012 — Conflict-Aware Exam Scheduling** supplies distinguishable exam sessions, exam validity context, exam outcomes, and existing exam correction actions.
- **FS-013 — Versioned Review and Publication Lifecycle** supplies Working and Current Published revision identity, lifecycle state, immutability, history, and established lifecycle actions.
- **FS-018 — Unified Application Navigation** supplies the one shared Schedule and Academic Data navigation shell that this workspace reuses.
- The existing Courses overview becomes the unified workspace's List view. Its filters, List and Weekly review outcomes, alerts, result summaries, and editors remain behavioral references and required parity targets during gradual migration.
- No external service or new integration is required by this slice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance cases, every calendar item, summary value, detail, warning, and available action shown at one time belongs to the same visibly identified semester revision context.
- **SC-002**: In 100% of prepared aggregation cases, unscheduled units and instructional time, conflict findings, capacity-affected sessions, applicable failures, and distinct needs-review courses exactly match independently established expected results, with unavailable data never reported as zero.
- **SC-003**: In 100% of traceability cases, activating a non-zero operational metric exposes all and only its contributing courses, sessions, exams, findings, or outcomes, and every contributor can be identified within two interactions from the metric.
- **SC-004**: In an unaided usability review with at least 10 representative planner users or designated acceptance reviewers, at least 90%, rounded up to the next whole participant, correctly identify the selected semester, whether they are viewing Working or Current Published, the lifecycle state, and the largest current operational issue within 30 seconds.
- **SC-005**: In the same review, at least 90% of participants locate a named teaching session, a named exam, a course with remaining units, and one needs-review reason within two minutes without leaving the workspace or receiving guidance.
- **SC-006**: In the same review, at least 90% of participants follow a summary to an affected record and invoke the correct existing correction or planning path on their first attempt without attempting to mutate Published content.
- **SC-007**: In 100% of keyboard acceptance paths, the planner can select semester and revision context, navigate dates, use every mode and filter, activate every summary, inspect every session kind, invoke every available existing action, retry failures, and return without pointer input or focus loss.
- **SC-008**: In 100% of acceptance checks using the supported screen-reader and desktop-browser combination, calendar mode and visible date range, selected revision context, session kind and identifying detail, warning state, metric name and value or unavailability, and opened detail context are announced accurately.
- **SC-009**: At a viewport width equivalent to 320 CSS pixels and at text zoom up to 200%, 100% of required records, summaries, filters, modes, detail fields, retry actions, and existing correction or lifecycle actions remain reachable and operable without overlap from application navigation.
- **SC-010**: For a reference semester containing up to 500 teaching and exam occurrences, 50 current holidays, and 100 course-semester contexts, at least 95% of initial workspace loads present a complete usable calendar and operational summary within 3 seconds, and 100% present either that result or an actionable failure state within 10 seconds.
- **SC-011**: At the same reference scale, at least 95% of calendar mode, date-period, filter, summary-drilldown, and revision-context changes present the updated visible state within 1 second, and 100% do so or present an actionable failure within 3 seconds.
- **SC-012**: At the same reference scale, at least 95% of successful existing correction or lifecycle actions refresh all affected visible calendar and summary context within 2 seconds after the action completes, without requiring the planner to reopen the semester.
- **SC-013**: In 100% of loading, partial-data, initial-failure, refresh-failure, and retry acceptance cases, no value from another context is presented as current, no unavailable metric is represented as zero, and no saved domain data changes solely because the workspace failed or retried.
- **SC-014**: All applicable acceptance scenarios from FS-009 through FS-013 and FS-018, plus the required existing Courses overview review outcomes, continue to pass after the existing overview becomes the unified workspace's List view.
- **SC-015**: In 100% of scope-verification cases, schedule mutation remains available only through established explicit actions; no second session-list presentation, drag, drop, resize, duplicate, split, merge, automatic repair, new optimization, lecturer access, external synchronization, or second Dashboard destination is introduced.
- **SC-016**: In 100% of planning-outcome retention cases, the latest applicable outcome remains available after reload and a later workspace visit, is visible only in its associated revision context, and is replaced only by a newer applicable outcome for the same course, operation kind, and revision.
- **SC-017**: In 100% of post-publication planning-data change cases, Current Published retains exactly the same captured sessions, course totals, relationships, and identifying context while its current validation warnings and affected summaries reflect the changed planning data, are labeled as current, and exclude every Working or historical session.

## Assumptions

- The first delivery uses Week as the primary operational calendar, with Day and
  Month available for focused and broad date navigation and List retained for
  the existing dense review use case.
- Drag, drop, and resize remain out of scope because their scheduling,
  validation, confirmation, keyboard-equivalent, and revision semantics have
  not been confirmed. Their visual presence in the reference image does not
  authorize them.
- "Needs review" is a derived operational exception label for a course with at
  least one current actionable condition defined in FR-038. It is not a new
  lifecycle state, approval requirement, lecturer-review result, or publication
  gate.
- Ready for review retains the exact FS-013 meaning: an optional informative
  state for the one active Working revision. It does not indicate that a course
  has been approved or that every operational issue is resolved.
- Remaining instructional hours are a presentation of teaching-unit coverage,
  using 45 minutes per unit. They are not elapsed session duration and exclude
  the 10-minute breaks used when calculating default multi-unit session times.
- Conflict aggregation follows FS-010: each unordered overlapping session pair
  is counted once for each applicable lecturer, room, or cohort conflict type.
- A room-capacity aggregate counts affected scheduled occurrences, not alert
  messages, courses, rooms, or missing seats.
- The product retains the latest applicable completed planning outcome for each
  course, operation kind, semester, and revision across reloads and later
  workspace visits. A newer applicable outcome for the same course, operation
  kind, and revision supersedes it; outcomes from other contexts do not.
  Superseded outcomes remain outside the current operational total.
- Planning-outcome coverage is measured at the included eligible-course level,
  not by assuming every possible operation kind must have been attempted for
  every course. A retained reliable completed outcome for any applicable
  established operation gives its course coverage; every retained failed
  outcome still contributes separately to the failure count.
- Course-level remaining work may be narrowed by course, cohort, lecturer, and
  study-type context. A room filter may narrow the affected course set through
  scheduled sessions but never assigns the remaining work to that room.
- The planner-only access model remains authoritative. This feature neither adds
  authentication nor exposes any workspace content or action to lecturers.
- The Current Published snapshot remains immutable and stable under FS-013.
  Its sessions, captured course totals, relationships, and identifying context
  never change through workspace validation. Applicable warnings are
  recalculated against current planning data, explicitly labeled as current
  validation, and derived only from sessions in the Published revision, never
  from a coexisting Working or historical revision.
- The existing correction and lifecycle workflows remain the single source of
  truth for mutations. The workspace may open them with selected context but
  does not duplicate their business rules.
- The authoritative calendar image is visual inspiration for information
  hierarchy, calendar emphasis, operational summaries, filters, and detail
  context. Its branding, mock data, Dashboard destination, Professor
  terminology, duplicate action, drag instructions, and exact geometry are not
  requirements.
- The authoritative navigation image governs the shared application shell
  through FS-018. FS-014 changes the Schedule workspace content rather than the
  primary navigation hierarchy.
- The existing Courses overview is adapted into, and becomes, the unified
  workspace's single List view rather than being rebuilt or duplicated. It
  remains usable during gradual migration until its required semester filters,
  List and Weekly review outcomes, alert visibility, result summaries, and
  correction paths pass parity verification inside the unified workspace; only
  then may the separate legacy presentation be removed.
- The supported acceptance scale is 500 scheduled teaching and exam
  occurrences, 50 current institution holidays, and 100 course-semester
  contexts in one semester. Larger-scale policy may be established separately
  without changing the functional meaning of this slice.
- The product owner supplies at least 10 representative planners or designated
  acceptance reviewers for the moderated success criteria. Automated work may
  finish beforehand, but those criteria cannot be reported as passed without
  actual participants.
