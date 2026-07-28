# Backend Regression Evidence

**Date**: 2026-07-27  
**Environment**: Python 3.12.8, pytest 7.4.4  
**Result**: PASS

Commands from `quickstart.md`:

1. API calendar/draft/exam/lifecycle suite: 68 passed, 135 warnings, 13.40s.
2. Service calendar/validation/exam/lifecycle/concurrency suite: 52 passed, 43 warnings, 6.54s.
3. Complete `backend/tests`: 347 passed, 851 warnings, 58.99s.

Every pytest command exited 0. Windows printed an existing post-run `0xc0000139` native-library diagnostic from the pyarrow/pandas/OR-Tools import stack after results were complete; it did not change pytest exit status or test outcomes.

FS-019 changes no backend production file, endpoint, HTTP schema, persistence model, lifecycle state, exam eligibility rule, or scheduling validation rule. The passing API and service suites preserve the existing calendar, draft schedule, exam, and lifecycle contracts.
