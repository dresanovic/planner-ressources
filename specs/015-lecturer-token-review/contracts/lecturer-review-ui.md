# FS-015 UI Contract

## Entry points

### Planner

The existing Schedule navigation adds one child destination:
**Lecturer coordination** (renamed from **Lecturer reviews**). It is visible
only inside the normal planner shell and
uses the selected semester and FS-013 revision. The trusted gateway requires
its existing planner authorization before serving this page or forwarding any
planner API request.

### Accountless reviewer

The exact public route
`/lecturer-review/#/{secret}` renders only the public lecturer review page.
The gateway permits this public path while protecting the planner root. Before
the first API request, the page:

1. validates the fragment shape;
2. keeps the secret only in page memory;
3. removes the fragment while retaining `/lecturer-review/` in the address
   bar/history entry; and
4. sends it only in the authorization header to fixed, relative, same-origin
   public endpoints with browser credentials omitted.

Client bootstrap branches on the exact pathname before dynamically importing
the public page or planner application. The public branch may load shared
calendar, neutral list, filter, pane, and discard-dialog presentation modules
in restricted mode. It never loads the planner App, planner API adapters,
global planner navigation, Versions, Exams, operational summaries, mutation
callbacks, or administrative data.

## Planner Lecturer coordination destination

### Required order

1. Page heading and selected revision identity/state.
2. Feedback counters, filters, active-filter status, and clear-all action.
3. Filtered feedback result/status.
4. Link management for lecturers assigned in the revision.

### Scoped feedback filters and counters

- Available filters are intended lecturer, course, session kind, and feedback
  kind. The outer Schedule context fixes the revision, so no redundant
  one-value revision selector is rendered.
- Filters intersect and are applied to individual immutable items before
  regrouping.
- Every active filter, including feedback kind, recomputes both the displayed
  result and all four counters from exactly the same scope: all feedback items,
  comment items, impossible-session items, and distinct affected sessions.
- Comment count includes revision and session comments. Optional text on an
  impossible-session item does not turn it into a comment item.
- Course and session-kind filters exclude revision comments because those
  items have no session context. Historical filtering uses immutable captured
  context.
- Repeated impossible items count separately; distinct affected sessions count
  each `(revision, session kind, source session ID)` once.
- **Not possible** remains a prominent feedback-kind control with a non-color
  marker and semantic selected state.
- Complete results may display exact zero. Partial or unavailable feedback
  displays qualified/non-definitive counters and never presents missing data
  as zero.
- Active filters remain visible. Clear all restores the selected revision's
  complete feedback result and changes no domain data.
- Filter and count changes announce the new result scope and move focus only
  when needed to keep keyboard position understandable.

### Feedback group

Each group shows:

- revision-level or session-level identity;
- captured submission-time course/session context for every individual
  session feedback item, including when several items in one group were
  submitted before and after a schedule edit;
- intended lecturer attribution phrased as link attribution, not proof of
  identity;
- feedback kind in words and without color-only meaning;
- plain-text comment, submission date/time, and time zone;
- number of impossible flag items in the group;
- **Open current session** only when the server supplies both revision ID and
  current occurrence reference.

Opening a current session runs the existing unsaved-change navigation guard,
establishes or preserves the correct semester/revision Schedule context,
switches to Calendar, selects the exact authoritative occurrence, and opens the
existing planner session workflow without mutation. If the session was removed,
reassigned, historical, or cannot be mapped, the group retains its historical
context and never substitutes another target.

### Link management

- The lecturer selector is populated only from server-supplied assignment
  summaries for the selected revision.
- Duration choices are **1 day**, **2 days**, and **3 days**; 3 is selected by
  default for both issue and replace.
- Initial issue is enabled only in the active Working Draft or Ready for review
  revision and only for a lecturer with at least one current assignment.
- Ready for review is labeled as recommended. Draft requires no extra
  confirmation.
- Replacement is available for an active pair while Working or while its
  revision is Current Published.
- Revoke and replace require deliberate buttons and show an authoritative
  result.
- Published historical, superseded, abandoned, and ended links remain
  non-secret history only.

### One-time review URL

After successful issue or replacement, the backend returns the raw secret once
and the planner client constructs
`{window.location.origin}/lecturer-review/#/{secret}`. A transient success
region shows:

- intended lecturer;
- revision and course context;
- issue time;
- exact expiry date/time/time zone;
- active status;
- the selectable review URL;
- **Copy link** and **Dismiss**;
- manual/private-delivery and bearer-link warning text.

Copy uses the browser clipboard API, announces success with `role="status"` and
failure with `role="alert"`, and never regenerates the credential. The
one-time URL is cleared on Dismiss, revision/semester change, or leaving the
destination. It is never placed in local/session storage, routine overview
state, analytics, or error text. Loss is recovered only by replacement.

## Accountless Lecturer review page

### Safe states

The page begins in a non-disclosing loading state. Absent, malformed, unknown,
expired, revoked, replaced, abandoned, superseded, or source-throttled
credentials render the identical unavailable page:

> This review is unavailable. Contact the planner for a new link.

No lecturer, revision, expiry, course, session, feedback, or reason-specific
field remains visible. A known valid-link throttle may instead show the generic
temporary-unavailable message and retry guidance, still without protected
data.

If a later refresh or submission determines that the credential is unusable,
the page clears previously loaded protected data before showing the safe state.
An older in-flight response can never restore data after that terminal result.
For a temporary network or known-link throttle failure, the page clears
protected data, keeps the credential only in memory, and offers a safe retry.
If a feedback submission proves that its session changed or left scope while
the overall link remains valid, the page clears that target and its drafts,
creates no item, explains the scope change, and directs the reviewer to reload
the browser page or reopen the link.

### Review heading

A complete valid review shows:

- intended lecturer name;
- explicit statement that the name is intended scope and does not authenticate
  the person using the link;
- semester, revision label, and Draft/Ready/Published state;
- access expiry date/time/time zone, labeled as access expiry rather than an
  approval deadline;
- read-only and advisory-feedback explanation.

### Schedule

The public page composes the established calendar/list workspace in restricted
mode:

- Week, Day, Month, and List modes plus applicable period navigation;
- intended lecturer as fixed labeled non-editable context, never a filter;
- course, cohort, room, study type, session type, bound lifecycle, and
  validation facets when choices exist;
- visible intersecting active filters and one clear-all action;
- teaching and exam occurrences selectable from calendar and list;
- mode, visible period, filters, and eligible selection retained across mode
  and responsive changes.

The complete authorized assignment projection is distinct from its filtered
display. Zero authorized assignments shows an authoritative empty schedule.
A nonempty projection with zero filter matches explains that filters hid the
records and offers Clear filters.

The page never shows other lecturers, lecturer contacts, student data,
unassigned sessions, planner notes, raw/internal findings, other revisions,
operational summaries, or planner controls. Lecturer-safe current validation
categories/messages may be shown without counterpart identity or internal
references.

Assignment changes become visible only after full browser reload or reopening
the link. There is no timed polling, background refresh, or in-workspace refresh
action.

### Restricted session pane

Selecting a teaching or exam occurrence opens the shared adaptive session pane
with safe course, cohort, date/time, room, study type, teaching units or exam
duration/type, bound lifecycle, and sanitized validation context.

- Wide: pane may sit beside the calendar.
- Constrained: pane overlays from the established side.
- Narrow: pane is a temporary full-screen dialog with focus containment and
  obscured content made inert.
- Presentation changes preserve mode, period, filters, selection, scroll
  origin, and drafts.
- Only session comment and **Not possible** actions are rendered. Edit, delete,
  create, generation, availability, lifecycle, publication, source,
  configuration, capacity, and administrative actions are absent.
- Close returns focus to the originating calendar/list item or the results
  heading when that origin no longer exists.

### Unsubmitted feedback guard

When either session draft is nonblank, lecturer-initiated pane close, session
change, or a filter that would hide the target opens the shared discard dialog
with feedback wording. Cancel keeps the draft and all context. Discard clears
both drafts for that target, performs the requested context change, and creates
no feedback. Responsive changes do not prompt. Automatic scope loss clears the
target and drafts, explains why, and creates no item.

### Feedback controls

- One revision comment form is available without selecting a session.
- Each session offers an ordinary session comment and **Not possible**.
- Revision/session comments require 1–2,000 trimmed plain-text characters.
- Not possible accepts an optional 1–2,000-character explanation or
  recommended date/time.
- Every textarea has a visible label and character count.
- The active form is disabled while its request is pending.
- One logical submission keeps its client submission UUID across an ambiguous
  retry; a new deliberate submission gets a new UUID.
- Success clears only that successful draft, announces the accepted result,
  and appends the returned item to same-link history without reloading the
  assignment projection.
- A stale-target rejection creates no item, clears the unauthorized target and
  its drafts with an explanation, and directs the reviewer to reload the
  browser page or reopen the link.
- Every successful deliberate submission appears as a separate immutable
  history item.
- Markup-looking input is displayed only as literal text.

Previously submitted items shown publicly are limited to items created through
the same still-valid link.

## Accessibility and responsive behavior

- Use native buttons, select elements, textareas, headings, lists, and regions.
- All controls have programmatic names and visible keyboard focus.
- Loading uses `aria-busy`; success/status uses a polite live region; errors
  use an alert.
- Identity, revision, expiry, session, feedback kind, count completeness,
  unavailable state, and throttling never rely on color, position, or motion.
- Logical DOM order matches visible order.
- At 320 CSS pixels and 200% text zoom, fixed context, modes, date controls,
  filters, calendar/list records, pane details, feedback controls, status, and
  close actions wrap without horizontal page scrolling.

## Non-effects

No lecturer action changes a course, session, room, assignment, revision state,
publication action, link expiry, or prior feedback. No feedback count, comment,
flag, missing response, or expiry changes which FS-013 lifecycle actions the
planner may invoke.
