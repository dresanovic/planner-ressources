# Implementation Plan: Containerized Application Distribution

**Working Branch**: `main` | **Date**: 2026-07-30 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from
`/specs/I-001-containerized-distribution/spec.md`

## Summary

Distribute the complete planner as one OCI image that starts one Uvicorn
process, serves the compiled React application and existing FastAPI routes from
one origin, persists SQLite under `/data`, and is published to GHCR after
verification. Provide a Compose deployment manifest, required production
configuration, backup guidance, multi-architecture release tags, SBOM, and
provenance.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 6; Node.js 24 for the build stage

**Primary Dependencies**: FastAPI 0.139, Starlette 1.3, Uvicorn 0.49, React
19, Vite 8, Docker BuildKit/Buildx, GitHub Actions; production Python
dependencies are maintained in a separate exact lock

**Storage**: Existing SQLite database persisted at `/data/planner.db`; verified
SQLite backups retained under `/data/backups`

**Testing**: `pytest`; ESLint; Vitest; TypeScript/Vite production build; Docker
image build and runtime smoke checks

**Target Platform**: Linux containers on `linux/amd64` and `linux/arm64`;
browser access through one exposed HTTP port

**Project Type**: Existing React/FastAPI web application with new packaging and
release automation

**Performance Goals**: Healthy and browser-accessible within 60 seconds on a
typical supported host; static assets served without a second runtime service;
native image no larger than 450 MiB uncompressed

**Constraints**: One image, one long-lived process, one exposed port, non-root
runtime, Python 3.12 slim Debian Trixie base, no test or package-management
tooling in the final image, no new application runtime dependency, exact
release deploys, one application instance while SQLite remains in use

**Scale/Scope**: Small single-instance institutional deployment; orchestration,
PostgreSQL, authentication, TLS termination, and API behavior changes are out
of scope

## Constitution Check

*GATE: Re-evaluated after design and before commit.*

- **Spec-first**: Process-order exception recorded. The initial implementation
  preceded this artifact, but the change remains uncommitted; the recovered
  spec now captures the agreed scope and was reviewed against the actual diff
  before merge readiness was assessed.
- **Acceptance criteria**: PASS. Three independently testable user stories use
  Given/When/Then acceptance scenarios.
- **Test-first**: Process-order exception recorded. New routing tests were
  delivered with the production behavior, and the complete backend, frontend,
  build, and image smoke verification was executed before commit.
- **Simplicity and KISS**: PASS. One existing application process serves both
  application surfaces; no proxy, process supervisor, database service, or new
  runtime library is introduced.
- **Technology fit**: PASS. Existing FastAPI and React/Vite boundaries are
  retained; the distribution contract is documented in
  `contracts/container-distribution.md`.
- **Delivery workflow**: PASS with documented solo-change path on `main`; the
  working tree was clean before the requested implementation.
- **Verification before commit**: PASS. Concrete commands and end-to-end checks
  are listed below and have been executed.

The process-order exceptions cannot be made retroactively test-first or
spec-first. They are accepted for this uncommitted change because scope is now
explicit, no requirement ambiguity remains, comprehensive verification passes,
and the exception is visible rather than concealed.

## Simplicity Check *(mandatory before implementation)*

1. **Simplest viable solution**: Build the existing React client in a temporary
   stage, copy its static output beside the existing FastAPI application, and
   let the single Uvicorn/FastAPI process serve both known API routes and
   browser content. Persist the unchanged SQLite database through one volume.
2. **Necessary abstractions**: One small static-files adapter is necessary to
   provide browser-route fallback while preserving true not-found responses
   for unknown API paths. One deployment manifest and one release workflow are
   necessary to make pulling and starting the artifact repeatable.
3. **Deliberately excluded**: Nginx/Caddy, Supervisor/s6, separate web and API
   images, PostgreSQL, multiple workers or replicas, Kubernetes, runtime
   frontend configuration injection, authentication, bundled TLS, and
   automatic database seeding.

## Project Structure

### Documentation (this feature)

```text
specs/I-001-containerized-distribution/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- container-distribution.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- app/
|   |-- frontend.py
|   `-- main.py
|-- requirements-dev.txt
|-- requirements-runtime.txt
`-- tests/
    `-- test_frontend.py

backend/scripts/
|-- backup_sqlite_db.py
`-- seed_dummy_planning_data.py

client/
|-- package.json
|-- package-lock.json
`-- src/

infrastructure/docker/
|-- Dockerfile
`-- README.md

.github/workflows/
|-- ci.yml
|-- dependabot.yml
`-- publish-container.yml

compose.yaml
.env.example
.dockerignore
```

**Structure Decision**: Retain the established `backend/` and `client/`
applications and add packaging under the existing `infrastructure/docker/`
placeholder. The conventional root Compose and environment-example files keep
deployment discoverable.

## Complexity Tracking

No unjustified layer, dependency, design pattern, or abstraction is introduced.
The static-files adapter solves the demonstrated collision between browser
fallback and unknown API routes.

## Verification Plan

The following checks must pass before commit:

```text
cd backend
python -m pytest

cd client
npm run lint
npm run test
npm run build

docker compose config --quiet
docker build --file infrastructure/docker/Dockerfile --tag planner-ressources:local .
```

The built image must also prove:

- `/health` returns healthy state;
- `/` and `/lecturer-review/` serve browser content;
- an unknown `/api/*` route returns 404;
- the runtime user is non-root;
- `/data/planner.db` exists and survives restart;
- the backup command creates a consistency-checked backup;
- the optional seed command creates baseline catalog data without schedules;
- the Docker health state becomes `healthy`.
- the installed distribution inventory matches `requirements-runtime.txt`;
- pip, pytest, and HTTP test clients are absent;
- the image is no larger than 450 MiB uncompressed;
- the configured scanner reports no fixable critical or high vulnerability.

Release automation must build both `linux/amd64` and `linux/arm64` variants,
publish semantic and revision tags, avoid moving `latest` for prereleases, and
attach an SBOM and provenance attestation. Dependabot must check the pinned
base-image digests weekly, and CI must rebuild and scan the image weekly.

## Post-Design Constitution Check

PASS with the two transparent process-order exceptions described above. The
design remains limited to the requested distribution slice and the test plan
covers each acceptance boundary. The Spec Kit installation has no
`update-agent-context` script, so no agent-context update was available or
required.
