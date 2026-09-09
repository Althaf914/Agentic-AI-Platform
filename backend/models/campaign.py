import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(
        SAEnum("draft", "active", "archived", name="campaign_status"),
        nullable=False,
        default="draft",
    )
    domain = Column(String(255), nullable=False)
    wizard_step_completed = Column(Integer, nullable=False, default=0)
    config_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    workflows = relationship("Workflow", back_populates="campaign")
