"""
Models package — imports all ORM models so Alembic can detect them via Base.metadata.
"""

from backend.models.user import User
from backend.models.configuration import Configuration
from backend.models.campaign import Campaign
from backend.models.workflow import Workflow
from backend.models.planner_log import PlannerLog
from backend.models.agent_log import AgentLog
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.models.approval import Approval
from backend.models.memory import Memory

__all__ = [
    "User",
    "Configuration",
    "Campaign",
    "Workflow",
    "PlannerLog",
    "AgentLog",
    "Company",
    "Contact",
    "Recommendation",
    "Approval",
    "Memory",
]
