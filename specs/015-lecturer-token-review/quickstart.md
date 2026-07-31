# FS-015 Validation Quickstart

This guide validates the FS-015 extension after implementation against
[spec.md](spec.md), [data-model.md](data-model.md), the
[API contract](contracts/lecturer-review.openapi.yaml), and the
[UI contract](contracts/lecturer-review-ui.md). It does not replace the full
acceptance matrix or moderated usability review.

## Prerequisites

- Python 3.12 and the backend requirements installed.
- Node supported by the repository CI and client packages installed.
- A clean disposable database upgraded through migration `0009`.
- A protected source-fingerprint HMAC secret containing at least 256 bits of
  random key material is configured and remains stable across application
  restarts. Production startup rejects a missing or shorter value.
- The frontend origin is HTTPS for production validation. Localhost HTTP may be
  used only for development.
- The trusted gateway satisfies
  [gateway-boundary.md](contracts/gateway-boundary.md): it protects every
  planner page/API, exposes only the exact accountless review surface,
  overwrites caller forwarding headers, is the only backend peer, and is the
  only peer trusted by Uvicorn proxy-header processing.
- Production `VITE_API_BASE_URL` is empty/same-origin and public requests omit
  browser credentials.
- Test data contains:
  - at least three lecturers;
  - at least two revisions in one or more semesters;
  - at least 20 teaching/exam sessions;
  - one lecturer assigned across several courses;
  - a course with several eligible lecturers but separately assigned sessions;
  - a Working Draft/Ready revision and a Current Published revision.

## 1. Automated verification

Run focused backend tests first:

```powershell
Set-Location C:\Codex\planner-resource\backend
python -m pytest tests/services/test_calendar_workspace.py tests/services/test_lecturer_review.py tests/services/test_lecturer_review_concurrency.py tests/api/test_lecturer_review.py tests/performance/test_lecturer_review_performance.py tests/db/test_migrations.py
```

Run FS-013 regression tests, then the full backend suite:

```powershell
python -m pytest tests/services/test_schedule_lifecycle.py tests/services/test_schedule_lifecycle_concurrency.py tests/api/test_schedule_lifecycle.py
python -m pytest
```

Run focused client tests, then full client verification:

```powershell
Set-Location C:\Codex\planner-resource\client
npm test -- src/api/lecturerReview.test.ts src/components/CalendarPlanningWorkspace.test.tsx src/components/LecturerReviewManagement.test.tsx src/components/SessionPane.test.tsx src/pages/CourseSchedulePage.test.tsx src/pages/LecturerReviewPage.test.tsx
npm test
npm run lint
npm run build
```

Expected result: every command exits successfully. Focused suites cover the
contract shapes, security boundaries, exact thresholds, races, one-time secret
handling, shared restricted workspace and pane, coordination filters and
counters, public feedback, and lifecycle non-effects.

Implemented-baseline local execution record, 2026-07-28:

- Focused FS-015 backend: `109 passed` (exit 0).
- FS-013 lifecycle regression: `26 passed` (exit 0).
- Full backend: `441 passed, 2 failed` (exit 1). Both failures are confined to
  `tests/scripts/test_seed_dummy_planning_data.py` expectations against the
  separately modified dummy-data seed script; no FS-015 or FS-013 test failed.
- Focused client: `3` files and `52` tests passed (exit 0).
- Full client: `45` files and `311` tests passed (exit 0).
- ESLint and the TypeScript/Vite production build passed (exit 0).

Because the full backend command did not exit successfully, T057 remains open.
The separately modified seed script was preserved rather than changed as part
of FS-015. This record predates the calendar/list and Lecturer coordination
extension and does not prove its new acceptance cases. No extension test run is
claimed by this planning artifact.

Pre-extension checkpoint, 2026-07-31:

- Focused backend command including FS-014 calendar regression:
  `131 passed` (exit 0).
- Focused client command: `6` files and `133` tests passed (exit 0).
- This checkpoint records the starting baseline only; it does not claim that
  any extension task or acceptance criterion has passed.

## 2. Start a disposable local validation environment

Use a test database rather than the planner's normal data. From separate
terminals, start the backend and client with their existing development
commands:

```powershell
Set-Location C:\Codex\planner-resource\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

```powershell
Set-Location C:\Codex\planner-resource\client
$env:VITE_API_BASE_URL='http://127.0.0.1:8002'
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the planner at `http://127.0.0.1:5173`. Do not use a real review link or
real lecturer data in an HTTP environment. This direct localhost setup cannot
prove the production gateway boundary.

## 3. Validate the trusted gateway and source-address boundary

Run this section against the production-like HTTPS gateway, not the direct
localhost development servers.

Before testing, record the target environment, gateway configuration or
runbook, trusted gateway peer/CIDR, responsible person or team, and evidence
recorder. Missing ownership or configuration evidence blocks production
release.

1. As an authorized planner, request the planner root and representative link
   overview/issue operations.
2. As an anonymous client, request `/lecturer-review/`, the exact public GET,
   and the exact public feedback POST.
3. Anonymously request `/`, `/health`, API documentation, a representative
   planner API, an unlisted method on a public path, and an extra public
   subpath.
4. Attempt to connect directly to the backend host/port.
5. From one real client address, vary `Forwarded`, `X-Forwarded-For`, and
   `X-Real-IP` while exercising the unusable-link threshold.
6. Repeat from two real client addresses.
7. Inspect the deployed Uvicorn proxy-trust configuration.
8. Send active and ended stored lecturer bearer credentials to representative
   planner calendar, coordination, link-management, lifecycle, publication,
   and schedule-mutation APIs. Repeat with an unrelated 43-character URL-safe
   bearer and with the deployment's authorized planner request shape.

Expected result:

- Authorized planner traffic passes; anonymous planner traffic is rejected at
  the gateway before application data or actions are reached.
- Only `/lecturer-review/`, required static assets, and the exact two public API
  operations are anonymously reachable.
- Direct backend access fails.
- Forged forwarding headers do not change the limiter bucket or evade attempt
  21.
- Two actual client addresses receive independent buckets.
- The gateway peer/CIDR is recorded explicitly, proxy trust is not wildcard,
  and an application restart does not reset an active rejection period.
- Public calls are same-origin HTTPS requests with credentials omitted.
- Stored active and ended lecturer bearer requests to planner APIs are rejected
  before target validation or service execution, expose no planner data, and
  cause no state change. The unrelated bearer is not classified as a lecturer
  credential, and the gateway-authorized planner path remains usable.

Failure of any item blocks production release.

## 4. Validate issue, copy, and restricted workspace

1. Open **Schedule > Lecturer coordination** for a Working Draft revision.
2. Confirm Ready for review is recommended but Draft issuance is enabled
   without another confirmation.
3. Select a lecturer with teaching and exam assignments across multiple
   courses, leave duration at the three-day default, and issue the link.
4. Verify the transient one-time result, manual/private-delivery warning, copy
   success announcement, and clipboard-denial alert.
5. Open the copied URL in a private browser session with no lecturer account.
6. Exercise Week, Day, Month, and List modes and applicable period navigation.
7. Intersect course, cohort, room, study-type, session-type, lifecycle, and
   validation filters when corresponding facet choices exist.
8. Select teaching and exam occurrences from both calendar and list modes and
   resize through wide, constrained, and narrow pane presentations.

Expected result:

- Issue and copy remain possible within 60 seconds and five deliberate
  interactions; 1-, 2-, and 3-day choices produce exact 24-, 48-, and 72-hour
  validity.
- The fragment disappears after bootstrap, the token is sent only in the
  authorization header, and public requests remain relative, same-origin, and
  credential-free.
- The lecturer sees every and only the bound lecturer's current assignments
  across courses. Lecturer identity is fixed labeled context, not a filter.
- The public page uses established calendar/list behavior without loading
  planner navigation, planner API adapters, operational summaries, mutation
  callbacks, other lecturers, contacts, student data, planner notes, or raw
  validation details.
- The shared pane shows only lecturer-safe teaching/exam context and feedback
  actions. Planner edit, delete, create, generation, lifecycle, publication,
  availability, configuration, capacity, and administration controls are
  absent from the DOM.
- Mode, period, active filters, eligible selection, scroll origin, and drafts
  survive mode and responsive presentation changes.
- A complete zero-assignment projection is distinguished from a nonempty
  projection whose records are all hidden by filters.

Attempt issuance for a lecturer with no assignments and for a historical
revision; each attempt creates no link.

## 5. Validate reload-only assignment updates

With a valid link open:

1. Reassign one visible session to another lecturer and add a different
   session for the bound lecturer through the planner.
2. Wait longer than any normal UI interval and change public workspace modes,
   periods, and filters without reloading.
3. Perform a full browser reload or reopen the link.
4. Remove every assignment, reload, then restore an assignment and reload.

Expected result:

- No timer, background request, mode change, filter change, or in-workspace
  refresh action updates the already loaded projection.
- The next full browser reload or reopened link omits the reassigned session
  and includes the new assignment.
- Zero assignments is an authoritative empty schedule, not an ended link;
  restored assignments appear without issuing another link.
- No intermediate or partial public schedule is presented as complete.

## 6. Validate advisory feedback and draft safety

1. Enter nonblank session feedback, then try pane close, another session, and a
   filter that would hide the target. For each trigger, test Cancel and Discard.
2. Confirm responsive pane changes do not prompt and preserve the draft.
3. Submit a revision comment, a session comment, one exam **Not possible**
   item without text, and another impossible item for the same session with
   text.
4. Reopen the original link.

Expected result:

- Cancel retains the draft and context. Discard clears both drafts for the
  target, performs the requested context change, and creates no feedback.
- Every deliberate submission creates a separate immutable item; an ambiguous
  retry with the same client submission identity creates no duplicate.
- Success clears only the submitted draft, announces acceptance, and appends
  the returned item locally without reloading the assignment projection.
- Same-link history is visible after reopen and no feedback changes the
  schedule, publication eligibility, or any lifecycle action.

Boundary checks:

- Blank required comments and 2,001-character text are rejected; 2,000
  characters are accepted; markup-looking text is rendered literally.
- Edit an in-scope session after opening, then submit: the backend associates
  feedback with authoritative current context.
- Reassign the selected session away before submission: the backend rejects
  the stale target, creates no item, clears the unauthorized target and draft,
  and directs the reviewer to reload or reopen. It does not automatically
  reload the projection.
- Automatic authorized-scope loss discards affected drafts, explains the
  removal, and creates no feedback.

## 7. Validate Lecturer coordination

1. Open **Schedule > Lecturer coordination** for the feedback revision.
2. Apply intended-lecturer, course, session-kind, and feedback-kind filters
   individually and in intersections, including **Not possible**.
3. For each filter state, inspect all feedback, comment, impossible-item, and
   distinct-affected-session counters.
4. Clear all filters using only the keyboard, open one current affected
   session, and repeat with partial and unavailable feedback states.

Expected result:

- Items are filtered before regrouping, and every active filter recomputes the
  displayed result and all four counters from exactly the same item set.
- Comment count includes revision and session comment items; optional text on
  an impossible item does not make it a comment. Course/session-kind filters
  exclude revision comments.
- Repeated impossible items count separately, while distinct affected
  sessions count an occurrence once.
- Complete empty scopes may show exact zero; partial or unavailable data never
  presents missing data as definitive zero.
- Link management and history remain outside feedback filters.
- Opening a current session honors the existing unsaved-change guard,
  establishes the correct revision, and selects the exact occurrence.
  Historical, removed, or reassigned items keep captured context without a
  guessed navigation target.
- Clearing filters changes no link, feedback, schedule, or revision data.

## 8. Validate revoke, replace, expiry, and lifecycle end

For each case, retain the old URL and exercise it after the end action:

1. Explicitly revoke an active link.
2. Replace an active link with a new 1-, 2-, or 3-day duration.
3. Reach the exact expiry boundary using the test clock.
4. Publish the bound Working revision as Current Published.
5. Supersede that publication with another revision.
6. Abandon an active Working revision, then restore it.

Expected result:

- Revoke ends access on the next request.
- Replacement leaves exactly one active link for the pair and every earlier
  URL is unusable.
- Access works immediately before expiry and exposes/accepts nothing at or
  after the exact instant.
- First publication does not end the link and displays Published.
- Supersession and abandonment end it permanently.
- Restore does not reactivate the old link.
- Every unusable URL yields the same safe outcome and contact-planner guidance.
- Previously accepted feedback remains visible only in planner revision
  history.

Run the file-backed SQLite concurrency tests for simultaneous replacements,
issue races, revoke versus feedback, reassignment versus feedback, abandon
versus feedback, and supersede versus feedback. Expected result: the operation
that wins the authoritative transaction boundary determines the outcome,
exactly one replacement remains active, and no partial state exists.

## 9. Validate misuse boundaries

Use the injected test clock and automated API suites rather than manual
production traffic:

- unusable-link attempts 20 and 21 inside five minutes, the ten-minute block,
  continuity of the rolling attempts and active block across an application
  restart, and physical source-state row removal by 15 minutes after the last
  relevant attempt;
- valid protected views 120 and 121 inside five minutes and the five-minute
  block;
- feedback submissions 10 and 11 inside one minute and 60 and 61 inside one
  hour;
- release when the applicable rolling window/block ends;
- normal requests below each threshold.

Expected result: exact boundaries match FR-054 through FR-057, rejected requests
create no feedback, expiry is unchanged, unrelated links and lifecycle state
are unchanged, and unusable-source throttling returns the same public
unavailable response.

## 10. Validate secret and privacy surfaces

Use unique canary text for one token and one comment, then inspect:

- database rows and migration output;
- planner overview/list responses;
- public and planner error bodies;
- activity evidence;
- feedback attribution fields;
- application/server logs;
- browser history and storage;
- network request URLs and referrer headers;
- OpenAPI examples and rendered error details.

Expected result:

- The raw secret exists only in the successful issue/replacement response, the
  transient planner success UI/clipboard, the original URL fragment, page
  memory, and public authorization header.
- Only the digest is persisted.
- Comment text exists only in feedback/business displays, never activity
  evidence.
- Public responses carry `no-store` and `no-referrer`; the page is not indexed.
- Public success and error responses consistently carry `no-store`, `no-cache`,
  `no-referrer`, and `noindex, nofollow`.
- Malformed, unknown, expired, revoked, replaced, abandoned, and superseded
  cases have identical status/body/header shapes and expose zero protected
  fields.

## 11. Validate reference-scale response times

Use a scope containing 100 teaching/exam sessions and 200 retained feedback
items. After three unrecorded warm-up operations, record exactly 20 valid review
openings and 20 feedback submissions in the production-like environment.
Measure each opening from navigation until either the complete usable schedule
or a safe actionable state is visible, and each submission from activation
until the accepted or rejected result is visible. Record which opening outcome
was displayed; only a complete usable schedule counts toward the three-second
target.

Expected result:

- at least 19 of 20 review openings display the complete usable schedule within
  three seconds;
- all 20 review openings display either the complete usable schedule or a safe
  actionable state within ten seconds;
- at least 19 of 20 feedback submissions complete within two seconds;
- all 20 feedback submissions complete within five seconds; and
- no submission creates duplicate feedback.

Record the environment and every individual measurement with the release
evidence.

### Repeatable backend guard

Run the automated reference-scale guard with timing output:

```powershell
Set-Location C:\Codex\planner-resource\backend
python -m pytest tests/performance/test_lecturer_review_performance.py -q -s
```

The guard creates exactly 100 scoped teaching/exam sessions and 200 retained
feedback items in file-backed SQLite. It performs three unrecorded warm-ups,
then measures exactly 20 openings through the in-process FastAPI TestClient. It
separately performs three unrecorded submission warm-ups, then measures exactly
20 service submissions including the transaction commit. It asserts the
19-of-20 target, the 20-of-20 maximum, unique created IDs, and the expected
final feedback count.

This is a repeatable backend regression guard. Its opening measurement starts
immediately before the in-process HTTP request and ends after the complete JSON
response is returned. Its submission measurement starts before the service
call and ends after the SQLite commit. It includes no browser navigation,
rendering, deployed gateway, network, or result-announcement time and therefore
does **not** constitute SC-010/SC-011 end-to-end acceptance.

Implemented-baseline automated guard run on 2026-07-28:

- Environment: Windows 11 `10.0.22631`, Python `3.12.8`, SQLAlchemy `2.0.34`,
  SQLite `3.51.2`, pytest with FastAPI TestClient, file-backed SQLite, no
  network, no browser.
- Command result: `1 passed, 1 warning in 3.65s`.
- Complete usable API opening seconds, trials 01–20:
  `0.020878, 0.019824, 0.106736, 0.023306, 0.024657, 0.025610, 0.027628,
  0.025446, 0.034590, 0.036351, 0.027051, 0.021807, 0.024357, 0.024386,
  0.020982, 0.022351, 0.024242, 0.023483, 0.024283, 0.021665`.
- Created transactional service submission seconds, trials 01–20:
  `0.015644, 0.012233, 0.010963, 0.012403, 0.014900, 0.012442, 0.010977,
  0.010942, 0.013076, 0.010730, 0.011154, 0.011477, 0.010884, 0.011473,
  0.012633, 0.014093, 0.012857, 0.011160, 0.011820, 0.014584`.
- Guard outcome: all 20 API responses contained the complete 100-session
  schedule and all 200 retained items within three seconds and ten seconds;
  all 20 service submissions committed a unique feedback item within two
  seconds and five seconds. No duplicate feedback ID was created.

### Implemented-baseline local browser end-to-end performance evidence

Recorded on 2026-07-28 with the same 100-session, 200-retained-feedback
file-backed SQLite fixture. This predates the shared-workspace extension and
must be repeated after implementation:

- Environment: Windows 11 `10.0.22631`, Codex in-app Chromium browser, Vite
  development server with a same-origin `/api` proxy, FastAPI/Uvicorn on
  loopback, and file-backed SQLite. The run used local HTTP and did not traverse
  a production gateway or external network.
- Opening method: three unrecorded full-document warm-ups, followed by exactly
  20 full-document navigations. Each timer started immediately before browser
  navigation and stopped when the unique `Assigned schedule` heading was
  visibly available with the complete schedule.
- Submission method: three unrecorded warm-ups, followed by exactly 20 distinct
  revision-comment submissions. Each timer started when the submit button was
  activated and stopped when the browser exposed either `Feedback accepted.`
  or an alert rejection. The disposable fixture's activity-event rate window
  was cleared between measurement batches so 20 independent timings could be
  collected without changing the production limit. The real rate limit was
  still exercised: trial 08 produced the expected visible rejection.
- Persistence check: 19 accepted measured comments produced 19 rows, 19
  distinct comments, and 19 distinct client submission IDs. The rejected
  comment produced no row; no duplicate was persisted.

| Trial | Opening outcome | Opening seconds | Submission outcome | Submission seconds | Duplicate |
|---:|---|---:|---|---:|---|
| 01 | Complete schedule | 0.233 | Accepted | 0.342 | No |
| 02 | Complete schedule | 0.266 | Accepted | 0.350 | No |
| 03 | Complete schedule | 0.227 | Accepted | 0.358 | No |
| 04 | Complete schedule | 0.235 | Accepted | 0.366 | No |
| 05 | Complete schedule | 0.255 | Accepted | 0.346 | No |
| 06 | Complete schedule | 0.230 | Accepted | 0.358 | No |
| 07 | Complete schedule | 0.222 | Accepted | 0.365 | No |
| 08 | Complete schedule | 0.260 | Rejected by rate limit | 0.369 | No |
| 09 | Complete schedule | 0.300 | Accepted | 0.340 | No |
| 10 | Complete schedule | 0.228 | Accepted | 0.350 | No |
| 11 | Complete schedule | 0.296 | Accepted | 0.358 | No |
| 12 | Complete schedule | 0.268 | Accepted | 0.380 | No |
| 13 | Complete schedule | 0.238 | Accepted | 0.365 | No |
| 14 | Complete schedule | 0.272 | Accepted | 0.344 | No |
| 15 | Complete schedule | 0.220 | Accepted | 0.345 | No |
| 16 | Complete schedule | 0.237 | Accepted | 0.345 | No |
| 17 | Complete schedule | 0.273 | Accepted | 0.361 | No |
| 18 | Complete schedule | 0.237 | Accepted | 0.353 | No |
| 19 | Complete schedule | 0.232 | Accepted | 0.365 | No |
| 20 | Complete schedule | 0.278 | Accepted | 0.371 | No |

Outcome: 20 of 20 complete schedule openings were within three seconds and
within ten seconds. All 20 submissions showed an accepted or rejected browser
result within two seconds and within five seconds, with no duplicates.

### Deployment end-to-end acceptance protocol

The deployment acceptance run remains mandatory and pending until a
production-like target is identified. Record the release/commit, deployment
URL, gateway and application topology, database engine/location, seeded row
counts, browser/version, client device/OS, client-to-gateway network path,
observer, and UTC start time before measuring.

1. Confirm the selected lecturer's valid link resolves to exactly 100 scoped
   teaching/exam sessions and that 200 feedback items are retained.
2. Perform three opening warm-ups without recording them. Then perform exactly
   20 valid openings. Start each timer at browser navigation and stop only when
   either the complete usable schedule or a safe actionable state is visibly
   rendered. Record the outcome; only complete usable schedules count toward
   the three-second target.
3. Perform three submission warm-ups without recording them. Then perform
   exactly 20 distinct feedback submissions. Start each timer when the user
   activates submit and stop when an accepted or rejected result is visibly
   rendered. Verify persisted feedback identities/counts so retries or UI
   behavior did not create duplicates.
4. Apply the 19-of-20 and 20-of-20 thresholds above to the recorded browser
   results and retain screenshots/log correlation without recording a bearer
   secret.

Deployment record status on 2026-07-28: **not executed**. Target environment,
gateway, browser, network path, and evidence recorder are not yet identified;
there are no browser end-to-end measurements to report.

| Trial | Opening outcome | Opening seconds | Submission outcome | Submission seconds | Duplicate |
|---:|---|---:|---|---:|---|
| 01 | Pending | — | Pending | — | Pending |
| 02 | Pending | — | Pending | — | Pending |
| 03 | Pending | — | Pending | — | Pending |
| 04 | Pending | — | Pending | — | Pending |
| 05 | Pending | — | Pending | — | Pending |
| 06 | Pending | — | Pending | — | Pending |
| 07 | Pending | — | Pending | — | Pending |
| 08 | Pending | — | Pending | — | Pending |
| 09 | Pending | — | Pending | — | Pending |
| 10 | Pending | — | Pending | — | Pending |
| 11 | Pending | — | Pending | — | Pending |
| 12 | Pending | — | Pending | — | Pending |
| 13 | Pending | — | Pending | — | Pending |
| 14 | Pending | — | Pending | — | Pending |
| 15 | Pending | — | Pending | — | Pending |
| 16 | Pending | — | Pending | — | Pending |
| 17 | Pending | — | Pending | — | Pending |
| 18 | Pending | — | Pending | — | Pending |
| 19 | Pending | — | Pending | — | Pending |
| 20 | Pending | — | Pending | — | Pending |

## 12. Accessibility, responsive, and usability evidence

Manually validate at 320 CSS pixels and 200% browser text zoom:

- fixed lecturer context, mode and period controls, filters, calendar/list
  records, session details, drafts, feedback forms, status, and pane close
  controls wrap without horizontal page scroll;
- keyboard-only issue/copy/revoke/replace/filter/mode/selection/pane/feedback
  paths, with no in-workspace refresh control;
- logical focus after filter changes, discard/cancel, submission, errors,
  responsive pane transitions, close, and exact-session navigation;
- screen-reader announcements for identity disclaimer, revision/state, expiry,
  result scope, count completeness, copy result, submission result,
  automatic scope loss, unavailable, and throttled states;
- lifecycle, validation, feedback kind, count completeness, and
  flag/comment distinction without color.

Finally conduct SC-006, SC-007, and SC-016 with at least 10 representative
lecturers or designated acceptance reviewers. Record participant count,
completion times, task outcomes, filter/session-detail completion, and
understanding answers. These three criteria remain pending until the real
moderated review is complete.

## 13. Extension implementation evidence (2026-07-31)

The FS-015 shared-workspace extension was implemented and exercised locally
against the final source state.

Automated backend evidence:

- Focused FS-015, concurrency, API, bearer-boundary, performance, and migration
  suite: `139 passed, 301 warnings in 21.42s`, exit code 0.
- Focused FS-013 lifecycle and publication regression suite:
  `26 passed, 27 warnings in 8.28s`, exit code 0.
- Full backend suite: `466 passed, 1158 warnings in 81.46s`, exit code 0.
- Reference-scale guard: `1 passed, 1 warning in 3.74s`, exit code 0. All
  20 complete 100-session/200-feedback openings took `0.033130` to `0.050943`
  seconds; all 20 unique committed submissions took `0.009495` to `0.020446`
  seconds.
- The Windows Python environment emits a post-test diagnostic from optional
  NumPy 1.x-compiled pyarrow/numexpr/bottleneck modules loaded through
  pandas/OR-Tools. It occurs after pytest reports completion and does not
  change the recorded exit code 0. This environment issue should be repaired
  independently; it did not suppress or skip the passing assertions.

Automated client evidence:

- Focused transport, shared workspace/list/pane, draft dialog, Lecturer
  coordination, Schedule navigation, public page, and bootstrap suite:
  `11 files passed`, `170 tests passed`, exit code 0.
- Full client suite: `46 files passed`, `314 tests passed`, exit code 0.
- ESLint: passed with no findings.
- TypeScript plus Vite production build: passed; 72 modules transformed.

The automated security, privacy, and accessibility checks cover:

- exact public operation allowlisting and stored active/ended lecturer-bearer
  denial on non-public APIs;
- strict safe DTO keys and reference integrity, raw-secret/contact/planner-note/
  other-lecturer/raw-finding privacy canaries, literal feedback text, generic
  terminal failures, and non-cacheable public responses;
- lecturer-only assignment projection, authoritative empty scope, reload-only
  assignment updates, local feedback-history append, stale-scope clearing, and
  no planner controls in the restricted DOM;
- Week/Day/Month/List operation, applicable intersecting filters, fixed
  lecturer context, teaching/exam selection, long labels at 320 CSS pixels,
  live regions, keyboard activation, non-color semantics, focus containment,
  inert obscured content, and focus restoration;
- item-first Lecturer coordination filters, identical-scope counters, repeated
  impossible items, partial/unavailable qualification, exact current-session
  navigation, historical context retention, and non-blocking publication.

Manual/release evidence status:

- **Pending — release blocking where required by the specification**:
  production HTTPS and gateway configuration, anonymous/direct-backend denial,
  trusted-peer/CIDR and forwarding-header overwrite, deployed restart-safe
  misuse state, and deployed 20-opening/20-submission browser timings. No
  production-like target or gateway evidence owner was supplied for this run.
- **Pending**: physical 200% zoom inspection, real screen-reader pass, and
  cross-browser/device responsive inspection. Automated DOM, focus, semantic,
  and 320-CSS-pixel checks passed but do not replace these manual protocols.
- **Pending**: the SC-006, SC-007, and SC-016 moderated protocols with at least
  ten representative lecturers or designated reviewers. No participants were
  available in this implementation run, so no usability success is claimed.
- **Pending**: manual canary inspection of production gateway/application logs,
  browser history/storage, referrers, and deployed observability surfaces.
  Automated transport, response, rendered-DOM, and persistence canaries passed.

Final consistency audit:

- `spec.md`, `plan.md`, `data-model.md`, `research.md`, the UI and gateway
  contracts, and the six-operation OpenAPI contract agree on one lecturer and
  one revision, exactly two public operations, reload-only projection updates,
  component reuse, advisory immutable feedback, and the single Lecturer
  coordination destination.
- The OpenAPI YAML parses as 3.1.0 with 6 paths and 26 schemas.
- No extension migration, durable entity, public route, generic Action Center,
  account, email integration, export, availability workflow, schedule mutation,
  or publication gate was introduced.
- `git diff --check` passed; only repository line-ending notices were emitted.
- No `.specify/extensions.yml` post-command hook configuration exists.

## Completion evidence

Before commit, retain:

- focused and full automated command results;
- migration clean-create and `0008 → 0009` upgrade results;
- concurrency and exact-boundary results;
- the production-like environment and all 20 review-opening and 20
  feedback-submission timing measurements;
- privacy canary inspection;
- restricted-workspace reuse, planner-control DOM-absence, reload-only,
  draft-guard, keyboard, zoom, and screen-reader notes;
- production HTTPS, exact gateway allowlist, planner rejection, direct-backend
  denial, lecturer-bearer denial on representative planner APIs, trusted
  peer/CIDR, forwarding-header overwrite, same-origin public requests,
  identified gateway owner/configuration/runbook/evidence recorder, and
  restart-safe unusable-link rejection confirmation;
- moderated-review evidence when available.
