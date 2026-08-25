"""Consent record model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from database import Base


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=False)
    consent_given = Column(Boolean, nullable=False)
    consent_type = Column(String, default="clinical_intake")  # clinical_intake, data_processing
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
