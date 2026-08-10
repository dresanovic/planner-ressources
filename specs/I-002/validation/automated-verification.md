# FS-022 automated verification

Date: 10.08.2026

| Command | Result |
|---|---|
| `python -m pytest backend/tests -q` | PASS — 481 passed, 1163 warnings |
| `npm test` | PASS — 51 files, 356 tests |
| `npm run lint` | PASS |
| `npm run build` | PASS |
| Focused terminology and lecturer backend tests | PASS — 100 tests |
| Focused actionable-dialog/form tests | PASS — 3 files, 9 tests |
| Focused academic/resource tests | PASS — 3 files, 23 tests |
| Focused accountless lecturer tests | PASS — 1 file, 15 tests |
| Focused course schedule tests | PASS — 1 file, 48 tests |

The pytest process still prints the baseline Windows `0xc0000139` pyarrow/NumPy
shutdown diagnostic after reporting exit code 0. This was present in the T001
baseline and is not introduced by FS-022.

Date transport, public lecturer privacy/shape, catalog validation/startup,
schedule domain behavior, lint and production compilation are green. T052-T054
remain manual/deployment acceptance work; therefore release readiness is not
claimed.

The 10.08.2026 convergence rerun added one first-invalid-focus regression and
raised the complete client count from 352 to 356. It also verifies that
protected-delete and publication dialogs ignore injected backend `message`
strings and render domain-local German context instead.

The corrective review pass additionally verifies recovery from a transient
application-chunk failure without reinitializing the terminology catalog, end-
field focus for reversed recommendation ranges, and complete structured
outside-recommendation context in publication confirmation. The complete
backend suite remains green at 481 tests.
