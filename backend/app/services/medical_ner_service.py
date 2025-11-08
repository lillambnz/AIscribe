"""Medical Named Entity Recognition service."""
from typing import List, Dict, Optional
import re


class MedicalNERService:
    """Service for extracting medical entities from transcripts."""

    def __init__(self):
        """Initialize NER service."""
        # Common medication patterns (simplified - in production use spaCy medical models)
        self.medication_patterns = [
            # Generic patterns for medication mentions
            r'\b(metformin|aspirin|paracetamol|ibuprofen|amoxicillin|prednisolone)\b',
            r'\b(\w+cillin)\b',  # Antibiotics ending in cillin
            r'\b(\w+statin)\b',  # Statins
            r'\b(\w+pril)\b',  # ACE inhibitors
            r'\b(\w+sartan)\b',  # ARBs
        ]

        # Dosage patterns
        self.dosage_patterns = [
            r'\b(\d+\s*(?:mg|mcg|g|ml|units?))\b',
            r'\b(once|twice|three times|four times)\s+(?:daily|a day|per day)\b',
        ]

        # Allergy patterns
        self.allergy_patterns = [
            r'allergic to (\w+)',
            r'allergy to (\w+)',
            r'cannot take (\w+)',
        ]

        # Condition patterns
        self.condition_patterns = [
            r'\b(diabetes|hypertension|asthma|COPD|arthritis|depression|anxiety)\b',
            r'\b(type [12] diabetes)\b',
        ]

    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract medical entities from text.

        Args:
            text: Transcript text

        Returns:
            List of entity dictionaries
        """
        entities = []

        # Extract medications
        for pattern in self.medication_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": "med",
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.8,  # Rule-based confidence
                    "context": self._get_context(text, match.start(), match.end()),
                })

        # Extract dosages
        for pattern in self.dosage_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": "dose",
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.9,
                    "context": self._get_context(text, match.start(), match.end()),
                })

        # Extract allergies
        for pattern in self.allergy_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": "allergy",
                    "value": match.group(1),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.85,
                    "context": self._get_context(text, match.start(), match.end()),
                })

        # Extract conditions
        for pattern in self.condition_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": "condition",
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.75,
                    "context": self._get_context(text, match.start(), match.end()),
                })

        # Deduplicate entities
        entities = self._deduplicate_entities(entities)

        return entities

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for an entity."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities."""
        seen = set()
        unique_entities = []

        for entity in entities:
            key = (entity["type"], entity["value"].lower(), entity["start"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def load_medical_model(self):
        """
        Load advanced medical NER model (spaCy).
        Note: Requires spaCy medical models to be installed.
        """
        try:
            import spacy
            # Try to load medical model
            # In production, use: python -m spacy download en_core_sci_md
            # or en_ner_bc5cdr_md for biomedical NER
            self.nlp = spacy.load("en_core_web_sm")
            print("Loaded spaCy model for NER")
        except Exception as e:
            print(f"Could not load spaCy medical model: {e}")
            print("Using rule-based NER only")
            self.nlp = None

    def extract_with_spacy(self, text: str) -> List[Dict]:
        """
        Extract entities using spaCy (more accurate but slower).

        Args:
            text: Transcript text

        Returns:
            List of entity dictionaries
        """
        if self.nlp is None:
            return self.extract_entities(text)

        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            # Map spaCy entity types to our medical types
            entity_type = self._map_spacy_type(ent.label_)
            if entity_type:
                entities.append({
                    "type": entity_type,
                    "value": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 0.9,  # spaCy confidence
                    "context": self._get_context(text, ent.start_char, ent.end_char),
                })

        return entities

    def _map_spacy_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity label to our medical types."""
        mapping = {
            "CHEMICAL": "med",
            "DISEASE": "condition",
            "SYMPTOM": "symptom",
        }
        return mapping.get(spacy_label)


# Global service instance
medical_ner_service = MedicalNERService()
