"""WebSocket streaming endpoint for real-time transcription."""
import asyncio
import json
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.core.database import get_db
from app.core.security import verify_token
from app.models.encounter import Encounter
from app.models.transcript import Transcript

router = APIRouter()


class StreamingSession:
    """Manages a streaming transcription session."""

    def __init__(self, encounter_id: int, websocket: WebSocket):
        self.encounter_id = encounter_id
        self.websocket = websocket
        self.audio_buffer = []
        self.partial_text = ""
        self.stable_text = ""
        self.is_active = True

    async def process_audio_chunk(self, audio_data: bytes):
        """
        Process incoming audio chunk.

        In production, this would:
        1. Buffer audio chunks
        2. Send to streaming ASR (Azure Speech SDK)
        3. Send partial results back to client
        4. Store stable segments

        For MVP, we'll simulate streaming behavior.
        """
        # Append to buffer
        self.audio_buffer.append(audio_data)

        # Simulate partial transcription
        # In production, this would come from Azure Speech or streaming ASR
        chunk_length = len(audio_data)
        simulated_partial = f"[Processing {chunk_length} bytes of audio...]"

        # Send partial result
        await self.websocket.send_json({
            "type": "partial",
            "text": simulated_partial,
            "confidence": 0.7,
            "timestamp": len(self.audio_buffer) * 0.02,  # Simulate 20ms chunks
        })

    async def finalize_buffer(self, db: AsyncSession):
        """
        Finalize buffered audio and create transcript.

        This would normally:
        1. Combine audio chunks
        2. Run Whisper on the complete audio
        3. Store final transcript
        """
        if not self.audio_buffer:
            return

        # Simulate final transcription
        # In production, convert audio_buffer to audio file and run Whisper
        final_text = f"Final transcript from {len(self.audio_buffer)} audio chunks"

        # Create transcript record
        transcript = Transcript(
            encounter_id=self.encounter_id,
            engine="streaming_simulation",
            text=final_text,
            confidence_avg=0.85,
        )

        db.add(transcript)
        await db.commit()

        # Send final result
        await self.websocket.send_json({
            "type": "final",
            "text": final_text,
            "confidence": 0.85,
            "transcript_id": transcript.id,
        })


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    encounter_id: int = Query(...),
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time audio streaming.

    Protocol:
    Client -> Server:
        - Binary frames: PCM/Opus audio chunks (20ms recommended)
        - JSON: {"type": "control", "action": "stop"}

    Server -> Client:
        - JSON: {"type": "partial", "text": "...", "confidence": 0.8, "timestamp": 1.5}
        - JSON: {"type": "stable", "text": "...", "confidence": 0.9, "speaker": "doctor"}
        - JSON: {"type": "final", "text": "...", "transcript_id": 123}
        - JSON: {"type": "error", "message": "..."}
    """
    # Accept WebSocket connection
    await websocket.accept()

    # Verify token
    try:
        payload = verify_token(token)
        if payload.get("encounter_id") != encounter_id:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid token for this encounter"
            })
            await websocket.close(code=1008)
            return
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid authentication token"
        })
        await websocket.close(code=1008)
        return

    # Get database session
    from app.core.database import AsyncSessionLocal
    db = AsyncSessionLocal()

    try:
        # Verify encounter exists
        result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = result.scalar_one_or_none()

        if not encounter:
            await websocket.send_json({
                "type": "error",
                "message": "Encounter not found"
            })
            await websocket.close(code=1008)
            return

        # Create streaming session
        session = StreamingSession(encounter_id, websocket)

        # Send ready signal
        await websocket.send_json({
            "type": "ready",
            "encounter_id": encounter_id,
            "message": "Ready to receive audio"
        })

        # Main streaming loop
        while session.is_active:
            try:
                # Receive message
                data = await websocket.receive()

                # Handle binary audio data
                if "bytes" in data:
                    audio_chunk = data["bytes"]
                    await session.process_audio_chunk(audio_chunk)

                # Handle JSON control messages
                elif "text" in data:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")

                    if msg_type == "control":
                        action = message.get("action")
                        if action == "stop":
                            # Finalize session
                            await session.finalize_buffer(db)
                            await websocket.send_json({
                                "type": "stopped",
                                "message": "Session ended"
                            })
                            session.is_active = False

            except WebSocketDisconnect:
                print(f"WebSocket disconnected for encounter {encounter_id}")
                session.is_active = False
                break

            except Exception as e:
                print(f"Error in streaming: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    finally:
        await db.close()
        await websocket.close()


@router.post("/upload")
async def upload_audio_file(
    # This would handle file uploads for batch transcription
    # Implementation similar to streaming but for complete files
):
    """Upload audio file for batch transcription."""
    return {"message": "Upload endpoint - to be implemented"}
