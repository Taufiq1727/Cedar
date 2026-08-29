"""Doctor assignment service - auto-assign specialist doctors based on patient symptoms."""
import logging
from sqlalchemy.orm import Session
from models.doctor import Doctor

logger = logging.getLogger(__name__)

# Keyword → specialization mapping
# Each entry is (list_of_keywords, specialization_value_in_db)
SPECIALIZATION_KEYWORDS = [
    (
        ["eye", "vision", "blurry", "blind", "cataract", "glaucoma", "retina",
         "cornea", "optic", "myopia", "spectacle", "glasses", "squint", "watery eye"],
        "Ophthalmology"
    ),
    (
        ["ear", "hearing", "deaf", "tinnitus", "throat", "nose", "sinus",
         "tonsil", "adenoid", "snoring", "voice", "hoarse", "vertigo",
         "nasal", "nosebleed", "earache", "ear pain", "sore throat", "ent"],
        "ENT"
    ),
    (
        ["heart", "chest pain", "palpitation", "blood pressure", "hypertension",
         "cardiac", "cholesterol", "angina", "arrhythmia", "ecg", "breathless",
         "shortness of breath", "cardio", "murmur"],
        "Cardiology"
    ),
    (
        ["skin", "rash", "acne", "allergy", "itching", "eczema", "psoriasis",
         "fungal", "dermatitis", "mole", "wart", "pigmentation", "hives",
         "urticaria", "boil", "ringworm", "dandruff", "hair loss", "alopecia"],
        "Dermatology"
    ),
    (
        ["bone", "joint", "fracture", "sprain", "back pain", "spine", "knee",
         "shoulder", "hip", "arthritis", "osteoporosis", "disc", "ligament",
         "tendon", "muscle pain", "ortho", "scoliosis", "dislocation", "neck pain"],
        "Orthopedics"
    ),
    (
        ["surgery", "wound", "hernia", "appendix", "gallstone", "tumor",
         "abscess", "biopsy", "lump", "swelling", "cyst", "operation",
         "surgical", "stitches"],
        "General Surgery"
    ),
]


def assign_doctor_by_complaint(db: Session, chief_complaint: str) -> str | None:
    """
    Given a chief complaint text, find the best-matching specialist doctor.
    Returns the doctor's ID, or the fallback general surgeon's ID.
    """
    if not chief_complaint:
        return _get_fallback_doctor(db)

    complaint_lower = chief_complaint.lower()

    # Score each specialization by keyword match count
    best_spec = None
    best_score = 0

    for keywords, specialization in SPECIALIZATION_KEYWORDS:
        score = sum(1 for kw in keywords if kw in complaint_lower)
        if score > best_score:
            best_score = score
            best_spec = specialization

    if best_spec and best_score > 0:
        doctor = db.query(Doctor).filter(
            Doctor.specialization == best_spec
        ).first()
        if doctor:
            logger.info(
                f"Assigned doctor: {best_spec} (score={best_score}) for complaint: {chief_complaint[:80]}"
            )
            return doctor.id

    # Fallback to General Surgery
    return _get_fallback_doctor(db)


def _get_fallback_doctor(db: Session) -> str | None:
    """Get the General Surgery doctor as fallback, or any available doctor."""
    doctor = db.query(Doctor).filter(
        Doctor.specialization == "General Surgery"
    ).first()
    if doctor:
        return doctor.id

    # If no General Surgery doc, pick any doctor
    doctor = db.query(Doctor).first()
    return doctor.id if doctor else None


def get_doctor_profile_for_patient(db: Session, doctor_id: str) -> dict | None:
    """Get a doctor's public profile info suitable for showing to patients."""
    if not doctor_id:
        return None

    from models.user import User
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return None

    user = db.query(User).filter(User.id == doctor.user_id).first()
    if not user:
        return None

    return {
        "doctor_id": doctor.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "specialization": doctor.specialization,
        "department": doctor.department,
        "hospital": doctor.hospital,
        "years_of_experience": doctor.years_of_experience,
        "qualification": doctor.qualification,
        "bio": doctor.bio,
        "professional_id": doctor.professional_id,
    }
