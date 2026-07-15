# User Story 2 Validation — Resource Unavailability

Date: 2026-07-15

## Automated evidence

- Pure rules cover recurring weekday expansion, dated multi-day intervals, union behavior, exact half-open boundaries, and combined availability.
- Service/API coverage verifies owner-scoped recurring and dated CRUD, canonical ordering, duplicate rejection, revisions, stale writes, and deletion.
- Draft Schedule HTTP coverage adds overlapping Lecturer and Room periods after generation and verifies serializable `LECTURER_UNAVAILABLE` and `ROOM_UNAVAILABLE` alerts while every saved assignment/date/time remains byte-for-byte equivalent at the contract boundary.
- Client API/component coverage verifies discriminated payloads, canonical responses, retained invalid input, duplicate feedback, stale recovery, and resource-detail refresh behavior.

Focused commands used during implementation:

```text
python -m pytest tests/services/test_resource_rules.py tests/services/test_resource_catalog.py tests/api/test_resource_catalog.py tests/api/test_draft_schedule.py -q
npm test -- --run src/api/resourceCatalog.test.ts src/components/ResourceAvailabilityEditor.test.tsx src/pages/AcademicDataPage.test.tsx
```

Final regression confirmation: backend `142 passed`; client `71 passed`, lint and production build passed.

## Acceptance conclusion

Quickstart Scenarios 4 and 11 are represented by automated boundary, CRUD, stale-write, refresh-retention, serializable-alert, and no-mutation tests. User Story 2 passes independently.
