# Container Distribution Contract

## Published artifact

The release workflow publishes:

```text
ghcr.io/dresanovic/planner-ressources:<release-tag>
```

Each stable semantic release also publishes compatible major/minor and
`latest` tags. Prereleases never move `latest`. A source-revision tag is
published for traceability.

The image manifest covers:

- `linux/amd64`
- `linux/arm64`

The artifact exposes OCI source, version, and revision metadata plus an SBOM
and registry-backed provenance attestation.

## Runtime contract

The image:

- starts one Uvicorn process;
- listens on container port `8080`;
- reports health through `GET /health`;
- serves existing `/api/*` endpoints;
- serves compiled browser content from `/`;
- supports `/lecturer-review/` as a browser route;
- returns 404 for an unknown `/api/*` path;
- runs as UID/GID `10001`;
- writes the production SQLite database to `/data/planner.db`;
- contains `scripts/backup_sqlite_db.py`.

## Configuration contract

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `APP_ENV` | Image supplied | `production` | Enables production safety checks |
| `DATABASE_URL` | Image supplied | `sqlite:////data/planner.db` | Persistent database location |
| `FRONTEND_DIST_DIR` | Image supplied | `/app/frontend` | Compiled frontend location |
| `INSTITUTION_TIMEZONE` | No | `Europe/Vienna` | Institutional date/time rules |
| `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` | Yes | None | Stable key with at least 32 bytes of key material |

## Persistence contract

The deployment mounts a persistent volume at `/data`. Container restart or
replacement must reuse that volume. Removing the container must not remove the
volume.

Only one SQLite-backed application container may use the data volume.

## Registry visibility contract

Anonymous pull-and-run deployment requires the GHCR package to be public.
Private packages require the operator to authenticate to `ghcr.io` with
package-read permission before pulling.
