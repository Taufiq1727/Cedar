"""Clinical Assistant / Nurse Triage Router.
Enables healthcare assistants/nurses to register patients, enter/dictate symptoms,
record vitals, trigger AI clinical triage parsing, and dispatch structured cases to doctors.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.intake import IntakeSession, PatientAnswer
from models.clinical import ClinicalHistory, ClinicalSummary, RedFlagAlert, MedicalTimelineEvent
from models.audit import AuditLog
from services.auth_service import get_current_user
from services.ai_service import extract_assistant_triage_notes, generate_clinical_summary
from clinical.red_flags import evaluate_red_flags

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Clinical Assistant & Nurse Triage"])


# Schemas
class QuickRegisterPatientRequest(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = "Unknown"
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    medical_record_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None


class AIExtractNotesRequest(BaseModel):
    notes: str = ""
    voice_transcript: str = ""
    vitals: Optional[Dict[str, Any]] = None
    language: str = "en"


class VitalsModel(BaseModel):
    bp: Optional[str] = None          # e.g., "130/85"
    pulse: Optional[str] = None       # bpm
    spo2: Optional[str] = None        # %
    temp: Optional[str] = None        # F
    rbs: Optional[str] = None         # mg/dL
    respiratory_rate: Optional[str] = None


class TriageIntakeSubmitRequest(BaseModel):
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_blood_group: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    language: str = "en"
    nurse_notes: str = ""
    voice_transcript: Optional[str] = ""
    vitals: Optional[Dict[str, Any]] = None
    chief_complaint: Optional[str] = None
    pathway: Optional[str] = "general"
    severity: Optional[int] = 5
    onset_duration: Optional[str] = None
    associated_symptoms: Optional[List[str]] = None
    past_medical_history: Optional[str] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    triage_level: Optional[str] = "ROUTINE"  # EMERGENCY, URGENT, ROUTINE
    structured_data: Optional[Dict[str, Any]] = None


@router.get("/stats")
def get_triage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get triage statistics for the clinical assistant dashboard."""
    total_triaged = db.query(IntakeSession).filter(
        IntakeSession.assistant_id == current_user.id
    ).count()

    emergency_count = db.query(IntakeSession).filter(
        IntakeSession.triage_level == "EMERGENCY"
    ).count()

    urgent_count = db.query(IntakeSession).filter(
        IntakeSession.triage_level == "URGENT"
    ).count()

    pending_doctor_count = db.query(IntakeSession).filter(
        IntakeSession.status.in_(["completed", "in_progress"])
    ).count()

    return {
        "total_triaged_by_user": total_triaged,
        "emergency_count": emergency_count,
        "urgent_count": urgent_count,
        "pending_doctor_review": pending_doctor_count,
        "assistant_name": current_user.name,
    }


@router.get("/doctors")
def get_available_doctors(
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List specialist doctors available for case assignment."""
    query = db.query(Doctor).join(User, Doctor.user_id == User.id).filter(User.is_active == True)
    if specialization and specialization.lower() != "all":
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))

    doctors = query.all()
    results = []
    for doc in doctors:
        user = db.query(User).filter(User.id == doc.user_id).first()
        if not user:
            continue
        
        # Count active queue
        pending_cases = db.query(IntakeSession).filter(
            IntakeSession.assigned_doctor_id == doc.id,
            IntakeSession.status == "completed"
        ).count()

        results.append({
            "id": doc.id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "specialization": doc.specialization or "General Medicine",
            "department": doc.department or doc.specialization or "OPD",
            "hospital": doc.hospital or "Central Hospital",
            "professional_id": doc.professional_id,
            "experience_years": getattr(doc, "years_of_experience", 0),
            "qualifications": getattr(doc, "qualification", ""),
            "pending_queue_count": pending_cases,
        })
    return results


@router.get("/patients/search")
def search_patients(
    q: Optional[str] = Query(None, description="Search query by name, phone, or MRN"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search registered patients or get recent patient records."""
    query = db.query(Patient).join(User, Patient.user_id == User.id)
    if q and q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(
            (User.name.ilike(search)) |
            (User.phone.ilike(search)) |
            (Patient.medical_record_number.ilike(search))
        )
    
    patients = query.limit(limit).all()
    results = []
    for p in patients:
        user = db.query(User).filter(User.id == p.user_id).first()
        if not user:
            continue
        results.append({
            "id": p.id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "age": p.age,
            "gender": p.gender,
            "blood_group": p.blood_group,
            "medical_record_number": p.medical_record_number or f"MRN-{p.id[:8].upper()}",
            "emergency_contact_name": p.emergency_contact_name,
            "emergency_contact_phone": p.emergency_contact_phone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    return results


@router.post("/patients/register")
def register_patient(
    req: QuickRegisterPatientRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rapid patient registration at the triage desk."""
    mrn = req.medical_record_number or f"MRN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    random_suffix = str(uuid.uuid4())[:6]
    email_slug = req.phone.strip().replace("+", "").replace("-", "") if (req.phone and req.phone.strip()) else random_suffix
    email = f"patient_{email_slug}_{random_suffix}@clinassistai.local"

    # Create new patient user
    new_user = User(
        email=email,
        password_hash="NURSE_REGISTERED_PATIENT",
        role="patient",
        name=req.name.strip(),
        phone=req.phone,
    )
    db.add(new_user)
    db.flush()

    patient = Patient(
        user_id=new_user.id,
        age=req.age,
        gender=req.gender or "Unknown",
        blood_group=req.blood_group,
        address=req.address,
        emergency_contact_name=req.emergency_contact_name,
        emergency_contact_phone=req.emergency_contact_phone,
        medical_record_number=mrn,
    )
    db.add(patient)
    db.flush()

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        action="nurse_register_patient",
        resource="patient",
        resource_id=patient.id,
    )
    db.add(audit)
    db.commit()

    return {
        "id": patient.id,
        "user_id": new_user.id,
        "name": new_user.name,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "phone": new_user.phone,
        "medical_record_number": patient.medical_record_number,
        "message": "Patient registered successfully at triage desk",
    }


@router.post("/ai-extract")
async def ai_extract_notes(
    req: AIExtractNotesRequest,
    current_user: User = Depends(get_current_user),
):
    """AI Scribe endpoint: Extracts clinical entities, red flags, and triage urgency from assistant notes and speech."""
    extracted = await extract_assistant_triage_notes(
        notes=req.notes,
        spoken_transcript=req.voice_transcript,
        vitals=req.vitals or {},
        language=req.language
    )
    return extracted


@router.post("/triage-intake")
async def submit_triage_intake(
    req: TriageIntakeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit completed triage case from Assistant/Nurse desk and dispatch to Doctor's queue."""
    patient = None
    if req.patient_id:
        patient = db.query(Patient).filter(Patient.id == req.patient_id).first()

    # If patient not found but patient_name is provided, auto-create patient
    if not patient:
        pat_name = (req.patient_name or "Walk-in Patient").strip()
        mrn = f"MRN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        random_suffix = str(uuid.uuid4())[:6]
        email_slug = req.patient_phone.strip().replace("+", "").replace("-", "") if (req.patient_phone and req.patient_phone.strip()) else random_suffix
        email = f"patient_{email_slug}_{random_suffix}@clinassistai.local"

        new_user = User(
            email=email,
            password_hash="NURSE_REGISTERED_PATIENT",
            role="patient",
            name=pat_name,
            phone=req.patient_phone,
        )
        db.add(new_user)
        db.flush()

        patient = Patient(
            user_id=new_user.id,
            age=req.patient_age,
            gender=req.patient_gender or "Unknown",
            blood_group=req.patient_blood_group,
            medical_record_number=mrn,
        )
        db.add(patient)
        db.flush()

    patient_user = db.query(User).filter(User.id == patient.user_id).first()
    patient_name = patient_user.name if patient_user else "Patient"

    chief_complaint = (req.chief_complaint or req.nurse_notes or "General Health Assessment").strip()
    if len(chief_complaint) > 300:
        chief_complaint = chief_complaint[:297] + "..."

    # Merge structured data
    structured = req.structured_data or {}
    structured.update({
        "chief_complaint": chief_complaint,
        "pathway": req.pathway or "general",
        "severity": req.severity or 5,
        "onset": req.onset_duration or "",
        "duration": req.onset_duration or "",
        "associated_symptoms": req.associated_symptoms or [],
        "past_medical_history": req.past_medical_history or "",
        "medications": req.current_medications or [],
        "allergies": req.allergies or [],
        "vitals": req.vitals or {},
        "nurse_notes": req.nurse_notes,
        "triaged_by": current_user.name,
        "triage_time": datetime.now(timezone.utc).isoformat(),
    })

    # Evaluate red flags using rule-based safety engine
    red_flag_alerts = evaluate_red_flags(structured, req.pathway or "general")

    # Determine triage priority
    triage_level = req.triage_level or "ROUTINE"
    if red_flag_alerts:
        has_high = any(r.get("severity") == "HIGH" for r in red_flag_alerts)
        if has_high:
            triage_level = "EMERGENCY"
        elif triage_level == "ROUTINE":
            triage_level = "URGENT"

    # Create IntakeSession
    session = IntakeSession(
        patient_id=patient.id,
        language=req.language,
        status="completed",
        chief_complaint=req.chief_complaint,
        pathway=req.pathway or "general",
        progress_pct=100,
        assigned_doctor_id=req.assigned_doctor_id,
        assistant_id=current_user.id,
        triage_level=triage_level,
        vitals=req.vitals or {},
        nurse_notes=req.nurse_notes,
        intake_source="assistant_triage",
        structured_data=structured,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()

    # Save answers / key clinical observations
    observations = [
        ("chief_complaint", "Chief Complaint", req.chief_complaint),
        ("onset_duration", "Onset & Duration", req.onset_duration or "Not specified"),
        ("severity", "Severity Rating (1-10)", str(req.severity or 5)),
        ("associated_symptoms", "Associated Symptoms", ", ".join(req.associated_symptoms) if req.associated_symptoms else "None reported"),
        ("past_history", "Past Medical History", req.past_medical_history or "None reported"),
        ("nurse_observations", "Nurse/Assistant Clinical Notes", req.nurse_notes or "No additional notes"),
    ]

    for key, q_text, ans_text in observations:
        if ans_text:
            ans = PatientAnswer(
                session_id=session.id,
                question_key=key,
                question_text=q_text,
                answer_text=ans_text,
                input_method="assistant_entry",
                structured_data={"recorded_by": current_user.name}
            )
            db.add(ans)

    # Save Red Flags to DB
    for rf in red_flag_alerts:
        alert = RedFlagAlert(
            session_id=session.id,
            patient_id=patient.id,
            rule_id=rf.get("rule_id", "TRIAGE_ALERT"),
            severity=rf.get("severity", "HIGH"),
            title=rf.get("title", "Clinical Alert"),
            description=rf.get("description", ""),
        )
        db.add(alert)

    # Generate Structured Clinical Summary
    summary_input = {
        "name": patient_name,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "chief_complaint": req.chief_complaint,
        "vitals": req.vitals or {},
        "triage_level": triage_level,
        "nurse_notes": req.nurse_notes,
        "answers": {k: v for k, _, v in observations},
        "red_flags": [rf.get("title") for rf in red_flag_alerts],
    }
    
    summary_data = await generate_clinical_summary(summary_input)

    # Create ClinicalHistory & ClinicalSummary
    history = ClinicalHistory(
        session_id=session.id,
        patient_id=patient.id,
        history_json=structured,
        pathway=req.pathway or "general",
        completeness=1.0,
    )
    db.add(history)

    summary = ClinicalSummary(
        session_id=session.id,
        patient_id=patient.id,
        summary_json=summary_data,
        summary_text=summary_data.get("history_of_present_illness", ""),
        status="generated",
        doctor_id=req.assigned_doctor_id,
    )
    db.add(summary)

    # Add Medical Timeline Event
    timeline_event = MedicalTimelineEvent(
        patient_id=patient.id,
        event_date=datetime.now(timezone.utc),
        event_type="consultation",
        title=f"OPD Triage: {req.chief_complaint[:50]}",
        description=f"Triaged by Nurse {current_user.name}. Priority: {triage_level}. Vitals: {req.vitals}.",
        source_type="assistant_triage",
        source_id=session.id,
        metadata_json={
            "triage_level": triage_level,
            "assigned_doctor_id": req.assigned_doctor_id,
            "red_flags_count": len(red_flag_alerts),
        }
    )
    db.add(timeline_event)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="triage_case_dispatched",
        resource="intake_session",
        resource_id=session.id,
    )
    db.add(audit)
    db.commit()

    assigned_doc_name = None
    if req.assigned_doctor_id:
        doc = db.query(Doctor).filter(Doctor.id == req.assigned_doctor_id).first()
        if doc:
            doc_u = db.query(User).filter(User.id == doc.user_id).first()
            if doc_u:
                assigned_doc_name = doc_u.name

    return {
        "session_id": session.id,
        "patient_id": patient.id,
        "patient_name": patient_name,
        "triage_level": triage_level,
        "red_flags": red_flag_alerts,
        "assigned_doctor_id": req.assigned_doctor_id,
        "assigned_doctor_name": assigned_doc_name,
        "summary": summary_data,
        "status": "dispatched",
        "message": f"Case successfully triaged and dispatched to Dr. {assigned_doc_name or 'Specialist Queue'}.",
    }


@router.get("/recent-triages")
def get_recent_triages(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recent triage cases handled at the desk."""
    sessions = (
        db.query(IntakeSession)
        .order_by(desc(IntakeSession.created_at))
        .limit(limit)
        .all()
    )

    results = []
    for s in sessions:
        patient = db.query(Patient).filter(Patient.id == s.patient_id).first()
        patient_name = "Unknown"
        age = None
        gender = None
        mrn = None
        if patient:
            p_user = db.query(User).filter(User.id == patient.user_id).first()
            if p_user:
                patient_name = p_user.name
            age = patient.age
            gender = patient.gender
            mrn = patient.medical_record_number

        doctor_name = "Unassigned"
        doctor_spec = "General"
        if s.assigned_doctor_id:
            doc = db.query(Doctor).filter(Doctor.id == s.assigned_doctor_id).first()
            if doc:
                d_user = db.query(User).filter(User.id == doc.user_id).first()
                if d_user:
                    doctor_name = d_user.name
                doctor_spec = doc.specialization or "Specialist"

        assistant_name = current_user.name
        if s.assistant_id:
            a_user = db.query(User).filter(User.id == s.assistant_id).first()
            if a_user:
                assistant_name = a_user.name

        rf_count = db.query(RedFlagAlert).filter(RedFlagAlert.session_id == s.id).count()

        results.append({
            "session_id": s.id,
            "patient_id": s.patient_id,
            "patient_name": patient_name,
            "age": age,
            "gender": gender,
            "mrn": mrn,
            "chief_complaint": s.chief_complaint,
            "pathway": s.pathway,
            "triage_level": s.triage_level or "ROUTINE",
            "vitals": s.vitals or {},
            "nurse_notes": s.nurse_notes,
            "assistant_name": assistant_name,
            "assigned_doctor_name": doctor_name,
            "assigned_doctor_spec": doctor_spec,
            "status": s.status,
            "red_flags_count": rf_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return results
