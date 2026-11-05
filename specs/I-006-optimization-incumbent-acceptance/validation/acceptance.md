# I-006 implementation and acceptance evidence

Updated 2026-11-05. Builder branch: codex/i006-optimization-incumbent-acceptance. Goal3 correction1/5 in progress; 0 completed. **Not accepted or ready for Goal4.** Approved spec/plan hashes unchanged; reviewer checklist16/16 read-only; no extension hooks. No code review, commit, push or merge.

## Current verification

Windows backend venv Python3.12.8. Node acceptance runtime24.22.1 at C:/Users/b50578/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe. Tests run outside sandbox because Windows sandbox temp/process restrictions previously prevented meaningful verification.

| Check | Command from backend or client respectively | Result |
|---|---|---|
| Final full backend including required performance protocol | ./.venv/Scripts/python.exe -m pytest tests --basetemp=.tmp-pytest/i006-cycle1-current-full --junitxml=../.tmp/i006-cycle1-current-backend.xml -q --tb=short | **746 passed,1 skipped,29 subtests passed**,1675warnings,624.74s. Log .tmp/i006-cycle1-current-backend.log; JUnit retains per-run evidence. Only test additions/removal after collection are separately verified below; production code stayed unchanged. |
| Current affected backend | pytest tests/services/test_optimization_worker.py tests/services/test_optimization_operations.py tests/services/test_semester_optimization.py tests/services/test_conflict_aware_generation.py tests/api/test_optimization_operations.py tests/api/test_conflict_aware_generation.py --basetemp=.tmp-pytest/i006-cycle1-reasons -q --tb=short | 199 passed,116 warnings,99.18s; .tmp/i006-cycle1-targeted.log |
| Exact candidate matrix | pytest tests/services/test_conflict_aware_generation.py -k exact_candidate --basetemp=.tmp-pytest/i006-validator-matrix -q --tb=short | 27 passed, including inactive room, unavailability and joint lecturer/room/cohort collisions |
| Current file-backed operation matrix | pytest tests/services/test_optimization_operations.py --basetemp=.tmp-pytest/i006-cycle1-decision-matrix -q --tb=short | 41 passed,21 warnings,44.43s |
| Shared deadline replacing retired55s reserve assertion | pytest tests/services/test_optimization_operations.py -k original_deadline --basetemp=.tmp-pytest/i006-shared-deadline -q --tb=short | 1 passed; child receives original captured start+300 deadline unchanged |
| Startup isolation regressions | pytest tests/api/test_ui_terminology.py tests/api/test_planner_authorization.py --basetemp=.tmp-pytest/i006-recovered-isolation -q --tb=short | 6 passed,24.78s |
| Final full client | Node24 node_modules/vitest/vitest.mjs run | 495 passed/67files,34.46s; .tmp/i006-cycle1-final-client.log |
| Final affected client | Vitest ReplacementConfirmationDialog, BatchResultSummary, CourseSchedulePage, useOptimizationOperation, conflictAwareGeneration API | 99 passed; later12 hook tests passed exact5s watchdog and duplicate/lost decision saved reconciliation |
| Static/build | Node24 node_modules/eslint/bin/eslint.js .; node_modules/typescript/bin/tsc -b; node_modules/vite/bin/vite.js build | Final Node24 ESLint,TypeScript and Vite production build passed (590ms) |
| Linux image | docker build --file infrastructure/docker/Dockerfile --tag planner-i006:validation . | Final corrected image built, SHA eba0ac98042f9efff83f07a950f723263f0da733e6976ecf22311c1636fff108 |

Earlier cycle1 full suite:730 passed,1 skipped,29 subtests passed,6 failures,627.86s. All6 were startup-isolation tests: four replaced SessionLocal without app.main.engine; two terminology tests used default DB. All6 now independently pass with temporary startup/request databases. No partial-schema guard was weakened and no local planner.db was repaired to hide an unshipped prototype schema. The earlier full run included the prescribed performance protocol and none failed. This is not a passing final full-suite claim. Prior unrelated Windows importer os.replace failures passed isolated reruns; importer production code was not changed.

A prior final client check was not executed because automatic approval review itself hit an account usage limit, not a safety decision. Resumed commands execute. No Goal/cycle counter reset.

## Isolated runtime and UI evidence

No production database/volume changed. Synthetic20-course1600-unit Spring2027 dataset: semester2/revision2,2027-02-01–2027-06-20;80units/course, separate cohorts, five shared eligible lecturers/rooms, weekdays08:00–18:00, session sizes2–6. No initial saved teaching/fixed exams in this runtime dataset; protected occupancy is covered separately in deterministic fixtures.

| Trial | Evidence and result |
|---|---|
| >60s plus mounted hot policy | runtime-long-run.json: captured300, optimizing past60s, status/health about2s; startHTTP0.062s/cancel0.297s. Host atomic directory-mounted replacement600/1200: next preparation600, A retains300. Cancelled/savedfalse, complete business-state hash unchanged. |
| External-to-app HTTPS proxy | runtime-https.json: separate TLS proxy container, loopback localhost18767, app18766, local CA and hostname verified,5s upstream timeout. Real300s operation still optimizing past60s with usable short requests. StartHTTP2.109s/cancel2.328s; immediate UI acknowledgement is distinct from durable response latency. Cancelled/savedfalse, state unchanged. This does not claim validation of an unspecified public production proxy. |
| Abrupt container kill/start | Same HTTPS record: unfinished receipt becomes interrupted, reviewnull/canAcceptfalse/canFinalizefalse/savedfalse, business state unchanged. Post-restart docker top showed only Uvicorn, no solver. |
| Abrupt spawned-parent exit | backend/tests/optimization_parent_probe.py, Windows pytest and Linux docker run --rm --entrypoint python --mount type=bind,source=C:/Codex/planner-resource/backend,target=/validation,readonly --workdir /validation planner-i006:validation -m tests.optimization_parent_probe: parent os._exit(0) after search starts; solver exits bounded on both platforms. Linux resource_tracker cleaned5sem objects after deliberate abrupt exit; no solver survived. |
| Control-channel loss | Real Windows spawn: parent stays alive, control writer closes, child exits before parent cleanup; close/reap idempotent. No DB engine/session/write callback supplied to worker. |
| Saved receipt recovery | Service and actual final-image container trial passed. runtime-saved-receipt.json:5s80-unit candidate awaited explicit decision, preference proof false, no predecision business mutation, accepted80units, late cancel returned saved; graceful restart recovered the identical saved result outcome-only without review/accept/finalize and business state unchanged. |

Actual UI:5s real search yielded valid80/80, coverage proven, schedule_shape unfinished/later priorities unattempted; unsaved and all8objectives scoped to prepared selection. Uninterrupted review valid120s.320/820/1280 CSS widths no horizontal overflow; dialog289px at320 and765px at820, sticky actions reachable, Tab/ShiftTab trap. Retry Back now restores focus to Erneut optimieren. Cancellation confirmed unsaved; terminal wording no longer claims pending checking. AX tree exposes course-labelled regions and separately named current/generated facts; this does not establish complete assistive quality.

**Pending:** long/twenty-course comparison at all widths; genuine200% text zoom; assistive phase/terminal checks; five representative unaided humans with>=4/5 within2minutes. Native zoom shortcuts left measured viewport/font/device ratio unchanged in the available browser. User explicitly stated human checks currently unavailable. Do not count component tests or AI votes as SC-008/009 evidence.

## Requirements and31-scenario audit

Evidence names below refer to current operation routes and tests, not retired synchronous calls. Every source item and existing task remains independently assessable regardless of markers.

| Source | Implementation/evidence | Status |
|---|---|---|
| FR001–004;US1/AC1–3 | Policy strict/default/fingerprint/hot-read API tests; no override; real directory replacement | Implemented/tested |
| FR005–007;US1/AC4–5 | Shared original deadline, actual exhaustion separate from elapsed review, distinct phases/requests, exact5s watchdog and >60s trials | Implemented; complete manual/assistive evidence pending |
| FR008–010;US4/AC1–2,8 | FEASIBLE/UNKNOWN/invalid/checkpoint/all-zero deterministic solver tests; independent exact validator; faults distinguished from timeout; available German no-candidate reasons | Implemented/tested |
| FR011–014;US2/AC1,4,6–7;US3/AC1–2 | Whole selection provisional review, zero-unit entries, manual/lower-coverage disclosure,100%coverage without preference proof still explicit acceptance, missing reasons stated | Implemented/tested; human comprehension pending |
| FR015–017;US2/AC2–3;US3/AC3,6–7 | Ordered candidate objectives, conditional fixed values, same-coverage-problem finite/provenance bounds, unknown gaps, prior candidate after UNKNOWN, saved scoped evidence | Implemented/tested |
| FR018–020;US2/AC5;US3/AC4–5;US4/AC3,5 | Exact stored candidate apply/no solve; fresh hard/input/revision validation, semester writer claim, all-selected transaction/receipt; current freshness/race/rollback tests | Implemented/tested |
| FR021–023;US4/AC4,6–7 | Memory authority, rowID+digest with actual delete/relogin/reusedID, owner outcome/cancel; epoch/tab/revision/hidden/pagehide/auth/refresh/unknown/saved reconciliation; parent/restart cleanup | Implemented/tested; independent reassessment pending |
| FR024–026;US5/AC1–4 | No-candidate/retry guidance, durable discard before new preparation/current policy, Back exact review/focus, no resume or improved-result promise | Implemented/tested |
| FR027 | Proven new auto-finalize, existing comparison, saved proof retained, old /generate and /accept409 | Implemented/tested |
| FR028–029 | German messages/reasons, proof/readable comparison, focus trap and Back restoration, phase semantics | Partial manual evidence |
| TR001 | Test-first red evidence for schema/policy/validator/control loss/no-candidate reason transport in continuity record; minor presentation edits verified within correction batch | Execution evidence retained |
| TR002–005 | Policy/deadline/real runtime; deterministic incumbent/proof/zero cases; exact hard rules/freshness; complete business-table equality on cancel/stale; decision races and recovery | Above matrices; final suite pending |
| TR006–007 | Matching contracts/endpoints/nullable evidence/passive headers/no-secret responses; frontend495, current full backend/performance run | Final backend result pending |
| TR008 | Actual keyboard/defined widths and associations, immediate local action and5s update deadline tested | Zoom/assistive/human evidence pending |
| TR009;SC001,SC010 | Documented20-course1600-unit2027S problem; captured policy/>60s/hot change, accurate cancelled/interrupted outcome/state integrity | Runtime evidence above |
| SC002 | Immediate requested-state UI, passive2s polls, unknown by lastconfirmed+5s, real health/status | Complete assistive path pending |
| SC003–007 | Current solver/service/API/contract/decision/proof matrices; protected/manual/exam/lifecycle regressions | Implemented/tested; final full result pending |
| SC008 | Five representative people unaided<=2min,>=4/5 correct | Unavailable, not passed |
| SC009 | Complete widths/keyboard/200%zoom acceptance | Partial, not passed |

## Task audit and Goal4 boundary

| Tasks | Evidence/remaining work |
|---|---|
| T001–006 | Reusable fixtures; migration/identity/auth/nullable/extra-field contracts; receipt model/schema and live-vs-outcome identity implemented/tested |
| T007–017 | Policy, original deadline/no reserve, process, joint validator, operation routes/lifecycle, passive polls, operator directory mount docs and tests/runtime |
| T018–027 | Deterministic incumbent/UNKNOWN/empty/zero/hard-valid review and whole-selection exact acceptance; current100/90/10 vs40/50/0,60/40/20 arithmetic; provisional/saved reasons; affected backend199/client99 |
| T028–034 | Ordered/conditional proof, safe bounds, candidate association, earlier retention and saved scope; solver/API/component tests |
| T035–042 | Explicit accept/finalize/cancel/duplicate/publication races; rollback/postcommit receipt, actual session replacement, material freshness/ignored changes/context invalidation; operation41/full regressions |
| T043–046 | Durable discard/current-policy retry, UI confirm/Back/no-resume/worse possible guidance and tests |
| T047 | Responsive styles and runbooks implemented; long20course/zoom/assistive evidence partial |
| T048–049 | Final backend running; client495/lint/type passed; final build pending |
| T050 | >60s/hot policy/Windows+Linux parent loss/TLS/unfinished restart complete; final image/container saved-receipt trial pending |
| T051 | Human/zoom/assistive/long comparison evidence pending |
| T052 | This audit covers FR/TR/SC and31AC; final results/independent verifier/acceptance still pending |
| T053–058 | Context/unknown/rejected-start/parent/control/fault/search-vs-review/watchdog/status corrections implemented/tested |
| T059–060 | Expanded current operation freshness/security/decision/transport/lifecycle/arithmetic/conditional tests; independent completeness assessment pending |
| T061–062 | Final full/static/build and remaining runtime evidence pending |
| T063 | Human/manual evidence remains pending |
| T064 | German actionable policy/config/reason/no-candidate/missing-evidence recovery implemented; affected tests passed |

Builder alone updates task markers based on evidence. Fresh verifier assesses everything, append-only tasks.md, source frozen during assessment. Goal3 completion requires clean independent convergence and passing current tests plus acceptance evidence. Human starts Goal4 separately in a fresh session only after Goal3 completion; no automatic transition.

## Final automated checkpoint

Current production backend full suite passed746 tests plus29subtests/1skip. Later test-only operation additions passed41tests plus the separately passed shared-deadline test; the old55second reserve assertion was replaced. Client495/lint/type/Vite passed. Prescribed20fresh reference runs and3x20workflow measurements are retained in performance-cycle1.json. Final independent convergence and pending manual/runtime items still determine Goal3 status.

## Final cycle1 runtime checkpoint

Final image eba0ac98042f9efff83f07a950f723263f0da733e6976ecf22311c1636fff108 built and saved-receipt recovery passed on actual Linux container, with explicit acceptance of an unproven80/80 candidate. Unsaved review cancellation after revision becomes noneditable additionally passed with complete business-table equality (1test). Parent/control/fault/deadline/freshness/decision tests and final current production full suite are green. The remaining essential manual/human evidence is unchanged.

## Correction cycle2 - current checkpoint (2026-11-05)

Fresh convergence_2 closed cycle1 with4 findings: lifecycle-rejected start, inaccurate noneditable regression, stale README, and pending manual evidence. Its only write appended Phase10/T065–T068;40597original bytes preserved, task SHA beforee32e1fb7943ba02014e9b0358792302effad9052b259731cbcab01c324391cb5/after9c58c3b09449b259d153d696aa3a47cd72a2d897169d774eab666a7b38a89298. No constitution MUST violation/unrequested addition was demonstrated.

Builder corrected T065 with tests first: four lifecycle cases failed because unknown stayedtrue; hook now treats revision_not_editable/working_revision_required/stale_lifecycle_state/semester_not_found as definitive rejection before receipt creation, frees the identity, retains German refresh/re-preparation guidance and permits a fresh attempt. Genuine uncertain-start reconciliation remains tested. Current HTTP tests prove published/abandoned/missing revision/missing semester create no receipt/worker/business mutation. Page tests cover released controls and fresh preparation.

**Correction to earlier evidence:** ready_for_review is editable. Earlier tests with that state did NOT establish noneditable cancellation/recovery despite their old titles. T066 now uses actual lifecycle publish/abandon transitions with asserted noneditable preconditions. Unsaved cancellation rejects both apply modes and late work, leaves no review/decision authority and preserves complete business state; committed receipts remain saved after both transitions/recovery/latecancel. These real cases supersede the overstated earlier claim.

T068 updated backend/README.md to the current short-operation endpoints, exact provisional acceptance, no saved-unit floor, and whole-selection stale rejection/atomic apply. Related infrastructure runbook checked consistent.

Verification: backend pytest tests/services/test_optimization_operations.py tests/api/test_optimization_operations.py --basetemp=.tmp-pytest/i006-cycle2-lifecycle -q --tb=short: **68passed,25warnings,51.37s**, .tmp/i006-cycle2-backend.log. No backend production changes since full746pass/29subtest/1skip/performance run. Current full client **503passed/67files**,14.79s, .tmp/i006-cycle2-client.log; Node24 ESLint/TypeScript/Vite passed,149ms build. Affected hook/page86passed. Full backend was not unnecessarily repeated for test-only/backend-documentation changes.

Cycle1completed1/5; correction2inprogress pending NEW fresh verifier. Source/spec/plan/tasks/tests/checklists frozen after evidence/marker update. Manual/human T047/T051/T063/T067 remain pending; user already confirmed human participants unavailable. Goal4 is not ready.

Final cycle2 packaging: Docker build passed, image305c47dd5bcbe9b5f8cc54a14959b687c2644e0641ea0081a28add3a42d70305. Backend runtime acceptance records remain applicable to the unchanged backend; lifecycle-start frontend correction is covered by503client tests and current build. An additional native Google Chrome zoom attempt was stopped by Computer Use because the current browser URL could not be determined confidently; no bypass or200%pass claimed. Browser segment ended cleanly. Source/tests/tasks/checklist freeze unchanged while convergence_3 completes.

## Final independent reassessment and shared stop - 2026-11-05

Fresh convergence_3 returned tasks_appended: only1partial/HIGH manual-evidence finding C3-F1, Phase11/T069. All68existing tasks,48FR/TR/SC,31AC,12plan groups,6constitution principles plus technology/workflow assessed. No additional implementation, automated-test or documentation gap established; no missing/contradicting/unrequested finding or constitution MUST violation demonstrated. T065/T066/T068 closure independently supported. Recorded746backend+29subtests/1skip,68current operation/API,503client/static/build and runtime/performance evidence independently inspected; no unjustified expensive rerun.

Append-only verified independently by Builder: original43990bytes identical,756bytes appended,length44746. BeforeSHA5402b843fc9fc4ad39f36fd1288be964a918b98a8461fe8764a9d535ec2e5480; afterdffddaf6f1ac331666c5dba78ac15c2887f650f24d397cacdeca662e503588ff. Spec/plan approved hashes unchanged. Requirements checklist untouched. Pre/post hooks absent.

Correction cycles completed2/5,currentnone. Stop for required human/manual acceptance under FR-029/TR-008/SC-008/009; user explicitly confirmed participants unavailable. Do not consume more cycles repeating unavailable checks or claim convergence. T047/T051/T063/T067/T069 remain open. After manual evidence is available, resume this SAME Goal3/counters, correct any concrete failures, and obtain a NEW fresh verifier. Goal4 is not ready and must be started by the human in a separate fresh session only after full Goal3 convergence. No code review, commit, push, merge or other Goal occurred. Detailed handover: goal3-handover.md.

## User-reported11-course run and correction3 (2026-11-05)

User screenshots user-11courses-start.png/user-11courses-cancelled.png show11LV/semester1/revision1/budget300, preparing at0elapsed and cancelled at2elapsed with unsaved feedback. User identifies MI,TI,Wirtschaftsinformatik. Whether cancellation was clicked or automatic is not yet confirmed; this is not a passed timing, database-preservation or human-comprehension trial.

New independent reproduction: development-origin preflight for the live poll's X-Optimization-Context header failed400. Header added to backend CORS allowlist, with both trusted dev origins passing and foreign origin denied. Current relevant API/auth/frontend40tests passed (27.56s), log .tmp/i006-cycle3-cors.log. Client and solver unchanged; previous full/backend performance results are baseline evidence, not a repeated full suite after middleware change. User's running process still exposes old middleware until fullrestart; restart instruction supplied, actual user-path re-test pending. Goal3cycle3inprogress/newfreshconvergence pending;2/5completed. All prior required manual/human evidence remains open.

User subsequently confirmed the11-course cancellation was automatic, not a deliberate cancel. This is a failed user-path observation; the CORS correction addresses the independently reproduced matching first-poll failure. Restart/retest outcome is still pending. Current cycle3Docker packaging passed (see .tmp/i006-cycle3-image.log). Fresh convergence_4 now assesses frozen source/current correction; tasks prefix unchanged at delegation.

## Current correction3 independent result

convergence_4 independently inspected current CORS/API/auth/frontend40pass evidence and build, checked69tasks/48requirements/31AC/12plan groups/6principles, and found only required manual evidence (1partial/HIGH). No additional code/test/docs gap established. Appended Phase12/T070 preserving44746originalbytes; final45498bytes/SHA4583acd810bd1dbfce4af9706737227bf7db04d242e68bcbde052de091142e20. Builder verified append-only independently. Cycles3/5completed,currentnone. Both Builder and verifier observed live8000preflight200/currentheader; actual11course retry pending user observation. No claim of new full suite after middlewarechange or completed manual acceptance. Goal4notready.

### User confirmation after CORS correction (2026-11-05)

User explicitly answered "Ja, der Lauf läuft weiter" when asked to retry the same11LV with the browser tab open and confirm continuation beyond the first2seconds. This closes the reported immediate automatic-cancellation symptom for that retry. No final candidate/proof/save outcome, precise timing,300second completion,20course/zoom/assistive or five-person acceptance result was reported; those are not inferred. No source/task/checklist changes or new correction cycle from recording this observation.

## New user-result analysis: optimality claim contradicted (2026-11-05)

User's actual11LVrun saved48sessions/192of358units/166remaining in24.3s,full objective proof reported. Read-only analysis found only window-start candidates; same cohort and4unit cap force48available day starts x4=192. However an additional Communication & Presentation2unit session on2027-02-19,19:40–21:20 passes the full exact validator jointly with all saved sessions, yielding194. No writes. Thus the192maximum/unit bound is not a trustworthy maximum of all hard-valid within-window assignments; missing later-start alternatives are a newly evidenced code/search-space issue. Source report analysis-11courses-20261105.md and user-11courses-saved-result.txt. No course has a saved holiday session; displayed holiday/action-failure/improved-zero wording also misleading. Previous manual-only conclusion is superseded by this concrete finding. User explicitly requested analysis; no production code or task marker edits, no correction4started. Counters3/5completed/currentnone; Goal4notready.

## Correction4 implementation checkpoint

Later-start regression and truthful result wording implemented test-first, scope authorized by user's implementation request. Detail/proof: start-time-completeness.md. Newsequential/release/oracle11pass; existing affectedbackend222pass; affectedUI84pass; currentfullclient504/67files+lint/type/Vite pass. Currentfullbackend/performance pending in .tmp/i006-cycle4-backend.log/.xml. Linux correctedimage34dd3b8dff09267ed3356caea6cb11604ae989d74b0cc6f3fe59af319d60aead builds and nativeinterval sequential/subminute smoke passes.

Real newmasterdata-only11LVtrial: real-11courses-cycle4.json records334/358LE,24remaining,154sessions,all11withsessions,2complete,300.406s,hardvalid,unsaved,databaseunchanged. Nativecoveragebound358,coverageunfinished,laterprioritiesnotattempted. This is a usable provisional candidate, NOT a proven334maximum. No userplans were restored or written. User had removed all planning tables' data; only94mastercourses and related masterdata remain. Cycles3/5completed/current4inprogress until NEW fresh reassessment; originalmanual/humanchecksremainpending.

## Cycle4 final result and final correction batch

convergence_5 resumed the same frozen assessment after a usage-limit error and completed all70tasks/48requirements/31AC/12plan groups/6principles. Eventclosure/NoOverlap completeness supported; no solvercounterexample found. Onlymanualevidence(HIGH,T071) andEnglishholidayprovisional/no-candidate wording(MEDIUM,T072) appended. Original45498taskbytes preserved,total47188,SHA3de69c99f8727b61653a32718c47746c3727fb189ceceaec0e0c332bbde9251f.4/5cyclescompleted;5inprogress.

Current fullbackend:768passed,1skipped,29subtests,1WindowsreportreplacePermissionError,871.91s. Exactisolatedimporterre-runpassed1in0.12s,codeunchanged; notcalledafullgreeninvocation. performance-cycle4.json retains20reference+60workflowruns,allunder30s(maxreference22.599s).

Userreportedcancelled11LVat286s/8LVat173s,below300budget,andisuncertainwhethertabchangedduetomultiplemonitors. Actualpasttriggerunknown; neitherbadsolverresultnorbudgetexhaustionwasrecorded. Approvedcontext/transportlosscancellationnotchanged. Cancelledfeedbacknowexplainspossiblecauseswithoutfalselyassertingoneorclaimingmorebudgetfixesit. T072holidaymessageslocalizedatthebackendandstructuredreviewformatter(testfirstfailuresrecorded). Currentaffectedbackend80pass/UI102pass;fullclientandisolated300sHTTPpollprobeongoing. User'srealapp/datawere notstopped/restored/writtentobyprobe.

## Final correction batch verification (2026-11-05)

Correction5/5 implemented T072: German holiday explanations with European dates in provisional review and serialized no-candidate evidence, preserving named source and excluded-possibility semantics. Cancellation guidance now names possible interruption causes without asserting the actual cause or recommending a larger time budget. No cancellation policy/schema changes.

Current focused backend:80passed,3warnings,33.06s (.tmp/i006-cycle5-backend.log). Current full client:506passed/67files; Node24 ESLint, TypeScript and Vite build passed (.tmp/i006-cycle5-client.log). Earlier algorithm-wide backend invocation:768passed,1skipped,29subtests,1unrelated Windows report-file replace PermissionError; unchanged isolated failing-test rerun passed. That full invocation remains recorded as having a failure.

Isolated real HTTP 300-second workflow on a backup of current database:11courses, status and health polls every2seconds, no errors, awaiting_decision after302.187seconds,316LE provisional candidate, coverage unproven, savedfalse. Explicit cleanup cancellation occurred ONLY AFTER reaching review. See validation/http-poll-cycle5.json. This is server/API evidence, not a browser visibility test. Different time-limited runs may yield different provisional candidates (prior solver-only trial334LE); neither establishes optimality. User application and database were not mutated. User clarified multi-monitor tab visibility is uncertain; original286second/173second cancellation trigger remains unknown.

T072 marked complete by Builder after tests. Manual acceptance remains pending, including genuine200%zoom, long20course responsive comparison, full keyboard/assistive checks and five representative two-minute comprehension trials with at least four passing. Source/tests/spec/plan/tasks/checklists now frozen for a NEW fresh-context final convergence assessment. Counter:4/5completed, fifth in progress until reassessment returns. No sixth correction cycle or automatic Goal4.

## Final Goal3 stop and handover — supersedes earlier counters/readiness (2026-11-05)

Correction cycles:5/5completed, none active. Fresh-context verifier convergence_6 returned tasks_appended/not converged. It assessed all72existingtasks,48requirements(29FR/9TR/10SC),31acceptance scenarios,12plan groups,sixconstitution principles plus constraints. Only finding C6-F1 HIGH partial: required manual acceptance remains incomplete; appended Phase14/T073. No further implementation gap, unrequested scope or constitution MUST violation established. T072 closure independently supported. This is not a clean convergence report or Goal3 completion.

Builder independently verified append integrity:47188originalbytes preserved,864appended,48052total. TasksSHA2567410b2b38ccb618c7f060279e586f848b3aadffa965b87b06322cd605a3f82f1; prefixSHA25670241fe9ca9d81d0af269e4092d8f36db82bbfcadfcee65cb2381b25546a4345. Approved specSHAeb3e992a8cde3ea3f0a0f336aa6efc0ba1513cd5475adec7a07cc296a4741c27 and planSHA987094405a845e7b88c033de6defadd96944daffb5125e07f8c3a42529f21948 unchanged. Requirements checklist remains16/16 and untouched; extensionhooksabsent.

Latest tests:80focusedbackendpassed;506fullclientpassed/67files; Node24 lint/type/build passed. Algorithm-wide backend run768passed/1skipped/29subtests/1WindowsreportreplacePermissionError; unchanged isolated rerun1passed. Full invocation not green. Performance20reference+60workflowmeasurements passed, maxreference22.599seconds; Linux exact-start/sequential smoke passed. See performance-cycle4.json/linux-cycle4.json. Isolated HTTP run11courses reached review at302.187seconds with316LEunproven,152successfulpolls,maxrequest0.094seconds,noerrors,savedfalse; explicitcleanupcancelafterreview. Prior isolated solver-onlyrun334/358LEunproven. These are provisional results, not a proof of optimality/full358impossibility and not browser/manual acceptance. User's actual286/173secondcanceltriggerunknown; multiplemonitors alone do not establish hidden-tab state. No user app restart, userDB mutation or deleted-plan restoration by these checks.

STOP: five-cycle non-convergence limit in docs/process/Spec-Driven-Development-Process-with-User-Manual.md. Do not reset counters, start correction6, waive human checks, mark Goal complete or start another Goal. Pending manual tasks T047/T051/T063/T067/T069/T070/T071/T073 all refer to the outstanding acceptance. Required: long20course comparisons320/820/1280CSSpx,genuine200%textzoom,fullkeyboard/focus/restoration+assistiveannouncements,fiverepresentativeunaidedtwo-minutecomprehensiontrialswithatleastfourpassing. Human participation explicitly unavailable.

Human decision required on remaining acceptance/non-convergence disposition. Goal4 is NOT started or currently declared ready. If the human later authorizes Goal4, use a separate fresh session with feature specs/I-006-optimization-incumbent-acceptance, branch codex/i006-optimization-incumbent-acceptance, this handover, approved artifacts, latest acceptance records and explicitly agreed Git scope. Goal4 must independently verify relevant evidence and the unresolved manual/full-suite caveats; it must not infer they passed from this handover. Preexisting planning/process/feature-pointer changes preserved; no Git delivery scope approved. No code review, commit, push, merge or new Goal performed. Platform Goal remains externally usageLimited; this manual continuation did not reset or falsely complete it.


## User-approved follow-up: LE visibility and preferred session size (2026-11-05)

This concrete follow-up was requested after Goal3 stopped; it does not reset the five-cycle counter or constitute a new Goal. User requested visible required/planned/missing LE and session LE, then explicitly requested preferred-first search, approved an optional course preference field, and explicitly authorized initializing existing data at the midpoint. Scope is recorded in docs/planning/Preferred_session_units.md.

Implemented course trace coverage from complete workspace course totals independently of occurrence/date filters; displays Benötigt/Geplant/Offen LE. Teaching list displays elapsed duration plus actual session.units and explains 45-minute LE versus breaks. Backend duration remains units*45+(units-1)*10. Current saved run inspected read-only:319/358LE,122two-LEsessions/25three-LEsessions; original timeout had not reached shape preferences. No false claim that all sessions were two units.

Added nullable preferred_session_units to courses, optional preferredSessionUnits in catalog and planning APIs, numeric optional German editor and min/max/preferred course display. Strict finite whole/half-unit values constrained by service to course min/max; empty uses exact midpoint, actual sessions stay integral. Both search decision order and later schedule-shape distance use the same captured preference; coverage/conflict/objective priority and hard rules unchanged, all allowed sizes remain available. Initial coverage search uses native fixed branching over nearest-preference choices; later stages retain normal search. Preference included in course fingerprint and detached worker input, so changed preferences invalidate old preparation.

Migration0012 initializes existing courses exactly once to (min+max)/2.0, preserves explicit later NULL/default choices on repeated startup. Backup:backend/backups/before-preferred-session-units-20261105-142720/planner.db. User dev reload applied migration; read-only verification94/94coursevalues equal midpoint, allselected49-59equal3.0, all draft_schedules/draft_sessions/exam_sessions rows exactly equal backup. Backend health200. No appointments regenerated, removed or automatically saved.

Test-first failures recorded for missing trace coverage, missing per-row LE, absent preferred validation and old initial search [4,2,2] versus requested [3,3,2]. Broad backend batch200passed,73warnings; operation/API/captured identity batch158passed,76warnings (overlapping coverage, not358unique); final optimizer53passed. Full client509passed/67files, final affected UI110passed after final course label; TypeScript, ESLint and Vite production build passed. Initial sandbox worker/temp-directory permissions required an elevated rerun; do not treat that invocation as passed. A production-build UTF-8 error in the edited German editor was corrected and build/types rerun successfully.

Isolated30second real11course solver trial (validation/preferred-start-11courses.json): first candidate at15.625seconds288LE,96three-LEsessions,0two/four-LEsessions; then fallback sizes increased coverage to293LE at30seconds (91three/10two). Exact joint hard validator passed, source/copied DB unchanged, savedfalse, coverage unfinished and upper bound358. This establishes preferred-first/fallback behavior, not optimality or a comparison with prior300secondruns. Existing saved319LE schedule preserved. Search order can affect time-limited candidates; no quality guarantee claimed.

Prior fresh convergence reports predate these follow-up changes and do not independently assess them. Goal3 remains stopped5/5/manual acceptance incomplete; no fresh convergence, code review, commit, push, merge or Goal4/newGoal performed. Future human-started fresh Goal4 must include these later source/schema/UI changes and updated evidence in its agreed scope.

## Prepared selection identity correction (2026-11-05)

User authorized correction of high-priority code-review finding 1. Three new CourseSchedulePage regressions failed before implementation: clearing selection, editing unavailable dates and entering invalid dates retained the old start action. Preparation is now invalidated synchronously on those edits; dispatch requires the current preparation epoch, and normal/retry preparation responses use the same context guard.

Node 24.22.1 verification: full `node node_modules/vitest/vitest.mjs run --reporter=dot` passed 515 tests in 68 files. After strengthening those three tests to click the stale start action before React rerenders, targeted `node node_modules/vitest/vitest.mjs run src/pages/CourseSchedulePage.test.tsx -t "invalidates prepared optimization" --reporter=dot` passed all three. `node node_modules/eslint/bin/eslint.js .`, `node node_modules/typescript/bin/tsc -b`, and `node node_modules/vite/bin/vite.js build` passed. Focused post-correction review found no additional issue in this correction. No backend change or backend rerun. Existing manual acceptance remains pending; the other two review findings are outside this correction.
