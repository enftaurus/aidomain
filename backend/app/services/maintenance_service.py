"""
Maintenance service — scheduling, status updates, engineer notifications.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models.maintenance import Maintenance
from app.db.models.machine import Machine
from app.db.models.user import User
from app.services.notification_service import create_notification
from app.services.email_service import send_maintenance_email
from app.services.audit_service import log_action
from app.core.logging import logger


def schedule_maintenance(
    db: Session,
    machine_id: int,
    maintenance_type: str,
    description: str = "",
    scheduled_at: Optional[datetime] = None,
    engineer_id: Optional[int] = None,
    scheduled_by: Optional[int] = None,
    factory_notes: str = "",
) -> Maintenance:
    record = Maintenance(
        machine_id=machine_id,
        engineer_id=engineer_id,
        scheduled_by=scheduled_by,
        scheduled_at=scheduled_at,
        maintenance_type=maintenance_type,
        description=description,
        status="SCHEDULED",
        factory_notes=factory_notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Notify engineer if assigned
    if engineer_id:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        engineer = db.query(User).filter(User.id == engineer_id).first()
        if machine and engineer:
            create_notification(
                db,
                recipient_id=engineer_id,
                title=f"Maintenance Scheduled — {machine.machine_code}",
                message=f"{maintenance_type} scheduled for {scheduled_at}",
                type="MAINTENANCE",
                machine_id=machine_id,
                maintenance_id=record.id,
            )
            # Email notification
            send_maintenance_email(
                engineer.email,
                machine.machine_code,
                str(scheduled_at),
                maintenance_type,
            )

    log_action(
        db,
        action="MAINTENANCE_SCHEDULED",
        description=f"Maintenance scheduled for machine {machine_id}: {maintenance_type}",
        user_id=scheduled_by,
        machine_id=machine_id,
        new_state={"maintenance_id": record.id, "type": maintenance_type, "status": "SCHEDULED"},
    )

    logger.info(f"Maintenance scheduled for machine {machine_id}: {maintenance_type}")
    return record


def update_maintenance_status(
    db: Session,
    maintenance_id: int,
    new_status: str,
    engineer_notes: str = None,
    factory_notes: str = None,
    user_id: int = None,
) -> Optional[Maintenance]:
    record = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not record:
        return None

    old_status = record.status
    record.status = new_status
    if engineer_notes is not None:
        record.engineer_notes = engineer_notes
    if factory_notes is not None:
        record.factory_notes = factory_notes

    db.commit()

    log_action(
        db,
        action="MAINTENANCE_STATUS_UPDATED",
        description=f"Maintenance {maintenance_id} status: {old_status} → {new_status}",
        user_id=user_id,
        machine_id=record.machine_id,
        previous_state={"status": old_status},
        new_state={"status": new_status},
    )

    return record
