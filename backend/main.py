"""ClinAssistAI Backend - FastAPI Application Entry Point."""
import os
import sys
import logging

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import CORS_ORIGINS, UPLOAD_DIR
from database import create_tables, SessionLocal

# Import all models to register them with SQLAlchemy
import models  # noqa: F401

from routers.auth import router as auth_router
from routers.patient import router as patient_router
from routers.intake import router as intake_router
from routers.documents import router as documents_router
from routers.ai import router as ai_router
from routers.doctor import router as doctor_router
from routers.assistant import router as assistant_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ClinAssistAI API",
    description="AI-Powered Patient Case-Taking and Clinical History Software",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(patient_router)
app.include_router(intake_router)
app.include_router(documents_router)
app.include_router(ai_router)
app.include_router(doctor_router)


@app.on_event("startup")
def startup():
    """Create database tables and seed initial doctor accounts on startup."""
    logger.info("Initializing database...")
    create_tables()
    try:
        from seed_doctors import seed_doctors
        seed_doctors()
        logger.info("Doctor accounts verified.")
    except Exception as e:
        logger.warning(f"Doctor seeding check: {e}")
    logger.info("ClinAssistAI API started successfully.")


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ClinAssistAI API",
        "version": "1.0.0",
    }


@app.get("/api/status", tags=["Health"])
def api_status():
    """API status with feature availability."""
    from services.ai_service import _has_gemini
    from services.ocr_service import TESSERACT_AVAILABLE

    return {
        "status": "healthy",
        "features": {
            "authentication": True,
            "clinical_intake": True,
            "ai_extraction": _has_gemini(),
            "ocr": TESSERACT_AVAILABLE,
            "document_upload": True,
            "red_flag_detection": True,
            "fhir_export": True,
        },
    }


# Mount frontend directory for direct UI access
frontend_dir = os.path.abspath(os.path.join(backend_dir, "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
