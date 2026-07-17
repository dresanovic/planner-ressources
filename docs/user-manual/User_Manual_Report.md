# User Manual Generation Report

## Summary

The user manual was generated from the current product scope and verified implementation on 2026-07-17. It documents the verified planner-facing functionality in FS-001 through FS-005, FS-007 through FS-009, and FS-018. FS-006 is reported as temporarily unavailable because its formerly completed, passing UI entry point was displaced in the current working-tree snapshot. It does not present FS-010 through FS-017 as available.

Output:

- Manual: `docs/user-manual/User_Manual.md`
- Report: `docs/user-manual/User_Manual_Report.md`

## Evidence reviewed

- Scope: `docs/planning/Feature_slices.md`
- Specifications, clarifications, plans, research, data models, contracts, quickstarts, task lists, checklists, and validation artifacts under `specs/001-*` through `specs/010-*` and `specs/018-*`
- Backend implementation under `backend/app`, database migrations, seed script, API/service/schema behavior, and backend README
- Client implementation under `client/src`, API clients, pages, components, responsive navigation, and client README
- Backend and client automated tests, including API, service, repository, migration, component, navigation, performance, and regression coverage
- Existing design references and recorded browser-validation screenshots

Evidence priority followed the skill rule: current verified behavior, passing tests, implementation, accepted clarifications, specification, scope map, planning artifacts, and existing documentation.

## Verification performed

### Last fully passing baseline observed during this task

| Check | Result |
| --- | --- |
| `python -m pytest` in `backend` | 184 passed |
| `npm run test` in `client` | 21 files and 119 tests passed |
| `npm run lint` in `client` | Passed |
| `npm run build` in `client` | Passed |

### Current working-tree snapshot after concurrent FS-010 edits

| Check | Result |
| --- | --- |
| `python -m pytest` in `backend` | Collection blocked by missing `ortools` in the active Python environment after the in-progress optimizer was imported from `app.main`; current suite not established as passing |
| `npm run test` in `client` | 21 files passed, 1 failed; 121 tests passed, 1 failed in the in-progress optimization selection/unavailable-date component test |
| `npm run lint` in `client` | Passed |
| `npm run build` in `client` | Passed after the concurrent test/type updates |

The manual therefore does not instruct users to use the current **Several courses** / optimization controls. Other documented client workflows retain passing focused coverage in the current client run, and their last complete cross-stack baseline passed before the concurrent integration edits.

The current working tree contained unrelated in-progress FS-010 planning, dependency, backend, and client changes during manual generation. They were not modified for this task and were not treated as proof that FS-010 is available.

## Slice evidence table

| Slice | Status | Intended user | Entry point | Verified main use case | Evidence | Limitations or gaps | Manual action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FS-001 Single-Course Draft Schedule Generation | Implemented | Planner | Schedule > One course | Generate a complete Course draft or receive all failure reasons without a partial replacement | Generation API/service/repository; backend API and service tests; client workflow tests | No cross-Course conflict avoidance, holidays, or exams | Include Quick Start and Detailed Guide |
| FS-002 Review Generated Schedule | Implemented | Planner | Courses overview | Review chronological List and Weekly groupings and filter visible sessions | DraftSchedulePanel; API response context; component and API tests | Weekly view is not drag-and-drop calendar | Include Quick Start and Detailed Guide |
| FS-003 Configurable Generation Constraints | Implemented | Planner | One course > Inputs for the next draft | Use defaults, save successful custom Course-Semester constraints, clear to defaults, and review all Semester drafts | Constraint API/repository; overview API; client editor; automated tests | Constraint changes do not alter sessions until generation | Include Quick Start and Detailed Guide |
| FS-004 Manual Session Editing | Implemented | Planner | Session > Edit | Change date, time, Lecturer, or Room and retain saved edits | Draft Session PATCH implementation; editor component; backend/client tests | Manual smoke task remains unchecked, but automated behavior is passing; regeneration may replace edits | Include Quick Start and Detailed Guide |
| FS-005 Conflict Detection | Implemented | Planner | Session validation alerts | See overlap, capacity, window, and missing-data alerts after reads and saved changes | Validation service; response schemas; backend/client tests | Manual smoke task remains unchecked; alerts are non-blocking and no automatic resolution exists | Include Quick Start and Detailed Guide |
| FS-006 Multi-Course Draft Generation | Partially implemented in the current snapshot | Planner | Established backend endpoints remain, but the former Schedule > Several courses UI has been displaced by unverified FS-010 controls | Independent 2-50-Course generation was verified in the last green baseline, but its current intended UI entry point is no longer passing | Existing batch API/service and historical passing tests; current client test regression and blocked backend collection | Do not include as an available user workflow until the UI is restored or the replacement is completed and verified | Exclude from normal instructions; report limitation |
| FS-007 Academic Planning Data Administration | Implemented | Planner | Academic Data > Semesters, Cohorts, Courses, Study types, Time windows | Create, edit, archive/reactivate, and safely delete academic records | Academic API/service/migration; administration UI; API/service/component/performance tests | Required 10-participant usability study remains pending | Include Quick Start and Detailed Guide |
| FS-008 Resource Eligibility and Availability | Implemented | Planner | Academic Data > Lecturers, Rooms; Course eligibility editor | Maintain coded resources, unavailability, eligibility, capacity, lifecycle, and validation inputs | Resource API/service/rules/migration; UI editors; regression/performance tests and recorded validation | 10-participant study and some wide/narrow/manual acceptance timing remain pending | Include Quick Start and Detailed Guide |
| FS-009 Manual Session Management | Implemented | Planner | Add one Draft Session; session Delete; Clear course draft | Add, delete, or clear Course-Semester sessions with remaining-unit and stale-confirmation handling | Draft repository/API; deletion dialogs; manual-session UI; backend/client tests | Required 10-participant usability study remains pending | Include Quick Start and Detailed Guide |
| FS-010 Conflict-Aware Semester Optimization | Not implemented | Planner | No verified completed entry point | No completed, independently verified user workflow | Scope says Ready for specification; in-progress specifications and application files are present, but the slice is not established as delivered by the scope source or a completed verification set | Existing uncommitted implementation artifacts are not completion proof | Exclude |
| FS-011 Holiday Calendar and Avoidance | Not implemented | Planner | None | None | Scope only | Public holidays may still receive generated sessions | Exclude |
| FS-012 Conflict-Aware Exam Scheduling | Not implemented | Planner | None | None | Scope only | No exam controls or generation | Exclude |
| FS-013 Versioned Review and Publication | Not implemented | Planner | None | None | Scope only | No Draft/Ready/Published lifecycle | Exclude |
| FS-014 Calendar Workspace and Dashboard | Not implemented | Planner | None | None | Design reference and scope only | Current Weekly view is a grouped review surface | Exclude |
| FS-015 Accountless Lecturer Review | Not implemented | Planner/Lecturer | None | None | Scope only | No token links, feedback, or email delivery | Exclude |
| FS-016 Authenticated Access and Roles | Not implemented | Planner/Lecturer | None | None | Scope only | No authentication or role separation | Exclude |
| FS-017 External Import and Synchronization | Not implemented | Planner/provider | None | None | Scope only | No external provider integration | Exclude |
| FS-018 Unified Application Navigation | Implemented | Planner | Shared sidebar or narrow Menu | Reach Schedule and seven Academic Data categories from one hierarchy | ApplicationNavigation/App implementation; component tests; browser checks at 1280, 820, and 320 pixels; lint/build | Explicit 200% zoom, NVDA/Firefox, and 10-participant acceptance remain pending | Include Quick Start and Detailed Guide, without claiming pending acceptance outcomes |

## Slice coverage

- Implemented and documented: 9
- Partially implemented: 1
- Excluded as not implemented: 8
- Requiring functional verification before normal user documentation: 1 (the current multi-course replacement)

The pending acceptance activities above concern usability, assistive-technology, zoom, or recorded manual protocols. FS-006 is separately classified as partial because its formerly verified client entry point has been replaced by an incomplete, failing integration in the current worktree.

## Conflicts and resolutions

### Specification labels versus implementation

Several implemented feature specifications still carry a `Draft` label, and the detailed FS-018 section in `Feature_slices.md` still says `Ready for specification` while the slice map says `Implemented`. Current source code, passing tests, completed implementation tasks, and FS-018 validation artifacts demonstrate the actual delivered behavior. The manual therefore includes the verified behavior and records the status-label inconsistency here.

### Planned FS-010 artifacts in the working tree

FS-010 specifications, tasks, dependency edits, and in-progress backend/client files exist locally, but the scope source does not mark FS-010 implemented and no completed FS-010 acceptance set was verified. It is excluded from the manual as available functionality.

### FS-006 entry point versus in-progress FS-010 controls

The last fully passing baseline exposed the implemented FS-006 **Several courses** workflow. Concurrent FS-010 edits replaced that panel with 1-20-Course conflict-aware optimization controls. The current production build passes after follow-up edits, but one client test remains failing and the backend suite cannot currently be collected in the active environment. The manual omits both workflows as available: FS-006 lacks its verified UI entry point, and FS-010 lacks completed implementation and verification.

### Historical single-resource wording

Early FS-001 through FS-006 artifacts describe one Lecturer and Room per Course. FS-008 broadened the current implementation to multiple eligible resources while keeping exactly one Lecturer and one Room per Draft Session. The manual uses the current FS-008 behavior.

### Manual creation versus edit assignment rules

The verified FS-009 creation workflow inherits the Course Lecturer and offers current capacity-valid Rooms; changed assignments in the existing-session editor use the stricter current eligibility, lifecycle, availability, and capacity checks. The manual documents these workflows separately.

## Excluded and unavailable functionality

The manual explicitly lists these current limitations rather than presenting them as instructions:

- global conflict-aware optimization and automatic conflict repair
- holiday avoidance and exams
- publication lifecycle and calendar dashboard
- lecturer review, authentication, and role management
- imports, synchronization, email, and SSO
- persistent batch history, background generation, full-Semester bulk deletion, and session split/merge

## Documentation gaps

- FS-007: the specified 10-participant usability protocol has not been conducted.
- FS-008: the specified 10-participant protocol, complete wide/narrow walkthrough, and exact browser timing protocol remain pending.
- FS-009: the specified 10-participant manual creation and deletion-comprehension review remains pending.
- FS-018: explicit 200% zoom, NVDA with Firefox, and the representative-review study remain pending.
- FS-004 and FS-005 task lists retain unchecked manual smoke activities even though the corresponding automated suites pass.
- Current concurrent FS-010 integration leaves one client test failing and prevents backend test collection in the active environment until its new solver dependency is installed.

No screenshots were embedded in the manual. Existing verified navigation screenshots remain available under `specs/018-unified-app-navigation/validation/screenshots`, and broader UI audit images remain under `artifacts/ui-navigation-audit`.

## Assumptions and limitations of this manual

- The primary audience is the planner user described by `Feature_slices.md`.
- Local PowerShell startup is documented because no deployed production address or deployment runbook exists in the repository.
- The manual uses current visible UI labels and does not describe backend API use as an end-user workflow.
- Demonstration seeding is optional and intended for a local environment; it is not a production data-import workflow.
- No usability, accessibility-conformance, or production-readiness claim is inferred from passing automated tests.

## Recommended verification steps

1. Have a first-time planner follow only the Quick Start against a clean local database.
2. Either restore the passing FS-006 **Several courses** UI or finish FS-010, install its declared solver dependency, and complete its tests and acceptance evidence.
3. Re-run the complete backend tests, client tests, lint, and production build until all pass before documenting a multi-course workflow.
4. Conduct and record the pending representative-user protocols for FS-007, FS-008, FS-009, and FS-018.
5. Complete FS-018 acceptance with 200% text zoom and NVDA/Firefox on Windows.
6. Run the remaining FS-004 and FS-005 manual smoke scenarios and record their outcomes.
