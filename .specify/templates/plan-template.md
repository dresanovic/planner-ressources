# Implementation Plan: [FEATURE]

**Working Branch**: `[branch-name or main/master for clean verified solo change]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11 for backend, TypeScript for frontend or NEEDS CLARIFICATION]

**Primary Dependencies**: [FastAPI for backend, React with Vite for frontend, or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [pytest for backend, frontend lint/build/UI tests for client, or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, browser, or NEEDS CLARIFICATION]

**Project Type**: [web application, API, or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., <200ms p95 API response, fast route transitions, or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., avoid new dependencies, offline-capable, accessibility, or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., number of users, resources, screens, or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-first**: Feature spec exists/updated, with scope, requirements, and acceptance criteria before production implementation.
- **Acceptance criteria**: User stories are independently testable and acceptance scenarios use Given/When/Then.
- **Test-first**: Plan identifies tests to create/update before production code, or documents a justified exception with manual verification.
- **Simplicity and KISS**: The design is limited to current approved
  requirements; any new layer, dependency, pattern, or abstraction solves a
  demonstrated present need and is justified below.
- **Technology fit**: Backend work uses FastAPI; frontend work uses React with Vite; cross-stack contracts are documented.
- **Delivery workflow**: Work is on a feature branch for larger/risky/customer-facing changes, or on `main`/`master` only for clean verified solo changes.
- **Verification before commit**: Relevant test commands and expected verification evidence are listed.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: [Describe the direct solution with the fewest
   components, dependencies, and indirection that satisfies the approved
   requirements and tests.]
2. **Necessary abstractions**: [List only abstractions required by a demonstrated
   present need, or state "None".]
3. **Deliberately excluded**: [List possible abstractions, layers, patterns,
   dependencies, or extensions excluded because they are hypothetical,
   unrelated, or not yet justified.]

Implementation MUST NOT begin until all three answers are complete and consistent
with the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
|-- plan.md              # This file (/speckit-plan command output)
|-- research.md          # Phase 0 output (/speckit-plan command)
|-- data-model.md        # Phase 1 output (/speckit-plan command)
|-- quickstart.md        # Phase 1 output (/speckit-plan command)
|-- contracts/           # Phase 1 output (/speckit-plan command)
`-- tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths. The delivered plan must not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Resource Planner web application
backend/
|-- app/
|   |-- models/
|   |-- services/
|   `-- api/
`-- tests/

client/
|-- src/
|   |-- components/
|   |-- pages/
|   `-- services/
`-- tests/

# [REMOVE IF UNUSED] Option 2: Backend-only change
backend/
|-- app/
`-- tests/

# [REMOVE IF UNUSED] Option 3: Frontend-only change
client/
|-- src/
`-- tests/
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| New layer, dependency, pattern, or abstraction | Demonstrated current need | Simpler alternative rejected because |
|------------------------------------------------|---------------------------|--------------------------------------|
| [e.g., new dependency] | [current requirement or observed problem] | [why existing code is insufficient] |
| [e.g., new abstraction] | [duplication or multiple concrete uses] | [why direct code is insufficient] |

## Verification Plan

List the concrete commands that MUST pass before commit, such as backend
`pytest`, client `npm run build`, client `npm run lint`, or feature-specific
tests. If a command cannot be run, record the reason and residual risk.
