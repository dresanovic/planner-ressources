# I-014 code review

## Scope and context

Reviewed the implementation/test content identified by `change-manifest.json`
against the I-014 specification, plan, interface contract, task list and
constitution 1.2.0. Existing user changes to `.specify/feature.json`,
`docs/planning/Feature_slices.md` and the design reference images are excluded.

## Findings and follow-up

No unresolved material code finding remains in the reviewed scope. Corrective
implementation and test completion resolved these observed defects:

- Unavailable-section data could retain an available profile: decoder now
  quarantines the contradiction without discarding sound sessions.
- A Month date could snap back to the selected session: date activation now
  uses the existing guarded selection boundary and preserves cancel/continue.
- Empty calendar selection omitted date columns: explicit unknown date columns
  preserve the Day/Week range without inventing permission.
- Adjacent paint could hide the meaning of an existing single-window finding:
  the original finding now has an explicit single-source explanation.
- A narrow modal made the surrounding source disclosure inert: the planner
  SessionPane now includes the same read-only source context inside its modal
  subtree in detail and editing modes. Restricted review remains unchanged.

Each behavior correction has a recorded failing regression before its fix.
Final verification is recorded in backend-results.md/client-results.md, including
the full suites, focused checks, build and lint. Browser observations and live
database fingerprints are recorded in validation.md.

## Requirement traceability

| Requirement | Implementation and evidence | Review status |
|---|---|---|
| FR-001–004, 008–009 | Time-grid layout/surface; exact browser geometry, gaps, overlaps, early/late access | Verified within recorded cases |
| FR-005–007, 013, 019–020 | Read-only source projection, decoder isolation, profile/identity grouping, disclosures; API and snapshot checks | Verified within recorded cases |
| FR-010–012 | Complete Month grid, chronological entries, exact overflow and finding cues; 0/1/5/20 tests and browser expansion | Verified |
| FR-014–015 | Existing filtering/List/pane ownership and guarded date navigation; live save/cancel/refresh and zero-write fingerprints | Verified within recorded matrix |
| FR-016–018 | Native sections/buttons/scroll areas, focus return, 320px and modal context | Automated/browser subset verified; full observed acceptance pending |
| SC-004/005 | Actual AT, genuine 200% text enlargement, removed-color walkthrough and five representative planners | Pending T044/T045 |

## Architecture, security and reliability

No new dependency, endpoint, migration, persistence layer, snapshot format or
authorization path. Existing backend profiles and `window_applies` remain
authoritative; the browser only lays out supplied facts. Existing scheduling,
validation, save and publication production modules were not changed. Public
review does not fetch planner context. The existing workspace performance gate
passes; no new latency claim is introduced.

## Recommendation

**Blocked for full acceptance**, pending T044, T045 and completion of the observed
matrix in T049. No structural refactor is required to resolve those evidence gaps.
No commit, push or merge was performed. Final Git status retains the expected
implementation files and the original user planning/reference changes.


## T052 correction review

The subsequent clean-context convergence review found an additional HIGH/partial
FR-014 gap: an explicitly selected calendar lost known window context under
empty session filters. T052 corrects this by using the loaded workspace's
course/calendar/cohort context independently of the occurrence projection.
`matchesCourseContext` retains its original logic and is shared by both paths.

Reviewed nine red-to-green Day/Week/Month regressions, narrower course selection,
no-calendar fallback, exclusion of a different calendar's permission, and empty
List contributor identities. All 56 focused checks, 670 full client tests,
build and lint pass. No new code finding remains in this correction. Full
acceptance is still blocked by the original observed acceptance tasks and
convergence follow-ups T053–T055; this review does not fabricate those outcomes.
