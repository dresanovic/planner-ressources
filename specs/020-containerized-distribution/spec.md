# Feature Specification: Containerized Application Distribution

**Working Branch**: `main`

**Created**: 2026-07-30

**Status**: Implemented

**Input**: User description: "Package the application as one downloadable
container image that can be pulled from GitHub and started easily anywhere."

**Constitution Requirements**: This spec records the agreed behavior, scope,
requirements, acceptance criteria, and independent test paths for the
containerized distribution slice.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start One Downloadable Application (Priority: P1)

As an administrator, I can pull one versioned application artifact and start
the complete planner through one exposed port so that deployment does not
require separately installing or coordinating frontend and backend runtimes.

**Why this priority**: A single downloadable and runnable application is the
primary distribution goal and provides the minimum useful deployment.

**Independent Test**: On a clean supported container host, configure the
required secret, start the image with one data volume and one port, then open
the application, a public lecturer-review route, and the health endpoint.

**Acceptance Scenarios**:

1. **Given** a supported host and a published release, **When** the
   administrator starts the image with the required configuration, **Then** the
   planner user interface and API become available through the same port.
2. **Given** the running application, **When** a browser opens a valid frontend
   route such as the lecturer-review page, **Then** the application shell loads
   without a separate web server.
3. **Given** the running application, **When** a nonexistent API route is
   requested, **Then** it returns a not-found response instead of the frontend
   application shell.

---

### User Story 2 - Preserve and Back Up Planning Data (Priority: P2)

As an administrator, I can keep planning data outside the replaceable
application container and create a verified backup so that restarts and
upgrades do not lose institutional data.

**Why this priority**: A deployable application is not operationally safe
unless its persisted data survives normal container replacement.

**Independent Test**: Start the application with an empty persistent volume,
confirm that its database is created there, create a backup, restart the
container, and verify that the database remains present and unchanged.

**Acceptance Scenarios**:

1. **Given** a new persistent application-data volume, **When** the application
   starts, **Then** its database is created inside that volume.
2. **Given** an initialized application, **When** its container restarts or is
   replaced while reusing the same volume, **Then** the saved database remains
   available.
3. **Given** a running application with persisted data, **When** the
   administrator runs the documented backup operation, **Then** a
   consistency-checked backup is created in persistent storage.
4. **Given** an empty application database, **When** the administrator runs
   the optional baseline seed command, **Then** the catalog is populated
   without creating schedules, sessions, or exams.

---

### User Story 3 - Consume Traceable Release Images (Priority: P3)

As an administrator, I can select an exact application release for common
64-bit Intel/AMD or ARM Linux hosts and trace it to its source revision so that
deployments are repeatable and auditable.

**Why this priority**: Versioned, traceable artifacts make upgrades and
rollbacks predictable after the basic deployment and persistence behavior
exists.

**Independent Test**: Publish a release after all application checks pass,
inspect its available tags, architectures, source metadata, software inventory,
and provenance, then pull the exact release tag.

**Acceptance Scenarios**:

1. **Given** a published semantic release, **When** the publishing workflow
   completes, **Then** the registry contains the exact release tag and
   compatible major/minor convenience tags.
2. **Given** a prerelease, **When** it is published, **Then** it does not replace
   the stable convenience tag.
3. **Given** a published image, **When** its metadata is inspected, **Then** its
   source revision, supported architectures, software inventory, and build
   provenance are available.

### Edge Cases

- Startup must fail clearly when the production fingerprint key is missing,
  empty, or shorter than the established security minimum.
- Unknown API routes must never be masked by browser-route fallback behavior.
- Missing frontend build output must fail image startup rather than expose a
  partially working API-only application.
- Application code and persisted institutional data must remain separate when
  the container is replaced.
- Repeating the optional baseline seed command must update or reuse its known
  records instead of creating duplicates.
- The SQLite deployment must not be scaled beyond one application container.
- A release publication must not proceed when backend tests, frontend tests,
  linting, or the production build fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST be distributed as one versioned container image
  containing the complete browser application and service API.
- **FR-002**: The running image MUST use one long-lived application process and
  expose one configurable host port.
- **FR-003**: Browser routes and API routes MUST share one origin without
  unknown API routes falling back to browser content.
- **FR-004**: The image MUST run without root privileges and provide an
  application health status.
- **FR-005**: The default production database location MUST be inside a
  dedicated persistent data mount.
- **FR-006**: Production startup MUST require a stable fingerprint key with at
  least 32 bytes of key material.
- **FR-007**: Administrators MUST be able to create a consistency-checked
  database backup using the distributed image.
- **FR-008**: A ready-to-use deployment manifest and environment template MUST
  document exact-version deployment, configuration, startup, upgrade, logs,
  backup, and the single-instance limitation.
- **FR-009**: Published stable releases MUST provide exact, major/minor, source
  revision, and stable convenience tags; prereleases MUST NOT replace the
  stable convenience tag.
- **FR-010**: Release images MUST support 64-bit Intel/AMD and ARM Linux hosts.
- **FR-011**: Release publication MUST be blocked until backend and frontend
  verification succeeds.
- **FR-012**: Published images MUST include source metadata, a software
  inventory, and verifiable build provenance.
- **FR-013**: The deployment documentation MUST explain that anonymous pulls
  require public registry visibility and how private deployments authenticate.
- **FR-014**: The final runtime image MUST use a current digest-pinned slim
  base, install an exact production-only dependency lock, and exclude test
  tooling and Python package installers.
- **FR-015**: Automated maintenance MUST check pinned container base images
  weekly and block publication when the image exceeds the agreed size ceiling
  or contains a fixable critical or high vulnerability.
- **FR-016**: The image MUST include the existing baseline seed script and the
  deployment documentation MUST explain how to run it explicitly against the
  persistent production database. Seeding MUST NOT happen automatically during
  ordinary startup.

### Test Requirements *(mandatory)*

- **TR-001**: Tests MUST be created or updated before production code for each
  implemented user story where automated testing is practical.
- **TR-002**: Backend behavior MUST be verified with FastAPI-compatible tests
  using `pytest`.
- **TR-003**: Frontend behavior MUST be verified through React/Vite lint,
  component tests, and a production build.
- **TR-004**: The production image MUST be built and smoke-tested for health,
  frontend routing, API not-found behavior, non-root execution, persistence
  across restart, and backup creation.
- **TR-005**: The final image package inventory MUST match the production lock,
  exclude pip and test clients, and pass the configured image size and
  vulnerability gates.
- **TR-006**: The container smoke test MUST execute the bundled seed command
  and verify that baseline catalog data exists without generated schedules.

### Key Entities

- **Release Image**: An immutable application build identified by a release tag,
  source revision, supported architectures, software inventory, and provenance.
- **Deployment Configuration**: The selected image version, host port,
  institutional time zone, and stable production fingerprint key.
- **Persistent Application Data**: The planner database and verified backups
  retained independently of any one container instance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An administrator with a supported container host can configure,
  pull, and start the application in no more than 10 minutes using at most
  three documented operational commands.
- **SC-002**: The application reports healthy and serves both its main page and
  lecturer-review browser route within 60 seconds of startup on a typical
  supported host.
- **SC-003**: Restarting or replacing the application while reusing its data
  volume results in zero loss of saved database bytes or records.
- **SC-004**: Every stable release is available for both supported processor
  architectures and is traceable to one source revision.
- **SC-005**: 100% of published release images have passed all configured
  backend, frontend, and production-build checks.
- **SC-006**: A deployment operator can produce a consistency-checked backup
  with one documented command.
- **SC-007**: The native release image remains at or below 450 MiB uncompressed
  and has no known fixable critical or high vulnerability at publication time.
- **SC-008**: An administrator can populate an empty persistent database with
  the documented seed command without rebuilding the image.

## Assumptions

- Deployment hosts provide a current OCI-compatible container runtime with
  Compose support for the recommended path.
- The first distributable version is a single-instance deployment using the
  application's existing SQLite persistence model.
- TLS termination, public DNS, user authentication, PostgreSQL migration, and
  multi-instance orchestration are outside this slice.
- Public anonymous pulls are preferred for easiest distribution; operators may
  retain private package visibility when authenticated pulls are acceptable.
- Existing API behavior, scheduling rules, and browser workflows remain
  unchanged.
