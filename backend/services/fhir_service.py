"""FHIR Compatibility Service - generate FHIR-like resources from patient data."""
from datetime import datetime, timezone


def generate_fhir_patient(patient_data: dict, user_data: dict) -> dict:
    """Generate a FHIR-compatible Patient resource."""
    return {
        "resourceType": "Patient",
        "id": patient_data.get("id"),
        "meta": {
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
        },
        "identifier": [
            {
                "system": "urn:medikiosk:patient",
                "value": patient_data.get("id"),
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "text": user_data.get("name", ""),
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": user_data.get("phone", ""),
                "use": "mobile",
            },
            {
                "system": "email",
                "value": user_data.get("email", ""),
            },
        ],
        "gender": _map_gender(patient_data.get("gender")),
        "birthDate": None,  # Would calculate from age if needed
    }


def generate_fhir_condition(diagnosis: str, patient_id: str, date: str = None) -> dict:
    """Generate a FHIR-compatible Condition resource."""
    return {
        "resourceType": "Condition",
        "id": None,
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "text": diagnosis,
        },
        "onsetDateTime": date,
        "recordedDate": datetime.now(timezone.utc).isoformat(),
        "clinicalStatus": {
            "coding": [{"code": "active", "display": "Active"}],
        },
    }


def generate_fhir_observation(test_name: str, value: str, unit: str, patient_id: str) -> dict:
    """Generate a FHIR-compatible Observation resource (for lab values)."""
    return {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "text": test_name,
        },
        "valueQuantity": {
            "value": value,
            "unit": unit,
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
    }


def generate_fhir_medication_statement(medication: dict, patient_id: str) -> dict:
    """Generate a FHIR-compatible MedicationStatement resource."""
    return {
        "resourceType": "MedicationStatement",
        "status": "active",
        "subject": {"reference": f"Patient/{patient_id}"},
        "medicationCodeableConcept": {
            "text": medication.get("name", ""),
        },
        "dosage": [
            {
                "text": f"{medication.get('dosage', '')} {medication.get('frequency', '')}",
            }
        ],
    }


def generate_fhir_encounter(session_data: dict, patient_id: str) -> dict:
    """Generate a FHIR-compatible Encounter resource for the intake session."""
    return {
        "resourceType": "Encounter",
        "id": session_data.get("id"),
        "status": "finished" if session_data.get("status") == "completed" else "in-progress",
        "class": {
            "code": "AMB",
            "display": "ambulatory",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": session_data.get("created_at"),
            "end": session_data.get("completed_at"),
        },
        "reasonCode": [
            {"text": session_data.get("chief_complaint", "")},
        ],
    }


def generate_fhir_bundle(patient_data: dict, user_data: dict, session_data: dict = None,
                          conditions: list = None, medications: list = None) -> dict:
    """Generate a FHIR Bundle combining all resources for a patient."""
    entries = []

    # Patient resource
    patient_resource = generate_fhir_patient(patient_data, user_data)
    entries.append({"resource": patient_resource})

    # Encounter
    if session_data:
        encounter = generate_fhir_encounter(session_data, patient_data["id"])
        entries.append({"resource": encounter})

    # Conditions
    if conditions:
        for cond in conditions:
            c = generate_fhir_condition(cond, patient_data["id"])
            entries.append({"resource": c})

    # Medications
    if medications:
        for med in medications:
            m = generate_fhir_medication_statement(med, patient_data["id"])
            entries.append({"resource": m})

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": entries,
    }


def _map_gender(gender: str) -> str:
    """Map gender value to FHIR gender code."""
    if not gender:
        return "unknown"
    g = gender.lower()
    if g in ("male", "m"):
        return "male"
    elif g in ("female", "f"):
        return "female"
    elif g in ("other", "o"):
        return "other"
    return "unknown"
