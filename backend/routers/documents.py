"""Document router - upload, OCR, and AI extraction."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.patient import Patient
from models.document import MedicalDocument, ExtractedDocumentData
from services.auth_service import require_patient, get_current_user
from services.ocr_service import extract_text
from services.ai_service import extract_document_info
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {"jpg", "jpeg", "png", "pdf"}
ALLOWED_CATEGORIES = {"prescription", "lab_report", "discharge_summary"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    session_id: str = Form(None),
    user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Upload a medical document, run OCR, and extract clinical info."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(404, "Patient profile not found")

    # Validate category
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, f"Category must be one of: {', '.join(ALLOWED_CATEGORIES)}")

    # Validate file type
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(400, f"File type not allowed. Supported: {', '.join(ALLOWED_TYPES)}")

    # Read and validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(400, f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB")

    # Save file
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = MedicalDocument(
        patient_id=patient.id,
        session_id=session_id,
        filename=unique_name,
        original_filename=file.filename,
        file_type=ext,
        category=category,
        file_path=file_path,
        file_size=size_mb,
    )
    db.add(doc)
    db.flush()

    # Run OCR
    ocr_text = extract_text(file_path, ext)

    # Extract clinical info using AI
    extracted_json = await extract_document_info(ocr_text, category)

    # Save extracted data
    extracted = ExtractedDocumentData(
        document_id=doc.id,
        raw_text=ocr_text,
        extracted_json=extracted_json,
        confidence=extracted_json.get("confidence", 0.7) if isinstance(extracted_json, dict) else 0.5,
        extraction_method="ocr_gemini",
    )
    db.add(extracted)
    db.commit()

    return {
        "id": doc.id,
        "filename": doc.original_filename,
        "category": doc.category,
        "file_type": doc.file_type,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "ocr_text_preview": ocr_text[:500] if ocr_text else None,
        "extracted_data": extracted_json,
        "message": "Document uploaded and processed successfully. AI-extracted information requires clinician verification.",
    }


@router.get("/patient/{patient_id}")
def get_patient_documents(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all documents for a patient. Accessible by the patient or any doctor."""
    # Access control
    if user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if not patient or patient.id != patient_id:
            raise HTTPException(403, "Access denied")

    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id
    ).order_by(MedicalDocument.uploaded_at.desc()).all()

    result = []
    for doc in documents:
        extracted = db.query(ExtractedDocumentData).filter(
            ExtractedDocumentData.document_id == doc.id
        ).first()

        result.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "category": doc.category,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "has_extracted_data": extracted is not None,
            "extracted_data": extracted.extracted_json if extracted else None,
            "ocr_text": extracted.raw_text if extracted else None,
        })

    return result


@router.get("/{doc_id}/extracted")
def get_extracted_data(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get extracted data for a specific document."""
    doc = db.query(MedicalDocument).filter(MedicalDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Access control
    if user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if not patient or patient.id != doc.patient_id:
            raise HTTPException(403, "Access denied")

    extracted = db.query(ExtractedDocumentData).filter(
        ExtractedDocumentData.document_id == doc_id
    ).first()

    if not extracted:
        raise HTTPException(404, "No extracted data found for this document")

    return {
        "id": extracted.id,
        "document_id": doc_id,
        "raw_text": extracted.raw_text,
        "extracted_json": extracted.extracted_json,
        "confidence": extracted.confidence,
        "extraction_method": extracted.extraction_method,
    }
