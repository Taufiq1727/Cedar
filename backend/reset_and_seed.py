"""Reset and Seed Script for ClinAssistAI.
Purges previous database records, seeds new specialist doctors, and seeds brand new demo patients with realistic clinical cases.
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import engine, Base, SessionLocal, create_tables
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.intake import IntakeSession, PatientAnswer
from models.clinical import ClinicalHistory, ClinicalSummary, RedFlagAlert, MedicalTimelineEvent
from models.consent import ConsentRecord
from services.auth_service import hash_password
from seed_doctors import DOCTORS

DEMO_PATIENTS = [
    {
        "user": {
            "name": "Ramesh Patel",
            "email": "ramesh.patel@example.com",
            "password": "Patient@123",
            "phone": "+91-9811223344",
            "role": "patient"
        },
        "profile": {
            "age": 58,
            "gender": "Male",
            "blood_group": "B+",
            "emergency_contact_name": "Sita Patel",
            "emergency_contact_phone": "+91-9811223355",
            "medical_record_number": "MRN-2026-00101"
        },
        "session": {
            "chief_complaint": "Experiencing retrosternal chest tightness and shortness of breath upon climbing stairs for 4 days.",
            "pathway": "chest_pain",
            "status": "completed",
            "progress_pct": 100,
            "language": "en",
            "doctor_spec": "Cardiology",
            "created_offset_hours": 2,
            "completed_offset_hours": 1
        },
        "answers": [
            ("chief_complaint", "What is your main health concern today?", "I have persistent pressure and tightness in the center of my chest when walking or climbing stairs.", "text"),
            ("onset", "When did this chest tightness start?", "It began 4 days ago and occurs mostly with physical exertion.", "text"),
            ("severity", "On a scale of 1 to 10, how intense is the discomfort?", "It is around 7 out of 10 during exertion, subsides slightly after resting.", "text"),
            ("associated_symptoms", "Are you experiencing shortness of breath, sweating, or radiation to arms/jaw?", "Yes, moderate shortness of breath and mild sweating. Occasionally radiates to left shoulder.", "text"),
            ("medical_history", "Do you have any past medical conditions like hypertension or diabetes?", "I have had hypertension for 6 years, taking Amlodipine 5mg daily.", "text"),
            ("allergies", "Do you have any known allergies?", "No known drug or food allergies.", "text"),
        ],
        "red_flags": [
            {
                "rule_id": "RF-CARDIAC-01",
                "severity": "HIGH",
                "title": "Suspected Exertional Angina / Acute Coronary Syndrome",
                "description": "Retrosternal chest pressure radiating to left shoulder with exertional dyspnea in a 58yo male with chronic hypertension.",
                "resolved": False
            }
        ],
        "summary": {
            "summary_text": (
                "CLINICAL INTAKE SUMMARY (ClinAssistAI)\n"
                "--------------------------------------------------\n"
                "PATIENT: Ramesh Patel | 58Y / Male | Blood: B+\n"
                "CHIEF COMPLAINT: Retrosternal chest tightness and exertional dyspnea x 4 days\n\n"
                "HISTORY OF PRESENT ILLNESS (HPI):\n"
                "58-year-old male presents with a 4-day history of exertional retrosternal chest heaviness (7/10), "
                "radiating to the left shoulder and accompanied by moderate dyspnea and diaphoresis. Symptoms partially relieve with rest.\n\n"
                "PAST MEDICAL HISTORY (PMH):\n"
                "- Essential Hypertension (6 years)\n\n"
                "CURRENT MEDICATIONS:\n"
                "- Tab. Amlodipine 5mg OD\n\n"
                "ALLERGIES: NKDA\n\n"
                "RED FLAGS:\n"
                "[HIGH] Potential Cardiac Event / Angina Pectoris - Urgent ECG & Troponin evaluation advised."
            ),
            "summary_json": {
                "hpi": "Retrosternal chest tightness (7/10) on exertion radiating to left shoulder for 4 days.",
                "pmh": ["Hypertension (6 years)"],
                "medications": [{"name": "Amlodipine", "dosage": "5mg", "frequency": "Once daily"}],
                "allergies": [],
                "assessment": "High suspicion for angina pectoris / ischemic heart disease. Needs immediate clinical assessment."
            },
            "status": "generated"
        },
        "timeline": [
            ("diagnosis", "Diagnosed with Essential Hypertension", 6 * 365),
            ("medication", "Started on Tab Amlodipine 5mg OD", 6 * 365),
            ("consultation", "ClinAssistAI Pre-Consultation Intake: Chest Tightness", 0)
        ]
    },
    {
        "user": {
            "name": "Sunita Rao",
            "email": "sunita.rao@example.com",
            "password": "Patient@123",
            "phone": "+91-9822334455",
            "role": "patient"
        },
        "profile": {
            "age": 46,
            "gender": "Female",
            "blood_group": "O+",
            "emergency_contact_name": "Kishore Rao",
            "emergency_contact_phone": "+91-9822334466",
            "medical_record_number": "MRN-2026-00102"
        },
        "session": {
            "chief_complaint": "Gradual blurring of vision in both eyes and frequent headaches during digital screen work.",
            "pathway": "eye_vision",
            "status": "completed",
            "progress_pct": 100,
            "language": "en",
            "doctor_spec": "Ophthalmology",
            "created_offset_hours": 5,
            "completed_offset_hours": 4
        },
        "answers": [
            ("chief_complaint", "What is your main concern?", "Blurry vision for reading and working on laptop, with frontal eye strain.", "text"),
            ("duration", "How long have you noticed these vision changes?", "Progressive over the past 3 months.", "text"),
            ("eye_symptoms", "Any eye pain, redness, flashes of light, or halo around lights?", "Mild eye dryness and strain, no sudden flashes or severe pain.", "text"),
            ("past_glasses", "Do you currently wear eyeglasses?", "Yes, wear reading glasses (+1.25D) prescribed 3 years ago.", "text")
        ],
        "red_flags": [],
        "summary": {
            "summary_text": (
                "CLINICAL INTAKE SUMMARY (ClinAssistAI)\n"
                "--------------------------------------------------\n"
                "PATIENT: Sunita Rao | 46Y / Female | Blood: O+\n"
                "CHIEF COMPLAINT: Progressive bilateral near-vision blurring and asthenopia x 3 months\n\n"
                "HPI: 46-year-old female presents with 3-month progressive difficulty focusing on near tasks and computer screens, with associated end-of-day eye strain. Prior spectacles issued 3 years ago.\n"
                "PMH: Unremarkable\n"
                "ASSESSMENT: Probable presbyopic progression / refractive error with digital eye strain. Slit-lamp exam & comprehensive refraction indicated."
            ),
            "summary_json": {
                "hpi": "Progressive near-vision blurring and asthenopia for 3 months.",
                "pmh": [],
                "medications": [],
                "allergies": [],
                "assessment": "Presbyopia progression, refractive error evaluation."
            },
            "status": "generated"
        },
        "timeline": [
            ("procedure", "Last comprehensive eye exam & spectacle prescription", 3 * 365),
            ("consultation", "ClinAssistAI Pre-Consultation Intake: Eye Care", 0)
        ]
    },
    {
        "user": {
            "name": "Amitabh Sharma",
            "email": "amitabh.sharma@example.com",
            "password": "Patient@123",
            "phone": "+91-9833445566",
            "role": "patient"
        },
        "profile": {
            "age": 34,
            "gender": "Male",
            "blood_group": "A+",
            "emergency_contact_name": "Neha Sharma",
            "emergency_contact_phone": "+91-9833445577",
            "medical_record_number": "MRN-2026-00103"
        },
        "session": {
            "chief_complaint": "Acute right knee swelling and difficulty bearing weight after twisting injury while playing badminton.",
            "pathway": "joint_pain",
            "status": "completed",
            "progress_pct": 100,
            "language": "en",
            "doctor_spec": "Orthopedics",
            "created_offset_hours": 12,
            "completed_offset_hours": 11
        },
        "answers": [
            ("chief_complaint", "Describe your injury or joint pain.", "Twisted right knee 2 days ago while playing badminton, heard a popping sensation.", "text"),
            ("swelling", "Did the knee swell immediately?", "Significant swelling started within 2 hours of injury.", "text"),
            ("mobility", "Can you bend or bear weight on the right leg?", "Severe pain when trying to put full weight, limping significantly.", "text")
        ],
        "red_flags": [
            {
                "rule_id": "RF-ORTHO-02",
                "severity": "MEDIUM",
                "title": "Suspected Ligamentous / Meniscal Knee Injury",
                "description": "Acute twist mechanism with audible pop, immediate effusion and weight-bearing inability.",
                "resolved": False
            }
        ],
        "summary": {
            "summary_text": (
                "CLINICAL INTAKE SUMMARY (ClinAssistAI)\n"
                "--------------------------------------------------\n"
                "PATIENT: Amitabh Sharma | 34Y / Male | Blood: A+\n"
                "CHIEF COMPLAINT: Acute right knee injury with hemarthrosis/effusion x 2 days\n\n"
                "HPI: 34yo male experienced a non-contact pivoting twist of right knee during sport 2 days ago with audible pop and rapid effusion onset within 2 hours. Inability to fully weight bear.\n"
                "RED FLAGS: [MEDIUM] High likelihood of ACL/meniscus tear. Physical examination (Lachman/McMurray) and knee MRI recommended."
            ),
            "summary_json": {
                "hpi": "Right knee twisting injury, audible pop, acute effusion, limited weight bearing.",
                "pmh": [],
                "medications": [],
                "allergies": [],
                "assessment": "Suspected Right Knee Anterior Cruciate Ligament (ACL) or Meniscal Tear."
            },
            "status": "generated"
        },
        "timeline": [
            ("consultation", "ClinAssistAI Pre-Consultation Intake: Orthopedic Knee Injury", 0)
        ]
    },
    {
        "user": {
            "name": "Pooja Verma",
            "email": "pooja.verma@example.com",
            "password": "Patient@123",
            "phone": "+91-9844556677",
            "role": "patient"
        },
        "profile": {
            "age": 29,
            "gender": "Female",
            "blood_group": "AB+",
            "emergency_contact_name": "Vikram Verma",
            "emergency_contact_phone": "+91-9844556688",
            "medical_record_number": "MRN-2026-00104"
        },
        "session": {
            "chief_complaint": "Intense erythematous itchy rash and hives on forearms and neck for 2 days.",
            "pathway": "skin_rash",
            "status": "in_progress",
            "progress_pct": 60,
            "language": "en",
            "doctor_spec": "Dermatology",
            "created_offset_hours": 1,
            "completed_offset_hours": None
        },
        "answers": [
            ("chief_complaint", "What skin symptoms are you experiencing?", "Raised red hives and intense itching across both forearms and neck.", "text"),
            ("onset", "When did you first notice this rash?", "Started 48 hours ago after using a new cosmetic moisturizer.", "text")
        ],
        "red_flags": [],
        "summary": None,
        "timeline": [
            ("consultation", "ClinAssistAI Pre-Consultation Intake: Acute Dermatitis", 0)
        ]
    }
]


def reset_and_seed_all():
    """Drop and recreate all tables, seed new doctors, and seed fresh demo patients."""
    print("=" * 60)
    print("  ClinAssistAI - Complete Database Reset & Fresh Seeding")
    print("=" * 60)

    # Recreate tables cleanly
    Base.metadata.drop_all(bind=engine)
    create_tables()
    print("[OK] All tables dropped and cleanly recreated.")

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        # 1. Seed Clinical Assistants / Triage Nurses
        from seed_doctors import NURSES
        nurse_id_map = {}
        for nurse_data in NURSES:
            user = User(
                email=nurse_data["email"],
                password_hash=hash_password(nurse_data["password"]),
                role="assistant",
                name=nurse_data["name"],
                phone=nurse_data["phone"]
            )
            db.add(user)
            db.flush()
            nurse_id_map[nurse_data["name"]] = user.id
            print(f"  + Nurse/Assistant Seeded: {nurse_data['name']} ({nurse_data['email']})")

        lead_nurse_id = nurse_id_map.get("Nurse Sunita Verma")

        # 2. Seed Specialist Doctors
        doctor_spec_map = {}
        for doc_data in DOCTORS:
            user = User(
                email=doc_data["email"],
                password_hash=hash_password(doc_data["password"]),
                role="doctor",
                name=doc_data["name"],
                phone=doc_data["phone"]
            )
            db.add(user)
            db.flush()

            doctor = Doctor(
                user_id=user.id,
                hospital=doc_data["hospital"],
                professional_id=doc_data["professional_id"],
                specialization=doc_data["specialization"],
                department=doc_data["department"],
                years_of_experience=doc_data["years_of_experience"],
                qualification=doc_data["qualification"],
                bio=doc_data["bio"]
            )
            db.add(doctor)
            db.flush()
            doctor_spec_map[doc_data["specialization"]] = doctor.id
            print(f"  + Doctor Seeded: {doc_data['name']} ({doc_data['specialization']})")

        # 3. Seed Demo Patients (Triage Handoff Cases)
        for pdata in DEMO_PATIENTS:
            u_info = pdata["user"]
            prof_info = pdata["profile"]
            ses_info = pdata["session"]

            user = User(
                email=u_info["email"],
                password_hash=hash_password(u_info["password"]),
                role=u_info["role"],
                name=u_info["name"],
                phone=u_info["phone"]
            )
            db.add(user)
            db.flush()

            patient = Patient(
                user_id=user.id,
                age=prof_info["age"],
                gender=prof_info["gender"],
                blood_group=prof_info["blood_group"],
                emergency_contact_name=prof_info["emergency_contact_name"],
                emergency_contact_phone=prof_info["emergency_contact_phone"],
                medical_record_number=prof_info["medical_record_number"]
            )
            db.add(patient)
            db.flush()

            # Assigned doctor
            assigned_doc_id = doctor_spec_map.get(ses_info["doctor_spec"])

            session_created = now - timedelta(hours=ses_info["created_offset_hours"])
            session_completed = (now - timedelta(hours=ses_info["completed_offset_hours"])) if ses_info.get("completed_offset_hours") else None

            # Sample vitals based on condition
            has_high_flag = any(rf.get("severity") == "HIGH" for rf in pdata.get("red_flags", []))
            triage_lvl = "EMERGENCY" if has_high_flag else ("URGENT" if pdata.get("red_flags") else "ROUTINE")

            vitals_sample = {
                "bp": "148/92" if has_high_flag else "122/80",
                "pulse": "96" if has_high_flag else "74",
                "spo2": "94" if has_high_flag else "98",
                "temp": "100.8" if "fever" in ses_info["pathway"] else "98.4",
                "rbs": "164" if prof_info["age"] > 50 else "110",
            }

            nurse_note_sample = f"Patient interviewed at Triage Desk 1. Vitals recorded. Symptoms dictated and AI-parsed. Dispatched to Dr. {ses_info['doctor_spec']}."

            session = IntakeSession(
                patient_id=patient.id,
                language=ses_info["language"],
                status=ses_info["status"],
                chief_complaint=ses_info["chief_complaint"],
                pathway=ses_info["pathway"],
                progress_pct=ses_info["progress_pct"],
                assigned_doctor_id=assigned_doc_id,
                assistant_id=lead_nurse_id,
                triage_level=triage_lvl,
                vitals=vitals_sample,
                nurse_notes=nurse_note_sample,
                intake_source="assistant_triage",
                created_at=session_created,
                completed_at=session_completed
            )
            db.add(session)
            db.flush()

            # Consent record
            consent = ConsentRecord(
                patient_id=patient.id,
                session_id=session.id,
                consent_given=True,
                consent_type="clinical_intake",
                timestamp=session_created
            )
            db.add(consent)

            # Answers
            for answer in pdata.get("answers", []):
                # Support dict representation
                if isinstance(answer, dict):
                    q_key = answer.get("question_key") or answer.get("key")
                    q_text = answer.get("question_text") or answer.get("text")
                    ans_text = answer.get("answer_text") or answer.get("answer")
                    inp_method = answer.get("input_method") or answer.get("method")
                else:
                    # Assume a sequence (tuple/list). Allow 3 or 4 items.
                    if len(answer) == 4:
                        q_key, q_text, ans_text, inp_method = answer
                    elif len(answer) == 3:
                        q_key, q_text, ans_text = answer
                        inp_method = None
                    else:
                        raise ValueError(f"Unexpected answer format: {answer}")

                ans = PatientAnswer(
                    session_id=session.id,
                    question_key=q_key,
                    question_text=q_text,
                    answer_text=ans_text,
                    input_method=inp_method,
                    created_at=session_created + timedelta(minutes=2)
                )
                db.add(ans)

            # Red Flags
            for rf in pdata.get("red_flags", []):
                alert = RedFlagAlert(
                    session_id=session.id,
                    patient_id=patient.id,
                    rule_id=rf["rule_id"],
                    severity=rf["severity"],
                    title=rf["title"],
                    description=rf["description"],
                    resolved=rf.get("resolved", False),
                    created_at=session_created + timedelta(minutes=3)
                )
                db.add(alert)

            # Summary
            if pdata.get("summary"):
                sinfo = pdata["summary"]
                summary = ClinicalSummary(
                    session_id=session.id,
                    patient_id=patient.id,
                    summary_text=sinfo["summary_text"],
                    summary_json=sinfo["summary_json"],
                    status=sinfo["status"],
                    doctor_id=assigned_doc_id,
                    created_at=session_completed or session_created
                )
                db.add(summary)

            # Timeline
            for item in pdata.get("timeline", []):
                # Support multiple possible formats for timeline entries
                if isinstance(item, dict):
                    # Expected keys: event_type, title, days_ago
                    event_type = item.get("event_type")
                    title = item.get("title")
                    days_ago = item.get("days_ago", 0)
                elif isinstance(item, (list, tuple)):
                    # Allow tuple of length 3 or 4 (ignore extra values)
                    if len(item) >= 3:
                        event_type, title, days_ago = item[:3]
                    else:
                        # Skip malformed entry
                        continue
                else:
                    # Skip unsupported entry types (e.g., a plain string)
                    continue

                event_date = now - timedelta(days=days_ago)
                tl = MedicalTimelineEvent(
                    patient_id=patient.id,
                    event_date=event_date,
                    event_type=event_type,
                    title=title,
                    source_type="intake" if days_ago == 0 else "historical_record",
                    created_at=now,
                )
                db.add(tl)

            print(f"  + Patient Seeded: {u_info['name']} (Assigned: Dr. {ses_info['doctor_spec']})")

        db.commit()
        print("[OK] ClinAssistAI database successfully populated with fresh doctors and clinical cases!")

    except Exception as e:
        db.rollback()
        print(f"Error resetting and seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed_all()
