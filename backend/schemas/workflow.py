"""
Pydantic schemas for workflow endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentLogEntry(BaseModel):
    id: str
    agent_name: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowStartRequest(BaseModel):
    configuration_id: str
    override_icp_json: Optional[dict] = None


class WorkflowStatusResponse(BaseModel):
    id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_logs: list[AgentLogEntry] = []
    campaign_name: Optional[str] = None

    class Config:
        from_attributes = True


class ContactSummary(BaseModel):
    id: str
    full_name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    confidence_score: Optional[float] = None
    is_primary_persona: bool = False

    class Config:
        from_attributes = True


class CompanyDetail(BaseModel):
    id: str
    name: str
    domain: str
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    funding_stage: Optional[str] = None
    tech_stack_json: Optional[list] = None
    qualification_score: Optional[float] = None
    score_breakdown_json: Optional[dict] = None
    score_breakdown: Optional[dict] = None
    status: str
    rejection_reason: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    growth_rate: Optional[float] = None
    contacts: list[ContactSummary] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommendationSummary(BaseModel):
    id: str
    company_id: str
    priority: str
    reason: str
    suggested_action: str
    confidence: float

    class Config:
        from_attributes = True


class WorkflowResultsSummary(BaseModel):
    total_companies: int = 0
    validated: int = 0
    rejected: int = 0
    pending: int = 0
    with_scores: int = 0
    with_contacts: int = 0
    with_recommendations: int = 0


class WorkflowResultsResponse(BaseModel):
    summary: WorkflowResultsSummary
    companies: list[CompanyDetail] = []
    recommendations: list[RecommendationSummary] = []


class RetryAgentRequest(BaseModel):
    agent_name: str


class WorkflowListItem(BaseModel):
    id: str
    status: str
    configuration_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
