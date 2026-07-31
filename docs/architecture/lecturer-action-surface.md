# Architecture Exploration: Lecturer Action Surface

## Status

Accepted

## Context

The accountless lecturer workflow is expanding from schedule feedback to
pre-planning unavailability submissions and calendar export. Planner users need
one intuitive place to find lecturer-originated work that requires attention.
Authenticated planner and lecturer access remains later scope under FS-016.

The decision is whether to extend the existing lecturer-review area into a
lecturer-specific coordination surface or introduce a generic Action Center
that also aggregates planning conflicts, capacity warnings, generation
failures, and other operational issues.

## Current system

- The React application has a Schedule destination named `Lecturer reviews`.
- `LecturerReviewManagement` handles review-link lifecycle and retained
  lecturer feedback.
- The calendar workspace separately presents operational summary cards for
  conflicts, capacity issues, planning failures, and schedules needing review.
- Academic Data has existing lecturer editing and dated-unavailability
  components.
- FS-016 proposes authenticated planner and lecturer access but does not yet
  define credentials, role administration, or token/account coexistence.
- No generic notification or action-item aggregate currently exists.

## Goals

- Give planners one clear place to handle lecturer comments, impossible-session
  flags, and unavailability submissions.
- Reuse existing lecturer, availability, review, calendar, list, and detail
  components.
- Preserve strict token scope and planner-only mutation permissions.
- Allow later authenticated lecturer access to reuse the same domain workflows.
- Avoid speculative infrastructure that is not required by the current
  lecturer collaboration outcomes.

## Constraints

- The project constitution requires the simplest design that satisfies current
  approved requirements.
- Accountless token access must not expose planner-only controls or data.
- Planner authorization and lecturer token scope must be enforced by backend
  operations, not only by hidden UI.
- Existing calendar operational summaries remain useful and must not be
  duplicated with inconsistent counts or resolution semantics.

## Decision drivers

1. Simplicity and delivery risk.
2. Clear user terminology and workflow ownership.
3. Security and future role-based authorization.
4. Reuse of implemented components and read models.
5. Avoidance of duplicated or inconsistent issue state.
6. Evolution toward authenticated lecturer access.

## Assumptions

- The current expansion introduces lecturer-originated work, not new categories
  of planner, student, or external-system requests.
- Conflicts, capacity issues, and generation failures remain derived planning
  conditions rather than messages with a shared read/unread lifecycle.
- Future authenticated lecturers will initially reuse schedule review,
  feedback, calendar export, and personal unavailability workflows.

## Options considered

### Option 1: Lecturer-specific coordination surface

#### Description

Rename and broaden the existing `Lecturer reviews` destination to
`Lecturer coordination`. It contains review-link management, lecturer feedback,
impossible-session flags, availability-link management, and submitted
unavailable dates requiring planner decisions. Calendar conflicts, capacity
issues, and generation failures remain in the existing operational summaries.

Authenticated lecturers later receive role-scoped `My schedule`, `My feedback`,
and `My unavailable dates` views backed by the same domain operations and
components.

#### Benefits

- Reuses the existing destination, components, feedback read model, and
  lecturer domain context.
- Keeps accountless and future authenticated lecturer workflows aligned.
- Requires no generic notification entity, unread model, cross-domain
  resolution contract, or new aggregation infrastructure.
- Makes security boundaries easier to understand and test.
- Preserves current operational-summary behavior without duplication.

#### Disadvantages

- Planner users continue to use two attention surfaces: lecturer coordination
  and calendar operational summaries.
- A later generic Action Center would require a separate slice if additional
  roles or action types create a demonstrated need.

#### Risks

- The destination could become crowded unless lecturer feedback and
  availability submissions have clear filters and sections.
- Naming must make clear that the area includes more than schedule reviews.

### Option 2: Generic Action Center now

#### Description

Create one cross-product Action Center that aggregates lecturer feedback,
unavailability submissions, conflicts, capacity issues, planning failures, and
other records needing attention. Define a shared item contract with type,
audience, severity, status, target, timestamps, and resolution behavior.

#### Benefits

- Provides one planner destination for every known actionable condition.
- Could later show role-specific queues for authenticated users.
- Supports common filtering and prioritization if all included items share
  meaningful action semantics.

#### Disadvantages

- Requires a new cross-domain aggregation contract and UI.
- Derived planning conditions do not naturally share the same lifecycle as
  submitted lecturer requests.
- Introduces difficult questions about read versus resolved state,
  deduplication, prioritization, partial data, history, ownership, and
  authorization.
- Risks duplicating existing calendar summaries or making their counts disagree
  with the Action Center.

#### Risks

- Scope expands beyond the three lecturer outcomes currently being defined.
- A speculative shared abstraction may harden before authenticated roles and
  their actual queues are known.
- Security and completeness failures become cross-domain rather than isolated.

## Comparison

| Driver | Lecturer coordination | Generic Action Center |
| --- | --- | --- |
| Current delivery complexity | Medium | High |
| Component reuse | High | Medium |
| Security boundary clarity | High | Medium |
| Fits current lecturer scope | High | Medium |
| Immediate single-inbox experience | Partial | High |
| Future authenticated lecturer reuse | High | High |
| Risk of speculative abstraction | Low | High |
| Later extensibility to unrelated roles | Medium | High |

## Recommendation

Use **Lecturer coordination** now.

This is the simpler evolutionary architecture and is fully compatible with
future authenticated lecturer access. Authentication changes how identity and
authorization are established; it does not require unrelated operational
conditions to share one notification model.

The planner surface should aggregate all lecturer-originated actionable work:
schedule comments, impossible-session flags, and submitted unavailable dates.
The lecturer-facing token or authenticated view should use intuitive
self-service labels such as `My schedule` and `My unavailable dates`.

Keep conflicts, capacity issues, generation failures, and other derived
planning conditions in the established calendar operational summaries. Add a
generic Action Center only through a later requirements slice when multiple
roles or additional request types demonstrate a real need for a shared queue.

## Consequences

- The existing `Lecturer reviews` destination is broadened and renamed rather
  than supplemented by another planner navigation destination.
- Availability submissions gain pending counts and filters within lecturer
  coordination.
- Existing operational summary cards remain authoritative for planning issues.
- FS-016 can replace token-derived lecturer identity with authenticated
  identity while reusing the same lecturer workflows.
- No generic notification table or common read/unread lifecycle is required for
  the current slices.

## Validation required

- Verify during later specification that reused components expose only actions
  permitted for the current access mode.

## Open questions

- Whether a future authenticated planner needs a personal assigned queue rather
  than institution-wide lecturer coordination.
- Which additional roles or external systems, if any, would create actionable
  requests suitable for a generic Action Center.
- Whether future action prioritization, assignment, read/unread state, or
  service-level deadlines are required.

## Handoff to specification

- FS-015 should broaden the lecturer review presentation and planner feedback
  access while preserving advisory feedback semantics.
- The iCalendar export slice should reuse the lecturer-scoped schedule
  projection.
- The unavailability slice should use a separate one-use lecturer-and-semester
  token, per-date planner decisions, and the existing dated-unavailability
  domain behavior for approved dates.
- FS-016 should reuse these workflows under authenticated identity rather than
  redesigning them around a speculative generic notification model.
