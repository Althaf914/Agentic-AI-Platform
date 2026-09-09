"""
Routers package — all FastAPI route modules.
"""

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

__all__ = [
    "auth",
    "workflows",
    "configurations",
    "campaigns",
    "prospects",
    "approvals",
    "analytics",
    "planner",
    "memory",
    "dashboard",
    "websocket",
]
