# Research: Review Generated Schedule In Planner UI

## Decision: Keep The Existing Single-Course Draft Schedule Endpoint

**Rationale**: The Slice 2 clarification limits review to the current selected course's generated schedule. The existing endpoint family already models that boundary: `POST /api/courses/{course_id}/draft-schedule/generate` and `GET /api/courses/{course_id}/draft-schedule`. Enriching the response keeps the feature aligned with Slice 1 and avoids prematurely introducing semester-wide multi-course retrieval before Slice 5.

**Alternatives considered**:

- Add `GET /api/semesters/{semester_id}/draft-schedules`: rejected because it implies semester-wide multi-course review.
- Add separate filter query parameters to the read endpoint: rejected for this slice because filters narrow a single-course response and can be handled in the client.

## Decision: Enrich Draft Schedule Responses With Display Context

**Rationale**: The current frontend mock data contains human-readable planning context, but the API response only exposes schedule/session IDs and time values. Slice 2 requires staff to identify course, Cohort, lecturer, room, and study type context within the review UI. Returning a compact context object with IDs and names lets the UI display and filter real data without hard-coded labels.

**Alternatives considered**:

- Add separate lookup endpoints for each entity: rejected because it increases orchestration and loading states for a single-course review.
- Keep only IDs and map labels in the client mock state: rejected because it fails the real inspection requirement.

## Decision: Client-Side Filtering For Slice 2

**Rationale**: The clarified scope is one selected course's generated schedule, with semester-course sized session counts. Client-side filtering is simpler, keeps interactions immediate, and avoids adding backend query semantics that will likely change when multi-course review arrives.

**Alternatives considered**:

- Server-side filters on the schedule read endpoint: rejected because they provide little value for one course and add unnecessary API surface.
- Separate filter state persisted to storage: rejected because the spec requires review behavior, not saved user preferences.

## Decision: Weekly View As Simple Grouped Review, Not Calendar Infrastructure

**Rationale**: The spec asks for a simple weekly calendar-style review and explicitly excludes manual editing and calendar polish. A grouped presentation by week and day satisfies inspection needs without drag-and-drop, collision layout, or external calendar dependencies.

**Alternatives considered**:

- Introduce a calendar library: rejected because no edit, drag/drop, or complex event layout behavior is required.
- Only keep the list table: rejected because the spec requires a weekly calendar-style mode.

## Decision: No New Storage Or State Transitions

**Rationale**: Slice 2 reviews existing generated Draft Schedules and Draft Sessions. It does not create, edit, validate, or approve schedules. Existing `generated` schedule status remains sufficient.

**Alternatives considered**:

- Add review status such as `reviewed`: rejected because the spec does not include approval or workflow state.
- Add persisted filter/view preferences: rejected as outside current user value and not needed for acceptance tests.
