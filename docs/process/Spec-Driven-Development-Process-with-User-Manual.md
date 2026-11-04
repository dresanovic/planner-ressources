# Spec-Driven Development Process

This document defines the overall development process using **Spec Kit** together with the custom skills:

- `$architecture-exploration`
- `$requirements-engineering`
- `$code-review`
- `$user-manual-creation`
- `$code-refactor`

The process has four different levels:

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

Goal 1 — Specification Convergence
  $speckit-specify → $speckit-clarify → optional $speckit-checklist
  ↺ clarify and correct; maximum five correction cycles
        ↓ report → HUMAN APPROVAL before planning; manually start Goal 2
Goal 2 — Planning and Analysis Convergence
  $speckit-plan → $speckit-tasks → $speckit-analyze
  ↺ correct affected artifacts separately → analyze; maximum five cycles
        ↓ report → HUMAN APPROVAL before implementation; manually start Goal 3
Goal 3 — Implementation Convergence
  $speckit-implement → $speckit-converge → relevant tests
  ↺ implement appended gap tasks → converge → tests; maximum five cycles
        ↓ report → human decision; manually start Goal 4
Goal 4 — Code Review and Verification
  $code-review (read-only) → verification
  ↺ separate corrections → tests → review; maximum five cycles
        ↓ report → human decision; manually start Goal 5
Goal 5 — Documentation and Delivery
  $user-manual-creation → validate manual → review Git diff and status
  ↺ targeted documentation corrections → validate; maximum five cycles
        ↓ report → HUMAN APPROVAL for each intended Git operation
commit → approved push → review / pull request → approved merge

Every Goal: stop early on success; after five unsuccessful correction
cycles, stop and report non-convergence. No automatic Goal transitions.


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

The five Goals below group the existing skills without changing their order or responsibilities. They are repeated independently for every selected development slice:

```text
Goal 1: specify → clarify → optional checklist
        ↓ report and human approval; manually start
Goal 2: plan → tasks → analyze
        ↓ report and human approval; manually start
Goal 3: implement → converge → tests
        ↓ report and human decision; manually start
Goal 4: read-only code review → verification
        ↓ report and human decision; manually start
Goal 5: user manual → validate documentation → prepare delivery
        ↓ explicit human approval before commit, push, or merge
commit → push → review → merge

Each Goal: assess → targeted correction → reassess (maximum five cycles).
Stop early on success; stop and report if the limit is exhausted.
```

Each slice should normally have its own feature branch and specification artifacts. The manual should be updated in the same slice when the implemented behavior changes the way users operate the system.

---

## Codex Goals: execution model and shared rules

**Spec-Kit skills** perform individual activities and retain their own prerequisites, outputs, limits, and approval requirements. The custom review and documentation skills extend those activities. **Codex Goals** define an outcome, evidence required for completion, and bounded correction loops around those skills. **Spec-Kit Workflows** describe orchestration across commands and gates; they could eventually coordinate multiple Goals or stages.

### Verified Goal syntax and current execution

Checked on 2026-11-03: the installed CLI reports `codex-cli 0.150.1`, and `codex features list` reports `goals` as stable and enabled. Official OpenAI documentation describes `/goal <outcome>` in an interactive Codex session, plus `/goal` to inspect, `/goal pause`, `/goal resume`, and `/goal clear`. Goals persist an objective and can continue across turns; completion requires evidence. See [OpenAI: Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).

The examples below are interactive prompts, not shell commands. No `codex goal` subcommand or native five-cycle option is claimed. The cycle limit and approval gates are instructions in each Goal, not verified platform-enforced controls. Desktop command availability must be confirmed in the current client; if `/goal` is unavailable, ask Codex explicitly to create a Goal using the same objective and confirm that it became active.

**Current process:** a human selects and starts one Goal at a time, reviews its report, and authorizes the next stage. Automation occurs inside the selected Goal. The installed `.specify/workflows/speckit/workflow.yml` sequences specify, plan, tasks, and implement with review gates; it does not implement this five-Goal process. End-to-end orchestration of these Goals is a future integration proposal, requiring separate validation of dispatch, counters, approval persistence, stop handling, and evidence transfer. No new workflow command or configuration is assumed here.

### Rules applying to every Goal

- Bind the Goal to one selected slice, its feature directory, branch, and approved inputs. Preserve approved requirements and architectural decisions; follow the project constitution and KISS principle.
- Initial execution and assessment do not count as correction cycles. Allow at most **five correction cycles per Goal**. A cycle starts when addressing findings from a preceding assessment: announce cycle 1–5 and the findings in its correction batch before starting corrections. Multiple fixes in that batch count as one cycle; reassessment and relevant verification close it. Findings requiring another correction batch start the next cycle. This also applies to correction batches inside a skill invocation; invoking a skill does not define or reset a cycle. Internal skill limits, such as clarification question limits, still apply.
- Running analysis, tests, or reviews without corrections does not increment the counter. Waiting for answers or approval and performing approved Git operations do not consume correction cycles. A test or review finding starts a cycle only when corrective work begins.
- Preserve the completed-cycle count and any in-progress cycle across interruptions, context compaction, continuation turns, and fresh sessions of the same Goal. Resume an interrupted batch under its existing number; do not count it twice or silently reset the allowance. If previous state cannot be reconstructed reliably, stop and report the uncertainty before further corrections.
- Stop immediately when the explicit completion criteria are satisfied. Prefer minimal targeted corrections to affected artifacts over regenerating valid specifications, plans, or tasks.
- After the fifth unsuccessful correction cycle, stop substantive work and report non-convergence. Missing evidence, required human decisions, or unavailable checks can require an earlier stop. Do not mark the Goal successful because its cycle limit was reached.
- A stop report alone is not proof that runtime continuation has stopped. At an intervention or exhausted-cycle boundary, request human action; use `/goal pause` or `/goal clear` as appropriate to prevent further automatic work. Do not resume corrections or reset the allowance without human direction. Runtime lifecycle restrictions still apply.
- Do not advance to the next Goal automatically. Human approval is required before planning and implementation; all other transitions also require a human decision to start the next Goal. Completion of one Goal does not authorize the next.
- Preserve skill boundaries: `$speckit-analyze` and `$code-review` report findings read-only. Corrections are separate, explicitly authorized work, never edits performed by the review itself. Respect checklist ownership and skill-specific gates. Inspect applicable extension hooks before execution; if a hook would cross a Goal boundary or commit, push, or merge without approval, stop for human resolution rather than bypassing it.
- Do not change approved scope, architecture, or the constitution to force convergence. Escalate such decisions; after human approval, return to the affected earlier Goal and revalidate downstream artifacts.
- Maintain the execution summary below and include it in every stop or completion report, with changed artifacts and unavailable checks. Separate successful completion from a blocked or exhausted attempt. Never claim success without supporting evidence.
- Do not commit, push, or merge in any Goal without explicit human approval for the intended operation and reviewed changes. Delivery preparation does not grant that approval.

### Execution summary and session continuity

Use a concise summary in the current session after the initial assessment, at each cycle start and end, and before a handover or stop:

```text
Feature/slice: [identifier, feature-directory path, branch]
Goal: [number and name]; status: [initial / correcting / awaiting input / complete / stopped]
Cycles completed: [0–5]; current cycle: [1–5 in progress, or none]
Findings: [resolved references; remaining references and current batch]
Verification: [latest commands/results or artifact evidence; revision or files checked]
Handover: [next action; readiness for next Goal; approval evidence or approval needed]
```

Prefer this session summary; do not create a tracking file routinely. Before moving to a fresh session, persist the summary if existing feature-local notes do not already preserve it reliably. Reuse suitable notes without changing their intended meaning; otherwise use one small `goal-progress.md` in the feature directory, retaining each Goal's latest state and explicit human decisions. Update it at cycle boundaries and before stopping while cross-session continuity is needed, as a separate process step outside read-only reviews or append-only convergence. Keep this process record separate from Spec-Kit's standard artifacts: do not add tracking fields, task entries, or checkbox meanings to `spec.md`, `plan.md`, `tasks.md`, or checklists. No database or orchestration framework is needed.

In a fresh session, read this process, the selected feature's artifacts, and its execution summary before acting. Confirm the feature path and branch, recover the Goal, cycle count, unfinished batch, and approvals, and check that verification still applies to the current files. Do not infer cycle counts or human approvals from task markers, convergence-phase counts, or passing tests. If the record is missing or inconsistent and state cannot be reconstructed reliably, stop for human clarification; writing a new record cannot repair unknown history. Distinct Goals each start at zero; resuming the same Goal does not. Do not repeat completed creation skills just because a new session started.

This summary and optional file are process instructions, not a claim that Codex natively persists correction counters or transfers Goal state between chats. A fresh chat needs an explicitly started Goal with the recovered context; it does not inherit the previous chat's runtime Goal automatically.

For the copyable prompts, replace bracketed inputs before use. Each prompt incorporates the shared rules and continuity procedure above; load this document and recover the selected feature's state first. Starting a prompt authorizes only the work it describes, subject to the stated human gates. Stop immediately on evidenced completion, after five unsuccessful correction cycles, on a required human decision, or when execution state is uncertain; report the summary and never advance automatically.

### Goal 1 — Specification Convergence

**Purpose and sequence:** use `$speckit-specify` to define the selected slice, then `$speckit-clarify` iteratively, followed by optional `$speckit-checklist` for requirements quality. Reuse an existing specification for refinement rather than creating a duplicate feature.

**Correction logic:** after the initial specification assessment, treat each batch of clarification-driven or other requirements corrections and its reassessment as one cycle under the shared rules. Asking questions or waiting for answers alone does not increment the count; integrating accepted answers into a corrective batch does. Unresolved business decisions require human input, not invented answers. Custom checklists remain reviewer-owned: generation leaves items unchecked; assistance evaluating them requires an explicit reviewer request. They assess requirements writing, not working software.

**Completion criteria:** requirements and acceptance criteria are sufficiently clear, consistent, testable, and bounded; material decisions are resolved; the built-in spec-quality checklist supports readiness. Report custom-checklist status and any remaining nonblocking limitations.

**Human intervention:** answer clarification questions and review optional custom checklists. Stop for explicit specification approval before planning; Goal 1 never starts Goal 2.

```text
/goal Achieve Specification Convergence for [slice and feature directory], using [slice description or existing spec]. Read docs/process/Spec-Driven-Development-Process-with-User-Manual.md and apply its shared rules, execution summary, continuity procedure, and Goal 1 criteria. Recover prior state first; for new work run $speckit-specify, then $speckit-clarify and optional $speckit-checklist. Refine existing artifacts without duplicate creation. Assess initially, then correct and reassess in at most five tracked cycles; stop immediately on evidenced completion or the shared stop conditions. Ask humans to resolve business decisions. Report the execution summary and readiness, requesting specification approval before planning. Do not plan, commit, push, merge, or start another Goal.
```

### Goal 2 — Planning and Analysis Convergence

**Purpose and sequence:** after specification approval, run `$speckit-plan` → `$speckit-tasks` → `$speckit-analyze` to produce an implementation-ready technical path.

**Correction logic:** analysis stays read-only. Its installed skill requires explicit approval before remediation edits; submitting this Goal prompt provides that authorization for targeted in-scope corrections outside analysis. If authorization is absent or ambiguous, stop for it. One logical correction batch may update the plan and dependent tasks before reassessment; it counts as one cycle, not one per artifact or skill. Rerun only skills needed to propagate the changes, then analyze again; do not regenerate valid artifacts. Do not silently alter approved requirements or architecture.

**Completion criteria:** the plan includes the Simplicity Check; tasks are actionable, dependency-ordered, and traceable to requirements and necessary verification; analysis identifies no unresolved blocking inconsistency or constitution conflict. Report residual nonblocking findings and custom-checklist status.

**Human intervention:** confirm specification approval before starting. Escalate requirement or architectural changes and unresolved analysis issues. Require explicit approval of the implementation-ready plan and tasks before implementation.

```text
/goal Achieve Planning and Analysis Convergence for [feature directory] after [specification approval reference]. Read docs/process/Spec-Driven-Development-Process-with-User-Manual.md and apply its shared rules, execution summary, continuity procedure, and Goal 2 criteria. Recover prior state first; initially run $speckit-plan → $speckit-tasks → read-only $speckit-analyze as needed for the recovered state. I authorize separate targeted in-scope remediation outside analysis. Propagate only affected changes and reanalyze, at most five tracked correction cycles. Stop immediately on evidenced implementation readiness or the shared stop conditions. Report the execution summary and request plan/task approval before implementation. Do not implement, commit, push, merge, or start another Goal.
```

### Goal 3 — Implementation Convergence

**Purpose and sequence:** after plan/task approval, run `$speckit-implement` → `$speckit-converge`, then verify relevant tests. Convergence assesses the present implementation against spec, plan, tasks, and constitution; it is not a Git comparison or a code-quality review.

**Correction logic:** the local `$speckit-converge` definition permits only appending a new `## Phase N: Convergence` section with new sequential task IDs at the bottom of `tasks.md`; it never rewrites, renumbers, reorders, or deletes existing tasks, or modifies code, spec, or plan. A clean run leaves `tasks.md` byte-for-byte unchanged. Appending gap tasks records assessment findings; the correction cycle starts when `$speckit-implement` begins addressing them. Complete the appended in-scope tasks, then reassess with convergence and tests. Tests alone do not consume cycles. Investigate test failures within approved scope rather than weakening requirements or tests.

**Completion criteria:** approved tasks and any in-scope convergence tasks are implemented; acceptance criteria are evidenced; convergence reports no actionable gaps; relevant tests pass; unrelated changes are identified. Checked task markers alone do not establish completion.

**Human intervention:** respect implementation checklist gates and obtain decisions on scope changes or gaps that contradict approved intent. Report readiness and wait for the human to start Goal 4.

```text
/goal Achieve Implementation Convergence for [feature directory] after [plan/task approval reference]. Read docs/process/Spec-Driven-Development-Process-with-User-Manual.md and apply its shared rules, execution summary, continuity procedure, and Goal 3 criteria. Recover prior state first; preserve $speckit-implement → $speckit-converge and relevant tests. Implement appended in-scope gap tasks, then reassess with convergence and tests in at most five tracked correction cycles. Preserve converge's append-only contract and implementation checklist gates. Stop immediately when tasks and acceptance criteria are evidenced, convergence is clean, and relevant tests pass, or on the shared stop conditions. Report the execution summary and readiness for Goal 4; wait for human direction. Do not review, commit, push, merge, or start another Goal.
```

### Goal 4 — Code Review and Verification

**Purpose and sequence:** run read-only `$code-review`, classify findings, and verify the completed slice using relevant automated checks and acceptance evidence.

**Correction logic:** perform corrective implementation, test completion, or authorized artifact correction separately from review; rerun tests and `$code-review` after corrections, for at most five cycles. Use `$code-refactor` only for a justified behavior-preserving structural problem, followed by targeted tests, relevant broader verification, and review. If corrections affect completeness, recheck convergence; if they invalidate approved intent, stop and return to the affected earlier Goal with human direction.

**Completion criteria:** no unresolved blocking findings, relevant automated checks passing, adequate acceptance traceability, and reviewed changes consistent with approved requirements and architecture. Document nonblocking findings, verification limits, and the review recommendation; passing tests alone do not replace review.

**Human intervention:** obtain decisions on changed intent, disputed findings, or unavailable essential verification. Report readiness and wait for the human to start Goal 5.

```text
/goal Complete Code Review and Verification for [feature directory and Git review scope]. Read docs/process/Spec-Driven-Development-Process-with-User-Manual.md and apply its shared rules, execution summary, continuity procedure, and Goal 4 criteria. Recover prior state first; run read-only $code-review and relevant verification. I authorize separate targeted in-scope corrections and test completion, followed by verification and a fresh $code-review, in at most five tracked correction cycles. Follow Goal 4 rules for justified $code-refactor and completeness rechecks. Stop immediately when no blocking findings remain and current verification supports completion, or on the shared stop conditions. Report the execution summary and readiness for Goal 5; wait for human direction. Do not commit, push, merge, or start another Goal.
```

### Goal 5 — Documentation and Delivery

**Purpose and sequence:** run `$user-manual-creation` after verified implementation, validate Quick Start and Detailed Guide against actual behavior and passing tests, review all Git changes, and prepare the commit and merge proposal.

**Correction logic:** after initial documentation creation/update and validation, count each batch of documentation improvements addressing findings and its revalidation as one correction cycle. Waiting for delivery approval and Git operations do not consume cycles. Preserve accurate content and report unavailable functionality or conflicting evidence. Product defects discovered here require a human-directed return to implementation/review, not code changes hidden in documentation work.

**Completion criteria:** user-facing behavior is accurately documented (or a justified no-change result is evidenced), documentation gaps and limitations are explicit, final Git diff/status have been reviewed, relevant checks remain valid for the final changes, and proposed commit scope/message and merge target are ready for approval. Goal completion means **delivery preparation is complete**, not that Git operations occurred.

**Human intervention:** review the documentation and delivery proposal. Explicit approval is required before each intended commit, push, or merge; approval may cover clearly specified operations together. If changes invalidate the reviewed evidence or approved scope, revalidate and obtain renewed approval. Stop after preparation; never infer authorization from starting Goal 5.

```text
/goal Complete Documentation and Delivery preparation for [feature directory] after [review/verification evidence]. Read docs/process/Spec-Driven-Development-Process-with-User-Manual.md and apply its shared rules, execution summary, continuity procedure, and Goal 5 criteria. Recover prior state first; use $user-manual-creation and validate Quick Start and Detailed Guide against verified implementation and tests. Assess initially, then make targeted documentation corrections and revalidate in at most five tracked cycles. Stop immediately on evidenced documentation and delivery readiness, or on the shared stop conditions. Report the execution summary, final Git diff/status, proposed commit scope/message, and merge target. Request explicit human approval for intended Git operations. Do not commit, push, merge, or start another Goal; preparation is not authorization.
```

The numbered activities below remain the detailed methodology for these Goals. Any local repetition diagram is subject to the shared five-cycle ceiling and manual Goal transitions above.

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
repeat until sufficiently clear (Goal 1: maximum five correction cycles)
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
repeat until sufficiently consistent (Goal 2: maximum five correction cycles)
```

Implementation should not begin while material consistency problems remain unresolved.

`$speckit-analyze` is read-only. Apply remediation outside the skill with explicit authorization, then repeat analysis. Goal 2 ends with a report and human approval of the plan and tasks before implementation.

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

## 13. Converge the implementation

Skill:

```text
$speckit-converge
```

Purpose:

Verify that the completed implementation fully satisfies the specification, implementation plan, and task list.

Unlike `$code-review`, convergence checks **completeness**, not code quality.

Typical workflow:

```text
$speckit-implement
        ↓
$speckit-converge
        ↓
material gaps?
        ├─ Yes → implement remaining tasks
        │          ↓
        │    $speckit-converge
        └─ No
        ↓
$code-review
```

Run convergence once after completing a slice and repeat only if it identifies additional work.

Within Goal 3, allow at most five correction cycles, then stop and report if convergence is still not achieved. Convergence appends remaining work to `tasks.md`; `$speckit-implement` performs it. A clean report and passing relevant tests are required before reporting readiness for Goal 4, which the human starts separately.

---

## 14. Review the implementation

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

Within Goal 4, repeat this cycle until no blocking findings remain, with at most five correction cycles. Stop and report non-convergence when the limit is exhausted. Corrections are separate from the read-only review.

---

## 15. Verify the completed slice

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

## 16. Create or update the user manual

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
report delivery readiness
        ↓
explicit human approval → commit
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

## 17. Commit, review, and merge

Goal 5 prepares delivery and stops for explicit human approval before committing, pushing, or merging. This applies to specification and planning commits as well as implementation and documentation commits. Human approval to start a Goal does not authorize these Git operations.

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
human approval → commit specification artifacts
        ↓
human approval → commit planning artifacts
        ↓
human approval → commit implementation and documentation
        ↓
human approval → push branch
        ↓
create or inspect pull request
        ↓
human approval → merge into main
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

## 18. Refactor the codebase

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
explicit human approval → commit separately
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
Goal 1: $speckit-specify → $speckit-clarify → optional $speckit-checklist
        ↺ targeted corrections and reassessment, maximum five cycles
        ↓ report → human approval before planning; manually start
Goal 2: $speckit-plan → $speckit-tasks → $speckit-analyze
        ↺ separate artifact corrections → analyze, maximum five cycles
        ↓ report → human approval before implementation; manually start
Goal 3: $speckit-implement → $speckit-converge → tests
        ↺ implement gap tasks → converge → tests, maximum five cycles
        ↓ report → human decision; manually start
Goal 4: $code-review (read-only) → verify
        ↺ separate corrections → tests → review, maximum five cycles
        ↓ report → human decision; manually start
Goal 5: $user-manual-creation → validate → review complete Git diff
        ↺ documentation corrections → validate, maximum five cycles
        ↓ report and delivery proposal
explicit human approval → commit
        ↓
explicit human approval → push
        ↓
pull request or direct review
        ↓
explicit human approval → merge into main

All Goals stop early on success or report non-convergence after five
unsuccessful correction cycles. No automatic transitions between Goals.


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
4. Start Goal 1: specify → clarify → optional requirements-quality checklist
5. Review its evidence and explicitly approve the specification before planning
6. Manually start Goal 2: plan → tasks → read-only analysis
7. Correct authorized findings separately and repeat analysis
8. Review its evidence and explicitly approve the plan/tasks before implementation
9. Manually start Goal 3: implement → converge → relevant tests and diff inspection
10. Implement appended convergence tasks and reassess when needed
11. Review the outcome and manually start Goal 4
12. Run read-only code review → separate corrections → tests → repeat review
13. Review verification evidence and manually start Goal 5
14. Create/update the user manual for user-visible changes; validate actual behavior
15. Review User_Manual.md as a first-time user and inspect all Git changes
16. Report delivery readiness, proposed commits, and merge target
17. Obtain explicit human approval before committing and pushing
18. Review through a pull request or direct diff inspection
19. Obtain explicit human approval before merging into main
20. Update the slice status in Feature_slices.md based on verified delivery

Each Goal: initial assessment, then at most five correction cycles;
stop early on success, otherwise stop and report. Never advance automatically.
```

## Before a release or handover

```text
1. Run $user-manual-creation across all implemented slices
2. Verify Quick Start workflows against the current application
3. Review advanced scenarios, edge cases, and troubleshooting
4. Remove or mark outdated and unavailable behavior
5. Review recommended screenshots and documentation gaps
6. Obtain explicit human approval before committing documentation updates
```

## Periodically

```text
1. Review accumulated technical debt
2. Run $code-refactor when justified
3. Run tests
4. Run $code-review
5. Obtain explicit human approval before committing the refactoring separately
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
$speckit-checklist
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge
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
