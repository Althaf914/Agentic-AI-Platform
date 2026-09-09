"""
Pydantic schemas for dashboard statistics.
"""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_companies: int
    qualified_count: int
    rejected_count: int
    pending_approvals: int
    running_workflows: int
    memory_entries: int
    agent_success_rate: float
