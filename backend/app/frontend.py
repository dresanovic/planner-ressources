from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


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
