# I-014 Validation Guide

This is the acceptance guide. Actual implementation results and limitations are in
[validation.md](validation.md); automated gates pass and T044/T045/T049 remain open.
Exact data/interaction contracts are in [data-model.md](data-model.md) and
[contracts/interfaces.md](contracts/interfaces.md).

## Prerequisites and setup

Use an isolated disposable database and a named planner account. Retain existing locks/dependencies; record Git revision, Python/Node versions and browser. Existing deployment uses Python 3.13 and Node 26; use compatible installed runtimes. Do not seed or migrate the working planner database for acceptance fixtures.

From repository root, if environments are missing:

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm --prefix client ci
```

Use the existing environment if present rather than recreating it. Start a backend against an explicitly disposable SQLite path:

```powershell
$env:DATABASE_URL = 'sqlite:///C:/Codex/planner-resource/tmp/i014-acceptance.db'
Push-Location backend
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use another terminal for `npm --prefix client run dev`. Follow existing frontend API configuration and planner bootstrap/login in `backend/README.md`; keep secrets out of evidence. Fixture setup can use existing authenticated administration/manual-session flows or implementation test fixtures. No fixture creation helper is claimed to exist in this plan. Before seeding, verify the explicit database path is disposable.

## Automated verification

Write intended failing tests before production. Run the commands in [plan.md](plan.md#verification-plan), first targeted then full suites/build/lint. New `calendarTimeGridLayout`, `CalendarTimeGrid` and `CalendarMonthGrid` tests are to be created during implementation, not available today. Record failures, fixes and final exit codes; unavailable checks remain pending.

## Reference fixture and hourly comparison (US1; SC-001)

Create a semester covering June 2027, cohort/calendar A with Saturday 08:00–16:00 and Höber, Angelika assigned to a saved manual session on 26.06.2027, 12:15–17:20. Retain the existing non-blocking window finding through existing manual-save rules. Set other fixture constraints so they do not obscure this window example.

1. Open Day for 26.06.2027. Confirm 12:15/17:20 placement and full block. At the initial 72 px/hour scale its 305-minute interval occupies 366 CSS pixels; start is 882 px from midnight before container offsets. The 16:00 boundary is 1,152 px from midnight and outside portion is 96 px (80 minutes). Measure the actual block border box relative to the canvas; allow only rendering precision error, not an hour/minute rounding rule.
2. Confirm textual 16:00–17:20 / 1 hour 20 minutes with date, lecturer/session and calendar. Open existing detail, then return without resetting context.
3. Repeat in Week, including Saturday; scroll to 00:00 and 24:00. Compare equal-duration blocks across dates/groups.
4. Add separate in-window 09:00–10:30 and sessions surrounding an empty 10:00–12:00 gap using distinct fixture dates/resources as needed. Confirm exact duration, empty permitted space and no promise of free resources.
5. Inspect wholly outside, exact-boundary, short/non-hour and three concurrent/identical-interval sessions. Each block remains reachable/selectable with accurate geometry; adjacent intervals reuse lanes without becoming conflicts.

## Correct context (US2; SC-002)

- Add dated intensive Monday 09:00–12:00 and ordinary weekly hours on that weekday in a dedicated fixture. Confirm backend `window_applies` precedence is reflected exactly, and next Monday does not inherit the dated opportunity. Marker-only refresh changes label/token without inventing validity.
- Give calendar B different hours (10:00–18:00); show A/B together. An A session at 16:30 remains outside A despite B. Repeat with equal calendar labels but different IDs and with two courses having differing effective profiles.
- Inspect multiple overlapping/adjoining source windows; source boundaries remain readable and do not imply permission to stitch one session across them.
- Include a zero-session revision course, a selected calendar with no filtered sessions, no known calendar, no allowed hours and unknown context. Verify explicit states instead of an invented default.
- Compare Working and Current Published, including legacy capture without profile. Published uses captured source facts only; missing historical context remains unknown and existing current validation basis remains unchanged.
- Delay/fail context refresh or provide malformed section data. Sessions/List remain accessible, retry/last-known state is explicit, and old/new revisions are never mixed. Revisit after refresh and retain unsaved pane input.

## Month and established workflows (US3; SC-003/006)

Use dates with 0, 1, 5 and 20 filtered sessions. Month contains complete weeks and empty days; three initial entries give hidden counts 2 and 17 respectively. Expansion exposes every entry chronologically. Put all outside-window sessions in overflow: affected-entry count/cue remains visible before expansion. Partial permitted days disclose actual hours per calendar rather than all-day availability.

Activate date -> Day and entry -> existing pane. Test previous/next, Today, direct date and mode changes; compare matching session identities with List. Open existing edit/save/cancel and immutable Published detail. Existing unsaved-input confirmation and validation behavior must remain intact. Snapshot saved session/window/availability/revision data before view-only navigation and after: zero changes. Do not count authorized correction writes as view-only changes.

## Accessibility and observed comprehension (US4; SC-004/005)

Complete all mode/date/filter, scroll, window disclosure, overlap, overflow, pane and correction-entry actions with keyboard only. Check visible focus, logical reading order and return after close/disappearing session. With actual assistive technology, identify date/calendar/session/window provenance and findings without relying on spatial position. Record AT/browser versions and observed announcements.

Inspect real browser layout at 320 CSS pixels and genuine 200% text enlargement, including dense overlap and twenty-entry Month. Verify all facts/actions, calendar identity and scrolling remain reachable. Remove color cues and confirm labels/patterns/text still communicate permission and overrun. Capture wide/narrow/zoom screenshots and contrast observations. jsdom cannot establish these outcomes alone.

Ask five representative planners to identify the reference overrun/duration, an in-window session, an empty permitted gap and the applicable calendar, without first opening a warning list. At least four must succeed within 30 seconds per case. Record anonymized times/answers; do not substitute agent judgment for the five-human observation.

## Evidence and completion boundary

Command results, fixture facts, response examples, data fingerprints, geometry measurements and browser observations are recorded in `validation.md`. Missing observations remain explicit; this feature does not close predecessor acceptance obligations.

Implementation update (2026-11-15): these artifacts now exist in `validation.md`
and `verification/`. The full backend/client suites, focused checks, performance,
build and lint pass. The built application was also exercised against the isolated
database for Month/Day/List, modal source context, edit/cancel, unsaved protection,
save and refresh. Explicit fixture-setup writes and authorized correction saves
are excluded from view-only zero-write claims. Remaining acceptance is T044
(including actual AT, genuine 200% text enlargement and removed-color observation),
T045 (five representative planners) and the resulting T049 reconciliation.
