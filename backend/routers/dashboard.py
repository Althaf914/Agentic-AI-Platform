"""
Dashboard router — aggregated statistics for the overview page.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.company import Company
from backend.models.approval import Approval
from backend.models.workflow import Workflow
from backend.models.agent_log import AgentLog
from backend.models.memory import Memory
from backend.models.user import User
from backend.schemas.dashboard import DashboardStats
from backend.utils.dependencies import get_db, get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query DB for all dashboard statistics."""
    total_companies = db.query(Company).count()
    qualified_count = (
        db.query(Company).filter(Company.status == "validated").count()
    )
    rejected_count = (
        db.query(Company).filter(Company.status == "rejected").count()
    )
    pending_approvals = (
        db.query(Approval).filter(Approval.status == "pending").count()
    )
    running_workflows = (
        db.query(Workflow).filter(Workflow.status == "running").count()
    )
    memory_entries = db.query(Memory).count()

    # Agent success rate
    total_agents = db.query(AgentLog).count()
    completed_agents = (
        db.query(AgentLog).filter(AgentLog.status == "completed").count()
    )
    agent_success_rate = (
        (completed_agents / total_agents * 100) if total_agents > 0 else 0.0
    )

    return DashboardStats(
        total_companies=total_companies,
        qualified_count=qualified_count,
        rejected_count=rejected_count,
        pending_approvals=pending_approvals,
        running_workflows=running_workflows,
        memory_entries=memory_entries,
        agent_success_rate=round(agent_success_rate, 1),
    )
