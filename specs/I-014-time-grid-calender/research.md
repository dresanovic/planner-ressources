# I-014 Research and Decisions

Date: 2026-11-12. Read-only repository research for [spec.md](spec.md); no production changes or executed implementation checks are claimed.

## 1. Reuse the workspace, replace its presentation surface

**Decision**: Keep `CalendarPlanningWorkspace` as owner of mode, anchor, filters, selection, summaries and action callbacks. Extract the hourly and month surfaces into small presentational components. Preserve `CourseSchedulePage` pane integration and `projectWorkspace` filtering. Do not install a calendar package.

**Rationale**: `client/src/components/CalendarPlanningWorkspace.tsx` already offers all four modes, but `CalendarSurface` builds dates only from occurrences/holidays and renders stacked cards. `calendarWorkspaceUtils.ts` already defines Monday-based weeks, period movement and filtering. A complete date sequence and minute-positioned blocks directly address the demonstrated gap.

**Alternatives considered**: A third-party scheduler adds another event model, keyboard behavior and edit affordances to constrain; a replacement page duplicates established correction/lifecycle behavior. Neither is needed.

## 2. Expose authoritative context through an additive read-only response

**Decision**: Extend the existing authenticated `GET /api/semesters/{semester_id}/calendar-workspace?revisionId=…` response with per-course `teachingWindowContexts`, stable calendar references and a section status. Keep window source records plus server-resolved date applicability; use existing `window_applies`, not browser recurrence/precedence rules. Include zero-session revision courses.

**Rationale**: `backend/app/services/calendar_workspace.py` builds a constraint profile in `_working_content`, takes a captured profile in `_published_content`, uses it in `derive_calendar_validation_findings`, then removes it from occurrences before returning. Exposing a presentation projection of these same profiles avoids separate catalog requests and client reconstruction. `backend/app/services/schedule_generation.py::window_applies` suppresses recurring windows on dated-intensive dates; simply painting all weekly and dated records would be wrong.

**Alternatives considered**: Client joins of current catalog/constraints risk different precedence and incorrect Published provenance. Returning only occurrence profiles omits empty permitted dates. A new endpoint creates unnecessary loading and identity coordination. A new snapshot schema violates scope.

**Boundary**: Do not correct, normalize or redesign current profile construction or custom-constraint behavior in this slice. Use the exact profile used by existing workspace validation. Source records are not a promise that their union permits a session. Holiday/resource findings remain separate; teaching permission colors are not overall availability decisions.

## 3. Preserve revision and freshness semantics

**Decision**: Working context exposes the existing current working profile; Published exposes only its captured profile. Profile provenance is explicit and independent of `selectedRevision.validationBasis`, which remains `current`. Missing legacy capture is unavailable. Include new fields before the existing `_token(response)` calculation.

**Rationale**: Current Published occurrences come from captured content while current validation also evaluates current resource facts. Those two bases must not be conflated. The existing workspace token hashes the response, so including window facts provides freshness without new persistence or token infrastructure.

**Alternatives considered**: Joining live windows into publication would imply captured evidence that does not exist. Relabeling all validation captured would change established semantics. New version columns/cache services are unnecessary.

## 4. Geometry, overlaps and month overflow

**Decision**: Use existing CSS with a single hour scale (initial design: 72 CSS pixels/hour), a 24-hour canvas and positioned intervals in Day/Week; CSS Grid arranges date/calendar columns and the seven-column Month. Preserve actual minute geometry with border-box dimensions. Assign concurrent intervals to deterministic side-by-side lanes using start/end/ref sorting and end-exclusive overlap. Expose complete titles/times in adjacent textual detail when blocks are too short. Month initially shows three entries/date and an exact hidden count, with in-cell expansion to all entries.

**Rationale**: These are bounded presentation calculations, separate from scheduling or conflict validation. All-day rows can contain holidays above the hourly canvas. Month requires full weeks including adjacent-month cells; date enumeration cannot depend on event presence. See [MDN CSS Grid documentation](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout) for column/layer layout capabilities.

**Alternatives considered**: Min-height inflation misrepresents duration; hiding overlap loses sessions; hourly placement in Month defeats the compact overview. Virtualization is not justified by current acceptance cases.

## 5. Accessible semantics and restricted reuse

**Decision**: Use labeled sections, lists, native buttons and focusable labeled scroll regions; remove the current incomplete ARIA grid roles from the replaced surfaces. Use Tab/Shift+Tab, Enter/Space and normal scroll keys, explicit focus return and non-hover window disclosure. Do not introduce spreadsheet-style arrow navigation. Keep DOM order chronological despite visual lane placement.

**Rationale**: The specification needs an hourly visual grid, not a composite ARIA widget. The [WAI-ARIA grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) requires managed internal focus and directional navigation; visual CSS layout alone does not implement that interaction contract. Native controls provide the simpler supported behavior.

**Alternatives considered**: Retaining `role=grid` with only tabbed buttons misstates interaction. Implementing full composite-grid navigation adds unrequested complexity. List-only accessibility fails required in-calendar equivalents.

`adaptLecturerReviewToWorkspace` also consumes the shared workspace. Planner-only teaching context must not cause public lecturer review to fetch planner endpoints or expose extra calendars. Keep its existing authorized data/actions and show context as unavailable when absent. Regression-test the adapter and restricted page; do not broaden the public contract.

## 6. Verification and scope resolution

**Decision**: Use existing pytest, Vitest/jsdom, TypeScript build and ESLint. Add failing geometry/data-projection/contract/interaction tests before production. Real-browser layout, actual assistive technology, genuine text enlargement and five-person comprehension trials remain explicit manual acceptance work.

**Rationale**: jsdom checks cannot establish rendered proportionality or human comprehension. Existing locked dependencies suffice; no browser-test framework installation is required for this plan.

**Alternatives considered**: Screenshot-only checks miss contract/permission regressions; automated DOM assertions alone cannot prove visual or assistive usability.

All research questions are resolved. Backend changes are limited to read-only projection/schema, with existing authorization, validation, generation, persistence and snapshots untouched. No unresolved product or technology choice remains.
