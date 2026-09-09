"""
Approvals router — queue listing, decision submission, bulk actions,
inline outreach editing, and stats aggregation.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.models.user import User
from backend.models.approval import Approval
from backend.models.recommendation import Recommendation
from backend.models.company import Company
from backend.schemas.approval import ApprovalRequest, ApprovalResponse
from backend.services.approval_service import list_approvals, submit_approval
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError

router = APIRouter(prefix="/approvals", tags=["Approvals"])


# ─── Inline request schemas ───────────────────────────────────────────────────


class EditOutreachRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    linkedin_message: Optional[str] = None


class BulkActionRequest(BaseModel):
    ids: list[str]
    action: str  # "approve" | "reject"
    comment: Optional[str] = None
    rejection_reason: Optional[str] = None


# ─── GET /approvals — list with optional status filter ────────────────────────


@router.get("", response_model=list[ApprovalResponse])
def list_approvals_endpoint(
    status: Optional[str] = Query("pending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List approval queue with full context per approval (Kanban view)."""
    return list_approvals(status=status, db=db)


# ─── GET /approvals/stats — aggregated approval stats ─────────────────────────


@router.get("/stats")
def approval_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated approval statistics for the stats bar."""
    approvals_q = db.query(Approval)
    total_pending = approvals_q.filter(Approval.status == "pending").count()
    total_approved = approvals_q.filter(Approval.status == "approved").count()
    total_rejected = approvals_q.filter(Approval.status == "rejected").count()

    # Avg score across all companies that have approvals
    avg_score = (
        db.query(Company.qualification_score)
        .join(Recommendation, Recommendation.company_id == Company.id)
        .join(Approval, Approval.recommendation_id == Recommendation.id)
        .filter(Company.qualification_score.isnot(None))
        .all()
    )
    scores = [s[0] for s in avg_score if s[0] is not None]
    avg_composite = round(sum(scores) / len(scores), 1) if scores else 0.0

    # High priority count (pending approvals on high-priority recommendations)
    high_priority = (
        db.query(Approval)
        .join(Recommendation, Approval.recommendation_id == Recommendation.id)
        .filter(
            Approval.status == "pending",
            Recommendation.priority == "high",
        )
        .count()
    )

    return {
        "pending": total_pending,
        "approved": total_approved,
        "rejected": total_rejected,
        "avg_score": avg_composite,
        "high_priority": high_priority,
    }


# ─── POST /approvals/{id} — decide a single approval ──────────────────────────


@router.post("/{approval_id}", response_model=ApprovalResponse)
def decide_approval(
    approval_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an approval decision (approve/reject). Returns rich context."""
    result = submit_approval(
        approval_id=approval_id,
        request=request,
        reviewer_id=current_user.id,
        db=db,
    )
    return result


# ─── PUT /approvals/{id}/edit-outreach — edit outreach templates inline ───────


@router.put("/{approval_id}/edit-outreach")
def edit_outreach(
    approval_id: str,
    request: EditOutreachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update recommendation outreach template (for inline editor on approve flow).
    Directly modifies the linked Recommendation row.
    """
    approval = (
        db.query(Approval)
        .options(joinedload(Approval.recommendation))
        .filter(Approval.id == approval_id)
        .first()
    )
    if not approval:
        raise NotFoundError(detail=f"Approval {approval_id} not found")

    rec = approval.recommendation
    if not rec:
        raise NotFoundError(detail=f"Recommendation for approval {approval_id} not found")

    if request.subject is not None:
        rec.outreach_subject = request.subject
    if request.body is not None:
        rec.outreach_template = request.body
    if request.linkedin_message is not None:
        rec.linkedin_message = request.linkedin_message

    db.commit()

    return {
        "message": "Outreach template updated",
        "approval_id": approval_id,
        "recommendation_id": rec.id,
        "outreach_subject": rec.outreach_subject,
        "outreach_template": rec.outreach_template,
        "linkedin_message": rec.linkedin_message,
    }


# ─── POST /approvals/bulk — bulk approve or reject ────────────────────────────


@router.post("/bulk")
def bulk_approve_reject(
    request: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk approve or reject multiple approvals at once."""
    if request.action not in ("approve", "reject"):
        from backend.utils.exceptions import ValidationError
        raise ValidationError(detail="Action must be 'approve' or 'reject'")

    approvals = (
        db.query(Approval)
        .filter(Approval.id.in_(request.ids), Approval.status == "pending")
        .all()
    )

    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    updated = 0
    for approval in approvals:
        approval.status = request.action
        approval.reviewer_id = current_user.id
        approval.decided_at = now
        if request.comment:
            approval.comment = request.comment
        if request.rejection_reason and request.action == "reject":
            approval.comment = request.rejection_reason
        updated += 1

    db.commit()

    return {
        "message": f"{request.action}d {updated} approvals",
        "action": request.action,
        "requested": len(request.ids),
        "updated": updated,
    }
