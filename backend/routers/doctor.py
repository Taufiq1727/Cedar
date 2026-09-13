"""Doctor router - patient queue, review, summary approval, and profile."""
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
from services.auth_service import require_doctor, get_current_user
from services.timeline_service import generate_timeline
from services.doctor_assignment_service import get_doctor_profile_for_patient
from schemas.clinical import SummaryApproveRequest

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@router.get("/profile")
def get_doctor_profile(user: User = Depends(require_doctor), db: Session = Depends(get_db)):
    """Get the logged-in doctor's full profile."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(404, "Doctor profile not found")

    return {
        "doctor_id": doctor.id,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "hospital": doctor.hospital,
        "professional_id": doctor.professional_id,
        "specialization": doctor.specialization,
        "department": doctor.department,
        "years_of_experience": doctor.years_of_experience,
        "qualification": doctor.qualification,
        "bio": doctor.bio,
    }


from typing import Optional, List
from pydantic import BaseModel

class AssignDoctorRequest(BaseModel):
    doctor_id: Optional[str] = None

class PrescriptionRequest(BaseModel):
    patient_id: str
    session_id: Optional[str] = None
    diagnosis: str
    medications: list = []
    advice: Optional[str] = None
    investigations_ordered: Optional[str] = None
    follow_up_days: Optional[int] = None

class TimelineEventRequest(BaseModel):
    title: str
    event_type: str = "consultation"
    description: Optional[str] = None
    event_date: Optional[str] = None


@router.get("/patients")
def get_patient_queue(scope: str = "all", user: User = Depends(require_doctor), db: Session = Depends(get_db)):
    """Get the patient queue - supports scope='all', 'mine', or 'unassigned'."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()

    query = db.query(IntakeSession).filter(
        IntakeSession.status.in_(["completed", "in_progress", "reviewed", "approved"])
    )

    if scope == "mine" and doctor:
        query = query.filter(IntakeSession.assigned_doctor_id == doctor.id)
    elif scope == "unassigned":
        query = query.filter(IntakeSession.assigned_doctor_id.is_(None))
    # if scope == "all", shows all hospital sessions

    all_sessions = query.order_by(IntakeSession.created_at.desc()).all()

    # Deduplicate by patient: pick the most active/relevant session for each patient
    status_rank = {'approved': 0, 'completed': 1, 'reviewed': 2, 'in_progress': 3}
    patient_sessions = {}
    for s in all_sessions:
        if s.patient_id not in patient_sessions:
            patient_sessions[s.patient_id] = s
        else:
            existing = patient_sessions[s.patient_id]
            if status_rank.get(s.status, 9) < status_rank.get(existing.status, 9):
                patient_sessions[s.patient_id] = s

    sessions = list(patient_sessions.values())

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

        # Get assistant/nurse info
        assistant_name = None
        if s.assistant_id:
            ast = db.query(User).filter(User.id == s.assistant_id).first()
            if ast:
                assistant_name = ast.name

        # Get assigned doctor info
        assigned_doc = None
        if s.assigned_doctor_id:
            d_obj = db.query(Doctor).filter(Doctor.id == s.assigned_doctor_id).first()
            if d_obj:
                d_user = db.query(User).filter(User.id == d_obj.user_id).first()
                if d_user:
                    assigned_doc = d_user.name

        triage_lvl = s.triage_level or priority

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
            "triage_level": triage_lvl,
            "vitals": s.vitals or {},
            "nurse_notes": s.nurse_notes,
            "assistant_name": assistant_name,
            "intake_source": s.intake_source or "assistant_triage",
            "red_flag_count": len(red_flags),
            "high_priority_flags": len(high_flags),
            "has_summary": summary is not None,
            "summary_status": summary.status if summary else None,
            "assigned_doctor": assigned_doc,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        })

    # Sort by priority (HIGH first) then by creation time (newest first)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "NORMAL": 2}
    queue.sort(
        key=lambda x: (
            priority_order.get(x["priority"], 3),
            -(datetime.fromisoformat(x["created_at"]).timestamp() if x.get("created_at") else 0)
        )
    )

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

        # Get assistant/nurse info
        assistant_name = None
        if s.assistant_id:
            ast = db.query(User).filter(User.id == s.assistant_id).first()
            if ast:
                assistant_name = ast.name

        # Get assigned doctor info
        assigned_doc = None
        if s.assigned_doctor_id:
            d_obj = db.query(Doctor).filter(Doctor.id == s.assigned_doctor_id).first()
            if d_obj:
                d_user = db.query(User).filter(User.id == d_obj.user_id).first()
                if d_user:
                    assigned_doc = d_user.name

        sessions_data.append({
            "id": s.id,
            "chief_complaint": s.chief_complaint,
            "pathway": s.pathway,
            "status": s.status,
            "progress_pct": s.progress_pct,
            "language": s.language,
            "triage_level": s.triage_level or "ROUTINE",
            "vitals": s.vitals or {},
            "nurse_notes": s.nurse_notes,
            "assistant_name": assistant_name,
            "intake_source": s.intake_source or "assistant_triage",
            "structured_data": s.structured_data,
            "assigned_doctor": assigned_doc,
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

    # Get documents with file URLs
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
            "stored_filename": doc.filename,
            "file_type": doc.file_type,
            "category": doc.category,
            "file_url": f"/uploads/{doc.filename}",
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

    if req.status not in ("approved", "rejected", "reviewed"):
        raise HTTPException(400, "Status must be 'approved', 'reviewed', or 'rejected'")

    summary.status = req.status
    summary.doctor_id = doctor.id if doctor else None
    summary.doctor_notes = req.doctor_notes

    session = db.query(IntakeSession).filter(IntakeSession.id == summary.session_id).first()
    if session:
        if req.status == "approved":
            summary.approved_at = datetime.now(timezone.utc)
            session.status = "approved"
            # Sync any remaining draft sessions for this patient
            stale_sessions = db.query(IntakeSession).filter(
                IntakeSession.patient_id == session.patient_id,
                IntakeSession.id != session.id,
                IntakeSession.status == "in_progress"
            ).all()
            for os in stale_sessions:
                os.status = "approved"
        elif req.status in ("reviewed", "rejected"):
            session.status = "reviewed"

    if req.edits and summary.summary_json:
        # Merge doctor edits into summary
        from sqlalchemy.orm.attributes import flag_modified
        summary.summary_json = {**summary.summary_json, **req.edits}
        flag_modified(summary, "summary_json")
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


@router.get("/assigned/{session_id}")
def get_assigned_doctor(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the assigned doctor for a session. Accessible by the patient or any doctor."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    if not session.assigned_doctor_id:
        return {"assigned_doctor": None, "message": "No doctor assigned yet"}

    doctor_info = get_doctor_profile_for_patient(db, session.assigned_doctor_id)
    return {"assigned_doctor": doctor_info}


@router.post("/session/{session_id}/assign")
def assign_session_doctor(
    session_id: str,
    req: Optional[AssignDoctorRequest] = None,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Assign or claim a session for a doctor."""
    session = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    target_doctor_id = req.doctor_id if (req and req.doctor_id) else None
    if not target_doctor_id:
        doc = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if doc:
            target_doctor_id = doc.id

    session.assigned_doctor_id = target_doctor_id
    db.commit()

    assigned_name = "Unassigned"
    if target_doctor_id:
        d_obj = db.query(Doctor).filter(Doctor.id == target_doctor_id).first()
        if d_obj:
            u_obj = db.query(User).filter(User.id == d_obj.user_id).first()
            if u_obj:
                assigned_name = u_obj.name

    return {
        "message": f"Case assigned to Dr. {assigned_name}",
        "session_id": session_id,
        "assigned_doctor_id": target_doctor_id,
        "assigned_doctor_name": assigned_name,
    }


@router.post("/red-flag/{flag_id}/resolve")
def resolve_red_flag(
    flag_id: str,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Toggle or resolve a red flag alert."""
    flag = db.query(RedFlagAlert).filter(RedFlagAlert.id == flag_id).first()
    if not flag:
        raise HTTPException(404, "Red flag not found")

    flag.resolved = not flag.resolved
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    flag.resolved_by = doctor.id if flag.resolved and doctor else None
    flag.resolved_at = datetime.now(timezone.utc) if flag.resolved else None
    db.commit()

    return {
        "message": "Red flag resolved" if flag.resolved else "Red flag reactivated",
        "flag_id": flag_id,
        "resolved": flag.resolved,
    }


@router.post("/prescription")
def save_prescription(
    req: PrescriptionRequest,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Save doctor's clinical prescription, advice, and update medical records."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    doctor_name = user.name
    doc_spec = doctor.specialization if doctor else "General Medicine"

    # Find or update session
    session = None
    if req.session_id:
        session = db.query(IntakeSession).filter(IntakeSession.id == req.session_id).first()
    if not session:
        session = db.query(IntakeSession).filter(IntakeSession.patient_id == req.patient_id).order_by(IntakeSession.created_at.desc()).first()

    # Update summary if exists
    if session:
        from sqlalchemy.orm.attributes import flag_modified

        session.status = "reviewed"
        session.assigned_doctor_id = doctor.id if doctor else session.assigned_doctor_id
        session_data = dict(session.structured_data or {})
        session_data["latest_prescription"] = {
            "doctor_name": doctor_name,
            "specialization": doc_spec,
            "diagnosis": req.diagnosis,
            "medications": req.medications,
            "advice": req.advice,
            "investigations": req.investigations_ordered,
            "follow_up_days": req.follow_up_days,
            "prescribed_at": datetime.now(timezone.utc).isoformat(),
        }
        session.structured_data = session_data
        flag_modified(session, "structured_data")

        summary = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == session.id).first()
        if summary and summary.summary_json:
            s_json = dict(summary.summary_json)
            s_json["prescription"] = session_data["latest_prescription"]
            summary.summary_json = s_json
            flag_modified(summary, "summary_json")
            if summary.status == "generated":
                summary.status = "reviewed"

    # Add to timeline
    med_summary = ", ".join([f"{m.get('name', '')} ({m.get('dosage', '')})" for m in req.medications if isinstance(m, dict)])
    timeline_event = MedicalTimelineEvent(
        patient_id=req.patient_id,
        event_type="consultation",
        event_date=datetime.now(timezone.utc),
        title=f"Prescription & Advice - Dr. {doctor_name} ({doc_spec})",
        description=f"Diagnosis: {req.diagnosis}. Rx: {med_summary or 'See prescription'}. Advice: {req.advice or 'Routine follow-up'}.",
        source_type="doctor_review",
        source_id=session.id if session else None,
    )
    db.add(timeline_event)
    db.commit()

    return {
        "message": "Prescription successfully saved and added to patient medical record!",
        "doctor_name": doctor_name,
        "diagnosis": req.diagnosis,
        "medications": req.medications,
        "session_status": session.status if session else None,
    }


@router.post("/patient/{patient_id}/timeline")
def add_patient_timeline_event(
    patient_id: str,
    req: TimelineEventRequest,
    user: User = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Add a clinical timeline event for a patient."""
    evt_date = datetime.fromisoformat(req.event_date) if req.event_date else datetime.now(timezone.utc)
    evt = MedicalTimelineEvent(
        patient_id=patient_id,
        event_type=req.event_type,
        event_date=evt_date,
        title=req.title,
        description=req.description,
        source_type="manual",
    )
    db.add(evt)
    db.commit()
    return {"message": "Timeline event created successfully", "id": evt.id}

