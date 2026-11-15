# Feature Specification: Time-Grid Calendar with Teaching Window Context

**Working Branch**: `codex/i-014-time-grid-calendar` (implementation; original planning on `master`)

**Created**: 2026-11-12

**Status**: Implemented — automated gates pass; observed acceptance T044/T045/T049 remains pending. See [validation.md](validation.md).

**Slice ID**: I-014

**Input**: User description: "Show planned hours relative to applicable teaching windows in day/week hourly grids and a compact month calendar. Preserve List, context, details, correction actions and all business behavior. Specify I-014 only, including accessible presentation, gaps, overruns, dated/intensive windows and multiple calendars."

**Product source**: [I-014 in Feature_slices.md](../../docs/planning/Feature_slices.md#i-014--time-grid-calendar-with-teaching-window-context). The user explicitly selected the directory `I-014-time-grid-calender`; the slice identifier remains I-014.

**Visual references**: [Week](../../docs/designs/time-grid-calendar-reference-2026-11-12.png), [day](../../docs/designs/day-calendar-reference-2026-11-12.png), and [month](../../docs/designs/month-calendar-reference-2026-11-12.png), supplied on 12.11.2026. These illustrate proportional hourly blocks and compact dated entries. Exact Outlook styling, colors, spacing and behavior are not required.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Sessions Against Permitted Hours (Priority: P1)

A planner opens Day or Week and sees when teaching takes place, its duration, gaps between sessions, and portions outside the applicable teaching window.

**Why this priority**: Direct comparison of planned and permitted hours is the core outcome.

**Independent Test**: Display an in-window session, two separated sessions, and the supplied overrun example. Compare placement with labeled hours and inspect session/window text in both hourly modes.

**Acceptance Scenarios**:

1. **Given** Höber, Angelika has a session on 26.06.2027 from 12:15 to 17:20 against the applicable cohort window 08:00–16:00, **When** Day or Week shows that date, **Then** the block starts at 12:15, ends at 17:20, visibly crosses 16:00, and identifies the outside portion as 16:00–17:20, lasting 1 hour 20 minutes, with session, date and calendar identified.
2. **Given** a window of 08:00–16:00 and a session of 09:00–10:30, **When** displayed, **Then** its 90-minute block lies entirely within the window without a new window-violation indication.
3. **Given** sessions of 09:00–10:00 and 12:00–13:00 within 08:00–16:00, **When** displayed, **Then** 10:00–12:00 remains visibly empty within permitted hours and is not described as guaranteed lecturer/room availability or schedulable capacity.
4. **Given** a session wholly outside all applicable windows or on a date without permitted hours, **When** displayed, **Then** the complete session remains reachable on the time grid with explicit outside-window context; it is neither hidden nor shortened.
5. **Given** early/late sessions and overlapping sessions, **When** the planner scrolls through the day, **Then** all actual start/end times are reachable and every overlapping block is selectable without changing its represented time or duration.

---

### User Story 2 - Understand Which Window Applies (Priority: P1)

A planner compares several cohorts without mistaking one cohort's permission for another's or confusing weekly windows with dated/intensive opportunities.

**Why this priority**: Incorrect window attribution would mislead planning decisions.

**Independent Test**: Use two calendars with different hours, a dated-only intensive opportunity and a course with an effective override. Compare presentation with existing authoritative windows and validation results.

**Acceptance Scenarios**:

1. **Given** a dated intensive window permits Monday teaching while weekly windows permit Friday/Saturday, **When** that Monday and the following Monday are displayed, **Then** only the recorded date shows the dated opportunity, labeled with date, hours, calendar and intensive status.
2. **Given** calendars A and B permit 08:00–16:00 and 10:00–18:00 respectively on one date, **When** both are shown, **Then** their windows and sessions are separately labeled; an A session at 16:30 remains outside A's permission even though B permits it.
3. **Given** an active course constraint changes applicable hours under existing precedence, **When** its session is inspected, **Then** effective hours/source agree with existing validation; a generic cohort background is not presented as overriding that course's effective context.
4. **Given** overlapping or adjoining weekly/dated windows, **When** shown, **Then** source identities remain inspectable and their appearance does not imply combined permission for a longer session than existing rules allow.
5. **Given** Working and Current Published contexts, **When** the planner switches between them, **Then** session/window/validation presentation follows each selected context's existing semantics and shows revision identity; unavailable historical windows are labeled unavailable rather than replaced silently with current permission.
6. **Given** a window-context load or refresh failure, **When** sessions are available, **Then** sessions remain inspectable, missing/outdated context is explicit with retry access, and unknown hours are not represented as confirmed permitted or prohibited hours.

---

### User Story 3 - Survey a Month and Open Existing Actions (Priority: P2)

A planner surveys the month, opens crowded dates, and moves to hourly comparison or established session details without losing semester, revision or filters.

**Why this priority**: The month overview and retained workflows make the presentation useful within the existing workspace.

**Independent Test**: Open a month containing empty dates, partial windows, an outside-window session and a crowded date. Access every entry and existing detail/correction action, then compare the same filtered set with List.

**Acceptance Scenarios**:

1. **Given** timed sessions, **When** Month opens, **Then** days form a dated grid with compact entries showing actual start/end times and session titles; proportional hourly placement belongs to Day/Week.
2. **Given** more entries than a day cell can show, **When** displayed, **Then** an additional-entry control gives the exact hidden count and opens all filtered entries for that date in chronological order, each linked to existing detail.
3. **Given** dates with and without sessions, **When** Month is shown, **Then** empty dates show only their date and any holidays; session cards identify their cohort with a compact abbreviation and full-name tooltip. Window details remain available through session inspection without calendar placeholders in day cells.
4. **Given** a Month date or session, **When** activated, **Then** the date opens Day for that date or the session opens its established pane respectively, preserving semester, revision and filters.
5. **Given** a selected session in any mode, **When** established correction actions are used, **Then** existing authority, save/cancel, unsaved-change, validation and refresh behavior applies, and Published remains read-only.
6. **Given** filters and revision context, **When** switching among Day, Week, Month and List or navigating dates, **Then** existing context rules are preserved and saved sessions, windows and revision state do not change.

---

### User Story 4 - Compare Hours Accessibly (Priority: P2)

A planner using keyboard, assistive technology, enlarged text or a narrow screen can identify the same windows/sessions and reach the same actions.

**Why this priority**: Comparison and correction must remain usable across supported ways of accessing the workspace.

**Independent Test**: Complete overrun inspection and crowded-month navigation with keyboard only, without color, at 320 CSS pixels and at 200% text enlargement; inspect the textual equivalent with assistive technology.

**Acceptance Scenarios**:

1. **Given** indistinguishable availability colors, **When** inspecting the grid/legend, **Then** labels or patterns distinguish permitted/outside-window periods, blocks and unknown context; exact session/window hours and overrun text are available without hover.
2. **Given** keyboard-only operation, **When** changing mode/date/filter, reaching sessions/overflow, opening details and closing them, **Then** every action works with visible focus, no trap, and focus returns to its origin or a logical successor if the origin no longer exists.
3. **Given** a narrow viewport or enlarged text, **When** comparing dates/calendar groups, **Then** a labeled scrollable grid and Day navigation keep all dates, hours, entries and controls reachable without overlapping controls or lost calendar identity.
4. **Given** assistive technology, **When** a session/window is reached, **Then** date, calendar, actual interval, applicable hours/source and existing validation context are readable in logical order without duplicate session announcements from background decoration.

### Edge Cases

- Exact window-boundary starts/ends: no invented overrun; adjacent sessions retain existing non-overlap semantics.
- Very short sessions and non-hour times: preserve true geometry and expose readable labels separately rather than exaggerating duration.
- Three or more concurrent sessions, including identical intervals: each remains discoverable and selectable.
- Disjoint windows: retain the outside-window gap and show a session spanning it without changing the existing single-containing-window validation rule.
- Marker-only edits: refresh intensive source labeling without inventing permission or validity changes.
- Empty filtered results: retain each date once as an empty column/cell, without calendar/window placeholders. Dates with sessions retain the applicable cohort/calendar profile columns.
- All outside-window entries hidden in Month overflow: retain an affected-entry cue/count and access to those entries.
- Sessions spanning midnight, if existing data supports them: show dated continuation segments linked to the same session and full interval. Unsupported/malformed intervals retain existing data-error behavior and are never repaired by viewing.
- Context changes during loading: do not compare old sessions with newly selected windows; loading/outdated context remains explicit.
- Exams or sessions without applicable teaching-window context: preserve existing timed entries and findings, identifying non-applicable/unknown context without introducing teaching-window exam rules.
- Window edits after publication: preserve existing published/history semantics; explicitly distinguish current advisory context where already supported, without inventing snapshots or rewriting facts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The planner workspace MUST offer Day and Week hourly grids, a Month grid of days and the retained List view. Day focuses on one date; Week shows all seven dates including weekends in adjacent columns; Month identifies weekdays, dates, month/year and adjacent-month dates.
- **FR-002**: Day/Week MUST position each block at its actual start/end minute on a shared linear time scale. Equal elapsed intervals MUST have equal vertical extent at the same scale, including existing breaks in the saved interval. Readability aids MUST NOT alter represented duration.
- **FR-003**: The full 00:00–24:00 day MUST be reachable by vertical scrolling with hourly labels and identifiable date/calendar context. Opening a new date range MUST initially reveal the earliest known session or applicable window start, or 08:00 if neither exists. Permitted hours MUST NOT clip the scrollable range. Visible dates/groups MUST share the same scale.
- **FR-004**: Concurrent sessions MUST use separately selectable side-by-side positions within their date/calendar group without covering each other. Insufficient width MUST allow labeled horizontal scrolling to every block. Layout MUST NOT add, remove or reinterpret existing conflict findings.
- **FR-005**: Permitted and outside-window periods MUST use different colors, a visible legend and non-color cues/textual equivalents, with session blocks distinguishable over both. Unknown/outdated and non-applicable context MUST be labeled distinctly. Available means permitted by existing teaching-window context, not guaranteed schedulability.
- **FR-006**: Presentation MUST reuse existing effective constraints, cohort relationships, weekly and dated/intensive windows, availability results and validation behavior, including precedence and active/inactive handling. Dated windows MUST apply only on their recorded date. Intensive labels MUST confer no extra permission. Source windows MUST remain inspectable without implying new combined permission. Lecturer/room availability MUST never extend cohort permission.
- **FR-007**: Multiple calendars/cohorts MUST have separately labeled window/session groups per date on the same hourly scale, without pooled permissions. Every session MUST identify its calendar/cohort. Course-specific effective hours/source differing from the group background MUST be available alongside session inspection without leaving the selected context and MUST NOT be contradicted by the generic background.
- **FR-008**: Every matching saved session MUST remain reachable in full, including before, after, between or wholly outside windows. Existing window findings MUST remain associated with the correct session and have non-color cues and exact hours. A straightforward boundary overrun MUST expose its outside interval and elapsed duration, including 16:00–17:20 / 1 hour 20 minutes for the supplied example. This explanation MUST NOT introduce a new validation decision or severity.
- **FR-009**: Session and window gaps MUST retain proportional extent. Empty permitted time MUST NOT be labeled confirmed resource availability, remaining capacity or a guarantee that generation can fill it.
- **FR-010**: Month MUST show compact start/end times and titles in chronological order, with consistent ordering for equal starts. Overflow MUST give an exact hidden count and a labeled control exposing every filtered entry for that date. No entry may become inaccessible through truncation.
- **FR-011**: Month MUST show dated sessions and holidays without calendar/window summaries or empty-state text inside otherwise empty dates. Each session MUST display a compact cohort abbreviation with its full name available. Exact hours/source MUST remain accessible through session activation. Dates with existing window findings MUST retain an affected-entry cue/count even when affected sessions are in overflow. Month MUST NOT imply hourly proportional placement or uniform permission across calendars.
- **FR-012**: Activating a Month date MUST open Day for that date; activating a session in any mode MUST open its established pane. Previous/next MUST move by the mode's period; Today MUST include today's date; established direct-date navigation MUST remain available. Semester, revision, filters and selected-date context MUST survive mode changes, including List, under existing rules.
- **FR-013**: Semester and selected revision identity/lifecycle MUST remain visible. Session/window/validation context MUST follow existing selected-context semantics: current active constraints remain current where existing validation requires them, while published/history evidence MUST NOT be rewritten or relabeled. Missing historical window context MUST be reported as unavailable, not fabricated. No new snapshot or revision-persistence behavior is required.
- **FR-014**: Existing filters MUST select the same sessions in every mode. Cohorts MUST support checkbox selection of any subset, combined by OR within cohorts and AND with other filters including lecturer. No selected cohorts means all cohorts. Refresh MUST remove stale choices and reset MUST restore all. Day/Week MUST retain every date, showing cohort/calendar-profile columns only where matching sessions exist on that date, or one empty date column otherwise. Remove the separate expandable source overview; retain source facts through session inspection and accessible block descriptions.
- **FR-015**: Established session details/corrections MUST preserve access, unsaved-change, save/cancel, stale-state, validation, refresh and publication rules. Viewing, scrolling, switching modes, selecting, navigating and filtering MUST save no session/window/availability/lifecycle changes. Drag/drop and resize editing MUST NOT be added.
- **FR-016**: All controls, sessions, window explanations, overflow and detail actions MUST support keyboard operation, logical focus order, visible focus and standard activation keys. Keyboard scrolling MUST reach every grid region. Temporary content MUST receive focus on opening and restore it logically on closing. Required facts MUST be accessible on focus/activation without hover-only information.
- **FR-017**: Textual equivalents MUST identify date, calendar/cohort, session title/actual interval, applicable window intervals/source, relevant intensive status and existing findings or unknown state. Accessible labels/reading order MUST preserve these relationships without relying on color or spatial position alone. List MUST remain available but MUST NOT be the only access to essential window facts.

  Implementation clarification (2026-11-15): when the established session pane
  becomes modal, its accessible subtree must contain the selected saved session's
  read-only window context in both detail and editing modes; inert calendar
  siblings cannot serve as the only source disclosure.
- **FR-018**: At 320 CSS pixels and 200% text enlargement all modes/facts/actions MUST remain reachable. Grids MAY scroll horizontally; surrounding controls MUST remain readable without mutual overlap. Narrow layouts MUST retain date/calendar identity and Day navigation without silently removing Week/Month access. Existing responsive pane behavior MUST remain intact.
- **FR-019**: Loading, empty, failed and outdated context MUST be distinguishable from confirmed outside-window hours. Available sessions MUST remain inspectable during window failure, with retry and no false valid/invalid claim. Existing refresh MUST update presentation without mixing contexts or overwriting unsaved editor input.
- **FR-020**: This slice MUST change presentation only. It MUST NOT change scheduling, generation, optimization, validation decisions/severity, availability determination, precedence, persistence, publication or authorization. It MUST NOT add Outlook integration, automatic rescheduling, capacity diagnostics, resource-availability overlays, new permission controls or an optimization prerequisite.

### Test Requirements *(mandatory)*

This specification explicitly requests test-first delivery under the project constitution. Verification requirements below do not select implementation technology.

- **TR-001**: Create/update tests before production changes for each story where automated testing is practical. Record any exception and manual verification path in the plan.
- **TR-002**: Verify minute-accurate proportional geometry, full-day scrolling, concurrent blocks, all calendar modes, counted overflow, filter parity and the 80-minute example. Include in-window, wholly outside, exact-boundary, empty-gap and weekend cases.
- **TR-003**: Compare presentation against authoritative existing outcomes for weekly, dated-only, intensive, overlapping/adjacent and course-override windows, multiple calendars, unknown data and Working/Published context. Do not introduce alternative validation to satisfy display tests.
- **TR-004**: Verify unchanged scheduling/validation/availability results and zero saved-data changes from viewing/navigation/filtering. Verify existing edit/cancel, warning severity and immutable publication behavior through retained actions.
- **TR-005**: Verify keyboard completion, focus return, non-color information, assistive-technology relationships, 320 CSS pixels and 200% text enlargement, including dense overlaps and overflow. Record visual/manual observations for geometry, readable contrast and responsiveness where automated checks cannot establish usability.
- **TR-006**: Planning MUST identify frontend, backend and shared-contract impacts, including no-change areas, and name relevant project verification commands. Reuse existing data/behavior contracts; missing presentation facts MUST be recorded as a planning dependency rather than silently expanding business logic scope.

### Key Entities *(include if feature involves data)*

- **Calendar View Context**: Selected semester, revision/lifecycle, mode, date/period and filters; viewing context does not create a saved schedule revision.
- **Planned Session**: Existing teaching/exam record with identity, title, cohort/calendar, resources, date, actual interval and validation; a block/entry references it without changing it.
- **Applicable Teaching Window Context**: Existing effective intervals and source identities for a course/calendar/date, including weekly/dated origin, intensive marker and known/current/unknown status under established semantics.
- **Calendar Identity**: Cohort/calendar and course relationship associating sessions with their own permissions when several calendars are visible.
- **Window Finding**: Existing session-associated validation, presented with exact hours and explanatory interval/duration where available; no new persisted finding type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In Day/Week, 100% of reference sessions appear at exact start/end minutes with proportional duration; none is hidden or shortened for falling outside a window. The supplied example visibly and textually identifies an 80-minute overrun.
- **SC-002**: In every in-window, gap, boundary, outside, dated/intensive, override and two-calendar acceptance case, displayed permission/finding states agree with authoritative existing results; zero permissions are attributed to the wrong calendar.
- **SC-003**: In a month with dates containing 0, 1, 5 and 20 filtered sessions, every session is reachable, hidden counts are exact, and affected dates retain finding cues even when all affected entries overflow. All modes/List expose identical matching session identities.
- **SC-004**: In observed review with five representative planners, at least four correctly identify the example's overrun/duration, an in-window session, an empty permitted gap and the applicable calendar within 30 seconds per case, without first opening a generic warning list.
- **SC-005**: Every required navigation/inspection/correction entry action is completable with keyboard only at 320 CSS pixels and at 200% text enlargement. All reference window distinctions and overrun facts remain identifiable without color; no required information depends solely on hover.
- **SC-006**: Across the complete acceptance matrix, viewing/filtering/mode/date/revision navigation produces zero saved session, window, availability or lifecycle changes. Existing generation/validation results, severity and publication protections remain unchanged.

## Assumptions

- Dependencies are FS-014/FS-019 for workspace, navigation, List, pane and actions; FS-005 for effective constraints/validation; I-009 for weekly/dated/intensive semantics. Additional optimization, capacity diagnostics and resource overlays are not prerequisites.
- Feature_slices.md remains authoritative. This specification covers only I-014 and does not close predecessor acceptance work or reorder other slices.
- Presentation defaults resolve the listed clarification topics: scrollable full day with earliest-content positioning (08:00 fallback), seven-day weeks, side-by-side concurrent blocks, exact counted month overflow, session-bearing per-calendar groups, compact month cohort labels and cohort checkbox selection, keyboard activation/focus return and reachable narrow grids. These are documented defaults, not separately confirmed user choices.
- Week boundaries, locale, timezone, date formatting and revision selection retain established application conventions. Dates remain unambiguous and include the year when needed.
- Available/unavailable colors describe existing teaching permission only. Exact colors and final arrangement within these requirements remain design decisions.
- Existing effective constraints and precedence are consumed as delivered, including course-specific replacement/restriction behavior. Presentation must not resolve source differences by inventing rules; planning must identify missing authoritative presentation facts.
- Session duration means the actual saved interval, including existing breaks. No LE conversion, session splitting or new duration business rule is introduced. The example assumes the known effective cohort window 08:00–16:00.
- Published/history uses existing semantics and available evidence. This slice does not assume immutable window snapshots exist. Unknown context stays unknown; current advisory context, if already supported, is explicitly identified.

## User clarification — 15.11.2026

Remove duplicated teaching-window disclosures above Day/Week and inside Month cells. Keep Day/Week geometry, shading and overlapping blocks. Show cohorts side by side when they have matching sessions on the same date, including with a lecturer filter; keep other dates visible once and empty. Month cards show cohort abbreviations derived from the existing cohort name (the catalog has no abbreviation field), with the full name accessible. Checkbox selection works in every mode, navigation, refresh and reset.
