"""Notification creation and retrieval service."""
from sqlalchemy.orm import Session
from app.db.models.notification import Notification


def create_notification(
    db: Session,
    recipient_id: int,
    title: str,
    message: str = "",
    type: str = "SYSTEM",
    machine_id: int = None,
    alert_id: int = None,
    maintenance_id: int = None,
) -> Notification:
    n = Notification(
        recipient_id=recipient_id,
        machine_id=machine_id,
        alert_id=alert_id,
        maintenance_id=maintenance_id,
        type=type,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_notifications(db: Session, user_id: int, unread_only: bool = False):
    q = db.query(Notification).filter(Notification.recipient_id == user_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.order_by(Notification.created_at.desc()).all()


def mark_read(db: Session, notification_id: int, user_id: int) -> bool:
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == user_id,
    ).first()
    if n:
        n.is_read = True
        db.commit()
        return True
    return False


def mark_all_read(db: Session, user_id: int) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.recipient_id == user_id, Notification.is_read == False)
        .all()
    )
    for n in updated:
        n.is_read = True
    db.commit()
    return len(updated)
