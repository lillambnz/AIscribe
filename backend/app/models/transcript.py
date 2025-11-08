"""Transcript model."""
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transcript(Base):
    """Transcript model."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    engine = Column(String(50), nullable=False)  # whisper, azure, streaming, etc.
    text = Column(Text, nullable=False)
    confidence_avg = Column(Float, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    segments = Column(JSON, nullable=True)  # Detailed segment data with timestamps
    soap_notes = Column(JSON, nullable=True)  # Structured SOAP format
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    encounter = relationship("Encounter", back_populates="transcripts")
    entities = relationship("Entity", back_populates="transcript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transcript {self.id} - {self.engine}>"
