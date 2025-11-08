"""Clinic model."""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class Clinic(Base):
    """Clinic model for multi-tenant support."""

    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    data_residency = Column(String(50), nullable=False, default="AU")  # AU, US, EU, etc.
    retention_days = Column(Integer, nullable=False, default=90)
    kms_key_id = Column(String(255), nullable=False, default="default-key")
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="clinic")
    encounters = relationship("Encounter", back_populates="clinic")

    def __repr__(self):
        return f"<Clinic {self.name}>"
