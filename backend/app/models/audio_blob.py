"""Audio blob model."""
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AudioBlob(Base):
    """Audio blob storage reference model."""

    __tablename__ = "audio_blobs"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, index=True)
    uri = Column(String(1024), nullable=False)  # Storage URI (local path, S3 URL, etc.)
    duration_s = Column(Float, nullable=True)  # Duration in seconds
    file_size = Column(Integer, nullable=True)  # File size in bytes
    format = Column(String(50), nullable=True)  # wav, mp3, m4a, opus, etc.
    encrypted = Column(String(50), nullable=False, default="AES-256")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete for audit

    # Relationships
    encounter = relationship("Encounter", back_populates="audio_blobs")

    def __repr__(self):
        return f"<AudioBlob {self.id} - {self.duration_s}s>"
