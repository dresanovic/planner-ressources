# syntax=docker/dockerfile:1.7

FROM node:26-bookworm-slim@sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341 AS frontend-build

WORKDIR /build/client

COPY client/package.json client/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY client/ ./
RUN npm run build


FROM python:3.14-slim-trixie@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS python-dependencies

WORKDIR /build/backend

COPY backend/requirements-runtime.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --disable-pip-version-check --upgrade "pip==26.2" \
    && python -m pip install \
        --disable-pip-version-check \
        --prefix=/install \
        -r requirements-runtime.txt


FROM python:3.14-slim-trixie@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS runtime

ARG VERSION=""
ARG VCS_REF=""

LABEL org.opencontainers.image.title="Planner Resources" \
      org.opencontainers.image.description="Resource planning application with a React frontend and FastAPI backend" \
      org.opencontainers.image.source="https://github.com/dresanovic/planner-ressources" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}"

ENV APP_ENV=production \
    DATABASE_URL=sqlite:////data/planner.db \
    FRONTEND_DIST_DIR=/app/frontend \
    INSTITUTION_TIMEZONE=Europe/Vienna \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY --from=python-dependencies /install/ /usr/local/
COPY backend/app ./app
COPY backend/scripts/backup_sqlite_db.py ./scripts/backup_sqlite_db.py
COPY backend/scripts/create_seed_data.py ./scripts/create_seed_data.py
COPY backend/scripts/planning_baseline.json ./scripts/planning_baseline.json
COPY backend/scripts/seed_dummy_planning_data.py ./scripts/seed_dummy_planning_data.py
COPY --from=frontend-build /build/client/dist /app/frontend

RUN python -m pip uninstall --yes pip setuptools wheel \
    && ! command -v pip \
    && python -c "import alembic, fastapi, ortools, pydantic, sqlalchemy, uvicorn" \
    && groupadd --system --gid 10001 planner \
    && useradd --system --uid 10001 --gid planner --no-create-home \
        --home-dir /nonexistent --shell /usr/sbin/nologin planner \
    && install -d -o planner -g planner /data

USER planner

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3); raise SystemExit(0 if response.status == 200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
