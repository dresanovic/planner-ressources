# Lecturer Calendar Export UI Contract

## Placement and availability

- The visible action label is `Kalender herunterladen` following the established German UI copy/I-002 conventions.
- The action appears in the semantic context header of the reused FS-015 `CalendarPlanningWorkspace` only after a valid complete lecturer review has loaded.
- It does not appear during loading, transient initial failure, or the terminal unavailable state, and it never appears in the planner workspace.
- It is visually and structurally separate from calendar/list mode, date navigation, filters, and session selection so it cannot imply a partial export.
- `CalendarPlanningWorkspace` receives only an optional neutral `contextActions`/equivalent node; it has no iCalendar, bearer, or download logic.

## Notice dialog

Choosing the action opens a purpose-built modal dialog and performs no network request or file handoff. The dialog:

- has `role="dialog"`, `aria-modal="true"`, one programmatic name, and one description;
- identifies the complete unfiltered event count from the currently opened FS-015 projection, including zero;
- states that the file is a static personal snapshot outside product control;
- states that later schedule/revision/link changes do not update, revoke, remove, or recall the file;
- warns that copying the file can expose the schedule and that the recipient must store, share, and delete it appropriately;
- states that repeat manual import can create duplicates and the product does not update, reconcile, or remove earlier imports;
- provides `Abbrechen` and `Download fortsetzen` controls;
- initially focuses the safe Cancel control, traps Tab/Shift+Tab, and restores focus to the opener on cancel/close when present;
- closes on Escape only while not busy; backdrop interaction never confirms a download.

The displayed count is the complete unfiltered count of the opened projection, not a reservation or guarantee about the later file. The notice states that the confirmed request is authoritative and may contain a newer complete assignment set with a different count. The UI does not create a preview token or send the count.

## Confirmation and browser handoff

- Confirming issues exactly one request through `downloadPublicLecturerCalendar(secret)` with only the in-memory FS-015 secret.
- While pending, both decisions are disabled, Escape is ignored, repeat activation issues no second request, and an understandable busy state is announced.
- The API helper uses a fixed same-origin relative path, bearer header, `Accept: text/calendar`, and `credentials: 'omit'`.
- The helper validates success status, contracted media type, and safe server filename before returning `{ blob, filename }`.
- The page creates one temporary object URL and anchor with `download=filename`, activates it once, removes it, and revokes the URL after handoff.
- Neither page nor workspace derives event scope, calendar content, or filename from filters, visible dates, selected session, lecturer name, or DOM state.

## Outcomes and state preservation

- **Cancel**: no request, no file, close dialog, restore opener focus.
- **Success**: close dialog, restore focus when possible, and announce a concise polite success status without claiming that Outlook import completed.
- **Retryable incomplete projection, network/429/5xx, or invalid delivery metadata**: keep the dialog and complete workspace mounted, show one safe `role="alert"` message, restore actionable controls, and permit explicit retry.
- **Terminal 404/unavailable**: use the existing FS-015 terminal clearing path, remove all protected schedule/dialog data from the DOM, and show the generic unavailable state.

Cancel, success, and retryable failure preserve calendar/list mode, visible period, filters, scroll position, eligible selected session, and unsent feedback. Terminal scope loss may clear those values only through the existing FS-015 protected-review removal behavior.

Raw response bodies, `Content-Disposition`, thrown exception text, bearer material, filenames rejected as unsafe, internal identifiers, and server diagnostics are never shown to the user or logged by the client.

## Responsive and accessibility acceptance

- New controls meet the existing 44 CSS-pixel public-workspace target/focus treatment.
- At 320 CSS pixels and 200% text zoom, the header action, dialog copy, count, error, and decisions wrap without page-level horizontal scrolling.
- Keyboard-only and NVDA/Firefox checks confirm dialog announcement, count/notice comprehension, focus containment/restoration, busy/error/success communication without color, and no double-modal composition with the narrow-screen session pane.
- Latest stable Edge, Chrome, and Firefox checks confirm one blob handoff, filename preservation, cancellation, retry, and workspace-state preservation. Browser download-shelf behavior is manual evidence, not a jsdom assertion.
