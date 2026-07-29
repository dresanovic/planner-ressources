# Feature Specification: FS-015 Accountless Lecturer Token Review

**Working Branch**: `codex/fs-015-lecturer-token-review`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "Let a planner share one lecturer schedule with its corresponding lecturer through a secure temporary link and receive advisory comments and impossible-session flags without requiring a lecturer account."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-28

- Q: If every session is reassigned away from the lecturer while their link is still valid, what should happen? → A: Keep the link valid and show an empty schedule until expiry; new assignments appear automatically.
- Q: If the planner changes a session after the lecturer opens it but before feedback is submitted, what should happen? → A: Accept the feedback against the session's current state without requiring lecturer confirmation.
- Q: If the lecturer submits more than one impossible-session flag for the same session, what should happen? → A: Record every successful submission as a separate immutable feedback item.
- Q: What schedule and feedback scope should one lecturer link provide? → A: Show all sessions across the lecturer's assigned courses and allow a comment or impossible-session flag on each session, including recommended dates or times in comment text.
- Q: In which planner workflow status can an initial lecturer review request be sent? → A: Draft or Ready for review while the revision is Working; Ready for review is recommended but not required.
- Q: Where is planner authorization enforced for FS-015? → A: A trusted gateway/proxy protects planner pages and planner API routes; only the minimum accountless lecturer-review surface is publicly reachable.
- Q: Which network address is authoritative for unusable-link misuse limits? → A: The trusted gateway supplies the authoritative client address, discards client-provided forwarding values, and prevents direct backend access.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Share One Lecturer's Revision Safely (Priority: P1)

A planner selects one lecturer and one active Working semester revision,
chooses how many days the review should remain available, generates the review
link, and copies it for manual delivery. The corresponding lecturer opens the
link without an account and sees all teaching and exam sessions across their
assigned courses in that revision, and no sessions outside their lecturer
scope. Ready for review is the normal sharing point, but the planner may share
from Draft without creating a status gate.

**Why this priority**: Securely granting the minimum useful review scope is the
essential outcome on which all accountless feedback depends.

**Independent Test**: Prepare one Working revision containing assignments for
at least two lecturers across multiple courses, issue a link for one lecturer,
open it without an authenticated lecturer session, and verify that the review
contains every and only the selected lecturer's current assignments from the
selected revision.

**Acceptance Scenarios**:

1. **Given** a Working revision has sessions assigned to one lecturer, **When**
   the planner issues a link with no duration override and copies it, **Then**
   the planner receives a single temporary link scoped to that revision and
   lecturer, with an expiry exactly 72 hours after issuance.
2. **Given** the planner chooses a permitted shorter duration, **When** the link
   is issued, **Then** its exact expiry date, time, and time zone reflect that
   duration and are shown before the planner sends it.
3. **Given** a valid link for a lecturer whose revision contains assignments
   across multiple courses, **When** the link is opened, **Then** the reviewer
   sees the lecturer's assigned sessions across those courses and no session
   assigned solely to another lecturer.
4. **Given** a valid review, **When** the lecturer inspects any scoped session,
   **Then** they can read the schedule details needed to evaluate it but cannot
   add, change, remove, move, publish, or otherwise alter schedule data.
5. **Given** a planner has issued a link, **When** the copy action succeeds,
   **Then** the planner receives confirmation and a reminder that possession of
   the link grants access and that delivery remains the planner's manual
   responsibility.

---

### User Story 2 - Submit Advisory Schedule Feedback (Priority: P2)

While the link is valid, the lecturer can add a general comment about the
scoped revision, comment on a specific session, or mark a specific session as
not possible with an optional explanatory comment. A session comment may state
the dates or times the lecturer recommends for that scheduled block. The
planner can identify the exact revision and, where applicable, session to which
each item refers.

**Why this priority**: Structured, traceable feedback is the collaboration
value beyond merely viewing the schedule.

**Independent Test**: Through one valid link, submit a revision comment, a
session comment, and an impossible-session flag, then verify that each item is
retained with the correct intended lecturer-link attribution, revision,
session association, submission time, and advisory status and that no schedule
data changes.

**Acceptance Scenarios**:

1. **Given** a valid review link, **When** the lecturer submits a revision-level
   comment, **Then** the comment is retained against the intended lecturer and
   revision without creating an approval state.
2. **Given** a valid review link and a visible session, **When** the lecturer
   submits a session comment, **Then** the feedback identifies that exact
   session and revision even if the session is later edited.
3. **Given** a valid review link and a visible session, **When** the lecturer
   marks the session as not possible with or without an explanatory comment,
   **Then** one immutable impossible-session feedback item is retained for that
   session together with any supplied comment.
4. **Given** a valid review link and a visible session, **When** the lecturer
   comments with recommended dates or times for that session, **Then** the
   recommendation is retained as advisory text associated with that exact
   session and no schedule data changes automatically.
5. **Given** previously submitted feedback through the same still-valid link,
   **When** the lecturer reopens the review, **Then** the submitted items are
   visible as recorded feedback and cannot be mistaken for schedule changes.
6. **Given** a comment containing unsupported active or executable content,
   **When** it is submitted and later displayed, **Then** it remains inert text
   and cannot cause an action or reveal additional data.

---

### User Story 3 - End or Replace Access Immediately (Priority: P3)

The planner can revoke an active link at any time or replace it with a new link.
Expiry, revocation, replacement, abandonment, or supersession ends access
without revealing whether the link ever identified a lecturer or schedule.

**Why this priority**: A bearer link is safe enough for this slice only when the
planner can reliably end access and compromised or obsolete links disclose
nothing.

**Independent Test**: Exercise valid, expired, explicitly revoked, replaced,
abandoned-revision, superseded-revision, malformed, and unknown links and
verify that only the currently valid link exposes its minimum scope or accepts
feedback.

**Acceptance Scenarios**:

1. **Given** an active link, **When** the planner revokes it, **Then** every
   subsequent use of that link exposes no schedule, lecturer, revision, or
   feedback data and accepts no feedback.
2. **Given** one or more earlier links for the same lecturer and revision,
   **When** the planner issues a replacement, **Then** every earlier link for
   that lecturer/revision is revoked before the new link becomes available,
   leaving exactly one active link for that pair.
3. **Given** a link is valid immediately before its displayed expiry, **When**
   the expiry instant is reached, **Then** the same link stops exposing data
   and stops accepting feedback without a grace period.
4. **Given** a link's revision becomes Published and remains the current
   publication, **When** the lecturer uses the link before expiry, **Then** the
   link remains usable and clearly identifies the revision as Published.
5. **Given** a link's revision becomes abandoned or superseded, **When** any
   person next uses the link, **Then** access has ended and no scoped data is
   exposed.
6. **Given** an expired, revoked, replaced, malformed, unknown, or otherwise
   unusable link, **When** it is opened, **Then** the person sees the same safe
   unavailable outcome and a route to contact the planner, without learning
   which failure condition occurred.

---

### User Story 4 - Consider Feedback Without Losing Planner Control (Priority: P4)

The planner can review all feedback associated with the revision and sessions,
see the number of impossible-session flags in a prominent filter at the top of
the feedback area, narrow the view to flagged sessions, distinguish flags from
comments, and decide whether to revise, ignore the feedback, or publish.
Feedback status and the displayed review deadline remain informative and never
become an acceptance or publication gate.

**Why this priority**: The slice must support collaboration without weakening
the planner-controlled lifecycle delivered by FS-013.

**Independent Test**: Submit no feedback, positive comments, and
impossible-session flags in separate cases, verify the top filter count and
flagged-session result, and confirm that the planner can inspect an affected
session and publish the applicable Working revision in every case using the
unchanged FS-013 publication rules.

**Acceptance Scenarios**:

1. **Given** a revision has no lecturer feedback and its review deadline has
   passed, **When** the planner publishes it, **Then** publication is not
   blocked and no lecturer acceptance is requested.
2. **Given** a revision has one or more impossible-session flags or negative
   comments, **When** the planner publishes it, **Then** the feedback remains
   visible and advisory and publication is not blocked.
3. **Given** feedback refers to a session that the planner later edits, removes,
   or reassigns, **When** the planner reviews the feedback, **Then** the
   original revision/session association and the session context visible at
   submission remain understandable.
4. **Given** a link expires, is revoked, or is replaced, **When** the planner
   reviews its previously submitted feedback, **Then** the feedback remains in
   the linked revision history even though the link exposes no data.
5. **Given** a revision contains comments and impossible-session flags across
   multiple sessions, **When** the planner opens the feedback area and selects
   the impossible-session filter at its top, **Then** the filter shows the
   correct flag count and the result contains all and only the flagged
   sessions.
6. **Given** a revision contains no impossible-session flags, **When** the
   planner views or selects the impossible-session filter, **Then** its count is
   zero and the planner sees a clear empty result rather than missing or
   incomplete data.

### Edge Cases

- A planner attempts to issue a link for a lecturer with no session assigned in
  the selected revision; issuance is rejected with an explanation and does not
  create an empty or broader link.
- A public request attempts to reach a planner link-management or retained-
  feedback route; the trusted gateway rejects it without exposing planner data
  or allowing a planner action.
- A planner attempts initial issuance for a Published, superseded, abandoned,
  or historical revision; issuance is rejected because initial links are
  limited to the one active Working revision. A still-active link may be
  replaced after its bound revision becomes the Current Published revision.
- A session is newly assigned to the scoped lecturer after link issuance; it
  becomes visible because the link is scoped to the lecturer's current
  projection of that revision, not to an issuance-time session list.
- A session is reassigned away from the scoped lecturer; it ceases to be
  visible through the link, while previously submitted feedback retains its
  historical session context for the planner.
- Every session is reassigned away from the scoped lecturer; the link remains
  valid until its existing end condition, shows an explicit empty schedule,
  and automatically shows newly assigned sessions if assignments return before
  the link ends.
- A course has more than one eligible lecturer; each scheduled session remains
  assigned to one lecturer under the current schedule model, and a link exposes
  neither the other eligible lecturers nor their assigned sessions.
- Revocation and a feedback submission occur at nearly the same time; feedback
  is accepted only if the link was still valid when the submission was
  authoritatively evaluated.
- A scoped session's details change after the lecturer opens it but before
  feedback is submitted; if the session is still in scope, the feedback is
  accepted against its current state without a stale-version warning or
  lecturer reconfirmation. If it is no longer in scope, the submission is
  rejected.
- Replacement is requested twice nearly simultaneously; no more than one
  replacement remains active and every earlier link for the pair is unusable.
- The lecturer opens the link in multiple browser windows or devices; the same
  expiry, revocation, replacement, scope, and feedback rules apply everywhere.
- The review link is forwarded or exposed accidentally; possession alone may
  permit use while it remains valid, so the planner can revoke and replace it,
  and the review explains that the displayed lecturer identity is intended
  scope rather than proof of the person's identity.
- A submitted comment is blank after surrounding whitespace is removed or
  exceeds the allowed length; it is rejected without creating a partial
  feedback item. Unsupported active content within an otherwise valid comment
  is preserved only as inert visible text.
- The lecturer submits another impossible-session flag for a session already
  flagged through the link; if the submission is otherwise valid, it is
  retained as another immutable feedback item rather than replacing or
  modifying an earlier item.
- Repeated access or feedback requests exceed the misuse limits; excess
  requests are temporarily rejected without exposing additional data, while
  already accepted feedback remains unchanged.
- A caller supplies or alters a forwarding header; the trusted gateway removes
  or overwrites it, so the caller cannot select or evade the apparent request
  source used for misuse limits.
- Schedule or feedback data cannot be loaded completely; the review does not
  present incomplete information as complete and does not accept feedback
  against a session whose identity or current scope cannot be confirmed.
- Feedback is only partially available; the impossible-session filter MUST NOT
  present a definitive count or an empty result and instead identifies that the
  filtered result is unavailable or incomplete.

## Scope Boundaries

### In Scope

- One temporary review link for one lecturer's schedule projection within one
  FS-013 semester revision.
- The lecturer's teaching and exam sessions across every course assigned to
  that lecturer in the scoped revision.
- A comment or impossible-session flag on each scoped session, with recommended
  dates or times supplied as advisory comment text.
- Planner selection, duration choice, issuance, one-time presentation, copy,
  manual delivery, status inspection, revocation, and replacement.
- Reusable access for one, two, or three consecutive 24-hour periods, with
  three days as the default.
- Read-only schedule review, revision comments, session comments, and
  impossible-session flags.
- Traceable revision/session association, advisory planner review, and
  retention with revision history.
- A prominent planner filter at the top of the feedback area that displays the
  impossible-session flag count and narrows the result to flagged sessions.
- Explicit minimum-scope, privacy, expiry, secret-handling, misuse-control, and
  safe-failure behavior.

### Out of Scope

- A token covering more than one lecturer, a combined multi-lecturer review, or
  disclosure of other lecturers' schedules or identities.
- Multi-lecturer assignment of one scheduled session or any change to the
  existing one-lecturer-per-session schedule model.
- Automated email or message delivery, delivery tracking, reminders, or an
  external communication integration.
- Lecturer accounts, authentication, identity proofing, role management, or
  institutional single sign-on.
- Lecturer editing of any schedule, automatic application of suggestions, or
  lecturer-controlled lifecycle actions.
- Mandatory acceptance, approval states, quorum, publication blocking, or a
  requirement that the planner wait for feedback or a deadline.
- Attachments, rich-text authoring, threaded discussion, reactions, comment
  editing/deletion, or real-time collaboration.
- A general public schedule, bulk link issuance, one link spanning multiple
  revisions, or future authenticated lecturer workflows from FS-016.

## Requirements *(mandatory)*

### Functional Requirements

#### Review Scope and Issuance

- **FR-001**: Only a planner using the trusted gateway/proxy-protected planner
  workflow MUST be able to issue, copy, inspect, revoke, or replace a lecturer
  review link or inspect retained feedback. The gateway MUST reject public
  access to every planner page and planner API route while exposing only the
  minimum accountless lecturer-review surface required by this specification.
- **FR-002**: A new link MUST be issuable only for the one active Working
  revision in Draft or Ready for review state and for one lecturer who has at
  least one teaching or exam session assigned in that revision. A still-active
  link MAY be replaced for the same lecturer/revision pair after that revision
  becomes the Current Published revision. Ready for review SHOULD be presented
  as the normal initial-sharing point, but Draft MUST remain equally permitted
  and MUST NOT require an additional confirmation or approval gate.
- **FR-003**: Each link MUST be bound to exactly one stable revision identity
  and exactly one lecturer identity.
- **FR-004**: The accessible schedule MUST be derived from all and only the
  teaching and exam sessions currently assigned to the bound lecturer in the
  bound revision, regardless of how many courses those assignments span. If no
  sessions remain assigned, the still-valid link MUST show an explicit empty
  schedule and MUST automatically show newly assigned sessions if assignments
  return before the link ends.
- **FR-005**: The link MUST NOT grant access to another revision, a session
  assigned to another lecturer, planner-only data, or any planner action.
  Opening and using a valid link MUST NOT require a lecturer account, sign-in,
  credential, or separate identity assertion.
- **FR-006**: The planner MUST be able to choose a validity duration of one,
  two, or three consecutive 24-hour periods; if no choice is made, the duration
  MUST be three periods.
- **FR-007**: Before copying, the planner MUST see the scoped lecturer, revision,
  included course context, issuance time, exact expiry date/time/time zone, and
  current link status.
- **FR-008**: The link value MUST be presented only as part of successful
  issuance or replacement and MUST NOT be recoverable through later routine
  planner views; losing it requires replacement.
- **FR-009**: The planner MUST have an explicit copy action with a success or
  failure result that does not change the link's scope or duration.
- **FR-010**: Link issuance and copying MUST state that delivery is manual, that
  possession grants temporary access, that the link should be sent privately,
  and that suspected exposure should be handled by revocation or replacement.
- **FR-011**: At most one link for a given lecturer/revision pair MUST have
  active status at any instant.
- **FR-012**: Issuance for one lecturer/revision pair MUST NOT revoke or change
  a link for a different lecturer or a different revision.

#### Expiry, Revocation, and Replacement

- **FR-013**: A link MUST be usable repeatedly from successful issuance until
  the earliest of its exact expiry instant, explicit revocation, replacement,
  abandonment of the bound revision, or supersession of the bound revision.
- **FR-014**: Publishing the bound revision as the current publication MUST NOT
  by itself revoke the link or create an approval condition; the displayed
  revision state MUST reflect the publication.
- **FR-015**: At and after the exact expiry instant, the link MUST expose no
  schedule, lecturer, revision, or feedback data and MUST accept no feedback,
  without a grace period.
- **FR-016**: The planner MUST be able to revoke an active link immediately
  without deleting feedback already submitted through it.
- **FR-017**: Replacing a link MUST revoke every earlier link for the same
  lecturer/revision pair before the new link is made available.
- **FR-018**: Replacement MUST require a new permitted duration choice, default
  to three days if unchanged, and produce a new independently expiring link.
  Replacement MUST be rejected after the bound revision is abandoned or
  superseded.
- **FR-019**: Expiry, revocation, replacement, abandonment, and supersession
  MUST affect every open window and device using the ended link on its next
  access or submission.
- **FR-020**: An unusable link MUST produce one generic unavailable outcome
  that does not distinguish malformed, unknown, expired, revoked, replaced,
  abandoned, or superseded cases and does not confirm whether any lecturer or
  revision exists.
- **FR-021**: The generic unavailable outcome MUST provide a non-sensitive way
  to advise the person to contact the planner for a current link.

#### Security, Privacy, and Minimum Disclosure

- **FR-022**: A link secret MUST be infeasible to guess, with at least 128 bits
  of effective unpredictability, and MUST carry no readable lecturer,
  revision, course, institution, or expiry information.
- **FR-023**: The full link secret MUST NOT appear in routine activity history,
  audit displays, feedback records, analytics, error details, planner lists, or
  any destination reached through ordinary review navigation.
- **FR-024**: Ordinary use of the review MUST NOT disclose the link secret to
  an external destination; any navigation away from the review MUST require an
  explicit action that warns the reviewer before leaving.
- **FR-025**: The review MUST display only the intended lecturer's name, the
  semester and revision identity/state, course title and code, session type,
  date, start/end time, room name, cohort/class name, and the scoped feedback
  already submitted through that link, including its kind, text, associated
  session where applicable, and submission time.
- **FR-026**: The review MUST NOT expose student-level data, lecturer contact
  data, another lecturer's identity, unassigned sessions, planner notes,
  internal history, other revisions, administrative controls, or fields not
  required to identify and evaluate a scoped session.
- **FR-027**: A review MUST NOT identify other lecturers who are eligible for
  the same course or expose sessions assigned to those other lecturers.
- **FR-028**: The review MUST identify the lecturer whose schedule is in scope
  and clearly state that this is the link's intended identity, not proof that
  the current person is that lecturer.
- **FR-029**: Link validity and session scope MUST be evaluated again before
  every protected view and every feedback submission; a previously opened
  screen MUST NOT authorize later access after scope or validity changes. A
  change to an in-scope session's details MUST NOT require stale-version
  rejection or lecturer reconfirmation; accepted feedback applies to the
  session's current state at submission.
- **FR-030**: When current scope or required data cannot be confirmed, the
  review MUST fail closed, expose no unconfirmed schedule data, and accept no
  feedback against an unconfirmed session.

#### Read-Only Review and Feedback

- **FR-031**: The lecturer review MUST be read-only with respect to schedule
  content and lifecycle state; its only permitted data-changing actions are
  creation of in-scope feedback items.
- **FR-032**: A valid reviewer MUST be able to submit a plain-text comment about
  the bound revision without selecting a session.
- **FR-033**: A valid reviewer MUST be able to submit a plain-text comment about
  one currently scoped session.
- **FR-034**: A valid reviewer MUST be able to mark one currently scoped
  session as not possible and MAY include one plain-text explanatory or
  alternative-suggestion comment, including recommended dates or times when
  the lecturer could teach that session.
- **FR-035**: Every feedback item MUST identify the bound revision, intended
  lecturer, feedback kind, submission time and time zone, originating link
  record without retaining its secret, and the session when the item is
  session-specific.
- **FR-036**: Session-specific feedback MUST preserve enough of the session
  context current when the submission is accepted for the planner to
  understand it after the session is later edited, removed, or reassigned.
- **FR-037**: Feedback shown to the planner MUST be labeled as submitted through
  the link intended for the named lecturer and MUST NOT be represented as an
  authenticated identity claim.
- **FR-038**: A submitted feedback item MUST be immutable in this slice; a valid
  reviewer MAY submit additional items, including another impossible-session
  flag for the same session. Every successful submission MUST create a separate
  item and MUST NOT edit, replace, merge with, or delete an existing item.
- **FR-039**: After surrounding whitespace is removed, a comment MUST contain
  at least one non-whitespace visible character, MUST be limited to 2,000
  visible characters, and MUST treat any active or executable content as inert
  text in every display.
- **FR-040**: Impossible-session feedback MUST remain visibly distinguishable
  from ordinary comments without relying on color alone.
- **FR-041**: A feedback submission MUST produce an unambiguous accepted or
  rejected result and MUST NOT create duplicate items from one submission.
- **FR-042**: Previously submitted in-scope feedback MUST remain visible through
  the same link while it is valid, without exposing feedback from another
  lecturer or revision.

#### Planner Control, Advisory Status, and Retention

- **FR-043**: The planner MUST be able to review feedback grouped by its
  revision and, where applicable, session, with impossible-session flags
  distinguishable from comments.
- **FR-044**: A prominent filter at the top of the planner feedback area MUST
  display the total number of impossible-session flags in the selected revision
  and allow the planner to show all and only sessions with at least one such
  flag. The filter, its count, and its selected state MUST be keyboard-operable,
  available to assistive technology, and understandable without color alone.
- **FR-045**: The impossible-session filter count MUST count feedback flag
  items, while the filtered result MUST list each affected session once even
  when that session has multiple flags. Each result MUST provide a direct path
  to inspect that session's feedback and invoke the existing planner-authorized
  session workflow without changing the schedule automatically.
- **FR-046**: The planner MUST be able to clear the impossible-session filter
  and return to the complete feedback view without changing feedback, schedule
  data, link state, or revision state.
- **FR-047**: A complete result with no impossible-session flags MUST show a
  zero count and an explicit empty filtered state. Partial or unavailable
  feedback MUST NOT be represented as zero or as a complete empty result.
- **FR-048**: Missing feedback, a passed review deadline, comments,
  impossible-session flags, and any other feedback state MUST remain advisory
  and MUST NOT block, delay, require confirmation for, or otherwise change an
  FS-013 lifecycle transition.
- **FR-049**: The review deadline MUST be presented only as the access expiry
  and MUST NOT be labeled or counted as an acceptance, approval, response, or
  publication deadline.
- **FR-050**: Publication MUST NOT delete, resolve, approve, or otherwise change
  feedback automatically.
- **FR-051**: Feedback MUST remain associated with the bound revision history
  for as long as that revision history is retained under FS-013, including
  after link expiry, revocation, replacement, publication, abandonment, or
  supersession.
- **FR-052**: Ended links MUST expose no retained feedback; retained feedback is
  available only through the existing planner-authorized revision history.
- **FR-053**: This slice MUST NOT introduce an independent feedback purge,
  acceptance decision, resolution workflow, lecturer account, or publication
  state.

#### Misuse Controls and Activity Evidence

- **FR-054**: For one apparent request source, 20 unusable-link attempts within
  any rolling five-minute interval MUST cause subsequent link attempts from
  that source to be rejected for at least ten minutes without revealing
  whether a later link was valid. The apparent request source MUST be based on
  the authoritative client address supplied by the trusted gateway. The
  gateway MUST discard or overwrite caller-provided forwarding values, and
  direct access that bypasses the gateway MUST be prevented. An application
  restart, deployment restart, or worker replacement MUST NOT shorten an active
  rejection period or discard attempts that remain within the rolling
  five-minute interval.
- **FR-055**: For one valid link, more than 120 protected view requests within
  any rolling five-minute interval MUST be temporarily rejected for at least
  five minutes without ending the link or changing accepted feedback.
- **FR-056**: For one valid link, more than 10 feedback submissions within any
  rolling minute or more than 60 within any rolling hour MUST be temporarily
  rejected without creating partial or duplicate feedback and without
  extending the link's expiry.
- **FR-057**: A normal review path below the stated misuse thresholds MUST NOT
  be rejected by the misuse controls.
- **FR-058**: Link issuance, expiry, revocation, replacement, successful access,
  rejected access, accepted feedback, rejected feedback, and misuse-limit
  activation MUST leave time-ordered activity evidence sufficient to verify
  the event type, affected non-secret link record, revision, intended lecturer
  where known, and event time.
- **FR-059**: Activity evidence MUST exclude the full link secret, comment body,
  unnecessary schedule content, and network identifiers beyond the minimum and
  duration needed to enforce the stated misuse limits. A network identifier
  used only to enforce unusable-link limits MUST cease to be retained no later
  than 15 minutes after the latest relevant attempt.
- **FR-060**: Repeated invalid, malformed, expired, revoked, replaced, or
  excessive requests MUST NOT change schedule data, revision lifecycle state,
  existing feedback, link expiry, or another link's availability.

#### Accessibility and Responsive Review

- **FR-061**: The complete lecturer review and feedback flow MUST be operable
  with a keyboard alone, with logical visible focus and no pointer-only action.
- **FR-062**: Revision identity/state, expiry, session identity, feedback kind,
  submission result, and unavailable or throttled state MUST be available to
  assistive technology and MUST NOT rely on color, position, or motion alone.
- **FR-063**: At a viewport width equivalent to 320 CSS pixels and at text zoom
  up to 200%, all scoped session details, feedback controls, status messages,
  and expiry information MUST remain readable and operable without loss of
  content or horizontal page scrolling.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production behavior for
  each implemented user story wherever automated testing is practical; any
  exception MUST be justified with a manual verification path in the plan.
- **TR-002**: Scope tests MUST cover at least three lecturers, two revisions,
  multi-course assignments, teaching and exam sessions, a course with multiple
  eligible lecturers, and assignment changes, verifying FR-001 through FR-012
  with no cross-lecturer or cross-revision disclosure.
- **TR-003**: Lifecycle tests MUST exercise every boundary and race described in
  FR-013 through FR-021, including the instant immediately before and at
  expiry, revocation concurrent with submission, simultaneous replacement,
  publication, abandonment, and supersession.
- **TR-004**: Security and privacy tests MUST verify FR-022 through FR-030
  against valid, malformed, guessed, copied, forwarded, expired, revoked, and
  replaced links and must inspect every named routine surface for secret or
  out-of-scope data exposure.
- **TR-005**: Feedback tests MUST verify every feedback kind, association,
  session change before and after submission, current-state association,
  validation boundary, repeat submission, duplicate attempt, and inert-content
  case in FR-031 through FR-042.
- **TR-006**: Planner-control and retention tests MUST verify FR-043 through
  FR-053 for no feedback, comments, one and multiple flags per session,
  exact flag-item counts, distinct filtered sessions, clear-filter behavior,
  complete zero results, partial/unavailable feedback, passed deadlines, each
  link-ending condition, and every applicable FS-013 publication path.
- **TR-007**: Misuse tests MUST verify each threshold immediately below, at, and
  above its stated boundary and verify all non-mutation and minimum-evidence
  requirements in FR-054 through FR-060.
- **TR-008**: Accessibility tests MUST verify FR-061 through FR-063 with
  keyboard-only use, the supported screen-reader/browser combination, 200%
  text zoom, and a viewport equivalent to 320 CSS pixels.
- **TR-009**: Failure-state tests MUST verify initial loading failure, partial
  data, stale open views, copy failure, submission failure, and recovery
  without false success, data leakage, duplicate feedback, or schedule changes.
- **TR-010**: Scope tests MUST confirm the absence of multi-lecturer links,
  automated delivery, lecturer accounts, schedule editing, feedback
  editing/deletion, approval gates, publication blocking, attachments,
  threaded discussion, and authenticated FS-016 behavior.

### Key Entities

- **Lecturer Review Link Record**: The non-secret lifecycle record for one
  temporary access grant, including its stable identity, bound lecturer,
  bound revision, issuance time, exact expiry, duration, status, replacement
  relationship, and lifecycle event times.
- **Lecturer Schedule Projection**: The current read-only set of teaching and
  exam sessions in the bound revision that are assigned to the bound lecturer,
  together with only the identifying schedule fields permitted by this slice.
- **Scheduled Session**: One teaching or exam occurrence for one course at one
  specific date and time. A teaching session contains one or more teaching
  units; for example, one three-unit block on one date is one session. Two
  separately scheduled blocks for the same course on the same date are two
  sessions.
- **Review Feedback Item**: An immutable advisory revision comment, session
  comment, or impossible-session flag, including intended lecturer-link
  attribution, submission time, revision association, optional session
  association, and captured session context where applicable.
- **Review Activity Event**: Minimum non-secret evidence of a link lifecycle,
  access, feedback, failure, or misuse-control event used to verify security
  and planner control without retaining the link secret or comment body.
- **Review Access Context**: The validity, current revision state, current
  lecturer assignment scope, expiry, and misuse-control state evaluated for one
  protected view or feedback submission.
- **Planner Feedback Filter Context**: The selected revision's complete
  feedback availability, impossible-session flag-item count, selected
  all-feedback or impossible-session view, and distinct affected-session
  result used for non-mutating planner navigation.

## Dependencies

- **FS-013 — Versioned Review and Publication Lifecycle** supplies the stable
  semester revision identity, the one active Working revision, Draft and Ready
  for review states, immutable publication, supersession, abandonment, and
  planner-controlled publication behavior.
- Existing schedule data supplies lecturer assignments, course context,
  teaching sessions, and exam sessions used to derive the lecturer projection.
- No email, messaging, identity-provider, account, or external publication
  integration is required by this slice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of an acceptance matrix containing at least three
  lecturers, two revisions, 20 sessions, multi-course assignments, a course
  with multiple eligible lecturers, assignment changes, complete removal, and
  later restoration of a lecturer's assignments, a valid link displays every
  and only the sessions currently assigned to its one bound lecturer in its one
  bound revision and shows an explicit empty schedule when that set is empty.
- **SC-002**: In 100% of valid issuance cases, the planner can choose the
  duration, issue, and copy a correctly labeled link in no more than 60 seconds
  and no more than five deliberate interactions from selecting the lecturer
  and revision.
- **SC-003**: In 100% of expiry, revocation, replacement, abandonment,
  supersession, malformed, and unknown-link acceptance cases, the link exposes
  zero schedule, lecturer, revision, or feedback fields and accepts zero
  feedback items.
- **SC-004**: In 100% of feedback acceptance cases, every accepted item appears
  exactly once for the planner with the correct revision, intended lecturer,
  kind, submission time, and session association or revision-level
  classification.
- **SC-005**: In 100% of no-feedback, passed-deadline, negative-comment, and
  impossible-session cases, all otherwise permitted FS-013 publication
  transitions remain available and complete without lecturer approval.
- **SC-006**: In a moderated usability review with at least 10 representative
  lecturers or designated acceptance reviewers, at least 90%, rounded up to
  the next whole participant, open the link, identify the revision and expiry,
  find a named session, and submit the requested feedback correctly within
  three minutes without guidance.
- **SC-007**: In the same review, 100% of participants can state that the link
  shows the intended lecturer but does not authenticate the person using it,
  and at least 90% correctly identify that feedback is advisory rather than an
  approval requirement.
- **SC-008**: At the exact validity boundaries, 100% of links work immediately
  before expiry and fail closed at or after expiry; replacement and explicit
  revocation make every ended link unusable on its next request.
- **SC-009**: In 100% of misuse acceptance cases, the stated access and
  submission thresholds are enforced at their exact boundaries, accepted
  feedback remains unchanged, and no schedule, lifecycle, expiry, or unrelated
  link state changes. Acceptance cases include an application restart during an
  active ten-minute unusable-link rejection period.
- **SC-010**: For a scoped lecturer schedule containing up to 100 teaching and
  exam sessions and 200 retained feedback items, at least 95% of valid review
  openings present a complete usable schedule within three seconds and 100%
  present either that result or a safe actionable state within ten seconds.
- **SC-011**: For the same reference scope, at least 95% of feedback submissions
  present an accepted or rejected result within two seconds and 100% present
  one within five seconds without duplicate creation.
- **SC-012**: In 100% of secret-exposure inspections, the full link secret is
  absent from every routine activity, audit, feedback, analytics, error,
  planner-list, and external-navigation surface named in this specification.
- **SC-013**: In 100% of retention cases, accepted feedback remains available
  to the planner for the lifetime of its FS-013 revision history and remains
  inaccessible through every ended link.
- **SC-014**: In 100% of keyboard, supported assistive-technology, 200% text
  zoom, and 320-CSS-pixel acceptance paths, all review information and feedback
  actions remain understandable, reachable, and operable without exposing
  extra data.
- **SC-015**: In 100% of planner filter acceptance cases, the displayed
  impossible-session count equals the number of flag items in the selected
  revision, activating the filter exposes every affected session exactly once
  in one interaction, each affected session's feedback and existing planner
  workflow are reachable in one additional interaction, and clearing the
  filter restores the complete feedback view without changing any domain data.

## Assumptions

- "One lecturer schedule" means the single-lecturer projection of one
  semester-wide FS-013 revision. It contains all teaching and exam sessions
  assigned to that lecturer, potentially across multiple courses, and never
  expands to a combined multi-lecturer review.
- The current schedule model assigns exactly one lecturer to each teaching or
  exam session. Extending a single session to multiple assigned lecturers is a
  separate scheduling-model change and is outside FS-015.
- New links are issued only for the active Working revision in Draft or Ready
  for review. A link remains usable if that same revision is published and is
  still current and may then be replaced, but becomes unusable and cannot be
  replaced if the revision is abandoned or superseded. Ready for review is the
  recommended workflow point for sharing, but it remains informative and
  optional under FS-013; Draft sharing is allowed without another gate.
- A configured day is one consecutive 24-hour period from issuance. The allowed
  choices are one, two, or three periods, and the default is three; this
  resolves shorter-expiry configuration without adding arbitrary date picking
  or long-lived access.
- Replacement immediately revokes every earlier link for the same
  lecturer/revision pair and leaves exactly one active replacement. Links for
  other pairs are unaffected.
- Because no lecturer account or identity proofing is in scope, the lecturer
  name is the intended identity attached by the planner. Feedback attribution
  explicitly records that it came through that lecturer's link rather than
  claiming the named person was authenticated.
- Possession of the bearer link is sufficient for temporary use. The slice
  mitigates accidental disclosure through minimum scope, short expiry,
  one-time link presentation, safe secret handling, warnings, misuse controls,
  revocation, and replacement; it does not claim to prevent an intended
  recipient from deliberately forwarding the link.
- The current assignment set within the bound revision determines what the link
  can display at each access. Feedback preserves its submission-time session
  context so later edits or assignment changes do not make historical feedback
  ambiguous. If session details change while a review remains open, accepted
  feedback uses the session's current state without stale-version
  reconfirmation. Removing every assignment does not end the link: it shows an
  empty schedule and automatically reflects assignments that return before
  expiry, revocation, replacement, abandonment, or supersession.
- Feedback is retained with the associated FS-013 revision history. This slice
  introduces no separate deletion or anonymization workflow and no extension
  of revision-history retention.
- Comments are plain text without attachments, rich formatting, threads,
  reactions, or editing. Recommended dates, times, and other suggested
  alternatives may be written in the session comment but never alter schedule
  data automatically.
- Review expiry is an access-security boundary and an informational deadline,
  not an approval gate. The planner always retains the publication authority
  and choices defined by FS-013.
- A trusted gateway/proxy is the authoritative planner access boundary. It
  protects every planner page and planner API route and exposes only the
  minimum accountless lecturer-review surface publicly. This slice adds no
  application-level planner authentication, account, or role changes.
- The same trusted gateway is the authoritative client-address boundary for
  unusable-link misuse limits. It removes or overwrites caller-provided
  forwarding values, supplies the address used by the application, and is the
  only network path permitted to reach the backend.
- The product owner supplies at least 10 representative lecturers or designated
  acceptance reviewers for the moderated success criteria. Automated work may
  finish beforehand, but those criteria cannot be reported as passed without
  actual participants.
