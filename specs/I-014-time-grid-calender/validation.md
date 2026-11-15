# I-014 implementation evidence

Started 2026-11-13 on `codex/i-014-time-grid-calendar`, base
`a376fe67306578d5a47b7bf0ccf48b7245e052ef` (previous branch `master`).
Existing user changes preserved: `.specify/feature.json`,
`docs/planning/Feature_slices.md`, the three untracked design reference PNGs,
and this feature's untracked planning directory. No commit or publication requested.

## Setup (T001–T002)

Python `backend/.venv`: 3.12.8; pip check passes. Existing `.venv313` is
Python 3.13.0 but has no pip. Use the populated backend environment for checks;
deployment remains Python 3.13. Node 27.0.0-alpha.0.0.0, npm 11.13.0
(npm emits a runtime support warning); existing client node_modules and lock retained.
No dependency changes. Git/Docker/ESLint ignore coverage already includes the
required build, dependency, cache, environment and temporary patterns; private
client package requires no npm publish ignore. No Terraform/Helm/Prettier setup.

Disposable acceptance database: `C:/Codex/planner-resource/tmp/i014-acceptance.db`,
resolved inside the ignored workspace tmp directory, separate from planner.db and
manual-review-fresh.db. Automated service/API tests use isolated in-memory SQLite.

## Current status — 2026-11-15

Implementation and automated gates pass. **49 of 55 tasks are complete** after convergence task T052;
T044, T045, T049 and their convergence follow-ups T053–T055 remain open for the
outstanding observed acceptance matrix.
No actual assistive-technology session, genuine 200% text-enlargement observation,
removed-color walkthrough or five-planner trial is claimed.

Final results: backend focused 69 passed; full backend 1,119 passed/1 skipped
plus 29 subtests; performance passed; the original client focused gate had
214 passes, and the T052 focused gate has 56 passes. The latest full client suite
has 670 passes; TypeScript/build/lint and `git diff --check` passed. See
[backend results](verification/backend-results.md) and
[client results](verification/client-results.md).

The checkpoints below are historical evidence, not the final pending state.

## US1 test-first and automated checkpoint (T003–T018)

Shared June fixture added. Backend red run: 3 missing-field failures, 15 existing
checks passed. Client red run: two new modules absent, decoder quarantine failure,
9 existing decoder checks passed (after correcting a fixture finding-reference
format). Vite initially could not spawn a child in the sandbox; approved retry
ran successfully. First post-change run exposed a test's incorrect issue-code
assumption; authoritative code is COHORT_CALENDAR_WINDOW_VIOLATION. Corrected
fixture/oracle to the existing rule, without editing business validation.

US1 final targeted results: backend 18 passed; client 42 passed (API, layout,
hourly surface, existing workspace); production build exit 0. New helper asserts
882px start, 366px height, 80-minute outside interval; no-write SQL dump matches.
Browser measurements are in progress. Fixture breadth and additional edge-case
coverage remain tracked; tasks are not marked complete on partial evidence.

## US2–US4 incremental results

US2 pre-enhancement: 47 backend checks pass as characterization; client 80 pass
and the intended new grouping test fails (helper absent). Post enhancement:
82 client checks pass. Backend uses captured profiles/identity only; current
validation basis remains unchanged. Calendar identities and different effective
profiles are separated. Missing restricted context remains absent and makes no
planner fetch. Marker-only profile changes alter the existing token.

US3 red: missing Month module and two missing Month helpers; 108 existing
checks pass. Post Month implementation: 142 tests pass across layout, Month,
workspace and CourseSchedulePage. 0/1/5/20 cases, complete Monday weeks,
leap/year dates, first-three overflow, +2/+17, expansion and callbacks verified.

US4 red: missing provenance in session accessible label and missing hours/state
in Month summary; 137 checks pass. Post fixes: 139 checks pass. Additional
visual overrun segment test fails before paint, then passes after adding a
96px patterned segment. Build exit 0; first lint found a shared function exported
from a component module; moved that presentation helper to the layout module.
Final lint is pending below. No automated result claims actual AT or human use.

Browser initial observation (ChatGPT in-app browser, local reference harness):
Day actual border-box height 366px; top minus canvas top = 882px; window bottom
1387.359375 and block bottom 1483.359375, difference 96px. Canvas 1728px;
initial scrollTop 576px (08:00 window). Source fixture rendered through the real
workspace component. This is geometry evidence, not a full live authenticated
application/correction acceptance run. Additional final screenshots pending.


## Review corrections and additional coverage

Review found and corrected: inconsistent unavailable-section data being usable;
Month date navigation snapping to a selected session; missing date columns when
no calendar is identifiable; and the missing single-source explanation when
adjacent paint covers all minutes. Regression tests failed before each correction.
The real narrow pane also made the calendar source disclosure inert; two failing
SessionPane tests now prove the same context is inside the modal in detail and
editing modes. Spec/plan were clarified before that production correction.

Reusable fixtures now include June, separate A/B identities, zero-session course,
dated/intensive, current/legacy Published metadata and missing identity. Additional
API cases verify mixed availability and captured/nullable references through the
existing authenticated route. A new API no-write test initially included the
normal auth-session activity timestamp; its oracle was corrected to exclude only
planner_sessions inserts. The service's complete-dump zero-write test is unchanged.

One live save attempt initially failed because the inherited fixture's saved
semester snapshot still contained 2026 dates. The fixture builder and disposable
fixture were aligned to June 2027; no application validation rule was changed.
The retry and return correction then succeeded. An attempted dense fixture also
hit the existing one-session-per-course/date constraint; it was rolled back and
rebuilt using separate courses, retaining that invariant.

## Browser and live application observations

Browser: ChatGPT in-app browser (version not exposed by this tool). Initial and
resumed observations used the same real components; the later live application
served the production build at loopback port 8014 against the explicitly disposable
`tmp/i014-acceptance.db`, with a synthetic local test account. No normal planner
DB was seeded, migrated or edited. The ignored `client/tmp/i014.html` harness was
used for controlled 0/1/5/20 and source-state variants, not as a substitute for the
live correction flow.

| Case | Actual observation |
|---|---|
| Reference Day | 882px start offset, 366px border-box height, 96px outside portion and patterned segment; 1,728px canvas |
| Reference Week | All seven date columns, 1,728px canvases, full 366px reference block |
| Empty permitted gap | 09:00–10:00 and 12:00–13:00 blocks each 72px; positions 648px/864px leave exactly 144px empty for 10:00–12:00 |
| Early/late | 00:00–01:00 at top 0px/height 72px, 23:00–23:45 at top 1,656px/height 54px; keyboard end scrolling and late detail reachable |
| Three identical overlaps | Three 108px blocks at 0%, 33.3333%, 66.6667%; each selected with Enter; close returned focus to its original block |
| A/B | Separate calendar:1/calendar:2 columns; A shows 08:00–16:00 and 80-minute overrun while B shows 10:00–18:00 without borrowed permission |
| Dated intensive | 07.06.2027 shows only dated 10:00–12:00, Intensive, source 3; following Monday 14.06 shows weekly 08:00–16:00 |
| Different course profile | Same calendar has a separate course-specific profile/revision group beside the standard profile group |
| Adjacent sources | Separate 08:00–13:00 and 13:00–18:00 sources; original finding remains with explicit single-source explanation; no invented zero-overrun claim |
| Published/legacy | Captured/read-only labels for Published; legacy retains session with unknown context and no invented outside paint (controlled harness plus real API/snapshot tests) |
| Failed context/retry | Session remains selectable, unknown background and zero outside paint; retry callback activated (controlled harness) |
| Crowded Month | 35 complete dates, first three of 20 entries, exact +17, all 20 reachable on expansion; focus stays on collapse/expand control |
| Empty Month/overflow counts | 0/1/5/20 cases plus +2/+17 pass component tests; complete empty dates and calendar-specific summaries observed in browser |
| 320px | Surrounding controls wrap, no document-level horizontal overflow (305px content after scrollbar); Day and Month have separately labeled scroll regions |
| Modal pane | Source/date/calendar/hours are inside the actual narrow dialog in detail and editing, including the custom planner pane |
| Correction | Live Month entry -> edit -> changed date -> close confirmation -> continue retains input -> cancel/discard preserves saved session; subsequent save to 27.06 and save back to 26.06 both succeed and refresh window context |
| Date/List | Month date -> Day 25.06 works after closing details; retained List exposes the original teaching and exam identities |

Screenshots are in verification/: day-reference.jpg, day-320.jpg,
month-reference.jpg, month-320.jpg, multiple-calendars.jpg,
live-modal-context.jpg and live-correction-return.jpg. Viewport overrides were
reset. These observations do not establish actual AT announcements or the
five-human comprehension criterion.

## Zero-write and snapshot evidence

Before/after live viewing, mode/date navigation and edit/cancel, all non-auth
planning records had the identical SHA-256 fingerprint:
`4a1c6577d1f549b43d017e15509d23c6340ea0002646e9c7b7b3d1cf7e637d24`.
After explicitly adding the expanded fixture cases, a new view-only baseline was
captured and retained through the custom/adjacent/Week observations:
`93675f74e55994039f976d332e0ef92de552329fb95752c0324d1bf145ee4bd6`.
The authorized correction saves and fixture-setup writes are excluded from view-only
claims. Authentication session activity remains intentionally outside planning
fingerprints. API/service tests also verify captured snapshots are not rewritten
by reads and missing historical context never joins live permission.

## Acceptance boundary

- SC-001: Passed automated and observed reference/gap/early/late/overlap checks.
- SC-002: Passed source/provenance/context checks with the browser/API/harness
  provenance distinctions above; no client rule or validation severity changed.
- SC-003: Passed overflow/date/selection/List coverage; live correction/save/cancel
  and refresh were also observed.
- SC-004: Pending five representative planners, with anonymized timing/answers.
- SC-005: Partial: keyboard, non-hover facts, 320px, focus and modal context observed;
  actual AT, genuine 200% text enlargement and removed-color walkthrough pending.
- SC-006: Automated invariants and recorded live view-only fingerprints pass;
  the complete observed matrix remains open while T044/T045 are incomplete.

T044/T045/T049 remain unchecked. Their absence prevents claiming full acceptance
or merge readiness. No participant results or AT behavior are inferred from tests.

## Scope and final identity

No endpoint, dependency, migration, snapshot format, public-review access,
permission, generation/validation/availability algorithm, save or publication rule
changed. Production changes are response schema/projection, decoder, presentation,
and existing pane/navigation integration. User planning files/reference images were
preserved. No commit, push, deployment or publication was performed.

Branch and base revision remain as recorded above. `verification/change-manifest.json`
identifies the exact production/test file contents reviewed. Final diff whitespace
check passes. Extension configuration was checked before and after implementation;
`.specify/extensions.yml` is absent, so no hooks were registered to dispatch.


## Convergence correction T052 — selected calendar under session filters

The clean-context convergence pass found that window context was taken from
`projection.courses`, whose membership depends on matching sessions. Nine new
workspace regressions (Day/Week/Month × room/session-type/validation filter)
failed before the correction: explicitly selected Calendar A lost its known
08:00–16:00 and course-specific 09:00–15:00 context when sessions became empty.
The existing 30 workspace tests passed in that red run.

Explicit calendar selection now takes courses from the loaded workspace through
the existing `matchesCourseContext` predicate, respecting calendar, course and
cohort selection. Session-related filters still drive the unchanged session,
summary and List projection. The predicate was exported for reuse rather than
reimplementing the course/context matching rules. With no calendar selected,
context still follows the visible matching sessions.

All nine new cases pass. They verify that empty results keep both selected
calendar profiles, omit Calendar B's 10:00–18:00 context, leave List session/course
IDs empty, and respect a narrower course filter. Clearing explicit calendar
selection either shows Calendar B for its matching room/validation result or
shows the no-calendar prompt for the empty exam filter; no unrelated permission
is inferred. The tests cover Day, Week and Month.

Verification: 56 focused tests pass; all 670 client tests pass; TypeScript/Vite
build, ESLint and `git diff --check` pass (exit 0). Lint initially caught an unused
parameter in the new test callback; the callback now renders its captured count.
See `verification/convergence-t052-tests.txt`, `convergence-t052-full.txt`,
`convergence-t052-build.txt` and `convergence-t052-lint.txt` for raw results.
No backend, source-window precedence, permission, persistence or publication
behavior changed. No commit was made. Existing user changes were retained.

Review of the corrected branch found no remaining material code finding within
T052. The shared course/context predicate preserves existing matching semantics;
restricted review still uses its already-authorized workspace courses, with no
additional fetch. Actual AT/text enlargement, five-planner observations and the
full acceptance reconciliation remain pending under T053–T055 and their original
tasks T044/T045/T049. No extension configuration exists, so no hooks were dispatched.

## User-requested calendar simplification — 15.11.2026

Supersedes T052's empty-calendar display behavior per the user's clarification. Month calendar placeholders and the Day/Week source overview were removed; all dates remain, with session-bearing cohort/profile columns only and a single empty column otherwise. Month sessions display cohort abbreviations with full-name access. Cohort checkboxes support subsets combined with lecturer and other filters, navigation, refreshed facets and reset.

Verification: 676/676 client tests pass across 74 files; TypeScript/Vite production build, ESLint and git diff --check pass. Scoped review found no material findings. No browser visual inspection was performed in this pass; original observed acceptance tasks remain separate. See [calendar-simplification-review.md](verification/calendar-simplification-review.md). No backend or scheduling behavior was changed by this follow-up, and no commit was made.
