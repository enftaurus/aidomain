"""
ESP32 Router — Dedicated high-throughput Wi-Fi streaming ingestion and graphing endpoints.
Allows ESP32 hardware sensors (vibration, temperature, RPM) to stream time-series telemetry.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db, SessionLocal
from app.db.models.machine import Machine
from app.db.models.telemetry import Telemetry
from app.db.models.user import User
from app.services.telemetry_service import ingest_telemetry, should_trigger_report
from app.services.alert_service import evaluate_and_create_alert
from app.services.report_service import trigger_report_pipeline
from app.core.logging import logger

router = APIRouter(prefix="/esp32", tags=["ESP32 Hardware"])


class ESP32Payload(BaseModel):
    device_id: Optional[str] = "ESP32-GENERIC"
    machine_id: int
    rpm: Optional[float] = 1485.0
    temperature: Optional[float] = 54.0
    accel_x: Optional[float] = 0.0
    accel_y: Optional[float] = 0.0
    accel_z: Optional[float] = 1.0
    vibration_rms: Optional[float] = 1.7
    kurtosis: Optional[float] = 3.2
    crest_factor: Optional[float] = 2.8
    dominant_frequency: Optional[float] = 25.0


@router.post("/stream", status_code=201)
async def ingest_esp32_stream(
    payload: ESP32Payload,
    background_tasks: BackgroundTasks,
    x_esp32_device_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Dedicated ESP32 Wi-Fi Data Ingestion Endpoint.
    Directly streams time-series data from ESP32 microcontrollers.
    Persists data for live graphing, updates machine health, and evaluates threshold alerts.
    """
    device_id = x_esp32_device_id or payload.device_id or "ESP32-UNKNOWN"

    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine ID {payload.machine_id} not found")

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
    )

    machine_id_val = payload.machine_id
    rms = payload.vibration_rms
    kurt = payload.kurtosis
    temp = payload.temperature

    # Find admin user for report generation attribution
    admin_user = db.query(User).filter(User.role == "ADMIN", User.is_active == True).first()
    user_id = admin_user.id if admin_user else 1

    # Evaluate thresholds in background with own DB session
    background_tasks.add_task(_check_thresholds_bg, machine_id_val, rms, kurt, temp, user_id)

    # Check if critical AI report should be triggered
    trigger_reason = should_trigger_report(record)
    if trigger_reason:
        background_tasks.add_task(_trigger_report_bg, machine_id_val, f"ESP32 Anomaly [{device_id}]: {trigger_reason}", user_id)

    return {
        "status": "ingested",
        "device_id": device_id,
        "machine_code": machine.machine_code,
        "telemetry_id": record.id,
        "recorded_at": record.timestamp.isoformat() if record.timestamp else datetime.utcnow().isoformat(),
        "health_score": machine.health_score,
        "vibration_rms": payload.vibration_rms,
    }


@router.get("/stream/{machine_id}")
async def get_esp32_graph_series(
    machine_id: int,
    limit: int = 60,
    db: Session = Depends(get_db),
):
    """
    Graphing API Endpoint.
    Returns formatted time-series data array for Next.js live and historical charts.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    records = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )

    # Reverse to chronological order for chart plotting
    chronological = list(reversed(records))

    series = [
        {
            "timestamp": r.timestamp.isoformat() if r.timestamp else datetime.utcnow().isoformat(),
            "rpm": r.rpm or 0.0,
            "temperature": r.temperature or 0.0,
            "vibration_rms": r.vibration_rms or 0.0,
            "kurtosis": r.kurtosis or 0.0,
            "crest_factor": r.crest_factor or 0.0,
            "health_score": r.health_score or 100.0,
        }
        for r in chronological
    ]

    return {
        "machine_id": machine.id,
        "machine_code": machine.machine_code,
        "name": machine.name,
        "status": machine.status,
        "health_score": machine.health_score,
        "baseline": {
            "rms": [1.4, 2.0],
            "temperature": [51, 57],
            "rpm": [1470, 1500],
            "kurtosis": [2.9, 3.7],
        },
        "total_samples": len(series),
        "series": series,
    }


@router.get("/devices")
async def list_esp32_devices(db: Session = Depends(get_db)):
    """
    List connected ESP32 hardware devices and their monitored machines.
    """
    machines = db.query(Machine).all()
    devices = [
        {
            "device_id": f"ESP32-{m.machine_code}",
            "machine_id": m.id,
            "machine_code": m.machine_code,
            "machine_name": m.name,
            "status": "ONLINE" if m.status != "OFFLINE" else "OFFLINE",
            "last_rms": m.vibration_rms,
            "last_temperature": m.temperature,
            "health_score": m.health_score,
        }
        for m in machines
    ]
    return {"total_devices": len(devices), "devices": devices}


def _check_thresholds_bg(machine_id: int, vibration_rms, kurtosis, temperature, user_id: int):
    """Background threshold evaluation using a fresh DB session."""
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
        logger.error(f"ESP32 threshold check error: {e}")
    finally:
        db.close()


def _trigger_report_bg(machine_id: int, trigger_reason: str, user_id: int):
    """Background report pipeline using a fresh DB session."""
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            trigger_report_pipeline(db, machine, trigger_reason, None, None, user_id, True)
    except Exception as e:
        logger.error(f"ESP32 report pipeline error: {e}")
    finally:
        db.close()
