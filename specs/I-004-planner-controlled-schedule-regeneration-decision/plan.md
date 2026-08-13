# Implementation Plan: Planner-Controlled Schedule Regeneration Decision

**Working Branch**: `HEAD (delegated worktree; planning only—implementation requires an isolated feature branch because unrelated user changes are present)` | **Date**: 2026-08-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`specs/I-004-planner-controlled-schedule-regeneration-decision/spec.md`

## Summary

Add one pause between the existing optimizer and its persistence step when at
least one selected course has saved teaching sessions. The first solve returns a
hard-valid generated-only result, a factual current-versus-generated comparison,
the existing freshness evidence, and a canonical candidate fingerprint, but
does not save. `Neu erzeugten Stundenplan übernehmen` submits that evidence to a
separate accept operation. The backend revalidates current state, deterministically
reproduces the joint solution, requires the fingerprint to match, and saves the
complete selection through the existing atomic transaction. `Abbrechen` or
dismissal only clears client state because no provisional server state exists.

Selections with no existing teaching sessions retain the established direct-save
flow. This design needs no new table, migration, cache, expiry mechanism,
background cleanup, decision record, dependency, or second generator.

## Technical Context

**Language/Version**: Python 3.12.8 backend; TypeScript 6.0.2 with React 19.2.7
frontend; Node 26.7.0 in the current planning environment

**Primary Dependencies**: Existing FastAPI 0.139, SQLAlchemy 2.0, Pydantic
2.13, OR-Tools CP-SAT, React, React DOM, and Vite; no new dependency

**Storage**: Existing schedule, revision, constraint, resource, holiday, and exam
data only; no candidate or decision-history persistence

**Testing**: pytest 9 service/API/concurrency/regression tests plus a workflow-level
performance test for preview, direct-save, and actionable no-result outcomes;
Vitest 4 with jsdom for API, dialog, focus, and page state; existing lint/build;
manual keyboard, assistive-technology, 200%-text-zoom, and planner review

**Target Platform**: Existing FastAPI service and supported desktop browsers;
SQLite compatibility remains mandatory

**Project Type**: Cross-stack change in the existing FastAPI and React/Vite web
application

**Performance Goals**: Preserve the established one-to-twenty-course generation
envelope. The initial solve still produces a comparison or actionable outcome
within the existing target; acceptance may repeat the deterministic solve once
and must not introduce another algorithm or background operation.

**Constraints**: One unified generator; active editable Working revision only;
generated-only candidate when replacement is involved; valid lower-coverage
partial alternatives allowed; exact compared result verified before atomic save;
stale/repeated commits rejected; direct save for wholly unplanned selections;
no server-side provisional state, written reason, decision history, automatic
repair, or per-course decision

**Scale/Scope**: Existing conflict-aware optimizer/service/router/schema, one
additional accept operation, existing Schedule page and dialog, and focused
backend/client tests

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **Spec-first — PASS**: The validated FS-023 specification and checklist exist
  before implementation.
- **Acceptance criteria — PASS**: Four independently testable stories and their
  Given/When/Then scenarios cover comparison, atomic decision, stale protection,
  and direct save.
- **Test-first — PASS**: Optimizer, service, API, concurrency, component,
  accessibility, and regression tests are identified below and in
  `quickstart.md`; tasks must put failing tests before production edits.
- **Simplicity and KISS — PASS**: The plan splits the existing solve/save flow,
  reuses snapshot tokens, deterministic optimization, and atomic persistence,
  and adds no storage, dependency, scheduler, or architectural layer.
- **Technology fit — PASS**: Backend remains FastAPI/SQLAlchemy/OR-Tools and
  frontend remains React/Vite; cross-stack contracts are under `contracts/`.
- **Delivery workflow — PASS WITH REQUIRED ACTION**: This customer-facing
  transaction change should be implemented on
  `codex/I-004-planner-controlled-schedule-regeneration-decision` or an equivalent
  isolated clean worktree because the current detached worktree contains
  unrelated user changes.
- **Verification before commit — PASS**: Focused and complete commands and
  evidence are listed below.

### Post-design re-check

The simplified design introduces no constitution violation. The only new public
operation is the confirmed accept action required by FS-023. It reuses the
existing optimizer rather than persisting a temporary candidate or implementing
a second exact-session validator. The extra deterministic solve is an explicit
simplicity/performance trade-off: it keeps the design stateless while ensuring
the saved solution exactly matches the compared fingerprint.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: For replacement selections, return the existing
   optimizer result before save with current/generated comparison facts and a
   canonical fingerprint. On approval, revalidate the existing snapshot,
   deterministically solve again, require the same fingerprint, and execute the
   existing atomic save. On cancel, clear the dialog state. Preserve direct save
   when no selected course has sessions.
2. **Necessary abstractions**: One optimizer option that disables retention of
   current selected sessions and the non-worsening coverage floor; one canonical
   candidate fingerprint helper shared by preview and accept. No new service,
   repository, model, table, or generalized workflow abstraction.
3. **Deliberately excluded**: Candidate persistence, database migration,
   client-submitted generated sessions, signing/key management, process-local
   cache, expiry/cleanup, background jobs, decision/audit records, per-course
   choices, undo, provenance changes, and a second generator.

## Project Structure

### Documentation (this feature)

```text
specs/I-004-planner-controlled-schedule-regeneration-decision/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- planner-regeneration.openapi.yaml
|   `-- planner-regeneration-ui.md
|-- checklists/requirements.md
`-- tasks.md                                  # generated by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- schemas/conflict_aware_generation.py  # preview/accept/comparison shapes
|   |-- api/conflict_aware_generation.py      # generate preview and accept
|   `-- services/
|       |-- conflict_aware_generation.py      # split solve from conditional save
|       |-- semester_optimization.py           # generated-only replacement mode
|       `-- draft_schedule_validation.py       # current warning comparison facts
`-- tests/
    |-- api/test_conflict_aware_generation.py
    `-- services/
        |-- test_conflict_aware_generation.py
        |-- test_conflict_aware_generation_concurrency.py
        `-- test_semester_optimization.py

client/
|-- src/
|   |-- api/conflictAwareGeneration.ts
|   |-- components/
|   |   |-- ReplacementConfirmationDialog.tsx # evolve into comparison dialog
|   |   `-- ReplacementConfirmationDialog.test.tsx
|   |-- pages/
|   |   |-- CourseSchedulePage.tsx
|   |   `-- CourseSchedulePage.test.tsx
|   |-- test/optimizationFixtures.ts
|   `-- App.css
`-- package.json
```

**Structure Decision**: Extend the existing I-003 generation vertical path and
reuse the current page/dialog. The dialog file may be renamed, but the old
pre-generation confirmation must not remain beside the new comparison.

## Implementation Design

### 1. Produce a generated-only preview when replacement is involved

- Keep `/optimization/prepare` read-only and retain its canonical selection and
  shared/per-course snapshot tokens.
- Determine from authoritative state whether any selected draft contains saved
  sessions. Remove the pre-generation `replacementConfirmed` gate.
- If none does, keep the current solve, atomic save, outcome retention, and saved
  result response.
- If any does, call the same optimizer in generated-only mode: selected current
  sessions are comparison input but cannot be retained and do not establish a
  minimum generated unit count. Unselected teaching and active exams remain
  fixed occupancy.
- Permit zero generated units for one course inside a non-empty joint partial
  result. Treat an all-zero selection as no valid alternative and save nothing.
- Build a canonical fingerprint from the ordered selected course IDs and exact
  generated session fields. Return it with aggregate/per-course comparison facts,
  original prepared evidence, and `saved=false`; do not mutate drafts or retain
  PlanningOutcomes.

### 2. Accept by revalidating and reproducing the preview

- Add `POST /optimization/accept` with the original prepared request evidence and
  the candidate fingerprint. The request contains no generated sessions,
  per-course choice, or written reason.
- Include the Working revision state and row version in the shared preparation
  freshness evidence so a lifecycle change invalidates an open preview even when
  the revision ID remains the same.
- Rebuild authoritative shared/per-course snapshot tokens and reject the whole
  operation if revision, schedule, constraint, holiday, course, semester,
  resource, availability, capacity, active-exam, or protected teaching state is
  stale.
- Run the same generated-only deterministic optimizer with the same canonical
  inputs. Canonicalize its exact joint result and require its fingerprint to
  equal the preview fingerprint. A mismatch is non-mutating and directs the
  planner to regenerate.
- Claim/revalidate the active Working revision through the existing transaction
  boundary immediately before persistence. Apply every selected course through
  the existing atomic save plan. A zero-session selected result clears an
  existing draft or remains absent; it must not create an empty draft.
- Retain established saved generation outcomes only after the complete accepted
  result is applied. Any persistence error rolls back every selected draft and
  outcome.
- The first successful accept changes draft identities/revisions, so a repeated
  or losing concurrent accept fails existing freshness validation and cannot
  commit again.

### 3. Cancel without a backend operation

- `Abbrechen`, Escape, close, or leaving the unresolved comparison discards the
  preview/fingerprint from React state. Because preview created no server state,
  no cancel request, expiry, cleanup, or tombstone is needed.
- Current saved schedules and warnings remain exactly as they were; cancellation
  triggers no repair, mutation, or decision history.
- If any relevant state changes while the dialog is open, the later accept call
  rejects the old prepared evidence.

### 4. Present one accessible factual comparison

- Replace the current pre-generation confirmation with a post-generation dialog
  opened by the preview response.
- Show selection totals and one per-course current/generated comparison with
  required, scheduled, remaining, complete/partial, blocking reasons, and
  resolved current warning facts.
- State that acceptance replaces all selected saved sessions, including
  planner-created or edited work; individual session provenance is not needed.
- Offer exactly `Neu erzeugten Stundenplan übernehmen` and `Abbrechen`. A close
  control has cancellation semantics. Show no winner, per-course action, reason
  field, or keep-current button.
- Reuse the existing focus entry/containment/return and Escape handling. At narrow
  widths and 200% text zoom, stack explicit current/generated sections while
  preserving course association and reachable actions.
- Accept success refreshes authoritative schedules and shows the saved result.
  Stale/fingerprint-mismatch responses close the invalid preview, preserve the
  selection, and direct regeneration.

## Complexity Tracking

No constitution violations require justification.

## Verification Plan

From the repository root:

```text
python -m pytest backend/tests/services/test_semester_optimization.py backend/tests/services/test_conflict_aware_generation.py
python -m pytest backend/tests/api/test_conflict_aware_generation.py backend/tests/services/test_conflict_aware_generation_concurrency.py
python -m pytest backend/tests/performance/test_semester_optimization_performance.py
python -m pytest backend/tests
```

From `client/`:

```text
npm test -- src/api/conflictAwareGeneration.test.ts src/components/ReplacementConfirmationDialog.test.tsx src/pages/CourseSchedulePage.test.tsx
npm test
npm run lint
npm run build
```

Expected evidence:

- Preview changes no saved schedule or outcome and may show a valid
  lower-coverage partial alternative.
- Accept reproduces the exact fingerprint, then saves every selected course or
  none; stale, mismatched, repeated, concurrent-losing, or persistence-failing
  requests change nothing.
- Cancel/dismiss is entirely local and non-mutating.
- Wholly unplanned selections retain direct save with no comparison.
- Every offered/accepted generated result has zero active hard conflicts and
  never mixes retained current sessions with generated siblings.
- One-course and multi-course acceptance datasets explicitly cover every hard
  constraint category listed in TR-002.
- Workflow-level measurements cover preview, direct-save, and actionable
  no-result outcomes and satisfy SC-010's 95%-within-30-seconds threshold.
- Dialog tests prove post-generation timing, exact actions, factual comparison,
  keyboard/focus behavior, 200% zoom structure, and no per-course decision.
- Complete suites preserve manual editing, exams, lifecycle/publication,
  Calendar, resources, academic data, and I-003 behavior.
- The FS-023 product owner owns recruitment and evidence collection for the
  five-planner SC-008 review. Automated implementation may complete first, but
  the feature is not release-ready until the SC-008 threshold passes.

**Agent Context Update**: No `update-agent-context` script exists under
`.specify/scripts/`; no context file was created or modified.
