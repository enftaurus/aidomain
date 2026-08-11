"""Append-only audit log service."""
import json
from sqlalchemy.orm import Session
from app.db.models.audit_log import AuditLog


def log_action(
    db: Session,
    action: str,
    description: str = "",
    user_id: int = None,
    machine_id: int = None,
    previous_state: dict = None,
    new_state: dict = None,
    metadata: dict = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        machine_id=machine_id,
        action=action,
        description=description,
        previous_state=json.dumps(previous_state) if previous_state else None,
        new_state=json.dumps(new_state) if new_state else None,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
