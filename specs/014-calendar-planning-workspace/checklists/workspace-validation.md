# FS-014 Workspace Validation

Date: 2026-07-27  
Branch: `codex/fs-014-calendar-workspace`

## Automated evidence

| Check | Result |
|---|---|
| Migration and retained-outcome focused tests | PASS — reliable completion, request-level rejection, rollback, supersession, all optimization classifications, and exam stale-context matrices |
| Workspace service/API focused tests | PASS — revision selection/isolation, v1/v2 publication context, exact aggregation, availability, coverage, and contributor reconciliation |
| Phase 12 focused regression | PASS — 10 backend workspace-service tests and 25 client filter/workspace tests covering failed/stale no-issue exclusion, both drilldown clear paths, context restoration, and deterministic focus |
| Backend full regression | PASS — 344 tests |
| Client workspace/API/page/List convergence tests | PASS — 88 tests covering canonical planning eligibility, malformed response rejection, lifecycle/race coherence, correction handoff, contributor routing, restoration, and exact List focus |
| Client full regression | PASS — 213 tests across 38 files |
| Client lint | PASS |
| Client production build | PASS |
| Reference-scale workspace service, 20 loads | PASS — 100 courses, 500 occurrences, 50 holidays; clean virtual-environment performance test passed |

The Python suite reports existing framework deprecation warnings for
`datetime.utcnow`, Starlette status aliases, and the TestClient transport. No
FS-014 test failure remains.

## Browser and responsive evidence

Environment: Codex in-app browser, Vite development build, FastAPI local
backend, Windows.

- PASS: 1280×720 wide view showed the calendar workspace as the first
  operational surface with no document-level horizontal overflow.
- PASS: the workspace retained all five summary cards, Week/Day/Month/List,
  date controls, filters, revision context, and occurrence cards.
- PASS: List rendered exactly one `Courses overview` from the existing
  `DraftSchedulePanel`; the List current-period control was disabled and
  announced as not applicable.
- PASS: 320×900 view had no document-level horizontal overflow, retained all
  five summaries and all four mode controls, showed the workspace before the
  long planning-input form, and left the FS-018 Menu unobstructed.
- PASS: the selected semester/revision identity remained persistent and used
  non-color text labels.
- PASS: the reference-scale dense Month date exposed `Show all 100 sessions`,
  expanded to all sessions through a semantic button, and retained zero
  document-level horizontal overflow at 320×900.
- PASS: a computed-style audit of 62 visible workspace text samples found no
  enabled text below 4.5:1 after correcting selected-control and disabled
  summary-card cascade conflicts; the minimum measured enabled-text ratio was
  4.56:1.
- PENDING: supported screen-reader matrix.
- PENDING: actual 200% browser zoom check; the available browser viewport
  override verified the equivalent 320-CSS-pixel reflow, but its browser zoom
  control did not change zoom.
- PENDING: measured 3:1 essential non-text contrast audit.
- PENDING: formal physical-keyboard and supported-screen-reader protocol beyond
  automated focus, semantic, live-region, and dense-date coverage.

## Reference-scale performance evidence

Environment: deterministic temporary SQLite database, FastAPI using the project
virtual environment, Vite development build, Codex in-app Chromium browser,
Windows. Warm-up preceded every 20-run series.

| Path | Browser result | Threshold result |
|---|---:|---|
| Complete initial page/workspace load | 20/20; 2.095–2.452 s | PASS SC-010 — 20/20 under 3 s |
| Calendar Week/Day visible-state change | 20/20; 0.298–0.321 s | PASS SC-011 — 20/20 under 1 s |
| Working/Current Published context switch | 20/20; 0.338–0.533 s | PASS SC-011 — 20/20 under 1 s |
| Successful Ready/Draft action to refreshed calendar context | 20/20; 0.398–0.689 s after action dispatch | PASS SC-012 — 20/20 under 2 s |

The same reference workspace API was measured separately over 20 HTTP requests:
median 664.8 ms, p95 782.1 ms, maximum 788.4 ms, with 20/20 under 3 seconds.
The first action-refresh run exposed a sequential refresh waterfall. The
calendar/lifecycle critical refresh was moved alongside the established
schedule and exam refreshes, after which the final 20-run post-action series
passed.

## UI-reference comparison

Primary inspiration:
`docs/designs/resource-planner-calendar-screen-reference.png`.

Adopted gradually:

- compact mode and date controls;
- operational summary/alert cards before the calendar;
- central date-grouped session cards;
- persistent semester/revision context;
- warning badges and an inspectable detail region;
- responsive sequential composition.

Deliberate differences:

- product terminology remains Course, Cohort, Lecturer, Room, Working, and
  Current Published;
- existing FS-009–FS-013 correction dialogs/editors remain authoritative;
- no Dashboard destination, lecturer access, notes, save-changes form,
  duplication, drag/drop, or resize was copied from the reference;
- calendar cards use semantic grouped dates rather than claiming a
  pixel-perfect time-grid clone.

Shared navigation reference:
`docs/designs/resource-planner-unified-navigation-ground-truth.png`.
The existing FS-018 Schedule destination and Academic Data hierarchy remain
unchanged, current, keyboard-operable, and unobstructed at the checked narrow
size.

## Scope audit

- PASS: no second List implementation or second rendered list.
- PASS: no Dashboard destination.
- PASS: no drag, drop, resize, duplicate, split, merge, or automatic repair.
- PASS: no new optimizer or exam-generation behavior.
- PASS: no lecturer access or authentication change.
- PASS: no external synchronization or delivery.
- PASS: no independent course publication.
- PASS: filters and calendar navigation issue no mutation request.
- PASS: Working and Current Published are selected atomically and never blended.
- PASS: Working and Current Published conflicts, capacity, holiday, resource
  eligibility/active-state, resource-unavailability, and teaching-constraint
  checks share established validation sources; legacy v1 publications identify
  missing constraint-dependent coverage as partial.
- PASS: every operational metric returns typed contributor references.
- PASS: the No current issue validation scope excludes course contexts affected
  by failed or stale retained outcomes, including unscheduled courses, while
  the dedicated failure and stale scopes retain their exact affected records.
- PASS: dated contributors outside the visible period open in Day mode while
  retaining the selected revision and clearing the drilldown restores the
  prior mode/date context.
- PASS: undated course, planning-outcome, and validation-finding contributors
  route into the reused Courses overview with exact affected-course and related
  teaching/exam linkage; focus moves to a visibly identified affected-record
  target.
- PASS: summary drilldown focus enters the labelled contributor region and
  returns to the initiating summary after either Clear drilldown or the
  combined Clear filters action; both paths restore the prior calendar mode
  and date.

The separate historical-revision presentation remains available through the
FS-013 lifecycle history. It is not a second current Schedule List context.

## Acceptance and parity decision

Moderated SC-004–SC-006 evidence with at least 10 representative planners or
designated reviewers is **PENDING** because no such panel was available in this
implementation session. It is not reported as passed.

Therefore the T094 parity gate is **PENDING**. The adapted existing List is in
the unified workspace, but removal of any remaining legacy presentation
boundary under T095 and its post-removal verification under T096 must wait for
the required human, screen-reader, physical-keyboard, actual-zoom, and
essential-non-text contrast evidence.

Overall implemented-slice automated regression and performance status:
**PASS**. The manual accessibility and moderated acceptance gates remain
**PENDING**; this is not yet a release-parity declaration.
