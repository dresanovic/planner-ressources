# FS-022 surface migration control

This matrix turns `contracts/surface-inventory.md` into the implementation and verification control. Rows may be refined as exact occurrences are migrated, but no row may be removed without a machine-boundary or fixed-copy justification.

| Surface group | Terminology occurrences | Human dates or entry | Known problem states | Owning mapper/component | Planned automated evidence | Machine/fixed-copy exclusions |
|---|---|---|---|---|---|---|
| Application shell/navigation | Schedule, Academic Data navigation/headings | None | Bootstrap catalog failure | `main.tsx`, `App.tsx`, `ApplicationNavigation.tsx` | `main.test.tsx`, `App.test.tsx`, `ApplicationNavigation.test.tsx` | Stable navigation IDs and routes remain unchanged |
| Academic data | Course, Cohort, Lecturer, Room and Academic Data contexts | Semester start/end | Field validation, load/save, stale, permission, connectivity | `AcademicDataPage`, `AcademicRecordEditor` | Page/editor component tests | Record names and API ISO values remain unchanged |
| Resource administration | Lecturer, Room, Course contexts | Availability start/end and display | Field validation, load/save/delete, permission, stale, connectivity | Resource editors and `ProtectedDeleteDialog` | Resource/eligibility/holiday component tests | Resource IDs, kinds and stored names remain unchanged |
| Holidays | Fixed German copy plus applicable catalog contexts | Holiday date | Field validation and operation failures | `HolidayAdministration` | `HolidayAdministration.test.tsx` | Holiday API date remains ISO |
| Course schedule and draft generation | Schedule, Course, Lecturer, Cohort, Room contexts | Generation/manual/session dates and summaries | Findings, validation, stale, connectivity, permission, ambiguous mutations | `CourseSchedulePage`, `DraftSchedulePanel`, schedule editors | Listed schedule/page tests | API payloads, URL state, sorting and snapshot ISO stay unchanged |
| Calendar workspace | Schedule, Course, Lecturer, Cohort, Room contexts | Anchor, headers, rows, ranges and accessible names | Findings and load/update failures | `CalendarPlanningWorkspace`, `SessionPane`, calendar utilities | Calendar/session/utility tests | Navigation/comparison values stay ISO |
| Exams | Course, Lecturer, Cohort, Room contexts; fixed German exam prose | Scheduled/recommended/final-teaching dates and dialogs | Outside-window warning, generation/manual validation, deletion/publication conditions | Exam editors/panels/dialogs and finding mapper | Listed exam and publication tests | Exam rules, severity and ISO transport stay unchanged |
| Lecturer review (accountless) | Course, Lecturer, Room, Schedule contexts | Session dates/timestamps | Safe findings, load/submit/review failures | Backend safe projection and `LecturerReviewPage` | Backend lecturer and page tests | Public response shape, bearer/privacy boundary and machine dates stay unchanged |
| Lecturer review management | Course, Lecturer, Schedule contexts | Review timestamps/session dates | Safe findings, load/coordination failures | `LecturerReviewManagement` | Management component tests | Domain references and secrets remain unchanged |
| Lifecycle/deletion/batch summaries | Selected contexts in labels; fixed German prose | Revision, schedule, exam and result dates/timestamps | Stale, conditions, partial/multiple issues | Lifecycle/dialog/result components | Listed lifecycle/dialog/result tests | Revision IDs and persisted timestamps remain machine values |
| Shared date boundary | None | All human display, range, timestamp and entry conversion | Invalid/incomplete/min/max/range correction | `datePresentation`, `EuropeanDateField` | Pure and component tests | APIs, persistence, comparisons, logs, URLs, fixtures and exports stay ISO |
| Shared problem presentation | Catalog terms only when caller supplies context | Dates formatted before mapping | Blocking/warning, field, stale, connectivity, permission, unknown and multiple | `userProblems`, `ActionableProblemList` | Pure/component and owning-surface tests | Raw diagnostics are never presentation input |

## Completion fields

For each row, final verification will add the exact changed paths, failing-first evidence, final result, manual result where required, and any justified exclusions. Native `type="date"`, browser-locale presentation, joined error arrays, direct raw backend/error messages, and raw-code primary labels remain open until the final boundary-aware audit.

## Convergence evidence — 10.08.2026

- `ExamRequirementEditor` now renders distinct `UserProblem` items, stable
  field error IDs, `aria-invalid`/`aria-describedby`, preserved values, and
  first-invalid focus after the button-driven save attempt. Failing-first and
  passing evidence: `ExamRequirementEditor.test.tsx`.
- `ProtectedDeleteDialog` maps blocker kind/type/count locally and never renders
  the backend blocker `message`; `PublicationConfirmationDialog` maps known
  condition codes/details and uses a safe German fallback. Failing-first and
  passing evidence is in their component tests.
- `AcademicCatalogList`, `ResourceCatalogList`, `ResourceEditor`,
  `CourseResourceEligibilityEditor`, and `AcademicDataPage` now use German
  action/state copy and catalog values for selected Course/Lecturer/Room and
  Academic Data contexts. Candidate reason codes are mapped through safe user
  explanations rather than shown as primary labels.
- The accountless review loading/unavailable/header/fixed-lecturer context is
  German and consumes `lecturer.singular`; secret handling and public response
  contracts remain unchanged.
- Automated result: 51 client files / 356 tests, lint, and production build all
  pass. Backend remains at 481 passing tests from the same implementation run.
- The final source audit remains open: `CourseSchedulePage`, calendar outcome
  summaries, lecturer-management, and other inventory rows still contain
  presentation literals or raw-code humanization. Browser/NVDA and real-user
  evidence also remain open and are not inferred from jsdom.
