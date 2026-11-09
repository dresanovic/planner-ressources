# Teaching Strategy Contract: I-011

## Policy and endpoints

Policy permits only defaultSeconds, ceilingSeconds, activeAlgorithm, with exact constraints in [data-model.md](../data-model.md). Normal path independent of cwd; explicit TEACHING_OPTIMIZATION_POLICY_FILE wins. Missing/unreadable/malformed file returns 503 OPTIMIZATION_CONFIGURATION_INVALID with actionable German location/provision guidance, no file contents. Effective pre-Start change returns 409 BUDGET_POLICY_CHANGED with wording covering algorithm/settings. Formatting-only edits are immaterial.

Existing base `/api/draft-schedules/optimization`:

- POST `/prepare`: response adds server-derived `algorithm`, `strategyProfile`, `strategySettings`; retains policyFingerprint.
- POST `/operations`: request unchanged (operation/context/preparation/fingerprint), no algorithm override; unknown request fields rejected 422. Existing identity lookup before policy read; new Start checks fingerprint then captures server context. Echoed fingerprint cannot select algorithm.
- GET `/operations/{id}`: adds captured algorithm/strategyProfile/strategySettings and nullable `termination`; preserve ownership/context redaction.
- POST `/operations/{id}/accept`, `/finalize`, `/cancel`: unchanged request shapes. Accept fresh retained candidate under captured policy, not current file. No finalize for unproven heuristics.
- Retired `/generate`, `/accept` and batch HTTP routes retain errors. Retire synchronous service placement behavior too, migrating integration/performance callers. Pure Standard solver may remain in unit tests.

All supported teaching placements dispatch captured Strategy for 1–20 explicit courses; filters do not expand demand. Exams unchanged.

## Worker and evidence

Detached input carries frozen strategy context/ordered portion inputs, no ORM. Strategy takes existing detached courses/fixed occupancy/holidays/unavailable dates/settings/control; registry rejects unknown identifier, never falls back. Worker never rereads policy. Standard delegates unchanged to current optimizer; Cohort/Lecturer are concrete owner-specific constructive searches with repair.

Preparation/status/review/comparison/saved result identify same algorithm/profile/settings. Candidate fingerprint binds exact sorted assignments, captured context, ordered Lecturer identities/codes/targets/source. Planning snapshot binds material code/eligibility/explicit shares as well as current protections. Policy edits/deletion after Start alone are not stale input.

Review includes every selected course including zero, with required=scheduled+remaining. Lecturer `lecturerPortions` rows: lecturerId, lecturerCode, sequenceIndex, source, requiredUnits, scheduledUnits, remainingUnits, reasonCode/German reason or explicit uncertainty. Other strategies have empty portion rows. Whole nonnegative targets, unique identity and sum equality. Explain predecessor block without global infeasibility, e.g. “Vorheriger Lehrpersonenanteil ist noch nicht vollständig geplant.” Independently reject wrong sequence, target, transfer, predecessor completion or chronology.

## Proof profiles

Proof adds `objectiveProfile`: standard-v1 or heuristic-v1. Legacy absence normalizes Standard only. Standard key order/directions/validators stay unchanged. Heuristic ordered keys/directions:

| Key | Direction |
|---|---|
| total_units | max |
| intensive_teaching_time | max |
| daily_variety | max |
| preferred_size_deviation | min |
| course_rhythm_penalty | min |
| owner_balance_penalty | min |
| extra_cohort_day_rooms | min |
| course_room_changes | min |

Stable assignment ties are not an optimality proof. Finite fractional values allowed; comparison exact. Profile validator checks exact keys/order/directions/prefix proof rules and candidate/snapshot identities. Heuristic preference proofs remain false; total coverage equality may prove total_units only. Other proof statuses remain unfinished/not_attempted unless substantiated; exhausted neighborhood is no proof. Same-snapshot required LE may supply sound upper bound, labelled as bound not feasible packing; otherwise null bound/gap and gapKnown=false. Different profiles do not equate unrelated keys.

Termination: standard_completed, heuristic_completed, repair_limit, deadline, cancelled, failed; null during active work. budgetExhausted means actual deadline only. Keep saved state, validity, coverage and proof independent. Nonempty independently validated heuristic enters awaiting_decision/canAccept even before timeout, never auto-save/finalize. Zero total has no action. Standard existing finalization conditions stay intact.

## UI and fixtures

Read-only Standard/Kohorte/Lehrperson on existing preparation/progress/comparison/results. No dropdown. Show ordered Lecturer shares and remaining/blocker facts; show replacement consequences including emptied/manual courses. Distinct German text: “Heuristische Suche beendet — Optimalität nicht nachgewiesen”, “Reparaturlimit erreicht — Optimalität nicht nachgewiesen”, “Zeitlimit erreicht”, “Abgebrochen”, “Fehlgeschlagen”. Separate saved/unsaved statement. Announce status without repeated focus stealing/color-only cues; preserve keyboard/dialog focus/European dates; verify narrow layout and 200% zoom. Connected Start/cancel <=1s, status <=5s apart. Cancelled/stale late results cannot reopen review; saved receipt reconciles transport races.

Shared backend/client JSON fixtures cover selectors/profiles/termination, overrides/types, early complete/partial review, zero no-action, malformed proof key/order/bound/identity, portion corruption and legacy saved Standard. Backend endpoint serialization and client decoding must both execute cases, with semantic fixture parity assertion. Shape snapshots alone cannot prove dispatch/validity/atomicity.
