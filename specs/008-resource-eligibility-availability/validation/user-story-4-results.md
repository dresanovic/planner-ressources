# User Story 4 Validation — Scheduling Resource Choices

Date: 2026-07-15

## Automated evidence

- A deterministic dynamic-programming assignment pass independently minimizes Lecturer and Room transitions; normalized reference code then stable ID resolve equal-cost choices.
- Temporal placement skips windows where no complete hard-valid resource pair exists. Active state, Course eligibility, full-session availability, and Room capacity precede preferences.
- Single-Course and batch generation persist exactly one Lecturer and Room per session. Multi-Course tests prove Courses retain independent assignments with no shared score or cross-Course optimization.
- Draft Session PATCH changes both Lecturer and Room only to current valid choices, rejects invalid changed choices, preserves unchanged legacy-invalid assignments, and returns the refreshed parent schedule.
- Per-session response context exposes resource IDs, names, and reference codes. Validation composes eligibility, availability, capacity, temporal, and overlap alerts without mutation.
- The client renders coded per-session resources, filters by actual assignments, and supplies Course-specific Lecturer/Room controls.

Focused commands:

```text
python -m pytest tests/services/test_resource_rules.py tests/services/test_schedule_generation.py tests/services/test_multi_course_generation.py tests/api/test_draft_schedule.py tests/api/test_multi_course_generation.py tests/api/test_planning_options.py -q
npm test -- --run src/api/draftSchedule.test.ts src/api/planningOptions.test.ts src/components/DraftSchedulePanel.test.tsx
```

Final regression confirmation: backend `150 passed`; client `75 passed`, lint and production build passed.

## FS-010 boundary

Assignment is evaluated inside one Course Draft Schedule only. No resource ranks, quotas, weights, holiday/exam rules, global conflict solving, or semester-wide maximization were added.

## Acceptance conclusion

Quickstart Scenarios 7 and 8 are covered by deterministic allocation, hard-rule precedence, batch independence, manual edit, simultaneous alert, and unchanged-assignment tests. User Story 4 passes independently.
