"""
Pydantic schemas for prospect (company + contact) endpoints.
Extended to expose all rich fields: score_breakdown, market_signals, tech_stack_detected, etc.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


# ── Contact ──────────────────────────────────────────────────────────────────


class ContactResponse(BaseModel):
    id: str
    full_name: str
    role: str
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_confirmed: bool = False
    confidence_score: float = 0.0
    source: Optional[str] = None
    is_primary_persona: bool = False
    email_confidence: Optional[float] = None
    email_source: Optional[str] = None
    email_verified: bool = False
    phone_type: Optional[str] = None
    enrichment_score: Optional[float] = None

    class Config:
        from_attributes = True


# ── Recommendation ───────────────────────────────────────────────────────────


class RecommendationDetail(BaseModel):
    id: str
    priority: str
    reason: str
    suggested_action: str
    outreach_template: str = ""
    outreach_subject: Optional[str] = None
    linkedin_message: Optional[str] = None
    confidence: float = 0.0
    buying_committee: Optional[Any] = None
    talking_points: Optional[list[str]] = None
    market_trigger: Optional[str] = None
    outreach_channel: Optional[str] = None
    follow_up_sequence: Optional[list[dict]] = None

    class Config:
        from_attributes = True


# ── Company ──────────────────────────────────────────────────────────────────


class CompanyResponse(BaseModel):
    id: str
    name: str
    domain: str
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    funding_stage: Optional[str] = None
    qualification_score: Optional[float] = None
    status: str = "pending"
    description: Optional[str] = None
    logo_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    domain_age_days: Optional[int] = None
    hiring_signal_score: Optional[float] = None
    has_linkedin: bool = False
    source: Optional[str] = None
    growth_rate: Optional[float] = None
    # JSON columns exposed as unstructured dicts / lists
    tech_stack_detected: Optional[Any] = None
    market_signals: Optional[Any] = None
    score_breakdown: Optional[Any] = None
    validation_details: Optional[Any] = None
    metadata_json: Optional[Any] = None
    # Nested relations
    contacts: list[ContactResponse] = []
    recommendation: Optional[RecommendationDetail] = None

    class Config:
        from_attributes = True


# ── Paginated wrapper ────────────────────────────────────────────────────────


class PaginatedProspectsResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    page: int
    limit: int
