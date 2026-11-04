# Research — I-005

Repository evidence reviewed on 2026-11-03. Read-only generation and administration research agents were dispatched as required by speckit-plan. No external product recommendation or dependency upgrade is needed.

## 1. Filter existing response projections

**Decision**: Local predicates over complete loaded course lists; no backend work.
**Rationale**: client/src/api/planningOptions.ts exposes CourseOption.cohort, semesterId and availability; backend/app/schemas/planning_options.py requires semesterId. client/src/api/academicCatalog.ts exposes CourseRecord.semester, cohort, status and availability. AcademicDataPage.loadAllPages already retrieves the full catalog under the existing status restriction.
**Alternatives considered**: New server filtering/query parameters add unnecessary contracts and complicate selection coverage; filtering only the first page gives incorrect counts.

## 2. Independent page-session state

**Decision**: Generation cohort choice in CourseSchedulePage above the conditional panel; administration {semesterId, cohortId} controlled by App through props. Retain administration semester alongside cohort so navigation can return to the same scope. At a scope change discard the single previous cohort choice; no per-semester cache.
**Rationale**: App.tsx keeps CourseSchedulePage mounted in a hidden container and unmounts AcademicDataPage on leaving Academic Data. App state survives those transitions and resets on reload. CourseSchedulePage.requestSemesterChange already commits selection clearing after its navigation guard.
**Alternatives considered**: Panel-local state loses the filter on pane closure; administration-local state loses it on main navigation; browser storage survives reload against the confirmed decision; a global store/provider adds unnecessary indirection. Cancelled semester navigation must not reset anything.

## 3. Selection and operation remain independent

**Decision**: Pass all applicable courses and the original selected IDs into the existing panel. Only visible rendering is filtered. Keep startBatch, prepare/generate/accept payloads and I-004 evidence unchanged.
**Rationale**: CourseSchedulePage.startBatch defaults to selectedBatchCourseIds; a hidden existing course must still trigger decision_required. Panel currently counts all selected IDs but lacks richer hidden-selection review and unavailable handling.
**Alternatives considered**: Intersection with visible matches silently drops selections. Automatic selection/bulk operations add unconfirmed scope. Retain missing selected IDs with last-known display identity or an explicit unavailable ID fallback; never substitute or prune.

## 4. Identification and unavailable data

**Decision**: Display existing course name, cohort and applicable semester, using stable course ID as a distinguishing fallback. Do not add stored course codes.
**Rationale**: Neither CourseOption nor CourseRecord nor backend Course currently defines a course reference code. The specification requires available identifying references, not a new academic field. Existing generation availability reasons must remain visible; newly unavailable items cannot be newly selected, while existing unavailable selections must be removable when permitted and submitted only under established validation.
**Alternatives considered**: Adding a code schema expands academic data scope. Using lecturer/room reference codes as course identity would be incorrect.

## 5. Empty/error and editor preservation

**Decision**: Track course-list retrieval outcome distinctly from no-match results; preserve existing editor/action identity and status query.
**Rationale**: AcademicDataPage currently reports loading errors through message and ends loading in finally; an empty records array alone cannot distinguish failure. Filtering must not set selected, call edit selection, change editorGeneration or rewrite options used by an open edit. Null-semester legacy records remain discoverable in all-semester view.
**Alternatives considered**: Treat failure as zero matches misleads users. Rebuilding editor state on filtering violates FR-012. Broad list redesign is unnecessary; a scoped metadata slot preserves other categories.

## 6. Verification and scope boundaries

**Decision**: Existing Vitest/jsdom, build/lint and pytest regressions plus manual accessibility/timing checks; no new toolchain.
**Rationale**: client/package.json exposes test/build/lint. Actual reflow and screen-reader speech require browser/manual evidence. Requirements explicitly request test-first delivery. Existing API/service tests cover invalid sets, stale acceptance, atomic decisions and rollback.
**Alternatives considered**: New end-to-end/performance infrastructure is not necessary for this slice. Backend changes or new general observability would exceed the demonstrated need.

**Resolution**: No unresolved technical clarification remains. Source files and exact commands are listed in plan.md and quickstart.md; no tests were executed by the research agents.

## Cycle 2 research correction — parent retrieval state

**Decision**: Handle generation initial/refresh retrieval outcomes in CourseSchedulePage as well as panel messages, with parent-page tests. Keep retained records/selected IDs for explanation, but distinguish failed freshness from successful emptiness and prevent generation from a failed-refresh context until existing reload/recovery succeeds.
**Rationale**: CourseSchedulePage owns getPlanningOptions and renders an initial optionsLoading/unavailable fallback outside the panel. On refresh it can retain planningOptions. Panel-only tests cannot prove these page-boundary states or guard behavior. Tasks T024/T025 and the contract now explicitly cover both boundaries.
**Alternatives considered**: Panel-only state tests miss the parent fetch path. Clearing options/selection on failure loses user context and violates selection preservation. A new HTTP error contract is unnecessary.
