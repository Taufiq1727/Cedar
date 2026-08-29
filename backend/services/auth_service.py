"""Authentication service: password hashing, JWT, role-based access."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import binascii
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS


try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password safely using bcrypt or pbkdf2_sha256."""
    if HAS_BCRYPT:
        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        except Exception:
            pass

    # Fallback to PBKDF2-HMAC-SHA256
    salt = hashlib.sha256(os.urandom(16)).hexdigest()
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100000)
    return f"pbkdf2_sha256${salt}${binascii.hexlify(pwdhash).decode('ascii')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    if not hashed_password or not plain_password:
        return False

    # Check bcrypt hash format
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        if HAS_BCRYPT:
            try:
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            except Exception:
                pass
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    # Check custom PBKDF2 format
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            if len(parts) == 3:
                salt = parts[1]
                stored_hash = parts[2]
                pwdhash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("ascii"), 100000)
                return binascii.hexlify(pwdhash).decode("ascii") == stored_hash
        except Exception:
            return False

    # Check raw salt+hash fallback
    if len(hashed_password) > 64:
        try:
            salt = hashed_password[:64]
            stored_pwd = hashed_password[64:]
            pwdhash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("ascii"), 100000)
            if binascii.hexlify(pwdhash).decode("ascii") == stored_pwd:
                return True
        except Exception:
            pass

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(user_id: str, role: str, name: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload 
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: get the current authenticated user."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return user


def require_role(required_role: str):
    """FastAPI dependency factory: require a specific role."""
    def role_checker(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}",
            )
        return user
    return role_checker


# Convenience dependencies
require_patient = require_role("patient")
require_doctor = require_role("doctor")
