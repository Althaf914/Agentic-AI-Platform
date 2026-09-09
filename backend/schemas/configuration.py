"""
Pydantic schemas for configuration endpoints (ICP, Persona, Scoring).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ICPConfig(BaseModel):
    # Target market
    industries: list[str] = []
    countries: list[str] = []
    locations: list[str] = []  # NEW: cities/regions e.g. ["San Francisco", "New York", "Austin"]

    # Company size
    min_employees: int = 10
    max_employees: int = 10000
    revenue_range: str = ""

    # Funding
    funding_stages: list[str] = []  # ["Series A", "Series B"]

    # Signals
    hiring_keywords: list[str] = []  # ["engineer", "product manager"]
    tech_stack: list[str] = []  # ["Python", "AWS", "React"]

    # Additional signals
    growth_indicators: list[str] = []  # ["recently funded", "expanding team"]


class PersonaConfig(BaseModel):
    name: str
    role_keywords: list[str]
    departments: list[str]
    linkedin_keywords: list[str] = []
    priority: int = 1


class ScoringConfig(BaseModel):
    funding_weight: float = 0.15
    hiring_weight: float = 0.15
    revenue_weight: float = 0.2
    icp_match_weight: float = 0.25
    tech_stack_weight: float = 0.15
    growth_weight: float = 0.1


class ConfigSaveRequest(BaseModel):
    name: str
    type: str  # "icp", "persona", "scoring"
    config_json: dict


class ConfigListResponse(BaseModel):
    id: str
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigDetailResponse(BaseModel):
    id: str
    name: str
    type: str
    config_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
