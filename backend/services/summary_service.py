"""Summary Service - clinical summary generation and management."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.intake import IntakeSession, PatientAnswer
from models.clinical import ClinicalSummary, RedFlagAlert
from models.patient import Patient
from models.user import User
from models.document import MedicalDocument, ExtractedDocumentData
from services.ai_service import generate_clinical_summary

logger = logging.getLogger(__name__)


async def generate_summary_for_session(db: Session, session_id: str) -> dict:
    """Generate an AI clinical summary for a completed intake session."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")

    patient = db.query(Patient).filter(Patient.id == session.patient_id).first()
    user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

    # Gather all patient data
    answers = db.query(PatientAnswer).filter(PatientAnswer.session_id == session_id).all()
    red_flags = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == session_id).all()
    documents = db.query(MedicalDocument).filter(MedicalDocument.patient_id == session.patient_id).all()

    # Build patient data package for AI
    answers_dict = {}
    for a in answers:
        answers_dict[a.question_key] = a.answer_text

    # Get extracted document data
    doc_data = []
    for doc in documents:
        extracted = db.query(ExtractedDocumentData).filter(ExtractedDocumentData.document_id == doc.id).first()
        if extracted and extracted.extracted_json:
            doc_data.append({
                "category": doc.category,
                "filename": doc.original_filename,
                "extracted": extracted.extracted_json,
            })

    patient_data = {
        "name": user.name if user else "Unknown",
        "age": patient.age if patient else None,
        "gender": patient.gender if patient else None,
        "blood_group": patient.blood_group if patient else None,
        "chief_complaint": session.chief_complaint,
        "pathway": session.pathway,
        "answers": answers_dict,
        "structured_data": session.structured_data or {},
        "red_flags": [{"title": r.title, "severity": r.severity, "description": r.description} for r in red_flags],
        "documents": doc_data,
    }

    # Generate summary using AI
    summary_json = await generate_clinical_summary(patient_data)

    # Save or update summary
    existing = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == session_id).first()
    if existing:
        existing.summary_json = summary_json
        existing.summary_text = _json_to_text(summary_json)
        existing.status = "generated"
        existing.updated_at = datetime.now(timezone.utc)
        summary = existing
    else:
        summary = ClinicalSummary(
            session_id=session_id,
            patient_id=session.patient_id,
            summary_json=summary_json,
            summary_text=_json_to_text(summary_json),
            status="generated",
        )
        db.add(summary)

    db.commit()
    db.refresh(summary)

    return {
        "id": summary.id,
        "session_id": summary.session_id,
        "summary_json": summary.summary_json,
        "summary_text": summary.summary_text,
        "status": summary.status,
        "created_at": summary.created_at.isoformat() if summary.created_at else None,
    }


def _json_to_text(summary_json: dict) -> str:
    """Convert JSON summary to readable text format."""
    lines = []
    lines.append("=" * 60)
    lines.append("AI-GENERATED CLINICAL INTAKE SUMMARY")
    lines.append("Requires Clinician Verification")
    lines.append("=" * 60)

    if summary_json.get("patient_information"):
        pi = summary_json["patient_information"]
        lines.append(f"\nPATIENT: {pi.get('name', 'N/A')} | Age: {pi.get('age', 'N/A')} | Gender: {pi.get('gender', 'N/A')}")

    sections = [
        ("CHIEF COMPLAINT", "chief_complaint"),
        ("HISTORY OF PRESENT ILLNESS", "history_of_present_illness"),
        ("PAST MEDICAL HISTORY", "past_medical_history"),
        ("PAST SURGICAL HISTORY", "past_surgical_history"),
        ("FAMILY HISTORY", "family_history"),
        ("RELEVANT INVESTIGATIONS", "relevant_investigations"),
        ("ASSESSMENT", "assessment"),
    ]

    for title, key in sections:
        val = summary_json.get(key)
        if val and val != "Not reported":
            lines.append(f"\n{title}:")
            lines.append(f"  {val}")

    meds = summary_json.get("current_medications", [])
    if meds and meds != ["Not reported"]:
        lines.append("\nCURRENT MEDICATIONS:")
        for m in meds:
            lines.append(f"  • {m}")

    allergies = summary_json.get("allergies", [])
    if allergies and allergies != ["Not reported"]:
        lines.append("\nALLERGIES:")
        for a in allergies:
            lines.append(f"  • {a}")

    flags = summary_json.get("red_flags", [])
    if flags:
        lines.append("\n⚠️ RED FLAGS:")
        for f in flags:
            lines.append(f"  🔴 {f}")

    lines.append(f"\nPRIORITY: {summary_json.get('priority_level', 'NORMAL')}")
    lines.append("\n" + "=" * 60)

    return "\n".join(lines)
