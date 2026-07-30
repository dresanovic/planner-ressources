# Quickstart: Validate Containerized Distribution

## Prerequisites

- Docker Desktop or a current Docker Engine with Compose
- A locally built image or a published exact release
- A stable random fingerprint key containing at least 32 bytes

## 1. Run source verification

From `backend/`:

```text
python -m pytest
```

From `client/`:

```text
npm run lint
npm run test
npm run build
```

Expected: all commands exit successfully.

## 2. Validate deployment configuration

Copy `.env.example` to `.env`, set an exact image tag and generated fingerprint
key, then run:

```text
docker compose config --quiet
```

Expected: the configuration is valid. Removing or emptying the fingerprint key
must make validation fail.

## 3. Build the production image

```text
docker build --file infrastructure/docker/Dockerfile --tag planner-ressources:local .
```

Expected: the React build and Python runtime stages complete and the local
image is created.

## 4. Validate the optimized runtime

Inspect the native image and its installed Python distributions.

Expected:

- the image architecture matches the deployment host;
- the uncompressed image size is no greater than 450 MiB;
- installed distributions exactly match
  `backend/requirements-runtime.txt`;
- pip, pytest, httpx, and httpcore are absent;
- the configured CI scanner reports no fixable critical or high
  vulnerability.

The automated container job performs the size, inventory, and vulnerability
checks on every change and in its weekly scheduled run.

## 5. Start and validate the image

Start the local image with one host port, a disposable named volume, and the
generated key.

Validate:

- `GET http://127.0.0.1:8080/health` returns `{"status":"ok"}`;
- `/` returns the compiled application;
- `/lecturer-review/` returns the compiled application;
- `/api/does-not-exist` returns 404 even when HTML is accepted;
- `id -u` inside the container returns `10001`;
- `/data/planner.db` exists and is non-empty;
- the container health state becomes `healthy`.

## 6. Validate optional baseline seeding

Run:

```text
docker exec <container> python scripts/seed_dummy_planning_data.py
```

Expected:

- the command reports the seeded baseline counts;
- seven courses and the documented supporting catalog records exist;
- no draft schedules, teaching sessions, or exams are created;
- running the command again does not duplicate its baseline records.

## 7. Validate backup and restart persistence

Run:

```text
docker exec <container> python scripts/backup_sqlite_db.py --output-dir /data/backups
docker restart <container>
```

Expected:

- the backup command reports the created backup;
- at least one backup exists under `/data/backups`;
- the application becomes healthy again;
- `/data/planner.db` remains present with its previous data.

Remove only the disposable validation container and volume after recording the
results.

## 8. Validate release metadata

For a published release, inspect the registry manifest and attestation.

Expected:

- exact release, major/minor, and revision tags exist;
- `latest` moves only for a stable release;
- AMD64 and ARM64 Linux manifests exist;
- source revision labels, SBOM, and provenance are attached;
- a public package pulls anonymously, or a private package pulls after GHCR
  authentication.
