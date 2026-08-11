from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.schemas.schemas import AuditLogOut
from app.core.security import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=List[AuditLogOut])
async def list_audit_logs(
    machine_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
    q = db.query(AuditLog)
    if machine_id:
        q = q.filter(AuditLog.machine_id == machine_id)
    if action:
        q = q.filter(AuditLog.action == action.upper())
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
