# Data Model: Planner-Controlled Schedule Regeneration Decision

## Persistence impact

No new persisted entity or migration is required.

The feature reuses:

- `ScheduleRevision` for the active editable Working scope and concurrency guard;
- `DraftSchedule` and `DraftSession` for current and accepted teaching results;
- existing course, semester, constraint, holiday, resource, availability,
  capacity, unselected teaching, and active-exam inputs;
- `PlanningOutcome` only for results that were actually saved.

An unsaved preview is a request/response value held in client state. It is not a
database row, lifecycle snapshot, publication, schedule, or decision history.

## Existing entity rules

### ScheduleRevision

- Preview and acceptance target the same revision ID.
- Both require that revision to be the active editable Working revision.
- Acceptance rechecks current lifecycle state and freshness before saving.

### DraftSchedule and DraftSession

- A selected course requires post-generation comparison when its draft contains
  at least one saved teaching session.
- Selected sessions form the current side of the comparison and remain unchanged
  while the preview is open.
- Unselected sessions remain fixed occupancy.
- Acceptance replaces, creates, or clears every selected course result through
  the existing atomic save transaction.
- A zero-session generated course clears an existing selected draft or remains
  absent; no empty draft is created.

### PlanningOutcome

- Preview, cancel, dismissal, stale rejection, fingerprint mismatch, failure,
  timeout, and unproven results create no outcome.
- Direct save and successful acceptance retain the established saved-generation
  outcomes.
- No outcome records `accepted`, `cancelled`, a candidate fingerprint, or a
  written decision reason.

## Planning-time value objects

### PreparedGenerationEvidence

Existing preparation evidence reused by preview and accept:

- semester and active schedule revision IDs;
- active Working revision state and row version;
- selected course IDs;
- canonical unavailable dates;
- shared snapshot token;
- per-course draft IDs/revisions and input snapshot tokens.

Freshness covers the established I-003 inputs: selected and protected teaching,
active exams, course/semester/constraints, study-type windows, holidays,
resources, eligibility, availability, capacity, and lifecycle state. Past exams
retain I-003 behavior and do not independently stale the evidence.

### GeneratedJointSolution

The existing optimizer result in generated-only mode.

Per-course values:

- course identity;
- exact generated sessions;
- required, scheduled, and remaining units;
- complete or partial status;
- remaining/blocking reasons.

Invariants:

- Covers exactly the selected course set.
- Contains no retained-current course result.
- Has at least one generated session across the complete selection.
- May contain zero sessions for one selected course in a valid joint partial.
- Every session satisfies active hard rules and mutual/fixed occupancy rules.

### CandidateFingerprint

A SHA-256 digest of the canonical generated joint solution.

Canonical fingerprint input:

```text
[
  [
    courseId,
    [date, startTime, endTime, units, lecturerId, roomId, cohortId,
     timeWindowId, constraintWindowIndex]...
  ]...
]
```

Rules:

- Courses and sessions use stable deterministic ordering.
- Serialization has stable keys/separators and excludes display copy, elapsed
  time, database-generated draft/session IDs, and current comparison facts.
- Preview returns the digest.
- Accept re-solves from fresh authoritative inputs, recomputes the digest, and
  proceeds only when it matches.
- The fingerprint is equality evidence, not authorization or persisted identity.

### RegenerationComparison

Server-built factual evidence returned with an unsaved preview.

Fields:

- selected course IDs;
- aggregate current and generated coverage facts;
- one course comparison per selected course;
- `replacesAllSelectedSessions = true`;
- `mayReplacePlannerEdits = true`.

Coverage facts:

- required units;
- scheduled units;
- remaining units;
- status: `complete` or `partial`.

Per-course comparison:

- course identity;
- current and generated coverage facts;
- generated remaining/blocking reasons;
- current hard-warning codes/counts resolved by the hard-valid candidate.

The manual-edit flag states the consequence without identifying individual
sessions; `DraftSession` has no reliable provenance and no provenance migration
is needed.

### GenerationExecutionResult

A discriminated generation response:

- `mode = direct_saved`: existing saved summary/outcomes.
- `mode = decision_required`: `saved=false`, candidate fingerprint, prepared
  evidence, and comparison.

No-result responses contain no fingerprint or comparison.

### AcceptRegenerationRequest

Fields:

- semester ID and schedule revision ID;
- canonical unavailable dates;
- shared snapshot token;
- per-course prepared draft IDs/revisions and input snapshot tokens;
- candidate fingerprint.

It contains no generated sessions, per-course decision, comment, or reason.

### AcceptedGenerationResult

The established saved summary and per-course outcomes after the atomic commit.

## State transitions

```text
prepare (read-only)
  |
  v
generate
  |-- no selected saved sessions --> solve + direct atomic save
  `-- selected saved sessions
        |-- invalid/stale/timeout/unproven/all-zero --> no preview, no mutation
        `-- valid generated-only result -----------> client preview, no mutation
                                                       |-- cancel/dismiss: clear state
                                                       `-- accept
                                                            |-- stale or fingerprint mismatch: no mutation
                                                            `-- fresh matching re-solve: atomic save
```

## Acceptance transaction

1. Validate the request shape and selected-course identity.
2. Reload authoritative inputs and require all prepared evidence to remain fresh.
3. Run the same generated-only deterministic solve.
4. Recompute and compare the canonical fingerprint.
5. Claim/revalidate the active Working revision through the existing write
   boundary and final reload.
6. Replace/create/clear every selected result atomically.
7. Retain established saved PlanningOutcomes.
8. Commit once; any error rolls back all selected changes and outcomes.

The first successful commit changes captured draft identities/revisions. A
repeated or concurrent losing request therefore fails freshness validation and
cannot apply again.

## Cancellation

Cancellation has no data transition. The client discards its unsaved preview and
fingerprint. No API call, cleanup, expiry, or retained record is required.
