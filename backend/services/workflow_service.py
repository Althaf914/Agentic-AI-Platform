"""
Workflow service — business logic for starting, monitoring, and retrying workflows.
"""

import uuid
import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.workflow import Workflow
from backend.models.agent_log import AgentLog
from backend.models.configuration import Configuration
from backend.utils.exceptions import NotFoundError, ValidationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def start_workflow(config_id: str, user_id: str, db: Session) -> Workflow:
    """Create a Workflow row and schedule execution on the event loop."""
    # Check for already-running workflow with same config
    existing_running = db.query(Workflow).filter(
        Workflow.configuration_id == config_id,
        Workflow.status == "running",
    ).first()

    if existing_running:
        return existing_running

    # Validate configuration exists
    config = db.query(Configuration).filter(Configuration.id == config_id).first()
    if not config:
        raise NotFoundError(detail=f"Configuration {config_id} not found")

    # Create new workflow
    workflow = Workflow(
        id=str(uuid.uuid4()),
        user_id=user_id,
        configuration_id=config_id,
        status="pending",
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Schedule on the running event loop (non-blocking)
    asyncio.ensure_future(_run_workflow_async(workflow.id))
    logger.info(f"Scheduled workflow {workflow.id} on event loop")

    return workflow


async def _run_workflow_async(workflow_id: str):
    """Run workflow engine on the current event loop (with WebSocket access)."""
    from backend.database.session import SessionLocal
    from backend.workflow_engine.engine import WorkflowEngine
    from backend.routers.websocket import manager

    print(f"[WORKFLOW] Starting async execution: {workflow_id}")
    db = SessionLocal()
    try:
        engine = WorkflowEngine(db, manager)
        await engine.run(workflow_id)
        print(f"[WORKFLOW] Completed: {workflow_id}")
    except Exception as e:
        print(f"[WORKFLOW] Failed: {workflow_id} — {e}")
        import traceback
        traceback.print_exc()
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf:
            wf.status = "failed"
            db.commit()
    finally:
        db.close()


def _run_in_thread(workflow_id: str):
    """Fallback: run in a new thread with its own event loop."""
    from backend.database.session import SessionLocal
    from backend.workflow_engine.engine import WorkflowEngine

    db = SessionLocal()
    try:
        engine = WorkflowEngine(db, None)
        asyncio.run(engine.run(workflow_id))
    except Exception as e:
        logger.error(f"Thread workflow failed: {e}")
    finally:
        db.close()


def get_workflow_status(workflow_id: str, db: Session) -> dict:
    """Return workflow status along with its agent logs."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise NotFoundError(detail=f"Workflow {workflow_id} not found")

    agent_logs = (
        db.query(AgentLog)
        .filter(AgentLog.workflow_id == workflow_id)
        .order_by(AgentLog.started_at)
        .all()
    )

    return {
        "id": workflow.id,
        "status": workflow.status,
        "configuration_id": workflow.configuration_id,
        "started_at": workflow.started_at,
        "completed_at": workflow.completed_at,
        "agent_logs": agent_logs,
        "campaign_name": workflow.campaign.name if workflow.campaign else "Untitled",
    }


def retry_agent(workflow_id: str, agent_name: str, db: Session) -> AgentLog:
    """Reset a failed agent_log entry and re-dispatch it."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise NotFoundError(detail=f"Workflow {workflow_id} not found")

    agent_log = (
        db.query(AgentLog)
        .filter(AgentLog.workflow_id == workflow_id, AgentLog.agent_name == agent_name)
        .first()
    )
    if not agent_log:
        raise NotFoundError(detail=f"Agent log for '{agent_name}' not found")

    agent_log.status = "idle"
    agent_log.error_message = None
    agent_log.output_json = None
    agent_log.started_at = None
    agent_log.completed_at = None
    workflow.status = "running"
    workflow.completed_at = None
    db.commit()
    db.refresh(agent_log)
    return agent_log


def get_user_workflows(user_id: str, db: Session) -> list[Workflow]:
    """Return all workflows for a given user, newest first."""
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == user_id)
        .order_by(Workflow.created_at.desc())
        .all()
    )
