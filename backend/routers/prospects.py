"""
Prospects router — paginated company listing, detail view, and enhanced
sub-endpoints for scorecard, signals, and outreach detail.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from backend.models.user import User
from backend.models.company import Company
from backend.models.recommendation import Recommendation
from backend.schemas.prospect import CompanyResponse, PaginatedProspectsResponse
from backend.services.prospect_service import get_prospects, get_prospect_detail
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError

router = APIRouter(prefix="/prospects", tags=["Prospects"])


@router.get("", response_model=PaginatedProspectsResponse)
def list_prospects(
    workflow_id: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    industry: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None, pattern="^(A|B|C)$"),
    has_email: Optional[bool] = Query(None),
    has_market_signal: Optional[bool] = Query(None),
    sort: Optional[str] = Query(None, pattern="^(score_desc|name|date)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated, filterable list of prospects with full rich data."""
    filters = {
        "workflow_id": workflow_id,
        "min_score": min_score,
        "industry": industry,
        "status": status,
        "tier": tier,
        "has_email": has_email,
        "has_market_signal": has_market_signal,
        "sort": sort,
    }
    return get_prospects(filters=filters, page=page, limit=limit, db=db)


@router.get("/{company_id}", response_model=CompanyResponse)
def prospect_detail(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full company detail with contacts and recommendation."""
    return get_prospect_detail(company_id, db)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /{company_id}/scorecard — full score_breakdown JSON for radar chart
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{company_id}/scorecard")
def get_company_scorecard(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full score_breakdown JSON, formatted for radar chart display.
    Includes all 8 dimensions with scores, weights, and the composite.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise NotFoundError(detail=f"Company {company_id} not found")

    breakdown = company.score_breakdown
    if not breakdown:
        return {
            "company_id": company_id,
            "company_name": company.name,
            "score_breakdown": None,
            "radar_data": [],
            "composite": None,
            "tier": None,
        }

    # Build radar-friendly format: [{dimension, label, score, weight}, ...]
    dims = [
        "industry_match", "location_match", "hiring_signals",
        "tech_stack_match", "funding_stage", "revenue_tier",
        "employee_range", "decision_makers_found",
    ]
    labels = {
        "industry_match": "Industry match",
        "location_match": "Location match",
        "hiring_signals": "Hiring signals",
        "tech_stack_match": "Tech stack match",
        "funding_stage": "Funding stage",
        "revenue_tier": "Revenue tier",
        "employee_range": "Employee range",
        "decision_makers_found": "Decision makers",
    }

    radar_data = []
    for d in dims:
        dim_data = breakdown.get(d)
        if isinstance(dim_data, dict):
            radar_data.append({
                "dimension": d,
                "label": labels.get(d, d),
                "score": dim_data.get("score", 0),
                "weight": dim_data.get("weight", 0),
                "detail": dim_data.get("detail", ""),
            })

    return {
        "company_id": company_id,
        "company_name": company.name,
        "score_breakdown": breakdown,
        "radar_data": radar_data,
        "composite": breakdown.get("composite"),
        "tier": breakdown.get("tier"),
        "reason": breakdown.get("reason"),
        "strongest_signal": breakdown.get("strongest_signal"),
        "weakest_signal": breakdown.get("weakest_signal"),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /{company_id}/signals �� market_signals + tech_stack_detected
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{company_id}/signals")
def get_company_signals(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns market_signals + tech_stack_detected for sidebar display."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise NotFoundError(detail=f"Company {company_id} not found")

    return {
        "company_id": company_id,
        "company_name": company.name,
        "market_signals": company.market_signals or {},
        "tech_stack_detected": company.tech_stack_detected or {},
        "hiring_signal_score": company.hiring_signal_score,
        "domain_age_days": company.domain_age_days,
        "has_linkedin": company.has_linkedin,
        "linkedin_url": company.linkedin_url,
    }


# ──────────────────────────────────────────��──────────────────────────────────
#  GET /{company_id}/outreach — full recommendation with templates
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{company_id}/outreach")
def get_company_outreach(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full recommendation with outreach templates and follow_up_sequence.
    """
    rec = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.company))
        .filter(Recommendation.company_id == company_id)
        .first()
    )
    if not rec:
        raise NotFoundError(detail=f"No recommendation found for company {company_id}")

    company = rec.company

    return {
        "company_id": company_id,
        "company_name": company.name if company else "Unknown",
        "recommendation_id": rec.id,
        "priority": rec.priority,
        "confidence": rec.confidence,
        "reason": rec.reason,
        "suggested_action": rec.suggested_action,
        "outreach_subject": rec.outreach_subject,
        "outreach_template": rec.outreach_template,
        "linkedin_message": rec.linkedin_message,
        "market_trigger": rec.market_trigger,
        "outreach_channel": rec.outreach_channel,
        "talking_points": rec.talking_points,
        "buying_committee": rec.buying_committee,
        "follow_up_sequence": rec.follow_up_sequence or [],
        "created_at": rec.created_at,
    }
