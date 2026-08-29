"""Seed script - creates 6 specialist doctors in the database."""
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
        "name": "Dr. Ananya Sharma",
        "email": "ananya.sharma@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543201",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-OPH-2014",
        "specialization": "Ophthalmology",
        "department": "Eye Care",
        "years_of_experience": 12,
        "qualification": "MBBS, MS (Ophthalmology), FICO",
        "bio": "Specialist in cataract surgery, glaucoma management, and retinal disorders. Passionate about preventive eye care and community ophthalmology.",
    },
    {
        "name": "Dr. Rajesh Patel",
        "email": "rajesh.patel@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543202",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-ENT-2011",
        "specialization": "ENT",
        "department": "Ear, Nose & Throat",
        "years_of_experience": 15,
        "qualification": "MBBS, MS (ENT), DNB",
        "bio": "Experienced in treating hearing disorders, sinus conditions, and throat infections. Performs advanced endoscopic sinus surgery and cochlear implants.",
    },
    {
        "name": "Dr. Priya Nair",
        "email": "priya.nair@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543203",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-SUR-2008",
        "specialization": "General Surgery",
        "department": "Surgery",
        "years_of_experience": 18,
        "qualification": "MBBS, MS (General Surgery), FACS",
        "bio": "Senior surgeon specializing in laparoscopic and minimally invasive procedures. Handles emergency surgeries, hernia repairs, and gallbladder operations.",
    },
    {
        "name": "Dr. Vikram Desai",
        "email": "vikram.desai@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543204",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-CAR-2006",
        "specialization": "Cardiology",
        "department": "Heart & Vascular",
        "years_of_experience": 20,
        "qualification": "MBBS, MD (Medicine), DM (Cardiology)",
        "bio": "Leading cardiologist with expertise in interventional cardiology, cardiac catheterization, and heart failure management. Pioneer in preventive cardiology programs.",
    },
    {
        "name": "Dr. Meera Iyer",
        "email": "meera.iyer@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543205",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-DER-2016",
        "specialization": "Dermatology",
        "department": "Dermatology",
        "years_of_experience": 10,
        "qualification": "MBBS, MD (Dermatology), DDV",
        "bio": "Expert in diagnosing and treating skin disorders, allergies, and cosmetic dermatology. Specializes in psoriasis, eczema, and laser treatments.",
    },
    {
        "name": "Dr. Arjun Reddy",
        "email": "arjun.reddy@medikiosk.com",
        "password": "Doctor@123",
        "phone": "+91-9876543206",
        "hospital": "MediKiosk General Hospital",
        "professional_id": "MCI-ORT-2012",
        "specialization": "Orthopedics",
        "department": "Orthopedics & Joint Care",
        "years_of_experience": 14,
        "qualification": "MBBS, MS (Orthopedics), MCh",
        "bio": "Orthopedic surgeon specializing in joint replacements, sports injuries, and spinal disorders. Experienced in arthroscopic surgery and fracture management.",
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
    print("  MediKiosk - Seeding Specialist Doctors")
    print("=" * 50)
    seed_doctors()
