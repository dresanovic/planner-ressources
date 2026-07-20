# Feature Specification: Institution-Wide Holiday Calendar and Avoidance

**Working Branch**: `master`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Create FS-011 so a planner can maintain one institution-wide holiday calendar, prevent all current automatic teaching generation modes from scheduling on holidays, and see refreshed non-blocking holiday alerts for saved or manually placed sessions without silently changing those sessions."

**Constitution Requirements**: This spec MUST be updated before production
implementation. All user stories require clear acceptance criteria and
independent test paths.

## Clarifications

### Session 2026-07-17

- Q: What happens to a holiday's previous date and name after it is changed or removed, including through a future calendar import? → A: No holiday history is retained; the current calendar state replaces or removes the prior holiday data.

### Session 2026-07-20

- Q: How should holidays appear in existing semester review views before FS-014 delivers the broader calendar workspace? → A: Existing review shows holiday alerts only on affected sessions; standalone holiday display waits for FS-014.
- Q: What explanation should generation provide when holiday exclusion contributes to an incomplete or failed result? → A: Identify each substantiated relevant holiday by name and date while retaining the generation mode's existing outcome rules.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain the Institution Holiday Calendar (Priority: P1)

A planner creates, views, edits, and removes full-day holidays with readable names in one calendar that applies across the institution.

**Why this priority**: A reliable, planner-maintained calendar is the source of truth for holiday avoidance and review. Generation and alerts cannot be trusted until the dates are current.

**Independent Test**: Start with an empty holiday calendar; create, inspect, rename, redate, and remove holidays; after each action verify in holiday administration that only the saved current holiday definition remains.

**Acceptance Scenarios**:

1. **Given** no holiday exists on a valid calendar date, **When** the planner saves that date with a non-empty name, **Then** the holiday appears once in the institution-wide calendar with the saved date and name.
2. **Given** holidays exist across multiple years, **When** the planner views the holiday calendar, **Then** the planner can identify every current holiday by date and readable name.
3. **Given** a holiday exists, **When** the planner changes its name or moves it to another valid date that has no current holiday, **Then** the current calendar contains only the updated date and name and no duplicate current holiday date is created.
4. **Given** a holiday exists, **When** the planner confirms its removal, **Then** the holiday record is removed and it no longer constrains future generation or produces current holiday alerts.
5. **Given** a holiday has been used to evaluate earlier generation or alerts, **When** the planner edits it, **Then** the earlier date or name is not retained as holiday history and all current behavior uses the updated definition.
6. **Given** a holiday has been used to evaluate saved sessions, **When** the planner removes it, **Then** no historical holiday record is retained, the saved sessions remain unchanged, and their current holiday alerts are refreshed.
7. **Given** a holiday change is invalid, duplicates another current holiday date, or is based on a holiday that has changed since it was opened, **When** the planner attempts to save, **Then** no holiday data changes and the planner receives an understandable correction or refresh message.

---

### User Story 2 - Keep Automatic Generation Off Holidays (Priority: P2)

A planner runs any existing automatic teaching-schedule generation mode knowing that every current institution-wide holiday is treated as a hard unavailable date.

**Why this priority**: Preventing newly generated teaching sessions from landing on holidays is the primary scheduling outcome of the slice.

**Independent Test**: Maintain holidays inside the candidate date range, run single-course generation, multi-course generation, and FS-010 conflict-aware semester optimization with otherwise feasible holiday and non-holiday placements, and verify that saved generated sessions use only non-holiday dates.

**Acceptance Scenarios**:

1. **Given** a single-course generation request has feasible holiday and non-holiday placements, **When** generation runs, **Then** no generated teaching session is placed on a current holiday.
2. **Given** a multi-course generation request has competing placements that include current holidays, **When** generation runs, **Then** no generated teaching session for any selected course is placed on a current holiday.
3. **Given** an FS-010 optimization request could increase scheduled units only by using a current holiday, **When** optimization runs, **Then** that holiday placement is rejected and the saved result follows FS-010's existing complete, partial, unchanged, or failed outcome rules.
4. **Given** current holidays leave no permitted placement for some requested units, **When** generation completes, **Then** the existing generation mode reports its applicable incomplete or unsuccessful outcome without placing sessions on a holiday and identifies each holiday name and date substantiated as relevant to that outcome.
5. **Given** a holiday is added, edited, or removed before a new generation request begins, **When** generation evaluates dates, **Then** it uses the current holiday calendar rather than a superseded definition.
6. **Given** the holiday calendar changes after generation begins and the prepared result would conflict with the current calendar, **When** the result is about to be saved, **Then** the affected result is not saved as current and the planner is told to review or retry against the refreshed holiday calendar.
7. **Given** a course already has a saved session on a date that later becomes a holiday, **When** the holiday is saved, **Then** the existing session remains unchanged; only a later planner-initiated generation operation may replace it under that generation mode's established replacement rules.

---

### User Story 3 - See and Refresh Holiday Alerts in Schedule Review (Priority: P3)

A planner reviewing a semester sees a non-blocking alert on every saved teaching session that falls on a holiday, including generated sessions, manually created sessions, and manually edited sessions. Standalone holiday display outside administration is deferred to FS-014.

**Why this priority**: Saved schedules may predate a holiday change or contain deliberate manual exceptions. Visible, current context keeps the planner informed without silently overriding planner-controlled work.

**Independent Test**: Prepare generated and manual sessions on ordinary dates, add or move holidays onto those dates, edit sessions onto and off holidays, and remove holidays; after each change, verify that session alerts match the current calendar while all saved session fields remain unchanged unless the planner explicitly edited them and no standalone holiday entries appear in existing review views.

**Acceptance Scenarios**:

1. **Given** the selected semester contains a current holiday with no session on its date, **When** the planner uses the existing semester review views, **Then** no standalone holiday entry is required there; the holiday remains visible in the administration view.
2. **Given** one or more saved teaching sessions fall on a current holiday, **When** the planner reviews or inspects them, **Then** every affected session shows a non-blocking holiday alert containing the holiday date and name.
3. **Given** a structurally valid manual session is created or edited onto a current holiday, **When** the save completes, **Then** the session remains saved and its holiday alert is visible in the refreshed review state.
4. **Given** a holiday is added or moved onto a date containing saved sessions, **When** the holiday change completes, **Then** those sessions remain unchanged and gain the applicable holiday alert.
5. **Given** a holiday is removed or moved away from a date containing saved sessions, **When** the holiday change completes, **Then** the sessions remain unchanged and alerts that no longer apply are removed.
6. **Given** a session is manually moved off a holiday or onto a different holiday, **When** the edit completes, **Then** its holiday alert is removed or updated to match the saved date and current holiday name.
7. **Given** a session has a holiday alert and other validation alerts, **When** the planner inspects it or changes review filters or view mode, **Then** all applicable alerts remain available and associated with the correct session.

### Edge Cases

- A holiday name containing only whitespace is invalid; surrounding whitespace does not create a distinct name.
- Only one current institution-wide holiday may occupy a calendar date. An attempted create or edit to a date already used by another current holiday is rejected without changing either record.
- Valid leap-day dates are accepted; invalid dates are rejected without changing the calendar.
- Past and future dates are both maintainable and follow the same edit and removal rules.
- A current holiday outside the selected semester remains in the institution-wide calendar but does not appear as holiday context for that semester or affect its generation.
- If more than one holiday is substantiated as contributing to an incomplete or failed generation result, the outcome identifies each relevant holiday by name and date without claiming that holidays were the only cause when other constraints also contributed.
- Holiday treatment applies to the session's full calendar date. Partial-day closures, time ranges, and overnight closure rules are outside this slice.
- Adding one holiday can affect many sessions across courses in the same semester; every affected session must receive its own alert without being moved or deleted.
- Editing a holiday's date from one occupied session date to another must remove obsolete alerts and add new alerts in the same refreshed review state.
- Renaming a current holiday updates current alerts to the new readable name; the previous name is not retained as holiday history.
- If holiday context cannot be evaluated for a session because required date or calendar information is unavailable, the session must not be presented as holiday-safe; the planner receives a clear validation-data message.
- A failed or stale holiday save leaves the prior calendar, generation constraints, session data, and alert state unchanged.
- An explicit planner-initiated generation may replace saved sessions according to the selected generation mode's existing rules; holiday maintenance itself never triggers regeneration, movement, or deletion.

### Scope Boundaries

This slice includes one planner-maintained institution-wide calendar of named full-day dates; current-state holiday create, view, edit, and removal behavior without holiday history; use of current holidays as hard unavailable dates by single-course, multi-course, and FS-010 teaching generation; holiday-specific explanations when exclusion contributes to incomplete or failed generation; non-blocking holiday alerts on affected sessions in existing semester review; and alert refresh after holiday or session changes.

This slice does not add campus-specific or regional calendars, religious or personal leave calendars, external holiday providers or imports, timed or half-day closures, exam scheduling behavior, a new calendar-centered workspace, automatic regeneration, or automatic movement or deletion of saved sessions. Exam generation may consume the institution-wide calendar in FS-012, and broader calendar presentation may build on it in FS-014, but neither later slice is delivered here.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one institution-wide holiday calendar available to the planner.
- **FR-002**: The planner MUST be able to create a holiday with exactly one valid calendar date and one non-empty readable name.
- **FR-003**: The planner MUST be able to view current holidays across past and future years, including each holiday's date and name.
- **FR-004**: The planner MUST be able to edit the current date or name of a holiday, subject to validation rules.
- **FR-005**: The planner MUST be able to remove a holiday after confirming the action.
- **FR-006**: The system MUST allow no more than one current holiday on the same institution-wide calendar date.
- **FR-007**: The system MUST reject holiday changes containing an invalid date, a blank or overlong name, a duplicate current date, an unconfirmed removal, or a stale revision without partially changing the existing holiday calendar.
- **FR-008**: After a holiday is edited successfully, the system MUST use only the updated date and name as holiday data and MUST NOT retain the superseded values as holiday history.
- **FR-009**: After a holiday is removed successfully, the system MUST NOT retain a historical holiday record, while leaving every saved session unchanged.
- **FR-010**: Every current holiday date MUST be a hard unavailable date for new single-course teaching generation.
- **FR-011**: Every current holiday date MUST be a hard unavailable date for new multi-course teaching generation.
- **FR-012**: Every current holiday date MUST be a hard unavailable date for new FS-010 conflict-aware semester optimization.
- **FR-013**: As an overarching invariant across the three modes covered by FR-010 through FR-012, no in-scope automatic generation mode MUST save a newly generated teaching session on a current holiday.
- **FR-014**: When holiday exclusions contribute to incomplete or failed placement, each generation mode MUST retain its established complete, partial, unchanged, or failure behavior rather than bypassing a holiday and MUST identify each substantiated relevant holiday by name and date without presenting holidays as the only cause when other constraints also contributed.
- **FR-015**: A generation result prepared against superseded holiday data MUST NOT overwrite current schedule state when it would place a session on a current holiday; the planner MUST receive an understandable stale-result outcome.
- **FR-016**: Existing semester review views MUST present holiday context only through alerts on affected sessions and MUST NOT add standalone holiday entries as part of FS-011.
- **FR-017**: The system MUST identify every saved teaching session whose date is a current holiday, whether the session was generated, manually created, or manually edited.
- **FR-018**: Every saved teaching session on a current holiday MUST show a non-blocking alert containing the holiday date and readable name.
- **FR-019**: A holiday alert MUST NOT by itself prevent an otherwise valid manual session create or edit operation from being saved.
- **FR-020**: After a holiday is created, edited, or removed, the visible holiday context and all affected session alerts MUST refresh to match the saved current calendar.
- **FR-021**: After a session is generated, created, edited, deleted, or replaced, its holiday alert state and the alert state of other affected sessions MUST refresh to match the saved semester state.
- **FR-022**: Holiday alerts MUST remain associated with the correct sessions when the planner filters review results, switches existing review modes, or inspects a session alongside other validation alerts.
- **FR-023**: Creating, editing, or removing a holiday MUST NOT automatically move, delete, regenerate, or otherwise modify any saved session.
- **FR-024**: When required holiday-validation context is unavailable, the system MUST show an understandable validation-data issue rather than declaring the affected session holiday-safe.
- **FR-025**: This slice MUST NOT add campus or regional calendars, external provider integration, timed closures, exam scheduling, a replacement calendar workspace, or automatic repair of holiday collisions.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each implemented user story where automated testing is practical.
- **TR-002**: Holiday maintenance tests MUST cover valid create, view, edit, remove, duplicate-date, invalid-date, stale-change, and no-history behavior.
- **TR-003**: Generation tests MUST verify holiday exclusion independently for single-course generation, multi-course generation, and FS-010 optimization, including complete, partial, unchanged, failed, and stale-result paths where applicable, plus the correct holiday name and date in each substantiated holiday-related explanation.
- **TR-004**: Schedule-review tests MUST verify non-blocking alerts for generated and manual sessions, coexistence with other alerts, refresh after holiday and session changes, and the absence of standalone holiday entries in existing review views.
- **TR-005**: Preservation tests MUST verify that holiday maintenance alone never changes or removes saved sessions and that superseded or removed holiday values are not retained as holiday history.
- **TR-006**: Any exception to automated test-first work MUST document the reason and manual verification path in the plan.

### Key Entities *(include if feature involves data)*

- **Institution Holiday**: A named full calendar date that currently applies across the institution and makes that date unavailable to automatic scheduling.
- **Institution Holiday Calendar**: The planner-maintained collection of current institution holidays across calendar years; there is exactly one such scheduling calendar in this slice.
- **Draft Session**: A saved teaching session, generated or manual, that is never silently changed by holiday maintenance and receives a non-blocking alert when its date is a current holiday.
- **Holiday Alert**: Current review context that identifies an affected session and the matching holiday date and name without blocking planner-authorized manual work.
- **Generation Request**: A single-course, multi-course, or FS-010 automatic teaching-planning operation that must treat current holidays as hard unavailable dates.

## Dependencies

- **Required — FS-007: Academic Planning Data Administration** supplies the established planner-facing administration patterns this slice extends.
- **Required — FS-010: Conflict-Aware Semester Optimization** supplies the unavailable-date constraint boundary and coordinated generation behavior that this slice must populate with maintained holidays.
- Existing FS-001, FS-005, FS-006, and FS-009 behavior is integration context, not an additional slice dependency: it supplies single-course and multi-course generation, non-blocking validation alerts, and manual session workflows without being redefined.
- FS-012 exam scheduling and FS-014 calendar workspace are downstream consumers or extensions, not prerequisites or deliverables of FS-011. FS-013 publication behavior must not require FS-011 to retain superseded holiday records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of acceptance examples, the planner can create, rename, redate, and remove a holiday and can identify the saved current date and name immediately after each successful action.
- **SC-002**: At least 90% of representative planner users can add a named holiday and find it again on their first attempt in under two minutes without developer assistance.
- **SC-003**: Across single-course generation, multi-course generation, and FS-010 optimization acceptance datasets, 100% of newly saved generated teaching sessions avoid every current holiday in the applicable date range.
- **SC-004**: In 100% of tested cases where holidays contribute to incomplete or failed placement, generation follows the selected mode's established outcome, saves no holiday placement, and identifies every substantiated relevant holiday by the correct name and date.
- **SC-005**: In 100% of review examples, every generated, manually created, or manually edited teaching session on a current holiday displays the correct holiday date and name, while sessions on non-holiday dates display no holiday alert and existing review views display no standalone holiday entries.
- **SC-006**: After a successful holiday or session change, affected holiday display and alerts match the saved state within 2 seconds for a reference semester containing up to 500 sessions and 50 current holidays, without requiring the planner to leave and reopen the semester.
- **SC-007**: In 100% of holiday create, edit, and removal validation examples, no saved session changes date, time, room, lecturer, cohort, units, or existence solely because the holiday calendar changed.
- **SC-008**: In 100% of holiday edit and removal examples, superseded or removed holiday dates and names no longer appear in the holiday calendar, generation constraints, or current holiday alerts.
- **SC-009**: At least 90% of representative planner users can identify the affected session and understand the holiday name and date within two interactions after seeing a holiday alert.
- **SC-010**: All applicable acceptance scenarios from FS-001, FS-005, FS-006, FS-009, and FS-010 continue to pass except where those specifications intentionally delegate unavailable-date administration or holiday alerting to FS-011.

## Assumptions

- The planner-only MVP has one planner-user role with authority to maintain the institution-wide holiday calendar; authentication and finer-grained permissions remain outside this slice.
- Each maintained holiday is a full institution-local calendar date. No start time, end time, half-day, or time-zone-specific closure behavior is needed in FS-011.
- One current holiday per date is sufficient. If several observances share a date, the planner uses one readable combined name rather than separate current records.
- Manual administration remains authoritative until FS-017 defines external synchronization; this slice has no provider ownership or conflict-resolution rules.
- FS-011 treats the holiday calendar as current planning input and retains no prior holiday versions or deleted holiday records.
- A successful edit replaces the prior holiday date or name for all current generation and alert behavior. A successful removal deletes the holiday record from current holiday behavior.
- Future iCalendar or CSV import may create, update, or remove current holiday records, but import formats, matching rules, and synchronization behavior remain outside FS-011.
- FS-013 must define any publication-specific context it needs without requiring FS-011 to retain historical versions of changed or removed holidays.
- Holiday alerts follow the established non-blocking validation model: automatic generation must avoid holidays, while otherwise valid planner-authorized manual placement may remain saved with a visible warning.
- Holiday administration does not introduce a new semester relationship. The one calendar spans years, and review or generation uses only current holidays relevant to its selected date range.
- Standalone holiday display is available in holiday administration. Existing semester review views show holidays only through affected-session alerts until FS-014 introduces broader calendar presentation.
- The selected generation mode's existing replacement, partial-result, preservation, and failure rules remain authoritative after holiday dates are removed from its feasible choices.
