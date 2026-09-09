import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    agent_name = Column(String(255), nullable=False)
    status = Column(
        SAEnum("idle", "running", "completed", "failed", name="agent_status"),
        nullable=False,
        default="idle",
    )
    input_json = Column(JSON, nullable=True)
    output_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_logs")
