"""Authentication router - register, login, profile."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.audit import AuditLog
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from services.auth_service import (
    hash_password, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new patient or doctor."""
    # Validate role
    role = req.role.lower()
    if role == "nurse":
        role = "assistant"
    if role not in ("patient", "doctor", "assistant"):
        raise HTTPException(400, "Role must be 'assistant', 'doctor', or 'patient'")

    # Check duplicate email
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(409, "An account with this email already exists")

    # Validate password
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    # Create user
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        role=role,
        name=req.name,
        phone=req.phone,
    )
    db.add(user)
    db.flush()

    # Create role-specific profile
    if role == "patient":
        patient = Patient(
            user_id=user.id,
            age=req.age,
            gender=req.gender,
            blood_group=req.blood_group,
        )
        db.add(patient)
    elif role == "doctor":
        doctor = Doctor(
            user_id=user.id,
            hospital=req.hospital,
            professional_id=req.professional_id,
            specialization=req.specialization,
            department=req.department or req.specialization,
        )
        db.add(doctor)

    # Audit log
    audit = AuditLog(user_id=user.id, action="register", resource="user", resource_id=user.id)
    db.add(audit)

    db.commit()

    token = create_access_token(user.id, user.role, user.name)
    return TokenResponse(
        access_token=token,
        role=user.role,
        name=user.name,
        user_id=user.id,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")

    # Audit log
    audit = AuditLog(user_id=user.id, action="login", resource="user", resource_id=user.id)
    db.add(audit)
    db.commit()

    token = create_access_token(user.id, user.role, user.name)
    return TokenResponse(
        access_token=token,
        role=user.role,
        name=user.name,
        user_id=user.id,
    )


@router.get("/me")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile with role-specific data."""
    profile = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
    }

    if user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if patient:
            profile.update({
                "patient_id": patient.id,
                "age": patient.age,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "address": patient.address,
                "emergency_contact_name": patient.emergency_contact_name,
                "emergency_contact_phone": patient.emergency_contact_phone,
            })
    elif user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if doctor:
            profile.update({
                "doctor_id": doctor.id,
                "hospital": doctor.hospital,
                "professional_id": doctor.professional_id,
                "specialization": doctor.specialization,
                "department": doctor.department,
            })

    return profile
