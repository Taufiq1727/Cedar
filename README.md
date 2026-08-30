# ClinAssistAI

AI-Powered Patient Case-Taking & Clinical History Software for Indian Hospitals.

## Overview
**ClinAssistAI** automates pre-consultation patient intake with adaptive conversational questionnaires, multilingual support, document OCR & AI parsing, red-flag detection, and physician-ready clinical summaries.

## Quick Start

### 1. Backend Setup
```bash
# Activate virtual environment
.venv\Scripts\activate

# Reset and Seed Database with Doctors and Demo Patients
python backend/reset_and_seed.py

# Run FastAPI Server
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Frontend Access
Open `frontend/index.html` or navigate to `http://localhost:8000/` in your browser.

## Credentials
Refer to `doctor_credentials.txt` for all specialist doctor and demo patient login details.
- **Doctor Accounts**: `*@clinassistai.com` | Password: `Doctor@123`
- **Patient Accounts**: `*@example.com` | Password: `Patient@123`
