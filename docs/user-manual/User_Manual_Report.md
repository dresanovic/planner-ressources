# User Manual Update Report

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
