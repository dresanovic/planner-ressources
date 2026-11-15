# Code Review — Calendar simplification, 15.11.2026

## Scope reviewed

Only the user-requested changes to CalendarTimeGrid, CalendarMonthGrid, calendarTimeGridLayout, CalendarPlanningWorkspace, calendarWorkspaceUtils and associated CSS/tests/documentation. This checkout already contained broader frontend/backend I-014 and unrelated work; those changes were preserved and are outside this review.

## Context used

The user's four requirements and subsequent clarification to retain empty days; project constitution; I-014 specification, plan, tasks and interface contract; existing shared projection, session details, fixtures and restricted lecturer review.

## Verification performed

- `npm --prefix client test`: 74 files, 676 tests passed.
- `npm --prefix client run build`: TypeScript and Vite production build passed.
- `npm --prefix client run lint`: passed.
- `git diff --check`: passed.
- Regression cases were changed/added before implementation and failed on the removed placeholder behavior, missing multi-select and merged cohort identities. Final focused regressions passed.

## Findings

No material findings in the scoped changes. No critical, high, medium or low findings; no required refactoring.

## Requirement traceability

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Month empty days without calendar placeholders | CalendarMonthGrid | Empty date contains only its date; no window disclosure |
| Compact cohort label on Month sessions | cohortAbbreviation, month-cohort-label | Short codes, full-name title, long names and semester suffix regression tests |
| Week without source dropdown stack | CalendarTimeGrid | No overview/disclosures in grid; session inspection retains source access |
| Same-date cohorts side by side, other dates empty | CalendarTimeGrid, calendarGroups | Two session-bearing cohorts plus empty dates; distinct cohorts sharing a calendar/profile stay separate |
| Checkbox subset combined with lecturer | CohortFilter, matchesCourseContext | Two of three cohorts selected; matching session identities verified in Day/Week/Month/List |
| Navigation, refresh, All/reset and keyboard behavior | Existing workspace state, reconcileFilters, CohortFilter | Mode preservation, stale choice removal, All, final deselection, reset and Escape focus tests |

## Test assessment

Automated regressions cover changed behavior and retain existing geometry, overlap, window finding, overflow, detail and authority checks. One older lecturer Month test expected an unknown-window placeholder; it now checks the absence of that placeholder and presence of the cohort label. Full suite is green.

## Architecture and design assessment

Uses the existing React components, native checkboxes/details and client projection; no added dependency, API change or persistence operation. Cohort abbreviations derive from catalog names because no separate abbreviation field exists; full names remain available.

## Security assessment

No new external requests or mutation path. Restricted lecturer-review tests pass without fetching planner context or exposing planner controls.

## Performance and reliability assessment

Date-local columns use existing interval layout and profile grouping. Refresh reconciles stale cohort selections; summaries count the cohort subset as one filter dimension. No new material reliability concern found.

## Overall recommendation

Approve the scoped change based on automated verification and code inspection. This pass did not include a rendered browser inspection or real assistive-technology testing. Existing broader I-014 observed acceptance tasks remain pending and are not marked complete by this work.

## Suggested next action

Review the running UI with actual schedules. No follow-up code review is required absent further changes; no refactoring is required. No commit or push was performed. Git status retains the pre-existing dirty checkout plus these scoped client/documentation edits.
