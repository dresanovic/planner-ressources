# US2 Focused Schedule Evidence

**Date**: 2026-07-27  
**Result**: PASS

- Schedule exposes ordered Calendar, Versions, and Exams children; Calendar is the default and only one leaf carries current semantics.
- The Schedule page remains mounted and exposes only the selected destination; hidden destinations are hidden/inert and excluded from focus.
- The shared context header remains visible, with destination-meaningful revision/course controls.
- Destination changes use the page-owned dirty-navigation approval handshake; App stores no duplicate pending intent.
- Wide temporary-navigation selection closes the modal overlay, removes background inert state, and focuses the committed Schedule content.
- Focused navigation: 2 files, 21 tests passed in 2.17s.
- Focused context/pane/Calendar: 3 files, 29 tests passed in 2.55s.
- Live Chromium checks confirmed Versions and Exams replace Calendar, navigation closes after selection, main content receives focus, and the Exams eligibility groups are exposed only in Exams.

No navigation action invokes a schedule or Academic Data mutation.
