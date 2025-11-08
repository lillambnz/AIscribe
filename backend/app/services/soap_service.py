"""SOAP note generation service."""
from typing import Dict, List, Optional
import re


class SOAPService:
    """Service for generating SOAP notes from transcripts."""

    def __init__(self):
        """Initialize SOAP service."""
        # Keywords for section detection
        self.subjective_keywords = [
            "complains", "reports", "feels", "experiencing", "symptoms",
            "pain", "discomfort", "noticed", "started", "history"
        ]
        self.objective_keywords = [
            "examination", "vitals", "temperature", "blood pressure", "pulse",
            "inspection", "palpation", "auscultation", "findings", "observed"
        ]
        self.assessment_keywords = [
            "diagnosis", "differential", "likely", "assessment", "impression",
            "conclusion", "ruled out", "suspected"
        ]
        self.plan_keywords = [
            "plan", "treatment", "prescribe", "medication", "follow-up",
            "referral", "return", "advised", "recommended", "order"
        ]

    def generate_soap(
        self,
        transcript: str,
        entities: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Generate SOAP notes from transcript.

        Args:
            transcript: Full transcript text
            entities: List of extracted medical entities

        Returns:
            Dictionary with SOAP sections
        """
        # Split transcript into sentences
        sentences = self._split_sentences(transcript)

        # Classify sentences into SOAP sections
        soap = {
            "subjective": [],
            "objective": [],
            "assessment": [],
            "plan": [],
            "unclassified": [],
        }

        for sentence in sentences:
            section = self._classify_sentence(sentence)
            soap[section].append(sentence)

        # Format sections
        formatted_soap = {
            "S": self._format_section(soap["subjective"], "Subjective"),
            "O": self._format_section(soap["objective"], "Objective"),
            "A": self._format_section(soap["assessment"], "Assessment"),
            "P": self._format_section(soap["plan"], "Plan"),
        }

        # Add entity summary if available
        if entities:
            formatted_soap["entities_summary"] = self._summarize_entities(entities)

        return formatted_soap

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _classify_sentence(self, sentence: str) -> str:
        """Classify sentence into SOAP category."""
        sentence_lower = sentence.lower()

        # Score each category
        scores = {
            "subjective": sum(1 for kw in self.subjective_keywords if kw in sentence_lower),
            "objective": sum(1 for kw in self.objective_keywords if kw in sentence_lower),
            "assessment": sum(1 for kw in self.assessment_keywords if kw in sentence_lower),
            "plan": sum(1 for kw in self.plan_keywords if kw in sentence_lower),
        }

        # Find category with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "unclassified"

    def _format_section(self, sentences: List[str], title: str) -> str:
        """Format a SOAP section."""
        if not sentences:
            return f"{title}: [No information recorded]"

        content = " ".join(sentences)
        return f"{title}:\n{content}"

    def _summarize_entities(self, entities: List[Dict]) -> Dict[str, List[str]]:
        """Summarize extracted entities by type."""
        summary = {}
        for entity in entities:
            entity_type = entity.get("type", "unknown")
            value = entity.get("value", "")
            if entity_type not in summary:
                summary[entity_type] = []
            if value not in summary[entity_type]:
                summary[entity_type].append(value)

        return summary

    def generate_letter(
        self,
        soap: Dict,
        patient_name: str = "Patient",
        doctor_name: str = "Doctor",
        date: str = "",
    ) -> str:
        """
        Generate a medical letter from SOAP notes.

        Args:
            soap: SOAP notes dictionary
            patient_name: Patient name
            doctor_name: Doctor name
            date: Consultation date

        Returns:
            Formatted medical letter
        """
        letter = f"""
MEDICAL CONSULTATION LETTER

Date: {date}
Patient: {patient_name}
Doctor: {doctor_name}

---

{soap.get('S', '')}

{soap.get('O', '')}

{soap.get('A', '')}

{soap.get('P', '')}

---

This is a computer-generated draft. Please review and sign off before finalizing.
"""
        return letter.strip()


# Global service instance
soap_service = SOAPService()
