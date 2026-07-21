# Cross-Contract Amendment: Active Working Revision Guards

FS-013 keeps the existing FS-006 through FS-012 scheduling endpoints, but every operation that can add, change, replace, or remove a scheduled teaching or exam occurrence must identify the semester revision it intends to mutate.

## Required mutation context

All affected requests add:

| Field | Type | Rule |
| --- | --- | --- |
| `scheduleRevisionId` | positive integer | Must equal the semester's active Draft or Ready for review revision when the server claims the write boundary. |

This identity is distinct from:

- the displayed semester `revisionNumber`;
- `DraftSchedule.revision`, which protects one course draft row;
- `ExamSession.revision`, which protects one exam row;
- configuration revisions and material input snapshot tokens.

Existing row revisions and material snapshot tokens remain required where their originating contracts already require them. `scheduleRevisionId` adds the missing cross-lifecycle authority check; it does not replace those safeguards.

## Affected operation families

| Existing operation family | Amendment |
| --- | --- |
| Single-course teaching generation | Generation request includes `scheduleRevisionId`; the service rejects unless that revision is the active working revision for the requested semester. |
| Manual teaching-session creation | Request includes `scheduleRevisionId`. |
| Manual teaching-session edit | Request includes `scheduleRevisionId` in addition to current draft/session validation. |
| Teaching-session deletion | Confirmed request/query includes `scheduleRevisionId` in addition to expected draft identity/revision. |
| Complete course-draft deletion | Confirmed request/query includes `scheduleRevisionId` in addition to expected draft identity/revision. |
| Multi-course generation preparation and execution | Preparation includes the active `scheduleRevisionId`; execution echoes it and the material tokens. Both phases reject a different active revision. |
| Conflict-aware semester optimization preparation and execution | Preparation includes the active `scheduleRevisionId`; execution echoes it and all existing semester/course snapshot tokens. |
| Exam generation preparation and execution | Preparation includes the active `scheduleRevisionId`; execution echoes it and all existing exam/material snapshot tokens. |
| Manual exam creation, correction, and deletion | Each request includes `scheduleRevisionId` in addition to configuration/exam revisions and input snapshot tokens. |

## Unaffected planning-input operations

The following do not change scheduled occurrences and therefore do not receive a schedule revision identity in FS-013:

- generation-constraint save or clear;
- exam-configuration save, enable, disable, or preparation;
- academic catalog, resource eligibility/availability, and holiday administration.

Their later changes never rewrite an immutable snapshot. Current values are used only when the planner works in an active revision or prepares a new publication.

## Server behavior

Before the first schedule write in a transaction, the server must:

1. Load the supplied schedule revision.
2. Verify its semester matches the operation's semester.
3. Verify it is the one active revision and its state is Draft or Ready for review.
4. Claim the lifecycle/semester write boundary.
5. Recheck the same conditions before applying the existing row-level or snapshot-token mutation rules.

Failure returns HTTP `409` with error code `working_revision_required`, `revision_not_editable`, or `stale_lifecycle_state` and the current lifecycle overview when available. No existing row, revision, event, or snapshot is changed.

## Client behavior

- `CourseSchedulePage` obtains `scheduleRevisionId` from the authoritative lifecycle overview and supplies it to every affected client API function.
- Schedule mutation controls are present only while viewing that exact active working revision.
- A lifecycle refresh failure freezes all schedule mutations; the client never reuses the last known ID without a successful refresh.
- After any `409`, the client closes open mutation/confirmation UI, refreshes lifecycle plus teaching and exam state, and requires the planner to reopen the action.

## Required regression assertions

- An editor opened under revision N cannot save after N is Published, superseded, or abandoned.
- An editor or prepared generation opened under revision N cannot write into later revision N+1.
- Ready for review remains editable because the same revision identity remains active.
- Existing row-level stale checks still reject conflicting edits within the same active revision.
- Published-only semesters reject every scheduled-occurrence mutation until the planner explicitly creates or restores a working revision.
