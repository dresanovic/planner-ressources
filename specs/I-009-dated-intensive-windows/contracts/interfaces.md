# I-009 Shared Interface Contracts

Normative backend/TypeScript/UI design. Wire dates use ISO `YYYY-MM-DD`; entry/display uses `DD.MM.YYYY` with four-digit year, times use the existing 24-hour convention. No new generator, copy endpoint or acceptance authority.

## Catalog: US1 and US4

Retain `GET/POST /api/academic/study-types/{studyTypeId}/time-windows`, `GET/PATCH /api/academic/time-windows/{id}`, existing usage/archive/reactivate and DELETE routes. Create returns 201/one record, update/lifecycle retain existing response conventions, DELETE returns 204. Create owner comes from route; PATCH additionally accepts studyTypeId to change exactly one active owner with record identity preserved.

| Input shape | Required | Forbidden |
| --- | --- | --- |
| weekly | kind=weekly, weekday 0–6, startTime/endTime, sortOrder | non-null date; true isIntensive |
| dated | kind=dated, full date, startTime/endTime, sortOrder; isIntensive defaults false | non-null weekday |

Response adds `kind`, `date` (nullable), nullable `weekday`, `isIntensive`, `overlapNotice: string|null` to existing id/studyTypeId/times/sortOrder/isActive/revision/availability/usage. PATCH sends full scheduling shape, studyTypeId and expectedRevision; kind must match stored kind. Legacy weekly POST omitting kind/date/marker means weekly/false; legacy weekly PATCH omitting them retains stored weekly shape and cannot reinterpret a dated record. Deploy backend/client together and update every nullable-weekday consumer. Old captured snapshots without discriminator remain captured weekly values without rewriting them.

Create/edit/reactivate requires active form and current field validation. Duplicate identity is same form/kind and weekday-or-full-date/start/end, ignoring activity/marker. Cross-form/kind equality and partial overlaps are allowed. Lifecycle/deletion still uses expectedRevision and current usage checks; blockers retain type/count/prerequisiteAction. No ancestry blocker or cascade into sessions/peers.

Errors use existing `{errors:[{code,message,field,meta}]}`: invalid fields 422, duplicate/revision/protected/lifecycle conflicts existing 409 conventions, missing record 404. Aggregate detected errors in German with wire field names; discriminator/date/Boolean/type parsing errors must use the actionable envelope rather than raw English framework errors. Catch DB uniqueness/stale races with rollback and retained recoverable input. `overlapNotice` on GET/mutation is informative German text for positive same-form occurrence overlap, excluding self; it says no extra capacity is created. Exact endpoint adjacency is not overlap. No catalog mutation changes any session.

## Planning, permission and refresh: US1 and US3

Constraint maintenance GET/PUT/DELETE may proceed when `MISSING_ACTIVE_TIME_WINDOW` is the only availability blocker, so a saved period can be inspected, broadened or reset. Other eligibility, lifecycle, revision and semester guards remain binding. Generation continues to reject unusable periods. The focused editor offers explicit recovery inspection without making that request a prerequisite for other eligible generation; successful maintenance refreshes availability.

Current draft/calendar session and window clocks retain `HH:MM` for minute-aligned values and otherwise carry ISO `HH:MM:SS` with up to six fractional digits. Calendar validation and session editing preserve this precision. Precise teaching times are displayed in editable text fields with format guidance; unchanged or resource-only edits must round-trip exact times. Changing LE derives the end while retaining the start's seconds/fraction. Historical stored snapshots are not rewritten.

Planning-options, course derived read-only window responses, prepared generation windows and client types carry kind/date/marker plus existing source identity. Extend `schemas/planning_options.py`, `schemas/draft_schedule.py`, `schemas/conflict_aware_generation.py` and corresponding client types together. Direct consumers/producers include `api/draft_schedule.py` constraint serialization, `services/calendar_workspace.py` current constraintProfile serialization and reconstruction, `services/schedule_lifecycle.py` current window loading/new captured profiles and `client/src/components/DraftSchedulePanel.tsx` read-only rendering. New captures include discriminator/date/marker; missing fields in old captures mean captured weekly/false, without rewriting existing revisions. The derived panel labels weekly/dated and renders full German dates and dated marker rather than nullable-weekday indexing. Course availability recognizes a usable occurrence inside effective period with minimum elapsed duration, including dated-only cases, while precise hard resource/date/exam checks remain. Never convert dated records to recurring weekdays or invent fallback opportunities.

Shared applicability/whole-session containment is used for generation and current validation: same active form/record, exact date or weekly weekday, one containing record including breaks, narrower explicit restrictions additionally binding. Preserve manual warning severity and immutable historical/publication captures. Existing exam automatic proposals and active-start eligibility continue to consume active weekly windows only: mixed dated rows must not enter weekday sorting and a dated-only form supplies no weekly exam start. This is compatibility maintenance, not new exam-window policy; manual exam behavior stays unchanged.

Successful write acknowledgement immediately advances catalogRevision/invalidation even if later catalog reload fails. Affected mounted options, derived windows, Calendar/List/detail are non-current until refreshed for that revision. Refresh failure shows German unavailable/outdated status plus retry; old findings cannot appear authoritative. Prevent out-of-order older responses restoring currency. Preserve filters, unrelated selections and editor values. Revisited current views load current context. Marker-only changes stale results without adding window violations.

## Generation and comparison facts: US2, US3 and US5

Keep current unified prepare/generate and installed operation/candidate/accept routes and guards. Add `intensiveFacts` to generated results and separately to each current/generated comparison side when applicable markers exist:

| Field | Meaning |
| --- | --- |
| totalUnits | Existing selected-course scheduled LE |
| intensiveLe | `{numerator: integer selected instructional microseconds, denominator: 2700000000}`; exact rational |
| dailyVariety | Integer sum of per-cohort/date max(0,K−1) |
| cohortDates | Stable date/cohort-sorted array `{cohortId,date,distinctCourseIds,distinctLvCount,varietyContribution}`; unique sorted IDs include qualifying fixed teaching, count equals ID length, contribution max(0,count−1) |
| preparedSnapshotToken, candidateFingerprint | Existing problem/arrangement identity; current side uses its existing current snapshot identity rather than generated fingerprint |

Both sides use the same prepared context/fixed teaching. Fixed-only qualifying pairs are included as constants. Recompute actual current instructional intersections; never reuse generated facts for current side or add fixed coverage to selected totals. UI may format rational LE but never change comparisons through rounding. Explain German priority (total LE, intensive LE, variety), permitted single-LV days and lack of placement guarantee. Show counts per cohort/date and distinguish sides. No markers preserves existing flow, preference order, deterministic result and acceptance rules.

Installed proof support inserts `intensive_teaching_time` (max, integer microseconds) then `daily_variety` (max, integer points) immediately after total_units. Keep remaining keys/directions/order. Extend key/direction validators, serialization, progress/checkpoints, comparison reproduction and final acceptance checks together. Display intensive objective as LE using denominator, never label raw microseconds LE. Preserve proven/unfinished/not_attempted/conditional and condition values for all earlier fixed objectives; later-stage proof cannot establish full lexicographic proof while earlier evidence is unproven. Checkpoints/facts describe actual hard-valid arrangements. Coverage alone proves no preference optimum.

Detached inputs add window discriminator/date/marker and fixed teaching's units/form/marked context; no ORM/session crosses spawn boundary. Fingerprint and revalidate kind/date/weekday/hours/form/activity/marker/revision, including relevant fixed marker facts, before submission/final atomic application. Stale results use existing rejection and change no saved planning state. Preserve operation-wide explicit acceptance, permitted lower-coverage decisions, first-plan direct-save policy, rollback and at-most-once retry after interruption. Extend installed I-006 proof/operations, but core scoring must work through existing I-003/I-004 synchronous path without introducing I-006/I-007/I-008 services.

## List/editor accessibility: US1, US4 and US5

Create focuses kind; edit locks kind and focuses first editable field; copy labels an unsaved new entry and focuses Studienform. Snapshot kind/form/date-or-weekday/hours/marker/sortOrder once; no source relation/ID/revision is POSTed. Source changes do not synchronize. Explicit save creates one record; disable duplicate in-flight submission. Invalid save retains input, associates all errors and focuses first invalid field. Cancel/dismiss writes nothing and returns focus to origin or logical list location. Preserve existing modal focus containment.

Weekly group first, Monday–Sunday/start/end/form/stable existing order; dated group by full date/start/end/form/stable existing order. Display form, hours, explicit kind/full German date and dated marker in list/editor. New dated marker defaults off; weekly has no marker control. Required actions/confirmation/errors/outcomes are keyboard operable, labelled, visibly focused and announced, without color-only facts. Required controls/result facts stay reachable at 320 CSS px and 200% text enlargement.
