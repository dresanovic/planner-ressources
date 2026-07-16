# US3 — Keyboard and assistive-technology contract

- Result: PASS in the focused 36-test suite and rendered semantic inspection.
- Native buttons provide disclosure and leaf activation in DOM order; collapsed children are removed from the DOM and tab order.
- Destination changes focus the application content target; repeated-current selection does not jump focus.
- Narrow focus starts on **Close menu**, loops in both directions, and returns to **Menu** for Escape/explicit dismissal.
- Semantic inspection exposed one `Primary navigation`, the Academic Data expanded state, and one current leaf.
- Focus outline `#a33b00` measures 6.60:1 on white, 5.49:1 on current blue, 6.08:1 on active-parent gray, and 5.80:1 on hover blue (all above 3:1).

