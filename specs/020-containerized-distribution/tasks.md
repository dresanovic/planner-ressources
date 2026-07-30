# Tasks: Containerized Application Distribution

**Input**: Design documents from
`/specs/020-containerized-distribution/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`

**Tests**: Routing, frontend verification, backend regression, container smoke,
persistence, backup, and release checks are required by the constitution and
feature specification.

**Organization**: Tasks are grouped by independently testable user story.
Completed tasks are checked; remaining pre-merge review corrections stay open.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Record the requested distribution scope and deployment design.

- [x] T001 Create and validate the feature specification in `specs/020-containerized-distribution/spec.md` and `specs/020-containerized-distribution/checklists/requirements.md`
- [x] T002 [P] Record packaging and release decisions in `specs/020-containerized-distribution/research.md`
- [x] T003 [P] Define deployment entities, contract, and validation guide in `specs/020-containerized-distribution/data-model.md`, `specs/020-containerized-distribution/contracts/container-distribution.md`, and `specs/020-containerized-distribution/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish same-origin production frontend serving without changing
the local Vite development workflow.

- [x] T004 Add browser fallback and API not-found regression tests in `backend/tests/test_frontend.py`
- [x] T005 Mount configured production frontend output after API and health routes in `backend/app/frontend.py` and `backend/app/main.py`

**Checkpoint**: The existing backend remains independently runnable in
development, while configured production builds serve the browser application.

---

## Phase 3: User Story 1 - Start One Downloadable Application (Priority: P1) MVP

**Goal**: Pull and run the complete planner as one non-root image with one
process and one exposed port.

**Independent Test**: Build the image, start it with one key and one data
volume, verify health, both browser routes, API 404 behavior, and UID 10001.

### Tests for User Story 1

- [x] T006 [US1] Extend the automated image smoke test with API not-found and non-root assertions in `.github/workflows/ci.yml`

### Implementation for User Story 1

- [x] T007 [US1] Add the multi-stage, non-root, single-process image in `infrastructure/docker/Dockerfile`
- [x] T008 [US1] Add the one-service deployment manifest and required environment template in `compose.yaml` and `.env.example`
- [x] T009 [US1] Document Compose and direct-run startup, logs, and upgrades in `infrastructure/docker/README.md`

**Checkpoint**: User Story 1 is runnable as the independently useful MVP.

---

## Phase 4: User Story 2 - Preserve and Back Up Planning Data (Priority: P2)

**Goal**: Retain SQLite data through restarts and replacements and provide a
verified backup command.

**Independent Test**: Confirm `/data/planner.db` exists, run the backup command,
restart the container, and compare the persisted database state.

### Tests for User Story 2

- [x] T010 [US2] Add persistent-database, restart, and backup assertions to the container smoke test in `.github/workflows/ci.yml`

### Implementation for User Story 2

- [x] T011 [US2] Configure the production database path and named volume in `infrastructure/docker/Dockerfile` and `compose.yaml`
- [x] T012 [US2] Include and document the verified SQLite backup script in `infrastructure/docker/Dockerfile` and `infrastructure/docker/README.md`

**Checkpoint**: User Story 2 is independently validated with a disposable named
volume.

---

## Phase 5: User Story 3 - Consume Traceable Release Images (Priority: P3)

**Goal**: Publish tested, versioned AMD64/ARM64 images with source metadata,
SBOM, and provenance.

**Independent Test**: Publish a release and inspect its tags, platforms,
metadata, SBOM, provenance, and pull visibility.

### Tests for User Story 3

- [x] T013 [US3] Require frontend lint, tests, and build before publication in `.github/workflows/ci.yml` and `.github/workflows/publish-container.yml`
- [x] T014 [US3] Build and smoke-test the ARM64 variant from `infrastructure/docker/Dockerfile`

### Implementation for User Story 3

- [x] T015 [US3] Publish semantic, revision, stable, and multi-architecture GHCR images with SBOM and provenance in `.github/workflows/publish-container.yml`
- [x] T016 [US3] Document GHCR public visibility and private pull authentication in `infrastructure/docker/README.md`

**Checkpoint**: User Story 3 is ready when both target architectures build and
registry visibility instructions are explicit.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T017 Pin production base-image digests in `infrastructure/docker/Dockerfile`
- [x] T018 Run backend pytest, frontend lint/test/build, Compose validation, image build, routing, health, non-root, persistence, restart, and backup verification from `specs/020-containerized-distribution/quickstart.md`
- [x] T019 Move the runtime to the digest-pinned Python 3.12 slim Debian Trixie base in `infrastructure/docker/Dockerfile`
- [x] T020 Split exact runtime and development dependencies in `backend/requirements-runtime.txt`, `backend/requirements-dev.txt`, and `backend/requirements.txt`, and exclude pip and test tooling from the final image
- [x] T021 Add weekly Docker base-image digest maintenance in `.github/dependabot.yml`
- [x] T022 Add scheduled image-size and fixable high/critical vulnerability gates in `.github/workflows/ci.yml`
- [x] T023 Build and smoke-test the native AMD64 image, verify the exact runtime inventory, measure its size, and tag it as `planner-ressources:local`
- [x] T024 Bundle `backend/scripts/seed_dummy_planning_data.py` and document Docker Desktop startup plus optional baseline seeding
- [x] T025 Execute the bundled seed command in the container smoke test and verify catalog data exists without generated schedules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on the agreed specification and blocks
  the runtime stories.
- **User Story 1 (Phase 3)**: Depends on frontend-serving foundation.
- **User Story 2 (Phase 4)**: Depends on the runnable image from User Story 1.
- **User Story 3 (Phase 5)**: Depends on the verified image but not on stored
  planning records.
- **Polish (Phase 6)**: Completes after the selected user stories.

### User Story Dependencies

- **User Story 1 (P1)**: No other user-story dependency; this is the MVP.
- **User Story 2 (P2)**: Uses the User Story 1 image and runtime.
- **User Story 3 (P3)**: Publishes the User Story 1 image and can proceed in
  parallel with User Story 2 verification after the image exists.

### Parallel Opportunities

- T002 and T003 affect separate design artifacts.
- T013 and T014 can run independently of User Story 2 persistence checks.
- T016 documentation and T017 digest pinning affect separate files.

---

## Parallel Example: User Story 3

```text
Task: "Build and smoke-test the ARM64 image from infrastructure/docker/Dockerfile"
Task: "Document GHCR visibility and authentication in infrastructure/docker/README.md"
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete User Story 1.
3. Stop and validate the one-image, one-process experience.
4. Add persistence/backup assurance through User Story 2.
5. Add release publication and traceability through User Story 3.

### Incremental Delivery

1. One local all-in-one image becomes runnable.
2. Persistent data and backup behavior becomes operationally safe.
3. Verified images become pullable from the release registry.

## Format Validation

All tasks use a Markdown checkbox, sequential task ID, story label for
user-story phases, optional parallel marker only where valid, and exact
repository paths.
