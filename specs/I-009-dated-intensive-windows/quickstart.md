# I-009 Validation Guide

Future implementation guide, not evidence that software/tests are complete. Use a disposable DB containing representative weekly records and saved references; never seed/migrate the user's working DB for these checks. Exact rules are in [data-model.md](data-model.md) and [contracts/interfaces.md](contracts/interfaces.md).

## Prerequisites and commands

After plan/task approval and human-started Goal 3, record tested branch/revision/diff and environment. Use Python 3.12/backend virtualenv, Node 24 and existing locks. If absent, install with `backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt` and `npm --prefix client ci` from root, without upgrading locks. If virtualenv itself is absent, create it using Python 3.12 first.

From `backend/`:

```powershell
.venv/Scripts/python.exe -m pytest tests/db/test_migrations.py tests/services/test_dated_intensive_windows.py tests/services/test_intensive_objectives.py
.venv/Scripts/python.exe -m pytest tests/api/test_academic_catalog.py tests/api/test_dated_intensive_windows.py tests/api/test_conflict_aware_generation.py tests/api/test_optimization_operations.py
.venv/Scripts/python.exe -m pytest tests
```

From `client/`:

```powershell
npm test
npx tsc -b
npm run build
npm run lint
```

Run existing authenticated backend with `backend/README.md` environment setup against disposable DB and `npm --prefix client run dev` for Vite. Follow existing planner authentication/CSRF, not bypasses. Capture intended failing tests before production and final passing outcomes. Missing essential checks are reported as missing.

## US1: Specific dates

Use Friday/Saturday ordinary windows and otherwise eligible courses. Add Monday `09.11.2026`, 09:00–12:00 within course period. Save/reload/edit/delete and generate: only the exact date/form gains permission, never adjacent Monday/same date next year/other form. Verify six independent Mon–Sat entries, explicit Sunday and out-of-period dates; records permit, never compel teaching. Exercise invalid/leap dates, interval order, inactive form, marker-only duplicate, cross-form equality, overlap/adjacency, stale writes and protected deletion. Before closing US1, exercise direct constraint response, current Calendar/List/detail reconstruction, new lifecycle capture and derived read-only panel: kind/date/marker survive end-to-end and full German dates render. Old captures remain byte-for-byte unchanged and render as captured weekly values. Test mixed weekly/dated exam windows and dated-only forms: ordinary weekly exam proposals/eligibility remain unchanged, dated rows add no weekly start and never cause nullable-weekday sorting failures. Run `.venv/Scripts/python.exe -m pytest tests/services/test_exam_scheduling.py tests/services/test_exam_optimization.py tests/api/test_exam_scheduling.py` and `npm test -- src/components/DraftSchedulePanel.test.tsx` in their respective working directories. Upgrade disposable predecessor and inspect preserved weekly IDs/references/revisions/activity, equivalent fresh schema and untouched historical captures.

## US2: Exact priorities/accounting

Use independently enumerable `backend/tests/services/test_intensive_objectives.py` fixtures. Compare 12 total/4 intensive with 10/10, equal total with 4 vs 8 intensive, mixed same-cohort days scoring 2 vs isolated scoring 0. Include unrelated cohort, fixed teaching vs exam, cross-date ties, same LV over multiple days, one-LV fallback and unchanged unmarked deterministic output. Both higher-priority sacrifice attempts must lose.

Test a wider ordinary window needing an interior marker-aligned start and tightly packed boundary cases. Verify union/no-stitching and source independence. Teaching 09:00–09:45 plus 09:55–10:40 intersecting marker 09:30–10:10 contributes 30 instructional minutes = exactly 2/3 LE, excluding break. Ninety instructional minutes under overlapping markers is 2 LE once. Holidays/resources/capacity/exams/periods/session bounds/breaks/one LV per date remain hard. Installed proof flow must truthfully represent stage interruption/conditional evidence and retain its explicit acceptance rules.

## US3: Current context and saved work

Keep saved manual Monday teaching outside weekly windows. Add/shorten/archive/remove dated opportunity and inspect Calendar/List/detail; alerts change, saved facts do not. Marker-only change stales previews without new validity warning. Fail catalog reload/options/each alert/detail refresh independently after successful write: every affected view is non-current with retry. Delay old response beyond newer mutation; it cannot restore currency. Revisit views; preserve filters, unrelated selections and unsaved input. Inspect publication/history snapshots unchanged.

Prepare candidates then change each relevant date/hours/form/activity/marker before submission/acceptance. Stale submission saves nothing. Cancel/reject/fail/retry/interrupt replacement: prior state or one complete explicitly accepted state, never partial/repeated commit. Test I-004 first-plan direct save and conscious lower coverage. Test core synchronous path without I-006/I-007/I-008 services and installed worker/proof path separately.

## US4: Independent copying

Copy weekly and marked dated entries; inspect prefilled values/focus, cancel one, explicitly save one. Zero writes on open/cancel, one independent record on success. Duplicate feedback retains input; change date/form/hours/marker. Change/delete source while editor open; save validates current relationships/identity without synchronization. Later source/copy edits/deletion affect zero peers/sessions. Double in-flight submit cannot create two records.

## US5: Accessible operation and comprehension

Complete create/copy/edit/delete-confirm/cancel by keyboard only, including invalid saves. Check default focus, first invalid field, return/containment, visible focus, all error associations, German full dates, marker and outcome announcements. Record real browser/assistive-technology versions and observations. Separately inspect 320 CSS px and 200% text enlargement for readable/reachable labels, dates, markers, errors, actions and result facts. jsdom assertions supplement these checks.

Ask five representative planners or acceptance reviewers, unaided, to add a marked date, copy to another form, cancel an extra copy and explain independence/non-recurrence. At least four finish within five minutes; all five identify total LE priority and permitted single-LV days from facts. Record anonymized times/explanations/results; no current pass is claimed.

## SC-008 browser timing

Use documented normal acceptance environment, 100 mixed windows, 20 courses, 100 current teaching sessions. Instrument save acknowledgement through refreshed current options/Calendar/List/detail rendering in each affected mounted view. Run twenty sequential changes including marker/date/hours/activity. Each affected view must be current within two seconds; record every latency/environment/max/error and unchanged session fingerprints. Fake timers/API-only timing cannot establish this outcome. Force refresh failures and verify non-current labels/retry. Run inherited optimizer performance suites too.

## Evidence

During implementation record actual command outcomes, code/artifact identity, manual/browser/user results and limitations in `specs/I-009-dated-intensive-windows/validation.md`. This file does not exist until implementation evidence is collected. Missing acceptance evidence or failed regressions blocks implementation completion/delivery. Built-in requirements checklist remains specification-quality evidence; it is not software verification. User manual creation stays in Goal 5.


## Actual implementation validation environment (2026-11-06)

See validation.md and verification/browser-*-cycle1.* for actual results. Existing locked dependencies were retained (16direct client packages match package-lock.json). PATH Node27alpha was not used for acceptance; commands used existing Node24.22.1 at C:/Users/b50578/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe with node_modules/vitest/vitest.mjs run, node_modules/typescript/bin/tsc -b, node_modules/vite/bin/vite.js build and node_modules/eslint/bin/eslint.js . from client. Backend uses .venv/Scripts/python.exe3.12.8. Windows sandbox helper/temp restrictions required elevated test reruns; failed restricted attempts are not passes.

Real Edge browser checks used a newly seeded disposable database and port8765, production frontend,100mixedwindows/20courses/100sessions.20refresh measurements are aggregate current-render upper bounds for all affected mounted views, not fake timers/API-only durations. Actual AT, genuine200% enlargement and five-human trials remain required; user explicitly reported them unavailable. This does not change the acceptance requirements or authorize Goal4/delivery.

Cycle2 actual320CSSpx current/generated/provisional/saved result checks and screenshot observations are in verification/browser-result-layout.json and validation.md. Genuine200%/actual AT/five-human trials remain unavailable; acceptance is incomplete.
