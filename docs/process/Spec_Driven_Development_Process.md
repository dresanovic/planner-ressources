Spec Driven Development Process



Now here is the overall development process with Spec Kit, from project start to iterative delivery.

Overall Spec Kit development process

The official Spec Kit flow is basically:

Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement

Spec Kit’s documentation describes the core process as Spec → Plan → Tasks → Implement, with the quickstart adding constitution, clarification, checklist/analyze, and implementation steps around that flow. Sources: https://github.github.com/spec-kit/ and https://github.github.com/spec-kit/quickstart.html

 

1. Project setup / initialization

This is done once per project.

Typical actions:

create repositoryinstall / configure Spec Kitinitialize projectconnect coding agent

The goal is simply to prepare the project so that Spec Kit can create and manage the specification artifacts.

In your case, this is already mostly done for the resource planner project.

 

2. Constitution: define project rules

Command:

/speckit.constitution

Purpose:

Define the non-negotiable project principles.

Examples:

Use TDD where possible.Keep implementation simple.Prefer minimal dependencies.All features must have acceptance criteria.No implementation without updated spec.

This is not a feature spec. It is more like the project’s rulebook. Spec Kit’s quickstart describes /speckit.constitution as the step for establishing core rules and principles for the project. Source: https://github.github.com/spec-kit/quickstart.html

You usually do this once at the beginning, then update only if your development principles change.

 

3. Feature discovery

This is where you collect the first rough requirement from yourself, the customer, or stakeholders.

Example:

The system should allow users to book meeting rooms.

At this point, the requirement can still be incomplete. That is normal.

The important thing is: you do not start coding yet.

 

4. Specify: create the feature spec

Command:

/speckit.specify

Purpose:

Describe what should be built and why.

The spec should focus on:

user goalsuser scenariosfunctional requirementsacceptance criteriaedge casesbusiness rules

It should avoid too much technical implementation detail.

Example:

/speckit.specify Build a meeting room booking system where employees can select a room, choose a time range, and create a booking.

Output is usually a feature folder like:

specs/001-meeting-room-booking/spec.md

 

5. Clarify: resolve open questions

Command:

/speckit.clarify

Purpose:

Find ambiguity before planning and coding.

This is the important customer-interaction step.

Typical questions:

Can users book rooms in the past?Can bookings overlap?Who can cancel a booking?Are approvals required?What happens if a room is unavailable?

You answer the questions, and the answers are integrated back into spec.md.

This is where Spec Kit fits iterative customer discovery very well: the customer does not need to know everything upfront, but each implementation slice should be clarified before it is planned and built.

 

6. Optional checklist: check spec quality

Command:

/speckit.checklist

Purpose:

Check whether the spec is complete enough.

This helps verify whether the requirements are clear before moving to technical planning. The quickstart mentions checklist generation after planning/spec refinement. Source: https://github.github.com/spec-kit/quickstart.html

For smaller projects, you may not need this every time. For customer projects, I would use it often.

 

7. Plan: create the technical plan

Command:

/speckit.plan

Purpose:

Translate the spec into a technical implementation approach.

Here you provide or confirm the stack and architecture.

Example:

/speckit.plan Use React for the frontend, FastAPI for the backend, SQLite for local persistence, and pytest for backend tests.

Output usually includes:

plan.mddata-model.mdcontracts/research.mdquickstart.md

depending on the project and template.

The plan answers:

What architecture?What data model?What APIs?What libraries?What constraints?What testing approach?

 

8. Tasks: create implementation tasks

Command:

/speckit.tasks

Purpose:

Break the plan into concrete work items.

Output:

tasks.md

The task list should be actionable for the coding agent.

Example tasks:

Create Booking entityAdd booking validation serviceAdd API endpoint for booking creationAdd test for overlapping booking rejectionAdd UI validation message

This is the bridge between planning and implementation.

 

9. Analyze: check consistency

Command:

/speckit.analyze

Purpose:

Check whether spec, plan, and tasks are aligned.

This is a quality gate before implementation.

It should detect problems like:

spec says future-only bookings, but tasks do not include validationplan mentions REST API, but tasks do not create endpointsacceptance criteria exist, but no tests are planned

For serious work, I would run this before implementation.

 

10. Implement: build the feature

Command:

/speckit.implement

Purpose:

Use the spec, plan, and tasks to implement the feature.

This is where code changes happen.

You can add instructions such as:

Implement only tasks related to the booking validation.Create tests first, then implement the code.Do not implement unrelated tasks.Summarize changed files and test commands.

So the command is still /speckit.implement, but you can guide the implementation style.

 

11. Verify implementation

After implementation, you check:

git statuschanged filestestsapplication behavioracceptance criteria

You should ask:

Does the implementation satisfy the spec?Are all relevant tests passing?Were unrelated files changed?Were tasks correctly completed?

Only then commit the implementation.

 

12. Review with customer

Now you show the result to the customer.

Important: do not show only code. Show behavior against the spec.

Example:

Customer feedback was:"Users should not be able to create bookings in the past."

Implemented behavior:- Past start time is rejected.- End time before or equal start time is rejected.- Future booking is accepted.- User sees a validation message.

This turns the spec into a shared agreement.

 

13. Merge into main

Only merge when the branch is complete:

spec updatedplan/tasks updatedimplementation donetests passedcustomer or self-review accepted

Then merge into:

main

For solo work, you can merge directly. For a more professional workflow, create a GitHub Pull Request and review the diff before merging. GitHub describes pull requests as a way to propose, review, and merge changes into another branch. Source: https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests

 

The iterative process

The important thing: you do not do this once for the whole project.

You repeat it for each meaningful feature or customer feedback item.

Feature / feedback idea→ create branch→ update/create spec→ clarify with customer→ plan→ tasks→ analyze→ implement→ verify→ review→ merge→ next feature

For your resource planner, it could look like this:

Iteration 1:Meeting room booking baseline

Iteration 2:Future-only booking validation

Iteration 3:Booking conflict detection

Iteration 4:User cancellation rules

Iteration 5:Admin approval workflow

Iteration 6:Notifications

Each iteration has its own focused spec-driven cycle.

 

Recommended practical workflow for you

For every new feature or feedback item:

1. Start on main2. Pull latest main3. Create branch4. /speckit.specify or update existing spec.md5. /speckit.clarify6. Commit spec update7. /speckit.plan8. /speckit.tasks9. /speckit.analyze10. Commit plan/tasks11. /speckit.implement12. Run tests and review changed files13. Commit implementation14. Push branch15. Review / Pull Request / merge into main16. Push main

For customer feedback on an existing feature, the flow is slightly different:

1. Create feedback branch2. Update existing spec.md3. Clarify if needed4. Update plan/tasks5. Analyze6. Implement7. Verify8. Merge

 

Main principle

Use Spec Kit like this:

Spec is not a document written once at the beginning.Spec is the living agreement for the next implementation slice.

That is how you avoid waterfall and use Spec Kit iteratively.

Confidence: High. This workflow is based on the documented Spec Kit command structure and the branch-based process you just practiced.

 

From <https://chatgpt.com/g/g-p-6a3252a9b1688191ab6cc4e82f374227/c/6a44c747-2534-83eb-8938-18b5f471ad72> 

 

