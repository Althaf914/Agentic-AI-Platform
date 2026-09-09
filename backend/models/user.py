import uuid

from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum("admin", "sales", "viewer", name="user_role"), nullable=False, default="viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    configurations = relationship("Configuration", back_populates="user")
    campaigns = relationship("Campaign", back_populates="user")
    workflows = relationship("Workflow", back_populates="user")
    approvals = relationship("Approval", back_populates="reviewer")
