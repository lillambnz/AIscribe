"""Whisper ASR service using faster-whisper."""
import os
from typing import Dict, List, Optional
from faster_whisper import WhisperModel
import numpy as np

from app.core.config import settings


class WhisperService:
    """Service for Whisper-based transcription."""

    def __init__(self):
        """Initialize Whisper model."""
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def _load_model(self):
        """Lazy load the Whisper model."""
        if self.model is None:
            print(f"Loading Whisper model: {self.model_name} on {self.device}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            print("Whisper model loaded successfully")

    def transcribe_audio(
        self,
        audio_path: str,
        language: str = "en",
        initial_prompt: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file
            language: Language code (default: "en")
            initial_prompt: Context prompt for medical domain

        Returns:
            Dictionary with transcript, segments, and metadata
        """
        self._load_model()

        # Default medical prompt if not provided
        if initial_prompt is None:
            initial_prompt = (
                "This is a medical consultation between a doctor and patient. "
                "The conversation may include medical terminology, medications, "
                "symptoms, and clinical observations."
            )

        # Transcribe with Whisper
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            initial_prompt=initial_prompt,
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            word_timestamps=True,
        )

        # Collect segments
        segment_list = []
        full_text = []
        confidence_scores = []

        for segment in segments:
            segment_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "confidence": segment.avg_logprob,  # Use log probability as confidence
                "words": [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability,
                    }
                    for word in (segment.words or [])
                ] if segment.words else [],
            }
            segment_list.append(segment_data)
            full_text.append(segment.text.strip())
            confidence_scores.append(segment.avg_logprob)

        # Calculate average confidence
        avg_confidence = float(np.mean(confidence_scores)) if confidence_scores else 0.0

        return {
            "text": " ".join(full_text),
            "segments": segment_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "confidence_avg": avg_confidence,
            "engine": "whisper",
        }

    def transcribe_numpy(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000,
        language: str = "en",
        initial_prompt: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe audio from numpy array.

        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate in Hz
            language: Language code
            initial_prompt: Context prompt

        Returns:
            Dictionary with transcript and metadata
        """
        self._load_model()

        if initial_prompt is None:
            initial_prompt = (
                "This is a medical consultation. Medical terminology expected."
            )

        # Transcribe
        segments, info = self.model.transcribe(
            audio_array,
            language=language,
            initial_prompt=initial_prompt,
            beam_size=5,
            vad_filter=True,
        )

        # Collect results
        segment_list = []
        full_text = []
        confidence_scores = []

        for segment in segments:
            segment_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "confidence": segment.avg_logprob,
            }
            segment_list.append(segment_data)
            full_text.append(segment.text.strip())
            confidence_scores.append(segment.avg_logprob)

        avg_confidence = float(np.mean(confidence_scores)) if confidence_scores else 0.0

        return {
            "text": " ".join(full_text),
            "segments": segment_list,
            "confidence_avg": avg_confidence,
            "engine": "whisper",
        }


# Global service instance
whisper_service = WhisperService()
