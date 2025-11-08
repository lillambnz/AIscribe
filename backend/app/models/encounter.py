"""Encounter model."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EncounterSource(str, enum.Enum):
    """Encounter source types."""
    ROOM = "room"  # In-room consultation
    PHONE = "phone"  # Telephone consultation
    UPLOAD = "upload"  # File upload


class EncounterStatus(str, enum.Enum):
    """Encounter status."""
    IN_PROGRESS = "in_progress"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class Encounter(Base):
    """Encounter (consultation session) model."""

    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_ref = Column(String(255), nullable=True, index=True)  # External patient ID
    source = Column(SQLEnum(EncounterSource), nullable=False, default=EncounterSource.ROOM)
    status = Column(SQLEnum(EncounterStatus), nullable=False, default=EncounterStatus.IN_PROGRESS)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    clinic = relationship("Clinic", back_populates="encounters")
    doctor = relationship("User", back_populates="encounters")
    audio_blobs = relationship("AudioBlob", back_populates="encounter", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="encounter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Encounter {self.id} - {self.status}>"
