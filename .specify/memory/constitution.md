<!--
Sync Impact Report
Version change: 1.1.0 -> 1.2.0
Modified principles:
- Existing principles I-V retained without weakening
Added sections:
- VI. Incremental Delivery
- Explicit backend/client layout, TypeScript, and verification-task requirements
Removed sections:
- None
Templates requiring updates:
- .specify/templates/*-template.md: official Spec Kit v1.2.2 bases retained
- .specify/templates/overrides/plan-template.md: Simplicity and Verification sections
- .specify/templates/overrides/spec-template.md: explicit test-first requirements
- Tasks and checklist overrides removed; runtime constitution governs both
- .specify/README.md: customization ownership and compatibility documented
Follow-up TODOs:
- Existing `specs/*/plan.md` files predate v1.1.0; before implementation under
  this amendment, the applicable plan MUST add and complete the Simplicity Check.
-->
# Resource Planner Constitution

## Core Principles

### I. Spec-Driven Development

Every feature MUST begin with an updated feature specification under `specs/`.
Production implementation MUST NOT start until the relevant spec reflects the
intended behavior, scope, requirements, and acceptance criteria. Changes
discovered during implementation MUST be written back to the spec before the
production code is changed. Rationale: the specification is the source of truth
for review, task generation, and verification.

### II. Test-First Delivery

Every implementation MUST create or update tests before production code wherever
the behavior can be tested through unit, integration, contract, or UI tests. TDD
is the default workflow: write the failing test, implement the smallest change
that passes, then refactor while keeping tests green. Exceptions are allowed only
when automated testing is not practical for the change, and the plan MUST record
the reason plus the manual verification path. Rationale: test-first work keeps
behavior explicit and reduces regression risk.

### III. Clear Acceptance Criteria

Every feature specification MUST include independently testable user stories and
clear acceptance scenarios written in Given/When/Then form. Each functional
requirement and success criterion MUST be measurable enough for a reviewer to
decide whether the feature is complete. Ambiguity MUST be resolved during
clarification before planning or implementation proceeds. Rationale: acceptance
criteria define when work is done and prevent hidden scope changes.

### IV. Simplicity and KISS

The implementation MUST use the simplest design that satisfies the current
approved requirements and tests.

- Abstractions, interfaces, factories, services, repositories, adapters,
  configuration layers, and design patterns MUST NOT be introduced unless they
  solve an existing requirement or a clearly demonstrated problem.
- Implementations MUST NOT be designed for hypothetical future requirements.
- Direct, readable code MUST be preferred over flexible but complex
  architecture.
- Existing project structures and dependencies MUST be preferred over new ones.
- Shared abstractions MUST be extracted only after genuine duplication or
  multiple concrete use cases exist.
- Every new architectural layer, dependency, or design pattern MUST be justified
  in the implementation plan.
- When two solutions satisfy the requirements equally well, the solution with
  fewer components, fewer dependencies, and less indirection MUST be chosen.
- Implementation MUST remain limited to the current task or vertical slice and
  MUST NOT add unrelated capabilities.
- Complexity MUST be earned by demonstrated necessity, not anticipated
  possibility.

Rationale: direct solutions reduce maintenance cost and keep the codebase aligned
with demonstrated needs rather than speculative flexibility.

### V. Verified Delivery Workflow

Every implementation MUST be verified with the relevant automated tests before
commit. Solo development MAY happen on `main` or `master` when the working tree
is clean before the change starts and verification passes before commit. Feature
branches are RECOMMENDED for larger, risky, collaborative, or customer-facing
changes. Rationale: small solo changes can stay lightweight, while higher-risk
work still benefits from branch isolation and explicit review boundaries.

### VI. Incremental Delivery

Work MUST proceed in small, independently testable user stories or vertical
slices, delivering and verifying the highest-priority useful increment first.
Each increment MUST preserve previously verified behavior. Shared setup,
foundational work, optimization, logging, security changes, and refactoring
tasks MUST address a demonstrated requirement of the current slice; sample
template tasks MUST NOT become mandatory infrastructure by default.
Rationale: iterative delivery exposes feedback early and avoids speculative work.

## Technology Standards

The backend MUST use FastAPI for HTTP APIs and service entry points. Backend
tests SHOULD use `pytest` unless a feature plan justifies a different compatible
tool.

Backend production code MUST remain in `backend/app/`, with backend tests in
`backend/tests/`, unless a plan documents and justifies a different boundary.

The frontend MUST use React, TypeScript, and Vite. Frontend production code MUST remain
inside the `client/` application unless a plan documents a new app boundary.
Frontend verification MUST include the available Vite, TypeScript, lint, and UI
test commands relevant to the changed files.

Cross-stack contracts between the FastAPI backend and React/Vite frontend MUST
be captured in the feature spec or design artifacts before implementation.

## Development Workflow

Feature work MUST follow this order:

1. Create or update the feature spec.
2. Clarify open questions until acceptance criteria are testable.
3. Create or update the implementation plan and constitution check.
4. Complete the plan's Simplicity Check by stating the simplest viable solution,
   the abstractions necessary now, and the possible abstractions or extensions
   deliberately excluded.
5. Create or update tasks, with test tasks before implementation tasks.
6. Write or update tests and confirm they fail for the intended behavior when
   practical.
7. Implement the smallest production change that satisfies the spec.
8. Run the relevant automated tests before committing.

Plans and task lists MUST explicitly identify backend, frontend, and shared
contract impacts. Reviewers MUST reject implementation work that lacks an
updated spec, clear acceptance criteria, or verification evidence.

Task lists MUST include explicit verification tasks with the concrete backend,
frontend, and contract commands relevant to the change. Test tasks MUST precede
the production tasks they verify wherever automated testing is practical. Any
exception MUST cite the plan's rationale and include its manual verification
task. Task paths MUST follow the selected plan and existing `backend/` and
`client/` conventions, rather than generic template example paths.

## Governance

This constitution supersedes conflicting process guidance in project templates,
plans, task lists, and ad hoc instructions. Amendments MUST be proposed as a
documented change to this file, include a Sync Impact Report, and update all
affected spec-kit templates in the same change.

Versioning follows semantic versioning:

- MAJOR for incompatible changes to governance or principle meaning.
- MINOR for new principles, new required sections, or materially expanded rules.
- PATCH for clarifications, wording fixes, and non-semantic refinements.

Compliance MUST be reviewed during planning, task generation, implementation
review, and before commit. Any approved exception MUST be documented in the
feature plan with rationale, scope, and verification impact.

**Version**: 1.2.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-10-22
