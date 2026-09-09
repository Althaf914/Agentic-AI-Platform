"""
WebSocket event system — structured event types for granular per-step progress tracking.

14 event types covering the full workflow lifecycle, from agent-level status
down to individual sub-steps and per-company discoveries.

All event builders return a dict ready for broadcast via ConnectionManager.
"""
import json
import time
from datetime import datetime, timezone

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ── Event type constants ─────────────────────────────────────────────────
EVENT_WORKFLOW_STARTED = "workflow_started"
EVENT_WORKFLOW_COMPLETED = "workflow_completed"
EVENT_WORKFLOW_FAILED = "workflow_failed"
EVENT_AGENT_STARTED = "agent_started"
EVENT_AGENT_COMPLETED = "agent_completed"
EVENT_AGENT_FAILED = "agent_failed"
EVENT_AGENT_SUBSTEP = "agent_substep"
EVENT_COMPANY_DISCOVERED = "company_discovered"
EVENT_COMPANY_VALIDATED = "company_validated"
EVENT_COMPANY_REJECTED = "company_rejected"
EVENT_TECH_DETECTED = "tech_detected"
EVENT_CONTACT_FOUND = "contact_found"
EVENT_QUALIFICATION_SCORED = "qualification_scored"
EVENT_RECOMMENDATION_CREATED = "recommendation_created"


# ── Event builders ───────────────────────────────────────────────────────

def build_workflow_started(
    workflow_id: str,
    campaign_name: str = "",
    total_agents: int = 0,
    estimated_time_minutes: int = 0,
) -> dict:
    """Fired when workflow begins executing."""
    return {
        "event_type": EVENT_WORKFLOW_STARTED,
        "workflow_id": workflow_id,
        "data": {
            "campaign_name": campaign_name,
            "total_agents": total_agents,
            "estimated_time_minutes": estimated_time_minutes,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_agent_started(
    workflow_id: str,
    agent_name: str,
    agent_index: int = 0,
    total_agents: int = 0,
) -> dict:
    """Fired when an individual agent begins execution."""
    return {
        "event_type": EVENT_AGENT_STARTED,
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "data": {
            "agent_index": agent_index,
            "total_agents": total_agents,
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_agent_substep(
    workflow_id: str,
    agent_name: str,
    substep_name: str,
    substep_detail: str = "",
    progress_pct: int | None = None,
) -> dict:
    """Fired for each logical sub-operation within an agent.

    Examples:
      - {agent_name: "validation", substep_name: "linkedin_check",
         substep_detail: "Checking LinkedIn for Acme Inc...", progress_pct: 45}
      - {agent_name: "tech_analysis", substep_name: "builtwith_lookup",
         substep_detail: "Detected React, AWS, Kubernetes at Acme.com"}
    """
    return {
        "event_type": EVENT_AGENT_SUBSTEP,
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "data": {
            "substep_name": substep_name,
            "substep_detail": substep_detail,
            "progress_pct": progress_pct,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_agent_completed(
    workflow_id: str,
    agent_name: str,
    duration_seconds: float = 0.0,
    output_summary: str = "",
    company_count: int = 0,
) -> dict:
    """Fired when an agent finishes (success or skip)."""
    return {
        "event_type": EVENT_AGENT_COMPLETED,
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "data": {
            "agent_name": agent_name,
            "duration_seconds": round(duration_seconds, 1),
            "output_summary": output_summary,
            "company_count": company_count,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_agent_failed(
    workflow_id: str,
    agent_name: str,
    error: str = "",
    retry_available: bool = False,
) -> dict:
    """Fired when an agent encounters a non-recoverable error."""
    return {
        "event_type": EVENT_AGENT_FAILED,
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "data": {
            "agent_name": agent_name,
            "error": error[:500],
            "retry_available": retry_available,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_company_discovered(
    workflow_id: str,
    company_name: str,
    domain: str = "",
    source_query: str = "",
) -> dict:
    """Fired for each company found during discovery."""
    return {
        "event_type": EVENT_COMPANY_DISCOVERED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "domain": domain,
            "source_query": source_query,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_company_validated(
    workflow_id: str,
    company_name: str,
    domain: str = "",
    passed: bool = True,
    checks_passed: int = 0,
    checks_total: int = 0,
) -> dict:
    """Fired for each company that passes validation."""
    return {
        "event_type": EVENT_COMPANY_VALIDATED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "domain": domain,
            "passed": passed,
            "checks_passed": checks_passed,
            "checks_total": checks_total,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_company_rejected(
    workflow_id: str,
    company_name: str,
    domain: str = "",
    reason: str = "",
) -> dict:
    """Fired for each company rejected during validation."""
    return {
        "event_type": EVENT_COMPANY_REJECTED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "domain": domain,
            "reason": reason[:300],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_tech_detected(
    workflow_id: str,
    company_name: str,
    tech_stack: list[str] | None = None,
    match_score: float = 0.0,
) -> dict:
    """Fired when tech analysis completes for a company."""
    return {
        "event_type": EVENT_TECH_DETECTED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "tech_stack": tech_stack or [],
            "match_score": round(match_score, 2),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_contact_found(
    workflow_id: str,
    company_name: str,
    contact_name: str = "",
    role: str = "",
    source: str = "",
    has_email: bool = False,
    has_linkedin: bool = False,
) -> dict:
    """Fired when a decision-maker contact is identified for a company."""
    return {
        "event_type": EVENT_CONTACT_FOUND,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "contact_name": contact_name,
            "role": role,
            "source": source,
            "has_email": has_email,
            "has_linkedin": has_linkedin,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_qualification_scored(
    workflow_id: str,
    company_name: str,
    score: float = 0.0,
    tier: str = "",
    strongest_signal: str = "",
) -> dict:
    """Fired when a company receives its qualification score."""
    return {
        "event_type": EVENT_QUALIFICATION_SCORED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "score": score,
            "tier": tier,
            "strongest_signal": strongest_signal[:100],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_recommendation_created(
    workflow_id: str,
    company_name: str,
    priority: str = "",
    market_trigger: str = "",
) -> dict:
    """Fired when an outreach recommendation package is generated."""
    return {
        "event_type": EVENT_RECOMMENDATION_CREATED,
        "workflow_id": workflow_id,
        "data": {
            "company_name": company_name,
            "priority": priority,
            "market_trigger": market_trigger[:150],
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_workflow_completed(
    workflow_id: str,
    duration_seconds: float = 0.0,
    stats: dict | None = None,
) -> dict:
    """Fired when the workflow finishes successfully."""
    return {
        "event_type": EVENT_WORKFLOW_COMPLETED,
        "workflow_id": workflow_id,
        "data": {
            "duration_seconds": round(duration_seconds, 1),
            "stats": stats or {},
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_workflow_failed(
    workflow_id: str,
    failed_agent: str = "",
    error: str = "",
    recoverable: bool = False,
) -> dict:
    """Fired when the workflow encounters a fatal error."""
    return {
        "event_type": EVENT_WORKFLOW_FAILED,
        "workflow_id": workflow_id,
        "data": {
            "failed_agent": failed_agent,
            "error": error[:500],
            "recoverable": recoverable,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── High-level emit function ─────────────────────────────────────────────

async def emit(
    workflow_id: str,
    agent_name: str,
    event_type: str,
    data: dict | None = None,
    manager=None,
):
    """
    Low-level emit: broadcast a pre-built event dict via WebSocket.

    This is the general-purpose emitter. For structured events prefer using
    the specialized _emit_* functions on BaseAgent, which call into this.

    Args:
        workflow_id: Target workflow ID.
        agent_name: Name of the agent emitting (empty for workflow-level).
        event_type: Event type string (one of the EVENT_* constants).
        data: Payload dict.
        manager: ConnectionManager instance. If None, imports from routers.
    """
    if manager is None:
        try:
            from backend.routers.websocket import manager as ws_manager
            manager = ws_manager
        except ImportError:
            logger.warning("WebSocket manager not available, skipping emit")
            return

    message = {
        "event_type": event_type,
        "workflow_id": workflow_id,
        "agent_name": agent_name,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await manager.broadcast(workflow_id, message)
        logger.debug(f"Emitted: {event_type}/{agent_name} for workflow {workflow_id}")
    except Exception as e:
        logger.warning(f"Failed to broadcast event: {e}")
