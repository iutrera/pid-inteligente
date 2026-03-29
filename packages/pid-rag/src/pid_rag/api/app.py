"""FastAPI application with CORS, lifespan, and route mounting."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pid_knowledge_graph.neo4j_store import Neo4jStore

from pid_rag.config import Settings, get_settings
from pid_rag.api.routes import chat, convert, graph, validate


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: connect/disconnect Neo4j on startup/shutdown."""
    settings: Settings = get_settings()
    app.state.settings = settings

    store = Neo4jStore(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )
    await store.__aenter__()
    app.state.neo4j_store = store

    yield

    await store.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory function that creates and configures the FastAPI application.

    Parameters
    ----------
    settings:
        Optional Settings override (useful for testing).  When *None* the
        default environment-based settings are used.
    """
    app = FastAPI(
        title="P&ID Inteligente API",
        description=(
            "REST API for P&ID conversion (Draw.io <-> DEXPI), "
            "Knowledge Graph construction, validation, and "
            "LLM-powered chat with Graph-RAG."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    resolved_settings = settings or get_settings()

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(convert.router)
    app.include_router(graph.router)
    app.include_router(chat.router)
    app.include_router(validate.router)

    # Health endpoint
    class HealthResponse(BaseModel):
        status: str
        version: str

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", version="0.1.0")

    return app


# Default app instance for ``uvicorn pid_rag.api.app:app``
app = create_app()
