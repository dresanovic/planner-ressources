# Container deployment

The production package is one image and one long-running Uvicorn process.
FastAPI serves both the API and the compiled React application. SQLite data is
stored in the `/data` volume.

The release workflow publishes one multi-platform tag containing native
`linux/amd64` and `linux/arm64` variants. Docker selects the matching variant
when the image is pulled. Architecture-specific local images are intended only
for compatibility testing and should not be deployed on a host with a different
CPU architecture.

## Registry visibility

After the first GitHub release publishes the package, set the
`planner-ressources` package visibility to **Public** in its GitHub package
settings if deployments should pull anonymously. Public repository visibility
does not by itself make a newly published GHCR package public.

If the package remains private, authenticate each deployment host before
pulling. Use a classic GitHub personal access token with `read:packages`:

```text
echo TOKEN | docker login ghcr.io -u GITHUB_USERNAME --password-stdin
```

Do not put the registry token in `compose.yaml` or `.env`.

## Deploy with Docker Compose

1. Copy `compose.yaml` and `.env.example` to the deployment host.
2. Rename `.env.example` to `.env`.
3. Set `PLANNER_IMAGE` to the exact published release tag.
4. Generate and set `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY`. Keep this key
   stable across restarts and upgrades.
5. Start the application:

   ```text
   docker compose pull
   docker compose up -d
   ```

6. Open `http://localhost:8080`, or the host and port configured for the
   deployment.

Inspect status and logs with:

```text
docker compose ps
docker compose logs -f planner
```

Upgrade by changing `PLANNER_IMAGE` to a newer exact release and running:

```text
docker compose pull
docker compose up -d
```

Do not use more than one application container while SQLite is the database.

## Run from Docker Desktop

When starting `planner-ressources:local` from Docker Desktop, expand
**Optional settings** and configure:

| Setting | Value |
|---------|-------|
| Container name | `planner-ressources` |
| Host port | `8080` |
| Host path | A dedicated local folder, for example `C:\DockerData\planner-ressources` |
| Container path | `/data` |
| Environment variable | `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` |
| Environment value | A generated 64-character hexadecimal key |

Create the host folder before starting the container. Keep it outside folders
synchronized by OneDrive or similar services. The `/data` mapping preserves
the SQLite database when the container is replaced.

Generate the required key in PowerShell:

```powershell
$key = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($key)
$rng.Dispose()
[BitConverter]::ToString($key).Replace('-', '').ToLowerInvariant()
```

Keep the resulting value private and unchanged across upgrades. No other
environment variable is required for the default Europe/Vienna deployment.

After selecting **Run**, open <http://localhost:8080>. If port `8080` is
already occupied, use host port `8081` and open
<http://localhost:8081>.

## Optionally populate the baseline catalog

The image includes an idempotent baseline seed script. It creates lecturers,
rooms, cohorts, a semester, study types and time windows, courses, resource
eligibility, and holidays. It does not create schedules, teaching sessions,
exams, or generation constraints.

Run it explicitly after the container is healthy:

```powershell
docker exec planner-ressources python scripts/seed_dummy_planning_data.py
```

The command uses the configured `/data/planner.db` database. It can be rerun:
known baseline records are updated or reused rather than duplicated. Because
the script contains demonstration catalog values, review those values before
using it for a real institution. Seeding is never performed automatically
during normal container startup.

## Image maintenance and security

The final runtime image is based on the digest-pinned Python 3.12 Debian Trixie
image and contains only the dependencies from
`backend/requirements-runtime.txt`. Test tooling and the Python package
installer are not included in the final image.

Dependabot checks the pinned Docker base-image digests weekly. CI also rebuilds
the image weekly and fails when the image exceeds 450 MiB uncompressed or
contains a fixable critical or high vulnerability. Review and merge successful
base-image update pull requests promptly; pinning provides reproducibility but
does not apply security updates by itself.

## Back up SQLite

The image contains the repository's transaction-safe SQLite backup script.
Create a verified backup inside the persistent volume with:

```text
docker compose exec planner python scripts/backup_sqlite_db.py --output-dir /data/backups
```

Copy backups off the Docker host or volume on a regular schedule, and test the
restore procedure before relying on them.

## Run without Compose

After generating a stable fingerprint key, the equivalent direct command is:

```text
docker run -d --name planner-ressources -p 8080:8080 -v planner-ressources-data:/data --restart unless-stopped -e LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY=replace-with-generated-value ghcr.io/dresanovic/planner-ressources:v1.0.0
```

The image defaults to production mode and
`DATABASE_URL=sqlite:////data/planner.db`.

GitHub's current GHCR authentication and visibility guidance is available at
<https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>.
