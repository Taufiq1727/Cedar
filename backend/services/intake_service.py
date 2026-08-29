"""Intake service - manages the clinical intake workflow."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.intake import IntakeSession, PatientAnswer
from models.clinical import ClinicalHistory, RedFlagAlert
from models.consent import ConsentRecord
from clinical.pathways import detect_pathway, get_next_question, calculate_progress, get_pathway
from clinical.red_flags import evaluate_red_flags
from services.ai_service import extract_clinical_info, detect_chief_complaint

logger = logging.getLogger(__name__)


async def start_intake_session(
    db: Session, patient_id: str, language: str, consent_given: bool,
    ip_address: str = None, user_agent: str = None
) -> IntakeSession:
    """Create a new intake session with consent record."""
    session = IntakeSession(
        patient_id=patient_id,
        language=language,
        status="in_progress",
        structured_data={},
    )
    db.add(session)
    db.flush()

    # Record consent
    consent = ConsentRecord(
        patient_id=patient_id,
        session_id=session.id,
        consent_given=consent_given,
        consent_type="clinical_intake",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(consent)
    db.commit()
    db.refresh(session)
    return session


async def process_answer(
    db: Session, session_id: str, answer_text: str,
    input_method: str = "text", question_key: str = None
) -> dict:
    """Process a patient's answer, extract information, and determine next question."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")

    structured_data = session.structured_data or {}

    # First answer - detect chief complaint and pathway
    if not session.chief_complaint:
        complaint_info = await detect_chief_complaint(answer_text)
        from clinical.pathways import detect_pathway as detect_pw
        pathway = detect_pw(answer_text)
        if complaint_info.get("suggested_pathway") and complaint_info["suggested_pathway"] != "general":
            pathway = complaint_info["suggested_pathway"]

        session.chief_complaint = complaint_info.get("chief_complaint", answer_text)
        session.pathway = pathway
        structured_data["chief_complaint"] = session.chief_complaint

        if complaint_info.get("initial_symptoms"):
            structured_data["initial_symptoms"] = complaint_info["initial_symptoms"]

        # Auto-assign specialist doctor based on chief complaint
        try:
            from services.doctor_assignment_service import assign_doctor_by_complaint
            assigned_id = assign_doctor_by_complaint(db, session.chief_complaint)
            if assigned_id:
                session.assigned_doctor_id = assigned_id
                logger.info(f"Auto-assigned doctor {assigned_id} for session {session_id}")
        except Exception as e:
            logger.warning(f"Doctor assignment failed: {e}")

        q_key = "chief_complaint"
    else:
        q_key = question_key or "unknown"

    # Extract structured info from answer using AI
    extracted = await extract_clinical_info(
        answer_text, q_key, session.pathway or "general", session.language
    )

    # Save the answer
    answer = PatientAnswer(
        session_id=session_id,
        question_key=q_key,
        question_text=q_key,
        answer_text=answer_text,
        input_method=input_method,
        structured_data=extracted,
    )
    db.add(answer)

    # Update structured data
    extracted_value = extracted.get("extracted_value", answer_text)
    structured_data[q_key] = extracted_value

    # If numeric value extracted (e.g., severity), store it
    if extracted.get("numeric_value") is not None:
        structured_data[q_key] = extracted["numeric_value"]

    # Capture any associated symptoms mentioned
    if extracted.get("associated_symptoms"):
        existing = structured_data.get("associated_symptoms", [])
        structured_data["associated_symptoms"] = list(set(existing + extracted["associated_symptoms"]))

    session.structured_data = structured_data

    # Get answered keys
    answered_keys = [a.question_key for a in db.query(PatientAnswer).filter(PatientAnswer.session_id == session_id).all()]
    if q_key not in answered_keys:
        answered_keys.append(q_key)

    # Calculate progress
    progress = calculate_progress(session.pathway or "general", answered_keys)
    session.progress_pct = progress

    # Evaluate red flags
    red_flags = evaluate_red_flags(structured_data, session.pathway or "general")

    # Save new red flags
    new_flags = []
    existing_rule_ids = [r.rule_id for r in db.query(RedFlagAlert).filter(RedFlagAlert.session_id == session_id).all()]
    for flag in red_flags:
        if flag["rule_id"] not in existing_rule_ids:
            alert = RedFlagAlert(
                session_id=session_id,
                patient_id=session.patient_id,
                rule_id=flag["rule_id"],
                severity=flag["severity"],
                title=flag["title"],
                description=flag["description"],
            )
            db.add(alert)
            new_flags.append(flag)

    # Get next question
    lang_code = {"en": "en", "hi": "hi", "kn": "kn"}.get(session.language, "en")
    next_q = get_next_question(session.pathway or "general", answered_keys, lang_code)

    is_complete = next_q is None
    if is_complete:
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.progress_pct = 100

        # Create/update clinical history
        _update_clinical_history(db, session)

    # Force update of JSON column
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "structured_data")

    db.commit()
    db.refresh(session)

    response = {
        "session_id": session_id,
        "progress_pct": session.progress_pct,
        "extracted_data": extracted,
        "red_flags": red_flags,
        "new_red_flags": new_flags,
        "is_complete": is_complete,
        "pathway": session.pathway,
        "chief_complaint": session.chief_complaint,
    }

    if next_q:
        response.update(next_q)
    else:
        response["question_key"] = "complete"
        response["question_text"] = "Thank you! Your clinical intake is complete. The doctor will review your information shortly."

    return response


def _update_clinical_history(db: Session, session: IntakeSession):
    """Create or update the clinical history record for this session."""
    existing = db.query(ClinicalHistory).filter(ClinicalHistory.session_id == session.id).first()
    if existing:
        existing.history_json = session.structured_data
        existing.completeness = session.progress_pct / 100.0
    else:
        history = ClinicalHistory(
            session_id=session.id,
            patient_id=session.patient_id,
            history_json=session.structured_data,
            pathway=session.pathway,
            completeness=session.progress_pct / 100.0,
        )
        db.add(history)


def get_session_details(db: Session, session_id: str) -> dict:
    """Get full session details including answers and red flags."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        return None

    answers = db.query(PatientAnswer).filter(PatientAnswer.session_id == session_id).order_by(PatientAnswer.created_at).all()
    red_flags = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == session_id).all()

    return {
        "id": session.id,
        "patient_id": session.patient_id,
        "language": session.language,
        "status": session.status,
        "chief_complaint": session.chief_complaint,
        "pathway": session.pathway,
        "progress_pct": session.progress_pct,
        "structured_data": session.structured_data,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "answers": [
            {
                "question_key": a.question_key,
                "question_text": a.question_text,
                "answer_text": a.answer_text,
                "input_method": a.input_method,
                "structured_data": a.structured_data,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in answers
        ],
        "red_flags": [
            {
                "id": r.id,
                "rule_id": r.rule_id,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "resolved": r.resolved,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in red_flags
        ],
    }
