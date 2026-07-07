# Contract: Draft Schedule Review

## Scope

This contract supports Slice 2 review of the current selected course's generated Draft Schedule. It does not expose semester-wide multi-course review, manual editing, conflict detection, holidays, exams, dashboards, or validation alerts.

## Read Current Course Draft Schedule

`GET /api/courses/{course_id}/draft-schedule`

### Path Parameters

- `course_id` integer, required: selected course whose generated schedule is being reviewed.

### Success Response

Status: `200 OK`

```json
{
  "draftScheduleId": 1,
  "courseId": 1,
  "semesterId": 1,
  "selectedTimeWindowId": 1,
  "context": {
    "course": { "id": 1, "name": "Planning 101" },
    "cohort": { "id": 1, "name": "AI 1" },
    "lecturer": { "id": 1, "name": "Ada Lovelace" },
    "room": { "id": 1, "name": "R1" },
    "studyType": { "id": 1, "name": "Full-time" }
  },
  "sessions": [
    {
      "id": 1,
      "date": "2026-09-07",
      "startTime": "08:00",
      "endTime": "11:30",
      "units": 4,
      "courseId": 1,
      "cohortId": 1,
      "lecturerId": 1,
      "roomId": 1,
      "studyTypeId": 1,
      "timeWindowId": 1
    }
  ]
}
```

### Empty/Missing Response

Status: `404 Not Found`

```json
{
  "detail": "No generated draft schedule exists."
}
```

The frontend must show a no-schedule empty state for this response.

## Generate Current Course Draft Schedule

`POST /api/courses/{course_id}/draft-schedule/generate`

The generation endpoint keeps the Slice 1 request contract and returns the same enriched `DraftScheduleResponse` shape as the read endpoint on success.

### Request

```json
{
  "semesterId": 1,
  "selectedTimeWindowId": 1
}
```

### Success Response

Status: `201 Created`

Body: same shape as `GET /api/courses/{course_id}/draft-schedule`.

### Failure Response

Status: `422 Unprocessable Entity`

```json
{
  "errors": [
    {
      "code": "INSUFFICIENT_ROOM_CAPACITY",
      "message": "Room capacity is lower than Cohort size."
    }
  ]
}
```

## Frontend Review Contract

The review UI must support:

- View modes: `list`, `weekly`.
- Filter fields: course, Cohort, lecturer, room, study type.
- Match-all filter behavior.
- No-schedule empty state when the API returns `404`.
- No-results state when filters hide all sessions.
- No session editing controls in this slice.

The weekly view groups the filtered sessions by week and day. The list view shows the filtered sessions chronologically.
