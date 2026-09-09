"""
Prospect service — querying and filtering companies with contacts and recommendations.
Returns all rich fields needed for the 8-dimension scorecard and detail panel.
"""

from typing import Any

from sqlalchemy.orm import Session, joinedload

from backend.models.company import Company
from backend.utils.exceptions import NotFoundError


def _serialize_company(company: Company) -> dict[str, Any]:
    """Serialize a Company row into the full API response dict."""
    rec = company.recommendations[0] if company.recommendations else None

    # When joinedload is used the relationship items are plain ORM objects;
    # we rely on FastAPI's from_attributes to handle nested conversion.
    # For JSON columns ensure None rather than missing keys.
    return {
        "id": company.id,
        "name": company.name,
        "domain": company.domain,
        "industry": company.industry,
        "country": company.country,
        "city": company.city,
        "employee_count": company.employee_count,
        "revenue_range": company.revenue_range,
        "funding_stage": company.funding_stage,
        "qualification_score": company.qualification_score,
        "status": company.status,
        "description": company.description,
        "logo_url": company.logo_url,
        "linkedin_url": company.linkedin_url,
        "domain_age_days": company.domain_age_days,
        "hiring_signal_score": company.hiring_signal_score,
        "has_linkedin": company.has_linkedin,
        "source": company.source,
        "growth_rate": company.growth_rate,
        "tech_stack_detected": company.tech_stack_detected,
        "market_signals": company.market_signals,
        "score_breakdown": company.score_breakdown,
        "validation_details": company.validation_details,
        "metadata_json": company.metadata_json,
        "contacts": company.contacts if company.contacts else [],
        "recommendation": rec,
    }


def get_prospects(filters: dict, page: int, limit: int, db: Session) -> dict:
    """Paginated query with optional filters. Returns full company data."""
    query = db.query(Company)

    if filters.get("workflow_id"):
        query = query.filter(Company.workflow_id == filters["workflow_id"])

    if filters.get("min_score") is not None:
        query = query.filter(Company.qualification_score >= filters["min_score"])

    if filters.get("industry"):
        query = query.filter(Company.industry.ilike(f"%{filters['industry']}%"))

    if filters.get("status"):
        query = query.filter(Company.status == filters["status"])

    # Additional filters for the enhanced page
    if filters.get("tier"):
        # tier is stored in score_breakdown - we filter after fetch for simplicity
        pass

    if filters.get("has_email"):
        # Filter companies that have at least one contact with email
        from backend.models.contact import Contact
        subq = (
            db.query(Contact.company_id)
            .filter(Contact.email.isnot(None), Contact.email != "")
            .distinct()
        )
        query = query.filter(Company.id.in_(subq))

    if filters.get("has_market_signal"):
        query = query.filter(Company.market_signals.isnot(None))

    total = query.count()
    offset = (page - 1) * limit

    companies = (
        query.options(joinedload(Company.contacts), joinedload(Company.recommendations))
        .order_by(Company.qualification_score.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Post-filter by tier if needed (stored in JSON column)
    items = []
    tier_filter = filters.get("tier")
    for company in companies:
        if tier_filter:
            breakdown = company.score_breakdown or {}
            if breakdown.get("tier") != tier_filter:
                continue
        items.append(_serialize_company(company))

    # Re-count after post-filter
    filtered_total = len(items)

    return {
        "items": items,
        "total": filtered_total,
        "total_raw": total,
        "page": page,
        "limit": limit,
    }


def get_prospect_detail(company_id: str, db: Session) -> dict:
    """Get a single company with all contacts and recommendation."""
    company = (
        db.query(Company)
        .options(joinedload(Company.contacts), joinedload(Company.recommendations))
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise NotFoundError(detail=f"Company {company_id} not found")

    return _serialize_company(company)
