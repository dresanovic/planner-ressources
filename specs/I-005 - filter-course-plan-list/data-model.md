# Data Model — I-005

No database, migration or HTTP schema change. These are projections and local UI state.

| Entity | Fields used | Constraints and relationships |
| --- | --- | --- |
| Generation course | id, name, semesterId, cohort.id/name, availability.available/reasons | Existing stable course identity; backend semesterId is required; frontend legacy fixtures permit it to be absent. Preserve existing semester eligibility behavior; never infer cohort from names. |
| Administration course | id, name, semester.id/name or null, cohort.id/name, isActive, revision, availability | `semester is nullable`; null-semester records appear only in all-semester scope. Existing status restriction applies before local filtering. Record revision/relationships are never modified by filters. |
| Cohort / semester | Existing id and display name | Match IDs exactly; same names do not imply same identity. Missing chosen identity is an unavailable context, not permission to select another ID. |
| Generation filter | cohortId: number or null | `cohortId is nullable; null means all cohorts`. Owned in CourseSchedulePage; independent of selected IDs and calendar filters. |
| Administration filter | semesterId: number or null; cohortId: number or null | `semesterId is nullable; null means all semesters`; `cohortId is nullable; null means all cohorts`. Owned in App, passed to AcademicDataPage; initialize both null. |
| Generation selection | selectedCourseIds: number[]; last-known identity for selected courses where available | `valid generation selection contains 1–20 distinct course IDs`. Filter changes do not mutate this set. Missing/unavailable IDs remain represented and subject to existing whole-set validation, not discarded. Identity fallback may show course ID with unavailable status; it never changes identity. |
| Derived view | applicable courses, visible courses, totalSelected, hiddenSelected | Counts derive from full selected set. hiddenSelected means selected IDs absent from visible results, including missing records. Not persisted or sent as generation input. |

## State transitions

- Choose cohort: change only that surface's cohortId; retain selected IDs and editor values. Show results/count after successful catalog retrieval.
- Reset cohort: set only cohortId to null; retain semester/status scope and selection. Remember the unfiltered choice for later navigation.
- Choose administration semester (including all-semester): change semesterId and clear cohortId in one transition; do not reset editor or generation context. Retain that semester scope through navigation to restore the confirmed context.
- Commit generation semester change: existing guarded transition clears batch selection and cohortId together. Cancelled navigation changes neither. Returning to an earlier semester has no cached cohort to restore.
- Navigate away/back in the same page session and unchanged scope: restore each list's independent choice. Restoration never restores selection or an unsaved editor; those keep their existing lifetimes.
- Reload/fresh App mount: initialize filter state to null. No localStorage/sessionStorage or cross-tab synchronization.
- Retrieval state: parent-owned initial/loading/success/failure and refresh freshness are distinct from the visible-match count. Retain identities and selected IDs through failure; show an explicit failure/reload path and prevent generation on failed freshness, rather than treating retained data as a successful current empty result.
- Catalog refresh: recompute matches without changing selected IDs. If a remembered cohort or semester disappears, show unavailable context and retain an explicit reset/scope-recovery path. Do not silently broaden.
- Explicit select/deselect/clear: update only the existing selection set. At twenty selected IDs, reject new selection even when some are hidden; existing disabled/busy rules remain authoritative.
- Preparation/generation/comparison: read full selection through unchanged existing handlers. Filters never mutate captured evidence or candidate scope.

