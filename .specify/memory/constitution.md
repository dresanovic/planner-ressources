<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. Spec-Driven Development
- PRINCIPLE_2_NAME -> II. Test-First Delivery
- PRINCIPLE_3_NAME -> III. Clear Acceptance Criteria
- PRINCIPLE_4_NAME -> IV. Simple, Fit-for-Purpose Implementation
- PRINCIPLE_5_NAME -> V. Verified Delivery Workflow
Added sections:
- Technology Standards
- Development Workflow
Removed sections:
- None
Templates requiring updates:
- .specify/templates/plan-template.md: updated
- .specify/templates/spec-template.md: updated
- .specify/templates/tasks-template.md: updated
- .specify/templates/commands/*.md: not present
Follow-up TODOs:
- None
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

### IV. Simple, Fit-for-Purpose Implementation

Implementations MUST use the simplest design that satisfies the approved spec
and tests. New dependencies, frameworks, background services, abstractions, or
infrastructure MUST be justified in the implementation plan with the problem
they solve and the simpler alternative rejected. Rationale: this project remains
maintainable when complexity is limited to current feature needs.

### V. Verified Delivery Workflow

Every implementation MUST be verified with the relevant automated tests before
commit. Solo development MAY happen on `main` or `master` when the working tree
is clean before the change starts and verification passes before commit. Feature
branches are RECOMMENDED for larger, risky, collaborative, or customer-facing
changes. Rationale: small solo changes can stay lightweight, while higher-risk
work still benefits from branch isolation and explicit review boundaries.

## Technology Standards

The backend MUST use FastAPI for HTTP APIs and service entry points. Backend
tests SHOULD use `pytest` unless a feature plan justifies a different compatible
tool.

The frontend MUST use React with Vite. Frontend production code MUST remain
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
4. Create or update tasks, with test tasks before implementation tasks.
5. Write or update tests and confirm they fail for the intended behavior when
   practical.
6. Implement the smallest production change that satisfies the spec.
7. Run the relevant automated tests before committing.

Plans and task lists MUST explicitly identify backend, frontend, and shared
contract impacts. Reviewers MUST reject implementation work that lacks an
updated spec, clear acceptance criteria, or verification evidence.

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

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
