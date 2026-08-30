"""Seed script - creates 6 new specialist doctors for ClinAssistAI."""
import sys
import os

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from database import create_tables, SessionLocal
from models.user import User
from models.doctor import Doctor
from services.auth_service import hash_password

DOCTORS = [
    {
        "name": "Dr. Siddharth Varma",
        "email": "siddharth.varma@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543210",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-CARD-38491",
        "specialization": "Cardiology",
        "department": "Heart & Vascular Sciences",
        "years_of_experience": 16,
        "qualification": "MBBS, MD (Medicine), DM (Cardiology), FACC",
        "bio": "Senior consultant cardiologist specializing in interventional cardiology, heart failure management, acute coronary syndromes, and preventive cardiac wellness.",
    },
    {
        "name": "Dr. Roshni Sen",
        "email": "roshni.sen@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543211",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-OPHT-59218",
        "specialization": "Ophthalmology",
        "department": "Comprehensive Eye Care & Retina",
        "years_of_experience": 13,
        "qualification": "MBBS, MS (Ophthalmology), DNB, FICO",
        "bio": "Specialist in anterior segment disorders, advanced cataract microsurgery, glaucoma management, and diabetic retinopathy screenings.",
    },
    {
        "name": "Dr. Kabir Mukherjee",
        "email": "kabir.mukherjee@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543212",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-ENT-41092",
        "specialization": "ENT",
        "department": "Ear, Nose & Throat / Head & Neck",
        "years_of_experience": 14,
        "qualification": "MBBS, MS (ENT), FRCS (ORL-HNS)",
        "bio": "Otolaryngologist specializing in endoscopic sinus surgery, hearing loss interventions, voice pathology, and allergy-induced chronic rhinitis.",
    },
    {
        "name": "Dr. Ananya Kulkarni",
        "email": "ananya.kulkarni@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543213",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-SURG-72419",
        "specialization": "General Surgery",
        "department": "General & Laparoscopic Surgery",
        "years_of_experience": 17,
        "qualification": "MBBS, MS (General Surgery), FMAS, FIAGES",
        "bio": "General and laparoscopic surgeon skilled in minimally invasive abdominal surgeries, acute trauma care, and elective surgical procedures.",
    },
    {
        "name": "Dr. Farhan Alvi",
        "email": "farhan.alvi@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543214",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-ORTH-63820",
        "specialization": "Orthopedics",
        "department": "Orthopedics & Joint Reconstruction",
        "years_of_experience": 15,
        "qualification": "MBBS, MS (Orthopedics), MCh (Orth), Arthroplasty Fellowship",
        "bio": "Consultant orthopedic surgeon with high proficiency in complex fracture repair, joint replacements, sports injuries, and spinal degenerative conditions.",
    },
    {
        "name": "Dr. Sneha Roy",
        "email": "sneha.roy@clinassistai.com",
        "password": "Doctor@123",
        "phone": "+91-9876543215",
        "hospital": "ClinAssistAI Central Hospital",
        "professional_id": "MCI-DERM-81934",
        "specialization": "Dermatology",
        "department": "Dermatology & Clinical Immunology",
        "years_of_experience": 11,
        "qualification": "MBBS, MD (Dermatology, Venereology & Leprosy), DNB",
        "bio": "Dermatologist specializing in chronic dermatoses, severe eczema, psoriasis, autoimmune skin lesions, and precision clinical dermatology.",
    },
]


def seed_doctors():
    """Create all doctor accounts if they don't already exist."""
    create_tables()
    db = SessionLocal()

    created = 0
    skipped = 0

    try:
        for doc_data in DOCTORS:
            # Check if already exists
            existing = db.query(User).filter(User.email == doc_data["email"]).first()
            if existing:
                # Ensure doctor profile has latest details
                doc_profile = db.query(Doctor).filter(Doctor.user_id == existing.id).first()
                if doc_profile:
                    doc_profile.hospital = doc_data.get("hospital", doc_profile.hospital)
                    doc_profile.professional_id = doc_data.get("professional_id", doc_profile.professional_id)
                    doc_profile.specialization = doc_data.get("specialization", doc_profile.specialization)
                    doc_profile.department = doc_data.get("department", doc_profile.department)
                    doc_profile.years_of_experience = doc_data.get("years_of_experience", doc_profile.years_of_experience)
                    doc_profile.qualification = doc_data.get("qualification", doc_profile.qualification)
                    doc_profile.bio = doc_data.get("bio", doc_profile.bio)
                else:
                    new_doc = Doctor(
                        user_id=existing.id,
                        hospital=doc_data["hospital"],
                        professional_id=doc_data["professional_id"],
                        specialization=doc_data["specialization"],
                        department=doc_data["department"],
                        years_of_experience=doc_data["years_of_experience"],
                        qualification=doc_data["qualification"],
                        bio=doc_data["bio"],
                    )
                    db.add(new_doc)
                skipped += 1
                continue

            # Create user
            user = User(
                email=doc_data["email"],
                password_hash=hash_password(doc_data["password"]),
                role="doctor",
                name=doc_data["name"],
                phone=doc_data["phone"],
            )
            db.add(user)
            db.flush()

            # Create doctor profile
            doctor = Doctor(
                user_id=user.id,
                hospital=doc_data["hospital"],
                professional_id=doc_data["professional_id"],
                specialization=doc_data["specialization"],
                department=doc_data["department"],
                years_of_experience=doc_data["years_of_experience"],
                qualification=doc_data["qualification"],
                bio=doc_data["bio"],
            )
            db.add(doctor)
            db.flush()

            created += 1

        db.commit()
        print(f"Seeding complete: {created} created, {skipped} verified/updated")

    except Exception as e:
        db.rollback()
        print(f"Error seeding doctors: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("  ClinAssistAI - Seeding Specialist Doctors")
    print("=" * 50)
    seed_doctors()
