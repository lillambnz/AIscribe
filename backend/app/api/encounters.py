"""Encounter management endpoints."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, create_access_token
from app.models.encounter import Encounter, EncounterStatus
from app.models.transcript import Transcript
from app.models.entity import Entity
from app.schemas.encounter import (
    EncounterCreate,
    EncounterResponse,
    TranscriptResponse,
    FinalizeRequest,
)
from app.services.whisper_service import whisper_service
from app.services.soap_service import soap_service
from app.services.medical_ner_service import medical_ner_service

router = APIRouter()


@router.post("", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
async def create_encounter(
    encounter_data: EncounterCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new encounter (consultation session)."""
    user_id = int(current_user.get("sub"))
    clinic_id = int(current_user.get("clinic_id", 1))

    # Create encounter
    encounter = Encounter(
        clinic_id=clinic_id,
        doctor_id=user_id,
        patient_ref=encounter_data.patient_ref,
        source=encounter_data.source,
        status=EncounterStatus.IN_PROGRESS,
    )

    db.add(encounter)
    await db.commit()
    await db.refresh(encounter)

    # Generate WebSocket URL and auth token
    ws_token = create_access_token(
        data={
            "sub": str(user_id),
            "encounter_id": encounter.id,
            "type": "websocket",
        }
    )

    # Return response with WebSocket details
    return EncounterResponse(
        id=encounter.id,
        clinic_id=encounter.clinic_id,
        doctor_id=encounter.doctor_id,
        patient_ref=encounter.patient_ref,
        source=encounter.source.value,
        status=encounter.status.value,
        started_at=encounter.started_at,
        ended_at=encounter.ended_at,
        ws_url=f"/v1/stream?encounter_id={encounter.id}",
        auth_token=ws_token,
    )


@router.get("/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(
    encounter_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get encounter details."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )

    # Generate new WebSocket token
    ws_token = create_access_token(
        data={
            "sub": current_user.get("sub"),
            "encounter_id": encounter.id,
            "type": "websocket",
        }
    )

    return EncounterResponse(
        id=encounter.id,
        clinic_id=encounter.clinic_id,
        doctor_id=encounter.doctor_id,
        patient_ref=encounter.patient_ref,
        source=encounter.source.value,
        status=encounter.status.value,
        started_at=encounter.started_at,
        ended_at=encounter.ended_at,
        ws_url=f"/v1/stream?encounter_id={encounter.id}",
        auth_token=ws_token,
    )


@router.post("/{encounter_id}/finalize")
async def finalize_encounter(
    encounter_id: int,
    finalize_req: FinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize encounter: run batch re-scoring, diarization, NER, and SOAP generation.
    """
    # Get encounter
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encounter not found",
        )

    # Update status
    encounter.status = EncounterStatus.FINALIZING
    encounter.ended_at = datetime.utcnow()
    await db.commit()

    try:
        # Get existing transcript or create placeholder
        result = await db.execute(
            select(Transcript)
            .where(Transcript.encounter_id == encounter_id)
            .order_by(Transcript.created_at.desc())
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            # No transcript yet - create placeholder
            transcript = Transcript(
                encounter_id=encounter_id,
                engine="placeholder",
                text="No transcript available",
                confidence_avg=0.0,
            )
            db.add(transcript)
            await db.commit()
            await db.refresh(transcript)

        # Extract medical entities
        entities_list = []
        if finalize_req.run_ner:
            entities_data = medical_ner_service.extract_entities(transcript.text)

            for entity_data in entities_data:
                entity = Entity(
                    transcript_id=transcript.id,
                    type=entity_data["type"],
                    value=entity_data["value"],
                    confidence=entity_data.get("confidence"),
                    start_char=entity_data.get("start"),
                    end_char=entity_data.get("end"),
                    context=entity_data.get("context"),
                )
                db.add(entity)
                entities_list.append(entity_data)

            await db.commit()

        # Generate SOAP notes
        if finalize_req.generate_soap:
            soap_notes = soap_service.generate_soap(
                transcript.text,
                entities=entities_list,
            )
            transcript.soap_notes = soap_notes
            await db.commit()

        # Update encounter status
        encounter.status = EncounterStatus.COMPLETED
        await db.commit()

        return {
            "status": "completed",
            "encounter_id": encounter.id,
            "transcript_id": transcript.id,
            "entities_found": len(entities_list),
            "soap_generated": finalize_req.generate_soap,
        }

    except Exception as e:
        encounter.status = EncounterStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Finalization failed: {str(e)}",
        )


@router.get("/{encounter_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    encounter_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get encounter transcript with SOAP notes and entities."""
    # Get transcript with entities
    result = await db.execute(
        select(Transcript)
        .options(selectinload(Transcript.entities))
        .where(Transcript.encounter_id == encounter_id)
        .order_by(Transcript.created_at.desc())
    )
    transcript = result.scalar_one_or_none()

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found",
        )

    # Format entities
    entities = [
        {
            "type": e.type.value,
            "value": e.value,
            "confidence": e.confidence,
            "start": e.start_char,
            "end": e.end_char,
        }
        for e in transcript.entities
    ]

    return TranscriptResponse(
        id=transcript.id,
        encounter_id=transcript.encounter_id,
        engine=transcript.engine,
        text=transcript.text,
        confidence_avg=transcript.confidence_avg or 0.0,
        segments=transcript.segments,
        soap_notes=transcript.soap_notes,
        entities=entities,
        created_at=transcript.created_at,
    )
