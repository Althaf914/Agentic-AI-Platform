import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from backend.database.base import Base


class PlannerLog(Base):
    __tablename__ = "planner_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    agent_selected = Column(String(255), nullable=False)
    decision_reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    from sqlalchemy.orm import relationship
    workflow = relationship("Workflow", back_populates="planner_logs")
