"""Encounter schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class EncounterSource(str, Enum):
    """Encounter source."""
    ROOM = "room"
    PHONE = "phone"
    UPLOAD = "upload"


class EncounterStatus(str, Enum):
    """Encounter status."""
    IN_PROGRESS = "in_progress"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class EncounterCreate(BaseModel):
    """Schema for creating an encounter."""
    patient_ref: Optional[str] = Field(None, description="External patient reference ID")
    source: EncounterSource = Field(EncounterSource.ROOM, description="Encounter source")


class EncounterResponse(BaseModel):
    """Schema for encounter response."""
    id: int
    clinic_id: int
    doctor_id: int
    patient_ref: Optional[str]
    source: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    ws_url: str = Field(..., description="WebSocket URL for streaming")
    auth_token: str = Field(..., description="Bearer token for WebSocket auth")

    class Config:
        from_attributes = True


class TranscriptSegment(BaseModel):
    """Transcript segment with timing."""
    start: float
    end: float
    text: str
    confidence: float
    speaker: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Schema for transcript response."""
    id: int
    encounter_id: int
    engine: str
    text: str
    confidence_avg: float
    segments: Optional[List[TranscriptSegment]]
    soap_notes: Optional[Dict]
    entities: Optional[List[Dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class FinalizeRequest(BaseModel):
    """Schema for finalizing an encounter."""
    run_diarization: bool = Field(True, description="Run speaker diarization")
    run_ner: bool = Field(True, description="Run medical NER")
    generate_soap: bool = Field(True, description="Generate SOAP notes")
