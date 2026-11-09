# Code Review

## Scope reviewed
Course unit information only: migration 0014, startup integration, course model,
catalog schemas/API/service, client types, editor and edit-value mapping, and
targeted tests. Existing unrelated working tree changes are outside this review.

## Context used
User request, spec.md in this directory, project constitution, existing migration,
catalog and planning conventions, and relevant test fixtures.

## Verification performed
87 backend tests passed across course-total migration, existing migrations,
academic catalog API and service tests. 42 client tests passed across the editor,
academic data page and catalog API. TypeScript and Vite production build passed.

## Findings
No material findings in the scoped change. Repository-wide diff checking reports
an existing trailing blank line in the unrelated optimization-worker test.

## Requirement traceability
| Requirement | Implementation | Verification |
| --- | --- | --- |
| Rename displayed planning units | AcademicRecordEditor | Editor label test |
| Store independently editable full total | Course, catalog API/service/schema, editor mapping | API persistence and editor submission tests |
| Initialize existing totals once | Migration 0014 and startup | Migration preservation and repeatability test |
| Preserve planning behavior | Existing total_units consumers unchanged | Progress test with different overall total; existing catalog tests |
| Preserve schedules | Migration copies courses while startup disables SQLite foreign keys | Draft/session equality and foreign key check |

## Test assessment
Focused tests cover default creation, explicit creation, editing, omitted-update
preservation, invalid totals, list responses, independent planning progress,
existing-data upgrade and repeat startup. Full planning/solver suites were not
rerun because those implementations were unchanged.

## Architecture and design assessment
Legacy total_units / totalUnits identifiers preserve existing contracts and
planning semantics. overall_units / overallUnits is additive catalog information.
No new dependencies or changes to scheduling calculations.

## Security assessment
Existing authorization and optimistic revision checks remain in place.

## Performance and reliability assessment
One-time upgrade backfills existing courses and makes the new column non-null.
SQLite table rebuilding runs within the existing atomic startup transaction.
No additional planning queries or optimizer inputs are introduced.

## Overall recommendation
Approve for this scoped change. No follow-up review or refactoring is required.

## Suggested next action
Restart the backend to apply the migration to its configured database. Production
databases were not manually migrated during this task. Changes remain uncommitted;
the working tree also contains unrelated pre-existing modifications.
