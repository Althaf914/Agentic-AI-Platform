"""
Analytics router — funnel metrics, top companies, tech distribution,
and market signal breakdown. All endpoints are read-only aggregations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc

from backend.models.user import User
from backend.models.company import Company
from backend.models.workflow import Workflow
from backend.models.recommendation import Recommendation
from backend.models.approval import Approval
from backend.utils.dependencies import get_db, get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _score_to_tier(score: Optional[float]) -> Optional[str]:
    """Convert qualification score to tier label."""
    if score is None:
        return None
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    return "discard"


# ────────────────────────────────────────────────��────────────────────────────
#  GET /analytics/funnel — pipeline funnel metrics
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/funnel")
def funnel_metrics(
    workflow_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns funnel metrics for the current user's workflows.
    Optionally filter by specific workflow_id.
    """
    base = db.query(Company)

    if workflow_id:
        base = base.filter(Company.workflow_id == workflow_id)
    else:
        # Only user's workflows
        user_workflow_ids = (
            db.query(Workflow.id)
            .filter(Workflow.user_id == current_user.id)
            .subquery()
        )
        base = base.filter(Company.workflow_id.in_(user_workflow_ids))

    discovered = base.count()

    validated = base.filter(Company.status == "validated").count()
    rejected = base.filter(Company.status == "rejected").count()

    # Tech analyzed = companies with tech_stack_detected
    tech_analyzed = base.filter(Company.tech_stack_detected.isnot(None)).count()

    # Decision makers found = companies with at least one contact via decision_maker agent
    # Using has_linkedin or linkedin_url as proxy
    decision_makers = base.filter(
        (Company.has_linkedin == True) | (Company.linkedin_url.isnot(None))
    ).count()

    # Enriched = companies with contacts that have email
    from backend.models.contact import Contact
    enriched_subq = (
        db.query(Contact.company_id)
        .filter(Contact.email.isnot(None), Contact.email != "")
        .distinct()
    )
    if workflow_id:
        enriched_subq = enriched_subq.join(Company).filter(Company.workflow_id == workflow_id)
    else:
        enriched_subq = enriched_subq.join(Company).filter(
            Company.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.user_id == current_user.id).subquery()
            )
        )
    enriched = enriched_subq.count()

    # Qualified = has qualification_score
    qualified = base.filter(Company.qualification_score.isnot(None)).count()

    # Tier counts
    all_companies = base.filter(Company.qualification_score.isnot(None)).all()
    tier_a = sum(1 for c in all_companies if _score_to_tier(c.qualification_score) == "A")
    tier_b = sum(1 for c in all_companies if _score_to_tier(c.qualification_score) == "B")
    tier_c = sum(1 for c in all_companies if _score_to_tier(c.qualification_score) == "C")
    tier_discard = sum(1 for c in all_companies if _score_to_tier(c.qualification_score) == "discard")

    # Approved count
    approved = (
        db.query(Approval)
        .join(Recommendation)
        .join(Company)
    )
    if workflow_id:
        approved = approved.filter(Company.workflow_id == workflow_id)
    else:
        approved = approved.filter(
            Company.workflow_id.in_(
                db.query(Workflow.id).filter(Workflow.user_id == current_user.id).subquery()
            )
        )
    approved_count = approved.filter(Approval.status == "approved").count()

    return {
        "discovered": discovered,
        "validated": validated,
        "rejected": rejected,
        "tech_analyzed": tech_analyzed,
        "decision_makers": decision_makers,
        "enriched": enriched,
        "qualified": qualified,
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "tier_discard": tier_discard,
        "approved": approved_count,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /analytics/top-companies — top 10 companies by score
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/top-companies")
def top_companies(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns top N companies by qualification score across all user's workflows."""
    user_workflow_ids = (
        db.query(Workflow.id)
        .filter(Workflow.user_id == current_user.id)
        .subquery()
    )

    companies = (
        db.query(Company)
        .filter(
            Company.workflow_id.in_(user_workflow_ids),
            Company.qualification_score.isnot(None),
        )
        .order_by(Company.qualification_score.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": c.id,
            "name": c.name,
            "domain": c.domain,
            "industry": c.industry,
            "country": c.country,
            "qualification_score": c.qualification_score,
            "tier": _score_to_tier(c.qualification_score),
            "status": c.status,
            "funding_stage": c.funding_stage,
            "employee_count": c.employee_count,
            "market_signals_count": len(c.market_signals) if c.market_signals else 0,
        }
        for c in companies
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  GET /analytics/tech-distribution — tech stack aggregation
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/tech-distribution")
def tech_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregates tech stacks across all discovered companies.
    Returns a dict of {tech_name: count} sorted by count desc.
    """
    user_workflow_ids = (
        db.query(Workflow.id)
        .filter(Workflow.user_id == current_user.id)
        .subquery()
    )

    companies = (
        db.query(Company.tech_stack_detected)
        .filter(
            Company.workflow_id.in_(user_workflow_ids),
            Company.tech_stack_detected.isnot(None),
        )
        .all()
    )

    distribution: dict[str, int] = {}
    for row in companies:
        detected = row[0]
        if not isinstance(detected, dict):
            continue
        for key in ("confirmed", "probable"):
            techs = detected.get(key, [])
            if isinstance(techs, list):
                for t in techs:
                    if isinstance(t, str):
                        distribution[t] = distribution.get(t, 0) + 1

    # Sort by count descending
    sorted_dist = dict(sorted(distribution.items(), key=lambda x: -x[1]))
    return sorted_dist


# ─────────────────────────────────────────────────────────────────────────────
#  GET /analytics/signal-breakdown — market signal type counts
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/signal-breakdown")
def signal_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Categorizes and counts market signal types across all companies.
    Returns {"funding": N, "news": N, "hiring": N, "expansion": N, "leadership": N}.
    """
    user_workflow_ids = (
        db.query(Workflow.id)
        .filter(Workflow.user_id == current_user.id)
        .subquery()
    )

    companies = (
        db.query(Company.market_signals)
        .filter(
            Company.workflow_id.in_(user_workflow_ids),
            Company.market_signals.isnot(None),
        )
        .all()
    )

    counts = {
        "funding": 0,
        "news": 0,
        "hiring": 0,
        "expansion": 0,
        "leadership": 0,
        "total_companies_with_signals": 0,
    }

    for row in companies:
        signals = row[0]
        if not isinstance(signals, dict):
            continue
        counts["total_companies_with_signals"] += 1
        for key in ("funding", "news", "hiring", "expansion", "leadership"):
            sig = signals.get(key, {})
            if isinstance(sig, dict) and sig.get("detected"):
                counts[key] = counts.get(key, 0) + 1

    return counts
