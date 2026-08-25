"""AI Service - Gemini API integration for clinical data extraction and summarization."""
import json
import logging
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

def _has_gemini() -> bool:
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and not GEMINI_API_KEY.startswith("your-"))

# Configure Gemini
if _has_gemini():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")

MODEL_NAME = "gemini-1.5-flash"


def _get_model():
    """Get a Gemini model instance."""
    return genai.GenerativeModel(MODEL_NAME)


def _safe_json_parse(text: str) -> Optional[dict]:
    """Safely parse JSON from Gemini response, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse Gemini response as JSON: {text[:200]}")
        return None


async def extract_clinical_info(patient_answer: str, question_key: str, pathway: str, language: str = "en") -> dict:
    """Extract structured clinical information from a patient's free-text answer.

    Uses Gemini to understand the answer and extract relevant clinical data fields.
    """
    if not _has_gemini():
        return {"raw_answer": patient_answer, "extracted_value": patient_answer}

    prompt = f"""You are a clinical information extraction system. Extract structured medical information from the patient's answer.

Context:
- Clinical pathway: {pathway}
- Question key: {question_key}
- Patient's language: {language}

Patient's answer: "{patient_answer}"

Extract the following as JSON:
{{
    "extracted_value": "the cleaned/normalized value for the question",
    "numeric_value": null or a number if applicable (e.g., severity score, temperature),
    "duration_days": null or estimated number of days if a duration is mentioned,
    "associated_symptoms": [],
    "additional_info": "any additional clinically relevant information from the answer",
    "confidence": 0.0 to 1.0
}}

Rules:
- If the patient mentions severity, extract it as a number 1-10
- If duration is mentioned, estimate in days
- Extract any symptoms mentioned even if not directly asked
- Be conservative - only extract what is clearly stated
- Return ONLY valid JSON, no other text"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = _safe_json_parse(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")

    # Fallback: return raw answer
    return {"extracted_value": patient_answer, "raw_answer": patient_answer, "confidence": 0.5}


async def detect_chief_complaint(text: str) -> dict:
    """Use Gemini to detect the chief complaint and suggest a clinical pathway."""
    if not _has_gemini():
        return {"chief_complaint": text, "suggested_pathway": "general"}

    prompt = f"""You are a clinical triage system. Analyze the patient's initial complaint and identify:
1. The chief complaint (standardized medical term)
2. The most appropriate clinical pathway

Patient says: "{text}"

Available pathways: chest_pain, fever, headache, abdominal_pain, cough_breathing, general

Return ONLY valid JSON:
{{
    "chief_complaint": "standardized complaint",
    "suggested_pathway": "pathway_id",
    "urgency": "low/medium/high",
    "initial_symptoms": ["symptom1", "symptom2"]
}}"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = _safe_json_parse(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"Gemini complaint detection failed: {e}")

    return {"chief_complaint": text, "suggested_pathway": "general", "urgency": "medium"}


async def generate_clinical_summary(patient_data: dict) -> dict:
    """Generate a structured clinical summary from all collected patient data."""
    if not _has_gemini():
        return _generate_fallback_summary(patient_data)

    prompt = f"""You are a clinical documentation system. Generate a structured clinical intake summary from the following patient data.

Patient Data:
{json.dumps(patient_data, indent=2, default=str)}

Generate a comprehensive clinical summary in this EXACT JSON format:
{{
    "patient_information": {{
        "name": "",
        "age": "",
        "gender": "",
        "blood_group": ""
    }},
    "chief_complaint": "primary reason for visit",
    "history_of_present_illness": "detailed narrative of the current problem",
    "past_medical_history": "relevant past medical conditions",
    "past_surgical_history": "relevant past surgeries",
    "current_medications": ["list of current medications"],
    "allergies": ["list of known allergies"],
    "family_history": "relevant family medical history",
    "personal_history": {{
        "smoking": "",
        "alcohol": "",
        "diet": "",
        "exercise": ""
    }},
    "review_of_systems": {{
        "cardiovascular": "",
        "respiratory": "",
        "gastrointestinal": "",
        "neurological": ""
    }},
    "relevant_investigations": "any lab reports or imaging mentioned",
    "red_flags": ["list of concerning findings"],
    "assessment": "clinical impression based on gathered information",
    "priority_level": "NORMAL/MEDIUM/HIGH"
}}

Rules:
- Use only information provided, do not fabricate data
- Mark missing information as "Not reported" or null
- Be concise but thorough
- Use standard medical terminology
- Return ONLY valid JSON"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = _safe_json_parse(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"Gemini summary generation failed: {e}")

    return _generate_fallback_summary(patient_data)


async def extract_document_info(ocr_text: str, document_category: str) -> dict:
    """Extract structured medical information from OCR-processed document text."""
    if not _has_gemini():
        return {"raw_text": ocr_text, "extraction_status": "gemini_unavailable"}

    prompt = f"""You are a medical document information extraction system. Extract structured clinical information from this OCR-processed medical document.

Document Category: {document_category}
OCR Text:
\"\"\"
{ocr_text[:4000]}
\"\"\"

Extract and return as JSON:
{{
    "document_type": "{document_category}",
    "document_date": "date if found or null",
    "hospital_name": "hospital name if found or null",
    "doctor_name": "doctor name if found or null",
    "diagnoses": ["list of diagnoses"],
    "medications": [
        {{
            "name": "medication name",
            "dosage": "dosage",
            "frequency": "how often",
            "duration": "for how long"
        }}
    ],
    "lab_values": [
        {{
            "test_name": "test name",
            "value": "result value",
            "unit": "unit",
            "reference_range": "normal range if available",
            "is_abnormal": true/false
        }}
    ],
    "procedures": ["list of procedures mentioned"],
    "important_notes": ["any clinically important notes"],
    "follow_up_date": "follow up date if mentioned or null"
}}

Rules:
- Only extract information clearly present in the text
- Mark unclear values with "unclear" instead of guessing
- Identify abnormal lab values when possible
- Return ONLY valid JSON"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = _safe_json_parse(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"Gemini document extraction failed: {e}")

    return {"raw_text": ocr_text, "extraction_status": "extraction_failed"}


def _generate_fallback_summary(patient_data: dict) -> dict:
    """Generate a basic summary without AI when Gemini is unavailable."""
    answers = patient_data.get("answers", {})
    return {
        "patient_information": {
            "name": patient_data.get("name", "Not available"),
            "age": patient_data.get("age", "Not available"),
            "gender": patient_data.get("gender", "Not available"),
        },
        "chief_complaint": patient_data.get("chief_complaint", "Not recorded"),
        "history_of_present_illness": f"Patient reported {patient_data.get('chief_complaint', 'symptoms')}. Duration: {answers.get('duration', 'Not specified')}. Severity: {answers.get('severity', 'Not specified')}.",
        "past_medical_history": answers.get("past_medical_history", "Not reported"),
        "current_medications": [answers.get("medications", "Not reported")],
        "allergies": [answers.get("allergies", "Not reported")],
        "family_history": answers.get("family_history", "Not reported"),
        "red_flags": patient_data.get("red_flags", []),
        "assessment": "AI summary unavailable. Manual review required.",
        "priority_level": "MEDIUM",
        "_note": "Generated without AI assistance. Gemini API key may not be configured.",
    }
