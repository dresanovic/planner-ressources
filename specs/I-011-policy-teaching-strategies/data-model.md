# Data Model: I-011

Existing course/session/resource/revision entities remain authoritative. No permanent allocation or room entity is added.

## Effective policy

| Field | Constraint |
|---|---|
| activeAlgorithm | `standard`, `cohort`, `lecturer`; omission only defaults to `standard`; explicit null/empty/wrong type/unknown invalid |
| defaultSeconds | finite positive whole number; booleans invalid; omitted field defaults to 300 |
| ceilingSeconds | finite positive whole number; booleans invalid; omitted field defaults to 1800; defaultSeconds <= ceilingSeconds |
| policyFingerprint | SHA256 of canonical effective selector/budgets and effective settings version; formatting/key order irrelevant |

Allowed file keys are exactly the first three above; duplicates invalid. Repair/checkpoint defaults are server constants, not new policy keys. Derive normal path from installed module, env override wins; missing/unreadable file errors on new prepare/Start only.

## Captured context and receipt

Detached immutable context: algorithm, profile version, budgets, fixed 1000/eight/five-second defaults, prepared tokens, selected courses, active Working revision, resource eligibility, normalized lecturer codes/IDs and any genuinely supplied explicit allocation values. No ORM/session crosses worker boundary. One absolute monotonic deadline/cancellation applies throughout.

Add durable OptimizationOperation fields: `algorithm` non-null enum standard/cohort/lecturer; `strategy_profile` non-null version identifier; `strategy_settings` non-null JSON object of captured defaults. Migration 0015 backfills historical Standard/legacy settings; existing saved JSON normalized as Standard only on read. Integrate new/upgrade/schema-completeness detection. Candidates/portions/secrets remain memory-only; restart interrupts unfinished runs and cannot auto-save them.

## Lecturer portions

Per selected course: ordered unique active eligible lecturer IDs, normalized codes, index, source derived/explicit, required/scheduled/remaining LE and blocker or uncertainty. Ascending existing normalized code then stable ID; no input/availability reordering. Derived target is quotient T/N plus one for first T modulo N lecturers. All targets are whole nonnegative LE and sum to course requirement. Explicit confirmed targets, when available, replace sizes but not code order; invalid duplicate/negative/inconsistent targets reject input, never transfer silently. Zero targets do not block.

Every assignment debits course and portion once. Every preceding nonzero target must be complete before a successor starts, with all predecessor sessions ended before successor sessions. Unrepresentable shares remain open and block successors. Independent validation derives expected order/targets from captured authoritative data, checks actual sessions and freshness of codes/eligibility/explicit shares. Candidate-supplied sorted sessions are insufficient evidence.

## Search state and scoring

Global course-demand ledger, portion ledger, provisional assignments, lecturer/room/cohort occupancy, fixed protected occupancy, weekly loads, room sets, rhythm, run-wide repair attempts and immutable best checkpoint. Failed repair restores all fields. Selected current sessions are comparison alternatives, not deductions from full replacement targets. No protected session moves.

Monday–Sunday institution-local weeks clipped to course period; eligible dates/weeks based on minimum-size legal candidates before provisional competition. Owner weeks union relevant selected eligible weeks and fixed-teaching weeks inside selection span. Fixed teaching adds LE once; breaks/exams add no instructional load. Ordinary weight 1, feasible marked-intensive weight 2; no raw-minute normalization.

Ordered comparison: maximize coverage/intensive instruction/intensive variety; minimize preferred-size deviation/course rhythm/owner squared weekly LE divided by weight/extra cohort-day rooms/course room changes; stable assignment order last. Exact scaled/rational arithmetic. The spec's cadence, boundary-week exceptions, scarcity and numeric fixtures remain normative; Standard keeps its own order.

## Candidate and state

Every selected course has exact sessions, required/scheduled/remaining totals with equality and reasons/uncertainty. Lecturer adds portion facts. Algorithm/profile/settings, ordered shares, exact assignments and prepared/candidate fingerprints are bound together. Heuristic constructors explicitly set optimal=False.

Independent `termination`: standard_completed, heuristic_completed, repair_limit, deadline, cancelled, failed. Existing timeout_no_candidate phase remains for no usable candidate compatibility; termination/terminalCode distinguish early zero from actual deadline. Nonempty valid heuristic → awaiting_decision; never ready_to_save despite full coverage. Zero placement → no review/action. Accept → saving → saved atomically; precommit cancel/stale/failure saves nothing; postcommit receipt wins races. Policy changes after Start affect future runs only.
