"""Clinical history, summary, red flag, and timeline models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float, ForeignKey
from database import Base


class ClinicalHistory(Base):
    __tablename__ = "clinical_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=False, unique=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    history_json = Column(JSON, nullable=True)
    pathway = Column(String, nullable=True)
    completeness = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ClinicalSummary(Base):
    __tablename__ = "clinical_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=False, unique=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    summary_json = Column(JSON, nullable=True)
    summary_text = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, generated, approved, rejected
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RedFlagAlert(Base):
    __tablename__ = "red_flag_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    rule_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String, ForeignKey("doctors.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MedicalTimelineEvent(Base):
    __tablename__ = "medical_timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False)  # diagnosis, medication, lab_report, procedure, consultation, hospitalization
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String, nullable=True)  # document, intake, manual
    source_id = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
