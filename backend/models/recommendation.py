import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    priority = Column(SAEnum("high", "medium", "low", name="priority_level"), nullable=False)
    reason = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    outreach_template = Column(Text, nullable=False)
    outreach_subject = Column(String(500), nullable=True)
    linkedin_message = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    buying_committee = Column(JSON, nullable=True)
    talking_points = Column(JSON, nullable=True)
    market_trigger = Column(String(255), nullable=True)
    outreach_channel = Column(String(50), nullable=True)
    follow_up_sequence = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="recommendations")
    approvals = relationship("Approval", back_populates="recommendation")
