from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db, SessionLocal
from app.db.models.alert import Alert
from app.db.models.machine import Machine
from app.db.models.user import User
from app.schemas.schemas import AlertCreate, AlertUpdate, AlertOut
from app.core.security import get_current_user
from app.services.alert_service import create_manual_alert, resolve_alert, acknowledge_alert
from app.services.report_service import trigger_report_pipeline

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertOut])
async def list_alerts(
    machine_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Alert)
    if machine_id:
        q = q.filter(Alert.machine_id == machine_id)
    if status:
        q = q.filter(Alert.status == status.upper())
    return q.order_by(Alert.created_at.desc()).all()


@router.post("/", response_model=AlertOut, status_code=201)
async def create_alert(
    payload: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    alert = create_manual_alert(
        db,
        machine_id=payload.machine_id,
        severity=payload.severity.upper(),
        alert_type=payload.alert_type.upper(),
        title=payload.title,
        description=payload.description or "",
        confidence=payload.confidence or 80.0,
        evidence=payload.evidence or "",
        recommended_action=payload.recommended_action or "",
        created_by=current_user.id,
    )

    # Trigger report pipeline in background (with own session)
    if payload.severity.upper() in ("HIGH", "CRITICAL"):
        background_tasks.add_task(_alert_report_bg, payload.machine_id, payload.title, alert.id, current_user.id)

    return alert


def _alert_report_bg(machine_id: int, alert_title: str, alert_id: int, user_id: int):
    """Trigger report for high/critical alert in background with own session."""
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            from app.services.report_service import trigger_report_pipeline
            trigger_report_pipeline(db, machine, f"Alert: {alert_title}", alert_id, None, user_id, True)
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"Alert report error: {e}")
    finally:
        db.close()


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return a


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
async def ack_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = acknowledge_alert(db, alert_id, current_user.id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return a


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
async def resolve(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = resolve_alert(db, alert_id, current_user.id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return a
