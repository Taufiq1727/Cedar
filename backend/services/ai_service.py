"""AI Service - Gemini API integration for clinical data extraction and summarization."""
import json
import logging
import warnings
from typing import Optional

# Suppress the FutureWarning from the deprecated google-generativeai package.
# It still functions correctly — we can migrate to google.genai once the package is available.
warnings.filterwarnings("ignore", category=FutureWarning, module="google.*")

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

MODEL_NAME = "gemini-3.6-flash"


def _get_model():
    """Get a Gemini model instance with automatic fallback."""
    for m in [MODEL_NAME, "gemini-3.5-flash", "gemini-flash-latest"]:
        try:
            return genai.GenerativeModel(m)
        except Exception:
            continue
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


async def extract_assistant_triage_notes(notes: str, spoken_transcript: str = "", vitals: dict = None, language: str = "en") -> dict:
    """Extract clinical triage entities from nurse/assistant notes, voice transcripts, and vitals."""
    combined_text = f"Nurse Notes: {notes}\nSpoken Dialogue/Audio Transcript: {spoken_transcript}".strip()
    if vitals:
        combined_text += f"\nRecorded Vitals: {json.dumps(vitals)}"

    if not _has_gemini():
        return _fallback_assistant_triage(notes, spoken_transcript, vitals)

    prompt = f"""You are a clinical AI triage assistant helping an Indian hospital outpatient/emergency desk.
Analyze the following nurse/assistant triage input (voice transcript or notes) and vitals:

Input:
\"\"\"
{combined_text}
\"\"\"

Extract and structure into standard clinical intake fields. Return ONLY valid JSON:
{{
    "chief_complaint": "Clear primary complaint (e.g. Severe chest pain with sweating)",
    "suggested_pathway": "chest_pain | fever | headache | abdominal_pain | cough_breathing | general",
    "onset_duration": "Duration (e.g. 3 hours, 4 days)",
    "severity": 1-10 integer,
    "hpi_narrative": "Cohesive medical summary of History of Present Illness",
    "associated_symptoms": ["list of symptoms like nausea, breathlessness, dizziness"],
    "past_medical_history": "Relevant chronic diseases (hypertension, diabetes, asthma, CAD, etc.) or 'None reported'",
    "current_medications": ["list of medications or empty"],
    "allergies": ["list of allergies or 'No known allergies'"],
    "vitals_assessment": "Short assessment of vitals (e.g., Hypertensive urgency, Tachycardia, Normal vitals)",
    "red_flags": ["List of critical warning signs or emergencies detected"],
    "triage_level": "EMERGENCY | URGENT | ROUTINE",
    "recommended_specialization": "Cardiology | Neurology | Pulmonology | Gastroenterology | Orthopedics | General Medicine | Dermatology | ENT | Pediatrics"
}}"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        result = _safe_json_parse(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"Assistant triage AI parsing failed: {e}")

    return _fallback_assistant_triage(notes, spoken_transcript, vitals)


import re

def _fallback_assistant_triage(notes: str, spoken_transcript: str = "", vitals: dict = None) -> dict:
    """Advanced rule-based clinical NLP triage extractor."""
    raw_text = (notes + " " + spoken_transcript).strip()
    text = raw_text.lower()
    vitals = vitals or {}

    # Extract Duration / Onset via regex
    duration_match = re.search(r'(\d+\s*(?:hours?|hrs?|days?|weeks?|months?|years?|mins?|minutes?)|since\s+[a-zA-Z0-9\s]+|for\s+[a-zA-Z0-9\s]+)', text)
    onset_duration = duration_match.group(0).strip() if duration_match else "Recent onset"

    # Extract Associated Symptoms
    symptom_keywords = {
        "sweating": "Diaphoresis / Sweating",
        "breathless": "Shortness of breath / Dyspnea",
        "dyspnea": "Dyspnea",
        "dizziness": "Dizziness / Vertigo",
        "giddiness": "Giddiness",
        "nausea": "Nausea",
        "vomit": "Vomiting",
        "fever": "Pyrexia / Fever",
        "chills": "Chills & Rigors",
        "cough": "Cough",
        "palpitation": "Palpitations",
        "tightness": "Chest tightness",
        "headache": "Cephalea / Headache",
        "weakness": "Generalized weakness",
        "diarrhea": "Diarrhea / Loose stools",
        "swelling": "Peripheral edema / Swelling",
        "radiat": "Radiation to left arm/jaw",
        "blur": "Visual blurring",
    }
    found_symptoms = [label for key, label in symptom_keywords.items() if key in text]

    # Extract Past Medical History
    pmh_keywords = {
        "hypertens": "Essential Hypertension",
        "high bp": "Hypertension (High BP)",
        "htn": "Hypertension",
        "diabet": "Type 2 Diabetes Mellitus",
        "sugar": "Diabetes Mellitus",
        "asthma": "Bronchial Asthma",
        "copd": "COPD",
        "thyroid": "Hypothyroidism / Thyroid Disorder",
        "kidney": "Chronic Kidney Disease",
        "ckd": "CKD",
        "heart disease": "Coronary Artery Disease",
        "cad": "CAD / Ischemic Heart Disease",
        "stroke": "Past CVA / Stroke",
        "cholesterol": "Dyslipidemia",
        "arthritis": "Osteoarthritis / Arthritis",
    }
    found_pmh = list(set([label for key, label in pmh_keywords.items() if key in text]))
    pmh_str = ", ".join(found_pmh) if found_pmh else "No chronic illness recorded"

    # Extract Medications
    med_keywords = [
        "amlodipine", "telmisartan", "losartan", "atenolol", "metformin",
        "glimepiride", "insulin", "aspirin", "atorvastatin", "clopidogrel",
        "paracetamol", "pantoprazole", "omeprazole", "cetirizine", "inhaler",
        "levothyroxine", "ecosprin", "azithromycin", "augmentin"
    ]
    found_meds = [m.capitalize() for m in med_keywords if m in text]

    # Extract Allergies
    allergy_keywords = ["penicillin", "sulfa", "aspirin", "nsaids", "dust", "pollen", "peanuts", "eggs"]
    found_allergies = [f"Allergic to {a.capitalize()}" for a in allergy_keywords if a in text]
    if not found_allergies:
        found_allergies = ["No known drug allergies reported"]

    # Pathway and Specialization Detection
    pathway = "general"
    rec_spec = "General Medicine"
    red_flags = []
    triage = "ROUTINE"

    if any(k in text for k in ["chest", "heart", "angina", "cardiac", "infarct"]):
        pathway = "chest_pain"
        rec_spec = "Cardiology"
        if any(k in text for k in ["sweat", "breathless", "radiat", "severe", "crushing", "arm", "jaw"]):
            red_flags.append("Suspected Acute Coronary Syndrome (Chest pain + Autonomic/Radiation signs)")
            triage = "EMERGENCY"
        else:
            triage = "URGENT"
    elif any(k in text for k in ["fever", "chills", "pyrexia", "temperature"]):
        pathway = "fever"
        rec_spec = "General Medicine"
        if any(k in text for k in ["high", "convulsion", "seizure", "delirium", "rash", "stiff"]):
            red_flags.append("High grade fever with systemic warning signs")
            triage = "URGENT"
    elif any(k in text for k in ["headache", "head pain", "migraine", "vision"]):
        pathway = "headache"
        rec_spec = "Neurology"
        if any(k in text for k in ["sudden", "worst", "thunderclap", "neck stiff", "weakness", "slur"]):
            red_flags.append("Possible neurological emergency (Severe acute headache)")
            triage = "EMERGENCY"
    elif any(k in text for k in ["cough", "breath", "wheez", "asthma", "oxygen", "sputum"]):
        pathway = "cough_breathing"
        rec_spec = "Pulmonology"
        if any(k in text for k in ["gasping", "stridor", "cyanosis", "blood", "hemoptysis"]):
            red_flags.append("Severe respiratory compromise / Hemoptysis")
            triage = "EMERGENCY"
        else:
            triage = "URGENT"
    elif any(k in text for k in ["stomach", "abdomen", "vomit", "loose motion", "diarrhea", "belly"]):
        pathway = "abdominal_pain"
        rec_spec = "Gastroenterology"
        if any(k in text for k in ["rigid", "blood", "black stool", "unbearable", "melena"]):
            red_flags.append("Acute surgical abdomen / Gastrointestinal hemorrhage signs")
            triage = "EMERGENCY"
    elif any(k in text for k in ["eye", "vision", "cataract", "retina", "blur"]):
        pathway = "general"
        rec_spec = "Ophthalmology"
    elif any(k in text for k in ["ear", "nose", "throat", "sinus", "tonsil"]):
        pathway = "general"
        rec_spec = "ENT"
    elif any(k in text for k in ["bone", "fracture", "joint", "knee", "back", "spine"]):
        pathway = "general"
        rec_spec = "Orthopedics"
    elif any(k in text for k in ["skin", "rash", "itching", "eczema", "psoriasis"]):
        pathway = "general"
        rec_spec = "Dermatology"

    # Check Vitals Abnormalities
    spo2 = vitals.get("spo2")
    if spo2:
        try:
            val = float(spo2)
            if val < 92:
                red_flags.append(f"Hypoxia Alert: SpO2 critically low at {val}% (Normal > 95%)")
                triage = "EMERGENCY"
        except Exception:
            pass

    bp = vitals.get("bp", "")
    if "/" in str(bp):
        try:
            sys_bp = float(str(bp).split("/")[0].strip())
            if sys_bp >= 170:
                red_flags.append(f"Severe Hypertension Alert: Systolic BP {sys_bp} mmHg")
                if triage != "EMERGENCY":
                    triage = "URGENT"
        except Exception:
            pass

    temp = vitals.get("temp")
    if temp:
        try:
            t_val = float(temp)
            if t_val >= 102:
                red_flags.append(f"High Grade Pyrexia Alert: Temperature {t_val}°F")
                if triage == "ROUTINE":
                    triage = "URGENT"
        except Exception:
            pass

    # Clean standardized complaint
    sentences = [s.strip() for s in raw_text.split(".") if s.strip()]
    chief_comp = sentences[0] if sentences else (raw_text or "General Health Assessment")
    if len(chief_comp) > 180:
        chief_comp = chief_comp[:177] + "..."

    severity_score = 8 if triage == "EMERGENCY" else (6 if triage == "URGENT" else 4)

    hpi = f"Patient presented at the OPD Triage Station with {chief_comp.lower()} ({onset_duration}). "
    if found_symptoms:
        hpi += f"Associated clinical features include {', '.join(found_symptoms).lower()}. "
    if found_pmh:
        hpi += f"Significant past medical history includes {', '.join(found_pmh)}. "
    if found_meds:
        hpi += f"Patient reports taking {', '.join(found_meds)}. "
    if vitals and any(vitals.values()):
        hpi += f"Recorded triage vitals: BP {vitals.get('bp', '—')}, Pulse {vitals.get('pulse', '—')} bpm, SpO2 {vitals.get('spo2', '—')}%, Temp {vitals.get('temp', '—')}°F."

    return {
        "chief_complaint": chief_comp,
        "suggested_pathway": pathway,
        "onset_duration": onset_duration,
        "severity": severity_score,
        "hpi_narrative": hpi,
        "associated_symptoms": found_symptoms,
        "past_medical_history": pmh_str,
        "current_medications": found_meds,
        "allergies": found_allergies,
        "vitals_assessment": "Abnormal vital signs detected" if red_flags else "Vitals stable",
        "red_flags": red_flags,
        "triage_level": triage,
        "recommended_specialization": rec_spec,
    }


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
