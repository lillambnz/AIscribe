"""Audit logging service for compliance."""
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Service for creating audit log entries."""

    @staticmethod
    def hash_ip(ip_address: str) -> str:
        """Hash IP address for privacy."""
        return hashlib.sha256(ip_address.encode()).hexdigest()

    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        data_left_au: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            db: Database session
            action: Action performed (create, read, update, delete, export, etc.)
            resource_type: Type of resource (encounter, transcript, audio, etc.)
            resource_id: ID of the resource
            actor_id: User ID who performed the action
            details: Additional context as JSON
            ip_address: IP address (will be hashed)
            data_left_au: Tag if data left Australia (e.g., "US-API-call")

        Returns:
            Created AuditLog entry
        """
        # Hash IP if provided
        ip_hash = None
        if ip_address:
            ip_hash = AuditService.hash_ip(ip_address)

        # Create audit log entry
        audit_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_hash=ip_hash,
            data_left_au=data_left_au,
        )

        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)

        return audit_entry

    @staticmethod
    async def log_encounter_created(
        db: AsyncSession,
        encounter_id: int,
        actor_id: int,
        ip_address: Optional[str] = None,
    ):
        """Log encounter creation."""
        return await AuditService.log_action(
            db=db,
            action="create",
            resource_type="encounter",
            resource_id=encounter_id,
            actor_id=actor_id,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_encounter_accessed(
        db: AsyncSession,
        encounter_id: int,
        actor_id: int,
        ip_address: Optional[str] = None,
    ):
        """Log encounter access."""
        return await AuditService.log_action(
            db=db,
            action="read",
            resource_type="encounter",
            resource_id=encounter_id,
            actor_id=actor_id,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_transcript_exported(
        db: AsyncSession,
        encounter_id: int,
        actor_id: int,
        export_format: str,
        ip_address: Optional[str] = None,
    ):
        """Log transcript export."""
        return await AuditService.log_action(
            db=db,
            action="export",
            resource_type="transcript",
            resource_id=encounter_id,
            actor_id=actor_id,
            details={"format": export_format},
            ip_address=ip_address,
        )

    @staticmethod
    async def log_audio_deleted(
        db: AsyncSession,
        audio_id: int,
        actor_id: int,
        reason: str = "retention_policy",
        ip_address: Optional[str] = None,
    ):
        """Log audio deletion."""
        return await AuditService.log_action(
            db=db,
            action="delete",
            resource_type="audio",
            resource_id=audio_id,
            actor_id=actor_id,
            details={"reason": reason},
            ip_address=ip_address,
        )

    @staticmethod
    async def log_external_api_call(
        db: AsyncSession,
        service: str,
        action: str,
        actor_id: Optional[int] = None,
        data_left_au: bool = True,
    ):
        """
        Log external API calls, especially those that send data outside Australia.

        Args:
            db: Database session
            service: External service name (e.g., "Azure-Speech-US")
            action: Action performed
            actor_id: User ID
            data_left_au: Whether data left Australia
        """
        return await AuditService.log_action(
            db=db,
            action=action,
            resource_type="external_api",
            actor_id=actor_id,
            details={"service": service},
            data_left_au=service if data_left_au else None,
        )


# Global service instance
audit_service = AuditService()
