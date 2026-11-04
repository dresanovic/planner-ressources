# Quickstart validation — I-005

This is a validation guide for the later implementation, not evidence that the feature is implemented.

## Prerequisites and environment

Use the repository's existing Node environment (`client/package-lock.json`) and backend virtual environment. From repository root, `npm --prefix client ci` installs the locked client dependencies if missing; from backend, `.venv/Scripts/python.exe -m pip install -r requirements.txt` installs existing development requirements if needed. Do not upgrade dependencies for this feature. Keep unrelated work intact and use a codex/ implementation branch/worktree because master was already dirty when planning began.

For manual scenarios, use a running supported development/test instance configured per [client README](../../client/README.md) and [backend README](../../backend/README.md), with an authorized planner login and an editable Working revision. Use isolated test data for any selection/generation/acceptance action. Do not restore, seed or mutate the user's live planner database to prepare this check. A fixture catalog must contain semester 2027 S with 94 courses and exactly eleven in MA IT & Wirtschaftsinformatik – 2. Semester; include other semesters, an empty-match cohort, similar labels, unavailable records, and a course with existing teaching sessions. Use the shared test fixture in client/src/test/fixtures/courseLists.ts for automated versions. For manual verification use an approved equivalent test catalog prepared through existing administration/import tools; record its actual counts before timing.

## Automated checks

Write the story's tests first and observe the expected behavioral failure before changing production code. From repository root:

```powershell
npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/AcademicDataPage.test.tsx src/App.test.tsx src/api/conflictAwareGeneration.test.ts
npm --prefix client test
npm --prefix client run build
npm --prefix client run lint
```

From backend (test fixtures use isolated databases):

```powershell
.venv/Scripts/python.exe -m pytest tests/api/test_planning_options.py tests/api/test_academic_catalog.py tests/services/test_academic_catalog.py tests/api/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation.py tests/services/test_conflict_aware_generation_concurrency.py
```

Expected: all focused/new tests and regressions pass, TypeScript/Vite builds, lint has no new failures. Existing API contracts and prepared evidence stay unchanged. Document any baseline failure separately; do not dismiss a regression as unrelated without comparing baseline output.

## Scenario 1 — Generation discovery (US1; FR-001–004, FR-007–008, FR-010; SC-001)

Open Planung > Kalender > Plan erzeugen > Stundenpläne erzeugen in 2027 S. Choose the target cohort. Expect exactly eleven matches from 94, identifiable course/cohort/semester, and no automatic selection. Individually select the eleven, review total eleven and exact course identities, then in the test instance verify that existing generation preparation uses exactly those IDs. Unavailable matching courses retain their reasons and cannot become eligible through filtering.

## Scenario 2 — Administration discovery (US2; FR-001–004, FR-012–013)

Open Stammdaten > Lehrveranstaltungen. Confirm initial all-semester scope; choose 2027 S and target cohort. Expect the same membership with equivalent status/eligibility context. Change active/inactive status and verify intersection, not replacement, of restrictions. Open one course action and verify exact record identity and existing validation. Enter an unsaved value, change/reset cohort filters, and verify the editor/value is preserved without mutation. Check all-semester access to legacy null-semester records and all-page matching (include a record beyond page one in an automated variant). Other catalog categories keep their current behavior.

## Scenario 3 — Complete selection and I-004 (US3; FR-005, FR-007–011; SC-002–003, SC-007)

Select two courses in cohort A, choose B, select one more: expect three selected, two hidden, all identities reviewable. A no-match filter must retain those three and still show their identities. Reset reveals checked items without changing IDs; clear-selection removes all IDs without changing the filter. At twenty selected, including hidden courses, a twenty-first cannot be added while permitted deselection works.

In the isolated test instance, select a course with saved teaching sessions, hide it through filtering and start generation: the unchanged I-004 comparison must include it and the entire joint result. Cancel retains all saved schedules; acceptance applies the whole candidate atomically. Test stale rejection, read-only revision, unavailable/missing selected records, and no silent pruning through automated integration/regression tests. Inspect request payload assertions to prove exact IDs. Filtering during an existing preparation/comparison must not alter captured evidence or accept a candidate.

## Scenario 4 — Lifetime, recovery and accessibility (US4; FR-005–006, FR-014–017; SC-004, SC-008–009)

Set different filters in both surfaces. Navigate away and back, including closing/reopening the generation pane and changing Academic Data category: each list restores its own filter within unchanged semester scope. It must not restore generation selection beyond that selection's existing lifetime. Cancel a guarded generation semester change and verify state stays intact; commit the change and expect unfiltered with existing selection reset. Return to the earlier semester: the old filter must not revive. Reset then leave/return: still unfiltered. Reload: both reset. A remembered cohort/semester removed during refresh remains visibly unavailable until explicit recovery rather than silently broadening.

Verify successful empty semester, filtered zero matches, loading and failed retrieval are distinguishable. In generation page tests, cover initial retrieval failure with no panel, pending initial load, successful empty options, failed refresh with retained selected records, and successful recovery. Failed freshness must not appear as no matches or allow a generation request; retained IDs and identities must remain reviewable. Use keyboard only for all listed actions, checking visible focus and no traps. With a screen reader confirm filter names/values, course/cohort identity, result/no-match updates, checked/disabled reasons and total/hidden selection counts. Use long names at 320 CSS pixels wide and 200% text enlargement: identifying text/actions remain obtainable, no clipped controls or feature-induced two-dimensional scrolling. Verify calendar-session filters remain unchanged.

## Timing and comprehension (SC-005–006)

After the 94-course catalog has loaded, record twenty cohort changes per surface in the browser performance recording, from committed user choice to visible matching rows and count. At least nineteen of twenty must finish within one second in each surface. Record device/browser and individual durations; do not include initial loading or substitute request latency for visible response time.

Have the planner perform the primary tasks without assistance or another tab. Ask them to identify active semester/cohort, every course that will generate including hidden ones, and reset versus clear-selection effects. Pass if correct on the first attempt. This acceptance exercise does not require new usability tooling.

## Evidence to record during implementation

Record red/green test outputs per story, final focused/full client and backend regression results, build/lint results, timing observations, screen-reader/browser/viewport used, and the planner walkthrough outcome here or in the implementation delivery evidence. Manual checks are practical test-first exceptions for rendered/assistive/user comprehension behavior; automated state and semantics checks still precede production changes. Unexecuted manual checks remain incomplete implementation work. See [contract](contracts/course-list-contract.md) and [data model](data-model.md) for boundary/state details.


## Implementation evidence — 2026-11-03

T001: Created `codex/i-005-filter-course-plan-list`, preserving existing dirty baseline (feature.json, backend README/backup script, restore script/tests, planning/process docs, and untracked I-005 artifacts). No reset, commit, push or merge.
T002: Existing client node_modules and backend .venv available; no dependencies installed/upgraded. Focused client baseline: 5 files / 99 tests passed. Sandbox Vite startup failed with spawn EPERM; approved unsandboxed retry passed. Backend baseline: 106 passed, 104 existing deprecation warnings (26.02s). Ignore files cover detected build/dependency/environment outputs; private npm application, no publishing ignore needed.

US1 T004/T005 red: both new discovery tests failed because the cohort control was absent. T006–T009 green: 71 tests across panel/page/API; exact eleven submitted IDs, hidden selection/reset and existing safeguards verified. Reused safeReasonText after existing regression caught raw codes. T003 shared 94/11 fixture added.

US2 T010/T011 red: missing semester filter and controlled state callbacks. T012–T015 green: 32 tests; eleven matches from a paginated 206-record catalog, null-semester all-scope access, unsaved editor retained on no-match/reset, no mutations, App navigation/category memory and fresh-mount reset.

US3 T016–T021: 77 panel/page/API tests passed before further code edits. Existing first-increment review already satisfies all-hidden 0/1/20/21, missing-ID fallback, unavailable removal, cap and captured complete I-004 scope; no API production change necessary. Existing API/backend tests remain authority for rejection and atomic/stale behavior.

US4 T022–T029: four intended red failures for failed freshness, parent failed refresh, admin error-as-empty and disappearing-result focus. After implementation 106 focused UI tests passed. Added initial pending/failure/empty recovery, disappeared cohort/selected ID and admin status/scope reset cases. CSS wraps scoped course controls/identities. Full client 66 files / 473 tests passed; build passed; lint passed after fixing one unused fixture variable. No extensions.yml exists; implementation/convergence hooks skipped.

Convergence pass 1: 55 requirement/acceptance items (17 FR, 6 TR, 9 SC, 23 story scenarios), 9 plan decisions, 6 governing principles, 34 tasks assessed against current implementation. F1 HIGH partial retry freshness bypass; F2 MEDIUM unrequested layout class on non-course catalogs; F3 HIGH partial no-op cancel regression; F4 MEDIUM partial actual manual acceptance evidence. Appended T035–T038 under Phase 8. Correction cycle 1 started. Manual checklist tasks T030/T031 remain unchecked.

Correction cycle 1: T035 red reproduced two prepare calls after failed refresh; now both retry handlers and retry button guard freshness. T036 new layout class limited to courses. T037 actual Abbrechen action asserts dialog removal, hidden acceptance and five stale/read-only rejections tested. 85 page tests passed.

Convergence pass 2: same 55 requirement/acceptance items, 9 plan decisions, 6 principles, now 38 tasks assessed. F1–F3 resolved. F4 MEDIUM partial remains for independent manual acceptance; browser fixture timing/keyboard checks reduce this gap but do not prove screen-reader speech or human comprehension. New F5 MEDIUM partial FR-017: admin editor intrinsic form field sizes overflow at 320 viewport (352 scroll width vs 305 content width); course controls/list themselves fit. Appended T039/T040 Phase 9; correction cycle 2.

Browser fixture preview: local Vite at http://127.0.0.1:5175/.tmp/i005.html, IAB browser, isolated mocked reads / mutation requests rejected, 94 courses with eleven target matches in each surface. No live database touched. Generation keyboard Tab/Space selected eleven, all-hidden zero-match review reached by keyboard and reset retained all selections. Admin keyboard selected no-match cohort/reset and opened first exact edit action. Accessibility tree exposes names/checked/disabled/total/hidden context; actual speech not assessed. At 320x850 viewport with 200% inherited text simulation: generation no overflowing descendants, document client/scroll width 305/305; admin course controls/list no overflow, editor overflow identified. The inherited-size simulation does not replace actual full text-only zoom verification. Screenshots in artifacts/i005-generation-320.png and artifacts/i005-administration-320.png.

Browser timing (commit via flushSync to second requestAnimationFrame, conservative visible-paint upper bound after loaded fixture catalog; local IAB):
Generation ms: 32.5, 33.4, 33.3, 33.4, 33.3, 33.4, 33.2, 33.4, 33.4, 33.3, 33.3, 33.4, 33.4, 33.3, 33.2, 33.4, 33.4, 33.2, 33.3, 33.4. 20/20 <1000ms.
Administration ms: 32.7, 33.3, 33.4, 33.4, 33.4, 33.2, 33.3, 33.4, 33.4, 33.3, 33.4, 33.2, 33.5, 33.2, 33.3, 33.3, 33.2, 33.4, 33.3, 33.4. 20/20 <1000ms. This isolates render predicates, not authenticated end-to-end workflow or live device performance. Planner comprehension and actual screen-reader checks remain unexecuted.


Correction cycle 2: T040 fixed intrinsic editor grid/field width using only course-scoped CSS. Browser recheck at 320x850 (200% inherited-size simulation): client width 305, scroll width 305, no overflowing course-grid descendants. Screenshot updated. Added explicit guarded-semester cancel/commit regression; 65 schedule-page tests passed.

Final automated verification:
- `npm --prefix client test`: 66 files, 475 tests passed (13.52s).
- `npm --prefix client run build`: TypeScript + Vite passed (89 modules; Vite 386ms).
- `npm --prefix client run lint`: final run initially found only a Fast Refresh export issue in the ignored local preview harness; corrected its component export, then rerun recorded below.
- Backend command above: 106 passed, 104 baseline deprecation warnings (35.53s). No backend application/test changes made by I-005.
- `git diff --check`: passed (line-ending notices only).

T034 requirement evidence audit:
| Intent | Implementation / verification | Status |
| --- | --- | --- |
| FR-001–004; SC-001 | Panel and AcademicDataPage predicates by ID, labelled context/count/metadata; shared 94/11 fixture, exact page request and all-page/null-semester tests | Automated PASS |
| FR-005, FR-007–010; SC-002–003 | Derived visibility, complete selected IDs, total/hidden review, missing-ID fallback, separate reset/clear, 0/1/20/21/unavailable cases and exact prepare payload; API selection validator unchanged | Automated PASS |
| FR-006; FR-011; SC-007 | Parent revision-keyed freshness, failed retrieval distinct from successful empty/no-match, initial/refresh/recovery tests, guarded retry, hidden comparison cancel/accept/stale/read-only and backend atomic regressions | Automated PASS |
| FR-012 | Local display predicates, unchanged editor key/values/actions/status retrieval, paginated and unsaved editor tests; no filtering mutations | Automated PASS |
| FR-013–014; SC-009 | App-controlled independent admin scope; schedule-controlled generation cohort; no browser storage or caches; navigation/fresh-mount, scope round trip, explicit reset and cancelled/committed guard evidence | Automated PASS |
| FR-015–016; SC-004 | Native controls, labels, status/live counts, keyboard fixture walkthrough, result-focus regression, browser accessibility-tree semantics | Partial: actual screen-reader speech pending |
| FR-017; SC-008 | Scoped CSS, actual 320 browser viewport, long identities, 200% inherited-size simulation and overflow measurements/screenshots | Partial: actual full text-only enlargement and full authenticated layout pending |
| SC-005 | Requires independent real planner first-attempt walkthrough | Pending |
| SC-006 | Browser commit-to-second-paint timings, twenty changes per surface, all <1s | Fixture browser PASS; not a live workflow performance claim |
| TR-001–004, TR-006 | Story red/green evidence, shared fixture, full client/API/backend regression, this mapping | PASS |
| TR-005 | Automated semantics plus actual keyboard/reflow checks; speech/full text-only enlargement exception still outstanding | Partial |

Tasks T030/T031 and convergence follow-ups T038/T039 remain unchecked: they require missing independent acceptance evidence. User replied “ok” to the initial availability question; this was not treated as recorded results or a named test instance. The local read-only preview now supplies an isolated fixture surface; user has been asked to record actual planner/screen-reader outcomes. No acceptance results invented. Scope/status updates preserve approved requirements and design decisions, marking delivery acceptance pending rather than complete.


Final lint rerun: `npm --prefix client run lint` passed (exit 0). The ignored read-only preview remains available for independent acceptance; it is not application production code or part of the built bundle.

Convergence pass 3 after correction cycle 2: 55 requirement/acceptance items, 9 plan decisions, 6 principles and all 40 then-current tasks assessed. F1/F2/F3/F5 resolved. F4 is the only remaining finding: MEDIUM / partial / TR-005, SC-004, SC-005, SC-008, T030/T031. Zero critical/high, missing, contradictory or unrequested code findings remain. Appended T041 under Phase 10 to trace the remaining independent acceptance work; outcome `tasks_appended`, not `converged`. No extension file or before/after hooks exist. No additional production changes are justified without actual acceptance evidence. Two of at most five correction cycles used.

Delivery status: NOT READY for independent code review under the requested completion criteria. 32 of 34 original tasks completed; 36 of 41 total tasks completed. Outstanding T030/T031/T038/T039/T041 all represent the same remaining independent acceptance obligations (partially exercised browser checks, not five distinct missing features). No code review, commit, push or merge performed. Unrelated original backend/process work preserved.


Continuation acceptance audit — 2026-11-03: current tasks still show only T030/T031/T038/T039/T041 outstanding; no independent planner or screen-reader results were supplied. Existing Vite process session 26986 was polled and is live. Attempted stronger full-text enlargement verification, but the existing browser tab and both documented tab-recovery paths fail with `browser.user is unavailable`; inventory still shows the fixture tab. No new rendered outcome was obtained. Temporary unverified harness changes were restored; production code unchanged. Prior recorded 475/106 test results remain the last verified automated evidence; no repeat tests claimed. Same external acceptance blocker remains (second consecutive goal-turn audit). Two correction cycles used; no new convergence pass or duplicate task appended without new implementation evidence.

Third consecutive acceptance-blocker audit — 2026-11-03: authoritative tasks and evidence remain unchanged; no independent screen-reader, full text-enlargement/authenticated-layout or real planner first-attempt results received. The prior turn yielded browser-availability evidence but did not resolve these acceptance obligations. No additional justified implementation work remains without external acceptance input. Goal marked blocked; NOT READY, 2/5 correction cycles used. Resume after supplying the outstanding acceptance results or an accessible test environment with a participating planner. No further duplicate convergence tasks or repeated test runs added.


## User acceptance sign-off — 2026-11-03

After receiving the acceptance instructions for the isolated preview, including planner comprehension, screen-reader operation and 320-pixel/200% text checks, the user replied: “it is ok and i give my pass”. Record this as the user's overall acceptance PASS for the remaining manual gate. T030/T031/T038/T039/T041 are closed on that user sign-off together with the previously recorded automated, rendered, keyboard and timing evidence.

Evidence provenance: the user did not supply browser/screen-reader versions or individual scenario observations. Those details remain unspecified; this record does not invent them or claim the agent independently heard screen-reader speech or observed the user's full text-enlargement procedure. The prior preview-only and browser-control limitations remain applicable to agent-observed evidence. No production or test changes were made in response to the sign-off. Production source modification times precede the final recorded automated checks (475 frontend tests, 106 backend regressions, build and lint PASS); those results remain applicable.

The explicit user acceptance resolves the external acceptance blocker. All 41 tasks are now checked. Two implementation/convergence correction cycles were used, within the maximum of five. Final convergence is assessed below; no code review, commit, push or merge is authorized or performed.


## Final convergence after user acceptance

Outcome: converged — the implementation satisfies the approved spec, plan and tasks with the user's manual acceptance sign-off. Checked 55 requirement/acceptance items, 9 plan decisions, 6 constitution principles and all 41 tasks. Findings by type (missing/partial/contradicts/unrequested): 0/0/0/0; critical/high/medium/low: 0/0/0/0. The previous sole acceptance finding F4 is resolved by the explicit user PASS recorded above, with its provenance limitations retained.

No convergence phase appended. tasks.md SHA-256 before and after this clean assessment: 860CD9263FFA07D247506E4EE92895403DAD3B43724724F1B89F6548FFB0E57D (byte-for-byte unchanged during convergence). Before/after implementation and convergence hooks: none registered (extensions.yml absent). Final task verification: 41 completed, 0 outstanding. git diff --check passed, with line-ending notices only.

READY for independent code review. Final verified automated results: 475 frontend tests, 106 backend regressions, TypeScript/Vite build and ESLint PASS. No production changes after those checks; acceptance closeout modified documentation/task status only. Two correction cycles used. No code review, commit, push or merge performed. Remaining evidence limitation: user acceptance is overall sign-off; exact browser/assistive-technology versions and per-check manual observations are unspecified.
