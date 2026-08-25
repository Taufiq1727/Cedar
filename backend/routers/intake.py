"""Intake router - clinical intake session management."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.intake import IntakeSession
from services.auth_service import require_patient
from services.intake_service import start_intake_session, process_answer, get_session_details
from schemas.intake import StartIntakeRequest, AnswerRequest

router = APIRouter(prefix="/intake", tags=["Clinical Intake"])


@router.post("/start")
async def start_session(
    req: StartIntakeRequest,
    request: Request,
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Start a new clinical intake session."""
    if not req.consent_given:
        raise HTTPException(400, "Consent must be given to start the intake")

    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    # Get client info for consent record
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = await start_intake_session(
        db, patient.id, req.language, req.consent_given, ip_address, user_agent
    )

    # Return first question prompt
    return {
        "session_id": session.id,
        "status": session.status,
        "language": session.language,
        "question_key": "chief_complaint",
        "question_text": _get_initial_prompt(req.language),
        "question_type": "text",
        "progress_pct": 0,
        "is_complete": False,
    }


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    req: AnswerRequest,
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Submit a patient answer and get the next question."""
    # Verify session belongs to patient
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()

    if not session:
        raise HTTPException(404, "Session not found")
    if session.patient_id != patient.id:
        raise HTTPException(403, "Access denied")
    if session.status == "completed":
        raise HTTPException(400, "This session is already completed")

    if not req.answer_text.strip():
        raise HTTPException(400, "Answer cannot be empty")

    result = await process_answer(
        db, session_id, req.answer_text.strip(),
        req.input_method, req.question_key,
    )

    return result


@router.get("/{session_id}")
def get_session(
    session_id: str,
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Get full intake session details."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()

    if not session:
        raise HTTPException(404, "Session not found")
    if session.patient_id != patient.id:
        raise HTTPException(403, "Access denied")

    return get_session_details(db, session_id)


@router.post("/{session_id}/complete")
async def complete_session(
    session_id: str,
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Manually mark an intake session as complete."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()

    if not session:
        raise HTTPException(404, "Session not found")
    if session.patient_id != patient.id:
        raise HTTPException(403, "Access denied")

    from datetime import datetime, timezone
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    session.progress_pct = 100
    db.commit()

    return {"message": "Session marked as complete", "session_id": session_id}


def _get_initial_prompt(language: str) -> str:
    """Get the initial question prompt in the selected language."""
    prompts = {
        "en": "Hello! I'm here to help collect your health information before your doctor's appointment. Please tell me your main health concern or problem.",
        "hi": "नमस्ते! मैं आपकी डॉक्टर की अपॉइंटमेंट से पहले आपकी स्वास्थ्य जानकारी एकत्र करने में मदद करने के लिए यहां हूं। कृपया अपनी मुख्य स्वास्थ्य समस्या बताएं।",
        "kn": "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ವೈದ್ಯರ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗೆ ಮುಂಚೆ ನಿಮ್ಮ ಆರೋಗ್ಯ ಮಾಹಿತಿಯನ್ನು ಸಂಗ್ರಹಿಸಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಮುಖ್ಯ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಯನ್ನು ಹೇಳಿ.",
    }
    return prompts.get(language, prompts["en"])
