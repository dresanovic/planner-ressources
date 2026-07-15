# FS-008 User Story 1 Verification

Date: 2026-07-15

## Automated results

Backend command:

```text
python -m pytest tests/services/test_resource_catalog.py tests/api/test_resource_catalog.py -q
```

Result: `10 passed in 1.43s`.

Client commands and results:

```text
npm test -- --run src/pages/AcademicDataPage.test.tsx src/api/resourceCatalog.test.ts src/components/ResourceAdministration.test.tsx
# 3 files, 13 tests passed

npm run lint
# passed

npm run build
# passed; production bundle built in 164ms
```

## Quickstart Scenario 2: duplicate names and unique codes

- Same-named Lecturer records with distinct codes were accepted.
- Codes differing only by case or surrounding whitespace were rejected with `DUPLICATE_REFERENCE_CODE` and `referenceCode` field feedback.
- Name and code searches returned the intended stable resource.
- Lists render `Name · CODE`; Rooms also render capacity.

## Quickstart Scenario 3: lifecycle

- Usage preflight returned active Course identities and saved session/schedule counts.
- A resource used by an active Course and DraftSession was inactivated, with its eligibility and DraftSession assignment unchanged.
- The inactivated resource disappeared from the active-default list and remained available through inactive/all filters.
- Valid reactivation reported usable and unusable preserved relationships without changing assignments.
- A resource linked only to inactive Courses and no DraftSession was permanently deleted, and inactive eligibility links were reported as cleaned up.
- Cancellation from the consequence dialog issued no removal request.
- Stale revisions returned current revision metadata and did not mutate saved data.
- Refresh failures retained the selected resource, controlled input, and last-known list content.

This checkpoint implements only scheduling-resource administration and protected lifecycle behavior; availability, Course eligibility editing, and scheduling consumption remain later FS-008 user stories.
