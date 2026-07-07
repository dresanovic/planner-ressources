# Quickstart: Draft Course Schedule

This guide validates the first draft schedule generation slice end to end.

## Prerequisites

- Backend dependencies installed in `backend/`.
- Client dependencies installed in `client/`.
- Local SQLite database configured through the backend application settings.
- Planning seed data exists for one course, lecturer, room, Cohort, semester, study type, and Study Type Time Windows.

## Validation Scenario 1: Generate a Complete Weekly Draft

Seed data:

- Course: 20 teaching units
- Lecturer preference: 2 to 4 units per session
- Cohort: 30 students
- Room: capacity 40
- Semester: at least 5 valid weeks
- Study Type Time Window: selected window can fit a 4-unit session

Expected outcome:

- Generation succeeds.
- Five sessions are created.
- Each session has 4 units.
- Sessions occur once per week where possible.
- Sessions use the selected Study Type Time Window's weekday and start time where possible.
- Session duration includes four 45-minute units and three 10-minute breaks.

## Validation Scenario 2: Adjust Final Below-Minimum Remainder

Seed data:

- Course: 18 teaching units
- Lecturer preference: 3 to 4 units per session
- Other planning inputs valid

Expected outcome:

- Generation succeeds.
- Session unit distribution is 4, 4, 4, 3, 3.
- Total scheduled units equal 18.

## Validation Scenario 3: Use Additional Windows When Needed

Seed data:

- Semester has too few valid weeks for once-per-week placement.
- Study Type Time Windows contain multiple allowed windows.
- Selected window cannot complete all sessions alone.

Expected outcome:

- Generation succeeds if other allowed windows provide enough capacity.
- Multiple sessions may appear in the same week.
- No more than one generated session appears on the same day.

## Validation Scenario 4: Reject Insufficient Room Capacity

Seed data:

- Cohort: 45 students
- Room: capacity 40

Expected outcome:

- Generation is rejected.
- No draft schedule or draft sessions are created.
- Failure response includes `INSUFFICIENT_ROOM_CAPACITY`.

## Validation Scenario 5: Return All Detected Failure Reasons

Seed data:

- Room capacity below Cohort student count
- Invalid lecturer preference, such as minimum units greater than maximum units

Expected outcome:

- Generation is rejected.
- No partial draft is created.
- Failure response includes both detected failure reasons.

## Validation Scenario 6: Replace Existing Generated Draft

Steps:

1. Generate a valid draft for a course.
2. Change the selected Study Type Time Window or planning input.
3. Generate again for the same course.

Expected outcome:

- The second generation succeeds.
- Previous generated draft sessions for the course are replaced.
- Readback returns only the latest generated draft sessions.

## Commands

Run backend verification:

```text
cd backend
python -m pytest
```

Run frontend verification:

```text
cd client
npm run lint
npm run build
```

## Implementation Verification

Verified on 2026-07-06:

- Backend: `python -m pytest` completed 14 tests in about 1 second.
- Frontend: `npm run lint` passed.
- Frontend: `npm run build` passed after rerunning with elevated process permissions because Vite helper process spawning was blocked by the sandbox.
- The service-level valid single-course scenarios complete well under the 1-minute goal.

## API Contract

See [contracts/draft-schedule.openapi.yaml](./contracts/draft-schedule.openapi.yaml).
