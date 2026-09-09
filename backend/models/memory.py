import uuid

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SAEnum
from sqlalchemy.sql import func

from backend.database.base import Base


class Memory(Base):
    __tablename__ = "memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(
        SAEnum("company", "contact", "workflow", name="entity_type"),
        nullable=False,
    )
    entity_id = Column(String(36), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    embedding_id = Column(String(255), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
