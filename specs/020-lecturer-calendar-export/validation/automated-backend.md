# FS-020 Automated Backend Evidence

Environment: Windows, Python 3.12.8, isolated `.venv`, branch `codex/fs-020-lecturer-calendar-export`, base `133608f`, `icalendar==7.2.2`, `tzdata==2026.3`.

| Command | Result | Test duration |
|---|---:|---:|
| `python -m pytest backend/tests/services/test_lecturer_calendar_export.py backend/tests/api/test_lecturer_calendar_export.py backend/tests/services/test_lecturer_review_concurrency.py backend/tests/api/test_lecturer_bearer_authorization.py` | 55 passed | 11.80 s |
| `python -m pytest backend/tests/api/test_lecturer_review.py backend/tests/services/test_lecturer_review_concurrency.py` | 57 passed | 24.39 s |
| `python -m pytest` | 515 passed, 1 release-container test skipped | 409.60 s |
| `python -m pip check` | No broken requirements | n/a |

The single skip is `test_complete_100_event_export_meets_release_latency_contract`; it intentionally requires the release image constrained to 2 vCPU and 2 GiB with deployment metadata. The retained 100-event file and functional tests passed, but SC-007 remains a release-environment gate.
