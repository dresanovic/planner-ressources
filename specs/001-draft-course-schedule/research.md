# Research: Draft Course Schedule

## Decision: Use a pure scheduling service as the core feature boundary

**Rationale**: The most important behavior is deterministic schedule generation from known inputs. A pure service can be tested first without HTTP, storage, or UI concerns, which matches the project constitution's test-first requirement.

**Alternatives considered**:

- Put scheduling directly in the API endpoint: rejected because it would mix validation, persistence, and algorithm behavior.
- Put scheduling in the frontend: rejected because generation must be authoritative and reusable for later planner features.

## Decision: Use SQLAlchemy/Alembic with SQLite for the first implementation

**Rationale**: SQLite keeps local setup lightweight while SQLAlchemy/Alembic provide migration discipline and a cleaner path to PostgreSQL later. This feature needs persisted draft sessions so regeneration can replace the previous generated draft for a course.

**Alternatives considered**:

- In-memory storage: rejected because replacement behavior and persistence boundaries would not be meaningfully tested.
- PostgreSQL immediately: rejected for the first slice because it adds setup overhead before the core scheduling behavior is proven.

## Decision: Model generated draft sessions separately from source planning inputs

**Rationale**: Course, lecturer, room, Cohort, semester, study type, and study type time windows are source inputs. Draft sessions are generated output and need lifecycle rules, especially replacement on regeneration.

**Alternatives considered**:

- Store generated sessions directly on the course only: rejected because it hides draft lifecycle and makes later manual edits or versions harder to distinguish.
- Avoid storing generated sessions: rejected because the frontend and later planner features need readback.

## Decision: Use one generation endpoint and one readback endpoint

**Rationale**: The first feature needs an explicit admin trigger and a way to display generated output. Keeping the contract to `generate` plus `get current draft` avoids premature CRUD for all planning entities.

**Alternatives considered**:

- Full CRUD for all planning entities in this slice: rejected as broader than the feature.
- Single endpoint returning generated sessions without persistence: rejected because it does not satisfy replacement semantics.

## Decision: Return all detected failure reasons together

**Rationale**: The clarification phase chose all detected failure reasons. This gives admins actionable feedback and supports tests for multiple invalid inputs in one request.

**Alternatives considered**:

- Return first failure only: rejected because it can force repeated correction cycles.
- Return generic failure: rejected because it is not actionable and weakens acceptance criteria.

## Decision: Keep the initial UI minimal

**Rationale**: The spec explicitly excludes calendar polish and manual drag/drop editing. A minimal admin generation panel plus session/error display is enough to validate the end-to-end slice.

**Alternatives considered**:

- Build a full calendar view now: rejected because it pulls in a later slice and increases UI test complexity.
- Backend-only delivery: rejected because the feature says an admin explicitly triggers generation.
