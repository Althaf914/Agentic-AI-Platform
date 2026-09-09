import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id = Column(String(36), ForeignKey("recommendations.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(
        SAEnum("pending", "approved", "rejected", name="approval_status"),
        nullable=False,
        default="pending",
    )
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="approvals")
    reviewer = relationship("User", back_populates="approvals")
