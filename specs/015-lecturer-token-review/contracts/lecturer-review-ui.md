# FS-015 UI Contract

## Entry points

### Planner

The existing Schedule navigation adds one child destination:
**Lecturer reviews**. It is visible only inside the normal planner shell and
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
the public page or planner application. The planner shell, global planner
navigation, Calendar workspace, Versions, Exams, findings, and administrative
data are never rendered or loaded on this entry path.

## Planner Lecturer reviews destination

### Required order

1. Page heading and selected revision identity/state.
2. Prominent impossible-session filter at the top of the feedback area.
3. Feedback result/status.
4. Link management for lecturers assigned in the revision.

### Impossible-session filter

- A native button exposes the visible label **Not possible**, a non-color icon
  or word marker, its selected state through `aria-pressed`, and the flag-item
  count.
- A complete result displays the exact count, including `0`.
- A partial or unavailable result displays no numeric zero and clearly says
  the count is incomplete or unavailable.
- Activating the filter lists every affected session exactly once and shows all
  flag/comment items inside its session group.
- The filter count is the number of impossible flag items, not the number of
  session groups.
- Clearing the filter restores all feedback and changes no domain data.
- Filter activation moves focus to the result heading/status; clearing keeps a
  predictable focus path.

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
switches to Calendar, selects the authoritative revision/occurrence, and opens
the existing planner session workflow. If the session was removed, reassigned,
or cannot be mapped, the group retains its historical context and explains
that the current workflow is unavailable.

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
If a session changed or left scope while the overall link remains valid, the
page discards the stale projection and reloads before accepting another
submission.

### Review heading

A complete valid review shows:

- intended lecturer name;
- explicit statement that the name is intended scope and does not authenticate
  the person using the link;
- semester, revision label, and Draft/Ready/Published state;
- access expiry date/time/time zone, labeled as access expiry rather than an
  approval deadline;
- read-only and advisory-feedback explanation;
- explicit **Refresh schedule** action.

### Schedule

Courses are grouped by stable code and title. Each teaching or exam session
shows only:

- course title/code;
- session type;
- date;
- start and end time with time zone;
- room name;
- cohort/class name.

The page never shows other lecturers, lecturer contacts, student data,
unassigned sessions, planner notes, findings, internal history, other
revisions, or planner controls. If the complete current projection has no
assigned sessions, it shows an explicit valid empty schedule and keeps the
revision-comment and refresh actions available.

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
  and refreshes the review/history.
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
- At 320 CSS pixels and 200% text zoom, content uses one column, wraps long
  course names and dates, has no fixed card width, and causes no horizontal
  page scrolling.

## Non-effects

No lecturer action changes a course, session, room, assignment, revision state,
publication action, link expiry, or prior feedback. No feedback count, comment,
flag, missing response, or expiry changes which FS-013 lifecycle actions the
planner may invoke.
