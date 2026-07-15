# FS-008 Foundation Verification

Date: 2026-07-15  
Environment: Windows, SQLite in-memory and temporary-file databases, Python 3.12, pytest 7.4.4

## Test-first evidence

Before the production model and migration were added, the focused suite failed as intended:

- clean creation lacked the four FS-008 tables;
- migration 0004 did not exist;
- Lecturer and Room lacked resource code fields;
- seeded Courses lacked eligibility relationships; and
- the performance test could not import the FS-008 models.

## Passing verification

Command:

```text
python -m pytest tests/db/test_migrations.py tests/scripts/test_seed_dummy_planning_data.py tests/performance/test_resource_catalog_performance.py -q
```

Result: `11 passed in 1.57s`.

Verified invariants:

- empty databases are created directly with the current FS-008 schema;
- recognized FS-007 databases upgrade sequentially through migration 0004;
- legacy resources receive collision-free `LECT-<id>` and `ROOM-<id>` codes and normalized unique keys;
- every legacy Course receives its former Lecturer and Room in the corresponding eligibility junction;
- Course scalar `lecturer_id` and `room_id` columns are removed;
- DraftSession Lecturer and Room assignments remain unchanged;
- unavailable periods enforce exactly one owner, valid kinds/date shapes, positive revisions, and weekdays 0 through 6;
- seed data uses deterministic editable resource codes, creates one initial eligible Lecturer and Room for each Course, and remains duplicate-free when rerun; and
- 100 Lecturers, 100 Rooms, 100 Courses, and 1,000 unavailable periods can be loaded inside the two-second automated acceptance threshold.
