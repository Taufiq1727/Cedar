"""Red Flag Service - evaluation and persistence of clinical alerts."""
import logging
from sqlalchemy.orm import Session
from models.clinical import RedFlagAlert
from clinical.red_flags import evaluate_red_flags

logger = logging.getLogger(__name__)


def check_and_save_red_flags(
    db: Session, session_id: str, patient_id: str,
    structured_data: dict, pathway: str
) -> list:
    """Evaluate red flags and save new ones to the database."""
    triggered = evaluate_red_flags(structured_data, pathway)

    existing_rule_ids = [
        r.rule_id for r in db.query(RedFlagAlert)
        .filter(RedFlagAlert.session_id == session_id).all()
    ]

    new_flags = []
    for flag in triggered:
        if flag["rule_id"] not in existing_rule_ids:
            alert = RedFlagAlert(
                session_id=session_id,
                patient_id=patient_id,
                rule_id=flag["rule_id"],
                severity=flag["severity"],
                title=flag["title"],
                description=flag["description"],
            )
            db.add(alert)
            new_flags.append(flag)

    if new_flags:
        db.commit()

    return triggered


def get_patient_red_flags(db: Session, patient_id: str) -> list:
    """Get all red flags for a patient."""
    flags = db.query(RedFlagAlert).filter(
        RedFlagAlert.patient_id == patient_id
    ).order_by(RedFlagAlert.created_at.desc()).all()

    return [
        {
            "id": f.id,
            "session_id": f.session_id,
            "rule_id": f.rule_id,
            "severity": f.severity,
            "title": f.title,
            "description": f.description,
            "resolved": f.resolved,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in flags
    ]
