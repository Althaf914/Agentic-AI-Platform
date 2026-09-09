import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON, Text, Boolean, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    employee_count = Column(Integer, nullable=True)
    revenue_range = Column(String(50), nullable=True)
    funding_stage = Column(String(100), nullable=True)
    tech_stack_json = Column(JSON, nullable=True)
    hiring_keywords_json = Column(JSON, nullable=True)
    qualification_score = Column(Float, nullable=True)
    score_breakdown_json = Column(JSON, nullable=True)
    status = Column(
        SAEnum("pending", "validated", "rejected", name="company_status"),
        nullable=False,
        default="pending",
    )
    # Enrichment fields
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)  # serpapi_google / mock / manual
    rejection_reason = Column(Text, nullable=True)
    growth_rate = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    # Enhanced enrichment fields
    tech_stack_detected = Column(JSON, nullable=True)
    market_signals = Column(JSON, nullable=True)
    domain_age_days = Column(Integer, nullable=True)
    has_linkedin = Column(Boolean, nullable=False, default=False)
    linkedin_url = Column(String(500), nullable=True)
    hiring_signal_score = Column(Float, nullable=True)
    validation_details = Column(JSON, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="companies")
    contacts = relationship("Contact", back_populates="company")
    recommendations = relationship("Recommendation", back_populates="company")
