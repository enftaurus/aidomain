from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models.user import User
from app.db.models.machine import Machine
from app.db.models.engineer_machine_assignment import EngineerMachineAssignment
from app.schemas.schemas import UserOut, AssignmentCreate, AssignmentOut
from app.core.security import get_current_user
from app.services.audit_service import log_action
from app.services.notification_service import create_notification

router = APIRouter(prefix="/engineers", tags=["Engineers"])


@router.get("/", response_model=List[UserOut])
async def list_engineers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).filter(User.role == "ENGINEER", User.is_active == True).all()


@router.get("/{engineer_id}", response_model=UserOut)
async def get_engineer(engineer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    eng = db.query(User).filter(User.id == engineer_id, User.role == "ENGINEER").first()
    if not eng:
        raise HTTPException(status_code=404, detail="Engineer not found")
    return eng


@router.get("/{engineer_id}/machines")
async def get_engineer_machines(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignments = (
        db.query(EngineerMachineAssignment)
        .filter(
            EngineerMachineAssignment.engineer_id == engineer_id,
            EngineerMachineAssignment.is_active == True,
        )
        .all()
    )
    machine_ids = [a.machine_id for a in assignments]
    machines = db.query(Machine).filter(Machine.id.in_(machine_ids)).all()
    return machines


@router.post("/assignments", response_model=AssignmentOut, status_code=201)
async def assign_engineer(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    # Check existing active assignment
    existing = (
        db.query(EngineerMachineAssignment)
        .filter(
            EngineerMachineAssignment.engineer_id == payload.engineer_id,
            EngineerMachineAssignment.machine_id == payload.machine_id,
            EngineerMachineAssignment.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Assignment already exists")

    assignment = EngineerMachineAssignment(
        engineer_id=payload.engineer_id,
        machine_id=payload.machine_id,
        assigned_by=current_user.id,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Notify engineer
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    create_notification(
        db,
        recipient_id=payload.engineer_id,
        title=f"Assigned to {machine.machine_code if machine else payload.machine_id}",
        message="You have been assigned to a machine.",
        type="ASSIGNMENT",
        machine_id=payload.machine_id,
    )

    log_action(
        db,
        action="ENGINEER_ASSIGNED",
        description=f"Engineer {payload.engineer_id} assigned to machine {payload.machine_id}",
        user_id=current_user.id,
        machine_id=payload.machine_id,
    )

    return assignment


@router.delete("/assignments/{assignment_id}", status_code=200)
async def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    a = db.query(EngineerMachineAssignment).filter(EngineerMachineAssignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    a.is_active = False
    db.commit()
    return {"message": "Assignment removed"}


@router.get("/assignments/all", response_model=List[AssignmentOut])
async def get_all_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(EngineerMachineAssignment)
        .filter(EngineerMachineAssignment.is_active == True)
        .all()
    )


@router.get("/assignments/machine/{machine_id}", response_model=List[AssignmentOut])
async def get_machine_assignments(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(EngineerMachineAssignment)
        .filter(
            EngineerMachineAssignment.machine_id == machine_id,
            EngineerMachineAssignment.is_active == True,
        )
        .all()
    )

