"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # "assistant", "nurse", "doctor", "patient"
    phone: Optional[str] = None
    # Patient-specific
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    # Doctor/Assistant-specific
    hospital: Optional[str] = None
    professional_id: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True
