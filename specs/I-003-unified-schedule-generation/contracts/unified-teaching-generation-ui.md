# UI Contract: Unified Teaching Schedule Generation

## One generation surface

Calendar Planning exposes one teaching generation panel and no single/batch mode
switch.

- The selected semester and active editable revision are required.
- The planner selects one to twenty eligible courses in that semester.
- The visible selection count and selected course names update immediately.
- The same Prepare action and replacement confirmation are used for one and many
  courses.
- Empty, duplicate, oversized, cross-semester, or unavailable selections do not
  call generation.
- Results show one outcome for every selected course.
- The panel contains no algorithm selector and no link to a legacy generator.

## Focused course constraints

One selected/focused course may be inspected at a time.

- Start and end dates initially show the saved override or inherited semester
  boundaries.
- Save is explicit and writes through the constraints `PUT` operation.
- Reset is available only for a saved override and restores inherited semester
  dates through `DELETE`.
- Dirty date edits are local form state and never become preparation input.
- Generation is disabled while the focused form is dirty, invalid, or saving;
  copy explains that the dates must be saved or discarded first.
- The course study type and all active mapped weekly windows are displayed
  read-only. No add, edit, remove, or copy-window control is rendered.
- A successful save/reset refreshes the effective constraint response and the
  authoritative draft validation alerts. Sessions are not moved automatically.
- Date editing is not duplicated in Academic Data, Schedule Review, or other
  Calendar surfaces.

## Replacement confirmation

Preparation identifies every selected course with an existing draft.

- The confirmation dialog lists the affected course names.
- Confirm submits the exact prepared tokens with `replacementConfirmed=true`.
- Cancel closes the dialog and performs no mutation.
- Any stale-input response discards the prepared client state and asks the
  planner to prepare again.

## Teaching List field contract

Wide List header and every teaching row use this exact order:

| Position | Field | Narrow label |
|---:|---|---|
| 1 | Date and occurrence warnings | Date |
| 2 | Time | Time |
| 3 | Duration | Duration |
| 4 | Course | Course |
| 5 | Cohort | Cohort |
| 6 | Lecturer | Lecturer |
| 7 | Room | Room |
| 8 | Study type | Study type |
| 9 | Actions, when permitted | Actions |

Implementation rules:

- Header and teaching rows share one teaching-specific grid template.
- Generic schedule occurrence styles are scoped to their owning list and cannot
  override the teaching grid.
- Warnings remain inside position 1 and may increase row height without adding a
  grid item or shifting later values.
- Long text wraps inside its own field (`min-width: 0`; safe word wrapping).
- From 320 through 820 CSS pixels, the wide header is hidden and every value
  renders its explicit visible label. At 821 CSS pixels and above, the shared
  wide teaching grid applies. Actions and warnings remain reachable.
- At 200% text zoom, values may stack but must retain their labels and associations.

## Conflict warning contract

The visible title is determined by the backend alert code:

| Alert code | Visible title | Required resource sentence |
|---|---|---|
| `LECTURER_OVERLAP` | Lecturer conflict | Name the lecturer assigned to overlapping occurrences. |
| `ROOM_OVERLAP` | Room conflict | Name the room assigned to overlapping occurrences. |
| `COHORT_OVERLAP` | Cohort conflict | Name the cohort with overlapping occurrences. |

Each warning also lists the related course, date, and interval; lecturer, room,
and cohort context is included when available. Warnings for the same related
session remain separate when their conflict codes differ. Duplicate warnings with
the same affected session, related session, and conflict code render once.

After a constraint save, manual edit, deletion, or generation result, the List
renders only alerts returned by the refreshed authoritative draft response; it
does not preserve locally cached resolved warnings.
