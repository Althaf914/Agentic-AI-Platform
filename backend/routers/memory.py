"""
Memory router — semantic search (GET), duplicate check, status tracking,
and timeline retrieval. Extended for cross-campaign dedup and manual status updates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.memory import Memory
from backend.schemas.memory import (
    MemorySearchRequest,
    MemoryEntry,
    MemorySearchResponse,
    MemorySearchResult,
    DuplicateCheckResponse,
    MemoryStatusUpdate,
    OUTREACH_STATUSES,
)
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/memory", tags=["Memory"])


# ─── POST /memory/search — semantic search (body POST) ────────────────────────


@router.post("/search", response_model=list[MemoryEntry])
def search_memory_post(
    request: MemorySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search memory using semantic similarity via ChromaDB (POST version)."""
    try:
        from backend.memory.shared_memory import search_memory as do_search
        results = do_search(query=request.query, top_k=request.top_k, db=db)
        return results
    except Exception:
        results = (
            db.query(Memory)
            .filter(Memory.summary.ilike(f"%{request.query}%"))
            .limit(request.top_k)
            .all()
        )
        return results


# ─── GET /memory/search — semantic search (query params) ──────────────────────


@router.get("/search", response_model=MemorySearchResponse)
def search_memory_get(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    campaign_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search memory using semantic similarity via ChromaDB.
    Returns results with distance scores and full metadata.
    """
    try:
        from backend.memory.shared_memory import search_memory as do_search
        raw = do_search(query=q, top_k=limit, db=db)
    except Exception:
        raw = []

    results = []
    for r in raw:
        meta = r.get("metadata") or {}
        # Filter by campaign_id if specified
        if campaign_id and meta.get("campaign_id") != campaign_id:
            continue
        results.append(MemorySearchResult(
            id=r.get("id", ""),
            entity_type=r.get("entity_type", ""),
            entity_id=r.get("entity_id", ""),
            summary=r.get("summary", ""),
            last_seen=r.get("last_seen"),
            metadata=meta,
            distance=r.get("distance"),
            created_at=r.get("created_at"),
        ))

    return MemorySearchResponse(
        results=results,
        query=q,
        total=len(results),
    )


# ─── GET /memory — list all memory entries (for timeline) ────────────────────


@router.get("", response_model=list[MemoryEntry])
def list_memory(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all memory entries, newest first (for timeline view)."""
    entries = (
        db.query(Memory)
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .all()
    )
    return entries


# ─── GET /memory/check-duplicate — fast domain check ──────────────────────────


@router.get("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate(
    domain: str = Query(..., min_length=1, description="Company domain to check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fast check: is this domain already in memory?
    Used by frontend to show dedup warnings, and by agents for skip logic.
    """
    from sqlalchemy import Text, cast

    # Search memory entries of type 'company' whose metadata_json contains this domain
    memory_rows = (
        db.query(Memory)
        .filter(
            Memory.entity_type == "company",
            Memory.summary.ilike(f"%{domain}%"),
        )
        .order_by(Memory.created_at.desc())
        .all()
    )

    # Also check metadata_json['domain'] directly
    for row in memory_rows:
        meta = row.metadata_json or {}
        stored_domain = meta.get("domain", "")
        if domain.lower() == stored_domain.lower() or domain.lower() in row.summary.lower():
            campaign = meta.get("campaign", meta.get("campaign_name", ""))
            was_approved = meta.get("was_approved", meta.get("priority") == "high")
            return DuplicateCheckResponse(
                exists=True,
                last_seen=row.last_seen or row.created_at,
                campaign=campaign or "Unknown campaign",
                was_approved=bool(was_approved),
                memory_id=row.id,
                summary=row.summary,
            )

    # No match
    return DuplicateCheckResponse(exists=False, was_approved=False)


# ─── PUT /memory/{id}/status — update outreach status ────────────────────────


@router.put("/{memory_id}/status")
def update_memory_status(
    memory_id: str,
    request: MemoryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update memory entry's outreach status for manual tracking."""
    if request.status not in OUTREACH_STATUSES:
        raise ValidationError(
            detail=f"Invalid status. Must be one of: {', '.join(OUTREACH_STATUSES)}"
        )

    entry = db.query(Memory).filter(Memory.id == memory_id).first()
    if not entry:
        raise NotFoundError(detail=f"Memory entry {memory_id} not found")

    meta = dict(entry.metadata_json or {})
    meta["outreach_status"] = request.status
    entry.metadata_json = meta
    db.commit()

    return {
        "message": f"Status updated to '{request.status}'",
        "memory_id": memory_id,
        "status": request.status,
    }


# ─── GET /memory/timeline/{entity_id} — chronological entries ─────────��───────


@router.get("/timeline/{entity_id}", response_model=list[MemoryEntry])
def get_timeline(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get ordered memory entries for a specific entity (company/contact/workflow)."""
    entries = (
        db.query(Memory)
        .filter(Memory.entity_id == entity_id)
        .order_by(Memory.created_at.desc())
        .all()
    )
    return entries
