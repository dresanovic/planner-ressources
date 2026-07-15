# Backend Regression Results

Date: 2026-07-15

Command:

```text
cd backend
python -m pytest -q
```

Result after the code-review corrections: `153 passed, 333 warnings in 17.72s`.

The warnings are existing SQLAlchemy and Starlette deprecation warnings; there were no failures or errors. Coverage now includes database-enforced concurrent stale-write rejection for resources, unavailable periods, and Course eligibility; Course metadata eligibility preservation; current-Cohort capacity validation after growth and shrink; active-only planning choices; Course-specific availability/session-usage context; populated FS-008 downgrade preservation; and safe rejection of downgrade states that FS-007 cannot represent.
