# I-014 Interface Contracts

## Existing authenticated workspace read

`GET /api/semesters/{semester_id}/calendar-workspace?revisionId={id}` retains authentication, status codes, revision selection and error behavior in `backend/app/api/calendar_workspace.py`. No new endpoint, query argument or mutation is introduced. `backend/app/schemas/calendar_workspace.py` and `client/src/api/calendarWorkspace.ts` change together.

### Additive response fields

Each course adds `cohortCalendarRef: string | null`, normally `calendar:<source id>`. Resolve from Working data or captured calendar identity, never current lookup for a missing historical identity.

Loaded responses add `teachingWindowContexts: TeachingWindowContext[]` and `sectionStatus.teachingWindows` using existing section availability/reason/coverage conventions. Context identity is per course, not per occurrence. Each revision course has a context, even with no sessions; absent captured profile returns an unavailable context. A mixed available/unavailable set gives partial section availability. A known empty window collection is still available context.

| Context property | Shape |
| --- | --- |
| `courseRef` | Existing course ref, unique within contexts |
| `calendarRef`, `calendarLabel` | Nullable stable calendar ref; existing readable calendar label |
| `availability` | `available` / `unavailable` / `not_applicable` |
| `basis` | `current_working` / `captured_published` / `unavailable` |
| `reason` | String or null |
| `isCustom`, `sourceRevision` | Existing boolean and numeric revision metadata, or null when unavailable |
| `planningStartDate`, `planningEndDate` | ISO dates or null when unavailable |
| `windows` | Array of source window objects below |
| `days` | Array of resolved day objects below |

Source window: `{windowRef, sourceTimeWindowId, kind, weekday, date, isIntensive, startTime, endTime, sortOrder}`. `weekday` uses the existing Monday=0 convention for weekly windows; dated uses full ISO date and nullable weekday. Hours retain existing clock serialization. A `windowRef` must be unique within its context and stable for the same source response; nullable IDs use an explicit context-local reference, not an invented catalog identity.

Resolved day: `{date, periodStatus, applicableWindowRefs}`. Cover all selected-semester dates and any occurrence dates outside them. For within-period dates, use the exact existing date applicability helper across the full source collection. For outside-period dates, refs are empty and period status is explicit. These are display projections, not new validation results. Duplicate/unknown refs and invalid date/time shapes must not be silently accepted as permission.

Example for the acceptance fixture (abbreviated date coverage):

```json
{
  "courseRef": "course:1",
  "calendarRef": "calendar:1",
  "calendarLabel": "Fixture cohort calendar",
  "availability": "available",
  "basis": "current_working",
  "reason": null,
  "isCustom": false,
  "sourceRevision": null,
  "planningStartDate": "2027-03-01",
  "planningEndDate": "2027-07-31",
  "windows": [{
    "windowRef": "window:1",
    "sourceTimeWindowId": 1,
    "kind": "weekly",
    "weekday": 5,
    "date": null,
    "isIntensive": false,
    "startTime": "08:00",
    "endTime": "16:00",
    "sortOrder": 0
  }],
  "days": [{
    "date": "2027-06-26",
    "periodStatus": "within_period",
    "applicableWindowRefs": ["window:1"]
  }]
}
```

The profile must be the exact one used by existing workspace validation. Published basis is `captured_published`, never a join to live catalog windows; missing legacy capture uses unavailable/null metadata/empty arrays with reason. `selectedRevision.validationBasis` remains `current`; profile provenance does not relabel existing current validation. No-revision responses include empty contexts and a not-applicable teaching-window section, with no invented calendar context.

### Compatibility and failure

Existing sessions, findings, summary values, facets and token algorithm retain their meanings. Add new data before calculating the existing response token. Existing calendar filter values remain compatible; stable refs are additive grouping identities, not a filter migration.

The client treats absent context fields as unavailable for older/restricted adapters; it must not break session/List rendering. If the new section is malformed while existing core workspace data is sound, quarantine that section as unavailable with reason/retry, never accept malformed intervals or fail all session access. Core malformed workspace behavior remains unchanged. Last-known data is visibly outdated and cannot be mixed with another revision's windows.

Implementation verification: a section marked unavailable/not-applicable cannot
simultaneously supply an available profile; contradictory sections are quarantined.
Published profiles retain captured provenance independently of the existing current
validation basis. Null captured identity never becomes a current catalog identity.

Public lecturer-review endpoints are unchanged. The adapter may supply empty/unavailable context locally and must never fetch this planner endpoint with a public token or expose unassigned records.

## UI contract

- Existing `CalendarPlanningWorkspace` callbacks and controlled selection remain the entry points. Surfaces receive the resolved date range, filtered occurrences, authoritative contexts and selection/date callbacks; they neither fetch catalogs nor save data.
- Hourly surface: full 24 hours, 72 CSS pixels/hour initial scale, proportional block position/height, same scale per date/group. Start at earliest visible supplied content or 08:00 fallback. Sticky labels and focusable named scroll regions keep date/hour/calendar identity reachable.
- Date enumeration: Day=one date; Week=Monday through Sunday; Month=complete Monday-based weeks spanning its first/last date, with adjacent-month labels. Empty days remain present. Month padding does not expand the selected session filter set; adjacent-date activation opens Day to inspect that date using existing navigation semantics.
- Group by stable calendar identity; different course profiles use labeled subgroups instead of a misleading union. Existing validation issue codes drive affected-entry cues, not generic `has-warning` (which includes unrelated warnings).
- Window disclosure is keyboard/pointer accessible inline beside the selected context and available from Month; it lists source hours/kind/intensive status and unknown basis explicitly. Course-specific context remains visible alongside affected session inspection even when the established custom pane renderer is used.
- On narrow screens, the existing modal `SessionPane` includes the same read-only
  disclosure within its accessible subtree in both detail and editing modes.
  During editing it identifies the saved session's date; no browser permission
  computation or unsaved-draft permission preview is introduced.
- Use native sections/lists/buttons, not a partially implemented ARIA grid. Tab order is date/group/chronological entry; Enter/Space activates. Inline overflow expansion retains focus; pane close restores its origin or logical fallback. Native scroll keys reach all regions. No new custom shortcut or drag edit.
- Month shows three entries per day initially, `+N` hidden count, exact affected-occurrence count for existing window findings, and expandable complete entries. Shortened visible titles retain full accessible names. No hover-only facts.
- List uses the same existing projection and gains no independent permission logic. Window explanations remain reachable in calendar, not only through List.

## Required contract evidence

Backend API/service tests and client decoder fixtures cover the example, empty course/date, intensive suppression of weekly windows, adjacent/non-stitchable sources, differing profiles, duplicate calendar names with different identities, missing Published profile/identity, unknown/malformed section, token changes and no-revision. Compare old fields/findings and saved records before/after reads; new projection must not change them. Restricted adapter regression tests prove no planner fetch or extra action.

## Presentation clarification — 15.11.2026

The API still supplies all profile facts. The UI renders only session-bearing profile columns on each date; dates without sessions remain visible once and empty. No separate expandable source overview or Month calendar/window placeholders are displayed. Sources remain available through selected-session inspection. Month entries show a cohort abbreviation with full-name tooltip/accessibility text. The client cohort filter is a string array: OR within selected cohorts, AND with other dimensions; empty/undefined means all. Facet strings and network requests remain unchanged.
