# Data Model: FS-019 Streamlined Schedule Workspace

FS-019 adds no backend entity, database table, API schema, or migration. The model below describes client workspace state, one browser preference, and the relationships required to prevent mixed scheduling context.

## Schedule Destination

Represents one leaf below the Schedule navigation parent.

| ID | Label | Position | Visible workspace |
|---|---|---:|---|
| `calendar` | Calendar | 1 | Calendar planning, operational summary, deliberate List mode, and session pane |
| `versions` | Versions | 2 | Working/current lifecycle designations, actions, and history |
| `exams` | Exams | 3 | Requirements, eligibility, selection, constraints, preparation, and result |

### Invariants

- Calendar is the default child.
- Exactly one Schedule child is current while Schedule is the top-level view.
- Choosing a child changes no domain data.
- Academic Data remains a separate established hierarchy.

## Application Navigation State

| Field | Type | Initial value | Rules |
|---|---|---|---|
| `view` | `schedule | academic` | `schedule` | Existing top-level content owner |
| `scheduleDestination` | Schedule Destination ID | `calendar` | Changes only after any dirty guard commits |
| `scheduleExpanded` | Boolean | `true` while a child is current | Schedule children remain visible while Schedule content is current |
| `selectedAcademicCategory` | Existing Academic category ID | Existing default | FS-018 behavior unchanged |
| `academicExpanded` | Boolean | Existing FS-018 value | FS-018 behavior unchanged |
| `navigationPinned` | Boolean | Stored valid value, else `true` | Meaningful only on supported wide layout |
| `navigationOpen` | Boolean | `false` | Temporary narrow or unpinned navigation surface; never persisted |

`App` proposes destination changes to `CourseSchedulePage` and commits only an approved callback. It does not store a pending dirty-navigation intent or render a discard dialog.

### Persisted preference

| Property | Value |
|---|---|
| Key | `resource-planner.navigation.pinned.v1` |
| Value | Serialized boolean |
| Scope | Same browser/device |
| Fallback | Pinned |
| Failure behavior | Invalid values and read/write exceptions do not prevent application use |

No Schedule destination, semester, course, revision, filter, pane, or draft value is persisted.

## Shared Schedule Context

Represents server-backed selections owned by `CourseSchedulePage`.

| Field | Meaning | Validation/reconciliation |
|---|---|---|
| `semesterId` | Selected semester | Must exist in current catalog; choose an explicit valid fallback when unavailable |
| `courseId` | Selected planning or requirement-review course | Must belong to selected semester/context; clear or choose an explicit valid option when unavailable |
| `workingRevisionId` | Active editable revision when present | Must match lifecycle overview and selected semester |
| `publishedRevisionId` | Current published read context when present | Must match lifecycle overview and selected semester |
| `calendarRevisionRef` | Working or Current Published calendar read | Must resolve to one available stable revision identity |

### Destination projection

- Calendar identifies semester, calendar revision, and applicable course context.
- Versions identifies semester and lifecycle revision/designations.
- Exams identifies semester and any course whose exam requirement is being reviewed.
- A context change is applied once by the page owner and reflected by every workspace; hidden workspaces never retain a conflicting server context.

## Workspace Region State

| Field | Type | Persistence | Rules |
|---|---|---|---|
| `activeDestination` | Schedule Destination ID | Current application use | Equals the current Schedule child |
| `planningInputsVisible` | Boolean | Current mounted Schedule page only | Calendar-only and independent of navigation pin/open |
| `calendarMounted` | Constant true while Schedule page is mounted | N/A | Preserves same-use Calendar state |
| `versionsMounted` | Constant true while Schedule page is mounted | N/A | Uses the shared lifecycle state |
| `examsMounted` | Constant true while Schedule page is mounted | N/A | Preserves in-progress course selection/results |

Only the active region is exposed to layout, focus, and assistive technology. Hiding a clean region does not clear its permitted local state.

## Calendar View State

| Field | Meaning | Reconciliation |
|---|---|---|
| `mode` | Week, Day, Month, or deliberate List | Retain across same-context refresh and Schedule-child round trip |
| `anchor` | Date/period anchor | Retain unless selected semester/revision no longer supports it |
| `filters` | Course, cohort, lecturer, room, study type, session type, lifecycle, validation | Remove only unavailable values after refresh and announce adjustment |
| `selectedOccurrenceRef` | Stable `teaching:{id}` or `exam:{id}` | Retain while occurrence/revision remains available |
| `originOccurrenceRef` | Calendar item that opened the pane | Used for focus restoration; may become unavailable |
| `drilldown` | Month/day drilldown context | Retain across same-context refresh when still valid |
| `scrollPosition` | Active Calendar scroll-container offset | Preserve across pane open/edit/cancel/save/close and valid same-context refresh |

The existing semester key performs a hard reset for a genuine semester replacement. A workspace refresh token is data freshness, not view identity, and must not remount this state.

## Session Pane State

Use a discriminated state rather than independent booleans.

### Closed

```text
kind = closed
```

No selected pane content is exposed.

### Detail

```text
kind = detail
occurrenceRef = teaching:{id} | exam:{id}
originOccurrenceRef = stable Calendar occurrence reference
readOnlyReason = optional text
statusMessage = optional save/reconciliation result
```

### Editing

```text
kind = editing
occurrenceRef = teaching:{id} | exam:{id}
originOccurrenceRef = stable Calendar occurrence reference
baseline = normalized saved teaching or exam edit values
draft = current normalized edit values
fieldErrors = field-keyed validation feedback
serverFeedback = optional actionable feedback
saving = boolean
```

### Derived properties

- `sessionKind` derives from the occurrence reference prefix.
- `dirty` is `normalize(draft) != normalize(baseline)`; it is never stored independently.
- `editable` derives from current Working revision, canonical mutation record, and existing lifecycle/domain rules.
- Detail fields derive from the current calendar projection plus canonical draft/exam data; mixed revision sources are invalid.

## Pending Replacement Intent

Represents an action queued while pane state is editing and dirty. `CourseSchedulePage` is the sole owner of this union for both internal pane/context intents and application destinations proposed by `App`.

| Variant | Payload |
|---|---|
| `close-pane` | None |
| `select-occurrence` | Next stable occurrence reference |
| `schedule-destination` | Calendar, Versions, or Exams |
| `application-destination` | Schedule child or Academic Data child |
| `semester-change` | Next semester ID |
| `revision-change` | Next revision reference |
| `course-change` | Next course ID |

### Invariants

- At most one intent is pending.
- `App` never stores a second pending intent; it receives only the eventual approved destination callback.
- Keep editing clears the intent and leaves the draft unchanged.
- Discard resets the draft to baseline, clears edit state, and then applies exactly the queued intent.
- Resize, navigation pin/open, and Planning-input visibility are not replacement intents.
- Semantic current navigation changes only after the intent commits.

## Teaching Edit Model

| Field | Meaning |
|---|---|
| `sessionId` | Existing draft teaching session identity |
| `date` | Scheduled date |
| `startTime` | Scheduled local start |
| `endTime` | Scheduled local end |
| `lecturerId` | Assigned eligible lecturer |
| `roomId` | Assigned eligible room |
| `eligibleLecturers` | Existing current plus planning-option candidates |
| `eligibleRooms` | Existing current plus planning-option candidates |

The mapper from draft schedule data to this model is shared by deliberate List editing and pane editing. The established draft-session PATCH payload remains unchanged.

## Exam Edit Model

The existing exam editor fields, recommended ranges, override state, capacity feedback, lifecycle snapshot, confirmation, and API payload remain authoritative. FS-019 adds controlled draft/baseline and feedback ownership so the pane can derive dirty state and preserve it across layout changes.

## Revision Workspace Context

| Field | Meaning |
|---|---|
| `workingRevision` | Active editable draft revision, when present |
| `currentPublication` | Current immutable published revision, when present |
| `historicalRevisions` | Stable revision identities and lifecycle states |
| `expandedHistoryRevisionIds` | UI-only set controlling disclosed ordered event history |
| `pendingLifecycleAction` | Existing publish/review/abandon/restore confirmation state |

Event disclosure changes no lifecycle data.

## Exam Preparation Context

| Field | Meaning | Validation |
|---|---|---|
| `eligibleCourses` | Courses where `generationEligibility.eligible` is true | Selectable and shown first |
| `unavailableCourses` | Courses where eligibility is false | Not selectable; exact reason retained |
| `selectedCourseIds` | Selected eligible courses | Pruned after eligibility refresh |
| `requirementCourseId` | Course whose requirement is under review | Must exist in selected semester |
| `constraints` | Existing exam generation constraints | Existing validation unchanged |
| `preparationState` | Existing preparation/confirmation state | Existing FS-012 semantics |
| `result` | Existing per-course successes/failures | Associated with stable course IDs |

Selection count and preparation action derive from `selectedCourseIds` and remain outside the scrolling course list.

## State Transitions

| From | Event | To | Additional effects |
|---|---|---|---|
| Schedule initial | Application loads | Calendar current | Restore valid pin preference only |
| Calendar clean pane | Select Versions/Exams | Requested workspace current | Keep Calendar mounted and preserve pane |
| Versions/Exams | Return Calendar | Prior clean Calendar/pane | Reconcile semester/revision/session first |
| Pane closed/detail | Select occurrence | Detail for selected occurrence | Focus pane heading |
| Detail editable | Edit session | Editing with baseline=draft | Calendar mode/period/filters unchanged |
| Editing clean | Close/select/navigate/context change | Apply intent | No discard dialog needed |
| Editing dirty | Close/select/navigate/context change | Same edit plus pending intent | Open Keep editing / Discard decision |
| Dirty decision | Keep editing or Escape | Editing unchanged | Clear pending intent and return focus |
| Dirty decision | Discard | Apply queued intent | Reset draft; no domain mutation |
| Editing | Cancel | Current detail | Saved data unchanged |
| Editing | Save succeeds and refresh succeeds | Current detail | Calendar and summaries show saved state |
| Editing | Save succeeds, refresh fails | Detail/completed recovery state | Announce saved result and offer refresh/recovery |
| Editing | Save fails | Editing with same draft | Show actionable feedback |
| Editing | Refresh proves missing/noneditable | Accurate detail or closed | Explain state change and move focus safely |
| Any pane | Layout crosses presentation boundary | Same pane state | DOM/draft/errors unchanged |
| Wide pinned | Unpin | Wide unpinned | Persist false; reclaim shell width |
| Wide unpinned, closed | Open navigation | Wide temporary modal overlay | Focus enters overlay; background becomes unavailable |
| Wide temporary overlay | Escape/close | Wide unpinned, closed | Restore opener; destination unchanged |
| Wide temporary overlay | Pin | Wide pinned | Persist true; convert to persistent column without context change |
| Wide unpinned | Pin | Wide pinned | Persist true; current context unchanged |
| Any wide pin state | Enter narrow | Temporary nav closed | Retain stored wide preference |

## Derived Pane Presentation

| Condition | Presentation |
|---|---|
| Viewport width at or below 820px | Narrow full-screen modal |
| Viewport above 820px and Calendar pane container at least 70rem | Docked right column |
| Viewport above 820px and Calendar pane container below 70rem | Right overlay |

Presentation is derived rather than stored and never creates a second pane instance.

## Concurrency and failure rules

- The server remains authoritative for revision identity, editability, snapshots, conflicts, capacity, holidays, eligibility, and lifecycle transitions.
- A `409` or stale response never silently discards a draft. Authoritative refresh determines whether edit can continue.
- A selected occurrence that disappears closes or changes to an accurate state; it is never reconstructed from stale display data.
- A successful mutation and a failed follow-up read are reported as two distinct outcomes.
- Invalid or unavailable browser storage never blocks navigation.
