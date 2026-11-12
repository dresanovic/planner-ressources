# Implementation review

Scope: cohort-semester ownership, automatic LV inheritance, intensive replacement, UI contracts, development reset and baseline tooling. Reviewed with the code-review skill against spec.md and the project constitution.

- LV-to-cohort remains the existing courses.cohort_id foreign key. There is no independent course calendar foreign key. Calendar ownership is unique by cohort and semester.
- Calendar creation validates relationships and period boundaries. Updates protect owner identity and optimistic revisions; cohort/semester deletion counts calendars as dependencies.
- Candidate start construction, candidate generation, retained-session validation, exact-candidate validation and manual/snapshot validation all supply the full calendar to the shared intensive replacement rule.
- Default and custom teaching periods respect cohort calendar boundaries. Holidays retain their existing precedence.
- UI has cohort/semester calendar configuration and weekly/dated window sections. LV editing retains cohort/semester and has no calendar selector.
- Reset opens source read-only, writes a separate verified candidate and full recovery snapshot, checks all retained table fingerprints and every retained LV field, and leaves no schedules/history. Activation remains through the existing offline restore tool.
- Historical schema migration tests are replaced by fresh-schema and explicit-reset tests because backward schema compatibility is explicitly excluded. Historical migration source files are preserved unchanged.

No outstanding correctness findings in reviewed paths. Known unchanged master-data limitation: four LVs have 1 LE with minimum session size 2 LE. Final combined test results are recorded separately. Browser login with the user's credentials is not exercised; no credentials were requested or changed.

Final verification: 1070 backend tests and 623 frontend tests passed; build and lint passed. Catalog and publication performance passed after adding batched calendar loading. Installed baseline passed 16920 course/date checks; startup, health and login-page delivery passed. Recovery backup and activation are recorded in the baseline directory.
