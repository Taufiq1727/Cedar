"""Intake session and patient answer models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, ForeignKey
from database import Base


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    language = Column(String, default="en")
    status = Column(String, default="in_progress")  # in_progress, completed, reviewed, approved
    chief_complaint = Column(String, nullable=True)
    pathway = Column(String, nullable=True)  # chest_pain, fever, headache, etc.
    progress_pct = Column(Integer, default=0)
    assigned_doctor_id = Column(String, ForeignKey("doctors.id"), nullable=True, index=True)
    assistant_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    triage_level = Column(String, default="ROUTINE")  # EMERGENCY, URGENT, ROUTINE
    vitals = Column(JSON, nullable=True, default=dict)  # bp, pulse, spo2, temp, rbs
    nurse_notes = Column(Text, nullable=True)
    intake_source = Column(String, default="assistant_triage")  # assistant_triage, patient_self
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    structured_data = Column(JSON, nullable=True, default=dict)


class PatientAnswer(Base):
    __tablename__ = "patient_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=False, index=True)
    question_key = Column(String, nullable=False)
    question_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=False)
    input_method = Column(String, default="text")  # text or voice
    structured_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
