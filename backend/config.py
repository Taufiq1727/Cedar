"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clinassistai.db")

# Normalize SQLite URL to absolute path inside backend directory if relative
if DATABASE_URL.startswith("sqlite:///./") or DATABASE_URL.startswith("sqlite:////."):
    db_filename = DATABASE_URL.replace("sqlite:///./", "").replace("sqlite:////.", "")
    abs_db_path = os.path.abspath(os.path.join(BASE_DIR, db_filename))
    DATABASE_URL = f"sqlite:///{abs_db_path.replace(os.sep, '/')}"

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Server
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5000"))
cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000")
CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

# Uploads
env_upload = os.getenv("UPLOAD_DIR", "")
if env_upload and not os.path.isabs(env_upload):
    UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, env_upload.lstrip("./\\")))
else:
    UPLOAD_DIR = env_upload or os.path.join(BASE_DIR, "uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
