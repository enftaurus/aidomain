from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models.engineer_recommendation import EngineerRecommendation
from app.db.models.machine import Machine
from app.db.models.user import User
from app.schemas.schemas import RecommendationCreate, RecommendationOut
from app.core.security import get_current_user
from app.services.notification_service import create_notification
from app.services.audit_service import log_action

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/", response_model=List[RecommendationOut])
async def list_recommendations(
    machine_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(EngineerRecommendation)
    if machine_id:
        q = q.filter(EngineerRecommendation.machine_id == machine_id)
    return q.order_by(EngineerRecommendation.created_at.desc()).all()


@router.post("/", response_model=RecommendationOut, status_code=201)
async def create_recommendation(
    payload: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    rec = EngineerRecommendation(
        machine_id=payload.machine_id,
        engineer_id=current_user.id,
        maintenance_id=payload.maintenance_id,
        recommendation=payload.recommendation,
        priority=payload.priority.upper(),
        status="PENDING",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Notify all admins
    admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).all()
    for admin in admins:
        create_notification(
            db,
            recipient_id=admin.id,
            title=f"Engineer Recommendation — {machine.machine_code}",
            message=payload.recommendation[:200],
            type="SYSTEM",
            machine_id=payload.machine_id,
        )

    log_action(
        db,
        action="ENGINEER_RECOMMENDATION_ADDED",
        description=f"Recommendation by engineer {current_user.id} for machine {payload.machine_id}",
        user_id=current_user.id,
        machine_id=payload.machine_id,
    )

    return rec


@router.patch("/{rec_id}/acknowledge", response_model=RecommendationOut)
async def acknowledge_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    rec = db.query(EngineerRecommendation).filter(EngineerRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = "ACKNOWLEDGED"
    db.commit()
    return rec
