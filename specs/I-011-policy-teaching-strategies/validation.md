# I-011 implementation validation

## Authorized start and isolation (2026-11-09)

The human invoked `$speckit-implement` and then said “continue”; implementation
starts under that instruction and the plan/task approval recorded in
`goal-progress.md`. No runtime Goal was created or transitioned.

- Approved plan SHA256: `9A7E16C118C9A01EB369077DC72910FC5F302D5C84418582CA34A081EE42C63C`.
- Approved initial tasks SHA256: `99C25001E0F9E284A4AB47E71B94E38817048B61ABBAAE671E941F34EA1FFD69`.
- Baseline HEAD: `9a13127efcc6e3a698698f3060c02209e9015eff`, initially on `master`.
- Implementation branch: `codex/I-011-policy-teaching-strategies`.
- Preexisting untracked paths: this feature's `goal-progress.md`, `tasks.md`,
  and `verification/`. No tracked production/test changes at start.
- Python: existing backend virtualenv, 3.12.8. Node: v27.0.0-alpha.0.0.0;
  npm: 11.13.0. Node differs from the planned Node 24 environment and npm emits
  an unsupported-version warning; frontend results must identify that limitation.
- Tests use detached fixed-date inputs and disposable databases/policy files.
  No live database, policy, application session, commit, push or merge is used.
- Requirements checklist: 16/16 checked, read only. No extensions.yml present.
- Existing ESLint global ignores cover node_modules/dist/build/coverage/minified
  files. Client is private, so no npm publishing ignore is required. Git/Docker
  ignores reviewed; missing critical generic patterns added separately.

## Execution evidence

Unchecked tasks remain outstanding until their concrete evidence exists.

### Baselines and setup

- T002: captured `single`, `competition`, `protected_exam` results before changing
  production strategy code. Fixed snapshot SHA256 and complete deterministic
  result facts are in `backend/tests/fixtures/teaching_standard_baselines.json`.
  Baselines plus unchanged exam optimization tests: **6 passed**.
- Detached preference/portion/competition fixtures and temporary-policy/database
  helpers added. Fixture tests: **6 passed**, including 1/20-course disposable
  database initialization. T003 remains open for complete named-fixture coverage.
- Sandbox pytest temp-directory permission failures were resolved by running
  isolated tests outside the sandbox with workspace-local `--basetemp` paths.
  No automatic-approval rejection occurred.

### Test-first policy, identity and Standard increment

- Shared fixture parity plus backend serialization/coverage/profile/order/bound
  tests: initial **13 failed, 23 passed**, with expected absent identity/profile
  fields and missing coverage validation. Backend contract suite now passes.
  T004/005 remain open for complete portion/selection/review-contract coverage.
- Client decoder tests initially **8 failed, 19 passed** on unsupported
  selector/profile/termination responses being accepted. Read-only identity UI
  test initially **1 failed, 12 passed** on missing algorithm text.
- T007: strict policy cases initially **13 failed, 27 passed**, including absent
  installed-file resolution and selector identity. T011 now implements strict
  source-relative policy/explicit override, German provisioning diagnostics,
  canonical selector/profile/settings/budget fingerprints, and effective defaults.
  Live `config/optimization/policy.json` was not changed.
- Migration/new-schema tests initially **2 failed, 1 passed** for missing durable
  fields and migration. Migration 0015, historical Standard defaults, partial-state
  rejection and schema detection added. Policy + full migration suites:
  **86 passed**. T008/012 remain open for complete populated historical saved-payload
  and invalid-value acceptance coverage.
- Lifecycle tests initially **2 failed** for missing captured identity and
  algorithm-only pre-Start policy change. Receipts/status/detached input/review/save
  now capture identity. Frozen Standard identity survives policy deletion and
  idempotent replay. Historical overscheduled current-plan comparison regression
  found and corrected; generated exact validation still prohibits overallocation.
  Broader policy-lifetime/candidate-fingerprint evidence remains outstanding.
- T020: Standard registry adapter test initially failed at import because the
  module did not exist. Four adapter/unknown-ID tests now pass, with exact baseline
  facts preserved. Worker dispatch uses the registry. Only Standard is registered;
  missing algorithms fail without fallback. Synchronous service retirement (T021)
  is still outstanding, so no claim of all teaching paths being integrated.
- T016: example provisioning, source-relative path and required directory mount
  documented; compose sets an explicit container path. Example includes Standard
  and preserves 900/1800 budgets. No container/live deployment was exercised.

### Requested performance comparison (user steering during implementation)

The human additionally requested performance tests comparing algorithms. The
comparison harness was brought forward ahead of the original T049 dependency
order for that request; this does not complete the prerequisite algorithm work.

- Harness self-tests initially **3 failed** for missing scenario/measurement
  functions, then pass with the actual measurement implementation.
- Matrix covers single/cohort-competition/shared-lecturer/intensive/partial-week/
  20-course snapshots, identical two-second allowance per strategy, independently
  checked legality, coverage/remaining LE, weekly loads, objective proof/bounds,
  elapsed search time and termination. Every strategy gets detached fresh inputs.
- Actual comparison: **9 passed, 12 failed**. All six Standard cases schedule full
  demand; twelve cases report Cohort/Lecturer unavailable, because their concrete
  searches are not implemented. Missing implementations are failures, never skips
  or substituted Standard timings. No performance advantage is claimed.
- Measurements and scope are in `verification/performance-comparison.json` and
  `verification/performance-comparison.md`. Only in-process search is measured;
  spawned deadline/cancel/API latency/checkpoint evidence remains outstanding.
  T049/050 are not marked complete.

### Current-code verification and remaining work

- Backend command with config, migrations, shared contracts, Standard adapter,
  baselines, operation lifecycle and real worker suites: **212 passed**. Executed
  via existing venv with `PYTHONPATH=backend` and disposable workspace basetemp.
- Client API/component/hook tests: **84 passed** across the five non-page suites;
  page suite rerun after correcting its full API mock: **93 passed**. Combined
  affected-suite total **177 passed**. Client build and lint pass. An intermediate
  page build exposed a non-UTF-8 inserted character; corrected to UTF-8 and rebuilt.
- New runtime is Node 27 alpha rather than planned Node 24. npm warns about this;
  repeat client acceptance on supported deployment Node before final delivery.
- No extension hooks file at final check; no post-implementation hooks registered.
- External activity changed `docs/planning/Feature_slices.md` during this work;
  those changes were inspected and preserved without modification.
- **I-011 is incomplete.** Concrete Cohort/Lecturer construction/repair/scoring,
  ordered portions, independent portion validation, complete proof/freshness/UI
  lifecycle work and full acceptance/manual/runtime checks remain. The comparison
  suite intentionally stays red until the real implementations satisfy it.
  No commit, push, merge, live DB migration or live policy modification performed.

## Implementation continuation — 2026-11-10 (supersedes earlier incomplete status)

The human continued implementation. Standard, Cohort and Lecturer are now concrete strategies, not aliases or fallbacks. T001–T052 are complete. T053 is partially complete and T054 remains open for final acceptance closure because the manual conditions below could not all be exercised. The earlier missing-strategy failures above are historical red evidence; the current comparison is green.

### Delivered behavior and regression corrections

- `teaching_strategies.py` provides the static Strategy registry. Standard delegates unchanged to the existing optimizer. The worker is the production teaching-search entry point; retired synchronous generation/acceptance raise `OPERATION_API_REQUIRED`. Existing synchronous tests were migrated to real operation lifecycle or pure Standard search, with a name/coverage inventory in `verification/retired-service-tests.md`. Exams retain their existing paths.
- `teaching_preferences.py` implements exact rational preference scoring, feasible-opportunity weeks, owner-specific fixed loads, intensive overlap, scarcity and stable ties. `heuristic_teaching.py` constructs globally shared provisional assignments and repairs detached immutable states. A run spends at most 1,000 attempted alternatives, with at most eight displaced sessions per attempt. Repeated repair passes share that same cap. All scoring, enumeration, reconstruction and finalization retain cancellation/deadline checks; checkpoints preserve strict improvements and periodic refresh.
- Lecturer derives immutable normalized-code/identity-ordered portions, honors existing explicit targets, conserves shared demand and requires predecessor completion plus chronology. Independent exact validation reconstructs the authoritative expected portions before review and save. Unfilled portions expose remaining demand and predecessor-block or search-uncertainty facts.
- Strict required-file policy resolution is independent of cwd, with explicit deployment override, immutable captured identity and idempotent replay before policy access. Migration 0015 adds constrained receipt metadata, backfills historical Standard and preserves stored saved JSON. Legacy saved results are normalized on detached output only.
- Heuristics never claim preference optimality or auto-finalize. Nonempty independently valid candidates enter explicit review; zero-total candidates cannot save. Freshness, Working revision, protected occupancy, atomic acceptance and cancel/lost-response reconciliation remain enforced. Read-only German identity, proof, termination, saved state and ordered shares appear throughout preparation/progress/review/results, without an allocation editor or request selector.

Test-first corrections observed during this continuation included missing preference/heuristic modules, contract and portion validation, legacy receipt normalization, and actual search defects. Concrete red/green regressions also cover:

- A one-million-LE requirement with only one two-LE opportunity initially exhausted its budget building an unnecessary remainder table; capacity-bounded incremental cost construction now returns the valid two-LE partial result.
- A 25-LE/seven-date fixture initially stranded demand at 21 LE; residual capacity now excludes the proposed/used dates, and repair releases old own demand for moves/resizes. The fixture reaches 25 LE without invalid sessions.
- Cancellation arriving during final packet construction initially allowed publication; a post-finalization cancellation check now rejects it.
- The intensive fixture now uses actual dated intensive windows. Its stricter regression exposed failure to revisit earlier groups after later improvements; bounded repeated passes now reach variety 2 under the regression allowance. The two-second performance case truthfully retains its earlier valid checkpoint when time runs out.
- A fresh preparation could display a previous cancelled/saved operation's algorithm. The page now gives fresh preparation identity precedence; the new failing page test passes.
- Preparation decoding now rejects unsupported metadata; legacy saved receipt output uses captured identity without mutating persistence.

Arithmetic consistency correction: the spec/quickstart example `[6,3,3]` with weights `[1,2,1]` now states **49.5**, since `36 + 9/2 + 9 = 49.5`, replacing 40.5. Formula, priority and preference ordering are unchanged. Therefore the current spec bytes differ substantively from the approved hash by this explicit arithmetic correction; no claim of byte identity is made.

### Final automated verification

All tests use detached fixed-date inputs, disposable policies and databases under ignored `.tmp` directories. Python 3.12.8 / Windows 11; existing virtualenv. Spawn-capable pytest/npm commands ran with approved escalation because sandbox temporary-directory/process restrictions prevented ordinary execution. No automatic-approval rejection occurred.

| Check | Current outcome | Evidence |
|---|---|---|
| Full relevant backend suites | **563 passed**, zero failures/errors/skips, 191.261 s | `verification/backend-results.xml` |
| Algorithm performance/control suite | **33 passed**, 31.77 s | `verification/performance-results.xml`, comparison JSON/Markdown |
| Full client suite | **605 passed**, 70 files | `npm --prefix client test`; local `.tmp/i011-client-final.log` |
| ESLint | Passed | `npm --prefix client run lint` |
| TypeScript and Vite production build | Passed | `npm --prefix client run build` |
| Migrated legacy pure-Standard workflow performance probes | **3 passed**, 20 repetitions per context | `test_semester_optimization_performance.py` migrated probes; historical 21-run reference probe not rerun |
| Whitespace | Passed | `git diff --check` |

The final backend command used `PYTHONPATH=backend`, `-q --tb=short --basetemp=.tmp/i011-release-verification --junitxml=specs/I-011-policy-teaching-strategies/verification/backend-results.xml -o junit_family=xunit1` and these files:

```text
backend/tests/services/test_optimization_config.py
backend/tests/services/test_teaching_preferences.py
backend/tests/services/test_teaching_strategies.py
backend/tests/services/test_heuristic_teaching.py
backend/tests/services/test_teaching_strategy_baselines.py
backend/tests/services/test_teaching_strategy_lifecycle.py
backend/tests/services/test_semester_optimization.py
backend/tests/services/test_optimization_worker.py
backend/tests/services/test_optimization_operations.py
backend/tests/services/test_conflict_aware_generation.py
backend/tests/services/test_conflict_aware_generation_concurrency.py
backend/tests/api/test_teaching_strategy_contracts.py
backend/tests/api/test_teaching_strategy_acceptance.py
backend/tests/api/test_optimization_operations.py
backend/tests/api/test_conflict_aware_generation.py
backend/tests/services/test_exam_scheduling.py
backend/tests/services/test_exam_optimization.py
backend/tests/services/test_dated_intensive_windows.py
backend/tests/services/test_intensive_objectives.py
backend/tests/services/test_schedule_lifecycle.py
backend/tests/db/test_migrations.py
```

Performance reproduction is in `verification/performance-comparison.md`. Its latest invocation additionally used `--basetemp=.tmp/i011-final-comparison --junitxml=specs/I-011-policy-teaching-strategies/verification/performance-results.xml`. All 18 same-snapshot/two-second cases are independently hard-valid with full coverage. Different profile preference scores are not equated. Standard achieves greater intensive variety than the heuristics within this measured allowance; no universal gain is claimed. Weekly maps include relevant fixed teaching and need not equal selected demand alone. Real worker sections separately record six dispatch runs, expired deadlines, active cancellation and original absolute allowance enforcement.

### Connected and manual observations

- Isolated FastAPI endpoint acceptance with actual spawned workers passes all three algorithms × 1/20 selected courses: captured preparation/progress/review/saved identities, complete selected-course accounting, no save before acceptance, then atomic save and post-commit cancellation reconciliation. Recorded endpoint timings are extracted from JUnit into `verification/connected-acceptance.json`; these are TestClient measurements, not network measurements.
- Separate real TCP HTTP/Uvicorn runs on loopback port 8712 exercised Start and immediate cancellation for the same six combinations. Maximum observed Start was 0.031 s, cancellation 0.094 s, and saved planning tables remained identical. These cancellations may occur before child startup; the benchmark also checks active-worker cancellation. Exact observations are in `verification/http-latency.json`.
- A disposable local app on port 8711, launched from a different cwd with explicit temporary policy, was exercised through the real built frontend. Three 22-LE courses under Lecturer produced an unsaved 66-LE review. Course 1 showed ordered 11/11 lecturer portions; heuristic preferences remained unproven. Explicit acceptance saved 66 LE across the three courses with no reported conflicts. Live operator data was never used.
- At a 400-pixel viewport, client and scroll widths both measured 385 px; no horizontal overflow was observed. Review actions remained reachable. Tab/Shift-Tab exercised the modal focus loop. Progress updates did not steal focus. Browser keyboard zoom shortcuts did not change DPR/viewport, so this is **not evidence of true 200% zoom**. Accessible text/roles were checked, but **screen-reader speech was not tested**.
- While the isolated server ran, deleting its temporary policy left health at HTTP 200, blocked new preparation with HTTP 503 `OPTIMIZATION_CONFIGURATION_INVALID`, and atomic replacement restored successful Lecturer preparation. Policy path/permissions/atomic changes also have automated isolated coverage. No claim of real container permissions is made.
- Docker CLI could not reach `dockerDesktopLinuxEngine`; the daemon was not running. **Actual deployment directory-mount and container permission/missing-file smoke tests remain unavailable**. Compose/documentation are supplied, not runtime deployment acceptance.
- Both disposable Uvicorn processes were identified and stopped after their checks. Temporary files/databases remain under ignored `.tmp` for reproducibility.

### Requirement evidence and remaining acceptance boundary

| Requirements / success criteria | Implementation and evidence |
|---|---|
| FR-001–007; TR-002/003; SC-001/002 | Registry, strict policy, receipt migration/capture, worker/operations; config, migration, contract, lifecycle and real endpoint 1/20 matrices. Container runtime portion of FR-004 remains open. |
| FR-008; TR-008; UI portion of SC-009 | Client decoding, read-only identity and German proof/termination/share surfaces; full client tests/lint/build, real narrow/keyboard/focus check. Speech/200% zoom remain open. |
| FR-009; TR-004; SC-003 | Pre-change Standard baseline hashes/facts, unchanged solver delegation and exam/intensive/lifecycle regressions; retired synchronous paths reject. |
| FR-010–019; TR-005/006/009; SC-004/005/008 | Exact candidate validator, rational preference and constructive/repair tests: exact22 rhythm, owner distinction, fixed loads, dates, size redistribution, competition, rollback, cap and per-phase cancellation/deadline; comparison real worker/control sections. |
| FR-020–024; TR-007; SC-006/007/009 | Profile/proof contracts, independent validation, whole-selection operation/service/API/client lifecycle matrices, protected-state comparisons, concurrent exactly-once acceptance and lost-response/cancel reconciliation. |
| FR-025/026; TR-010; SC-010 | Ordered portion derivation/explicit precedence, no bypass/transfer/alternation, independent corruption/freshness rejection and accessible review facts; Lecturer search/API/client regressions. |
| TR-001 | Historical intended failures above and continuation red/green regressions; baseline capture is preservation evidence rather than a failing behavior test. Real browser/deployment/assistive checks follow the plan's manual exception. |

This is an implementation/self-review handover, not an independent review or unconditional release approval. Automated requirements are green; the manual acceptance boundary remains T053/T054. Node is still 27 alpha rather than planned supported Node 24, and npm emits a compatibility warning; repeat deployment client checks on the supported runtime. The remaining FastAPI TestClient warning concerns the existing httpx deprecation, not a test failure.

External changes to `docs/planning/Feature_slices.md` and `infrastructure/docker/Dockerfile` were inspected and preserved; they are excluded from this feature's implementation claims. Live policy SHA256 remains `4C20E12A7610DB25E76E9479AD0AC9EE5F4F041A84AF3E9B6017C3C41032EB67` (900/1800). No live DB migration, commit, push or merge was performed. Requirements checklist remains 16/16 and untouched. No `.specify/extensions.yml` exists at the final hook check, so no post-implementation hook is registered.

## Convergence implementation — 2026-11-10

The user invoked `$speckit-implement` for T055–T059 and continued the interrupted invocation. The requirements checklist passed 16/16 and was left unchanged. The preexisting modified/untracked feature, catalog, infrastructure and export/import files were preserved. No spec or plan changes, new dependency, live policy edit, live database access, commit, push or merge was required. Existing Git/Docker/ESLint ignores cover this work; the client is private and has no publication requirement.

### Search corrections and test-first evidence

- **T055 complete.** Three new construction-trace regressions first failed: Lecturer processed owner 3 before owner 2; Cohort retained a completed course's group scarcity; zero-demand work changed group order. Construction now retains `(owner, course)` work, restricts Lecturer placement to that owner's ready portion and recalculates the ordering from outstanding demand after each course/portion. Repair retains its owner and reconstructs affected demand through the same traversal. Hard code-order predecessor completion and chronology remain mandatory. Focused preference/search/strategy verification initially passed 71 tests.
- **T056 complete.** Four new in-loop cancellation/deadline regressions first failed because scarcity and intensive scoring did not accept search control. A fifth regression failed because packet construction crossing the deadline published the unfinished new incumbent instead of retaining the earlier complete checkpoint. Scarcity, intensive scoring, rhythm/balance, remainder-capacity and outstanding-demand scans now check the captured control. Packet construction checks control through its loops and after the constructor; state, score and completed packet become the incumbent together. Deadline return only updates constant-size metadata on the retained immutable packet, without restarting scoring or packet construction. Cancellation is checked before and after returning it. Periodic refresh reuses the retained packet. The corrected focused set passed 76 tests; the final search/performance/control pass below covers the final additional scan checks.

### Current verification

| Check | Result | Inspectable evidence |
|---|---|---|
| Full relevant backend matrix from the plan, including policy, migration, Standard/exam preservation, exact validation, lifecycle and six actual endpoint/worker/save cases | **571 passed**, zero failures/errors/skips | `verification/convergence-backend.xml` |
| Final preference/heuristic/strategy regression plus all real comparison/worker control tests | **109 passed**, zero failures/errors/skips | `verification/convergence-control.xml`, `verification/convergence-performance.json` |
| Full client suite on portable official Node **24.22.2**, npm **11.19.1** | **605 passed**, 70 files | `.tmp/i011-convergence-client-node24.log` |
| Node 24 ESLint, TypeScript and Vite production build | **Passed** | `npm --prefix client run lint`, `npm --prefix client run build` in the same Node 24 process environment |
| Whitespace | **Passed** | `git diff --check` |

The broad backend pass preceded the final extra interruption checks in demand/date scans; the subsequent 109-test run verifies those final changes together with actual spawned-worker dispatch, deadline, active cancellation and checkpoint cadence. Eight new parametrized regression cases account for the increase from 563 to 571 backend tests. Source/artifact hashes, suite totals and the six current connected acceptance measurements are recorded in `verification/convergence-summary.json`. Comparisons use identical isolated snapshots/budgets for all three real algorithms and make no universal quality/runtime claim.

The first broad run inside the sandbox encountered denied temporary-directory/process access and could not produce valid complete evidence. It was rerun successfully with approved escalation, fresh disposable workspace basetemp and the existing virtualenv. The Node download also needed approved escalation for network access. No automatic-approval rejection occurred. The portable runtime stays under ignored `.tmp`; the system Node installation was not changed. Existing FastAPI/httpx, SQLAlchemy datetime and HTTP status deprecation warnings remain warnings rather than failures.

### Outstanding manual acceptance and reconciliation

| Task | Current status and exact remaining condition |
|---|---|
| T057 / deployment portion of T053 | **Open.** `docker desktop start --detach` reported startup; a later direct launch of the installed Docker Desktop was also attempted. Docker Desktop still reports no running instance, and `docker info` cannot open `dockerDesktopLinuxEngine`. Actual container directory-mount visibility, host atomic replacement, container permissions and missing-file/health/frozen-operation checks could not run. Existing local/config tests and operator documentation do not substitute for these checks. |
| T058 / accessibility portion of T053 | **Open.** A newly seeded disposable app was launched on loopback port 8713 for browser verification. Computer Use stopped before browser interaction with: “could not determine the current browser URL on Windows with enough confidence to enforce policy.” UI automation was stopped; no alternate UI route was used. Real screen-reader speech and true 200% browser zoom therefore remain unverified. Prior keyboard/narrow-layout evidence and current automated UI checks remain applicable but do not prove these conditions. |
| T059 / T054 | **Partially complete; open.** The planned Node 24 verification is now green, resolving the earlier Node 27 alpha limitation. Final acceptance cannot close until T057/T058 observations exist. All six actual 1/20-course endpoint dispatch/review/atomic-save cases were rerun successfully in the backend matrix. |

Requirement reconciliation: FR-011/014 and preference definition 7 now have direct owner/outstanding-scarcity regressions; FR-019/SC-008 have internal interruption, completed-packet retention and real worker-control evidence. FR-001–007, FR-009–026, TR-002–007/009/010 and SC-001–008/010 retain the relevant green automated matrices, Standard baselines, named score/share fixtures and selected/protected-state comparisons. FR-004 remains qualified by the container checks; FR-008/TR-008 and the manual UI portion of SC-009 remain qualified by speech/zoom checks. TR-001 has the intended red/green evidence above and the plan's existing manual exception. A complete automated result is not unconditional manual acceptance.

Only the identified loopback validation server processes were stopped after the blocked browser attempt. The disposable database/policy and verification files remain under `.tmp` for reproducibility. The live policy hash was rechecked and remains `4C20E12A7610DB25E76E9479AD0AC9EE5F4F041A84AF3E9B6017C3C41032EB67`. No `.specify/extensions.yml` exists at the post-implementation hook check, so no hooks required dispatch.


## Human accessibility acceptance — 2026-11-10

The user confirmed screen-reader acceptance with "screnn reader passt" and, after the assistant explicitly identified true 200% browser zoom as the remaining separate check, confirmed "auch das ist in ordnung". Screen-reader and 200%-zoom acceptance are therefore recorded as passed by human confirmation. This supersedes the earlier unavailable accessibility status; it is not an agent-observed browser or speech test. Browser, assistive-technology version and detailed observations were not supplied.

T058 and its carried-forward duplicate T061 are complete on this basis. The accessibility portion of T053 is accepted; T053 remains open for its deployment checks. Container deployment T057/T060 and final acceptance reconciliation T054/T059/T062 remain outstanding. No application code or requirement was changed.
