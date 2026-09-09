"""
Planner router — returns planner decision logs for a workflow.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.planner_log import PlannerLog
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError

router = APIRouter(prefix="/planner", tags=["Planner"])


@router.get("/{workflow_id}/logs")
def get_planner_logs(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all planner decision logs for a workflow, ordered by step number."""
    logs = (
        db.query(PlannerLog)
        .filter(PlannerLog.workflow_id == workflow_id)
        .order_by(PlannerLog.step_number)
        .all()
    )
    if not logs:
        raise NotFoundError(detail=f"No planner logs found for workflow {workflow_id}")

    return [
        {
            "id": log.id,
            "step_number": log.step_number,
            "agent_selected": log.agent_selected,
            "decision_reasoning": log.decision_reasoning,
            "created_at": log.created_at,
        }
        for log in logs
    ]
