"""Doctor router - patient queue, review, and summary approval."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.intake import IntakeSession, PatientAnswer
from models.clinical import ClinicalSummary, RedFlagAlert, MedicalTimelineEvent
from models.document import MedicalDocument, ExtractedDocumentData
from services.auth_service import require_doctor
from services.timeline_service import generate_timeline
from schemas.clinical import SummaryApproveRequest

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@router.get("/patients")
def get_patient_queue(user: User = Depends(require_doctor), db: Session = Depends(get_db)):
    """Get the patient queue - all sessions waiting for review."""
    # Get all completed or in-progress sessions
    sessions = db.query(IntakeSession).filter(
        IntakeSession.status.in_(["completed", "in_progress", "reviewed"])
    ).order_by(IntakeSession.created_at.desc()).all()

    queue = []
    for s in sessions:
        patient = db.query(Patient).filter(Patient.id == s.patient_id).first()
        patient_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None
        red_flags = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == s.id).all()
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == s.id).first()

        # Determine priority
        high_flags = [f for f in red_flags if f.severity == "HIGH"]
        medium_flags = [f for f in red_flags if f.severity == "MEDIUM"]
        priority = "HIGH" if high_flags else ("MEDIUM" if medium_flags else "NORMAL")

        queue.append({
            "session_id": s.id,
            "patient_id": s.patient_id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_age": patient.age if patient else None,
            "patient_gender": patient.gender if patient else None,
            "chief_complaint": s.chief_complaint,
            "pathway": s.pathway,
            "status": s.status,
            "progress_pct": s.progress_pct,
            "priority": priority,
            "red_flag_count": len(red_flags),
            "high_priority_flags": len(high_flags),
            "has_summary": summary is not None,
            "summary_status": summary.status if summary else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        })

    # Sort by priority (HIGH first) then by creation time
    priority_order = {"HIGH": 0, "MEDIUM": 1, "NORMAL": 2}
    queue.sort(key=lambda x: (priority_order.get(x["priority"], 3), x.get("created_at") or ""))

    return queue


@router.get("/patient/{patient_id}")
def get_patient_detail(
    patient_id: str,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Get full patient detail for doctor review."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    patient_user = db.query(User).filter(User.id == patient.user_id).first()

    # Get all sessions
    sessions = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient_id
    ).order_by(IntakeSession.created_at.desc()).all()

    sessions_data = []
    for s in sessions:
        answers = db.query(PatientAnswer).filter(PatientAnswer.session_id == s.id).order_by(PatientAnswer.created_at).all()
        red_flags = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == s.id).all()
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == s.id).first()

        sessions_data.append({
            "id": s.id,
            "chief_complaint": s.chief_complaint,
            "pathway": s.pathway,
            "status": s.status,
            "progress_pct": s.progress_pct,
            "language": s.language,
            "structured_data": s.structured_data,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "answers": [
                {
                    "question_key": a.question_key,
                    "question_text": a.question_text,
                    "answer_text": a.answer_text,
                    "input_method": a.input_method,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in answers
            ],
            "red_flags": [
                {
                    "id": f.id,
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description,
                    "resolved": f.resolved,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in red_flags
            ],
            "summary": {
                "id": summary.id,
                "summary_json": summary.summary_json,
                "summary_text": summary.summary_text,
                "status": summary.status,
                "doctor_notes": summary.doctor_notes,
                "approved_at": summary.approved_at.isoformat() if summary.approved_at else None,
                "created_at": summary.created_at.isoformat() if summary.created_at else None,
            } if summary else None,
        })

    # Get documents
    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id
    ).order_by(MedicalDocument.uploaded_at.desc()).all()

    docs_data = []
    for doc in documents:
        extracted = db.query(ExtractedDocumentData).filter(
            ExtractedDocumentData.document_id == doc.id
        ).first()
        docs_data.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "category": doc.category,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "extracted_data": extracted.extracted_json if extracted else None,
            "ocr_text": extracted.raw_text if extracted else None,
        })

    # Get timeline
    timeline = generate_timeline(db, patient_id)

    return {
        "patient": {
            "id": patient.id,
            "name": patient_user.name if patient_user else "Unknown",
            "email": patient_user.email if patient_user else None,
            "phone": patient_user.phone if patient_user else None,
            "age": patient.age,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
        },
        "sessions": sessions_data,
        "documents": docs_data,
        "timeline": timeline,
    }


@router.post("/summary/{summary_id}/approve")
def approve_summary(
    summary_id: str,
    req: SummaryApproveRequest,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Approve or reject a clinical summary."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.id == summary_id).first()

    if not summary:
        raise HTTPException(404, "Summary not found")

    if req.status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be 'approved' or 'rejected'")

    summary.status = req.status
    summary.doctor_id = doctor.id if doctor else None
    summary.doctor_notes = req.doctor_notes

    if req.status == "approved":
        summary.approved_at = datetime.now(timezone.utc)
        # Update session status
        session = db.query(IntakeSession).filter(IntakeSession.id == summary.session_id).first()
        if session:
            session.status = "approved"

    if req.edits and summary.summary_json:
        # Merge doctor edits into summary
        summary.summary_json = {**summary.summary_json, **req.edits}
        from services.summary_service import _json_to_text
        summary.summary_text = _json_to_text(summary.summary_json)

    db.commit()

    return {
        "message": f"Summary {req.status} successfully",
        "summary_id": summary_id,
        "status": summary.status,
        "approved_at": summary.approved_at.isoformat() if summary.approved_at else None,
    }


@router.get("/summary/{session_id}")
def get_session_summary(
    session_id: str,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Get the clinical summary for a session."""
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == session_id).first()
    if not summary:
        raise HTTPException(404, "Summary not found for this session")

    return {
        "id": summary.id,
        "session_id": summary.session_id,
        "patient_id": summary.patient_id,
        "summary_json": summary.summary_json,
        "summary_text": summary.summary_text,
        "status": summary.status,
        "doctor_id": summary.doctor_id,
        "doctor_notes": summary.doctor_notes,
        "approved_at": summary.approved_at.isoformat() if summary.approved_at else None,
        "created_at": summary.created_at.isoformat() if summary.created_at else None,
    }
