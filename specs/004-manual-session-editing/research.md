# Research: Manual Session Editing

## Decision: Reuse Existing Draft Session Fields

Use the existing `DraftSession` fields for `date`, `start_time`, `end_time`, and `room_id` as the persisted manual-edit state. Do not add a separate manual-edit table or audit model in this slice.

**Rationale**: Slice 4 changes the current draft schedule data, not source planning records and not an audit workflow. The existing model already stores the editable values and the Courses overview reads from those fields.

**Alternatives considered**:

- Add a `ManualEdit` table: rejected because the spec requires durable edited schedule values, not edit history or approvals.
- Store manual overrides separately from generated sessions: rejected because it would add merging logic without user-visible value in this slice.

## Decision: Edit Length By End Time

Represent manual length changes by saving a new `end_time`. Display derived session length from the saved start/end time range. Keep `units` as existing teaching-unit coverage metadata for generated sessions.

**Rationale**: The clarification selected end-time editing. The existing model already has start and end time fields, so no migration is required. This also matches office-staff mental models when manually adjusting timetable blocks.

**Alternatives considered**:

- Edit whole teaching units: rejected by clarification.
- Add a duration-minutes column: rejected because duration is derivable from start/end time and would duplicate state.

## Decision: Add A Focused Session Edit Contract

Add a focused update contract for an existing Draft Session that accepts date, start time, end time, and room ID and returns the updated Draft Schedule response.

**Rationale**: Returning the updated course schedule lets the frontend replace or refresh the affected schedule while retaining the existing overview response shape. Editing by session ID matches the semester overview, where sessions from multiple courses are visible.

**Alternatives considered**:

- Update the entire Draft Schedule: rejected because the user edits one session at a time.
- Add separate endpoints per field: rejected because date/time/room edits should be validated together.

## Decision: Enforce Capacity, Defer Occupancy

Manual room edits must reject replacement rooms whose capacity is below the session cohort size. The same edit must not check whether the room is occupied at the edited date/time.

**Rationale**: The user clarified that insufficient capacity should never be allowed, while occupancy and overlap conflicts remain Slice 5 conflict detection. This mirrors the existing generation rule that capacity violations block draft creation.

**Alternatives considered**:

- Defer all room validation to Slice 5: rejected by clarification.
- Add occupancy checks now: rejected because it would introduce conflict detection before Slice 5.
- Restrict to course-eligible rooms: rejected because multiple eligible rooms per course is a later roadmap item.

## Decision: Extend Planning Options With Room Capacity Metadata

Extend the existing planning-options response with all rooms and their capacities so the edit UI can present room choices and indicate capacity suitability. Backend validation remains authoritative.

**Rationale**: The frontend currently only receives each course's assigned room, which is insufficient for a replacement-room selector. Adding room options to the existing planning-options payload keeps the UI data flow simple and avoids a new endpoint.

**Alternatives considered**:

- Add a dedicated rooms endpoint: rejected as unnecessary for the current small planning-options payload.
- Hard-code rooms in frontend tests only: rejected because production UI needs real room choices.

## Decision: Preserve Existing Regeneration Replacement Behavior

If office staff regenerate a course's draft schedule, the regenerated sessions replace previous generated sessions as established by earlier slices.

**Rationale**: Slice 4 is about manual edits to current Draft Sessions. Changing regeneration semantics would create a broader merge/preservation problem and contradict the existing replacement behavior.

**Alternatives considered**:

- Preserve manual edits across regeneration: rejected as a larger scheduling reconciliation feature.
- Block regeneration after manual edits: rejected because the spec says to continue using existing replacement behavior.

## Decision: Preserve Existing One-Session-Per-Date Invariant

Manual date edits must reject a date already used by another session in the same Draft Schedule.

**Rationale**: The existing Draft Session model has a unique schedule/date invariant from earlier generation behavior. Handling this as an explicit validation keeps user-facing errors clear and avoids raw persistence failures.

**Alternatives considered**:

- Allow multiple sessions on the same date: rejected because it would require a schema and behavior change outside Slice 4.
- Treat duplicate dates as room or lecturer conflicts: rejected because Slice 5 conflict detection is not required to preserve an existing storage invariant.
