"""Pydantic schemas for document and clinical endpoints."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    patient_id: str
    filename: str
    original_filename: str
    file_type: str
    category: str
    file_size: Optional[float] = None
    uploaded_at: datetime
    extracted_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ExtractedDataResponse(BaseModel):
    id: str
    document_id: str
    raw_text: Optional[str] = None
    extracted_json: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True


class ClinicalSummaryResponse(BaseModel):
    id: str
    session_id: str
    patient_id: str
    summary_json: Optional[Dict[str, Any]] = None
    summary_text: Optional[str] = None
    status: str
    doctor_id: Optional[str] = None
    doctor_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryApproveRequest(BaseModel):
    status: str  # "approved" or "rejected"
    doctor_notes: Optional[str] = None
    edits: Optional[Dict[str, Any]] = None


class TimelineEventResponse(BaseModel):
    id: str
    patient_id: str
    event_date: datetime
    event_type: str
    title: str
    description: Optional[str] = None
    source_type: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class RedFlagResponse(BaseModel):
    id: str
    session_id: str
    patient_id: str
    rule_id: str
    severity: str
    title: str
    description: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DoctorPatientView(BaseModel):
    patient: Dict[str, Any]
    session: Dict[str, Any]
    answers: List[Dict[str, Any]]
    red_flags: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
    timeline: List[Dict[str, Any]]
