# User Manual Update Report

## Summary

The user manual was updated on 2026-07-28 to match the current verified Resource Planner.

The previous manual stopped at the early planner baseline and explicitly described semester optimization, holidays, exams, versioned publication, and the calendar workspace as unavailable. Those sections were replaced with verified instructions for the complete planner-only MVP and the merged streamlined Schedule workspace.

Output:

- Manual: `docs/user-manual/User_Manual.md`
- Report: `docs/user-manual/User_Manual_Report.md`

## Evidence reviewed

- `docs/planning/Feature_slices.md`
- specifications, plans, tasks, quickstarts, contracts, and validation evidence under `specs/001-*` through `specs/014-*`, `specs/018-*`, and `specs/019-*`
- current backend implementation and API/service/repository tests
- current React application shell, Schedule and Academic Data pages, components, API clients, and component tests
- `backend/README.md` and `client/README.md`
- the existing user manual and generation report
- current Git history showing FS-013, FS-014, and FS-019 merged into `master`

The evidence priority was: verified current behavior, passing tests, implementation, accepted clarifications, specifications, scope map, plans/tasks, and older documentation.

## Verification performed

| Check | Result |
| --- | --- |
| `python -m pytest` in `backend` | 347 passed; exit code 0 |
| `npm run test` in `client` | 41 files and 250 tests passed |
| `npm run lint` in `client` | Passed |
| `npm run build` in `client` | Passed |

The backend run emitted a Windows native-extension diagnostic after the successful pytest summary. The command still returned exit code 0 and every collected test passed. This diagnostic was not treated as a functional test failure, but it should be investigated if it recurs in a clean, non-concurrent verification run.

## Slice evidence table

| Slice | Status | Intended user | Entry point | Verified main use case | Primary evidence | Limitations or gaps | Manual action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FS-001 Single-Course Draft Schedule Generation | Implemented | Planner | Calendar > Planning inputs > One course | Generate a complete Course draft or preserve the existing draft with understandable failure reasons | Generation implementation; API/service tests; page/component tests | Produces complete one-Course replacements; partial planning is handled by FS-010 | Include Quick Start and Detailed Guide |
| FS-002 Review Generated Schedule | Implemented | Planner | Calendar modes and Calendar > List | Review sessions chronologically or by period and filter visible context | Calendar and DraftSchedulePanel implementation/tests | List remains the deliberate dense-review workflow | Include Quick Start and Detailed Guide |
| FS-003 Configurable Generation Constraints | Implemented | Planner | One course > Inputs for the next draft | Use Semester/Study type defaults, save valid custom constraints, and restore defaults | Constraint API/repository; client editor; automated tests | Constraint changes do not alter sessions until generation runs | Include Detailed Guide |
| FS-004 Manual Session Editing | Implemented | Planner | Calendar occurrence > Edit session; Calendar > List | Correct date, interval, Lecturer, or Room without losing Calendar context | Session pane/editor; PATCH behavior; backend/client tests | Pending manual acceptance evidence does not block verified automated behavior | Include Quick Start and Detailed Guide |
| FS-005 Conflict Detection | Implemented | Planner | Calendar warnings, summaries, and session pane | Inspect current overlap, capacity, window, holiday, resource, and exam-validity warnings | Validation services; workspace projection; tests | Warnings are non-blocking and are not automatic repair | Include Detailed Guide |
| FS-006 Multi-Course Draft Generation | Implemented; user outcome superseded by FS-010 UI | Planner | Calendar > Planning inputs > Several courses | Generate several selected Courses from one operation | Legacy batch API/tests; current conflict-aware several-Course workflow | The old independent batch UI is no longer exposed; the stronger coordinated workflow is documented | Include Quick Start and Detailed Guide under optimization |
| FS-007 Academic Planning Data Administration | Implemented | Planner | Academic Data categories | Create, edit, archive/reactivate, and safely delete academic records | Academic implementation and API/service/component/performance tests | Representative-user usability study remains pending | Include Quick Start and Detailed Guide |
| FS-008 Resource Eligibility and Availability | Implemented | Planner | Academic Data > Lecturers, Rooms, Courses | Maintain coded resources, unavailability, eligibility, capacity, and lifecycle | Resource implementation; regression/performance tests | Representative-user and recorded responsive acceptance evidence remain incomplete | Include Detailed Guide |
| FS-009 Manual Session Management | Implemented | Planner | Planning inputs > Add one Draft Session; session deletion; Clear course draft | Add, delete, or clear teaching sessions with consequence and stale-state protection | Draft repository/API; dialogs; backend/client tests | Representative-user study remains pending | Include Detailed Guide |
| FS-010 Conflict-Aware Semester Optimization | Implemented | Planner | Calendar > Planning inputs > Several courses | Maximize scheduled units for 1-20 Courses without new resource/cohort conflicts and retain improved partial plans | OR-Tools optimizer; preparation/execution APIs; service/API/performance/client tests | Result summary is mounted UI state, not persisted operation history | Include Quick Start and Detailed Guide |
| FS-011 Institution Holiday Calendar | Implemented | Planner | Academic Data > Holidays; Calendar warnings | Maintain full-date holidays, avoid them in generation, and warn on saved affected sessions | Holiday CRUD, generation/validation integration, backend/client tests | One institution-wide full-date calendar only | Include Detailed Guide |
| FS-012 Conflict-Aware Exam Scheduling | Implemented | Planner | Schedule > Exams; Calendar exam occurrence | Configure requirements; generate, place, correct, review, and delete exams safely | Exam services/APIs/components; optimization, regression, and performance tests | One responsible Lecturer/Cohort; no registration, grading, invigilation, or external booking | Include Quick Start and Detailed Guide |
| FS-013 Versioned Review and Publication | Implemented | Planner | Schedule > Versions | Start, mark ready, publish, revise, abandon, restore, and inspect immutable history | Lifecycle API/service/concurrency/performance/component tests; recorded validation | Representative-user lifecycle study remains pending | Include Quick Start and Detailed Guide |
| FS-014 Calendar Planning Workspace | Implemented | Planner | Schedule > Calendar | Operate a coherent revision-scoped Week/Day/Month/List workspace with summaries, filters, traceability, and read-only publication context | Calendar workspace API/service/performance/components and tests | Recorded manual browser, assistive-technology, zoom, and representative-user evidence remains incomplete | Include Quick Start and Detailed Guide |
| FS-015 Accountless Lecturer Review | Not implemented | Planner/Lecturer | None | None | Scope identifies later release only | No secure review link or feedback workflow | Exclude |
| FS-016 Authenticated Access and Roles | Not implemented | Planner/Lecturer | None | None | Scope identifies later release only | No authentication or role separation | Exclude |
| FS-017 External Import and Synchronization | Not implemented | Planner/provider | None | None | Scope identifies later release only | No external provider integration | Exclude |
| FS-018 Unified Application Navigation | Implemented | Planner | Shared application navigation | Reach Schedule and all Academic Data destinations through one responsive hierarchy | Navigation implementation/tests and validation artifacts | Some recorded zoom, screen-reader, and representative-user evidence remains pending | Include Quick Start and Detailed Guide |
| FS-019 Streamlined Schedule Workspace | Implemented behavior; scope-record gap | Planner | Schedule > Calendar, Versions, Exams | Use focused destinations, in-pane correction, independent navigation pinning, and collapsible Planning inputs | Merged implementation; 250 passing client tests; focused validation artifacts; client README | `Feature_slices.md` does not yet list FS-019; manual browser/AT and 10-reviewer acceptance tasks remain blocked | Include Quick Start and Detailed Guide with evidence gap reported here |

## Slice coverage

- Implemented and documented: 16
- Partially implemented: 0
- Excluded as not implemented: 3
- Requiring slice-level functional verification before documentation: 0

Pending acceptance evidence is listed below. It limits usability and accessibility claims, not the verified functional instructions in the manual.

## Major documentation changes

- Replaced the outdated **Schedule** entry point with **Schedule > Calendar**, **Versions**, and **Exams**.
- Added the active Working revision prerequisite and **Start Draft** first-use step.
- Replaced the old List/Weekly-first correction instructions with Calendar occurrence selection and the adaptive session pane.
- Added the unsaved-change guard and wide/narrow pane behavior.
- Added conflict-aware semester optimization for 1-20 Courses, prepared-snapshot confirmation, partial outcomes, stale preservation, and retry.
- Added institution holiday administration and its effect on generation and current warnings.
- Added exam requirement, eligibility, automatic generation, manual placement, correction, and deletion workflows.
- Added Draft/Ready for review/Published lifecycle, safe post-publication revision, abandonment, restoration, and history.
- Added Week, Day, Month, and List Calendar modes; operational summaries; filters; contributor drilldowns; and Working/Published context.
- Added wide navigation pinning and independently collapsible Planning inputs.
- Removed obsolete limitations that described FS-010 through FS-014 as unavailable.
- Retained and reorganized verified academic-data, resource, eligibility, manual-session, validation, startup, and troubleshooting instructions.

## Conflicts and resolutions

### FS-019 is absent from the scope map

`docs/planning/Feature_slices.md` currently stops at FS-018. FS-019 nevertheless exists as a merged implementation on `master`, has a complete client-side automated suite, validation artifacts, and current user-facing documentation in `client/README.md`.

Because current verified behavior outranks the stale scope record for user instructions, the manual documents the interface users actually receive. The scope-record mismatch remains an explicit documentation gap and was not silently corrected during this manual-only task.

### Specification labels versus delivered behavior

Several older specifications retain a `Draft` label even though their implementations and tests are delivered. The manual uses verified behavior and the current scope map rather than interpreting the front-matter label alone.

### FS-006 versus FS-010

The former independent several-Course UI was replaced by the conflict-aware FS-010 workflow. The legacy FS-006 backend contract and tests remain, while the visible user outcome—planning several Courses in one operation—is now provided by the stronger optimized workflow. The manual documents the current entry point rather than an unavailable legacy screen.

### Published content versus current validation

Published schedule content is immutable. The Calendar may still calculate clearly current warnings from changed planning data. The manual distinguishes stable Published content from current validation warnings so neither behavior is misrepresented.

## Excluded functionality

The manual does not present these later-release or out-of-scope capabilities as available:

- lecturer review links, feedback, or lecturer accounts
- authentication and role-based access
- provider-neutral or provider-specific import and synchronization
- automated email and institutional SSO
- external room booking or operational publication delivery
- drag-and-drop, resize, split, merge, or duplicate Calendar editing
- background optimization or persisted optimization-result history
- multiple institutional or partial-day holiday calendars
- student registration, grading, or broad invigilator management

## Documentation and verification gaps

- `docs/planning/Feature_slices.md` needs a product-owner-approved FS-019 entry and status.
- FS-019 T059 remains blocked: the full wide, unpinned, 70rem boundary, 820px, 320px, 200% zoom, NVDA/Firefox, focus, and screenshot acceptance matrix has not been recorded.
- FS-019 T060 remains blocked because ten representative planners or designated reviewers were unavailable.
- FS-019 final review T061 remains blocked by those two acceptance tasks.
- FS-014 retains related manual browser, zoom, assistive-technology, and representative-user evidence gaps.
- FS-007, FS-008, FS-009, FS-013, and FS-018 retain specified representative-user or recorded manual acceptance gaps.
- No new screenshots were embedded in the manual.
- The backend verification emitted a post-summary Windows native-extension diagnostic despite all tests passing with exit code 0.

## Assumptions and limitations of this manual

- The primary audience is the planner user.
- Local PowerShell startup is documented because the repository has no production deployment address or end-user deployment runbook.
- The manual describes visible UI workflows rather than backend API use.
- Passing automated tests establish functional behavior; they do not establish production readiness, formal accessibility conformance, or usability-study success.
- FS-019 changes frontend composition and interaction only; it does not introduce new scheduling, lifecycle, eligibility, or persistence rules.

## Recommended verification steps

1. Have a first-time planner follow only the Quick Start against a clean local database.
2. Run the FS-019 browser matrix at wide pinned/unpinned, the 70rem pane boundary, 820px, 320px, and 200% zoom.
3. Complete keyboard and NVDA/Firefox checks for navigation, Calendar, session pane, dirty-change dialog, Versions, and Exams.
4. Conduct the required representative-planner reviews and record the results without inferring missing outcomes.
5. Re-run backend tests in a clean isolated process and investigate the Windows native-extension diagnostic if it recurs.
6. Add FS-019 to `docs/planning/Feature_slices.md` through the product scope workflow.
7. Capture three verified screenshots: Schedule navigation and context header, Calendar with an open session pane, and focused Versions/Exams workspaces.
