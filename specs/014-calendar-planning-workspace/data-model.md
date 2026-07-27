# Data Model: FS-014 Calendar Planning Workspace

**Date**: 2026-07-23  
**Research basis**: [research.md](research.md)  
**API contract**: [contracts/calendar-workspace.openapi.yaml](contracts/calendar-workspace.openapi.yaml)

Only `PlanningOutcome` is a new relational entity. The other entities below
are revision-scoped read models or client presentation state. They do not
duplicate schedule ownership from FS-009 through FS-013.

## Persisted entity: PlanningOutcome

Stores the latest reliable completed per-course result for one operation kind
and one schedule revision.

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Primary key |
| `schedule_revision_id` | integer | Required foreign key to `schedule_revisions`; included in unique key |
| `course_id` | integer | Required foreign key to `courses`; included in unique key |
| `operation_kind` | enum text | `single_course_generation`, `multi_course_generation`, `semester_optimization`, or `exam_generation`; included in unique key |
| `classification` | enum text | `successful`, `failed`, `stale`, `unchanged`, or `skipped` |
| `source_status` | text | Required source operation status retained without reinterpretation |
| `result_payload` | JSON | Structured substantiated reasons and source result fields; no credentials or unrelated personal data |
| `completed_at` | timestamp | Required completion time used to decide whether an incoming applicable result is newer |

### Constraints and relationships

- Unique: (`schedule_revision_id`, `course_id`, `operation_kind`).
- A revision has zero or more retained outcomes.
- A course has at most one current retained outcome per operation kind in each
  revision.
- Upsert replaces only the same unique key and only with a newer applicable
  completed result.
- Deleting or archiving unrelated lifecycle history must not reassign an
  outcome to another revision.
- A successor Working revision starts with no inherited outcomes.
- Publishing, restoring the same active revision after a failed action, or
  changing that revision between Draft and Ready for review keeps its outcomes.
- Abandoned or superseded revision outcomes may remain relationally associated
  for integrity but are not included in the main workspace.
- No migration backfill invents earlier response-only outcomes.

### Retention state transitions

```text
no retained outcome
  -> reliable completed result: insert

retained outcome
  -> newer completed result for same revision/course/kind: replace
  -> result for different revision/course/kind: coexist
  -> request rejected/cancelled/confirmation required: unchanged
  -> operation-level failure without reliable per-course result: unchanged
```

## Existing persisted entity extension: ScheduleRevision snapshot

No new table is required. New publications use snapshot schema version 2 and
extend the existing immutable JSON snapshot with the captured course constraint
context required to interpret the captured occurrences.

| Snapshot field | Rules |
|---|---|
| `schema_version` | New publications use `2`; readers continue to support `1` |
| `courses[].constraint_profile` | Captured values needed by established current-validation evaluators; immutable after publication |

Version 1 snapshots remain valid. When a needed constraint is absent, only the
affected validation category is `unavailable`; the reader must not borrow a
mutable Working value or alter the snapshot.

## Read entity: SemesterWorkspaceSnapshot

One coherent response for one semester and exactly one permitted revision.

| Field | Meaning |
|---|---|
| `semester` | Stable semester identity, name, and inclusive date range |
| `selected_revision` | Stable revision identity, number, lifecycle state, Working/Current Published designation, mutability, and content source |
| `available_contexts` | Optional active Working and Current Published selectors only |
| `workspace_token` | Opaque identity/version token for stale-response rejection |
| `section_status` | Availability and error/coverage metadata per response section |
| `courses` | Revision-scoped course operational records |
| `occurrences` | Revision-scoped teaching and exam occurrences |
| `holidays` | Current holiday date context relevant to the semester |
| `validation_findings` | Deduplicated current findings over selected occurrences |
| `planning_outcomes` | Latest applicable retained outcomes for selected revision |
| `summary` | Authoritative complete-revision metrics and contributor references |
| `filter_facets` | Filter choices derived from this response only |

### Revision selection rules

- Without `revisionId`, select active Working when present; otherwise Current
  Published; otherwise return the explicit no-revision state.
- An explicit `revisionId` must equal the semester's active Working or Current
  Published revision. Historical revisions are rejected from this endpoint.
- `content_source` is `active_working` for live Working data and
  `captured_published` for immutable Published content.
- Published validation uses only `captured_published` occurrences and current
  planning facts.

## Read entity: WorkspaceCourse

One course-semester operational context as represented by the selected revision.

| Field | Meaning |
|---|---|
| `course_ref` | Stable typed reference |
| `course_id`, `code`, `name` | Captured or live identifying data appropriate to the selected revision |
| `cohort`, `lecturers`, `study_type` | Filter/detail dimensions |
| `planning_eligible` | Whether the course belongs to the current semester-planning outcome coverage universe; ineligible courses remain visible for other workspace concerns |
| `total_teaching_units` | Revision-appropriate total; captured value for Published |
| `scheduled_teaching_units` | Sum of selected revision's teaching occurrences |
| `remaining_teaching_units` | `max(0, total - scheduled)` |
| `remaining_instructional_minutes` | `remaining_teaching_units * 45` |
| `occurrence_refs` | All selected-revision teaching/exam references for the course |
| `finding_refs` | All current finding references affecting the course |
| `outcome_refs` | All latest applicable retained outcome references |
| `needs_review_reason_refs` | Distinct qualifying reasons; lifecycle state alone is excluded |

## Read entity: WorkspaceOccurrence

A discriminated teaching or exam occurrence. Its `occurrence_ref` is
`teaching:{id}` or `exam:{id}`.

Common fields:

- occurrence reference and `kind`;
- course, cohort, lecturer, and room references/names;
- scheduled ISO date, start time, end time;
- selected revision reference;
- current finding references;
- source/recommendation context where already available.

Teaching-only fields include teaching units and established manual/planning
source. Exam-only fields include exam type, duration, resource/capacity,
recommendation, and validity context required by FS-012.

Occurrences are never moved, resized, duplicated, split, merged, or mutated by
calendar navigation/filtering.

## Read entity: CurrentValidationFinding

A canonical established condition evaluated for the selected revision.

| Field | Meaning |
|---|---|
| `finding_ref` | Stable identity within the response |
| `category` | Conflict, capacity, holiday, exam validity, or other established category |
| `validation_basis` | `current` |
| `affected_course_refs` | Distinct courses affected |
| `affected_occurrence_refs` | Distinct selected-revision occurrences affected |
| `details` | Category-specific substantiated values and related record references |

Deduplication rules:

- conflict: one finding per conflict type and sorted unordered occurrence pair;
- capacity: one finding per affected occurrence;
- holiday/exam/other established rule: one canonical rule result, even if
  exposed from multiple affected records.

For Published, all affected occurrence references must belong to that Published
snapshot. Working and historical references are forbidden.

## Read entity: OperationalSummaryMetric

| Field | Meaning |
|---|---|
| `metric` | `unscheduled_work`, `conflicts`, `capacity_issues`, `planning_failures`, or `needs_review` |
| `availability` | `available`, `partial`, `unavailable`, or `not_applicable` |
| `scope` | `complete_revision` in the server response; client may derive `filtered_subset` |
| `value` | Complete numeric value when available; known incomplete value when partial; absent when unavailable or not applicable |
| `secondary_values` | Metric-specific units/minutes/course count or outcome-category counts |
| `contributor_refs` | Complete canonical contributor set |
| `unavailable_reason` | Required when unavailable; coverage detail when partial |

Zero is valid only when availability is `available` and the contributor set is
empty. The value must reconcile with its contributor definitions.

For `planning_failures`, coverage uses the included eligible courses in the
current revision/filter scope:

- `eligible_course_count` is the number of included course-semester contexts
  eligible for at least one established planning operation.
- `covered_course_count` is the number of those courses having at least one
  reliable completed retained outcome in the selected revision.
- `coverage_complete` is true only when both counts are equal and at least one
  eligible course exists.
- no eligible courses is `not_applicable`;
- eligible courses with zero covered courses is `unavailable`;
- some but not all eligible courses covered is `partial`, and any value is a
  known incomplete failure count;
- all eligible courses covered is `available`, and only then may no failed
  outcomes be displayed as zero.

The failure value counts failed retained outcome records, not distinct courses.
An unattempted operation kind is not a failure and does not separately reduce
coverage after its course is covered.

The other metric applicability universes are:

- `unscheduled_work`: included course-semester contexts. No included course is
  not applicable; complete unit data with no remaining work is available zero.
- `conflicts`: included scheduled occurrences. No included occurrence is not
  applicable; at least one evaluated occurrence with no conflict is available
  zero.
- `capacity_issues`: included scheduled occurrences requiring capacity
  evaluation. No applicable occurrence is not applicable; all evaluated with
  no capacity issue is available zero.
- `needs_review`: included course-semester contexts. No included course is not
  applicable; all evaluated with no qualifying reason is available zero.

For every metric, no verifiable required source data is unavailable and a
strict subset of verifiable applicable records is partial. Available and
partial states carry their named numeric values; unavailable and not-applicable
states do not.

## Presentation state: FilterContext

Ephemeral React state owned by the Schedule workspace:

- selected course(s), cohort(s), lecturer(s), room(s), study type(s);
- session scope (`all`, `teaching`, or `exam`);
- permitted lifecycle context;
- validation categories;
- optional summary drilldown;
- calendar mode (`week`, `day`, `month`, or `list`);
- visible date/period and selected detail reference.

Applicable filters combine by intersection. A conflict remains understandable
when only one affected occurrence is visible by retaining a path to the related
occurrence. Room filtering may select courses through assigned occurrences but
does not assign remaining work to that room. Clearing drilldown preserves the
prior mode, date, revision, and unrelated filters.

## Workspace availability states

The UI distinguishes these states without representing them as one generic
empty response:

- no semester selected;
- no Working or Current Published revision;
- loading intended context;
- loaded revision with no occurrences;
- available metric with zero contributors;
- not-applicable metric with no eligible contributor universe;
- no matching filtered results;
- partial response;
- initial failure;
- refresh failure with complete last-known response;
- recovered coherent response.

Only a complete coherent response becomes current. Partial-section
availability is explicit, and unavailable sections do not contribute to totals.
The no-revision response has null selected revision, empty revision-owned
records and filter facets, and not-applicable summaries with `no_revision`
scope; those values cannot be interpreted as a loaded empty schedule.
