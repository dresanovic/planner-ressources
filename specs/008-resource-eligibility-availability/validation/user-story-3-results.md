# User Story 3 Validation — Course Resource Eligibility

Date: 2026-07-15

## Automated evidence

- Atomic Course replacement covers multiple eligible resources, duplicate IDs, inactive and undersized additions, final-resource guards, preserved invalid relationships, stale revisions, and all-or-nothing failure.
- Course configuration returns coded candidates, capacity/usability reasons, current unavailable periods, Course-specific saved-session usage, and fixed `minimizeLecturerChanges` / `minimizeRoomChanges` metadata. Inactive resources assigned to historical sessions remain inspectable after eligibility removal.
- Room shrink preserves eligibility and saved assignments for validation. Cohort growth removes every newly insufficient relationship, increments each affected Course revision once, and reports Courses without Rooms.
- Draft Schedule contract coverage verifies simultaneous `LECTURER_INELIGIBLE`, `ROOM_INELIGIBLE`, availability, and `ROOM_CAPACITY` alerts without assignment mutation, including current-Cohort capacity alerts after Cohort growth.
- Planning options retain unavailable Courses and return `NO_ACTIVE_ELIGIBLE_LECTURER` / `NO_USABLE_ELIGIBLE_ROOM` readiness reasons.
- Client coverage verifies atomic payloads, Cohort capacity results/messages, searchable coded groups, invalid preserved links, disabled invalid additions, fixed guidance, and refresh retention.

Focused command:

```text
python -m pytest tests/services/test_resource_catalog.py tests/api/test_resource_catalog.py tests/api/test_planning_options.py tests/api/test_draft_schedule.py -q
npm test -- --run src/api/resourceCatalog.test.ts src/api/academicCatalog.test.ts src/components/CourseResourceEligibilityEditor.test.tsx src/pages/AcademicDataPage.test.tsx
```

Final regression confirmation: backend `150 passed`; client `75 passed`, lint and production build passed.

## Acceptance conclusion

Quickstart Scenarios 5, 6, and 11 are covered by automated eligibility, capacity-asymmetry, stale-update, assignment-preservation, alert, and refresh-failure tests. User Story 3 passes independently.
