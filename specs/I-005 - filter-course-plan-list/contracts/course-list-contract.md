# Course-list UI and existing boundary contract — I-005

## Inputs and ownership

- CourseSchedulePage owns planning-option retrieval state, including refresh failure with retained options. Initial loading/failure may render at the page boundary before the panel exists. When options are retained, show pending/failed freshness rather than a successful zero-match result, preserve selected IDs/identity, and block generation on failed freshness until reload/recovery succeeds. Pass that context to the panel when mounted.
- CourseSchedulePage passes the full semester course list, complete selectedCourseIds, existing workflow-disabled/busy status, semester identity, controlled cohort choice and filter-change callback into MultiCourseGenerationPanel. Filter controls must not call onChange(selected IDs) or onGenerate.
- App owns administration semester/cohort filter state and passes state/change callbacks into AcademicDataPage. CourseSchedulePage owns independent generation cohort state. No shared selection or calendar-filter state is introduced.
- AcademicDataPage retains complete records loaded with existing status restrictions; apply explicit semester membership and cohort membership to the display projection only. Editor values/options and exact-record callbacks remain independent.
- AcademicCatalogList may accept a narrow optional course metadata renderer. Non-course callers retain their current labels/actions unchanged.

## Matching, review and states

1. Semester restriction precedes cohort matching. Match cohort IDs, never names. All-semester administration keeps null-semester records discoverable; a particular semester excludes them.
2. Generation uses existing semesterCourses semantics (including existing legacy missing-semester fixtures); eligibility/whole-set validation are authoritative. Unavailable matching records show their reason and cannot be newly selected; selected ones remain reviewable/removable when the workflow permits.
3. Count matches against applicable successfully loaded data. Empty underlying scope, no matches, loading and failed retrieval have distinguishable messages. A missing chosen cohort remains explicitly unavailable until reset; do not label unfiltered data as its results.
4. Before generation, display totalSelected and hiddenSelected plus a review of every selected identity and cohort. Include absent IDs with last-known identity or an explicit unavailable ID fallback. Provide a way to reveal hidden items by reset or cohort change; missing IDs remain visible in review for whole-set clearing/validation.
5. Reset cohort affects only visibility; clear-selection explicitly affects all selected IDs, including hidden ones. Their labels/effects must be distinguishable.
6. Filter restoration survives list/pane navigation in the same page session and scope. Explicit reset replaces memory with null. Semester change and reload discard prior choice; earlier semesters must not revive it. No filter restoration modifies generation selection.
7. Controls have accessible German names and visible focus. Result/no-match and selected/hidden counts are perceivable to assistive technology. Focus stays meaningful when result content disappears. Layout wraps long identities and controls at 320 CSS pixels and 200% text enlargement.

## Existing HTTP contracts — unchanged

- GET /api/planning-options[?semesterId=...] supplies CourseOption fields; preserve current activity, authorization, filtering and failure semantics.
- GET /api/academic/courses?page=...&pageSize=...[&status=...] supplies CourseRecord pages; existing administration loads all pages. GET academic cohort/semester options remains unchanged. No cohort query parameter is added.
- POST /api/draft-schedules/optimization/prepare receives existing semesterId, scheduleRevisionId, **complete explicit courseIds**, and unavailableDates. Visible IDs are never substituted.
- Existing generate and accept requests use captured snapshot/preparation evidence and candidate fingerprint. Filtering must not change those values or an unresolved comparison. Hidden courses with saved sessions still require the established complete joint decision.
- Filters issue no mutation requests, no generation requests, and no new integration calls. Existing mutations remain bound to the explicitly opened course with their current revision/permission safeguards.

## Verification boundary

Extend client page/panel/navigation tests to assert exact full input IDs, no mutation calls for filter-only actions, option restoration/reset and stable editor values. Run existing client API tests and backend planning-options/catalog/conflict-aware-generation tests. Any discovered contract change requires updating this design and failing contract tests before production changes; no such change is planned.

