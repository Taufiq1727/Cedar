"""Timeline Service - medical timeline generation from patient data."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.clinical import MedicalTimelineEvent
from models.document import MedicalDocument, ExtractedDocumentData
from models.intake import IntakeSession

logger = logging.getLogger(__name__)


def generate_timeline(db: Session, patient_id: str) -> list:
    """Generate a medical timeline by aggregating all patient events."""
    events = []

    # Get events from intake sessions
    sessions = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient_id
    ).order_by(IntakeSession.created_at).all()

    for s in sessions:
        events.append({
            "id": f"session_{s.id}",
            "event_date": s.created_at.isoformat() if s.created_at else None,
            "event_type": "consultation",
            "title": f"Clinical Intake: {s.chief_complaint or 'General Assessment'}",
            "description": f"Status: {s.status}. Pathway: {s.pathway or 'General'}.",
            "source_type": "intake",
            "source_id": s.id,
        })

    # Get events from uploaded documents
    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id
    ).order_by(MedicalDocument.uploaded_at).all()

    for doc in documents:
        extracted = db.query(ExtractedDocumentData).filter(
            ExtractedDocumentData.document_id == doc.id
        ).first()

        doc_event = {
            "id": f"doc_{doc.id}",
            "event_date": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "event_type": _category_to_event_type(doc.category),
            "title": f"{doc.category.replace('_', ' ').title()}: {doc.original_filename}",
            "description": "",
            "source_type": "document",
            "source_id": doc.id,
        }

        # Add extracted info to description
        if extracted and extracted.extracted_json:
            ej = extracted.extracted_json
            if ej.get("document_date"):
                doc_event["event_date"] = ej["document_date"]
            parts = []
            if ej.get("diagnoses"):
                parts.append(f"Diagnoses: {', '.join(ej['diagnoses'])}")
            if ej.get("medications"):
                med_names = [m.get("name", "") for m in ej["medications"] if isinstance(m, dict)]
                if med_names:
                    parts.append(f"Medications: {', '.join(med_names)}")
            doc_event["description"] = ". ".join(parts)

            # Create sub-events for medications and diagnoses
            if ej.get("diagnoses"):
                for diag in ej["diagnoses"]:
                    events.append({
                        "id": f"diag_{doc.id}_{diag[:20]}",
                        "event_date": ej.get("document_date") or doc.uploaded_at.isoformat(),
                        "event_type": "diagnosis",
                        "title": f"Diagnosis: {diag}",
                        "description": f"Source: {doc.original_filename}",
                        "source_type": "document",
                        "source_id": doc.id,
                    })

            if ej.get("medications"):
                for med in ej["medications"]:
                    if isinstance(med, dict):
                        events.append({
                            "id": f"med_{doc.id}_{med.get('name', '')[:20]}",
                            "event_date": ej.get("document_date") or doc.uploaded_at.isoformat(),
                            "event_type": "medication",
                            "title": f"Medication: {med.get('name', 'Unknown')}",
                            "description": f"Dosage: {med.get('dosage', 'N/A')}, Frequency: {med.get('frequency', 'N/A')}",
                            "source_type": "document",
                            "source_id": doc.id,
                        })

        events.append(doc_event)

    # Get persisted timeline events from database
    db_events = db.query(MedicalTimelineEvent).filter(
        MedicalTimelineEvent.patient_id == patient_id
    ).order_by(MedicalTimelineEvent.event_date).all()

    for e in db_events:
        events.append({
            "id": e.id,
            "event_date": e.event_date.isoformat() if e.event_date else None,
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "source_type": e.source_type,
            "source_id": e.source_id,
            "metadata": e.metadata_json,
        })

    # Sort by date (most recent first)
    events.sort(key=lambda x: x.get("event_date") or "0", reverse=True)

    return events


def _category_to_event_type(category: str) -> str:
    """Map document category to timeline event type."""
    mapping = {
        "prescription": "medication",
        "lab_report": "lab_report",
        "discharge_summary": "hospitalization",
    }
    return mapping.get(category, "document")
