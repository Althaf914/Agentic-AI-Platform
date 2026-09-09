"""
Pydantic schemas for memory endpoints.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ─── Search ───────────────────────────────────────────────────────────────────


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 5


class MemorySearchResult(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    summary: str
    last_seen: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None
    distance: Optional[float] = None
    created_at: Optional[datetime] = None


class MemorySearchResponse(BaseModel):
    results: list[MemorySearchResult]
    query: str
    total: int


# ─── Standard entry ───────────────────────────────────────────────────────────


class MemoryEntry(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    summary: str
    last_seen: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Duplicate check ���────────────────────────────────────────────────────────


class DuplicateCheckResponse(BaseModel):
    exists: bool
    last_seen: Optional[datetime] = None
    campaign: Optional[str] = None
    was_approved: bool = False
    memory_id: Optional[str] = None
    summary: Optional[str] = None


# ─── Status update ────────────────────────────────────────────────────────────


class MemoryStatusUpdate(BaseModel):
    status: str  # "outreach_sent" | "replied" | "in_pipeline" | "closed"


OUTREACH_STATUSES = ["outreach_sent", "replied", "in_pipeline", "closed"]
