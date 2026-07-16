# US4 — Responsive access

- Result: PASS in focused tests and rendered checks at 820×800 and 320×720.
- At/below 820px the persistent sidebar is replaced by a visible **Menu** opener and a named modal panel.
- The open panel is 290px wide, background content is inert/aria-hidden, initial focus is **Close menu**, and Escape restores **Menu** focus.
- Selection dismisses the panel, preserves category/expansion state across breakpoint changes, and hands focus to changed content.
- At 320px all eight leaves were present, the panel fit within the viewport, and the document had no horizontal overflow.
- Schedule header reflow at 320px measured 296px within the 320px viewport with its metadata control unobstructed.

