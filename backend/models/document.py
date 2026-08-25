"""Medical document and extracted data models."""
import uuid
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, ForeignKey
from database import Base


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("intake_sessions.id"), nullable=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # jpg, png, pdf
    category = Column(String, nullable=False)  # prescription, lab_report, discharge_summary
    file_path = Column(String, nullable=False)
    file_size = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ExtractedDocumentData(Base):
    __tablename__ = "extracted_document_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("medical_documents.id"), nullable=False, unique=True)
    raw_text = Column(Text, nullable=True)
    extracted_json = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    extraction_method = Column(String, default="ocr_gemini")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
