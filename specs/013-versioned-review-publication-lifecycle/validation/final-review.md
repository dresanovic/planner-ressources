# Final implementation review — FS-013

## Outcome and scope

The implemented lifecycle is semester-wide and planner-controlled: Draft and optional Ready for review are editable working states; publication is always explicit; Published/Superseded content is captured and immutable; a successor starts from the current publication; abandonment retains work; restoration reuses the same abandoned revision when no other working revision exists; replacement supersedes the old publication only in the successful replacement transaction.

No approval workflow, lecturer access/feedback, authentication, automatic publication, external delivery, course-level publication, in-place published editing, field-level audit, or FS-014 workspace redesign was introduced. Planning-input administration remains outside occurrence versioning.

## Functional-requirement traceability

| Requirements | Primary implementation evidence |
|---|---|
| FR-001–FR-007 | Semester lifecycle models/service, explicit Draft creation, Draft/Ready guards and transitions, direct publication |
| FR-008–FR-010 | Server-prepared publication context, captured non-blocking conditions, explicit confirmation, stable UTC publication identity/time |
| FR-011–FR-013 | Canonical snapshot documents, historical detail reads from captured content, working-revision mutation guards, protected snapshot references |
| FR-014–FR-019 | Successor materialization from the current publication, origin identity, atomic replacement, current/historical selection and semester-wide projection |
| FR-020–FR-024 | Confirmed abandonment, captured abandoned content, same-identity restore, active-working conflict rejection, immutable Published/Superseded states |
| FR-025–FR-028 | Per-semester revision numbering, row versions, append-only ordered events, origin and designation metadata |
| FR-029–FR-031 | Text state/designation UI, expected revision/state/publication tokens, authoritative stale conflict responses, duplicate-event prevention |
| FR-032 | Scope inspection and contract review; excluded systems are absent |

## Constitution and simplicity check

- The implementation extends existing FastAPI/SQLAlchemy/React structures and SQLite migration sequencing; it adds no dependency or generic workflow framework.
- State authority and snapshot construction remain in one lifecycle service, while existing schedule services receive a narrow active-working guard.
- The HTTP surface is limited to overview/history, working-revision creation, revision detail, publication preparation, and transitions.
- Published display uses captured data and does not enrich historical content from mutable current catalogs.
- Automated backend, client, lint, type, build, and browser acceptance results are recorded alongside this review.

## Exceptions requiring follow-up evidence

The automated performance proof now covers 100 courses, 500 teaching sessions, 100 exams, fewer than 50 preparation queries, all five lifecycle operation classes, and 101-revision history under two seconds.

1. The quickstart browser pass used a narrow effective viewport but did not apply literal 200% browser zoom.
2. SC-008/SC-009 remain unverified because the required moderated study with 10 representative planners has not been run.

These are validation-evidence gaps, not authorization to weaken the lifecycle completion rule. Automated and browser evidence confirms that an existing publication remains stable until an explicitly published successor replaces it.
