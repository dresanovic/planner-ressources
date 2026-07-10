# Quickstart: Manual Session Editing

This guide validates Slice 4 after implementation. It assumes Slices 1-3 are available.

## Prerequisites

- Backend dependencies are installed.
- Client dependencies are installed.
- Seed or fixture data includes:
  - at least one semester;
  - at least one generated Draft Schedule with Draft Sessions;
  - a Cohort with a known student count;
  - at least two rooms, where one room has enough capacity for the Cohort and one room does not.

## Automated Verification

Run backend verification:

```powershell
cd backend
python -m pytest tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

Expected coverage:

- valid session date/start/end/room edits update the existing Draft Session;
- edited dates outside the parent semester are rejected;
- duplicate dates inside the same Draft Schedule are rejected cleanly;
- end times equal to or before start times are rejected;
- replacement rooms below Cohort capacity are rejected;
- missing sessions and missing rooms return clear errors;
- failed edits leave the existing Draft Session unchanged;
- room occupancy conflicts are not blocked in this slice;
- regenerated course schedules continue to replace prior sessions.

Run frontend verification:

```powershell
cd client
npm run test
npm run lint
npm run build
```

Expected coverage:

- office staff can open edit controls from the Courses overview;
- edit controls show current date, start time, end time, room, and derived length;
- canceling edit controls leaves the visible session unchanged;
- saving valid edits updates list and weekly modes;
- edited room values affect room filter results;
- invalid edit messages are visible and do not falsely update the saved schedule;
- room choices include capacity metadata from planning options.

## Manual Smoke Scenario

1. Start the backend and client applications.
2. Open the planner page.
3. Select a semester with at least one generated Draft Schedule.
4. In the Courses overview, open a visible Draft Session for editing.
5. Change the session date to another date inside the selected semester.
6. Change the start time and end time so the end time is later than the start time.
7. Select a room whose capacity is at least the session Cohort size.
8. Save the edit.
9. Confirm the Courses overview shows the updated date, time range, derived length, and room.
10. Switch between list and weekly modes.
11. Confirm both modes show the edited values.
12. Filter by the replacement room.
13. Confirm the edited session appears in the filtered results.
14. Reopen the same selected semester.
15. Confirm the edited values are still visible.

## Negative Smoke Scenarios

### Out-Of-Semester Date

1. Open a generated Draft Session for editing.
2. Enter a date before the selected semester start or after the selected semester end.
3. Save the edit.
4. Confirm the edit is rejected and the existing Draft Session remains unchanged.

### Invalid Time Range

1. Open a generated Draft Session for editing.
2. Set the end time equal to or earlier than the start time.
3. Save the edit.
4. Confirm the edit is rejected and the existing Draft Session remains unchanged.

### Insufficient Room Capacity

1. Open a generated Draft Session for editing.
2. Select a room whose capacity is below the session Cohort size.
3. Save the edit.
4. Confirm the edit is rejected and the existing Draft Session room remains unchanged.

### Occupied Room Deferred To Slice 5

1. Create or use data where another Draft Session already uses the replacement room at the edited date and time.
2. Save an otherwise valid edit using that room and time.
3. Confirm Slice 4 does not show a room-occupancy warning or block the edit for overlap.

## Out Of Scope Checks

Confirm the Slice 4 UI does not expose:

- conflict warnings;
- public holiday warnings;
- exam scheduling;
- dashboard summaries;
- multi-course generation;
- session creation;
- session deletion;
- session splitting;
- session merging;
- editing source Course, Cohort, Lecturer, Semester, Study Type, or generation constraint records.
