"""
Pydantic models for typed execution plans produced by the Planner Agent.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentStep(BaseModel):
    """A single step in the execution plan."""
    agent_name: str  # One of: search_strategy, company_discovery, validation, decision_maker, contact_enrichment, qualification, recommendation_memory
    input_params: dict = {}
    skip: bool = False
    skip_reason: Optional[str] = None


class ExecutionPlan(BaseModel):
    """The full execution plan output by the Planner Agent."""
    workflow_id: str
    steps: list[AgentStep]
    reasoning: str
    created_at: datetime

    @property
    def active_steps(self) -> list[AgentStep]:
        """Returns only steps that are not skipped."""
        return [step for step in self.steps if not step.skip]

    @property
    def skipped_steps(self) -> list[AgentStep]:
        """Returns only steps that are skipped."""
        return [step for step in self.steps if step.skip]
