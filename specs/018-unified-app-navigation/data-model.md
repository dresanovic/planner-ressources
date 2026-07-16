# Data Model: FS-018 Unified Application Navigation

FS-018 introduces no persistent or domain data. The model below describes only ephemeral client navigation state and the fixed destination metadata used to render the single hierarchy.

## Academic Data Category

Represents one implemented Academic Data child destination.

| Field | Meaning | Validation |
|---|---|---|
| `id` | Stable client identifier | Exactly one of `semesters`, `cohorts`, `courses`, `study-types`, `time-windows`, `lecturers`, `rooms` |
| `label` | Visible destination label | Exactly Semesters, Cohorts, Courses, Study types, Time windows, Lecturers, or Rooms |
| `position` | Place beneath Academic Data | Unique integer 1–7 matching the confirmed order |

### Fixed ordered set

1. `semesters` — Semesters
2. `cohorts` — Cohorts
3. `courses` — Courses
4. `study-types` — Study types
5. `time-windows` — Time windows
6. `lecturers` — Lecturers
7. `rooms` — Rooms

The ordered set is the shared source for navigation rendering and Academic Data category typing; all seven children are fixed implemented destinations, and no runtime availability state is modeled. It does not describe catalog records.

## Current Destination

Identifies the one leaf whose content is displayed and whose navigation control is current.

| Variant | Fields | Meaning |
|---|---|---|
| Schedule | `kind = schedule` | Existing Schedule view is current; no Academic Data child is current |
| Academic Data child | `kind = academic`, `category` | The named Academic Data child is current and Academic Data is active/expanded |

### Invariants

- Exactly one variant is current.
- Academic Data itself is never a current destination because it is disclosure-only.
- An Academic Data current destination always references one of the seven fixed categories.
- Choosing the already-current variant is a no-op.

## Navigation State

Owns the complete non-domain state permitted by FS-018.

| Field | Type | Initial value | Rules |
|---|---|---|---|
| `currentDestination` | Current Destination | Schedule | Changes only when a different leaf is selected |
| `selectedAcademicCategory` | Academic Data Category ID | `semesters` | Retained while Schedule is current and changed only by child selection |
| `academicExpanded` | Boolean | `false` on initial Schedule | Forced `true` for an Academic child; otherwise retains the most recent permitted value |
| `narrowPanelOpen` | Boolean | `false` | Meaningful only in narrow presentation; closes on leaf selection, close control, Escape, or transition to wide |
| `responsivePresentation` | Derived `wide` or `narrow` | Derived from existing 820px boundary | Not persisted and never creates a second navigation state source |

### Relationships

- `currentDestination.category`, when present, equals `selectedAcademicCategory`.
- `currentDestination.kind = academic` implies `academicExpanded = true`.
- `responsivePresentation = wide` implies `narrowPanelOpen = false` as a modal state, even though the shared sidebar remains visible.
- The narrow and wide presentations read the same destination/category/expansion values.

## Focus State

Focus is transient interaction context rather than stored product data.

| Context | Required target |
|---|---|
| Narrow panel opens | First meaningful panel control |
| Narrow panel closes without selection | The control that opened it |
| A different leaf is selected | The selected view's shared content start/primary heading target |
| Academic children collapse while focus is within them | Academic Data disclosure control |
| Responsive state changes while the panel is open | A visible, operable navigation or content control; never hidden content |

## State Transitions

| From | Event | To | Additional effects |
|---|---|---|---|
| Initial Schedule, collapsed | Activate Academic Data | Schedule, expanded | Children become visible; no content changes |
| Schedule, expanded | Activate Academic Data | Schedule, collapsed | Focus remains/moves to disclosure; no child is current |
| Any Schedule state | Select Academic child | Academic child, expanded | Store category; close narrow panel; focus content |
| Academic child, expanded | Activate Academic Data | Unchanged | Collapse is refused so active context remains visible |
| Academic child | Select Schedule | Schedule, expanded | Retain selected category and expansion; close narrow panel; focus content |
| Any destination | Select the same leaf | Unchanged | Do not reset page state or move focus to content |
| Narrow closed | Open navigation | Narrow open | Focus enters panel; background becomes unavailable |
| Narrow open | Escape/close | Narrow closed | Destination unchanged; focus returns to opener |
| Narrow open | Select different leaf | Narrow closed at selected leaf | Focus moves to content after render |
| Narrow open | Cross into wide | Wide sidebar | Clear modal state and background blocking; preserve destination/category/expansion |

## Persistence and concurrency

- No navigation state is saved to a database, browser storage, URL, cookie, or external service.
- A new application use starts on Schedule with Academic Data collapsed and Semesters retained only as the initial potential category.
- Navigation state changes are local synchronous client interactions. There is no concurrent-write, revision, migration, or conflict-resolution behavior.
- Catalog and scheduling domain data, requests, revisions, and saved workflow state remain governed by FS-007 and FS-008 and are not part of this model.
