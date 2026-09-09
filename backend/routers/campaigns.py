"""
Campaigns router — CRUD for campaign configurations with config_json validation,
presets library, and A/B test duplication.
"""

import copy
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.campaign import Campaign
from backend.schemas.campaign import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignListResponse,
    CampaignDetailResponse,
    CampaignPresetsResponse,
    CampaignConfig,
)
from backend.utils.dependencies import get_db, get_current_user
from backend.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# ─── Preset library ──────────────────────────────────────────────────────────

B2B_SAAS_PRESET = {
    "business": {
        "description": "AI-powered B2B SaaS platform for sales teams",
        "value_proposition": "Automate prospect discovery and outreach with AI agents",
        "product_name": "AgentForge AI",
        "target_market_description": "B2B SaaS companies with 10-500 employees",
    },
    "geography": {
        "countries": ["US", "Canada", "UK"],
        "states": ["California", "New York", "Texas", "Illinois", "Florida"],
        "cities": ["San Francisco", "New York", "Austin", "Boston", "Chicago", "Denver", "Seattle"],
    },
    "company_filters": {
        "industries": ["SaaS", "Enterprise Software", "Cloud Computing", "B2B Software", "AI", "Machine Learning"],
        "min_employees": 10,
        "max_employees": 2000,
        "revenue_range": "$1-10M",
        "funding_stages": ["Seed", "Series A", "Series B"],
    },
    "technology_filters": {
        "required_tech": ["AWS", "Python", "React", "PostgreSQL"],
        "nice_to_have_tech": ["Kubernetes", "Docker", "TypeScript", "GraphQL", "Redis"],
        "excluded_tech": ["PHP", "WordPress", "Shopify"],
    },
    "hiring_signals": {
        "keywords": ["software engineer", "sales", "customer success", "product manager"],
        "roles": ["Engineering", "Sales", "Marketing"],
        "min_hiring_count": 3,
    },
    "buying_committee": {
        "roles": ["VP of Sales", "Head of Revenue", "CRO", "CEO", "Head of Growth", "VP of Marketing"],
        "departments": ["Sales", "Marketing", "Executive"],
        "seniority": ["VP", "Director", "C-Level", "Head"],
    },
    "scoring_weights": {
        "industry_match": 25,
        "location_match": 10,
        "hiring_signals": 15,
        "tech_stack_match": 15,
        "funding_stage": 15,
        "revenue_tier": 5,
        "employee_range": 10,
        "decision_makers_found": 5,
    },
}

CYBERSECURITY_PRESET = {
    "business": {
        "description": "Next-gen cybersecurity platform for enterprise",
        "value_proposition": "AI-driven threat detection and response platform",
        "product_name": "CyberForge",
        "target_market_description": "Cybersecurity and IT companies with 50+ employees",
    },
    "geography": {
        "countries": ["US", "UK", "Germany", "Israel", "Singapore"],
        "states": ["California", "Virginia", "Texas", "Massachusetts", "Washington"],
        "cities": ["San Jose", "Austin", "Washington DC", "Tel Aviv", "London", "Berlin"],
    },
    "company_filters": {
        "industries": ["Cybersecurity", "Information Security", "Network Security", "IT Security", "Cloud Security", "Defense"],
        "min_employees": 50,
        "max_employees": 10000,
        "revenue_range": "$10-50M",
        "funding_stages": ["Series A", "Series B", "Series C", "Series D"],
    },
    "technology_filters": {
        "required_tech": ["Python", "AWS", "Kubernetes", "Linux"],
        "nice_to_have_tech": ["Go", "Rust", "TensorFlow", "Elasticsearch", "Splunk"],
        "excluded_tech": ["PHP", "WordPress"],
    },
    "hiring_signals": {
        "keywords": ["security engineer", "penetration tester", "SOC analyst", "incident response"],
        "roles": ["Engineering", "Security", "IT"],
        "min_hiring_count": 5,
    },
    "buying_committee": {
        "roles": ["CISO", "VP of Security", "CTO", "CIO", "Head of IT", "Security Director"],
        "departments": ["Security", "IT", "Executive", "Engineering"],
        "seniority": ["C-Level", "VP", "Director", "Head"],
    },
    "scoring_weights": {
        "industry_match": 30,
        "location_match": 5,
        "hiring_signals": 15,
        "tech_stack_match": 20,
        "funding_stage": 10,
        "revenue_tier": 5,
        "employee_range": 5,
        "decision_makers_found": 10,
    },
}

STAFFING_PRESET = {
    "business": {
        "description": "AI-powered staffing and recruitment platform",
        "value_proposition": "Automate candidate sourcing and client matching",
        "product_name": "StaffForge",
        "target_market_description": "Staffing agencies and HR tech companies of all sizes",
    },
    "geography": {
        "countries": ["US", "Canada", "UK", "Australia"],
        "states": ["California", "New York", "Texas", "Illinois", "Georgia", "Florida"],
        "cities": ["New York", "San Francisco", "Chicago", "Atlanta", "Dallas", "Miami", "Los Angeles"],
    },
    "company_filters": {
        "industries": ["Staffing", "Recruitment", "HR Tech", "Talent Acquisition", "Workforce Management", "Human Resources"],
        "min_employees": 5,
        "max_employees": 5000,
        "revenue_range": "$1-10M",
        "funding_stages": ["Seed", "Series A", "Bootstrapped"],
    },
    "technology_filters": {
        "required_tech": ["Python", "React", "PostgreSQL"],
        "nice_to_have_tech": ["Docker", "TypeScript", "Node.js", "Elasticsearch", "Salesforce"],
        "excluded_tech": ["WordPress", "Shopify", "Magento"],
    },
    "hiring_signals": {
        "keywords": ["recruiter", "talent acquisition", "HR manager", "staffing coordinator"],
        "roles": ["HR", "Recruiting", "Operations"],
        "min_hiring_count": 2,
    },
    "buying_committee": {
        "roles": ["VP of Talent", "Head of HR", "CEO", "Director of Recruiting", "COO"],
        "departments": ["HR", "Recruiting", "Executive", "Operations"],
        "seniority": ["VP", "Director", "C-Level", "Head", "Manager"],
    },
    "scoring_weights": {
        "industry_match": 25,
        "location_match": 15,
        "hiring_signals": 20,
        "tech_stack_match": 10,
        "funding_stage": 5,
        "revenue_tier": 5,
        "employee_range": 10,
        "decision_makers_found": 10,
    },
}

PRESETS = {
    "b2b_saas": {"name": "B2B SaaS", "description": "Target B2B SaaS companies with tech stack matching", "config_json": B2B_SAAS_PRESET},
    "cybersecurity": {"name": "Cybersecurity", "description": "Target cybersecurity firms and enterprise security buyers", "config_json": CYBERSECURITY_PRESET},
    "staffing": {"name": "Staffing & Recruitment", "description": "Target staffing agencies and HR tech companies", "config_json": STAFFING_PRESET},
}


def _validate_config_json(data: dict) -> dict:
    """Validate config_json against CampaignConfig schema, return cleaned version."""
    try:
        validated = CampaignConfig(**data)
        return validated.model_dump()
    except Exception as e:
        raise ValidationError(detail=f"Invalid campaign configuration: {str(e)}")


# ─── GET /campaigns/presets — get preset library ──────────────────────────────


@router.get("/presets", response_model=CampaignPresetsResponse)
def get_presets():
    """Get the 3 campaign presets (b2b_saas, cybersecurity, staffing)."""
    return CampaignPresetsResponse(presets=list(PRESETS.values()))


# ─── POST /campaigns — create new campaign ────────────────────────────────────


@router.post("", response_model=CampaignDetailResponse, status_code=201)
def create_campaign(
    request: CampaignCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new campaign with validated config_json."""
    validated_config = _validate_config_json(request.config_json)

    campaign = Campaign(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=request.name,
        domain=request.domain,
        config_json=validated_config,
        status="draft",
        wizard_step_completed=0,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


# ─── GET /campaigns — list user's campaigns ───────────────────────────────────


@router.get("", response_model=list[CampaignListResponse])
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all campaigns for the current user, sorted by created_at desc."""
    campaigns = (
        db.query(Campaign)
        .filter(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return campaigns


# ─── GET /campaigns/{id} — get campaign detail ────────────────────────────────


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single campaign with full config_json."""
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .first()
    )
    if not campaign:
        raise NotFoundError(detail=f"Campaign {campaign_id} not found")
    return campaign


# ─── PUT /campaigns/{id} — partial update ──────────────────────────────────────


@router.put("/{campaign_id}", response_model=CampaignDetailResponse)
def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a campaign (e.g. wizard step-by-step saves)."""
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .first()
    )
    if not campaign:
        raise NotFoundError(detail=f"Campaign {campaign_id} not found")

    if request.name is not None:
        campaign.name = request.name
    if request.domain is not None:
        campaign.domain = request.domain
    if request.wizard_step_completed is not None:
        campaign.wizard_step_completed = request.wizard_step_completed
    if request.config_json is not None:
        # Merge deeply: new values override, missing keys keep existing
        current = dict(campaign.config_json or {})
        for key, value in request.config_json.items():
            if isinstance(value, dict) and key in current and isinstance(current[key], dict):
                current[key] = {**current[key], **value}
            else:
                current[key] = value
        validated = _validate_config_json(current)
        campaign.config_json = validated

    campaign.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    return campaign


# ─── POST /campaigns/{id}/duplicate — A/B test copy ────────────────────────────


@router.post("/{campaign_id}/duplicate", response_model=CampaignDetailResponse, status_code=201)
def duplicate_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duplicate a campaign for A/B testing."""
    original = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .first()
    )
    if not original:
        raise NotFoundError(detail=f"Campaign {campaign_id} not found")

    dup = Campaign(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=f"{original.name} (Copy)",
        domain=original.domain,
        config_json=copy.deepcopy(original.config_json),
        status="draft",
        wizard_step_completed=original.wizard_step_completed,
    )
    db.add(dup)
    db.commit()
    db.refresh(dup)
    return dup


# ─── DELETE /campaigns/{id} — remove campaign ──────────────────────────────────


@router.delete("/{campaign_id}")
def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a campaign."""
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        .first()
    )
    if not campaign:
        raise NotFoundError(detail=f"Campaign {campaign_id} not found")

    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted", "id": campaign_id}
