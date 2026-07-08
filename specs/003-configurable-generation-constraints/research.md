# Research: Configurable Generation Constraints

## Decision: Persist constraints per course and semester

**Rationale**: The planning period is bounded by a selected semester, and office staff clarified that saved constraints should reload for later generation. Scoping by course and semester prevents a custom period or window set from one semester from becoming an invalid default in another semester.

**Alternatives considered**:

- Course-only persistence: rejected because custom dates are semester-bound and could leak invalid dates across semesters.
- Request-only constraints: rejected by clarification; office staff expect saved constraints to reload.

## Decision: Save custom constraints only after successful generation

**Rationale**: A successful generation proves the constraints are usable for the selected course's required sessions. Failed or blocked attempts must not replace a known-good saved constraint set.

**Alternatives considered**:

- Save on every edit: rejected because invalid drafts could become defaults before they have been validated.
- Save on failed generation attempt: rejected because impossible constraints should remain a rejected attempt, not a persisted planning setting.

## Decision: Model custom teaching windows independently from Study Type Time Windows

**Rationale**: Slice 3 allows office staff to define arbitrary weekly windows, so generated sessions may be based on windows that do not exist as study type defaults. The generator should accept normalized generation-window inputs rather than requiring every custom window to be promoted into the study type catalog.

**Alternatives considered**:

- Create Study Type Time Window rows for each custom window: rejected because custom constraints are course-semester-specific and should not change global study type defaults.
- Keep a single selected time window: rejected because Slice 3 explicitly requires one or more allowed weekly teaching windows.

## Decision: Keep source Study Type Time Window IDs optional

**Rationale**: Default windows can retain a source ID for traceability, while custom windows need only weekday, start time, end time, and stable order within the constraint set. Draft Sessions already store concrete date/start/end values, so review remains understandable even when the source window is custom.

**Alternatives considered**:

- Require a database ID for every generation window: rejected because it forces custom windows into a shared catalog.
- Drop window traceability entirely: rejected because tests and debugging benefit from knowing which input window produced a session.

## Decision: Add explicit constraint loading and clearing contracts

**Rationale**: The UI needs to load saved constraints or defaults whenever course/semester selection changes, and it needs a durable clear action that deletes saved constraints. Dedicated contracts keep generation constraints separate from review filters and avoid overloading the schedule review endpoint.

**Alternatives considered**:

- Add all saved constraints to `/api/planning-options`: rejected because constraints are scoped by course and semester and would grow the general options response.
- Use only the generation endpoint: rejected because staff need to see active constraints before generating.

## Decision: Reuse existing verification stack

**Rationale**: The constitution requires FastAPI and React/Vite. Existing backend tests already cover generation and API behavior, and existing frontend tests cover review components. Slice 3 can extend these without adding dependencies.

**Alternatives considered**:

- Add browser end-to-end tooling: rejected for this slice because component/API contract tests can verify the required behavior with lower setup cost.
- Add a scheduling optimization library: rejected because multi-course optimization and conflict-aware scheduling are explicitly out of scope.