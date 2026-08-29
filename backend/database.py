"""Database engine, session management, and base model with robust fallback."""
import logging
from sqlalchemy import create_engine, inspect, text
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


def _sync_columns():
    """Ensure existing tables have all columns defined in ORM models (SQLite/PostgreSQL)."""
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            existing_tables = inspector.get_table_names()

            for table_name, table in Base.metadata.tables.items():
                if table_name not in existing_tables:
                    continue

                existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
                for column in table.columns:
                    if column.name not in existing_cols:
                        col_type = column.type.compile(engine.dialect)
                        logger.info(f"Adding missing column '{column.name}' ({col_type}) to table '{table_name}'")
                        try:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"))
                            conn.commit()
                        except Exception as add_err:
                            logger.warning(f"Could not add column {column.name} to {table_name}: {add_err}")
    except Exception as e:
        logger.warning(f"Column synchronization notice: {e}")


def create_tables():
    """Create all tables defined by ORM models and sync missing columns."""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        _sync_columns()
    except (OperationalError, DatabaseError) as e:
        logger.warning(f"Database error during table creation: {e}. Falling back to local SQLite database.")
        from config import BASE_DIR
        import os
        sqlite_path = os.path.join(BASE_DIR, "medikiosk.db").replace(os.sep, "/")
        sqlite_url = f"sqlite:///{sqlite_path}"
        engine = _get_engine(sqlite_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        _sync_columns()


