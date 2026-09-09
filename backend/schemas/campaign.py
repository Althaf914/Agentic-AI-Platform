"""
Pydantic schemas for Campaign endpoints.
Includes config_json validation via nested models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Nested config_json validation ────────────────────────────────────────────


class CampaignBusiness(BaseModel):
    description: str = ""
    value_proposition: str = ""
    product_name: str = ""
    target_market_description: str = ""


class CampaignGeography(BaseModel):
    countries: list[str] = Field(default_factory=lambda: ["US"])
    states: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)


class CampaignCompanyFilters(BaseModel):
    industries: list[str] = Field(default_factory=list)
    min_employees: int = 10
    max_employees: int = 10000
    revenue_range: str = ""
    funding_stages: list[str] = Field(default_factory=list)


class CampaignTechnologyFilters(BaseModel):
    required_tech: list[str] = Field(default_factory=list)
    nice_to_have_tech: list[str] = Field(default_factory=list)
    excluded_tech: list[str] = Field(default_factory=list)


class CampaignHiringSignals(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    min_hiring_count: int = 0


class CampaignBuyingCommittee(BaseModel):
    roles: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)


class CampaignScoringWeights(BaseModel):
    industry_match: int = 25
    location_match: int = 10
    hiring_signals: int = 15
    tech_stack_match: int = 15
    funding_stage: int = 15
    revenue_tier: int = 5
    employee_range: int = 10
    decision_makers_found: int = 5


class CampaignConfig(BaseModel):
    """Validated shape of the campaign config_json field."""
    business: CampaignBusiness = Field(default_factory=CampaignBusiness)
    geography: CampaignGeography = Field(default_factory=CampaignGeography)
    company_filters: CampaignCompanyFilters = Field(default_factory=CampaignCompanyFilters)
    technology_filters: CampaignTechnologyFilters = Field(default_factory=CampaignTechnologyFilters)
    hiring_signals: CampaignHiringSignals = Field(default_factory=CampaignHiringSignals)
    buying_committee: CampaignBuyingCommittee = Field(default_factory=CampaignBuyingCommittee)
    scoring_weights: CampaignScoringWeights = Field(default_factory=CampaignScoringWeights)


# ── Request / Response schemas ────────────────────────────────────────────────


class CampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(default="")
    config_json: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    config_json: Optional[dict[str, Any]] = None
    wizard_step_completed: Optional[int] = None


class CampaignListResponse(BaseModel):
    id: str
    name: str
    status: str
    domain: str
    wizard_step_completed: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignDetailResponse(BaseModel):
    id: str
    name: str
    status: str
    domain: str
    wizard_step_completed: int
    config_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignPreset(BaseModel):
    name: str
    description: str
    config_json: dict[str, Any]


class CampaignPresetsResponse(BaseModel):
    presets: list[CampaignPreset]
