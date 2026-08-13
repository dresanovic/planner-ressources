# Research: Planner-Controlled Schedule Regeneration Decision

## Decision 1: Pause the existing solve/save workflow without storing a candidate

**Decision**: When selected saved sessions exist, return the solver result as an
unsaved preview with comparison facts and a canonical fingerprint. Keep it only
in client state until accept or dismiss.

**Rationale**: The requirement is a planner-controlled pause, not a new durable
planning object. Stateless preview avoids a table, migration, token lifecycle,
expiry, cleanup, and decision history.

**Alternatives considered**:

- Durable candidate table: rejected as unnecessary for this interaction.
- Process-local cache: rejected because it adds lifecycle behavior without
  cross-process reliability.
- Client-submitted sessions: rejected because the server should not trust a
  mutable generated schedule payload.

## Decision 2: Reproduce the compared result on acceptance

**Decision**: Accept submits the original snapshot evidence plus the preview's
canonical fingerprint. The backend revalidates state, deterministically runs the
same solver again, and saves only if the reproduced fingerprint matches.

**Rationale**: I-003 already requires deterministic outcomes for unchanged
inputs. Reusing that property verifies the exact compared result without storing
or trusting provisional sessions.

**Alternatives considered**:

- Save the client-returned sessions after validation: rejected because it needs
  a broader exact-session validation surface and still accepts client-controlled
  content.
- Sign the preview payload: rejected because it introduces key management solely
  to avoid one repeated solve.

## Decision 3: Add a generated-only optimizer mode

**Decision**: For preview and accept, current selected sessions cannot be retained
by the solver and do not create a non-decreasing coverage floor. Every course is
represented only by generated sessions.

**Rationale**: The current automatic-retention/non-worsening rules can prevent the
valid lower-coverage alternative the planner must be allowed to accept.

**Alternatives considered**:

- Keep the current solver mode and add the dialog afterward: rejected because the
  desired alternative might never be produced.
- Solve each course independently: rejected because it breaks joint conflict
  guarantees.

## Decision 4: Reuse existing freshness and atomicity controls

**Decision**: Preview and accept use the existing shared/per-course snapshot
tokens, draft identities/revisions, active Working-revision guard, final reload,
and atomic save plan. The first successful accept changes the captured state, so
repeated or concurrent losing requests become stale.

**Rationale**: These mechanisms already cover the planning inputs named by
FS-023 and close the validation-to-write race without another lock or idempotency
store.

**Alternatives considered**:

- Add acceptance tokens/tombstones: rejected because they create storage and an
  implicit decision history for behavior already covered by revision freshness.
- Revalidate only the schedule revision ID: rejected because material inputs may
  change without changing that identifier.

## Decision 5: Build comparison facts server-side

**Decision**: The preview response contains aggregate and per-course
current/generated counts/status, candidate remaining reasons, and resolved
current warning codes/counts derived from the exact solved snapshot.

**Rationale**: This keeps business interpretation consistent and prevents the
client from recomputing facts that must match the accepted fingerprint.

**Alternatives considered**:

- Client-side comparison: rejected because warning and completeness rules would
  be duplicated.
- Recommended-winner label: rejected because the planner owns the trade-off.

## Decision 6: Cancellation is local state disposal

**Decision**: Button, Escape, close, and navigation dismissal clear the preview
from React state. No backend cancel operation exists.

**Rationale**: Preview writes no server state, so a cancel API, expiry policy,
cleanup job, or audit row would add behavior without value.

**Alternatives considered**:

- Persist cancelled/accepted status: rejected by the no-decision-history scope.
- Best-effort server cancellation: rejected because there is nothing to cancel.

## Decision 7: Preserve direct save for wholly unplanned selections

**Decision**: If no selected course contains saved teaching sessions, the
existing generation operation continues to solve and save atomically without a
comparison.

**Rationale**: This is explicitly confirmed and limits FS-023 to replacement
authority.

**Alternatives considered**:

- Preview every generation: rejected because it adds approval where no current
  selected result exists.
