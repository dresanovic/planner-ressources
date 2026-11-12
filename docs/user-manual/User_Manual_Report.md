# User Manual Update Report

## Current update — 11.11.2026

Updated [User_Manual.md](User_Manual.md) against all 35 entries in the reconciled
[scope map](../planning/Feature_slices.md), current source, behavioral tests and
feature verification records. Accurate baseline instructions are retained.
Application code, specifications, task markers, live policy and databases were not changed.
The preceding scope-map correction belongs to the earlier user request.

### Changes delivered

- Shortened Quick Start by moving Docker/source installation and first-administrator setup to the Detailed Guide. Preserved setup procedures and links.
- Corrected teaching generation to preparation, displayed algorithm/allowance, explicit Start, whole-selection comparison and exact acceptance actions. Removed the outdated per-course non-worsening claim.
- Explained all four installed teaching strategies, captured settings, operator-only selection, ordered lecturer portions, coverage versus preference proof, conditional proof and uncertainty.
- Retained and clarified Standard Optimized starting-arrangement behavior and continuation from the current proposal; documented cancellation, lost context and unconfirmed outcomes.
- Added recurring/dated windows, independent copying, duplicate rules and intensive priorities. Clarified preferred half-step session size versus whole actual LE.
- Added the verified lecturer `.ics` download workflow with static-file/privacy/reimport guidance. Representative Outlook import instructions are withheld pending institutional validation.
- Added operator policy-file configuration and symptom-based recovery. Removed the obsolete claim that algorithm selection is entirely unavailable.

### Slice coverage and evidence inventory

This table is a documentation assessment, not a rewrite of product slice statuses.
`partially-implemented` conservatively means only the independently verified workflow
is documented while recorded essential acceptance, verification or rollout conditions
remain open. It does not assert a newly discovered functional defect. For unchanged
baseline areas, prior verified manual/report evidence is retained; no new product-wide
release audit is claimed. `implemented` does not imply that the current live installation
has deployed or activated that increment.

| Slice | Status | Intended user | Entry point | Main use case | Evidence | Limitations | Manual action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FS-001 | implemented | Planner | Kalender > Plan erzeugen | Generate one course | Prior verified baseline; current generation UI/tests | Unified workflow supersedes legacy single-course entry | include-quick-start-and-detailed |
| FS-002 | implemented | Planner | Kalender | Review sessions | Prior baseline and current workspace | No new full visual audit | include-quick-start-and-detailed |
| FS-003 | implemented | Planner | Kursdetails | Set date boundaries | Current constraints UI; retained tests/evidence | Window editing belongs to Stammdaten | include-detailed-only |
| FS-004 | partially-implemented | Planner | Session pane | Edit session | Prior verified baseline; slice tasks | Manual smoke evidence open | include-with-limitation |
| FS-005 | partially-implemented | Planner | Current warnings | Inspect conflicts | Prior verified baseline; slice tasks | Manual acceptance open; no automatic repair | include-with-limitation |
| FS-006 | partially-implemented | Planner | Plan erzeugen | Plan a selection | Current unified UI; retained verification | Historical usability/performance evidence open | include-with-limitation |
| FS-007 | partially-implemented | Planner | Stammdaten | Maintain planning data | AcademicDataPage; fresh tests; slice tasks | Representative usability evidence open | include-with-limitation |
| FS-008 | partially-implemented | Planner | Lehrende/Räume/course eligibility | Maintain resources | Prior verified resource evidence; slice tasks | Manual/usability reconciliation open | include-with-limitation |
| FS-009 | partially-implemented | Planner | Kalender session actions | Add/delete teaching | Prior verified baseline; slice tasks | Verification/usability follow-ups open | include-with-limitation |
| FS-010 | partially-implemented | Planner | Plan erzeugen | Joint optimization | Current operations UI/tests; prior solver evidence | Historical acceptance/final audit open; later increments govern decisions | include-with-limitation |
| FS-011 | partially-implemented | Planner | Feiertage | Avoid holidays | Prior verified baseline; dated-window tests | Manual/usability evidence open | include-with-limitation |
| FS-012 | implemented | Planner | Prüfungen | Schedule exams | Prior verified baseline; complete slice tasks | No new full exam audit | include-quick-start-and-detailed |
| FS-013 | partially-implemented | Planner | Versionen | Publish revisions | Prior verified lifecycle evidence | Manual/usability evidence open | include-with-limitation |
| FS-014 | partially-implemented | Planner | Kalender | Operate calendar | Prior verified workspace evidence and parity record | Manual parity, legacy retirement and follow-up verification open | include-with-limitation |
| FS-015 | partially-implemented | Planner/Lecturer | Coordination/private link | Scoped review and feedback | Prior verified baseline; fresh LecturerReviewPage tests | Manual/deployment acceptance open | include-with-limitation |
| FS-016 | partially-implemented | Planner/Administrator/Operator | Anmelden; Planer-Konten | Protect planner access | Prior auth verification; current scope/tasks | Production memory, security/deployment and manual acceptance open | include-with-limitation |
| FS-017 | not-implemented | Planner/provider | None | External synchronization | Proposed scope; no implemented entry | Excluded | exclude |
| FS-018 | partially-implemented | Planner | Navigation | Reach destinations | Prior verified baseline; current route integration | Manual/usability/final audit open | include-with-limitation |
| FS-019 | partially-implemented | Planner | Kalender/session pane | Focus planning work | Prior verified baseline; fresh page tests | Manual/usability/final review open | include-with-limitation |
| FS-020 | partially-implemented | Lecturer | Kalender herunterladen | Download complete scoped `.ics` | Current dialog/page; fresh UI/serializer tests; independent validation record | Outlook, manual AT/usability and designated performance acceptance pending | include-with-limitation |
| FS-021 | not-implemented | Planner/Lecturer | None | Submit pre-planning unavailability | Ready-for-specification scope only | Excluded; planner-entered availability remains available | exclude |
| FS-022 | not-implemented | Lecturer | None | Ongoing authenticated lecturer access | Deferred scope | Excluded; private review links remain separate | exclude |
| I-001 | implemented | Operator | Container startup | Run one application image | Prior verified container baseline and current Compose | No fresh deployment run | include-detailed-only |
| I-002 | partially-implemented | All users/operator | Current UI/terminology file | German labels/dates/messages | Prior verified surface evidence; current editor/dialog labels | Source inventory/deployment/browser/participant gaps remain | include-with-limitation |
| I-003 | partially-implemented | Planner | Plan erzeugen | Unified teaching generation | Current page and fresh page tests | Manual List/workflow/usability follow-ups open | include-with-limitation |
| I-004 | partially-implemented | Planner | Stundenpläne vergleichen | Accept/cancel complete selection | Current dialog/operations; fresh dialog/page tests | Broader manual acceptance open | include-with-limitation |
| I-005 | implemented | Planner | Course-list filters | Discover cohort courses | Prior reviewed source/user PASS; fresh administration/page tests | Human PASS lacks detailed browser/AT provenance | include-quick-start-and-detailed |
| I-006 | partially-implemented | Planner/Operator | Budget preview/progress/comparison | Bounded search and valid unproved acceptance | Current config/operations/hook; fresh relevant tests | Responsive/manual acceptance open; continuation superseded by I-013 | include-with-limitation |
| I-007 | not-implemented | Planner | None | Capacity diagnostics/proposals | Confirmed future scope only | Excluded | exclude |
| I-008 | not-implemented | Planner | None | Approve shorter breaks | Future scope dependent on I-007 | Excluded | exclude |
| I-009 | partially-implemented | Planner | Zeitfenster; result facts | Dated/intensive windows and copying | Current editor/page; fresh tests; feature validation | Full regression/reconciliation and actual AT/zoom/reviewer evidence open | include-with-limitation |
| I-010 | not-implemented | Planner | None for general allocation editor | Enter fixed lecturer LE portions | Proposed scope only | Excluded; I-011's derived Lecturer portions documented separately | exclude |
| I-011 | partially-implemented | Planner/Operator | Algorithm preview/policy file | Select and run teaching strategies | Current registry/config/UI; fresh tests; feature validation | Container deployment and final reconciliation open; human speech/zoom acceptance recorded | include-with-limitation |
| I-012 | implemented | Planner/Operator | Standard optimiert | Distribute across feasible weeks | Current strategy/labels; validation and scoped review | Activation/migration required; no universal gain claimed | include-detailed-only |
| I-013 | implemented | Planner | Weiter optimieren | Continue same proposal | Current service/hook/dialog; fresh continuation and UI tests; scoped review | No fresh live browser/deployment acceptance | include-detailed-only |

Coverage: **8 implemented and documented; 21 partially implemented and documented with
limitations; 6 excluded; 0 wholly unclear/request-verification slices.** Total: 35.
Outstanding verification within included slices remains explicit below.

### Verification performed for this update

- Fresh frontend verification on portable Node 24.22.2: **213 passed, 8 files**.
  `AcademicRecordEditor`, `AcademicDataPage`, `OptimizationProofFacts`,
  `ReplacementConfirmationDialog`, `useOptimizationOperation`,
  `LecturerCalendarDownloadDialog`, `LecturerReviewPage`, `CourseSchedulePage`.
- Fresh backend verification: **91 passed**, existing dependency deprecation warnings.
  `test_optimization_config.py`, `test_teaching_strategies.py`,
  `test_optimization_continuation.py`, `test_dated_intensive_windows.py`,
  `test_lecturer_calendar_export.py`. Tests used disposable databases and
  `--basetemp=../.tmp/manual-update-verified-pytest`.
- Initial sandbox runs were inconclusive: Vite could not spawn its helper (`EPERM`)
  and pytest temporary-directory access was denied. Both commands passed after
  approved execution outside the sandbox; no production planning data was used.
- Checked documentation whitespace, local links/anchors, all 35 slice IDs and
  current visible action labels. These documentation changes do not need a new
  application build. No browser, screen-reader, container or Outlook session was
  performed during this update; earlier evidence is attributed below.

### Evidence and conflicts resolved

- [I-011 validation](../../specs/I-011-policy-teaching-strategies/validation.md)
  records automated strategy/worker/acceptance matrices and supported Node 24
  verification. Human confirmations on 10.11.2026 accept screen-reader and true
  200% zoom; those are human-reported, without tool versions. Container acceptance
  and final reconciliation remain open. The manual does not present policy mounting
  as a completed deployment acceptance check.
- [I-012 validation](../../specs/I-012-standard-optimized/validation.md) and
  [activation](../../specs/I-012-standard-optimized/quickstart.md) support the
  separate strategy, explicit review, conditional proofs and migration caveat.
- [I-013 verification](../../specs/I-013-continue-optimization/verification.md)
  supersedes old fresh-retry/discard instructions. Fresh continuation tests support
  same-operation seeding, quality/proven-prefix retention, stale rejection,
  duplicate-request protection and failure/timeout fallback.
- [I-009 validation](../../specs/I-009-dated-intensive-windows/validation.md)
  and current editor/page tests support copying and intensive behavior. Pending
  feature-wide browser/AT/human gates are not inferred from component tests.
- [FS-020 release checklist](../../specs/020-lecturer-calendar-export/validation/release-checklist.md)
  resolves the older report's unclear export entry point: download and independent
  RFC validation exist, but representative Outlook import, designated performance
  and manual accessibility/usability gates are pending. The manual documents file
  download only and defers application-specific import instructions.
- `optimization_operations.py` and `useOptimizationOperation.ts` establish that
  only eligible fully proved initial Standard runs without selected saved teaching
  can auto-save. Explicit comparison governs the other documented cases. The old
  blanket claim of never replacing a course with fewer units was removed.
- The old report's presentation-work identifier FS-022 refers historically to what
  is now I-002. Current FS-022 is deferred authenticated lecturer access.

### Exclusions, assumptions and limitations

Excluded slices: **FS-017, FS-021, FS-022, I-007, I-008, I-010**. No normal workflow
is invented for synchronization, lecturer unavailability submissions, lecturer
accounts, capacity proposals, five-minute breaks or a general fixed-allocation editor.
Current derived Lecturer portions are distinct from the proposed general editor.

The manual describes the current checkout, not proof of deployment on a particular
institution's server. Access address, image release, private delivery channels and
Outlook version remain organization-specific. Shipped German labels are used;
customer terminology may differ. No secrets or live policy values are embedded.

Existing baseline manual acceptance gaps remain as listed in slice tasks, including
FS-004–FS-011, FS-013–FS-016, FS-018/019, I-002–I-004, I-006, I-009 and I-011.
FS-014 includes a still-open legacy-retirement/parity boundary. The manual teaches
verified current workspace actions without claiming that boundary is closed.

### Recommended verification

1. Have a first-time planner follow the shortened Quick Start through preparation,
   Start and result acceptance; check the actual installed algorithm and allowance.
2. Complete I-011 container policy directory/replacement/permission acceptance and
   final reconciliation on a disposable deployment before rollout.
3. Complete FS-020 institutional Outlook import, timezone/device observations,
   designated performance and manual accessibility/usability protocols. Until then,
   retain the manual's import limitation.
4. Complete the remaining recorded auth, calendar parity, generation and intensive
   accessibility/usability/regression gates using actual environments/reviewers.
5. If visual guidance is needed, capture the current authenticated window editor,
   algorithm/budget preview, comparison/proof panel and download notice. No new
   screenshot was created or implied by this update.

Quality checklist: scope reviewed; every slice classified; only verified parts
included; Quick Start numbered and outcome-based; role-specific installation and
policy details separated; planned scope excluded; limitations and recovery
explicit; source/test conflicts resolved or reported; labels checked; links and
formatting checked. No application code or requirement change was required.

## Historical update records

Everything below is dated historical evidence. Its counts, exclusions, branch names,
identifier mappings and suggested actions are superseded by the current inventory
above. Historical test results are not claimed as fresh runs.


## I-005 update — 2026-11-04

Scope: focused update for filterable generation and administration course lists on `codex/i-005-filter-course-plan-list`. The user invoked user-manual-creation after Goal 4 completed. This authorizes the documentation work; no new runtime Goal was created and no Git operation is authorized. Application code, specifications, slice statuses, and task markers were not changed.

### Evidence and slice inclusion

Inspected the current scope map, existing manual/report, I-005 reviewed implementation and acceptance record, specification/design contract, native control labels, generation navigation, exact-record administration handlers, and behavioral tests. Goal 4's [review](../../specs/I-005%20-%20filter-course-plan-list/code-review.md) establishes no blocking findings with 475 frontend tests, 106 backend regressions, TypeScript/Vite build, ESLint and diff checks passing on 2026-11-03. The [feature evidence](../../specs/I-005%20-%20filter-course-plan-list/quickstart.md) retains the user's overall acceptance PASS and its limits.

The following inventory uses current slice identifiers. For older slices, classifications retain prior verified baseline evidence rather than claiming a new product-wide acceptance audit. Only I-005 and the directly connected teaching-generation instructions were updated. `request-verification` denotes a gap in current evidence/documentation, not a newly discovered product defect.

| Slice | Status | Intended user | Entry point | Main use case | Evidence | Limitations | Manual action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FS-001 | implemented | Planner | Kalender | Generate one course | Prior manual evidence; unchanged generation integration | No new slice-wide audit | include-quick-start-and-detailed |
| FS-002 | implemented | Planner | Kalender | Review sessions | Prior manual evidence | No new slice-wide audit | include-quick-start-and-detailed |
| FS-003 | implemented | Planner | Kursdetails | Set constraints | Prior evidence; current generation inputs | No new slice-wide audit | include-detailed-only |
| FS-004 | implemented | Planner | Calendar session | Edit a session | Prior manual evidence | Historical manual acceptance gaps retained | include-with-limitation |
| FS-005 | implemented | Planner | Calendar warnings | Inspect conflicts | Prior manual evidence | No automatic repair | include-detailed-only |
| FS-006 | implemented | Planner | Plan erzeugen | Select several courses | Prior evidence; I-005 integration tests | Superseded visible workflow documented under unified generation | include-quick-start-and-detailed |
| FS-007 | implemented | Planner | Stammdaten | Maintain records | Prior evidence; fresh AcademicDataPage tests | No new full catalog acceptance audit | include-quick-start-and-detailed |
| FS-008 | implemented | Planner | Stammdaten | Maintain resources | Prior manual evidence | Historical responsive/usability gaps retained | include-with-limitation |
| FS-009 | implemented | Planner | Kalender | Manage sessions | Prior manual evidence | Historical acceptance gaps retained | include-with-limitation |
| FS-010 | implemented | Planner | Plan erzeugen | Optimize selections | Prior evidence; fresh API/page tests | No new optimizer audit | include-quick-start-and-detailed |
| FS-011 | implemented | Planner | Feiertage | Maintain holidays | Prior manual evidence | Full-date institution calendar | include-detailed-only |
| FS-012 | implemented | Planner | Prüfungen | Plan exams | Prior manual evidence | No new exam acceptance audit | include-quick-start-and-detailed |
| FS-013 | implemented | Planner | Versionen | Publish revisions | Prior manual evidence | Historical acceptance gaps retained | include-with-limitation |
| FS-014 | implemented | Planner | Kalender | Review semester | Prior manual evidence | Historical AT/browser gaps retained | include-with-limitation |
| FS-015 | implemented | Planner/Lecturer | Abstimmung mit Lehrenden | Review and give feedback | Prior evidence and current scope map | Manual/deployment acceptance pending | include-with-limitation |
| FS-016 | implemented | Planner/Administrator | Anmelden; Planer-Konten | Manage planner access | Prior implementation/test evidence | Current scope-map status conflicts with older verified implementation; not re-audited | include-with-limitation |
| FS-017 | not-implemented | Planner | None verified | External synchronization | Proposed in scope map | Excluded from usage | exclude |
| FS-018 | implemented | Planner | Navigation | Reach destinations | Prior evidence; fresh App tests | No new full navigation acceptance audit | include-quick-start-and-detailed |
| FS-019 | implemented | Planner | Kalender | Focus planning work | Prior evidence; fresh page tests | Manual acceptance pending in scope map | include-with-limitation |
| FS-020 | unclear | Lecturer | Prior report has no verified entry point | Export iCalendar | Current scope map says implemented; old report says not implemented | Release acceptance pending; export not inspected in this I-005 update | request-verification |
| FS-021 | not-implemented | Planner/Lecturer | None verified | Submit unavailability | Ready for specification in scope map | Excluded from usage | exclude |
| FS-022 | not-implemented | Lecturer | None verified | Authenticated lecturer access | Deferred in current scope map | Older report used this ID for presentation work now named I-002 | exclude |
| I-001 | implemented | Operator | Container startup | Run application | Prior manual evidence | No new deployment audit | include-detailed-only |
| I-002 | partially-implemented | Planner/Lecturer/Operator | Current UI | Consistent labels, dates, messages | Prior report under former FS-022 label; current scope map | Inventory, browser and participant follow-ups remain | include-with-limitation |
| I-003 | implemented | Planner | Plan erzeugen | Unified generation | Current controls and passing I-005/API tests; Goal 4 | Only directly connected instructions refreshed | include-quick-start-and-detailed |
| I-004 | implemented | Planner | Generation comparison | Accept/cancel full replacement | Passing hidden-selection accept/cancel/stale tests; Goal 4 | Broader manual acceptance pending in scope map | include-with-limitation |
| I-005 | implemented | Planner | Plan erzeugen; Stammdaten > Lehrveranstaltungen | Discover cohort courses and retain explicit selection | Reviewed source, 119 fresh focused tests, prior 475/106 checks, user PASS | No new manual AT/authenticated-layout run; browser/version observations unspecified | include-quick-start-and-detailed |
| I-006 | not-implemented | Planner | None | Configure longer optimization / incumbent acceptance | Requirements-only scope entry | Do not document as available | exclude |

### Changes made

- Updated the generation Quick Start to the actual **Kursdetails**, **Plan erzeugen**, and **Stundenpläne erzeugen** labels; added cohort filtering and complete-selection review.
- Added a short administration course-discovery procedure with expected results.
- Added full-selection/hidden-course instructions, the 20-total limit, exact reset versus clear-selection effects, and unavailable/missing identity recovery.
- Documented independent session-only filter memory, semester/reload reset behavior, editor preservation and current-status intersection.
- Added symptom-based course-list troubleshooting and the single-cohort/no-search/no-bulk limitation.
- Updated the directly connected generation comparison instructions to current behavior without changing the approved product scope.

### Verification and quality assessment

Fresh command on 2026-11-04: `npm --prefix client test -- src/components/MultiCourseGenerationPanel.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/AcademicDataPage.test.tsx src/App.test.tsx src/api/conflictAwareGeneration.test.ts` — **PASS, 5 files / 119 tests**. Approved execution outside the sandbox was used because Vite process spawning required it. The existing Node/npm compatibility warning remains nonblocking. No dependency changes.

The numbered Quick Start was checked against current navigation/labels and passing tests for discovery, exact eleven-ID preparation, full hidden selections, editor retention and status/scope changes. Detailed recovery instructions were checked against actual rendered message branches and freshness guards. Markdown links, documentation whitespace, scope of changes, and consistency of reset/clear wording were checked. No new manual browser or screen-reader pass is claimed. The prior full checks are supporting historical evidence; the fresh focused run is the current verification for this documentation update.

Quality checklist: scope map reviewed; all current slice identifiers inventoried; I-005 included only on reviewed/passing evidence; no planned search/bulk selection documented; Quick Start retains prerequisites/access, numbered workflows and expected results; advanced lifetime/validation/recovery rules live in the Detailed Guide; existing role separation retained; UI terms checked; no secrets or implementation identifiers added to normal instructions. No screenshot is required for the native labelled filters. If visual guidance is later needed, capture current authenticated generation and administration surfaces rather than reusing the isolated fixture as production evidence.

### Coverage and outstanding gaps

- Newly documented slice: **I-005 (1 implemented)**. Directly connected existing I-003/I-004 instructions refreshed.
- Inventory: **22 implemented**, **1 partially implemented** (I-002), **4 excluded** (FS-017, FS-021, FS-022, I-006), **1 requiring verification** (FS-020). These are inventory counts, not 22 newly verified slices.
- The old report's FS-022 presentation label now maps to I-002. Current FS-022 means deferred authenticated lecturer access. The historical sections below are retained as dated evidence and must not be read as a current identifier/status inventory.
- Current FS-016 scope status says ready for specification while the older report records working authentication and extensive passing tests. Existing access instructions are retained under the skill's evidence priority; a full current reconciliation was outside I-005.
- Current FS-020 says implemented with release acceptance pending; the historical exclusion is superseded as a current status claim. Export remains undocumented in this focused update until its UI, tests and acceptance evidence are inspected. Do not infer that export is unavailable from the historical section below.
- Earlier unrelated release/accessibility/deployment gaps remain open; this update does not close them. I-005 acceptance remains the user's overall PASS with browser/screen-reader details unspecified.

Recommended next action: read the two updated Quick Start procedures as a first-time planner; for a later broader manual refresh, verify FS-020 and reconcile FS-016/I-002 scope evidence. No blocking I-005 documentation gap was identified.

### Delivery handover

Documentation outputs: this report and `User_Manual.md`. Application code, tests and specifications remain untouched by this skill invocation. Existing unrelated backend/process changes are preserved.

Suggested future commit scope: I-005 frontend changes/tests/fixture, I-005 feature artifacts and review report, feature pointer, I-005-only planning changes, and these two manual files. Suggested message: `feat: add cohort filters to course lists and document selection safety`. Exclude unrelated backup/restore/process edits and the I-006 planning hunks; review a selective staged diff before any commit. Proposed base: local `master`, subject to the human's delivery choice; no fetch or remote freshness claim was made.

No commit, push, merge, or further Goal was started. This is the authorized manual skill's completed output, not a claim that a separately started runtime Goal 5 was completed.

## Historical report — 2026-08-25

The remainder is the earlier manual update record. Counts, slice names, excluded functionality and test results below refer to that historical assessment; use the current inventory and conflicts above for this I-005 handover.

## Summary

The user manual was updated on 25.08.2026 to reflect the current verified Resource Planner, including implemented FS-016 named planner authentication and account administration, the implemented container distribution, the implemented portions of FS-022, and the accountless lecturer-review workflow.

Outputs:

- Manual: `docs/user-manual/User_Manual.md`
- Report: `docs/user-manual/User_Manual_Report.md`

The manual now explains named planner sign-in, first-administrator bootstrap, planner onboarding, password and session behavior, account lifecycle administration, atomic administrator transfer, emergency recovery, and the preserved accountless lecturer boundary. It also retains shipped German UI terminology, European date guidance, actionable problem recovery, customer terminology configuration, and separate planner, lecturer, administrator, and operator procedures.

## Evidence reviewed

- `docs/planning/Feature_slices.md`
- existing user manual and report
- FS-016 specification, clarifications, plan, tasks, contracts, quickstart, and implementation-verification evidence under `specs/016-authenticated-planner-access/`
- current planner authentication services, API routes, authorization middleware, account/session models, startup reconciliation, client authentication gate, auth pages, account-administration page, and navigation
- current migration, authentication service/concurrency/API/authorization, lecturer-boundary, planner request, route, auth-page, account-page, and navigation tests
- FS-022 specification, plan, tasks, contracts, quickstart, and validation artifacts under `specs/I-002/`
- current terminology catalog, deployment configuration, loader, client bootstrap, and terminology tests
- current date-presentation utilities, `EuropeanDateField`, API boundary tests, and consuming surface tests
- current problem model, actionable-problem rendering, warning/failure mappers, and owning surface tests
- current planner navigation, Calendar, academic/resource, exam, lifecycle, and lecturer-review implementation
- current FS-015 planner-management and accountless lecturer tests
- backend/client README and Docker deployment guidance
- implemented I-001 container-distribution specification, tasks, quickstart, Dockerfile, Compose configuration, release workflow, and CI smoke-test contract
- current official Docker Desktop installation and Images-view instructions

Evidence priority followed the skill: verified behavior, passing tests, implementation, accepted clarifications, specifications, scope map, plans/tasks, and older documentation.

## Verification performed

| Check | Result |
| --- | --- |
| `python -m pytest backend/tests -q` | Passed: 557 tests, 1 skipped, 1651 warnings |
| Focused final lecturer/planner authorization matrix | Passed, including active/ended/replaced lecturer credentials without and with a valid planner cookie and mutation snapshots |
| `npm run test` in `client` | Passed: 66 files, 452 tests |
| `npm run lint` in `client` | Passed |
| `npm run build` in `client` | Passed |
| `docker compose config --quiet` with a valid 64-character fingerprint key | Passed |

## Slice evidence table

| Slice | Status | Intended user | Entry point | Verified main use case | Limitations or gaps | Manual action |
| --- | --- | --- | --- | --- | --- | --- |
| FS-001 Single-Course Draft Generation | Implemented | Planner | Planung > Kalender > Planungseingaben | Generate or preserve one teaching draft with reasons | None blocking documented workflow | Include Quick Start and Detailed Guide |
| FS-002 Schedule Review | Implemented | Planner | Kalender modes and Liste | Review and filter planned sessions | Dense review remains list-oriented | Include Quick Start and Detailed Guide |
| FS-003 Generation Constraints | Implemented | Planner | One-course planning inputs | Use defaults, custom dates/windows, and reset | Changes apply only on generation | Include Detailed Guide |
| FS-004 Manual Session Editing | Implemented | Planner | Calendar occurrence > editor | Correct a saved session without losing context | Manual acceptance evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-005 Conflict Detection | Implemented | Planner | Calendar warnings/summaries/details | Inspect non-blocking current validation issues | No automatic repair | Include Detailed Guide |
| FS-006 Multi-Course Generation | Implemented; visible outcome superseded by FS-010 | Planner | Several-course planning inputs | Plan several selected courses | Legacy independent UI is not documented | Include under optimization |
| FS-007 Academic Data Administration | Implemented | Planner | Stammdaten | Maintain planning records safely | Representative-user evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-008 Resource Eligibility/Availability | Implemented | Planner | Stammdaten > Lehrende/Räume/Lehrveranstaltungen | Maintain resources, availability, and eligibility | Recorded responsive/usability evidence remains incomplete | Include Detailed Guide |
| FS-009 Manual Session Management | Implemented | Planner | Planning inputs and Calendar | Add, delete, or clear teaching sessions | Representative-user evidence remains incomplete | Include Detailed Guide |
| FS-010 Semester Optimization | Implemented | Planner | Mehrere Lehrveranstaltungen | Optimize 1–20 courses and preserve worse/stale results | No persisted operation history | Include Quick Start and Detailed Guide |
| FS-011 Holiday Calendar | Implemented | Planner | Stammdaten > Feiertage | Maintain full-date holidays used by planning | One institution-wide full-date calendar | Include Detailed Guide |
| FS-012 Exam Scheduling | Implemented | Planner | Planung > Prüfungen | Configure, generate, place, correct, and delete exams | No registration, grading, or external booking | Include Quick Start and Detailed Guide |
| FS-013 Versioned Publication | Implemented | Planner | Planung > Versionen | Manage working and published revisions | Representative-user evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-014 Calendar Workspace | Implemented | Planner | Planung > Kalender | Use revision-scoped modes, filters, summaries, and detail | Manual browser/AT evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-015 Accountless Lecturer Review | Implemented behavior; scope-status gap | Planner/Lecturer | Abstimmung mit Lehrenden; private review URL | Issue scoped links, review assignments, submit and inspect feedback | `Feature_slices.md` still describes extension work as pending; manual acceptance gaps remain | Include Quick Start and Detailed Guide with limitation |
| FS-016 Authenticated Planner Access and Account Administration | Implemented; release acceptance evidence pending | Planner/System administrator/operator/accountless lecturer | Anmelden; Planer-Konten; startup setup/recovery routes | Protect planner work, bootstrap the sole administrator, onboard/manage planners, maintain one current session, transfer/recover administration, preserve lecturer links | Argon2 production-architecture benchmark, complete manual accessibility/participant acceptance, and production deployment evidence remain open | Include Quick Start and Detailed Guide with release limitation |
| FS-017 External Import/Synchronization | Not implemented | Planner/provider | None | None | No external provider integration | Exclude |
| FS-018 Unified Navigation | Implemented | Planner | Shared navigation | Reach all planner destinations responsively | Recorded AT/zoom evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-019 Streamlined Schedule Workspace | Implemented | Planner | Planung > Kalender/Versionen/Prüfungen | Use focused destinations, in-pane correction, pinning, and collapsible inputs | Manual acceptance evidence remains pending | Include Quick Start and Detailed Guide |
| FS-020 Lecturer iCalendar Export | Not implemented | Lecturer | None | None | Specification not implemented | Exclude |
| FS-021 Lecturer Unavailability Submission | Not implemented | Planner/Lecturer | None | None | Specification not implemented | Exclude |
| FS-022 Consistent Labels, Dates, Messages | Partially implemented | Planner/Lecturer/operator | All current UI; deployment terminology file | Use German/customer labels, `DD.MM.YYYY`, and contextual problem items | Final inventory audit, deployment matrix, browser/NVDA, and 10-user study remain open | Include verified behavior with limitation |
| I-001 Containerized Application Distribution | Implemented | Deployment operator | Docker Desktop, `compose.yaml`, or container runtime | Run one complete application image, persist data, seed an optional catalog, and create a verified backup | Single application container with SQLite; registry access and production URL are installation-specific | Include Quick Start and Detailed Guide |

## Slice coverage

- Implemented and documented: 19
- Partially implemented and documented with limitations: 1
- Excluded as not implemented: 3
- Requiring verification before any additional user-facing claim: 0

## Major documentation changes

- Added the first-administrator startup runbook for source and Docker launches, including one-time credential generation, redemption, removal, replay behavior, and normal sign-in.
- Added named planner onboarding through a manually delivered one-time setup link and documented the shared 24-hour, single-use, replacement behavior for setup, reset, and reactivation.
- Added the administrator-only **Planer-Konten** workflow for account creation, reset, disablement, reactivation, lifecycle timestamps, and atomic administration transfer.
- Added self-service password change, one-current-session behavior, login throttling, inactivity/absolute expiry, invalidation events, logout, and browser session-restoration limitations.
- Added operator-assisted emergency administrator recovery without email, SSO, VPN identity, an operator account, or a Forgot-password workflow.
- Added verified IntelliJ/Vite local-origin guidance and troubleshooting for `localhost` versus `127.0.0.1` strict-cookie failures.
- Corrected Docker instructions so production planner credentials and secure cookies use HTTPS, while isolated local development behavior is clearly limited.
- Replaced English navigation/action references with current shipped German UI labels.
- Added the **Abstimmung mit Lehrenden** destination and planner link-management workflow.
- Added a separate accountless lecturer Quick Start and detailed privacy/restricted-action guidance.
- Added `DD.MM.YYYY` display and `TT.MM.JJJJ` entry rules, including invalid-date correction and preserved input.
- Corrected the multi-course unavailable-date instruction from ISO input to comma-separated European dates.
- Added exact explanations for all eight Calendar filters and their combined behavior.
- Added actionable-message structure, multiple-problem behavior, stale/unknown-outcome recovery, and the outside-recommended-period decision path.
- Added deployment-operator instructions for `config/terminology-overrides.json` and safe startup validation.
- Added a complete Docker Desktop installation path covering Docker Desktop setup, exact-image pulling, persistent data, required key generation, GUI container settings, health verification, logs, optional seeding, backup, upgrade, and troubleshooting.
- Updated navigation guidance for the red close icon and pin icon.
- Removed the obsolete claim that accountless lecturer review links are unavailable.

## Conflicts and resolutions

### FS-022 scope status is stale

`Feature_slices.md` still labels FS-022 as ready for implementation, while current implementation and the passing frontend/backend suites prove substantial delivered behavior. The task and validation artifacts still leave the final source audit, deployment/container matrix, manual browser/accessibility checks, and representative-user study open. The report therefore classifies FS-022 as partially implemented and documents only verified behavior.

### FS-015 status understates current behavior

The scope map says the secure-link baseline is retained while the shared workspace and coordination extension are pending. Current code and extensive tests implement the restricted calendar/list workspace, session/revision feedback, coordination filters/counters, session navigation, and link lifecycle. Verified behavior is documented, while the stale scope status is reported rather than silently changed.

### Configurable labels versus fixed German prose

Only selected reusable terminology is customer-configurable. Ordinary instructions, warnings, actions, and stored record names remain fixed German or user data. The manual uses shipped defaults and warns that customer installations may display alternative terms.

### Published content versus current warnings

Published schedule content remains immutable while current validation may reflect changed catalog or resource data. The manual keeps these concepts separate.

### FS-016 is usable while release acceptance remains open

`Feature_slices.md` classifies FS-016 as implemented with release acceptance evidence pending. Current code and automated suites verify the complete user-facing account workflows and authorization boundary. T082, T085, and T086 still require production-architecture password-verification benchmarking, complete manual accessibility/participant acceptance, and production HTTPS/deployment verification. The manual documents usable behavior but does not claim those release gates are complete.

## Excluded functionality

- authenticated lecturer accounts, general role management, multiple administrators, and institutional SSO
- MFA, passkeys, email provisioning, and self-service forgotten-password recovery
- multiple concurrent sessions and session/device-management UI
- lecturer iCalendar export
- lecturer pre-planning unavailability submission and approval
- external planning-data import or synchronization
- automated review-link email delivery
- runtime language switching, multiple active languages, and in-application terminology administration
- notification centers, support workflows, and exposure of internal diagnostics
- automatic correction of warned appointments

## Documentation and verification gaps

- FS-016 T082 lacks the required four-simultaneous-verification Argon2 memory and duration evidence for each supported production architecture.
- FS-016 T085 lacks the complete keyboard, screen-reader, responsive/zoom, browser-close, timed-journey, and ten-participant acceptance record.
- FS-016 T086 lacks the complete production secure-cookie, remote HTTP/HTTPS, CORS, no-store, startup-log, credential replay, and SQLite restore record.
- FS-022 T050/T057–T061 remain open or partial: the complete source/surface inventory and representative override matrix are not fully reconciled.
- FS-022 T052 has no recorded built-container matrix for default, valid partial, and every invalid override class.
- FS-022 T053 has no complete Edge/Chrome/Firefox, 320px, 200% zoom, accessibility-tree, and NVDA/Firefox record.
- FS-022 T054 has no 10-participant outside-window comprehension study; SC-006 is therefore unverified.
- FS-015 and FS-019 scope/status text is behind current verified implementation.
- No new verified screenshots were embedded.
- No new Docker Desktop GUI acceptance pass was performed during this FS-016-focused documentation update; the instructions are grounded in the implemented I-001/FS-016 artifacts, completed automated evidence, and current deployment guidance.

## Assumptions and limitations of this manual

- The primary audience is a planner; accountless lecturer and deployment-operator procedures are separated.
- The sole system administrator is also a planner; account-management and infrastructure-operator procedures are separated from ordinary planner workflows.
- Docker Desktop and local PowerShell startup are both documented; the production URL, exact approved image tag, and registry access remain deployment-specific.
- The manual describes visible UI workflows, not API use.
- Automated tests support functional claims but do not establish formal accessibility conformance, production readiness, cross-browser acceptance, or representative-user comprehension.
- Customer-specific terminology may make labels differ from the shipped defaults named in the manual.

## Recommended verification steps

1. Complete FS-016 T082, T085, and T086 and record the architecture, accessibility/participant, and production deployment evidence.
2. Have a first-time planner and administrator complete bootstrap, account setup, login, reset, reactivation, transfer, and recovery using only the updated manual.
3. Repeat representative flows with a long Unicode customer terminology override and verify no stored data changes.
4. Execute the FS-022 browser, keyboard, 320px, 200%-zoom, and NVDA/Firefox matrix.
5. Run the outside-recommended-period comprehension exercise with ten representative users.
6. Have one planner issue a temporary review link and one lecturer complete both session and revision feedback without coaching.
7. Reconcile the FS-015 and FS-022 status text through the product scope workflow.
8. Investigate the Windows native-extension diagnostic in a clean Python environment if it recurs.
9. Have a first-time Windows operator install and run the application through Docker Desktop using only the updated manual, then record the Docker Desktop version, exact image tag, HTTPS/login result, persistence check, and backup result.
