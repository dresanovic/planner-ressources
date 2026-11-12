# Plan

Use the existing calendar/window management and optimizer structures, replacing study format ownership with cohort-semester ownership. No reusable template layer, independent calendar publishing workflow or new dependencies. Calendar identity is resolved by cohort and semester; existing schedule snapshot machinery captures the resulting calendar. Development reset migrates master data into the new schema and discards all plans after saving a full recovery snapshot.

## Constitution and Simplicity Check
Specification precedes production changes. Tests precede implementation. Reuse existing React catalog and SQLAlchemy/FastAPI services. One cohort-calendar parent with existing window children is the simplest explicit semester-scoped design. Exclude template sharing, backward-compatible planning paths and historical restoration.

## Verification
Backend: backend/.venv/Scripts/python.exe -m pytest backend/tests/services/test_dated_intensive_windows.py and related API, catalog, lifecycle and optimization tests. Frontend: npm run build; npm run lint; npm test -- --run. Verify migrated baseline integrity, LV/cohort/unit preservation, no schedules, 37 intensive dates, weekly hours and per-semester isolation.
