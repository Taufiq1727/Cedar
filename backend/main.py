"""MediKiosk Backend - FastAPI Application Entry Point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import CORS_ORIGINS, UPLOAD_DIR
from database import create_tables

# Import all models to register them with SQLAlchemy
import models  # noqa: F401

from routers.auth import router as auth_router
from routers.patient import router as patient_router
from routers.intake import router as intake_router
from routers.documents import router as documents_router
from routers.ai import router as ai_router
from routers.doctor import router as doctor_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MediKiosk API",
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
app.include_router(patient_router)
app.include_router(intake_router)
app.include_router(documents_router)
app.include_router(ai_router)
app.include_router(doctor_router)


@app.on_event("startup")
def startup():
    """Create database tables on startup."""
    logger.info("Creating database tables...")
    create_tables()
    logger.info("MediKiosk API started successfully.")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MediKiosk API",
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
