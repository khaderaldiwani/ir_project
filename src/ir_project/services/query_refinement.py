from dataclasses import dataclass, field

from ir_project.services.text_processing import TextProcessor


DEFAULT_SYNONYMS = {
    "treatment": ["therapy", "medication", "medicine", "management"],
    "treat": ["therapy", "medication", "manage"],
    "symptoms": ["signs", "indications", "manifestations"],
    "symptom": ["sign", "indication"],
    "diabetes": ["diabetic", "glucose", "insulin"],
    "covid": ["coronavirus", "virus"],
    "coronavirus": ["covid", "viral", "infection"],
    "cancer": ["tumor", "oncology"],
    "medicine": ["medication", "drug", "therapy"],
    "doctor": ["physician", "clinician"],
}

SPELLING_CORRECTIONS = {
    "diabete": "diabetes",
    "diabetis": "diabetes",
    "corona": "coronavirus",
    "medecine": "medicine",
    "symptons": "symptoms",
    "treatement": "treatment",
}


@dataclass
class QueryRefinementService:
    processor: TextProcessor = field(default_factory=TextProcessor)
    max_synonyms_per_token: int = 3

    def refine(self, query: str) -> str:
        tokens = self.processor.tokenize(query)
        expanded: list[str] = []
        for token in tokens:
            corrected = SPELLING_CORRECTIONS.get(token, token)
            expanded.append(corrected)
            expanded.extend(DEFAULT_SYNONYMS.get(corrected, [])[: self.max_synonyms_per_token])
        if not expanded:
            return query
        return " ".join(expanded)
