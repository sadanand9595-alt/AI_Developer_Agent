"""
FastAPI application factory for AI Command Center.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_exception_handlers
from api.routers import approvals, auth, conversations, tasks
from config.environment import bootstrap_environment
from config.settings import settings
from database.initializer import initialize_database


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Refuses to start outside development with unsafe defaults
    # (e.g. the well-known default JWT secret) still in place.
    bootstrap_environment(settings)
    initialize_database()
    yield


def create_app() -> FastAPI:
    """Build and return a configured FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=_lifespan,
    )

    register_exception_handlers(app)

    # CORS is only opened for the local Vite dev server, and only
    # outside production. It is never wildcarded, and never enabled
    # in production, so this does not weaken the deployed API's
    # security boundary.
    if settings.app_env.strip().lower() != "production":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(conversations.router)
    app.include_router(approvals.router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
