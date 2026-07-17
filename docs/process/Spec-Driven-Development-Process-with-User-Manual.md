# Spec-Driven Development Process

This document defines the overall development process using **Spec Kit** together with the custom skills:

- `$architecture-exploration`
- `$requirements-engineering`
- `$code-review`
- `$user-manual-creation`
- `$code-refactor`

The process has three different levels:

1. **Project foundations**, normally established once
2. **Product scope and slice management**, established initially and updated when necessary
3. **Iterative slice implementation and user documentation**, repeated for every development slice
4. **Periodic codebase improvement**, performed when justified

---

# Overall process

```text
PROJECT FOUNDATION
──────────────────────────────────────────────────────────

$speckit-constitution
        ↓
$architecture-exploration


PRODUCT SCOPE AND SLICE DEFINITION
──────────────────────────────────────────────────────────

$requirements-engineering
        ↓
docs/planning/Feature_slices.md


ITERATIVE IMPLEMENTATION — REPEATED FOR EACH SLICE
──────────────────────────────────────────────────────────

$speckit-specify
        ↓
$speckit-clarify
        ↺ repeat until sufficiently clear
        ↓
$speckit-plan
        ↓
$speckit-tasks
        ↓
$speckit-analyze
        ↺ correct findings and repeat until consistent
        ↓
$speckit-implement
        ↓
$code-review
        ↓
verify
        ↓
$user-manual-creation
        ↓
commit → merge


PERIODIC CODEBASE IMPROVEMENT
──────────────────────────────────────────────────────────

$code-refactor
```

The official Spec Kit workflow focuses on specification, planning, task creation, analysis, and implementation. The custom skills extend this workflow with architecture exploration, product-level requirements engineering, code review, user-manual creation, and controlled refactoring.

Official Spec Kit documentation:

- [Spec Kit documentation](https://github.github.com/spec-kit/)
- [Spec Kit quickstart](https://github.github.com/spec-kit/quickstart.html)

---

# Phase 1: Project foundation

These activities define the rules and technical direction of the project. They are normally performed once at the beginning and are not repeated for every development slice.

## 1. Project setup and initialization

This is performed once per project.

Typical activities include:

- creating the repository;
- initializing the project structure;
- installing and configuring Spec Kit;
- connecting the coding agent;
- defining the basic Git workflow;
- configuring the development and test environments.

The purpose is to prepare the project so that specification artifacts and implementation changes can be managed consistently.

---

## 2. Constitution: define project principles

Skill:

```text
$speckit-constitution
```

The constitution defines the project’s non-negotiable development principles.

Typical principles include:

- specifications must be updated before implementation;
- acceptance criteria must be defined;
- tests should be written before production code;
- the simplest design satisfying current approved requirements and tests must be used;
- abstractions, layers, dependencies, and patterns must solve demonstrated current needs;
- hypothetical future requirements and unrelated capabilities must not shape the implementation;
- all changes must be verified before they are committed;
- unrelated changes must not be introduced into a slice.

The constitution is not a feature specification. It is the project’s development rulebook.

It is normally created once at the start of the project and updated only when the project’s general development principles change.

---

## 3. Architecture exploration

Custom skill:

```text
$architecture-exploration
```

Architecture exploration is used to evaluate and select the project’s fundamental technical direction.

It can be executed:

```text
$architecture-exploration
        ↓
$speckit-constitution
```

or:

```text
$speckit-constitution
        ↓
$architecture-exploration
```

The appropriate order depends on the project.

Architecture exploration may come first when architectural options must be understood before meaningful project rules can be established. The constitution may come first when important organizational or development constraints already exist and must guide the architectural decision.

Typical architecture questions include:

- Which frontend and backend technologies should be used?
- Should the application use a monolith, modular monolith, or distributed architecture?
- Which persistence technology is appropriate?
- Which external systems must be integrated?
- Which deployment model should be used?
- Which architectural constraints are imposed by the organization?
- Which quality attributes are most important?
- What are the major technical risks and trade-offs?

Example output may include:

- selected technology stack;
- rejected alternatives;
- architectural decisions;
- important constraints;
- integration boundaries;
- major technical risks;
- assumptions that still require validation.

Architecture exploration is normally performed once for the initial project architecture. It may be repeated only when a substantial architectural decision or major technology change is required.

It is not part of the regular implementation cycle for every slice.

---

# Phase 2: Product scope and slice definition

## 4. Requirements engineering

Custom skill:

```text
$requirements-engineering
```

Requirements engineering establishes the product-level ground truth.

Its purpose is to transform a broad product idea, major feature area, or scope change into a structured set of ordered vertical development slices.

The skill creates or updates:

```text
docs/planning/Feature_slices.md
```

This file is the authoritative source for:

- product goals;
- target users and actors;
- application scope;
- explicit exclusions;
- external-system boundaries;
- major business rules;
- high-level workflows;
- development slices;
- slice dependencies;
- recommended implementation order;
- ready-to-copy `$speckit-specify` prompts.

## Development slices

A slice is a vertical implementation of a meaningful high-level capability.

A slice should deliver an observable user or business outcome across the necessary technical layers. It should not normally be defined as an isolated technical component such as:

- create the database;
- build the backend;
- create the frontend;
- add an API layer;
- configure infrastructure.

Those are usually implementation tasks within a vertical slice.

Examples of vertical slices for a resource-planning application could be:

- create a meeting-room booking;
- prevent conflicting bookings;
- cancel an existing booking;
- approve restricted bookings;
- notify users about booking changes;
- manage rooms and availability.

From a requirements-engineering perspective, slices often correspond to complete or partial business processes, user workflows, or business capabilities. However, a slice should remain small enough to be handled through one focused Spec Kit cycle.

## How often requirements engineering is used

`$requirements-engineering` is first executed near the beginning of the project after the initial project and architecture foundations are sufficiently clear.

Unlike the project constitution and initial architecture exploration, requirements engineering is not strictly a one-time activity.

It can be executed again when:

- new product scope is introduced;
- stakeholder requirements change;
- a slice must be added;
- an existing slice must be divided;
- several slices must be merged;
- priorities change;
- dependencies change;
- an integration boundary changes;
- previously planned scope is deferred or removed;
- implementation experience reveals that the original slice boundaries are unsuitable.

It will therefore normally be used multiple times during development, but less frequently than the iterative Spec Kit skills.

The distinction is:

```text
$requirements-engineering
    manages the overall product scope and slice map

$speckit-* skills
    specify and implement one selected slice
```

The current `Feature_slices.md` remains the product-level ground truth throughout development.

---

# Phase 3: Iterative slice implementation

The following workflow is repeated independently for every selected development slice:

```text
$speckit-specify
        ↓
$speckit-clarify
        ↺
$speckit-plan
        ↓
$speckit-tasks
        ↓
$speckit-analyze
        ↺
$speckit-implement
        ↓
$code-review
        ↓
verify
        ↓
$user-manual-creation
```

Each slice should normally have its own feature branch and specification artifacts. The manual should be updated in the same slice when the implemented behavior changes the way users operate the system.

---

## 5. Select the next slice

Before starting a new Spec Kit cycle:

1. open `docs/planning/Feature_slices.md`;
2. identify the next recommended slice;
3. check its dependencies;
4. confirm that prerequisite slices are complete;
5. copy the prepared `$speckit-specify` prompt;
6. create a dedicated branch.

Example:

```text
feature/003-booking-conflict-detection
```

Only one sufficiently focused slice should normally be implemented in one cycle.

---

## 6. Specify the selected slice

Skill:

```text
$speckit-specify
```

Purpose:

Define **what the selected slice must achieve and why**.

The specification should focus on:

- user goals;
- actors;
- user scenarios;
- functional requirements;
- acceptance criteria;
- business rules;
- edge cases;
- observable behavior;
- explicit exclusions.

It should avoid premature implementation detail.

Example:

```text
$speckit-specify

Allow employees to create a booking for an available meeting room.
The user selects a room, start time, and end time. The system validates
the request and confirms a successful booking.
```

Typical output:

```text
specs/003-room-booking/spec.md
```

The specification represents the detailed agreement for this particular slice.

---

## 7. Clarify the specification

Skill:

```text
$speckit-clarify
```

Purpose:

Identify and resolve ambiguities before technical planning begins.

Typical clarification questions include:

- Can bookings be created for past times?
- Can a booking span multiple days?
- Who may create a booking?
- What happens when a room becomes unavailable?
- Which time increments are supported?
- Who may cancel or modify a booking?
- Which validation message should the user receive?

Clarification should be run repeatedly when necessary:

```text
$speckit-clarify
        ↓
update specification
        ↓
$speckit-clarify
        ↓
repeat until sufficiently clear
```

The goal is not to eliminate every possible future question. The goal is to remove ambiguities that could materially affect planning, implementation, testing, or acceptance.

All confirmed answers must be integrated into the specification.

---

## 8. Optional specification checklist

Skill:

```text
$speckit-checklist
```

Purpose:

Assess whether the specification is sufficiently complete and testable.

The checklist may verify that:

- user scenarios are defined;
- acceptance criteria are measurable;
- important business rules are documented;
- exclusions are explicit;
- edge cases are considered;
- unresolved questions are visible;
- requirements do not contradict each other.

This step is especially useful for:

- customer projects;
- important business processes;
- high-risk functionality;
- complex slices;
- specifications created from incomplete stakeholder input.

It may be omitted for simple, low-risk slices when the specification is already clearly defined.

---

## 9. Create the technical plan

Skill:

```text
$speckit-plan
```

Purpose:

Translate the confirmed specification into a technical implementation approach.

The plan answers questions such as:

- Which components must change?
- Which architecture patterns should be used?
- Which domain entities are required?
- Which API contracts are required?
- Which persistence changes are required?
- Which external integrations are involved?
- Which tests are required?
- Which existing conventions must be followed?
- Which technical risks must be addressed?

Depending on the project, the generated artifacts may include:

```text
plan.md
research.md
data-model.md
contracts/
quickstart.md
```

The plan must remain aligned with:

- the selected slice;
- the project constitution;
- the established architecture;
- the existing codebase;
- the confirmed specification.

Before implementation, the plan must include a short Simplicity Check stating:

1. the simplest viable solution;
2. which abstractions are necessary now;
3. which possible abstractions or extensions were deliberately excluded.

A plan must not silently expand the scope of the slice.

---

## 10. Create implementation tasks

Skill:

```text
$speckit-tasks
```

Purpose:

Convert the plan into an ordered and executable task list.

Typical tasks include:

- create or update tests;
- add a domain entity;
- implement validation rules;
- update persistence;
- expose an API endpoint;
- add user-interface behavior;
- handle error responses;
- update documentation;
- run verification commands.

The output is usually:

```text
tasks.md
```

Tasks should:

- be concrete;
- reference relevant files where possible;
- follow dependency order;
- support incremental implementation;
- map back to requirements and acceptance criteria;
- include necessary tests;
- avoid unrelated work.

Technical-layer tasks are appropriate at this stage because they are implementation steps within an already-defined vertical slice.

---

## 11. Analyze consistency

Skill:

```text
$speckit-analyze
```

Purpose:

Check whether the specification, plan, tasks, and project rules are mutually consistent.

Analysis should detect issues such as:

- a requirement has no corresponding implementation task;
- an acceptance criterion has no test task;
- a task introduces behavior not present in the specification;
- the plan contradicts the project constitution;
- the selected architecture is not respected;
- dependencies are missing;
- data-model changes are inconsistent with API contracts;
- scope from another slice has been added accidentally.

Analysis is an iterative quality gate:

```text
$speckit-analyze
        ↓
findings
        ↓
correct spec, plan, or tasks
        ↓
$speckit-analyze
        ↓
repeat until sufficiently consistent
```

Implementation should not begin while material consistency problems remain unresolved.

---

## 12. Implement the slice

Skill:

```text
$speckit-implement
```

Purpose:

Implement the selected slice according to the specification, plan, and task list.

Implementation should follow a test-first approach where practical:

```text
select one task or small task group
        ↓
identify related acceptance criteria
        ↓
write or update tests
        ↓
run tests
        ↓
confirm the expected failure
        ↓
implement the minimum production code
        ↓
run tests again
        ↓
refactor locally when necessary
        ↓
review the diff
        ↓
continue with the next task
```

The implementation skill should:

- work only within the selected slice;
- follow the ordered task list;
- create or update tests before production behavior;
- avoid unrelated changes;
- run appropriate verification commands;
- document deviations from the plan;
- stop before committing;
- show the resulting Git diff and status.

Implementation is complete only when:

- the relevant tasks are completed;
- acceptance criteria are satisfied;
- required tests pass;
- no unexplained unrelated changes remain.

---

## 13. Review the implementation

Custom skill:

```text
$code-review
```

The code-review skill is executed after implementation and before commit, pull request, or merge.

It reviews the changes for:

- functional correctness;
- specification compliance;
- acceptance-criteria coverage;
- test quality;
- missing edge cases;
- maintainability;
- architectural consistency;
- unnecessary complexity;
- security concerns;
- performance risks;
- appropriate use of design principles and patterns;
- accidental scope expansion.

The review should prioritize findings by severity.

Example categories:

```text
Critical
High
Medium
Low
Suggestion
```

The review skill should report findings but should not automatically modify the code.

When material problems are found:

```text
$code-review
        ↓
correct implementation
        ↓
run tests
        ↓
$code-review
```

This cycle may be repeated until no blocking findings remain.

---

## 14. Verify the completed slice

Before committing, verify:

- all acceptance criteria;
- relevant automated tests;
- application behavior;
- changed files;
- `git diff`;
- `git status`;
- completed task markers;
- absence of unrelated modifications;
- consistency between code and specification.

Recommended commands include:

```text
git diff --stat
git diff
git status --short
```

The final implementation summary should state:

- what was implemented;
- which tests were executed;
- whether they passed;
- which files changed;
- which risks remain;
- which follow-up work was deliberately deferred.

---

## 15. Create or update the user manual

Custom skill:

```text
$user-manual-creation
```

Purpose:

Create or update an intuitive user manual from the verified implemented state of the product.

The skill uses:

- `docs/planning/Feature_slices.md` as the product-scope source;
- the selected slice specification and clarifications;
- implementation plans and tasks;
- analysis artifacts;
- current implementation;
- passing tests;
- existing README files and user documentation.

The documentation must reflect actual available behavior. Planned, incomplete, or unverified functionality must not be presented as available.

The manual contains two complementary perspectives:

### Quick Start

The Quick Start helps a new user obtain value from the system with minimal setup and prior knowledge.

It should include:

- a short explanation of the system;
- only essential prerequisites;
- how to access or start the application;
- the most important use cases;
- numbered procedures;
- expected results.

It should remain simple, intuitive, and focused on common user goals.

### Detailed Guide

The Detailed Guide covers behavior beyond the minimum first-use path.

It may include:

- complete and alternative workflows;
- roles and permissions;
- input and validation rules;
- advanced scenarios;
- edge cases;
- failure situations;
- recovery procedures;
- known limitations;
- troubleshooting.

The skill should normally create or update:

```text
docs/user-manual/User_Manual.md
docs/user-manual/User_Manual_Report.md
```

`User_Manual.md` is the user-facing documentation.

`User_Manual_Report.md` is an optional internal report containing:

- documented slices;
- excluded or partially implemented slices;
- implementation evidence;
- conflicting artifacts;
- documentation gaps;
- recommended screenshots;
- unresolved verification points.

Before documenting a slice as available, the skill must verify that:

- its user-facing workflow exists;
- it is accessible through the intended interface;
- relevant tests pass;
- essential acceptance criteria are satisfied;
- no evidence contradicts its availability.

When the evidence is insufficient, the skill must report the gap rather than guess.

Typical workflow:

```text
$code-review
        ↓
correct blocking findings
        ↓
run tests and verify behavior
        ↓
$user-manual-creation
        ↓
review Quick Start as a first-time user
        ↓
inspect documentation diff
        ↓
commit
```

The skill must not:

- modify application code;
- invent buttons, screens, commands, or behavior;
- document planned features as implemented;
- expose passwords, secrets, tokens, or private configuration;
- mix developer setup into end-user instructions unless users truly need it;
- hide conflicting or missing evidence.

The user manual should be updated after every slice that changes user-visible behavior. A broader manual review should also be performed before a release or handover.

---

## 16. Commit, review, and merge

Only commit the slice when:

- the specification is complete enough;
- clarification is resolved;
- the plan and tasks are aligned;
- analysis has no unresolved material findings;
- implementation is complete;
- tests pass;
- code review has no blocking findings;
- the diff has been inspected.

Typical workflow:

```text
commit specification artifacts
        ↓
commit planning artifacts
        ↓
commit implementation
        ↓
push branch
        ↓
create or inspect pull request
        ↓
merge into main
```

For a small solo project, some commits may be combined. However, specification, planning, and implementation changes should remain understandable from the Git history.

GitHub describes pull requests as a mechanism for proposing, reviewing, and merging changes into another branch:

[GitHub: About pull requests](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)

---

# Phase 4: User documentation and release readiness

User documentation is maintained incrementally through `$user-manual-creation` after verified user-facing changes.

Before a release, demonstration, training session, or handover, run the skill across all implemented slices to confirm that the Quick Start and Detailed Guide remain complete and consistent.

A release-level documentation review should verify:

- all implemented slices relevant to users are covered;
- removed or deferred functionality is not presented as available;
- startup and access instructions are current;
- screenshots and interface terminology match the current application;
- known limitations and troubleshooting guidance are accurate;
- the Quick Start still represents the simplest successful path.

---

# Phase 5: Periodic refactoring

## 17. Refactor the codebase

Custom skill:

```text
$code-refactor
```

Refactoring is not necessarily executed for every slice.

It should be used periodically to reduce accumulated technical debt and improve the internal structure of the code without intentionally changing its observable behavior.

Typical triggers include:

- `$code-review` identifies structural or maintainability issues;
- several slices have introduced duplication;
- responsibilities have become unclear;
- modules or classes have grown too large;
- temporary implementation decisions have accumulated;
- new abstractions are now justified by repeated patterns;
- testability has deteriorated;
- dependencies between components have become difficult to manage;
- naming and structure no longer represent the domain clearly.

A practical rule is to consider refactoring:

```text
after a code review identifies meaningful structural issues
```

or:

```text
after every few completed slices
```

The exact frequency should depend on the state of the codebase rather than a rigid number.

## Refactoring workflow

```text
identify concrete technical debt
        ↓
define the refactoring scope
        ↓
confirm existing tests
        ↓
add characterization tests when necessary
        ↓
run tests and establish a baseline
        ↓
$code-refactor
        ↓
run the complete relevant test suite
        ↓
$code-review
        ↓
verify behavior and diff
        ↓
commit separately
```

Refactoring should normally be performed in a dedicated branch or dedicated commit so that structural changes are not mixed unnecessarily with feature behavior.

The refactoring skill must not:

- silently add new functionality;
- change product requirements;
- expand into unrelated modules;
- claim that behavior was preserved without verification;
- commit or push automatically.

---

# Updating the product scope during development

During implementation, new information may require changes to the overall product scope.

Examples include:

- stakeholders request a new workflow;
- an external integration becomes necessary;
- one slice becomes too large;
- two slices are strongly coupled and should be merged;
- a planned capability is no longer needed;
- implementation reveals a missing prerequisite;
- priorities change.

In such cases, return to:

```text
$requirements-engineering
```

The skill updates:

```text
docs/planning/Feature_slices.md
```

After the slice map is updated, continue with the next selected slice through the normal iterative workflow.

This creates a controlled hierarchy:

```text
Feature_slices.md
    defines the product scope and slice structure

spec.md
    defines one selected slice in detail

plan.md
    defines how that slice will be implemented

tasks.md
    defines the concrete implementation work

production code
    implements the approved slice
```

---

# Complete development lifecycle

```text
PROJECT INITIALIZATION
────────────────────────────────────────

Initialize repository and Spec Kit
        ↓
$speckit-constitution
        ↓
$architecture-exploration


PRODUCT DEFINITION
────────────────────────────────────────

$requirements-engineering
        ↓
Create docs/planning/Feature_slices.md
        ↓
Select recommended first slice


SLICE IMPLEMENTATION
────────────────────────────────────────

Create feature branch
        ↓
$speckit-specify
        ↓
$speckit-clarify
        ↺ until sufficiently clear
        ↓
optional $speckit-checklist
        ↓
$speckit-plan
        ↓
$speckit-tasks
        ↓
$speckit-analyze
        ↺ until sufficiently consistent
        ↓
$speckit-implement
        ↓
run tests and inspect diff
        ↓
$code-review
        ↺ correct and review again when needed
        ↓
verify
        ↓
$user-manual-creation
        ↓
review documentation diff
        ↓
commit
        ↓
push
        ↓
pull request or direct review
        ↓
merge into main


CONTINUOUS PRODUCT DEVELOPMENT
────────────────────────────────────────

Select next slice
        ↓
repeat the slice-implementation cycle
        ↓
update $requirements-engineering when scope changes
        ↓
update the user manual for user-visible changes
        ↓
use $code-refactor periodically
```

---

# Recommended practical workflow

## Once near the beginning of the project

```text
1. Initialize the project and repository
2. Run $speckit-constitution
3. Run $architecture-exploration
4. Run $requirements-engineering
5. Review docs/planning/Feature_slices.md
6. Confirm the first implementation slice
```

Architecture exploration may also be run before the constitution when the technology decision must be understood first.

## For every development slice

```text
1. Start from the latest main branch
2. Select the next slice from Feature_slices.md
3. Create a feature branch
4. Run $speckit-specify
5. Run $speckit-clarify until sufficiently clear
6. Optionally run $speckit-checklist
7. Run $speckit-plan
8. Run $speckit-tasks
9. Run $speckit-analyze
10. Correct findings and repeat analysis when necessary
11. Run $speckit-implement
12. Run tests and inspect the Git diff
13. Run $code-review
14. Correct blocking review findings
15. Repeat tests and code review where necessary
16. Run `$user-manual-creation` for user-visible changes
17. Review `User_Manual.md` as a first-time user
18. Inspect the documentation diff and report
19. Commit and push the branch
20. Review through a pull request or direct diff inspection
21. Merge into main
22. Update the slice status in Feature_slices.md
```

## Before a release or handover

```text
1. Run $user-manual-creation across all implemented slices
2. Verify Quick Start workflows against the current application
3. Review advanced scenarios, edge cases, and troubleshooting
4. Remove or mark outdated and unavailable behavior
5. Review recommended screenshots and documentation gaps
6. Commit documentation updates
```

## Periodically

```text
1. Review accumulated technical debt
2. Run $code-refactor when justified
3. Run tests
4. Run $code-review
5. Commit the refactoring separately
```

## When product scope changes

```text
1. Run $requirements-engineering
2. Update Feature_slices.md
3. Preserve unaffected slices
4. Update dependencies and priorities
5. Select the next ready slice
6. Continue with the regular Spec Kit cycle
```

---

# Main principles

## Project foundations are relatively stable

```text
$speckit-constitution
$architecture-exploration
```

These are normally established once and changed only when fundamental project rules or architectural decisions change.

## The slice map is the product-level ground truth

```text
$requirements-engineering
        ↓
docs/planning/Feature_slices.md
```

Requirements engineering manages the complete product scope and is revisited when that scope changes.

## Spec Kit is applied incrementally

```text
$speckit-specify
$speckit-clarify
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
```

These skills are executed iteratively for each selected vertical slice.

## User documentation follows verified implementation

```text
$user-manual-creation
```

The user manual is generated from the current implemented product and its development artifacts.

`Feature_slices.md` defines which product capabilities should be considered. Verified implementation and tests determine what is actually documented as available.

The manual always provides:

```text
Quick Start
    minimal setup and common use cases

Detailed Guide
    advanced workflows, edge cases, limitations, and troubleshooting
```

Documentation is updated incrementally after user-visible slices and reviewed comprehensively before releases and handovers.

## Review is mandatory before integration

```text
$code-review
```

Review ensures that implementation changes satisfy the specification and meet the project’s quality expectations.

## Refactoring is deliberate and periodic

```text
$code-refactor
```

Refactoring is triggered by concrete technical debt, code-review findings, or accumulated structural problems after several slices. It should not become uncontrolled redesign.

## Specifications are living agreements

A specification is not written once for the entire product.

The hierarchy is:

```text
Feature_slices.md = living agreement about overall product scope

spec.md = living agreement about one implementation slice

plan.md and tasks.md = technical path for delivering that slice

code = verified implementation of the agreed behavior

User_Manual.md = user-focused explanation of verified implemented behavior
```

This preserves iterative development while maintaining a clear and traceable connection between product scope, detailed requirements, technical planning, implementation, and review.
