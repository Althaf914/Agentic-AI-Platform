"""
Approval service — handles approve/reject decisions and returns rich context
for the Kanban-style approval queue page.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from backend.models.approval import Approval
from backend.models.recommendation import Recommendation
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.user import User
from backend.schemas.approval import ApprovalRequest as ApprovalRequestSchema
from backend.utils.exceptions import NotFoundError, ValidationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _build_rich_approval(approval: Approval) -> dict[str, Any]:
    """Build a rich approval response dict from the joined Approval object."""
    rec: Optional[Recommendation] = approval.recommendation
    company: Optional[Company] = rec.company if rec else None

    # Prepare contacts (eager-loaded via recommendation → company → contacts)
    contacts_list: list[dict] = []
    if company and company.contacts:
        for c in company.contacts:
            contacts_list.append({
                "id": c.id,
                "full_name": c.full_name,
                "role": c.role or "",
                "email": c.email,
                "linkedin_url": c.linkedin_url,
                "linkedin_confirmed": c.linkedin_confirmed,
                "confidence_score": c.confidence_score,
                "email_confidence": c.email_confidence,
                "email_verified": c.email_verified,
                "source": c.source,
                "is_primary_persona": c.is_primary_persona,
            })

    # Score breakdown from company
    score_breakdown = None
    tier = None
    if company:
        sb = company.score_breakdown or company.score_breakdown_json
        if sb:
            score_breakdown = sb if isinstance(sb, dict) else None
            tier = sb.get("tier") if isinstance(sb, dict) else None

    # Market signals
    market_signals = company.market_signals if company else None

    # Reviewer name
    reviewer_name = None
    if approval.reviewer:
        reviewer_name = getattr(approval.reviewer, "full_name", None) or getattr(approval.reviewer, "email", None)

    return {
        "id": approval.id,
        "recommendation_id": approval.recommendation_id,
        "status": approval.status,
        "comment": approval.comment,
        "rejection_reason": approval.comment if approval.status == "rejected" else None,
        "decided_at": approval.decided_at,
        # Company
        "company_id": company.id if company else "",
        "company_name": company.name if company else "Unknown",
        "company_domain": company.domain if company else "",
        "company_industry": company.industry if company else None,
        "company_logo_url": company.logo_url if company else None,
        # Score
        "qualification_score": company.qualification_score if company else None,
        "tier": tier,
        "score_breakdown": score_breakdown,
        # Recommendation
        "priority": rec.priority if rec else "",
        "reason": rec.reason if rec else "",
        "confidence": rec.confidence if rec else 0.0,
        "outreach_subject": rec.outreach_subject if rec else None,
        "outreach_template": rec.outreach_template or "",
        "linkedin_message": rec.linkedin_message if rec else None,
        "market_trigger": rec.market_trigger if rec else None,
        "talking_points": rec.talking_points if rec else None,
        "buying_committee": _serialize_buying_committee(rec.buying_committee) if rec and rec.buying_committee else None,
        "outreach_channel": rec.outreach_channel if rec else None,
        "follow_up_sequence": rec.follow_up_sequence if rec else None,
        # Contacts
        "contacts": contacts_list,
        # Market signals
        "market_signals": market_signals,
        # Reviewer
        "reviewer_name": reviewer_name,
    }


def _serialize_buying_committee(bc: Any) -> Optional[dict]:
    """Convert buying_committee JSON to structured dict."""
    if not bc:
        return None
    if isinstance(bc, dict):
        return bc
    return None


def list_approvals(status: Optional[str], db: Session) -> list[dict]:
    """List approval queue with full context per approval."""
    query = (
        db.query(Approval)
        .options(
            joinedload(Approval.recommendation)
            .joinedload(Recommendation.company)
            .joinedload(Company.contacts),
            joinedload(Approval.reviewer),
        )
    )

    if status and status != "all":
        query = query.filter(Approval.status == status)

    approvals = query.order_by(Approval.created_at.desc()).all()

    return [_build_rich_approval(a) for a in approvals]


def submit_approval(
    approval_id: str,
    request: ApprovalRequestSchema,
    reviewer_id: str,
    db: Session,
) -> dict:
    """Process an approval decision and return rich response."""
    approval = (
        db.query(Approval)
        .options(
            joinedload(Approval.recommendation)
            .joinedload(Recommendation.company)
            .joinedload(Company.contacts),
            joinedload(Approval.reviewer),
        )
        .filter(Approval.id == approval_id)
        .first()
    )
    if not approval:
        raise NotFoundError(detail=f"Approval {approval_id} not found")

    if request.status not in ("approved", "rejected"):
        raise ValidationError(detail="Status must be 'approved' or 'rejected'")

    if approval.status != "pending":
        raise ValidationError(detail=f"Approval already decided: {approval.status}")

    # Update approval
    approval.status = request.status
    approval.comment = request.comment or request.rejection_reason
    approval.reviewer_id = reviewer_id
    approval.decided_at = datetime.now(timezone.utc)

    # Update recommendation with edited template if provided
    if request.status == "approved" and request.edited_template:
        rec = approval.recommendation
        if rec:
            rec.outreach_template = request.edited_template
            if request.edited_subject:
                rec.outreach_subject = request.edited_subject
            if request.channel:
                rec.outreach_channel = request.channel

    db.commit()

    # If approved, trigger memory write
    if request.status == "approved":
        _write_to_memory(approval, db)

    return _build_rich_approval(approval)


def _write_to_memory(approval: Approval, db: Session):
    """Write approved recommendation to shared memory for future reference."""
    try:
        from backend.memory.shared_memory import write_memory

        rec = approval.recommendation
        if not rec:
            return
        company = rec.company
        if not company:
            return

        summary = (
            f"Approved outreach for {company.name} ({company.domain}). "
            f"Priority: {rec.priority}. "
            f"Reason: {rec.reason}"
        )

        write_memory(
            entity_type="company",
            entity_id=company.id,
            summary=summary,
            metadata_json={
                "recommendation_id": rec.id,
                "priority": rec.priority,
                "suggested_action": rec.suggested_action,
            },
            db=db,
        )
        logger.info(f"Memory written for approved company: {company.name}")
    except Exception as e:
        logger.error(f"Failed to write memory on approval: {e}")
