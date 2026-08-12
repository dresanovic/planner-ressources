# Quickstart: Verify Unified Teaching Schedule Generation

## Preconditions

- Work on `codex/I-003-unified-schedule-generation` or an equivalent isolated
  clean worktree before editing production files.
- Use a fresh test database seeded with one semester, one active editable working
  revision, at least two courses in the same cohort, shared eligible resources,
  study-type windows, and an institution holiday.
- Include Matematik 1 with an existing draft and Data Visualization as the course
  to regenerate. Add one active exam and one past exam.

## Test-first sequence

1. Add failing service tests for protected unselected teaching, active exam
   occupancy, past-exam exclusion, exact-boundary adjacency, same-course exam
   deadline, effective date overrides, and live study-type windows.
2. Add failing API contract tests for immediate constraint save/reset, stale
   preparation, one-to-twenty unified selection, replacement confirmation, and
   `410` legacy responses with no mutation.
3. Add failing React tests for the single selection surface, focused date editor,
   read-only windows, dirty-edit generation guard, specific warning copy, and List
   field association.
4. Implement only enough production behavior to pass those tests, then refactor
   while keeping the focused suites green.

## Automated verification

From the repository root:

```powershell
python -m pytest backend/tests/services/test_conflict_aware_generation.py backend/tests/services/test_semester_optimization.py backend/tests/services/test_draft_schedule_repository.py
python -m pytest backend/tests/api/test_conflict_aware_generation.py backend/tests/api/test_draft_schedule.py backend/tests/api/test_multi_course_generation.py
python -m pytest backend/tests/services/test_draft_schedule_validation.py backend/tests/services/test_exam_scheduling.py backend/tests/services/test_schedule_lifecycle.py
python -m pytest backend/tests
```

From `client/`:

```powershell
npm test -- src/pages/CourseSchedulePage.test.tsx src/components/DraftSchedulePanel.test.tsx
npm test -- src/components/CalendarPlanningWorkspace.test.tsx src/components/ScheduleOccurrenceList.test.tsx
npm test
npm run lint
npm run build
```

If a listed focused file does not yet exist when tasks are generated, place the
corresponding cases in the nearest existing service/component suite and update
this command list rather than creating a test-only abstraction.

## Core manual scenario

1. Start from fresh seeded data and create the active working revision.
2. Generate all eligible courses through the one unified panel.
3. Create an active Data Visualization exam that uses a lecturer, room, and cohort
   during otherwise eligible teaching time. Also retain a past exam.
4. Select only Data Visualization and prepare generation.
5. Confirm that the preparation identifies its current draft for replacement and
   displays the active saved dates plus read-only study-type windows.
6. Confirm replacement and generate.
7. Verify all Matematik 1 sessions and both exams are unchanged.
8. Verify regenerated teaching has no positive-duration lecturer, room, or cohort
   overlap with Matematik 1 or the active exam and ends no later than the active
   exam begins. Verify the past exam did not reduce candidate availability.

## Constraint activation scenario

1. Focus Data Visualization in Calendar Planning inputs.
2. Change its start/end dates and save without generating.
3. Verify the saved dates immediately appear as custom and any now-invalid existing
   teaching session receives a current constraint warning but is not moved.
4. Force generation to fail or submit a stale prepared token.
5. Verify the new dates remain active and the prior draft, manual edits, and exams
   remain unchanged.
6. Reset the override and verify semester dates are inherited again.
7. Change the course study type or its mapped windows in Academic Data; verify the
   Calendar editor updates read-only windows, existing sessions revalidate, and a
   previously prepared operation is rejected as stale.

## Legacy retirement scenario

Call each retired route with otherwise valid data:

- `POST /api/courses/{courseId}/draft-schedule/generate`
- `POST /api/draft-schedules/batch/prepare`
- `POST /api/draft-schedules/batch/generate`

Each must return `410`, code `GENERATION_ENDPOINT_RETIRED`, and the supported
prepare/generate paths. Compare database state before and after to confirm no
schedule, constraint, exam, or lifecycle record changed.

## Warning and List review

Create a manual overlap pair that shares lecturer, room, and cohort.

- Confirm three visibly distinct warnings: Lecturer conflict, Room conflict, and
  Cohort conflict.
- Confirm each warning names its resource plus the related course, date, and
  interval.
- Confirm no category appears twice for the same related session pair.
- Resolve one resource conflict and refresh; only that category disappears.

Review List mode at 1280, 820, and 320 CSS pixels at 100% browser zoom and with a
1280-pixel browser viewport at 200% zoom. Test zero, one, and several warnings
and long names at every presentation. Record browser zoom separately from
operating-system display scaling. Every value must remain associated with Date,
Time, Duration, Course, Cohort, Lecturer, Room, Study type, or Actions; controls
and warnings must remain reachable.

## Performance evidence

1. Record the application version, processor allocation, memory allocation,
   operating system or container environment, and confirmation that no competing
   workload is intentionally running.
2. Run one unmeasured warm-up operation using the reference workload of up to
   twenty selected courses, six hundred requested teaching units, and five
   hundred protected teaching/exam occurrences.
3. Run twenty sequential measured operations, recreating fresh reference input
   before every operation.
4. Record every duration, save status, and outcome summary.
5. Pass only when all twenty operations finish or return an actionable no-save
   failure within sixty seconds and at least nineteen finish within thirty
   seconds.

## Unaided usability evidence

Recruit at least ten representative semester planners whose responsibilities
include semester or course scheduling. Give every participant the same fresh
editable-revision scenario and no procedural coaching. A first-attempt success
requires the participant to:

1. select one or more courses;
2. locate the focused course's active start/end dates and read-only derived
   study-type windows; and
3. initiate unified preparation without entering a legacy workflow.

Record anonymized participant identifiers and pass/fail outcomes. SC-006 passes
only when at least 90% of participants succeed on their first attempt (nine of
ten for the minimum cohort). If ten representative participants are unavailable,
report the criterion as unverified rather than substituting developer testing.

## I-003 implementation evidence (2026-08-11)

- Unified backend, constraint, staleness, exam-boundary, and warning suites pass.
- Retired single and batch routes return the same `410`
  `GENERATION_ENDPOINT_RETIRED` body and preserve database state.
- Client verification passes: 54 files / 372 tests, ESLint, and production build.
- A fresh local database with long-named Data Visualization and Mathematik 1
  drafts sharing lecturer, room, and cohort showed exactly one
  `Lehrendenkonflikt`, one `Raumkonflikt`, and one `Kohortenkonflikt` for the
  affected row.

List matrix evidence from the in-app browser:

| Presentation | Header/labels | Horizontal table overflow | Warnings | Actions |
|---|---|---:|---|---|
| 1280 × 900 CSS px, 100% | matching nine-column header/row templates | 0 px | inside Date and reachable | reachable |
| 820 × 900 CSS px, 100% | stacked row with all nine explicit labels | 0 px | reachable | reachable |
| 320 × 900 CSS px, 100% | one-column fields with all nine explicit labels | 0 px | reachable | reachable |
| 1280 px at 200% zoom equivalent (640 CSS px) | stacked row with all nine explicit labels | 0 px | reachable | reachable |

The browser automation surface did not expose a browser-zoom setter, so the
200% case was verified using its layout-equivalent 640 CSS-pixel viewport. An
interactive browser-zoom confirmation remains a manual-only release check.
SC-006 also remains unverified because ten representative semester planners
were not available; developer testing was not substituted for that criterion.

Performance protocol evidence (Windows 11, Python 3.12.8, Intel64 Family 6
Model 170): one unmeasured warm-up followed by twenty fresh measured runs, all
optimal with 600 scheduled units and protected active-exam occupancy. Durations
in seconds were: `8.510`, `7.963`, `7.624`, `8.006`, `8.270`, `8.097`, `7.806`,
`8.067`, `7.799`, `7.934`, `6.950`, `7.693`, `7.679`, `8.133`, `7.705`, `7.526`,
`8.106`, `8.073`, `7.870`, `7.917`. All 20/20 completed below 30 seconds and
therefore below 60 seconds; both performance thresholds pass.
