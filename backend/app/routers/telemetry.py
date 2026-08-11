from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db, SessionLocal
from app.db.models.machine import Machine
from app.db.models.user import User
from app.schemas.schemas import TelemetryCreate, TelemetryOut
from app.core.security import get_current_user
from app.services.telemetry_service import ingest_telemetry, get_recent_telemetry, should_trigger_report
from app.services.alert_service import evaluate_and_create_alert
from app.services.report_service import trigger_report_pipeline

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/ingest", response_model=TelemetryOut, status_code=201)
async def ingest(
    payload: TelemetryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ingest a single telemetry sample.
    Source-agnostic: mock data or ESP32 both call this endpoint.
    Automatically evaluates thresholds and triggers alerts/reports.
    """
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    record = ingest_telemetry(
        db,
        machine_id=payload.machine_id,
        rpm=payload.rpm,
        temperature=payload.temperature,
        accel_x=payload.accel_x,
        accel_y=payload.accel_y,
        accel_z=payload.accel_z,
        vibration_rms=payload.vibration_rms,
        kurtosis=payload.kurtosis,
        crest_factor=payload.crest_factor,
        dominant_frequency=payload.dominant_frequency,
        health_score=payload.health_score,
    )

    # Background tasks use their own DB sessions (request session will be closed)
    machine_id = payload.machine_id
    user_id = current_user.id

    background_tasks.add_task(
        _check_thresholds_bg,
        machine_id, payload.vibration_rms, payload.kurtosis, payload.temperature, user_id,
    )

    trigger_reason = should_trigger_report(record)
    if trigger_reason:
        background_tasks.add_task(_trigger_report_bg, machine_id, trigger_reason, user_id)

    return record


def _check_thresholds_bg(machine_id: int, vibration_rms, kurtosis, temperature, user_id: int):
    """Alert threshold evaluation with its own DB session."""
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            evaluate_and_create_alert(
                db, machine,
                vibration_rms=vibration_rms,
                kurtosis=kurtosis,
                temperature=temperature,
                created_by=user_id,
            )
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"Threshold check error: {e}")
    finally:
        db.close()


def _trigger_report_bg(machine_id: int, trigger_reason: str, user_id: int):
    """Report pipeline in background with its own DB session."""
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            trigger_report_pipeline(db, machine, trigger_reason, None, None, user_id, True)
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"Report pipeline error: {e}")
    finally:
        db.close()


@router.get("/{machine_id}", response_model=List[TelemetryOut])
async def get_telemetry(
    machine_id: int,
    limit: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_recent_telemetry(db, machine_id, limit)


@router.post("/mock/{machine_id}", status_code=201)
async def inject_mock_telemetry(
    machine_id: int,
    mode: str = "normal",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inject a simulated telemetry reading for development/testing.
    mode: normal | warning | critical
    """
    import random

    noise = lambda base, amp: base + (random.random() - 0.5) * amp

    if mode == "critical":
        data = dict(rpm=noise(1440, 5), temperature=noise(72, 1), vibration_rms=noise(4.8, 0.2), kurtosis=noise(8.5, 0.3), crest_factor=noise(5.5, 0.2))
    elif mode == "warning":
        data = dict(rpm=noise(1465, 5), temperature=noise(64, 1), vibration_rms=noise(3.2, 0.15), kurtosis=noise(5.5, 0.2), crest_factor=noise(3.8, 0.15))
    else:
        data = dict(rpm=noise(1485, 3), temperature=noise(54, 0.8), vibration_rms=noise(1.7, 0.1), kurtosis=noise(3.2, 0.1), crest_factor=noise(2.8, 0.08))

    payload = TelemetryCreate(machine_id=machine_id, **data)
    return await ingest(payload, background_tasks, db, current_user)
