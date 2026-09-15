# ClinAssistAI

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Credentials](#credentials)
- [Testing](#testing)
- [Contribution Guidelines](#contribution-guidelines)
- [License](#license)

---

## Overview
**ClinAssistAI** is an AI‑powered patient case‑taking and clinical history platform designed for Indian hospitals. It automates the pre‑consultation intake process using adaptive conversational questionnaires, multilingual support, document OCR, AI parsing, red‑flag detection, and generates physician‑ready clinical summaries.

---

## Features
- **Adaptive Conversational Questionnaire** – Dynamically adjusts based on patient responses.
- **Multilingual Support** – Handles conversations in multiple Indian languages.
- **Document Upload & OCR** – Patients can upload PDFs or images; the system extracts text automatically.
- **Red‑Flag Detection** – Flags critical symptoms for immediate physician attention.
- **AI‑Generated Summaries** – Produces concise, structured clinical notes ready for the doctor.
- **Secure Authentication** – Separate credentials for doctors and demo patients.

---

## Architecture
- **Backend** – FastAPI (Python) exposing REST endpoints for authentication, questionnaire flow, file upload, and AI processing.
- **Frontend** – Vanilla HTML, CSS, and JavaScript providing a lightweight, responsive UI.
- **Database** – SQLite (development) / PostgreSQL (production) storing user accounts and session data.
- **AI Services** – Integrated with LLM APIs (e.g., OpenAI, Anthropic) for natural‑language processing and summary generation.
- **Docker (optional)** – Dockerfile and docker‑compose configurations are provided for containerised deployment.

---

## Project Structure
```
Cedar/
├─ backend/               # FastAPI server
│   ├─ app/               # API routers, models, services
│   ├─ main.py            # Application entry point
│   ├─ requirements.txt   # Python dependencies
│   └─ reset_and_seed.py  # DB reset & seed script
├─ frontend/              # Static HTML/JS/CSS
│   └─ doctor-dashboard.html
├─ uploads/               # Uploaded patient documents (runtime)
├─ doctor_credentials.txt # Sample login credentials
├─ .env.example           # Example environment variables
└─ README.md              # This documentation
```

---

## Prerequisites
- **Python 3.9+**
- **Git** – to clone the repository.
- **Virtual Environment** – recommended to isolate Python packages.
- **Node.js (optional)** – only if you wish to extend the frontend with a build system.

---

## Installation
### Backend Setup
```bash
# Clone the repository
git clone https://github.com/your-org/ClinAssistAI.git
cd ClinAssistAI

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# .venv/bin/activate       # macOS/Linux

# Install Python dependencies
pip install -r backend/requirements.txt

# Copy environment variables and edit as needed
cp .env.example .env
# Edit .env to set your AI API keys, DB URL, etc.

# Reset and seed the database with demo doctors & patients
python backend/reset_and_seed.py
```
### Frontend Setup
The frontend consists of static files; no build step is required.
- Open `frontend/doctor-dashboard.html` directly in a browser, **or**
- Access it via the FastAPI static route at `http://localhost:8000/` after the server is running.

---

## Running the Application
```bash
# Start the FastAPI server (development mode)
cd backend
uvicorn main:app --reload --port 8000
```
The API will be available at `http://localhost:8000/`. Visit `http://localhost:8000/` in your browser to launch the dashboard.

---

## API Reference
The backend exposes the following key endpoints (see `backend/app/routers/` for full implementation):
- `POST /auth/login` – Authenticate doctors or patients.
- `GET /questionnaire/{session_id}` – Retrieve the next set of questions.
- `POST /questionnaire/{session_id}` – Submit answers.
- `POST /upload` – Upload PDF/Image documents for OCR processing.
- `GET /summary/{session_id}` – Fetch the AI‑generated clinical summary.

For detailed OpenAPI documentation, navigate to `http://localhost:8000/docs` after the server starts.

---

## Credentials
Refer to `doctor_credentials.txt` for sample login details.

- **Doctor Accounts**: `doctor1@clinassistai.com` | Password: `Doctor@123`
- **Patient Accounts**: `patient1@example.com` | Password: `Patient@123`

Feel free to add more users by editing the SQLite database via the `reset_and_seed.py` script.

---

## Testing
```bash
# Run backend unit tests
pytest test_endpoints.py
```
Make sure the server is not running while executing the tests, as they launch a test client internally.

---

## Contribution Guidelines
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Write tests for new functionality.
4. Ensure linting passes (`flake8` is configured).
5. Submit a Pull Request with a clear description of changes.

---

## License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

*Happy hacking! 🚀*
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
