
"""

FastAPI application factory for AI Command Center.

"""

from __future__ import annotations

from collections.abc import AsyncIterator

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from ai.factory import AIProviderFactory

from ai.planner import AIPlanner

from api.errors import register_exception_handlers

from api.routers import (
    agents,
    approvals,
    auth,
    conversations,
    executions,
    orchestrations,
    tasks,
)

from config.environment import bootstrap_environment

from config.settings import settings

from core.execution_system_factory import ExecutionSystemFactory

from database.initializer import initialize_database

from services.ai_execution_service import AIExecutionService

@asynccontextmanager

async def _lifespan(app: FastAPI) -> AsyncIterator[None]:

    # Refuses to start outside development with unsafe defaults

    # (e.g. the well-known default JWT secret) still in place.

    bootstrap_environment(settings)

    initialize_database()

    provider_result = AIProviderFactory.create(settings)

    if provider_result.is_failure():

        raise RuntimeError(

            f"{provider_result.error.code}: "

            f"{provider_result.error.message}"

        )

    provider = provider_result.require_data()

    execution_system = (

        ExecutionSystemFactory.create_with_provider(

            provider

        )

    )

    app.state.ai_execution_service = AIExecutionService(

        AIPlanner(provider),

        execution_system,

    )

    try:

        yield

    finally:

        execution_system.close()

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

    app.include_router(agents.router)
    app.include_router(executions.router)
    app.include_router(orchestrations.router)

    @app.get("/health", tags=["health"])

    def health() -> dict:

        return {"status": "ok"}

    return app

app = create_app()

