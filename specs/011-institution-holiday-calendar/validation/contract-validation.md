# FS-011 Contract Validation

**Validated:** 2026-07-20  
**Contract:** `contracts/holiday-calendar.openapi.yaml`  
**Result:** PASS for the implemented FS-011 HTTP slice

## Endpoint coverage

| Contract operation | Implementation boundary | Validation evidence |
|---|---|---|
| `GET/POST /api/holidays` | `backend/app/api/holiday_calendar.py` | Sorted current-state list, create, date/name validation, duplicate handling |
| `GET/PATCH/DELETE /api/holidays/{holidayId}` | `backend/app/api/holiday_calendar.py` | Read, replacement update, optimistic revision, explicit confirmation, hard delete |
| `GET /api/draft-schedules` | `backend/app/api/draft_schedule.py` | Current derived session alerts; no standalone holiday rows |
| `POST /api/courses/{courseId}/draft-schedule/generate` | `backend/app/api/draft_schedule.py` | Server-loaded hard exclusion, named failure evidence, pre-save revalidation |
| `POST /api/draft-schedules/batch/generate` | `backend/app/api/multi_course_generation.py` and service | Per-course exclusion/evidence and affected-course stale preservation |
| `POST /api/draft-schedules/optimization/prepare` | `backend/app/api/conflict_aware_generation.py` and service | Holiday state in opaque fingerprints; caller `unavailableDates` unchanged |
| `POST /api/draft-schedules/optimization/generate` | `backend/app/api/conflict_aware_generation.py` and optimizer | Internal union, separate named reasons, snapshot revalidation |

## Representation checks

- `HolidayRecord` responses contain exactly current `id`, `date`, `name`, and positive `revision` state.
- Create/update inputs forbid extra import/source fields. Invalid dates and extra fields return the structured `errors` envelope with `VALIDATION_ERROR` and field context.
- Duplicate date conflicts return `DUPLICATE_HOLIDAY_DATE`; stale writes return `STALE_REVISION`; unconfirmed deletion returns `CONFIRMATION_REQUIRED`.
- Institution-holiday generation evidence contains non-null `holidayDate` and `holidayName` together. Non-holiday failure and optimizer-reason JSON omits both fields.
- Session holiday alerts contain the current date/name and an empty `relatedSessions` list.
- Non-holiday session alerts may serialize `holidayDate` and `holidayName` together as explicit `null` values; the OpenAPI schema and TypeScript client model accept that FastAPI representation.
- Confirmed deletion returns 204 and leaves no current or historical holiday row.

## Executed contract tests

```text
cd backend
.venv\Scripts\python.exe -m pytest tests/services/test_holiday_calendar.py tests/api/test_holiday_calendar.py tests/db/test_migrations.py -q
22 passed
```

The contract file contains no literal example blocks requiring separate example-schema validation. Request/response examples are exercised by the API tests above and the generation/alert integration suites recorded in `automated-tests.md`.
