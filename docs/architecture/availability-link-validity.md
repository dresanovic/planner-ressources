# Architecture Exploration: Availability-Link Validity

## Status

Accepted

## Context

A planner needs to issue a separate accountless link through which one active
lecturer can submit whole-day unavailability for one semester exactly once.
The link is separate from the FS-015 schedule-review link because availability
is collected before a schedule revision or assigned session necessarily
exists.

The validity rule should minimize implementation complexity while retaining a
safe bounded lifetime for a bearer link.

## Current system

FS-015 review links already provide:

- cryptographically random bearer secrets stored only as digests;
- exact issue and expiry instants;
- a default duration of three consecutive 24-hour periods;
- planner-selectable durations of one, two, or three days;
- active, expired, revoked, replaced, and revision-ended states;
- planner revocation and replacement;
- one active link per lecturer and revision;
- safe public failure behavior and misuse controls.

The implemented validation, database constraints, API contracts, UI, and tests
explicitly support only one-, two-, or three-day review-link durations.
Availability links require a different lecturer-and-semester scope and end
after their one permitted submission.

## Goals

- Permit exactly one availability submission.
- Prevent forgotten bearer links from remaining usable indefinitely.
- Let the planner revoke or replace an unused link.
- Reuse implemented token-security and expiry behavior where appropriate.
- Minimize new states, controls, validation paths, and test combinations.

## Constraints

- Only planner users may issue, revoke, or replace availability links.
- Public possession of the link grants its bounded capability without identity
  proof.
- Submission ends the link immediately.
- The availability link must not expose schedule-review capabilities.
- Exact permissions must be enforced by the backend.

## Decision drivers

1. Security of an accountless bearer link.
2. Smallest implementation and test surface.
3. Consistency with FS-015.
4. Understandable planner behavior.
5. Recovery when a lecturer misses the deadline or a date is rejected.

## Assumptions

- Three consecutive 24-hour periods normally provide enough time for the
  lecturer to submit dates.
- A planner can issue a replacement when the original link expires or when a
  rejected date needs another submission.
- Arbitrary dates, times, or long validity periods are not a current product
  need.

## Options considered

### Option 1: Fixed 72-hour validity

#### Description

Every availability link expires exactly 72 hours after issuance. The planner
does not choose a duration. The link ends earlier upon submission, revocation,
or replacement.

#### Benefits

- Reuses the existing FS-015 default and exact-expiry semantics.
- Requires no duration selector or duration-choice validation in the new
  planner workflow.
- Has one primary expiry test path instead of three.
- Keeps forgotten bearer links bounded.
- Replacement provides a simple recovery path.

#### Disadvantages

- The planner cannot intentionally choose a shorter access window.
- A lecturer who misses the window requires a replacement link.

#### Risks

- The fixed duration may later prove unsuitable for an institution's process.
  Changing to the existing one-to-three-day choice remains a small,
  reversible extension.

### Option 2: Planner-selectable one-, two-, or three-day validity

#### Description

Availability links reuse the same duration choices and three-day default as
FS-015 review links. The link still ends earlier after its one submission,
revocation, or replacement.

#### Benefits

- Provides consistent planner interaction across both token workflows.
- Reuses the established duration domain and validation limits.
- Allows a planner to reduce exposure when a shorter response window is
  sufficient.

#### Disadvantages

- Adds a selector, API field, validation, persistence, display, and test
  combinations to the new workflow.
- The flexibility does not improve the confirmed one-submission outcome.

#### Risks

- Low architectural risk, but avoidable product and test surface if duration
  choice is not genuinely needed.

### Option 3: Valid until submission or planner action

#### Description

The link has no automatic time expiry. It remains usable until the lecturer
submits once or the planner revokes or replaces it.

#### Benefits

- Removes deadline selection and expiry-related user confusion.
- A lecturer does not need a replacement merely because time passed.

#### Disadvantages

- Forgotten or leaked bearer links remain usable indefinitely.
- Requires planners to remember manual cleanup.
- Diverges from the established accountless token security model.
- Makes retained active-link cleanup and operational monitoring more
  important, not less.

#### Risks

- Unbounded public access is inappropriate for a link that represents one
  lecturer and semester.
- The apparent removal of expiry logic increases security and operational
  complexity.

## Comparison

| Driver | Fixed 72 hours | Selectable 1–3 days | Until submission/revocation |
| --- | --- | --- | --- |
| Implementation complexity | Low | Low–medium | Medium |
| New UI and validation | Minimal | Additional | Minimal UI, more lifecycle risk |
| Security exposure | Bounded | Bounded | Unbounded |
| Consistency with FS-015 | Uses default | Full consistency | Diverges |
| Planner flexibility | Low | Medium | Medium |
| Recovery | Replace link | Replace link | Revoke/replace manually |
| Reversibility | Easy to extend | Easy to simplify | Harder security migration |

An arbitrary date/time or validity longer than three days is not a viable
current option. It adds timezone, range, policy, display, and testing decisions
without a confirmed need.

## Recommendation

Use **fixed 72-hour validity** for the first availability slice.

This is the smallest safe option. It reuses the implemented three-day default
and exact-expiry pattern but avoids adding duration choice to a one-submission
workflow. The planner can revoke or replace the link, and rejection of one date
can be handled through a fresh 72-hour link.

The decision is reversible: selectable one-, two-, or three-day validity can be
added later using already established FS-015 behavior if users demonstrate a
need.

## Consequences

- Availability-link issuance requires no duration field or selector.
- Every issued link displays its exact expiry instant and time zone.
- Successful submission ends the link immediately.
- Expiry, revocation, or replacement ends access without exposing which
  condition occurred publicly.
- A planner issues a new link after expiry or when a rejected date needs another
  submission.
- Availability and schedule-review links retain separate scopes even though
  they may share low-level secret, digest, safe-failure, and misuse-control
  utilities.

## Validation required

- Later specification must verify that successful one-time submission and
  concurrent replacement/revocation cannot leave the link usable.

## Open questions

- Whether the planner needs a visible reminder when an unused link approaches
  expiry; this is not required for the first slice.

## Handoff to specification

Define availability links as planner-issued, lecturer-and-semester-scoped,
single-submission bearer links with fixed 72-hour expiry, immediate termination
after submission, and planner revocation/replacement. Reuse proven FS-015
security behavior without merging the distinct token capabilities or requiring
a common persisted link entity.
