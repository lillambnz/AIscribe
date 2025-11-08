"""User model."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles."""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    STAFF = "staff"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for SSO-only users
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STAFF)
    full_name = Column(String(255), nullable=True)
    sso_sub = Column(String(255), unique=True, nullable=True, index=True)  # SSO subject ID
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    clinic = relationship("Clinic", back_populates="users")
    encounters = relationship("Encounter", back_populates="doctor")

    def __repr__(self):
        return f"<User {self.email}>"
