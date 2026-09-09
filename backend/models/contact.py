import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    linkedin_confirmed = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    source = Column(String(50), nullable=True)  # linkedin_serpapi | hunter_match | generated | website | formula
    is_primary_persona = Column(Boolean, nullable=False, default=False)

    # Enrichment-specific fields
    email_confidence = Column(Float, nullable=True)
    email_source = Column(String(50), nullable=True)  # website | hunter_domain | hunter_individual | formula
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_type = Column(String(20), nullable=True)  # real | estimated
    enrichment_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="contacts")
