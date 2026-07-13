# Research: Conflict Detection

## Decision: Derive Validation Alerts At Read Time

Validation alerts will be computed when draft schedules are returned for the selected semester, rather than stored in a new table.

**Rationale**: Alerts depend on the current selected-semester schedule set, room and Cohort data, active generation constraints, and Study Type Time Windows. Read-time computation avoids stale persisted alerts after manual edits, regeneration, or constraint changes, and it keeps the slice additive with no migration.

**Alternatives considered**:

- Persist alerts after generation/edit save. Rejected because alerts could become stale when another course schedule or active constraint changes.
- Background validation job. Rejected because current volumes are small and the feature needs immediate post-save feedback.
- Client-only alert computation. Rejected because capacity, active constraints, and validation reference data belong to backend planning data and should be consistently exposed through the existing API contract.

## Decision: Extend Existing Draft Session Responses

Each `DraftSessionResponse` will include a `validationAlerts` array. Existing endpoints that return Draft Schedules will include alerts:

- generated draft schedule response after `POST /api/courses/{courseId}/draft-schedule/generate`;
- single-course read from `GET /api/courses/{courseId}/draft-schedule`;
- semester overview read from `GET /api/draft-schedules?semesterId=`;
- updated schedule response after `PATCH /api/draft-sessions/{sessionId}`.

**Rationale**: The frontend already renders the Courses overview from Draft Schedule responses. Attaching alerts to sessions keeps alert state colocated with the reviewed data and avoids new round trips or a separate validation endpoint.

**Alternatives considered**:

- Add a separate `/api/draft-schedule-validation` endpoint. Rejected because it would duplicate schedule retrieval and introduce synchronization complexity.
- Add summary-level alerts only. Rejected because the spec requires affected sessions and related conflicting sessions to be inspectable.

## Decision: Add A Focused Validation Service

Validation logic should live in a focused backend service such as `backend/app/services/draft_schedule_validation.py`, called from the draft schedule response mapping path.

**Rationale**: Overlap, capacity, and window checks are cohesive validation behavior, not persistence behavior. A separate service makes unit tests straightforward and avoids overloading repository functions with derived alert construction.

**Alternatives considered**:

- Implement checks directly in API response mapping. Rejected because it would make route code harder to test and maintain.
- Embed checks in SQL queries. Rejected because current rules are clearer as small Python domain checks and volumes are modest.

## Decision: Use Positive-Duration Interval Intersection

Two sessions overlap only when they are on the same date and their time ranges intersect with positive duration: one starts before the other ends and one ends after the other starts.

**Rationale**: This satisfies the spec's back-to-back boundary rule and is easy to test across lecturer, room, and Cohort grouping.

**Alternatives considered**:

- Treat touching boundaries as overlaps. Rejected by the spec edge case.
- Round or pad session times. Rejected because no tolerance window is specified and would create unexpected alerts.

## Decision: Alert Related Sessions Explicitly

Each overlap alert will include every related conflicting session available in the selected semester.

**Rationale**: The clarification requires specific related session detail. This supports filtered views where one side of a conflict may be hidden while the visible session still explains what it conflicts with.

**Alternatives considered**:

- Alert type plus count only. Rejected by clarification.
- Affected marker without details. Rejected because staff need to identify the conflict reason and related sessions.

## Decision: Evaluate Generation Constraints Against Currently Active Constraints

Generation-window violation alerts will compare Draft Sessions to the currently active course-semester generation constraints.

**Rationale**: The clarification selected current active constraints. This makes changing constraints a way to re-evaluate whether existing Draft Sessions still fit the active planning rules.

**Alternatives considered**:

- Validate against constraints captured at generation time. Rejected by clarification.
- Validate against both generated-time and current constraints. Rejected as more complex than requested and likely to produce duplicate alert categories.

## Decision: Custom Active Constraints Replace Study Type Window Validation

When currently active custom generation constraints exist for a course-semester, Study Type Time Window validation is skipped for that course-semester. Sessions outside the custom constraints receive a generation-constraint alert, not a duplicate Study Type alert.

**Rationale**: Custom generation constraints are the office staff's active planning rule for the course-semester. If staff configure Friday 18:00-22:00, validation should judge sessions against that active rule and avoid duplicate alerts from the default Study Type definition.

**Alternatives considered**:

- Always validate Study Type Time Windows independently. Rejected because it creates duplicate or misleading warnings when custom planning windows are the active rule.
- Remove Study Type Time Window alerts entirely. Rejected because default-window violations are still useful when no custom active constraint authorizes the session.

## Decision: Keep Alerts Non-Blocking

Generation and otherwise valid manual edits will continue to save even when the resulting schedule has validation alerts.

**Rationale**: The spec explicitly frames alerts as review information, not enforcement. Blocking belongs to future conflict-aware generation or stricter edit validation work.

**Alternatives considered**:

- Block saves that create conflicts. Rejected as out of scope and contrary to the Slice 5 spec.
- Add suggested fixes. Rejected as automatic conflict resolution scope.
