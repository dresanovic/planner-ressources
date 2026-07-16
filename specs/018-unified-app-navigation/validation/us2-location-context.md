# US2 — Location context

- Result: PASS in the focused 36-test suite.
- Schedule starts as the sole current leaf with Academic Data collapsed.
- Selecting an Academic Data child exposes one current child, an active parent, and `aria-expanded="true"`.
- An active Academic Data parent refuses collapse. Category and permitted expansion state persist across Schedule round trips.
- Selecting the current leaf again is a no-op for page rendering/state and leaves focus on that leaf.
- Current leaves use text weight plus a leading marker; the parent uses a separate active treatment, so location is not communicated by color alone.

