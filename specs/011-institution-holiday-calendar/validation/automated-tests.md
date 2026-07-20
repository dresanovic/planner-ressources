# FS-011 Automated Validation

**Executed:** 2026-07-20  
**Environment:** Windows, Python 3.12 backend virtual environment, Node/Vite client toolchain

## Focused verification

```text
cd backend
.venv\Scripts\python.exe -m pytest tests/services/test_holiday_calendar.py tests/api/test_holiday_calendar.py tests/db/test_migrations.py -q
22 passed

.venv\Scripts\python.exe -m pytest tests/services/test_schedule_generation.py tests/services/test_semester_optimization.py tests/services/test_draft_schedule_validation.py tests/services/test_multi_course_generation.py tests/services/test_conflict_aware_generation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py tests/api/test_conflict_aware_generation.py tests/performance/test_holiday_calendar_performance.py -q
157 passed

.venv\Scripts\python.exe -m pytest tests/performance/test_holiday_calendar_performance.py -q --durations=1
1 passed; 50-holiday/500-session alert derivation call: 0.10 seconds
```

```text
cd client
npm run test -- holidayCalendar HolidayAdministration CourseSchedulePage
22 passed
```

## Full regression verification

```text
cd backend
.venv\Scripts\python.exe -m pytest tests -q
267 passed
```

```text
cd client
npm run test
143 passed

npm run lint
PASS

npm run build
PASS
```

All listed full-suite, lint, and build results are final for this implementation and review-refactor pass.
