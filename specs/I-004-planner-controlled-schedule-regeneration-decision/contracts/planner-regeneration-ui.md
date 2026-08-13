# UI Contract: Planner-Controlled Schedule Regeneration Decision

## Entry and generation timing

- The existing `Stundenpläne erzeugen` surface remains the only teaching
  generation workflow for one to twenty selected courses.
- Generation begins from the selected semester's active editable Working
  revision and uses the established saved constraints and unavailable dates.
- If no selected course has saved teaching sessions, a valid result saves
  directly and the existing saved-result summary is shown.
- If any selected course has saved sessions, generation changes no schedule and
  opens the post-generation comparison only after a valid joint candidate exists.
- Preparation no longer opens a replacement confirmation, and the interface
  never asks for permission before the comparison facts exist.
- Failure, timeout, stale preparation, an invalid candidate, or no non-empty
  valid alternative shows actionable German guidance and opens no comparison.

## Comparison dialog structure

The modal has one programmatically named title and description, followed by:

1. Why a decision is required and that it applies to the complete selection.
2. The consequence that accepting replaces all selected saved sessions,
   including planner-created or edited sessions.
3. Aggregate `Aktueller Stundenplan` and `Neu erzeugter Stundenplan` facts:
   required, scheduled, and remaining teaching units plus complete/partial text.
4. One semantic section per selected course with the same two explicitly named
   sides, per-course counts/status, generated remaining reasons, and resolved
   current warnings.
5. Exactly the actions `Neu erzeugten Stundenplan übernehmen` and `Abbrechen`.
6. An optional close icon/button named `Vergleich schließen`; it has the same
   behavior as `Abbrechen` and is not a third decision.

The comparison:

- never labels either side as the winner or recommends one;
- never provides per-course accept/reject controls;
- never provides a reason/comment field;
- keeps a valid lower-coverage partial candidate selectable;
- distinguishes status and side with headings/text/structure, not color alone;
- associates every reason and warning with a course and side.

## Decision behavior

### Accept

- Disable both actions while acceptance is in flight.
- Submit the preview's prepared snapshot evidence and candidate fingerprint; do
  not submit generated sessions.
- On success, close the dialog, refresh authoritative schedule/workspace data,
  and show the saved result summary for every selected course.
- Repeated activation while busy sends no second client request.
- If the response is lost, refreshing schedule data is the recovery path.

### Cancel or dismiss

- `Abbrechen`, Escape, the close control, and leaving the unresolved comparison
  all clear the complete unsaved preview from client state.
- No backend cancellation is required because generation stored no provisional
  server state.
- No saved schedules are refreshed as changed and no automatic repair occurs.

### Stale or non-reproducible

- Close the unusable comparison and remove its fingerprint/evidence from client
  state.
- Preserve the selected courses and relevant generation inputs.
- Present an actionable German message equivalent to: the planning state changed
  or the compared result could not be reproduced; generate a new alternative
  before deciding.
- Never retry acceptance automatically and never submit an older candidate.

## Focus and keyboard contract

- When the comparison opens, store the invoking control and move focus to the
  dialog title/container or first meaningful dialog control.
- `Tab` and `Shift+Tab` remain within enabled dialog controls; when all actions
  are disabled, focus remains on the dialog.
- Escape cancels only when no acceptance request is in flight.
- Background content is unavailable to pointer and keyboard interaction while
  the modal is open.
- Closing returns focus to the generation control or another logical surviving
  control.
- Status/error updates use an appropriate live region without repeatedly
  announcing the entire comparison.

## Responsive and zoom contract

- The dialog is vertically scrollable within the viewport.
- At wide presentation, current/generated facts may use two aligned columns.
- At narrow presentation and 200% text zoom, each course stacks under explicit
  `Aktuell` and `Neu erzeugt` headings; facts never depend on column position
  alone.
- Long course names, warnings, and reasons wrap without horizontal page overflow.
- Both decision actions remain reachable through dialog scrolling and retain
  visible focus indicators.

## Client state contract

The Schedule page keeps at most one unresolved candidate:

```text
null
or
{
  candidateFingerprint,
  preparedEvidence,
  semesterId,
  scheduleRevisionId,
  comparison
}
```

- Starting another generation is unavailable until the current comparison is
  accepted or discarded.
- Semester/revision changes and navigation away discard the local candidate and
  require no server cleanup.
- Constraint/manual/lifecycle mutations are unavailable behind the modal; if
  relevant state changes elsewhere, server acceptance freshness checks remain
  authoritative.
- Candidate data is never merged into the `schedules` collection before accept.

## Required component and page tests

- Comparison opens after generation, not preparation, for selections with saved
  sessions.
- Direct-save selection opens no comparison.
- Aggregate and every course current/generated fact render on the correct side.
- A lower-unit partial candidate keeps the accept action enabled.
- Exact action labels exist; no legacy `Optimierung bestätigen`, winner label,
  keep-current action, per-course action, or reason field exists.
- Accept calls once, refreshes after success, and applies mixed selections as one
  UI outcome.
- Button, close control, Escape, and navigation dismissal all clear the complete
  candidate and do not call accept.
- Stale/fingerprint-mismatch errors remove the preview evidence, preserve
  selection, and direct the planner to regenerate.
- Focus entry, wrap, disabled-control containment, Escape, and focus return pass.
- Narrow/long-copy/200%-zoom review preserves course and side association.
