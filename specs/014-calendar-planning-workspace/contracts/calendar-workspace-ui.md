# UI Contract: Calendar Planning Workspace

This contract defines observable behavior shared by the React workspace, the
existing Schedule page, and the backend response. It is not a visual
implementation prescription.

## Authority and placement

- The workspace is content within the existing **Schedule** destination.
- FS-018 remains authoritative for the application shell and primary
  navigation.
- `resource-planner-calendar-screen-reference.png` informs calendar emphasis,
  information hierarchy, filters, summaries, and detail context gradually.
- `resource-planner-unified-navigation-ground-truth.png` governs shared
  navigation.
- Existing Courses overview behavior is authoritative for List parity.
- Reference-image controls that are out of scope—Dashboard navigation,
  lecturer access, duplicate, drag/drop, resize, external sync, and unsupported
  actions—must not appear as functional behavior.

## One workspace, one List

The existing Courses overview becomes the `List` mode of the unified Schedule
workspace. Its required filters, List and Weekly review outcomes, alerts,
result summaries, session review, and established correction/editor paths are
adapted rather than rebuilt.

During gradual migration, the legacy presentation may remain reachable only
until parity tests pass. Once parity passes, there must be no second Courses or
session-list presentation. This migration removes a duplicate presentation
boundary, not the existing behavior or implementation value.

## Revision-context invariant

At any instant, these elements identify the same semester/revision response:

- persistent revision label;
- calendar/List records;
- summaries and availability;
- selected detail;
- warnings;
- current filters and facets;
- mutation/lifecycle action availability.

Context switch behavior:

1. Record the intended Working or Current Published selection.
2. Present it as loading without relabeling old records as the new context.
3. Replace records, summaries, detail, and actions together after one coherent
   response succeeds.
4. On failure, identify any prior response as last known and keep the intended
   selection retryable.

Historical revisions remain in the established lifecycle history, not in this
selector. Published content is read-only. Published warnings are labeled
**Current validation** and do not imply snapshot mutation.

## Modes and date navigation

Week is default. Day, Month, and List are available through native buttons that
communicate selected state programmatically.

- Week/Day/Month expose previous period, next period, current period, and an
  in-semester date choice.
- Current period uses today when it is inside the semester, otherwise the
  nearest semester boundary, with an announced explanation. It is not
  applicable in List and does not reposition that result.
- Navigation preserves semester, revision, filters, and applicable selection.
- Boundary dates outside the semester are identified and never introduce
  another semester's records.
- Teaching and exam occurrences use text/icon/structure in addition to color.
- Dense Month dates show an item count and an operable continuation to every
  occurrence.
- List uses the adapted existing Courses overview.
- No mode or date control mutates domain data.

## Filters

Available facets include course, cohort, lecturer, room, study type, session
type, lifecycle context, and current validation status when the response offers
choices.

- Different filter dimensions combine by intersection.
- Selected choices stay visible.
- Session scope is all, teaching, or exam. Exam-only excludes unscheduled
  teaching work.
- Lifecycle selection switches the permitted revision context; it never blends
  revisions.
- Course/cohort/lecturer/study filters can include a course with remaining work
  and no occurrence.
- Room filters can include a course through a matching scheduled occurrence but
  must not describe its remaining units as assigned to that room.
- A drilldown adds a trace condition while retaining unrelated filters.
- One **Clear filters and drilldown** action restores the complete selected
  revision.
- Filter operations are presentation-only.

## Summaries and traceability

Each metric announces its name, availability/value, and whether it describes
the complete revision or a filtered subset.

- **Unscheduled work**: remaining units, exact instructional hours/minutes, and
  distinct contributing course count. Detail lists total, scheduled, and
  remaining units per course.
- **Conflicts**: distinct finding count. Detail identifies conflict type, both
  affected occurrences, course/date/time, and conflicting resource/cohort.
- **Capacity issues**: distinct affected occurrence count. Detail identifies
  required capacity, assigned room, and current room capacity.
- **Planning failures**: failed retained outcomes only. Stale and unchanged are
  separately identified. Coverage is not applicable with no eligible courses,
  unavailable with no covered eligible course, partial with some covered
  eligible courses, and available only when every eligible course is covered.
  Partial counts are labelled as known incomplete counts. Detail includes
  course, operation kind, and all substantiated reasons.
- **Needs review**: each affected course once, with every qualifying reason.
  Lifecycle state alone never qualifies a course.

Applicability is derived after revision and filter scope: unscheduled work and
needs review require at least one included course, conflicts require at least
one included occurrence, and capacity requires at least one included
capacity-evaluable occurrence. No applicable records is not applicable;
complete evaluation with no contributors is available zero; no verifiable
required source is unavailable; and partial evaluation shows labelled known
incomplete values.

Activating a metric exposes all and only its contributor set. A dated
contributor moves the calendar to its date or opens detail. An undated course or
outcome opens course/List detail without a fabricated date. Clearing drilldown
restores the prior un-drilled context.

Filtered summaries are pure projections of the response's canonical
contributors; the client does not invent validation findings. Tests must
reconcile every displayed value to its visible/linked contributor set.

## Detail and action handoff

Selection opens a labelled detail region/dialog and moves focus into it.
Teaching and exam details expose the information required by FS-009 and FS-012,
the selected revision, and all current findings.

For active Working only, action controls hand off to existing manual creation,
editing, deletion, planning, exam, and lifecycle flows. Their validation,
confirmation, preservation, and stale-state behavior remains unchanged.
Published detail remains inspectable while mutations are absent with an
explanation.

After a successful action, refresh the workspace response atomically. After
cancel/failure/stale result, do not imply success or discard saved context. If
an edited/deleted item disappears, focus moves to the nearest remaining result
or result-set heading and an understandable status message is issued.

## Responsive behavior

- Wide layouts may show summary, calendar, filters, and detail concurrently.
- At 820 CSS pixels or below, and at 200% text zoom, use sequential document
  flow: calendar first, then clearly labelled summary/filter/detail controls or
  regions.
- At 320 CSS pixels, all modes, date controls, filters, summaries, records,
  details, retry controls, and available established actions remain reachable.
- Fixed panels must not cover the FS-018 navigation or workspace controls.
- Spatial calendar placement is supplemented by textual date/time and
  identifying relationships.

## Accessibility behavior

- All controls and occurrences are keyboard-operable with visible focus.
- Mode buttons communicate selected state; date headings label occurrence
  groups; summary controls communicate activation purpose and scope.
- Teaching, exam, holiday, warning, revision, selected, and focus states never
  rely on color alone.
- Simultaneous/overlapping occurrences remain individually discoverable.
- Detail/drilldown gets predictable initial focus and returns focus to its
  initiator or a deterministic nearby target.
- Loading, partial, failure, successful refresh, and mutation results are
  announced without unexpected focus movement.
- Text contrast is at least 4.5:1 and essential non-text contrast at least 3:1.
- No required understanding depends on motion.

## Empty and failure behavior

Distinct presentations are required for:

- no semester;
- no lifecycle revision, with established Start Draft path;
- loaded revision with no occurrences;
- available metrics with zero contributors;
- no active issues;
- no filter matches, with clear action;
- loading;
- partial availability;
- initial failure, with retry and no unverified values;
- refresh failure, with explicit last-known data;
- recovered current data.

Unavailable and not-applicable values are never rendered as zero. Verified
partial sections remain usable, while partial counts are labelled incomplete
and the UI states that complete semester status cannot be confirmed.

The no-revision response contains no courses, occurrences, holidays, findings,
planning outcomes, or filter facets. Every operational summary is not
applicable with `no_revision` scope; the UI presents the established Start
Draft state rather than rendering those empty arrays as a loaded calendar.

## Parity evidence

Before the separate legacy overview presentation can be retired, automated and
manual evidence must show that List mode preserves:

- semester and revision context;
- existing filters and List/Weekly review outcomes;
- alerts and result summaries;
- session selection and detail;
- edit/delete/manual creation/planning/editor handoffs;
- cancel, stale, failure, and refresh behavior;
- keyboard, narrow-screen, and FS-018 navigation access.
