"""AI router - summary generation and FHIR export."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.intake import IntakeSession
from services.auth_service import get_current_user
from services.summary_service import generate_summary_for_session
from services.timeline_service import generate_timeline
from services.fhir_service import generate_fhir_bundle

router = APIRouter(prefix="/ai", tags=["AI Processing"])


@router.post("/generate-summary/{session_id}")
async def generate_summary(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI clinical summary for a session."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    # Access control
    if user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if not patient or patient.id != session.patient_id:
            raise HTTPException(403, "Access denied")

    result = await generate_summary_for_session(db, session_id)
    return result


@router.get("/timeline/{patient_id}")
def get_timeline(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the medical timeline for a patient."""
    if user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if not patient or patient.id != patient_id:
            raise HTTPException(403, "Access denied")

    timeline = generate_timeline(db, patient_id)
    return timeline


@router.get("/fhir/{patient_id}")
def get_fhir_bundle(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get FHIR-compatible bundle for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    patient_user = db.query(User).filter(User.id == patient.user_id).first()

    patient_data = {
        "id": patient.id,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
    }
    user_data = {
        "name": patient_user.name if patient_user else "",
        "email": patient_user.email if patient_user else "",
        "phone": patient_user.phone if patient_user else "",
    }

    bundle = generate_fhir_bundle(patient_data, user_data)
    return bundle


from pydantic import BaseModel

class GeminiKeyRequest(BaseModel):
    api_key: str

@router.post("/configure-key")
def configure_gemini_key(req: GeminiKeyRequest):
    """Dynamically set the Gemini API Key."""
    import os
    import google.generativeai as genai
    import services.ai_service as ais

    key = req.api_key.strip()
    if not key:
        raise HTTPException(400, "API key cannot be empty")

    os.environ["GEMINI_API_KEY"] = key
    ais.GEMINI_API_KEY = key
    try:
        genai.configure(api_key=key)
        return {"status": "configured", "has_gemini": True, "message": "Gemini API key linked successfully!"}
    except Exception as e:
        raise HTTPException(400, f"Failed to configure Gemini: {e}")

