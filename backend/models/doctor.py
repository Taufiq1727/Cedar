"""Doctor profile model."""
import uuid
from sqlalchemy import Column, String, ForeignKey
from database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    hospital = Column(String, nullable=True)
    professional_id = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    department = Column(String, nullable=True)
