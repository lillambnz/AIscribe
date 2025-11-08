"""Audit log model for compliance."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """Immutable audit log for compliance tracking."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for system actions
    action = Column(String(100), nullable=False, index=True)  # create, read, update, delete, export, etc.
    resource_type = Column(String(100), nullable=False, index=True)  # encounter, transcript, audio, etc.
    resource_id = Column(Integer, nullable=True, index=True)
    details = Column(JSON, nullable=True)  # Additional context
    ip_hash = Column(String(64), nullable=True)  # Hashed IP for privacy
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    data_left_au = Column(String(50), nullable=True)  # Tag if data left Australia

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type}>"
