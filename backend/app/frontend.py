from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


PUBLIC_UNAUTHENTICATED_BROWSER_PATHS = frozenset(
    {
        "/login/",
        "/bootstrap/",
        "/account-access/",
        "/administrator-recovery/",
        "/lecturer-review/",
    }
)


def is_public_unauthenticated_browser_path(path: str) -> bool:
    """Recognize only the deliberately public application entry points."""

    return path in PUBLIC_UNAUTHENTICATED_BROWSER_PATHS or path.startswith("/assets/")


def development_cors_origins(*, production: bool | None = None) -> list[str]:
    """Permit credentialed cross-origin requests only for local development."""

    if production is None:
        production = os.getenv("APP_ENV", "").casefold() == "production"
    if production:
        return []
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


class SPAStaticFiles(StaticFiles):
    """Serve frontend assets and fall back to index.html for browser routes."""

    _BACKEND_PATHS = {"api", "docs", "health", "openapi.json", "redoc"}

    async def get_response(self, path: str, scope: Scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or not self._uses_spa_fallback(path, scope):
                raise
            return await super().get_response("index.html", scope)

    @classmethod
    def _uses_spa_fallback(cls, path: str, scope: Scope) -> bool:
        normalized_path = str(scope.get("path", path)).strip("/")
        root_segment = normalized_path.partition("/")[0]
        accepts_html = "text/html" in Headers(scope=scope).get("accept", "")
        return root_segment not in cls._BACKEND_PATHS and accepts_html


def mount_frontend(app: FastAPI) -> None:
    """Mount the production frontend when a build directory is configured."""

    configured_directory = os.getenv("FRONTEND_DIST_DIR")
    if not configured_directory:
        return

    frontend_directory = Path(configured_directory).resolve()
    app.mount(
        "/",
        SPAStaticFiles(directory=frontend_directory, html=True),
        name="frontend",
    )
