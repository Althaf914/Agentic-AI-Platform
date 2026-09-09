import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    configuration_id = Column(String(36), ForeignKey("configurations.id"), nullable=False)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=True)
    status = Column(
        SAEnum("pending", "running", "completed", "failed", name="workflow_status"),
        nullable=False,
        default="pending",
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="workflows")
    configuration = relationship("Configuration", back_populates="workflows")
    campaign = relationship("Campaign", back_populates="workflows")
    planner_logs = relationship("PlannerLog", back_populates="workflow")
    agent_logs = relationship("AgentLog", back_populates="workflow")
    companies = relationship("Company", back_populates="workflow")
