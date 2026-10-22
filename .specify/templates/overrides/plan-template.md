# Implementation Plan: [FEATURE]

**Working Branch**: `[branch-name or main/master for clean verified solo change]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: Filled by `$speckit-plan`; its skill definition describes the workflow.
This project override retains the mandatory Simplicity Check and Verification Plan.
Read `.specify/memory/constitution.md` for all engineering rules and exceptions.

## Summary

[Primary requirement and the simplest technical approach for this approved slice.]

## Technical Context

**Language/Version**: [Existing backend Python and frontend TypeScript versions, or NEEDS CLARIFICATION]
**Primary Dependencies**: [FastAPI; React, TypeScript, Vite; existing dependencies relevant to this slice]
**Storage**: [Existing storage, required change, or N/A]
**Testing**: [Backend pytest; relevant client build, TypeScript, lint, component/UI checks]
**Target Platform**: [Server/browser targets, or NEEDS CLARIFICATION]
**Project Type**: [Web application, backend-only, or frontend-only slice]
**Performance Goals**: [Measurable goals from the spec, or N/A]
**Constraints**: [Current scope and architectural constraints, including approved exceptions]
**Scale/Scope**: [Users, resources, screens, and affected backend/frontend/contracts]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Evaluate every applicable principle in `.specify/memory/constitution.md`:
spec-first; Given/When/Then acceptance; practical test-first delivery and documented
manual exceptions; KISS; FastAPI and React/TypeScript/Vite; backend/client/contracts;
incremental delivery; branch choice and the clean verified solo main/master
exception; concrete verification before commit. Record evidence and justify
exceptions in Complexity Tracking.]

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: [Fewest components, dependencies, and indirection
   satisfying the approved requirements and tests.]
2. **Necessary abstractions**: [Only those justified by a demonstrated present
   need; otherwise "None".]
3. **Deliberately excluded**: [Hypothetical, unrelated, or unjustified layers,
   patterns, dependencies, abstractions, and extensions.]

Implementation MUST NOT begin until all three answers are complete and consistent
with the selected vertical slice.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
|-- plan.md              # $speckit-plan
|-- research.md          # Phase 0
|-- data-model.md        # Phase 1, if applicable
|-- quickstart.md        # Phase 1
|-- contracts/           # Phase 1, if applicable
`-- tasks.md             # $speckit-tasks; not created by $speckit-plan
```

### Source Code (repository root)

```text
backend/app/             # FastAPI production code
backend/tests/           # pytest tests
client/src/              # React/TypeScript code and colocated tests
```

**Structure Decision**: [Expand with actual affected paths, remove unaffected
paths, and justify any new boundary. Do not introduce placeholder layers.]

## Complexity Tracking

> Fill only for constitution exceptions or a new architectural element requiring justification.

| New layer, dependency, pattern, abstraction, or exception | Demonstrated current need | Simpler alternative rejected because |
|---------------------------------------------------------|---------------------------|--------------------------------------|
| [Only if needed] | [Current requirement or observed problem] | [Why existing direct code is insufficient] |

## Verification Plan

[List concrete backend, frontend, and contract commands that MUST pass before
commit, expected evidence, and the tests to write before production changes.
Carry these commands into explicit verification tasks. For a practical testing
exception or an unavailable command, record the reason, manual verification path,
and residual risk.]
