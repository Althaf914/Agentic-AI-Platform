"""
AgentForge AI — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.database.init_db import init_database

# Import routers
from backend.routers import (
    auth,
    workflows,
    configurations,
    campaigns,
    prospects,
    approvals,
    analytics,
    planner,
    memory,
    dashboard,
    websocket,
)
from backend.routers import platform
from backend.routers.debug import router as debug_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize database and seed data
    init_database()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="AgentForge AI",
    description="Agentic AI Platform for B2B Customer Discovery",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(configurations.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(prospects.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(planner.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(platform.router, prefix="/api/v1")

# WebSocket router — mounted at root (not under /api/v1)
app.include_router(websocket.router)

# Debug router — temporary, DELETE after debugging
app.include_router(debug_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AgentForge AI"}
