# Feature Specification: Consistent Labels, European Dates, and Actionable Messages

**Working Branch**: `master`

**Created**: 2026-08-10

**Status**: Specified

**Input**: User description: "Provide one simple customer-configurable catalog
for selected German application terms and labels, display calendar dates
throughout the application as DD.MM.YYYY, and replace generic warnings and
errors with precise, contextual, actionable German messages. Store this
initiative in specs/I-002/."

**Constitution Requirements**: This specification must be updated before
production implementation. Every user story has explicit acceptance scenarios
and an independent test path. Implementation planning must select the simplest
solution that satisfies the approved scope, with tests created or updated before
production behavior wherever practical.

## Clarifications

### Session 2026-08-10

- Q: How must user-facing date-entry controls present the European date format? → A: Date fields always display and accept `DD.MM.YYYY`; an accessible calendar picker may also be provided.
- Q: How should messages provide the user's next recovery action? → A: Provide a direct button or link beside the message when the action is safe and available; otherwise point precisely to the existing control.
- Q: How is language and customer-specific terminology configured? → A: One optional customer override file may be supplied during deployment or startup; one effective terminology set and the German language are active for the installation, with no runtime switch.
- Q: Must a customer catalog contain every fixed interface string or only terminology overrides? → A: Keep ordinary application copy in German; ship German terminology defaults and let the customer file override only selected reusable terms.
- Q: How are German grammatical and UI-context variants represented for configurable terms? → A: Each configurable UI context has its own complete value, such as singular, plural, navigation, and table-heading labels; no automatic grammatical inflection is used.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand and Act on Reported Problems (Priority: P1)

As a planner or accountless lecturer, I receive a plain-language German warning or
error that tells me what happened, which record, field, or action is affected,
why the condition occurred when the reason is known, whether it blocks my work,
and what I can do next.

**Why this priority**: A context-poor message can prevent users from completing
or confidently continuing a planning task even when the underlying application
behavior is correct. The supplied Courses overview screenshot demonstrates this
problem directly.

**Independent Test**: Trigger representative known validation warnings, field
errors, failed operations, stale-data responses, connectivity failures, and an
unexpected failure. Confirm that every resulting message contains the available
context and a truthful next action, that multiple problems are distinct, and
that no message relies on an internal code or exposes sensitive diagnostics.

**Acceptance Scenarios**:

1. **Given** an exam for `KI Grundlagen` is scheduled outside its recommended
   period, **When** the Courses overview reports the condition, **Then** the
   message identifies the affected course or exam, shows the scheduled date and
   recommended start and end dates as `DD.MM.YYYY`, identifies the condition as
   non-blocking, confirms whether the current placement remains saved, and tells
   the planner how to edit the date or retain the intentional override.
2. **Given** a user submits a field value that violates a known rule, **When**
   validation rejects the action, **Then** the message identifies the field,
   states the expected value or rule, preserves the user's other valid input
   where possible, and directs the user to the field that needs correction.
3. **Given** an operation cannot be completed because the displayed data is
   stale, **When** the failure is shown, **Then** the message names the attempted
   action and affected record, explains that the record changed, and states
   whether the user must refresh, review current values, or repeat the action.
4. **Given** the application cannot reach its service, **When** a load or save
   attempt fails, **Then** the message names the attempted action, distinguishes
   a connection problem from a validation problem, states whether entered work
   remains available, and provides a direct retry control when retry is safe and
   available or points precisely to the existing recovery control otherwise.
5. **Given** the exact cause of a failed action is unavailable, **When** the
   fallback message is shown, **Then** it names the attempted action, does not
   invent a cause, provides the safest available retry or refresh guidance, and
   does not show stack traces, internal exception text, bearer values, secrets,
   or raw infrastructure details.
6. **Given** one action produces multiple problems, **When** they are presented,
   **Then** each problem is separately readable and actionable instead of being
   merged into one undifferentiated sentence.

---

### User Story 2 - Read and Enter European Calendar Dates (Priority: P2)

As a planner or accountless lecturer, I see and enter calendar dates in the
familiar zero-padded `DD.MM.YYYY` form everywhere that dates are intended for
people, without changing the represented day.

**Why this priority**: ISO dates are widespread in the current interface and
slow recognition for the intended European users. A uniform display convention
also removes ambiguity between day and month.

**Independent Test**: Review every current planner and accountless lecturer
surface that displays or accepts a calendar date, including list, calendar,
detail, form, notice, dialog, and generated-message states. Confirm the exact
display convention, accessible date entry, correct boundary-day behavior, and
unchanged machine-facing contracts and exports.

**Acceptance Scenarios**:

1. **Given** a stored calendar date of `2026-09-11`, **When** it appears in a
   user-facing list, calendar, detail pane, summary, dialog, notice, or message,
   **Then** its numeric date is displayed as `11.09.2026`.
2. **Given** a user-facing date range from `2026-09-11` through `2026-10-02`,
   **When** the range is displayed, **Then** both endpoints appear in the
   European form and the range remains unambiguous.
3. **Given** a user enters or selects a calendar date, **When** the date control
   is displayed and operated by pointer or keyboard, **Then** the visible value
   always uses and accepts `DD.MM.YYYY`, an optional accessible calendar picker
   uses the same visible field value, and a valid entry represents the same
   calendar day submitted through the existing workflow.
4. **Given** an invalid or incomplete European date is entered, **When** the user
   attempts to continue, **Then** the application identifies the date field,
   shows the expected `DD.MM.YYYY` form, and does not silently reinterpret it as
   a different day or month.
5. **Given** a date near a daylight-saving or timezone boundary, **When** it is
   displayed anywhere in the application, **Then** formatting does not move it
   to the previous or next calendar day.
6. **Given** a date is sent through an existing machine interface, stored,
   sorted, compared, logged, placed in a URL, or included in a standards-based
   export, **When** this feature is applied, **Then** the established machine
   representation and behavior remain unchanged.

---

### User Story 3 - Configure Customer-Specific German Terminology (Priority: P3)

As a deployment operator, I can supply one customer-specific override file so
that an installation consistently uses the customer's chosen terms for selected
German domain and workflow concepts without rebuilding the application,
changing user data, or editing individual screens.

**Why this priority**: A small deployment-time terminology catalog lets the same
German application package match different institutional vocabulary while
remaining simpler than a full translation catalog, runtime language switching,
or an administration system.

**Independent Test**: Start one installation with the shipped German terminology
defaults and another with a customer file that overrides a representative
subset. Verify that the selected terms change everywhere they are used on the
next startup without rebuilding, unspecified terms retain their German defaults,
ordinary German application copy remains unchanged, and invalid overrides cannot
produce blank labels or raw keys.

**Acceptance Scenarios**:

1. **Given** no customer override file is supplied, **When** the installation
   starts, **Then** all configurable terms use the shipped German defaults and
   the rest of the application remains German.
2. **Given** a customer override changes one configurable term used in multiple
   current screens, **When** the installation next starts, **Then** every
   catalog-backed occurrence uses the customer wording without rebuilding the
   application or modifying those screens individually.
3. **Given** one concept has singular, plural, navigation, and table-heading
   labels, **When** the customer overrides those contexts, **Then** each complete
   configured value appears in its corresponding context without automatic
   grammatical transformation or token substitution.
4. **Given** a customer override omits a configurable term, **When** the
   installation starts, **Then** that term uses its shipped German default.
5. **Given** a customer override contains an empty, unreadable, or unknown term
   entry, **When** the installation starts, **Then** the problem is reported to
   the deployment operator and no user receives an empty label or raw key.
6. **Given** an ordinary German sentence, instruction, complete message
   template, or other fixed copy is not a configurable term, **When** customer
   overrides are applied, **Then** that copy remains unchanged.
7. **Given** a course name, lecturer name, room name, user-entered description,
   or contextual problem detail is displayed, **When** catalog wording changes,
   **Then** that stored or dynamically supplied value remains unchanged.

### Edge Cases

- Single-digit days and months are displayed with leading zeroes.
- Leap day, end-of-month, end-of-year, semester-boundary, and daylight-saving
  dates retain the represented calendar day.
- An open-ended or partially unavailable date range names the available endpoint
  without manufacturing a missing date.
- A message with a known affected record but an unknown technical cause still
  names the record and action while acknowledging that the cause is unavailable.
- A message with a known rule but no safe correction does not promise an action
  that the current user or surface cannot perform.
- A recovery control is not duplicated beside a message when the same action is
  already clear, adjacent, and safer to perform through the existing control;
  the message identifies that control precisely instead.
- A non-blocking warning cannot be styled or worded as if the save failed; a
  blocking error cannot imply that the action succeeded.
- When retry could duplicate an operation whose outcome is unknown, the message
  directs the user to refresh or verify the current state before retrying.
- Very long record names and multiple simultaneous messages remain readable,
  wrap without hiding recovery actions, and do not break the supported layout.
- Repeated messages remain distinguishable to assistive technology and do not
  move focus unexpectedly on every background refresh.
- A catalog value containing punctuation, diacritics, or a longer phrase remains
  readable in every consuming control without changing the underlying record.
- A customer override containing German diacritics or longer institutional terms
  remains readable without changing ordinary application copy.
- A customer override for one grammatical or UI context cannot silently replace
  a different context or trigger automatic inflection inside fixed German copy.
- User-visible dates embedded inside problem messages, confirmations, empty
  states, and accessibility text follow the same date convention as visible
  schedule content.
- Technical dates intended exclusively for interchange, diagnostics, or source
  fixtures are not reformatted merely because they resemble a calendar date.

## Requirements *(mandatory)*

### Functional Requirements

#### Controlled labels

- **FR-001**: The product MUST ship one complete German default catalog for the
  selected configurable terminology and MUST accept one optional
  customer-specific override file supplied during deployment or startup.
- **FR-002**: Each configurable term MUST have a stable identifier and one
  non-empty German default value for every supported grammatical or UI context;
  a customer override MAY replace any subset with non-empty Unicode wording.
- **FR-003**: Configurable terminology MUST be limited to selected reusable
  German domain and workflow concepts, such as the customer-specific names for
  Course, Lecturer, Cohort, Room, Schedule, and Academic Data. Each supported
  singular, plural, navigation, heading, field, or table context MUST use its
  own complete catalog value. The product MUST NOT derive grammatical forms or
  substitute catalog tokens into ordinary sentences, instructions, notices,
  confirmations, or complete warning or error message templates; those remain
  fixed German application copy.
- **FR-004**: Every current planner and accountless lecturer occurrence of a
  selected configurable term MUST obtain that term from the effective catalog,
  consisting of customer overrides applied over the shipped German defaults.
- **FR-005**: Changing a catalog value MUST update every consuming occurrence
  on the installation's next startup without rebuilding the application or
  modifying stored user or planning data.
- **FR-006**: Deployment or startup validation MUST detect an empty, unreadable,
  unknown, or unresolved customer override before an affected user interface is
  served. An omitted override MUST use its shipped German default.
- **FR-007**: A delivered user interface MUST NOT display an empty label or a raw
  catalog identifier in place of required wording.
- **FR-008**: User-entered values, academic record names, resource names, and
  dynamic contextual details MUST remain outside the fixed-text catalog and
  MUST NOT be renamed by catalog changes.
- **FR-009**: The application language MUST be German. The product MUST NOT
  expose runtime language switching, per-user language preferences, translation
  management, or user-facing terminology administration. Changing customer
  overrides is a deployment or startup operation.

#### European date presentation

- **FR-010**: Every explicit numeric calendar date intended for a user MUST be
  presented as a zero-padded two-digit day, two-digit month, and four-digit year
  in the exact order `DD.MM.YYYY`.
- **FR-011**: FR-010 MUST apply to planner and accountless lecturer lists,
  calendars, cards, detail panes, summaries, forms, dialogs, confirmations,
  notices, empty states, generated user-facing messages, and accessibility text.
- **FR-012**: Every user-facing numeric date range MUST format each available
  endpoint according to FR-010 and MUST communicate range direction
  unambiguously.
- **FR-013**: Date entry controls MUST always display and accept the
  `DD.MM.YYYY` convention, support keyboard operation, and preserve an entered or
  selected valid calendar day through submission. An accessible calendar picker
  MAY supplement the field but MUST NOT replace it with a browser-dependent
  visible date format.
- **FR-014**: Invalid or incomplete date entry MUST identify the affected field,
  state the expected `DD.MM.YYYY` form, and MUST NOT silently reinterpret the
  value as a different date.
- **FR-015**: Date presentation MUST preserve the source calendar day across
  institution-local timezone and daylight-saving boundaries.
- **FR-016**: When a user-facing timestamp includes a numeric calendar date, its
  date portion MUST follow FR-010 while the established 24-hour time and timezone
  meaning remain unchanged.
- **FR-017**: Existing machine-facing date representations used for APIs,
  persistence, comparison, ordering, URLs, logs, standards-based exports, and
  source fixtures MUST retain their established formats and semantics.

#### Actionable warnings and errors

- **FR-018**: Every known validation warning or operation failure MUST state in
  plain German what condition or action is being reported.
- **FR-019**: Every known message MUST identify the affected record, field, or
  attempted action with the most specific context safely available to the user.
- **FR-020**: When the cause, violated rule, expected value, or relevant boundary
  values are known, the message MUST present them in user-facing terms.
- **FR-021**: Every known message MUST state whether the condition blocks the
  requested action or is non-blocking and whether the affected record remains
  saved or usable when that status is known.
- **FR-022**: Every known message MUST provide at least one correction, retry,
  refresh, review, or intentional-retention action that the current user can
  actually perform on or from the current surface. When the action is safe and
  directly available, the message MUST include an adjacent button or link;
  otherwise it MUST point precisely to the existing control that performs the
  action.
- **FR-023**: A message MUST NOT claim a cause, outcome, saved state, or recovery
  action that the system cannot determine.
- **FR-024**: Internal codes MAY be shown as secondary supporting information
  only when safe and useful, but MUST NOT be the primary or sole user-facing
  explanation.
- **FR-025**: Multiple simultaneous problems MUST be presented as distinct
  readable items with their own context and guidance.
- **FR-026**: The outside-recommended-window warning MUST identify the affected
  course or exam, display the scheduled date and recommended start and end dates
  under FR-010, state that the condition is non-blocking, state whether the
  current placement remains saved, and offer the available edit-or-retain path.
- **FR-027**: Field-validation messages MUST be programmatically associated with
  the affected control and MUST communicate the expected correction without
  relying on color alone.
- **FR-028**: Newly presented blocking errors and urgent operation failures MUST
  be programmatically announced to assistive technology without requiring users
  to discover them visually.
- **FR-029**: Non-blocking warnings and status guidance MUST be identifiable as
  such to assistive technology and MUST NOT be communicated as blocking alerts.
- **FR-030**: Message content and recovery actions MUST remain readable and
  operable at every supported viewport size, with text enlargement, and by
  keyboard.
- **FR-031**: Connectivity failures MUST be distinguished from validation,
  permission, stale-data, and unexpected service failures whenever the failure
  category is known.
- **FR-032**: A stale-data message MUST tell the user to obtain and review the
  current state before repeating a conflicting action and MUST state how unsaved
  input is affected when known.
- **FR-033**: An unexpected-failure fallback MUST name the attempted action,
  preserve or describe the status of user-entered work when known, and offer the
  safest available retry or refresh guidance without inventing an unavailable
  cause.
- **FR-034**: User-facing messages MUST NOT expose stack traces, raw internal
  exception text, bearer values, secrets, private tokens, database details, or
  infrastructure identifiers.
- **FR-035**: Current domain rules, warning severity, save/block behavior,
  permissions, and operation results MUST remain unchanged by this presentation
  feature.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each
  implemented user story wherever automated verification is practical.
- **TR-002**: The complete current user-facing surface inventory MUST be checked
  for eligible catalog labels, explicit numeric calendar dates, and known
  warning or failure states.
- **TR-003**: Automated tests MUST cover representative label changes and
  missing-label detection, including confirmation that raw catalog identifiers
  and empty required labels cannot reach a released interface.
- **TR-004**: Automated tests MUST cover date display, range display, date entry,
  invalid entry, leap-day, year-boundary, and timezone-boundary cases without a
  calendar-day shift.
- **TR-005**: Automated tests MUST verify the message-content requirements for
  known validation, field, operation, stale-data, connectivity, and unexpected
  failure categories, including the motivating outside-recommended-window case.
- **TR-006**: Accessibility verification MUST cover programmatic field-error
  association, appropriate announcement semantics, keyboard operation, visible
  focus, non-color-only severity, text enlargement, and message wrapping.
- **TR-007**: Existing contract, persistence, sorting, standards-based export,
  business-rule, save/block, and authorization tests MUST confirm that this
  feature changes presentation only.
- **TR-008**: Frontend behavior MUST pass the project's established static,
  component, interaction, accessibility, and production-delivery checks relevant
  to the changed surfaces.
- **TR-009**: Any behavior that cannot be verified automatically MUST have a
  documented manual verification path covering the applicable acceptance
  scenario before implementation is considered complete.

### Key Entities

- **German Terminology Catalog**: The shipped mapping from every selected stable
  terminology identifier to its non-empty German default.
- **Customer Terminology Override**: The optional deployment-supplied subset of
  catalog entries that replaces selected German defaults for one installation.
- **Terminology Entry**: A stable identifier, its non-empty German default, and
  an optional non-empty customer value for one selected reusable concept in one
  grammatical or UI context. Singular, plural, navigation, heading, field, and
  table contexts are independent entries rather than automatically derived
  forms. An entry changes presentation only and is not a user-managed business
  record.
- **Display Date**: A human-visible representation of an existing calendar date
  or date endpoint. It retains the source calendar day while presenting it as
  `DD.MM.YYYY`.
- **Problem Message Context**: The safely available facts needed to explain one
  warning or failure: condition or attempted action, affected record or field,
  reason or relevant values, blocking and saved-state information, and available
  next actions. It does not create a new persisted business entity.
- **Problem Item**: One separately readable warning or error presented to a
  user. Multiple problem items may result from one attempted action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the approved inventory of current planner and accountless
  lecturer surfaces, 100% of occurrences of selected configurable terms use the
  effective catalog, and changing a sampled override updates every intended
  occurrence on the next startup without an application rebuild.
- **SC-002**: Deployment or startup verification detects 100% of sampled empty,
  unreadable, unknown, or unresolved customer overrides; omitted overrides use
  German defaults, and no reviewed installation displays a blank value or raw
  catalog identifier.
- **SC-003**: In the approved user-facing date inventory, 100% of explicit
  numeric calendar dates and range endpoints display as `DD.MM.YYYY`, including
  leap-day and timezone-boundary samples, with zero observed calendar-day shifts.
- **SC-004**: Users can enter a valid European date and correct an invalid date
  using pointer-only or keyboard-only interaction, with 100% of acceptance test
  attempts preserving the intended calendar day.
- **SC-005**: 100% of inventoried known warning and failure scenarios contain
  the safely available action or condition, affected context, reason or relevant
  values, blocking and saved-state information, and a truthful next action.
- **SC-006**: In usability validation, at least 9 of 10 representative users can
  explain the motivating outside-recommended-window condition and choose a valid
  next action within 30 seconds without assistance.
- **SC-007**: Accessibility verification finds no blocking issue in field-error
  association, message announcement, severity identification, keyboard access,
  visible focus, text enlargement, or message readability on supported layouts.
- **SC-008**: Existing automated regression checks show zero changes to domain
  decisions, save/block outcomes, permissions, machine-facing date contracts,
  or standards-based exports attributable to this feature.

## Assumptions

- The application is German-only. Different customer installations may override
  selected German domain and workflow terms without requiring different
  application builds.
- The optional customer override file is supplied as deployment or startup
  configuration and may be source-controlled with that customer's deployment
  configuration. Users do not select a language or edit wording while using the
  application.
- The catalog covers only selected reusable terminology and derived labels.
  Ordinary German sentences, complete messages, stored academic data,
  user-entered content, and dynamic contextual values remain outside it.
- Each configurable grammatical or UI context uses a complete catalog value.
  No German inflection engine, pluralization logic, or token replacement inside
  fixed application copy is required.
- The existing planner and accountless lecturer surfaces form the complete
  initial coverage inventory, including infrequent dialogs, empty states, and
  failure states.
- `DD.MM.YYYY` applies to every explicit human-visible numeric calendar date.
  User-facing weekday and month names are German. Existing 24-hour times,
  durations, timezone meaning, and number formatting remain unchanged unless
  required to present the date unambiguously.
- User-facing date controls always display and accept `DD.MM.YYYY` with
  accessible keyboard entry. An accessible calendar picker may supplement this
  behavior; implementation planning will choose the simplest conforming control
  without changing machine contracts.
- Existing domain validation and error details provide the facts required for
  known messages. When a fact is unavailable, the message follows the safe
  unknown-failure behavior instead of adding new business rules.
- Recovery uses current screen actions. A message adds a direct action only when
  that action is safe and already available; otherwise it directs the user to
  the existing control. No generic recovery workflow or automatic corrective
  action is assumed.
- User-visible diagnostic reference identifiers are not required for this
  slice. They may be proposed later only if a concrete support workflow requires
  them.
- FS-019 and the implemented validation behavior of earlier slices are available
  dependencies. No external system or new business-data persistence is needed.
