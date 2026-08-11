from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models.report import Report
from app.db.models.machine import Machine
from app.db.models.user import User
from app.schemas.schemas import ReportOut
from app.core.security import get_current_user
from app.services.report_service import trigger_report_pipeline

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=List[ReportOut])
async def list_reports(
    machine_id: Optional[int] = None,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Report)
    if machine_id:
        q = q.filter(Report.machine_id == machine_id)
    if report_type:
        q = q.filter(Report.report_type == report_type.upper())
    return q.order_by(Report.generated_at.desc()).all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


@router.get("/{report_id}/download")
async def download_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    if not r.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available for this report")
    import os
    if not os.path.exists(r.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    return FileResponse(r.pdf_path, media_type="application/pdf", filename=f"machsense-report-{report_id}.pdf")


@router.post("/generate/{machine_id}", status_code=202)
async def generate_report(
    machine_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a report for a machine."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    background_tasks.add_task(
        trigger_report_pipeline,
        db, machine, "Manual report request", None, None, current_user.id, True
    )

    return {"message": f"Report generation triggered for {machine.machine_code}"}
