"""
Workflow router — start, status, results, retry, and list endpoints.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.schemas.workflow import (
    WorkflowStartRequest,
    WorkflowStatusResponse,
    WorkflowResultsResponse,
    WorkflowResultsSummary,
    CompanyDetail,
    ContactSummary,
    RecommendationSummary,
    RetryAgentRequest,
    WorkflowListItem,
)
from backend.services.workflow_service import (
    start_workflow,
    get_workflow_status,
    retry_agent,
    get_user_workflows,
)
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError

router = APIRouter(prefix="/workflow", tags=["Workflows"])


def _build_workflow_results(workflow_id: str, db: Session) -> WorkflowResultsResponse:
    """Shared logic — build full company results with scores, contacts, and recommendations."""
    companies = db.query(Company).filter(Company.workflow_id == workflow_id).all()
    if not companies:
        raise NotFoundError(detail="No results found for this workflow")

    company_ids = [c.id for c in companies]

    # Build rich company details with contacts
    company_details = []
    for c in companies:
        contacts_list = (
            db.query(Contact)
            .filter(Contact.company_id == c.id)
            .all()
        )
        company_details.append(CompanyDetail(
            id=c.id,
            name=c.name,
            domain=c.domain,
            industry=c.industry,
            country=c.country,
            city=c.city,
            employee_count=c.employee_count,
            revenue_range=c.revenue_range,
            funding_stage=c.funding_stage,
            tech_stack_json=c.tech_stack_json,
            qualification_score=c.qualification_score,
            score_breakdown_json=c.score_breakdown_json,
            score_breakdown=c.score_breakdown,
            status=c.status,
            rejection_reason=c.rejection_reason,
            logo_url=c.logo_url,
            description=c.description,
            growth_rate=c.growth_rate,
            contacts=[
                ContactSummary(
                    id=ct.id,
                    full_name=ct.full_name,
                    role=ct.role,
                    email=ct.email,
                    phone=ct.phone,
                    linkedin_url=ct.linkedin_url,
                    confidence_score=ct.confidence_score,
                    is_primary_persona=ct.is_primary_persona,
                )
                for ct in contacts_list
            ],
            created_at=c.created_at,
        ))

    # Aggregate summary stats
    validated = len([c for c in companies if c.status == "validated"])
    rejected = len([c for c in companies if c.status == "rejected"])
    pending = len([c for c in companies if c.status == "pending"])
    with_scores = len([c for c in companies if c.qualification_score is not None])
    with_contacts = len([c for c in company_details if c.contacts])

    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.company_id.in_(company_ids))
        .all()
    )

    return WorkflowResultsResponse(
        summary=WorkflowResultsSummary(
            total_companies=len(companies),
            validated=validated,
            rejected=rejected,
            pending=pending,
            with_scores=with_scores,
            with_contacts=with_contacts,
            with_recommendations=len(recommendations),
        ),
        companies=company_details,
        recommendations=[
            RecommendationSummary(
                id=r.id,
                company_id=r.company_id,
                priority=r.priority,
                reason=r.reason,
                suggested_action=r.suggested_action,
                confidence=r.confidence,
            )
            for r in recommendations
        ],
    )


@router.post("/start", response_model=WorkflowStatusResponse)
async def start(
    request: WorkflowStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new discovery workflow."""
    workflow = await start_workflow(
        config_id=request.configuration_id,
        user_id=current_user.id,
        db=db,
    )
    return WorkflowStatusResponse(
        id=workflow.id,
        status=workflow.status,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        agent_logs=[],
    )


@router.get("/{workflow_id}", response_model=WorkflowResultsResponse)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflow with full company details (scores, contacts, emails) and recommendations."""
    return _build_workflow_results(workflow_id, db)


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
def status(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflow status with agent logs."""
    result = get_workflow_status(workflow_id, db)
    return WorkflowStatusResponse(**result)


@router.get("/{workflow_id}/results", response_model=WorkflowResultsResponse)
def results(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get discovered companies (with scores, contacts/emails) and recommendations for a workflow."""
    return _build_workflow_results(workflow_id, db)


@router.post("/{workflow_id}/retry-agent")
def retry(
    workflow_id: str,
    request: RetryAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run a specific agent within a workflow."""
    agent_log = retry_agent(workflow_id, request.agent_name, db)
    return {"message": f"Agent '{request.agent_name}' re-dispatched", "agent_log_id": agent_log.id}


@router.get("s", response_model=list[WorkflowListItem])
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all workflows for the current user (for WorkflowHistory page)."""
    workflows = get_user_workflows(current_user.id, db)
    return workflows
