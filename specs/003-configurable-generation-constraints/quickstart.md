# Quickstart: Configurable Generation Constraints

## Prerequisites

- Backend dependencies installed in the existing backend environment.
- Client dependencies installed with `npm install` in `client/`.
- Slice 1 generation and Slice 2 review behavior available.

## Backend Validation

Run backend tests:

```powershell
cd backend
python -m pytest tests/services/test_schedule_generation.py tests/services/test_draft_schedule_repository.py tests/api/test_draft_schedule.py
```

Expected coverage:

- Default generation constraints are derived from selected semester dates and study type windows.
- Custom planning period is accepted only when inside the selected semester and start date is not after end date.
- One or more allowed teaching windows are accepted when each has weekday, start time, and end time.
- Missing windows, invalid windows, and invalid planning periods return 422 with no partial schedule.
- Generated sessions stay inside the active planning period and active allowed windows.
- Successful generation saves constraints for the selected course and semester.
- Failed or blocked generation leaves saved constraints unchanged.
- Clearing saved constraints deletes the course-semester constraint set and restores defaults.

## Frontend Validation

Run frontend checks:

```powershell
cd client
npm run test
npm run lint
npm run build
```

Expected coverage:

- Generation constraints load when course and semester selections are available.
- The planning period defaults to the selected semester and can be overridden.
- Weekly teaching windows default from the selected course study type and can be added or removed.
- The UI distinguishes generation constraints from review filters.
- Generate sends the active planning period and allowed teaching windows.
- Clear custom constraints resets the UI to semester and study type defaults and calls the clear contract.
- Review filters continue to affect only visible Draft Sessions after generation.

## Manual Smoke Scenario

1. Start the backend API.
2. Start the client app.
3. Open the resource planner schedule page.
4. Select a course and semester with study type time windows.
5. Confirm the generation constraints section shows the semester start/end dates and default weekly teaching windows.
6. Add custom windows such as Monday 08:00-12:00 and Wednesday 09:00-13:00.
7. Generate the draft schedule.
8. Confirm all generated Draft Sessions occur within the active planning period and one of the active windows.
9. Reload or revisit the same course and semester.
10. Confirm saved custom constraints reload.
11. Attempt invalid constraints, such as start date after end date or a window whose end time is earlier than its start time.
12. Confirm generation is blocked and the previously saved constraints remain unchanged.
13. Clear custom constraints.
14. Confirm defaults are restored and the next visit to the same course and semester does not reload the cleared custom constraints.

## Contract Reference

Use [contracts/openapi.yaml](./contracts/openapi.yaml) for request and response shapes.