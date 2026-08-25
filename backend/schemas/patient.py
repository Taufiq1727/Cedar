"""Pydantic schemas for patient endpoints."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PatientProfile(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    class Config:
        from_attributes = True


class PatientUpdateRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    phone: Optional[str] = None


class SessionSummaryResponse(BaseModel):
    id: str
    chief_complaint: Optional[str] = None
    pathway: Optional[str] = None
    status: str
    progress_pct: int
    language: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_summary: bool = False
    has_red_flags: bool = False

    class Config:
        from_attributes = True
