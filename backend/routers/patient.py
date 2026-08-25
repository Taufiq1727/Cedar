"""Patient router - patient profile and session management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.intake import IntakeSession
from models.clinical import ClinicalSummary, RedFlagAlert
from models.document import MedicalDocument
from services.auth_service import get_current_user, require_patient
from schemas.patient import PatientUpdateRequest

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/me")
def get_my_profile(user: User = Depends(require_patient), db: Session = Depends(get_db)):
    """Get patient profile."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    return {
        "id": patient.id,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "address": patient.address,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
    }


@router.put("/me")
def update_profile(
    updates: PatientUpdateRequest,
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Update patient profile."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "phone":
            user.phone = value
        elif hasattr(patient, field):
            setattr(patient, field, value)

    db.commit()
    return {"message": "Profile updated successfully"}


@router.get("/me/sessions")
def get_my_sessions(user: User = Depends(require_patient), db: Session = Depends(get_db)):
    """Get all intake sessions for the current patient."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    sessions = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient.id
    ).order_by(IntakeSession.created_at.desc()).all()

    result = []
    for s in sessions:
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.session_id == s.id).first()
        flags = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == s.id).count()

        result.append({
            "id": s.id,
            "chief_complaint": s.chief_complaint,
            "pathway": s.pathway,
            "status": s.status,
            "progress_pct": s.progress_pct,
            "language": s.language,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "has_summary": summary is not None,
            "summary_status": summary.status if summary else None,
            "has_red_flags": flags > 0,
            "red_flag_count": flags,
        })

    return result


@router.get("/me/documents")
def get_my_documents(user: User = Depends(require_patient), db: Session = Depends(get_db)):
    """Get all uploaded documents for the current patient."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient.id
    ).order_by(MedicalDocument.uploaded_at.desc()).all()

    return [
        {
            "id": d.id,
            "filename": d.original_filename,
            "file_type": d.file_type,
            "category": d.category,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in documents
    ]
