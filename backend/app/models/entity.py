"""Entity model for medical NER."""
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EntityType(str, enum.Enum):
    """Medical entity types."""
    MEDICATION = "med"
    DOSAGE = "dose"
    ALLERGY = "allergy"
    CONDITION = "condition"
    PROCEDURE = "procedure"
    SYMPTOM = "symptom"
    LAB_TEST = "lab_test"
    VITAL_SIGN = "vital_sign"


class Entity(Base):
    """Medical entity extracted from transcript."""

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False, index=True)
    type = Column(SQLEnum(EntityType), nullable=False, index=True)
    value = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=True)
    start_char = Column(Integer, nullable=True)  # Character position in transcript
    end_char = Column(Integer, nullable=True)
    context = Column(String(1000), nullable=True)  # Surrounding text for context

    # Relationships
    transcript = relationship("Transcript", back_populates="entities")

    def __repr__(self):
        return f"<Entity {self.type}: {self.value}>"
