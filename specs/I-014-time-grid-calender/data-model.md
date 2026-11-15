# I-014 Presentation Data Model

This feature introduces transient response/view data only. No table, migration, persistent preference, snapshot schema or write operation changes. See [contracts/interfaces.md](contracts/interfaces.md) for the wire contract.

## Existing entities retained

- **Workspace / Revision**: `semester`, `selectedRevision`, `availableContexts`, `workspaceToken`, section availability. Existing Working/current-publication selection and immutable publication remain authoritative.
- **Course**: `courseRef`, `courseId`, name/code, cohort, `cohortCalendar`, resources and existing reference lists. Add nullable `cohortCalendarRef` from live or captured identity; labels alone are not identity.
- **Occurrence**: Existing teaching/exam identity, course/date/start/end/resources/findings. No duration, units or source changes. One occurrence may produce dated continuation pieces only if supported by existing valid source data; all pieces select the same record.
- **Finding**: Existing category, issue code and affected references. No severity, finding count or publication decision is derived from layout.

## TeachingWindowContext (read-only, per course)

| Field | Meaning and relationship |
| --- | --- |
| `courseRef` | Exactly one existing workspace course; includes zero-session courses |
| `calendarRef`, `calendarLabel` | Live/captured calendar identity and readable label; missing identity remains nullable, never guessed from label |
| `availability` | `available`, `unavailable` or `not_applicable`; distinguish known empty hours from unknown context |
| `basis` | `current_working`, `captured_published` or `unavailable`; identifies profile provenance independently of current validation basis |
| `reason` | Nullable explanation for missing/non-applicable context |
| `isCustom`, `sourceRevision` | Existing profile metadata; nullable when source is unavailable |
| `planningStartDate`, `planningEndDate` | Existing effective profile bounds; nullable if unavailable |
| `windows` | Source window collection, retaining separate identities and boundaries |
| `days` | Date-resolved references to applicable source windows, never a new permission store |

Contexts are projected from the exact profiles assembled for workspace validation. Current profile construction is not refactored to match older descriptions of custom constraints. Any discovered business-rule defect is separate work, not permission to change behavior here.

## SourceWindow

Fields: context-local `windowRef`, nullable `sourceTimeWindowId`, `kind` (`weekly`/`dated`), nullable `weekday`/`date`, `isIntensive`, `startTime`, `endTime`, `sortOrder`. A deterministic context-local reference may use source identity plus position; source IDs are not assumed globally unique across captured profiles. Older captures default missing kind to weekly and marker to false as existing code does.

Relations: belongs to one course context, referenced by zero or more resolved dates. Preserve overlap/adjacency as separate records. Use the unchanged `window_applies(window, date, allWindows)` rule, including dated-intensive suppression of recurring windows. Planning bounds use the same profile comparisons as existing evaluation; no new resource or holiday availability policy is computed.

## ResolvedWindowDay

Fields: ISO `date`, `applicableWindowRefs`, and `periodStatus` (`within_period`/`outside_period`). Cover every semester date plus occurrence dates outside it, preserving complete session inspection. Out-of-period dates have no effective applicable windows, while source records remain inspectable. Empty references with available context mean known no applicable teaching hours on that date. Missing date coverage is unknown/outside supplied coverage, never permission inferred by the browser. Month padding outside covered dates is labeled outside coverage/semester.

This resolves dates for display only. It does not determine whether a session fits a single window or satisfies holidays, resources or any other hard rule.

## Client-only models

- **Calendar view state**: existing mode, anchor, filters, selection; local Month expanded-date set and scroll position. Context changes follow existing reconciliation and unsaved-input protection. No new local-storage/database persistence.
- **Calendar group**: stable calendar ref and date, with labeled course-profile subgroups where effective contexts differ. Legacy unknown identity remains separately labeled per course; identical names are never merged by guesswork.
- **Timed block**: occurrence ref, date, start/end minute offsets, lane index/count. Start/end are measured from supplied clock fields; stable sort is start, end, occurrence ref. Assign the lowest free lane within each overlap-connected group; intervals meeting only at endpoints can reuse a lane. Layout does not produce findings.
- **Window paint**: supplied applicable intervals painted below blocks, with source boundaries retained in text. A visual union may prevent double paint; it never grants combined-session permission. Unknown context has separate paint/text.
- **Outside portion explanation**: elapsed interval(s) outside known effective coverage for an existing window finding, with date and duration. In the reference case, 16:00–17:20 = 80 elapsed minutes. A finding caused by failure to fit one complete source window must retain that reason even when a visual union covers all minutes; do not invent an outside duration of zero as proof of validity. Unknown context exposes no invented duration.
- **Month day**: date, chronological entries, first three entries by default, exact hidden count, count of entries with existing window findings, and compact per-calendar context disclosure. Count affected occurrences once even if they have several window findings.

## State transitions and invariants

1. Load/refresh -> replace response only for intended semester/revision using existing guards. Loading/error/last-known remains explicit.
2. Available context -> paint known applicable hours and text. Unavailable -> unknown cue/retry, retaining sessions. Known empty -> no-hours cue. These states are not interchangeable.
3. Change mode/date/filter -> reproject presentation only; no network write. Revision changes retain existing filter/selection reconciliation rather than inventing persistence.
4. Open date -> Day; open block/entry -> existing session pane. Close/return restores focus; disappeared source uses logical fallback.
5. Authorized correction -> existing mutation/validation flow -> existing refresh with new token. Cancel/failure preserves saved data.
6. Restricted lecturer review -> absent planner context is unavailable; no planner fetch, additional calendar disclosure or planner action.

All new response fields participate in the existing response hash before `workspaceToken` is assigned. Tests compare findings and saved-data fingerprints before/after reads and ensure source hours/marker/provenance affect the token without changing its algorithm.
