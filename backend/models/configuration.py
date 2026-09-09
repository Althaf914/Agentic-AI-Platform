import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(SAEnum("icp", "persona", "scoring", name="config_type"), nullable=False)
    config_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="configurations")
    workflows = relationship("Workflow", back_populates="configuration")
