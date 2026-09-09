"""
Pydantic schemas for approval endpoints.
Extended to return full context per recommendation for the Kanban view.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ── Individual contact on approval card ──────────────────────────────────────


class ApprovalContactInfo(BaseModel):
    id: str
    full_name: str
    role: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_confirmed: bool = False
    confidence_score: float = 0.0
    email_confidence: Optional[float] = None
    email_verified: bool = False
    source: Optional[str] = None
    is_primary_persona: bool = False


# ── Buying committee ─────────────────────────────────────────────────────────

class ApprovalCommitteePersona(BaseModel):
    id: str
    full_name: str
    role: str
    linkedin_url: str = ""
    confidence_score: float = 0.0
    source: str = ""


class ApprovalBuyingCommittee(BaseModel):
    primary_persona: Optional[ApprovalCommitteePersona] = None
    secondary_personas: list[ApprovalCommitteePersona] = []
    influencers: list[ApprovalCommitteePersona] = []


# ── Full recommendation detail ────────────────────────────────────────────────


class ApprovalRecommendationDetail(BaseModel):
    id: str
    priority: str
    reason: str
    suggested_action: str
    outreach_template: str = ""
    outreach_subject: Optional[str] = None
    linkedin_message: Optional[str] = None
    confidence: float = 0.0
    buying_committee: Optional[ApprovalBuyingCommittee] = None
    talking_points: Optional[list[str]] = None
    market_trigger: Optional[str] = None
    outreach_channel: Optional[str] = None
    follow_up_sequence: Optional[list[dict]] = None


# ── Score breakdown dimension (for the approval card mini breakdown) ────────


class ApprovalDimensionScore(BaseModel):
    score: float = 0
    weight: float = 0
    detail: str = ""


# ── Full approval response ──────────────────────────────────────────────────


class ApprovalResponse(BaseModel):
    id: str
    recommendation_id: str
    status: str
    comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    decided_at: Optional[datetime] = None

    # Company context
    company_id: str = ""
    company_name: str = ""
    company_domain: str = ""
    company_industry: Optional[str] = None
    company_logo_url: Optional[str] = None

    # Score & tier
    qualification_score: Optional[float] = None
    tier: Optional[str] = None
    score_breakdown: Optional[dict[str, Any]] = None

    # Recommendation detail
    priority: str = ""
    reason: str = ""
    confidence: float = 0.0
    outreach_subject: Optional[str] = None
    outreach_template: str = ""
    linkedin_message: Optional[str] = None
    market_trigger: Optional[str] = None
    talking_points: Optional[list[str]] = None
    buying_committee: Optional[ApprovalBuyingCommittee] = None
    outreach_channel: Optional[str] = None
    follow_up_sequence: Optional[list[dict]] = None

    # Contacts
    contacts: list[ApprovalContactInfo] = []

    # Market signals
    market_signals: Optional[dict[str, Any]] = None

    # Reviewer info
    reviewer_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Decision submission request ──────────────────────────────────────────────


class ApprovalRequest(BaseModel):
    status: str  # "approved" | "rejected"
    comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    channel: Optional[str] = None       # "email" | "linkedin" | "both"
    scheduled_at: Optional[str] = None  # ISO datetime or "now"
    edited_template: Optional[str] = None
    edited_subject: Optional[str] = None
