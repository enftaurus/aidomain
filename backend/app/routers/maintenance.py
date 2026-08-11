from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models.maintenance import Maintenance
from app.db.models.user import User
from app.schemas.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceOut
from app.core.security import get_current_user
from app.services.maintenance_service import schedule_maintenance, update_maintenance_status

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("/", response_model=List[MaintenanceOut])
async def list_maintenance(
    machine_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Maintenance)
    if machine_id:
        q = q.filter(Maintenance.machine_id == machine_id)
    return q.order_by(Maintenance.created_at.desc()).all()


@router.post("/", response_model=MaintenanceOut, status_code=201)
async def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = schedule_maintenance(
        db,
        machine_id=payload.machine_id,
        maintenance_type=payload.maintenance_type,
        description=payload.description or "",
        scheduled_at=payload.scheduled_at,
        engineer_id=payload.engineer_id,
        scheduled_by=current_user.id,
        factory_notes=payload.factory_notes or "",
    )
    return record


@router.get("/{maintenance_id}", response_model=MaintenanceOut)
async def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return m


@router.patch("/{maintenance_id}", response_model=MaintenanceOut)
async def update_maintenance(
    maintenance_id: int,
    payload: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = update_maintenance_status(
        db,
        maintenance_id=maintenance_id,
        new_status=payload.status or db.query(Maintenance).filter(Maintenance.id == maintenance_id).first().status,
        engineer_notes=payload.engineer_notes,
        factory_notes=payload.factory_notes,
        user_id=current_user.id,
    )
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return m
