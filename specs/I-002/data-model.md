# Data Model: FS-022 Consistent Labels, European Dates, and Actionable Messages

FS-022 adds no persisted business entity and no database migration. The models below are deployment configuration or transient presentation values derived from existing records and API responses.

## German Terminology Default Catalog

The source-controlled complete map shipped with the application.

| Field | Type | Rules |
|---|---|---|
| `key` | Stable string identifier | Uses `<concept>.<context>`; unique; never shown to users; cannot be customer-created |
| `value` | Unicode string | German, nonblank, single-line, control-character-free, complete for its context |

### Initial configurable concepts and contexts

| Concept | Supported contexts | Intent |
|---|---|---|
| `course` | `singular`, `plural`, `navigation`, `heading`, `fieldLabel`, `tableHeading` | Customer name for a course/teaching-offer concept |
| `lecturer` | `singular`, `plural`, `navigation`, `heading`, `fieldLabel`, `tableHeading` | Customer name for a teaching person/resource concept |
| `cohort` | `singular`, `plural`, `navigation`, `heading`, `fieldLabel`, `tableHeading` | Customer name for a student group concept |
| `room` | `singular`, `plural`, `navigation`, `heading`, `fieldLabel`, `tableHeading` | Customer name for a room concept |
| `schedule` | `navigation`, `heading` | Customer name for the planning/schedule workspace |
| `academicData` | `navigation`, `heading` | Customer name for the academic master-data workspace |

Each context is a separate complete value even when several defaults happen to be equal. Consumers request the exact contextual key; they do not derive forms or insert catalog values into ordinary sentences.

### Invariants

- Every schema key has exactly one non-empty shipped German default.
- The checked-in override-schema property set, backend default-map keys, and client `TerminologyKey`/expected-key set are identical and are compared by automated contract tests.
- No default key exists outside the client `TerminologyKey` union and override schema.
- Values affect presentation only. IDs, enum values, routes, filters, API fields, and stored names remain unchanged.
- Removing or renaming a stable key is a deployment-contract change and is not part of this slice.

## Customer Terminology Override

An optional operator-supplied UTF-8 JSON object selected at startup.

| Field | Type | Rules |
|---|---|---|
| property name | Existing terminology key | Must appear in the shipped catalog/schema; duplicate properties and unknown keys are invalid |
| property value | Unicode string | Nonblank after trimming; single-line; no control characters |

The object is partial: omission means use the shipped German default. An unset environment variable means there is no override. A set variable whose file is absent, unreadable, malformed, has the wrong root type, or contains any invalid entry fails startup.

The file contains no user record, language selection, message template, markup, script, or token-substitution instruction. React always renders values as text.

## Effective Terminology Catalog

An immutable full map held in FastAPI application state and copied into React memory during bootstrap.

```text
effective[key] = override[key] when supplied, otherwise default[key]
```

### Validation

- Contains the exact complete set of known keys.
- Contains no blank or raw/unresolved value.
- Server and client validate the same exact key set independently.
- The public response is all-or-nothing; an affected UI never renders before client validation succeeds.
- Direct component tests initialize deterministic shipped defaults in the shared Vitest setup. Tests for alternative catalogs or bootstrap failures isolate module state and cannot relax the production set-once invariant.

### Lifecycle

```text
No override configured -> validate defaults -> effective defaults -> service ready
Valid override configured -> validate defaults/file -> merge -> effective catalog -> service ready
Invalid configured override -> startup error -> service not ready
Valid service response -> client exact-set validation -> set once -> import/render selected UI
Fetch/response failure -> fixed German bootstrap error -> Retry -> repeat fetch/validation
```

Catalog changes require service restart and do not mutate business data.

## Calendar Date Value

An existing machine date and its transient human presentation.

| Field | Type | Rules |
|---|---|---|
| `iso` | `YYYY-MM-DD` string | Canonical API/client/storage/comparison value; strict real calendar day |
| `display` | `DD.MM.YYYY` string | Derived, zero-padded, same day as `iso` |

### Invariants

- `parseEuropeanDate(formatCalendarDate(iso)) === iso` for every valid supported date.
- Conversion never applies a timezone to a date-only value.
- Invalid or incomplete display text has no ISO submission value.
- Sorting, comparisons, URLs, logs, persistence, fixtures, and standards exports continue to use the existing machine representation.

## European Date Field State

A transient state owned by each `EuropeanDateField` instance.

| Field | Type | Meaning |
|---|---|---|
| `rawText` | string | Exact visible user input |
| `isoValue` | ISO date or null | Parsed value only while `rawText` is complete and valid |
| `touched` | boolean | User has interacted with the field |
| `submissionAttempted` | boolean | Owning workflow attempted to continue/save |
| `validity` | `empty`, `incomplete`, `format`, `impossible`, `before-min`, `after-max`, `valid` | Deterministic field state |
| `errorId` | stable DOM ID | Associates the active correction message with the input |

### State transitions

| From | Event | To | Effect |
|---|---|---|---|
| Initial valid ISO | Render/reset | `rawText=DD.MM.YYYY`, `valid` | Emits corresponding ISO |
| Any | User types/pastes | Recompute strict validity | Emits ISO only if valid; never retains old ISO while text is invalid |
| Invalid | Submit/continue | Same validity, attempted | Show German correction, set association, focus field through owner |
| Invalid | Correct text | `valid` | Clear active error and emit same-day ISO |
| Any | External value/reset changes | Synchronized state | Replace draft with formatted external value without timezone conversion |
| Optional value | Clear | `empty` | Valid only when field is not required |

Min/max and range ordering checks operate on parsed ISO values. No input is silently padded, day/month-swapped, or normalized to another date.

## Timestamp Presentation

An existing instant formatted for people.

| Field | Type | Rules |
|---|---|---|
| `machineValue` | Existing timestamp string | Retained in API and `<time dateTime>` |
| `displayDateTime` | string | `DD.MM.YYYY` plus established 24-hour time in `Europe/Vienna` |

Timestamp conversion may cross a UTC day because an instant is being shown in the institution timezone; this is distinct from date-only conversion, which may never shift days.

## User Problem

A transient, safe presentation item for one warning or failure.

| Field | Type | Rules |
|---|---|---|
| `key` | stable string | Unique within the rendered result; supports list identity and repeated-problem distinction |
| `tone` | `blocking` or `warning` | Reflects existing severity/save behavior; never changes the domain decision |
| `title` | German string | Plain-language condition or failed action; not a raw code |
| `details` | non-empty German string array | Separately states available affected context, known reason/values, saved/blocking status, and next guidance |
| `fieldId` | optional DOM control ID | Present for field-specific correction and used by `aria-describedby` |
| `action` | optional safe UI action | Label plus current surface callback or link; present only when already available and safe |

### Source context

A domain mapper may consume only facts already safely available to its current user:

- typed API status/code/field/safe metadata;
- affected record/field and attempted action supplied by the caller;
- known input preservation, save, and blocking state;
- existing local edit/retry/refresh/review callback availability;
- current domain values, formatted through presentation helpers.

Raw exception text, stack traces, bearer values, secrets, database/infrastructure details, or unvalidated backend prose are not fields of `UserProblem`.

### Message-state rules

| Condition | Required model behavior |
|---|---|
| Known field validation | Blocking; field ID; expected correction; preserved-input state; no unrelated action |
| Known non-blocking warning | Warning; saved/usable state; correction or intentional-retain guidance |
| Stale mutation | Blocking; action and record; current-state refresh/review before repeat; truthful draft state |
| Safe load failure | Blocking; affected load context; direct Retry callback when available |
| Ambiguous mutation connection failure | Blocking; outcome unknown; verify/refresh before any retry |
| Unexpected failure | Blocking; attempted action; known draft state; safest available guidance; no invented cause |
| Multiple problems | One `UserProblem` per issue; never concatenate into one sentence |

## Outside Recommended Window Problem

A specialized derived `UserProblem`; it is not a new business warning.

| Required fact | Source |
|---|---|
| Affected course/exam | Existing course name and exam configuration/context |
| Scheduled date | Existing exam date, formatted `DD.MM.YYYY` |
| Recommended start/end | Existing recommendation context, each formatted `DD.MM.YYYY` |
| Severity/blocking | Existing `outsideRecommendedWindow` non-blocking rule |
| Saved state | Existing active/working placement state known by the surface |
| Next action | Adjacent Edit when available, otherwise accurate review/feedback/retain guidance for the current surface |

The problem mapper does not recalculate the recommendation window or change whether the exam is valid/saved.

## Accountless Safe Finding Projection

The existing public finding response shape remains unchanged:

| Existing field | FS-022 behavior |
|---|---|
| `findingRef` | Existing stable privacy-safe derived reference |
| `category` | Existing allowlisted public category or `other` |
| `message` | Fixed German contextual text generated only from public-visible record data and validated allowlisted supporting values |
| `affectedSessionRefs` | Existing scoped public references |

Internal finding messages and unrestricted metadata never cross the projection boundary. If a fact required for precise safe text is unavailable, the projection acknowledges only the known condition/context and provides truthful review/feedback guidance; it does not invent the missing cause.

## Migration Inventory

Before a surface is considered migrated, its inventory row records:

| Field | Meaning |
|---|---|
| `surface` | Current planner/accountless page, panel, dialog, list, or notice |
| `terminologyKeys` | Approved configurable labels consumed there |
| `displayDates` | Date-only/range/timestamp locations and semantic kind |
| `dateEntries` | Entry controls, required/min/max/range behavior, multi-value behavior |
| `problemStates` | Known validation/warning/stale/connectivity/unexpected paths |
| `mapperOwner` | Component/page/API boundary that has sufficient safe context |
| `automatedCoverage` | Unit/component/integration tests proving behavior |
| `manualCoverage` | Browser/accessibility evidence where automation is insufficient |

Completion requires every approved current surface row to be accounted for; machine-only ISO fields and fixed German prose are marked explicitly excluded rather than silently skipped.
