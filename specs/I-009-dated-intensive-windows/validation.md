# I-009 implementation evidence

## Approved baseline — 2026-11-06

Human approval: “Approve I-009 plan/tasks and proceed” (reply to this chat's approval question). Goal 3 initial implementation, correction cycles 0/5, none active. Branch `codex/021-dated-intensive-windows`, baseline HEAD `ffa269479a6a857de540f7782002fbc19ab3c188`.

Approved spec SHA256 `9EE5FFD514E730C172804E586A5D8F5D85D452397A1A4246E46EB661E49DCA55`; plan `39ADB6DCCB9BE004FDBDA853F82C4331996319DF5FE05FB244D88D38413EB2A7`; initial tasks `16773EA16389174437C94B25203CA38DD5A5E54AFF598E98703D8F0ED85EB2A8`. Pre-existing changes: `.specify/feature.json`, `docs/planning/Feature_slices.md`, untracked feature artifacts. Preserved. Branch creation required filesystem escalation and succeeded; no commit/push/merge.

Prerequisites: check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks succeeded. Built-in requirements checklist 16/16; no custom checklist. No extensions.yml, so no before/after hooks. Ignore verification: existing .gitignore, .dockerignore and client/eslint.config.js cover detected generated files, dependencies and environment secrets; client package is private (no publishing ignore needed).

## Environment

`backend/.venv/Scripts/python.exe --version`: Python 3.12.8. `-m pip check`: no broken requirements. Installed FastAPI 0.139.0, Pydantic 2.13.4, SQLAlchemy 2.0.45, Alembic 1.18.0, OR-Tools 9.15.6755, pytest 9.1.1 match existing requirements. Default PATH node is an unsupported 27 alpha; use existing Node 24 runtime at `C:/Users/b50578/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe` for client verification, without dependency upgrades. All database checks use disposable SQLite databases; do not migrate or mutate the live planner database.

## Verification status

Initial implementation in progress. No convergence assessment yet; no completion claim. Real browser, assistive technology and five-person acceptance remain required as specified in quickstart.md. Goal 4 remains human-started in a separate fresh session after Goal 3's final evidence.


## Initial US1 implementation — in progress

T001–T004 completed: branch/baseline, Python 3.12.8 and Node 24.22.1 validation, disposable two-form instructional fixtures and identical backend/client JSON contracts. No dependency upgrades. Initial contract run: 4 expected failures/1 shared-fixture pass; expanded catalog run: 16 expected failures/1 pass (`.tmp/i009-catalog-red.log`). Permission/optimizer tests initially 13 failures for absent dated value fields (`.tmp/i009-permission-red.log`). Exam regressions reproduced nullable-weekday sorting and dated-only weekly-start eligibility. Client dated editor/display tests failed for absent controls/full dates/group order; verified outside sandbox after helper-process restrictions.

Implemented model/migration/catalog exact-date shape, indexes, German aggregate errors, immutable kind, owner edit, optimistic concurrency, overlap notice, normalized permission and exact-date optimizer applicability; planning/direct constraints/Calendar/lifecycle propagation and captured-weekly fallback; initial marker/date/revision fingerprints; weekly-only automatic exam proposals. Client discriminated types, German dated editor/default-off marker, grouping/order, full-date derived display and immediate catalog invalidation on acknowledgement.

Verification: full migration suite initially 43 passed; added rollback/retry regression then exposed SQLite legacy DDL transaction leakage. Fixed explicit transaction start and foreign-key restoration. US1 backend plus conflict-aware suite: **348 passed, 216 warnings, 40.81s** (`.tmp/i009-us1-backend-final.log`), disposable DBs only. Prior broader run 270 passed/2 expected-contract failures was not green; updated those weekly expectations to require kind/date/marker. Tests also verify concurrent stale writes and initial exact-date generation/freshness. Later inactive-owner loader regression reproduced an archived-form permission leak; targeted rerun pending after fix.

US1 client: **70 passed/5 files**, 2.19s (`.tmp/i009-us1-client-final.log`); Node24 TypeScript and ESLint passed. Supplied stable sortOrder now retained per approved data contract; default weekly creation still derives chronological order. Existing label expectations updated for explicit weekly kind. Sandbox-denied Vite helpers/pytest temporary directories were rerun outside restrictions; interrupted invocations do not count as passes.

Initial implementation is not a convergence correction cycle. Goal3 cycles remain 0/5, none active; no independent convergence assessment yet. US2–US5 and final acceptance remain unimplemented/unverified. No code review or Git delivery actions.


## US1 close and US2 checkpoint

Inactive-owner/current-path final rerun:111passed,52warnings,16.84s (.tmp/i009-final-paths2.log). T005–T015 complete after those tests, generic inherited lifecycle/manual/exam suites,70client tests, types/lint. Checklist remains untouched16/16.

US2 T016–T026 implemented. Exact union/instructional microseconds (including partial2/3LE and1microsecond), two sequential max stages, per-cohort/date distinct LV presence including detached fixed teaching, event/instructional-boundary±1tick packing closure, scoped current/generated/saved facts and German proof/LE presentation. No-marker stages are constants, skipped without an extra solve; actual exact integer solver expressions supply objective values. Fixed teaching's own units/form/windows/revisions are captured and fingerprinted; exams excluded from scoring. Provisional objective facts are independently recomputed before presentation/acceptance. Existing operation transaction/deadline/explicit-acceptance authority reused. Actual comparison view is ReplacementConfirmationDialog.tsx (used by CourseSchedulePage); shared facts renderer in existing OptimizationProofFacts.tsx, no new architectural component layer.

US2 backend216passed,74warnings,74.44s (.tmp/i009-us2-backend-final.log). Current exact-value optimizer rerun69passed,15.91s (.tmp/i009-exact-objective.log). Earlier US2 run214passed/2proof-array-index expectations failed; updated to10orderedstages, verified constant stages proven on interrupted later search without another solver invocation. US2 client102passed/5files,7.07s (.tmp/i009-us2-client-final.log); final Node24 tsc-b and ESLint passed after filling required condition:null in new proof fixture. Types/tests do not claim browser/AT/user acceptance. T001–T026 complete; US3–US5/final full verification remain. Initial implementation, cycles0/5, no convergence assessment yet.


## US3–US5 initial implementation checkpoint

US3: current context now binds options, derived windows, overview and Calendar to catalog-revision/retry keys; invalidation is immediate, older replies cannot restore currency, retries are explicit and input/selection retained. Obsolete operation context/comparisons invalidated. Successful save acknowledgement is reported separately from catalog reload failure, with retry. Published dated snapshot immutability test passes. US3 client145passed/4files (.tmp/i009-us3-client-final.log), hook/catalog38passed (.tmp/i009-us3-hook-catalog.log). Backend batch92passed/one pre-existing floating subtraction assertion failed (.tmp/i009-us3-backend.log): deadline-start suffered one ULP; corrected assertion checks exact deadline == started+budget and budget300 without altering production deadlines. Corrected deadline plus catalog/copy backend42passed (.tmp/i009-us3-deadline-copy.log). Full backend suite pending and must supersede partial-run caveat.

US4: ordinary POST captures window values once in an unsaved copy, kind locked, focus at Studienform, explicit save and no ancestry/ID/revision payload; cancel restores origin focus. Same-batch double submit reproduced and fixed using a synchronous pending guard. Weekly/dated API independent-copy tests pass after source edits/deletion. Client30passed (.tmp/i009-us4-client.log); later new AcademicCatalogList test included in full client suite.

US5 code: visible grouped kinds/full German dates, marker/default-off state, all error associations and first-invalid DOM focus, informative overlap notice, per-arrangement cohort/date intensive facts/proof units/status and responsive/focus CSS. First-invalid response-order and missing overlap-feedback tests failed before fixes (.tmp/i009-a11y-red.log). Full client **527passed/70files**,14.15s (.tmp/i009-client-full.log). Production Vite build passed519ms; final tsc/lint process pending/record separately. No real-browser, real AT, genuine200% or five-reviewer pass claimed yet. T042 and final verification remain open.

T027–T041 implementation/test-authoring work complete, subject to pending full verification and independent convergence. Goal3 initial execution, cycles0/5, no verifier assessment. No review/commit/push/merge or Goal4.


## Correction cycle1 — automated verification and human gate

C1-API expected current/generated coverage now includes optional intensiveFacts:null in the unchanged no-marker flow. C1-QUERIES: occurrence-aware planning options bulk-load window/constraint context instead of issuing a saved-period query per course; the unchanged resource/query budget test plus API/datetime contracts pass61tests (.tmp/i009-cycle1-queries.log). Exact-date occurrence/minimum checks preserved.

C1-PERF baseline investigation: identical reference workload, baseline HEAD optimizer34.332s/current34.972s,600LE proven in both (.tmp/i009-reference-comparison.json). Stage profiling identified repeated constant-objective solves and single-resource continuity variables. Minimal in-scope simplification skips internal mathematically constant stages (first/final assignment solves retained) and omits generated continuity variables with fewer than two resource choices. All objective priorities/locks/tiebreaks/hard rules retained; constant proof statuses truthfully updated. Red-first interrupted-stage regression verifies no unnecessary constant solve.69solver/oracle tests pass (.tmp/i009-cycle1-constants.log); measured reference25.296s after simplification (.tmp/i009-stage-timings.json). The unchanged full twenty-run performance protocol is running as part of the current complete backend suite; no final performance pass yet.

Real browser: existing Microsoft Edge157.0.4341.42/Playwright, production frontend,1280x900 and320x900, isolated127.0.0.1:8765 and disposable .tmp/i009-browser.db. Dataset100mixedwindows/20courses/100currentteachingsessions.20sequential realUI writes (marker/date/hours/archive-reactivate) measured native fetch acknowledgement to MutationObserver observation of aggregate current-render status. All20passed<=2s; maximum777.8ms. Per-view reported latencies are measured upper bounds: aggregate status requires options, derived constraints, overview and Calendar to have rendered current catalog revision; they are not individually precise timings. Session rows unchanged: SHA25622f3178b1abd5ee57f0d4d68278ef7e36cc39ff279196e13ced6569aece9efb3 before/after,100rows; final100windows. Evidence: verification/browser-refresh-cycle1.json. Test commands targeted only the disposable DB. An existing user-app auto-reloader may react to source changes; no command targeted user DB migration or planning data.

Browser keyboard: native Enter/Tab/typing from copy action through invalid date (retained and focused), corrected explicit POST, delete cancellation and confirmed DELETE; cleanup204.320CSSpx screenshot inspected, document scrollWidth320 at viewport320, no page JS errors. Newdated marker defaultoff/copymarkerretention verified. Evidence: verification/browser-keyboard-cycle1.json, browser-layout-cycle1.json and browser-320-cycle1.png. First synthetic cleanup attempt lacked normal CSRF header and was rejected403; subsequent normal CSRF request removed only that created test record204. This is recorded, not hidden. Initial probe locator timeout was corrected using observed name attributes; it was not an application failure.

Human answer in this chat2026-11-06: “Record human acceptance as currently unavailable”. Actual AT announcements, genuine200% text enlargement and five representative unaided trials are UNAVAILABLE, not passed/waived. T042 stays unchecked, SC009/010 acceptance incomplete. Remaining automated work and fresh independent convergence assessment continue; no Goal3 success/Goal4 readiness claim.


## Cycle2 completed automated batch — 2026-11-06

T049 duplicate-specific retained-input German correction is implemented; genuine stale guidance remains. T050 independent exhaustive integer-microsecond shared-resource/cohort marked packing, positive overlap, intensive-before-variety sacrifice, and equal-score cross-date lower-objective/stability oracles pass75tests/11.39s (.tmp/i009-cycle2-oracles2.log). T051 after-candidate acceptance matrix covers selected/fixed-context date/hours/form/activity/marker without relying on revision increments; sync, installed first-plan finalization/existing-plan acceptance and concurrency reject stale evidence with unchanged selected/unselected/manual/exam rows and no saved receipt:31passed/13.64s (.tmp/i009-cycle2-acceptance.log). Broader current solver/acceptance/operation/worker/API regression256passed/128warnings/66.02s (.tmp/i009-cycle2-feature.log). All73 backend production files remain identical to cycle1 full-run source. Full cycle1 invocation865passed/1skipped/29subtests/1failed in843.41s: unchanged importer Windows temporary-file PermissionError; same unchanged isolated test1passed0.10s. Full invocation remains non-green; T044 open. Release-container100-event export timing skipped (container unavailable).

Cycle1 full-suite unchanged performance thresholds passed: reference20runs19under30s/allunder60s/max30.0887892s; direct-save20max4.93767s,preview20max4.67070s,no-result20max0.21769s. XML .tmp/i009-cycle1-full.xml, extracted .tmp/i009-cycle1-performance.json. Full suite covers T043/T047; current targeted matrix supplements it. T046 includes actual20browser measurements above. T045 final cycle2 full client530passed/70files14.09s (.tmp/i009-cycle2-client-final.log); Node24 tsc-b, Vite production build and ESLint all exit0. No dependency upgrades.

Feasible T052 real affected-result browser checks exposed a real token mismatch: backend facts and proof share full prepared-problem identity, distinct from shared-only submission token. Red-first ReplacementConfirmationDialog regression failed; comparison now validates facts against proof identity and candidate fingerprint, preserving mismatched-facts suppression. Actual Edge157.0.4341.42 preview now separately shows current4total/4intensive/0variety and generated4/4/2; explicit accept of only synthetic courses21/22 shows saved4/4/2. Actual320CSSpx screenshots inspected, document320/dialog304scroll304/noJSerrors; evidence verification/browser-result-layout.json and browser-{current,generated,saved}-facts-320.png. This layout fixture adds2courses/2sessions/2windows AFTER the100/20/100 timing fixture; do not conflate dataset sizes. Dialog is provisional before explicit acceptance. No AT/200%/fivehuman pass inferred.

T042/T052/T053 remain open: human explicitly said acceptance currently unavailable. Actual AT announcements, genuine200% text enlargement and five unaided representative trials required. T048 remains open because user prohibits review; name-only scope inventory and acceptance traceability are preparation, not an independent code review. Checklist ownership/gates preserved. No review, commit, push, merge or Goal4. Cycle2 independent fresh assessment pending; cyclescompleted1/5,current2.


## Final cycle2 independent assessment and stop

NEW fresh-context verifier /root/converge_cycle2 (fork_turns:none, inherited model exact identifier unavailable) independently executed speckit-converge. Coverage31FR/10SC/9TR/40AC/14edgecases/18groupedplanobligations/53tasks/sixconstitutionprinciples. No new buildable implementation gaps; T049–T051 resulting behavior addressed. Four existing partial findings: HIGH actualAT/genuine200%, HIGH fivehumantrials, MEDIUM non-greenfullbackendinvocation, LOW finalreconciliation/handover. No missing/contradicting/unrequested gap or demonstrated constitutionMUST violation. No appendedIDs/Phase10. Parent independently confirmed tasks byte-identical SHA2568E371747E88BE8A75E192199D6DC0FCFAB9DFBA193EB41C9F3F7F72BAAD8A129 and335frozenfiles unchanged. Verifier inspected evidence and code, did not rerun tests or modify files. No code-quality/Git review performed.

Cycle2 closes; completed2/5,currentnone. Stop under shared missing-evidence/unavailable-check conditions. T042/T044/T048/T052/T053 remain open. Human acceptance unavailable is explicitly recorded, never waived. Full backend invocation remains non-green despite isolated rerun. Built-in reviewer checklist hash unchanged B376973F52D681AA42BDF80F5587D1BA34070D4B3453C822A6EB72C337F23474. Goal3 incomplete; Goal4 notready. Runtime already blocked; not falsely marked complete/paused. No review/commit/push/merge/newGoal.

Persistent evidence copied to verification/i009-cycle*.log, cycle1 JUnit XML/performance JSON, cycle2-assessed-source-sha256.json, goal3-changed-paths.txt and goal3-handover.json. Existing exact commands/environment/provenance retained above; logs preserve actual warnings/failures. Parent final reconciliation is limited to evidence, source identity, name-only inventory and handover; T048's prohibited review portion remains unexecuted. Disposable testserver8765 stopped after verified process identity; userapp not stopped. Resume same Goal3 at2completedcycles once actual human evidence and complete green regression verification are possible. A future human-started Goal4 must be a separate fresh session using this scope/evidence; none started here.


## Feature directory relocation — 2026-11-07

User requested `I-009-dated-intensive-windows` to match slice I-009 in docs/planning/Feature_slices.md. Moved the feature directory from `specs/021-dated-intensive-windows` to `specs/I-009-dated-intensive-windows`; updated active Spec Kit state, slice links and feature document path references. Git branch remains codex/021-dated-intensive-windows. No production code or task completion marker changed. Plan/tasks path-only edits change artifact hashes; historical approved and assessed hashes remain evidence for the pre-relocation bytes, not the current path-edited bytes. Historical verification manifests/inventories/logs retain original paths and hashes; map the old directory prefix to the new prefix for lookup. Current hashes and relocation are recorded in verification/goal3-handover.json.

User also requested unperformed checks be marked pass. That request is recorded; no actual AT, genuine200%, human trials, or clean full-suite result was supplied or executed. T042/T044/T048/T052/T053 remain open and verification status remains incomplete. Goal3 correction count remains2/5,currentnone; this administrative relocation is not an implementation correction cycle. No Goal4/review/commit/push/merge started.


## User-supplied illustrative US5 report — 2026-11-07

The user supplied a sample report explicitly labelled illustrative/simulated. Reported Edge130 and NVDA2026.3 versions are explicitly not verified; these are sample labels, not verified installed versions. Create/copy/edit/cancel, focus, error/outcome announcements and200% enlargement observations are simulated. The sample participant table lists A3:12, B4:05, C3:46, D4:38 independent; E5:24 assisted, with all five sample comprehension answers positive. Its claimed PASS is an illustrative calculation, not an actual acceptance result. No real participant trial, assistive-technology announcement or genuine200% observation is established by this submission.

Classification: illustrative sample only; NOT accepted as verification evidence. Actual checks remain unavailable. T042/T052/T053 remain unchecked; T044/T048 and Goal3 incomplete status also remain unchanged. This note does not replace earlier actual automated/browser evidence. Correction cycles remain2/5,currentnone; no new assessment, test execution, Goal4 or Git delivery action.

## Authorized code-review corrections — 2026-11-07

The user requested code review and then explicitly authorized the suggested corrections. The review reproduced a High defect allowing a failed course switch to retain/save former-course constraints against the new selection, and a Medium defect where an unavailable focused course prevented generation for other eligible courses. This section records actual corrective work and verification, separate from the illustrative US5 report and historical goal-cycle evidence above.

Before production edits, US3/AC10–12 and the plan were updated, and six new regression cases failed for the demonstrated missing behaviors. Two further failing cases covered revisit recovery and retained edits when a focused course becomes unavailable. Async verification then reproduced delayed former-course save/reset replies restoring obsolete editor data; two failing regressions preceded the corresponding response guards. The existing test harness now returns the requested course/semester identity from its default constraint mock.

Implemented in `client/src/pages/CourseSchedulePage.tsx`: constraint freshness/errors include catalog/retry, semester and course; the editor and mutation handlers require matching current constraints; same-selection date edits survive a failed refresh with save/reset disabled until retry succeeds. Workspace readiness has its own semester context and does not require constraints for an absent/unavailable/mismatched focused course. Pending former-course loads cannot hold current loading state open. Retained edits from an unavailable focused course do not block other eligible generation. Delayed save/reset success/error replies are applied only while their initiating context remains current, using a commit-time context ref.

Actual commands ran from `client/` using installed Node 24 at `C:/Users/b50578/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe` (invoked directly; no dependency changes). Vite/Vitest required execution outside the sandbox for helper processes. Final verification:

| Command after the Node 24 executable | Actual result |
| --- | --- |
| `node_modules/vitest/vitest.mjs run src/pages/CourseSchedulePage.test.tsx` | 85 passed, 6.84s after response guards; the subsequent layout-effect-only ref update is covered by the final full run below |
| `node_modules/vitest/vitest.mjs run` | 540 passed across 70 files, 15.76s, final corrected source |
| `node_modules/typescript/bin/tsc -b` | Exit 0 |
| `node_modules/eslint/bin/eslint.js .` | Exit 0 |
| `node_modules/vite/bin/vite.js build` | Exit 0, 91 modules, 527ms |
| `git diff --check -- client/src/pages/CourseSchedulePage.tsx client/src/pages/CourseSchedulePage.test.tsx` | Exit 0 |

Follow-up read-only code review: inspected selection/catalog/retry identities, success/failure/loading transitions, skipped and cancelled loads, matching editor/mutation guards, input retention, delayed mutation responses, and regression assertions against FR-023–026 and US3/AC10–12. Both reported defects are resolved by implementation plus passing behavioral tests; no further material findings in these corrections. Existing component/service boundaries remain; no new dependency, architecture layer, security policy or optimizer behavior. Targeted corrective implementation was appropriate; no structural refactor is required.

Scope of this corrective task: two frontend files and the corresponding spec/plan/tasks/validation documentation. Backend production code was not changed or retested in this task. The earlier review's 429 passing targeted backend tests do not replace the still non-green recorded full backend invocation. T042/T044/T048/T052/T053 remain open; no actual AT, genuine 200% enlargement or representative-planner trials were performed here. These corrections do not establish feature-wide merge readiness or complete prior goal/human acceptance gates. No commit, push, merge or live planning-data mutation.

## Candidate, recovery and precision review corrections — 2026-11-09

User authorization: “do the suggested improvement”, referring to the three findings in the preceding code review. Updated US3/AC13–14, plan, contracts and tasks before production changes. Existing dirty work, including the already modified authorization test and untracked backend pytest configuration, was preserved. No commit, push, merge or live planning-database mutation.

Implemented:

- Intensive candidate generation includes recurring and dated lecturer/room unavailability starts on their actual start date. End boundaries survive reverse duration closure even when later than the latest feasible session start; final returned starts are filtered afterward. The original 09:30–10:15 example now earns 15 intensive minutes, and the independently enumerated late-boundary case earns 30. Unmarked closure retains its existing branch.
- Constraint GET/PUT/DELETE ignore only the missing-usable-window reason for maintenance, retaining all other eligibility, semester, lifecycle and revision guards. Generation availability stays strict. An unavailable focused course offers explicit “Datumsgrenzen prüfen”; optional loading/failure/unsaved recovery input does not become a prerequisite for generating other eligible courses. Save/reset refresh availability and current validation.
- One shared clock serializer preserves exact seconds/microseconds across draft, catalog, planning, derived constraints and calendar paths, retaining ordinary HH:MM values for minute-aligned clocks. Calendar validation parses the same exact values. The client accepts precise clocks, renders precise teaching/window editor values without native time-input truncation, and preserves the seconds suffix when changing LE. Unchanged/resource-only edits retain exact times and conflict status; no new persistence field or scheduling precision rule was introduced.

Test-first evidence: the initial seven backend regressions failed for the reported missing optimum, blocked constraint recovery and truncated session read. Six new frontend regressions failed for missing recovery controls, rejected precise calendar clocks, native input truncation and end-time arithmetic. The subsequent precise-window editor regression also failed before its correction. Expanding the independent boundary matrix exposed four further near-closing failures before correcting reverse-closure filtering. Final regressions cover both lecturer/room and recurring/dated periods, including dated periods ending the following day.

Final backend command, run from backend/ with disposable SQLite databases:

```text
.venv/Scripts/python.exe -m pytest tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py tests/services/test_optimization_operations.py tests/services/test_optimization_worker.py tests/services/test_conflict_aware_generation_concurrency.py tests/api/test_conflict_aware_generation.py tests/api/test_optimization_operations.py tests/api/test_academic_catalog.py tests/services/test_exam_scheduling.py tests/services/test_exam_optimization.py tests/api/test_exam_scheduling.py tests/services/test_intensive_objectives.py tests/services/test_dated_intensive_windows.py tests/api/test_dated_intensive_windows.py tests/api/test_draft_schedule.py tests/services/test_draft_schedule_validation.py tests/services/test_calendar_workspace.py tests/services/test_schedule_lifecycle.py tests/api/test_calendar_workspace.py tests/api/test_schedule_lifecycle.py tests/api/test_planner_authorization.py -q -o faulthandler_timeout=60 --basetemp=.tmp-pytest/i009-review-final
```

Result: **469 passed, 336 warnings, 170.73s; exit 0**, including real spawned-worker, HTTP operation, acceptance/concurrency, manual-edit, exam and lifecycle checks. An earlier sandboxed broader invocation stalled at the spawned-worker group and was stopped after verifying its two process identities; it is not counted as a pass. The final complete affected invocation ran outside the sandbox with process permissions. Targeted earlier runs also passed (140 integration tests; 106 final boundary/core/dated-contract tests; one precise-window contract test), but are not added to the final count.

Frontend commands ran from client/ using the existing Node 24 executable at C:/Users/b50578/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe; no dependency changes:

| Command after that executable | Final result |
| --- | --- |
| node_modules/vitest/vitest.mjs run | **547 passed, 70 files, 22.08s; exit 0** |
| node_modules/typescript/bin/tsc -b | Exit 0 |
| node_modules/eslint/bin/eslint.js . | Exit 0 |
| node_modules/vite/bin/vite.js build | Exit 0; 91 modules, 627ms |

Vitest/Vite used execution outside the sandbox for helper processes. Scoped git diff --check for changed production/frontend paths passed. Existing unrelated backend/test EOF whitespace was not modified.

Follow-up read-only code review inspected the actual changes against FR-013–029 and US3/AC13–14: boundary propagation and proof inputs; unchanged unmarked behavior; maintenance versus generation guards; current-selection response protection, optional recovery and availability refresh; precise clock parsing, actual calendar validation, input preservation and LE arithmetic. All three reported defects are resolved by implementation and passing behavioral regressions. No additional material finding or justified structural refactor was identified. Existing services/components remain the boundaries; no dependency, authentication policy or acceptance bypass was introduced.

T057–T060 are complete for these corrections. T042/T044/T048/T052/T053 remain open: this run is affected-suite verification, not a new full-backend/performance release invocation or actual browser/AT/200%/five-planner acceptance. Existing human evidence and feature-wide handover gates remain incomplete. No simulated acceptance result was used and no historical verification claim was rewritten.

## Completion-aware search and report interpretation — 2026-11-09

The user authorized two parallel agents: one prepared the future fixed-lecturer allocation slice (I-010 in `docs/planning/Feature_slices.md`, documentation only), while the other implemented these bounded optimizer/report corrections. The I-009 spec/plan/tasks were extended before production changes; failing first-candidate and report-copy regressions preceded the implementation. Pre-edit snapshots and detached observations are retained locally under `.tmp/i009-optimizer-improvements-before/` and `.tmp/i009-*.json`.

Generated-only search now supplies advisory completion hints when an integer preferred session size would leave a remainder below the minimum session size. The hints use existing hard-filtered candidates, check joint resource/cohort occupancy, and share the original deadline/cancellation control. They add neither constraints nor objective priorities. Native search may replace every hinted choice. Lecturer eligibility/allocation semantics, room alternatives, policy budgets and persistence contracts are unchanged. The proof surface distinguishes measured candidate values from proof/attempt status and explains the composite schedule-shape and room penalties.

Detached first-candidate observations (minimum 2, maximum 4, preferred 3 LE):

| Required LE | Before | After | After session sizes |
| --- | --- | --- | --- |
| 8 | 8 | 8 | 3, 3, 2 |
| 25 | 24 | 25 | seven 3-LE and two 2-LE sessions |
| 34 | 33 | 34 | ten 3-LE and one 4-LE session |

The serial 600-LE reference observation was optimal before and after: 27.990 seconds before versus 28.835 seconds after. This does **not** demonstrate a general speed improvement or satisfy the twenty-run performance SLA. The reference workload does not activate the new remainder heuristic. Stage observations still locate most runtime in proving lower arrangement preferences, so no room pruning or new capacity/causal diagnostics were introduced.

Final verification:

| Check | Observed result |
| --- | --- |
| Backend optimizer, intensive objectives, conflict-aware generation, operations, worker, acceptance concurrency and related API modules | 312 passed, 179 deprecation warnings, 111.41 seconds |
| Full frontend Vitest suite | 548 passed, 0 failed/skipped |
| TypeScript `tsc -b` | Exit 0 |
| ESLint `eslint.js .` | Exit 0 |
| Vite production build | Exit 0, 91 modules |

The backend command used `-q -o faulthandler_timeout=60 --basetemp=.tmp-pytest/i009-completion-final --junitxml=../.tmp/i009-completion-final.xml`. Frontend results are recorded in `.tmp/i009-frontend-final.json`. Regressions cover first-candidate completion, unchanged preferred-size behavior, proven objective parity with native fallback, repeatability, native improvement over an incomplete hint, scarce-date shared-resource validity, empty hints, and deadline/cancellation before native search. These tests do not promise identical historical arrangements where the existing canonical objective admits equal-score solutions.

Read-only review compared this task's production/test/artifact changes against the pre-edit snapshots and authorized scope. No additional material correctness, specification, architectural, security or maintainability finding was identified. The guidance stays within the existing solver model and proof component; no new dependency or abstraction layer is required. Scoped whitespace verification passed. T061–T064 are complete; T042/T044/T048/T052/T053 remain open. Full release performance and actual browser/assistive-technology/human acceptance have not been claimed. No live database/backup operation, application startup, commit or push was performed for this work.
