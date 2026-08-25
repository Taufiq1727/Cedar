"""Database engine, session management, and base model with robust fallback."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, DatabaseError
from config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()


def _get_engine(db_url):
    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)


try:
    engine = _get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Could not connect to configured DB ({DATABASE_URL}): {e}. Falling back to SQLite.")
    DATABASE_URL = "sqlite:///./medikiosk.db"
    engine = _get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined by ORM models."""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
    except (OperationalError, DatabaseError) as e:
        logger.warning(f"Database error during table creation: {e}. Falling back to local SQLite database.")
        sqlite_url = "sqlite:///./medikiosk.db"
        engine = _get_engine(sqlite_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)

