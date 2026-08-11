from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db, SessionLocal
from app.db.models.machine import Machine
from app.db.models.user import User
from app.schemas.schemas import MachineCreate, MachineUpdate, MachineOut, ShutdownRequest
from app.core.security import get_current_user
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.services.report_service import trigger_report_pipeline
from app.services.email_service import send_shutdown_email
from app.core.logging import logger

router = APIRouter(prefix="/machines", tags=["Machines"])


@router.get("/", response_model=List[MachineOut])
async def list_machines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Machine).all()


@router.post("/", response_model=MachineOut, status_code=201)
async def create_machine(
    payload: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    existing = db.query(Machine).filter(Machine.machine_code == payload.machine_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Machine code already exists")
    m = Machine(**payload.model_dump(), status="RUNNING", health_score=100.0)
    db.add(m)
    db.commit()
    db.refresh(m)
    log_action(db, "MACHINE_CREATED", f"Machine {payload.machine_code} created", user_id=current_user.id, machine_id=m.id)
    return m


@router.delete("/{machine_id}", status_code=200)
async def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    code = m.machine_code
    db.delete(m)
    db.commit()
    log_action(db, "MACHINE_DELETED", f"Machine {code} deleted", user_id=current_user.id, machine_id=machine_id)
    return {"message": f"Machine {code} deleted"}


@router.get("/{machine_id}", response_model=MachineOut)
async def get_machine(machine_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    return m


@router.patch("/{machine_id}", response_model=MachineOut)
async def update_machine(
    machine_id: int,
    payload: MachineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return m


@router.post("/{machine_id}/shutdown", status_code=200)
async def shutdown_machine(
    machine_id: int,
    payload: ShutdownRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Human-confirmed shutdown. AI must never call this.
    Requires explicit confirmation and a reason.
    """
    if not payload.confirmed:
        raise HTTPException(status_code=400, detail="Shutdown requires explicit confirmation")
    if not payload.reason:
        raise HTTPException(status_code=400, detail="Shutdown reason is required")

    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")

    previous_status = m.status
    m.status = "STOPPED"
    db.commit()

    log_action(
        db,
        action="MACHINE_SHUTDOWN_CONFIRMED",
        description=f"Manual shutdown by {current_user.name}: {payload.reason}",
        user_id=current_user.id,
        machine_id=machine_id,
        previous_state={"status": previous_status},
        new_state={"status": "STOPPED"},
        metadata={"reason": payload.reason},
    )

    # Notify all admins
    admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).all()
    for admin in admins:
        create_notification(
            db,
            recipient_id=admin.id,
            title=f"Manual Shutdown — {m.machine_code}",
            message=f"Shut down by {current_user.name}. Reason: {payload.reason}",
            type="SHUTDOWN",
            machine_id=machine_id,
        )

    # Background: email + report (with own sessions)
    all_emails = [a.email for a in admins]
    machine_code = m.machine_code
    machine_id_val = machine_id
    reason_str = payload.reason
    uid = current_user.id
    background_tasks.add_task(send_shutdown_email, all_emails, machine_code)
    background_tasks.add_task(_shutdown_report_bg, machine_id_val, reason_str, uid)

    logger.info(f"Machine {m.machine_code} shut down by {current_user.name}")
    return {"message": f"Machine {m.machine_code} shut down. Audit record created."}


@router.post("/{machine_id}/start", status_code=200)
async def start_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    if m.status != "STOPPED":
        raise HTTPException(status_code=400, detail="Machine is not stopped")

    m.status = "RUNNING"
    db.commit()
    log_action(db, "MACHINE_STARTED", f"Machine {m.machine_code} started", user_id=current_user.id, machine_id=machine_id)
    return {"message": f"Machine {m.machine_code} started."}


def _shutdown_report_bg(machine_id: int, reason: str, user_id: int):
    """Run report pipeline for shutdown in background with own session."""
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            trigger_report_pipeline(db, machine, f"Manual Shutdown: {reason}", None, None, user_id, True)
    except Exception as e:
        logger.error(f"Shutdown report error: {e}")
    finally:
        db.close()
