"""Pydantic schemas for intake endpoints."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class StartIntakeRequest(BaseModel):
    language: str = "en"
    consent_given: bool = True


class AnswerRequest(BaseModel):
    answer_text: str
    input_method: str = "text"  # "text" or "voice"
    question_key: Optional[str] = None


class IntakeQuestionResponse(BaseModel):
    session_id: str
    question_key: str
    question_text: str
    question_type: str = "text"  # text, select, scale
    options: Optional[List[str]] = None
    progress_pct: int
    extracted_data: Optional[Dict[str, Any]] = None
    red_flags: Optional[List[Dict[str, Any]]] = None
    is_complete: bool = False


class IntakeSessionResponse(BaseModel):
    id: str
    patient_id: str
    language: str
    status: str
    chief_complaint: Optional[str] = None
    pathway: Optional[str] = None
    progress_pct: int
    structured_data: Optional[Dict[str, Any]] = None
    answers: Optional[List[Dict[str, Any]]] = None
    red_flags: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
