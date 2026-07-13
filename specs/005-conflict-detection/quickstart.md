# Quickstart: Conflict Detection

This guide validates Slice 5 after implementation. It assumes Slices 1-4 are available.

## Prerequisites

- Backend dependencies are installed.
- Client dependencies are installed.
- Seed or fixture data includes:
  - at least one semester;
  - at least two generated Draft Schedules in the same semester;
  - generated Draft Sessions that can be arranged to overlap by lecturer, room, and Cohort;
  - at least one room with capacity below a session Cohort size;
  - at least one course-semester active generation constraint set;
  - at least one Study Type Time Window.

## Automated Verification

Run backend verification:

```powershell
cd backend
python -m pytest tests/services/test_draft_schedule_validation.py tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

Expected coverage:

- lecturer overlap alerts appear on all affected sessions;
- room overlap alerts appear on all affected sessions;
- Cohort overlap alerts appear on all affected sessions;
- cross-course overlaps identify every related conflicting session available in the selected semester;
- back-to-back sessions where one ends exactly when another starts do not produce overlap alerts;
- room capacity violations produce room capacity alerts;
- sessions outside currently active generation constraints produce generation-constraint alerts;
- sessions outside Study Type Time Windows produce Study Type Time Window alerts;
- sessions with multiple issues expose every applicable alert;
- missing validation reference data produces a validation-data issue;
- generation and otherwise valid manual edits remain non-blocking when alerts are present;
- regeneration and manual edits refresh alerts and remove alerts that no longer apply.

Run frontend verification:

```powershell
cd client
npm run test
npm run lint
npm run build
```

Expected coverage:

- validation alerts render in the Courses overview list mode;
- validation alerts render in weekly mode;
- alert details expose the conflict reason and related sessions for overlap alerts;
- alert state remains associated with the correct visible sessions when filters hide related sessions;
- sessions with multiple alerts show all alert reasons;
- after a manual edit callback updates schedule state, created alerts appear and resolved alerts disappear;
- existing generation and edit controls remain usable when alerts are present.

## Manual Smoke Scenario

1. Start the backend and client applications.
2. Open the planner page.
3. Select a semester with at least two generated Draft Schedules.
4. Create or use two sessions in the selected semester that overlap by lecturer, room, or Cohort.
5. Open the Courses overview.
6. Confirm each affected visible session shows a validation alert.
7. Inspect one alert.
8. Confirm the alert names the conflict reason and every related conflicting session available in the selected semester.
9. Switch between list and weekly modes.
10. Confirm alerts remain attached to the same affected sessions.
11. Apply a filter that hides one related conflicting session.
12. Confirm the visible affected session still shows its alert and related-session context.

## Manual Edit Refresh Scenario

1. Open a generated Draft Session for editing.
2. Save an otherwise valid edit that creates a room, lecturer, or Cohort overlap.
3. Confirm the edit saves.
4. Confirm the updated Courses overview shows the new validation alert.
5. Edit the session again to remove the overlap.
6. Confirm the resolved alert disappears after save.

## Capacity And Window Scenario

1. Use or create a Draft Session assigned to a room below the session Cohort size.
2. Confirm the session shows a room capacity alert.
3. Change the active generation constraints so the session falls outside the current course-semester planning period or allowed weekly teaching windows.
4. Confirm the session shows a generation-constraint alert.
5. Use or create a Draft Session outside its Study Type Time Window.
6. Confirm the session shows a Study Type Time Window alert.

## Non-Blocking Behavior Checks

1. Generate or use a draft schedule that produces validation alerts.
2. Confirm generation completes and the alerts appear after the generated schedule is shown.
3. Save an otherwise valid manual edit that leaves an alert unresolved.
4. Confirm the edit saves and the alert remains visible.

## Out Of Scope Checks

Confirm the Slice 5 UI does not expose:

- automatic conflict resolution;
- conflict-aware generation;
- public holiday warnings;
- exam scheduling;
- dashboard summaries;
- multi-course generation;
- session creation;
- session deletion;
- session splitting;
- session merging;
- multiple lecturers per course;
- multiple rooms per course.
