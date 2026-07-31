# Research: Containerized Application Distribution

## Decision 1: Publish one all-in-one image

**Decision**: Package the React build and FastAPI backend in one release image.

**Rationale**: The requested user experience is one pull, one container, one
port, one volume, and one version. The application is intentionally
single-instance while it uses SQLite.

**Alternatives considered**:

- Separate web and API images with Compose: cleaner operational separation but
  more artifacts and coordination than the current distribution goal needs.
- One image with a web proxy and process supervisor: preserves a dedicated
  static server but introduces a second long-lived process and failure
  coordination without a current traffic requirement.

## Decision 2: Use the existing FastAPI process for browser content

**Decision**: Mount compiled frontend files after all API and health routes,
with SPA fallback only for HTML browser requests outside reserved backend path
spaces.

**Rationale**: It provides same-origin frontend/API access and keeps one
long-lived process. Reserving backend path roots prevents unknown API requests
from being converted into successful HTML responses.

**Alternatives considered**:

- Generic root static mount: simpler but masks unknown API routes with
  `index.html`.
- Runtime Vite server: a development server is unsuitable as the production
  static-file runtime.

## Decision 3: Persist the existing SQLite database under `/data`

**Decision**: Set the production database URL to the absolute container path
`/data/planner.db` and mount a named volume at `/data`.

**Rationale**: It preserves the current data model and migrations while
separating institutional data from the replaceable image. The existing backup
script uses SQLite's online backup API and integrity checking.

**Alternatives considered**:

- Database inside the image/container writable layer: loses data on ordinary
  replacement.
- Bundled PostgreSQL: adds a second service and an application dependency before
  multiple instances are required.

## Decision 4: Require a stable production fingerprint key

**Decision**: Require the existing production environment variable through the
deployment manifest and leave it unset in the example environment file.

**Rationale**: Compose fails before startup when the operator has not supplied
the key, and the application independently enforces the minimum key material.
Keeping it stable preserves fingerprint behavior across restarts.

**Alternatives considered**:

- Bake a key into the image: every deployment would share a public secret.
- Generate a new key at every start: fingerprint state would change after
  restarts.
- Add automatic secret-file generation: increases application behavior and
  lifecycle complexity beyond this packaging slice.

## Decision 5: Publish release-driven multi-architecture images to GHCR

**Decision**: Publish from GitHub releases only after backend and frontend
checks, targeting `linux/amd64` and `linux/arm64`, with semantic/revision tags,
SBOM, and provenance.

**Rationale**: Both architectures are supported by the pinned Python solver
runtime. Release-driven publication prevents pullable images from being
confused with unverified pull-request builds and gives administrators exact
rollback targets.

**Alternatives considered**:

- Publish every main-branch commit as `latest`: convenient but makes deployment
  state ambiguous.
- Publish only AMD64: excludes current ARM servers and ARM-based desktops.
- Duplicate publication to Docker Hub: adds credentials and package lifecycle
  without a demonstrated need.

## Decision 6: Run as a fixed non-root user

**Decision**: Run the production process as UID/GID 10001 and pre-create the
data mount point with matching ownership.

**Rationale**: The application needs write access only to persistent data and
does not require operating-system privileges.

**Alternatives considered**:

- Root runtime: operationally easy but grants unnecessary privileges.
- Dynamically remapped UID: useful for some bind-mounted environments but adds
  entrypoint and permissions complexity not required for named volumes.

## Decision 7: Minimize and continuously refresh the runtime

**Decision**: Build Python dependencies with current pip in a temporary stage,
copy an exact production-only dependency set into a digest-pinned Python 3.12
slim Debian Trixie runtime, and remove pip from the final image. Use Dependabot
for weekly base-image digest refreshes and CI gates for size and fixable
critical/high vulnerabilities.

**Rationale**: Test clients and package-management tools do not serve
application requests. Excluding them reduces image size and attack surface,
while automated digest refresh and scanning prevent reproducible pins from
silently becoming stale.

**Alternatives considered**:

- Keep one combined development/runtime lock: simpler file management but
  unnecessarily ships pytest, HTTP test clients, and their dependencies.
- Alpine Linux: smaller base layers but a poor fit for OR-Tools and its
  manylinux/glibc binary dependencies.
- Unpinned base tags: receive newer layers opportunistically but make release
  builds non-reproducible.
