"""
Telemetry service — ingest telemetry, compute derived features, update machine snapshot.
Source-agnostic: mock or ESP32 both enter the same pipeline.
"""
import math
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.telemetry import Telemetry
from app.db.models.machine import Machine
from app.core.logging import logger


def _compute_health_score(
    vibration_rms: Optional[float],
    kurtosis: Optional[float],
    temperature: Optional[float],
) -> float:
    """Simple heuristic health score 0–100."""
    score = 100.0

    if vibration_rms is not None:
        if vibration_rms >= 4.5:
            score -= 45
        elif vibration_rms >= 3.0:
            score -= 25
        elif vibration_rms >= 2.0:
            score -= 10

    if kurtosis is not None:
        if kurtosis >= 8.0:
            score -= 30
        elif kurtosis >= 5.0:
            score -= 15
        elif kurtosis >= 4.0:
            score -= 5

    if temperature is not None:
        if temperature >= 80:
            score -= 20
        elif temperature >= 70:
            score -= 10
        elif temperature >= 65:
            score -= 5

    return max(0.0, score)


def ingest_telemetry(
    db: Session,
    machine_id: int,
    rpm: Optional[float] = None,
    temperature: Optional[float] = None,
    accel_x: Optional[float] = None,
    accel_y: Optional[float] = None,
    accel_z: Optional[float] = None,
    vibration_rms: Optional[float] = None,
    kurtosis: Optional[float] = None,
    crest_factor: Optional[float] = None,
    dominant_frequency: Optional[float] = None,
    health_score: Optional[float] = None,
) -> Telemetry:
    """
    Ingest a single telemetry sample.
    Computes health_score if not provided.
    Updates the machine snapshot.
    """
    computed_health = health_score or _compute_health_score(vibration_rms, kurtosis, temperature)

    record = Telemetry(
        machine_id=machine_id,
        rpm=rpm,
        temperature=temperature,
        accel_x=accel_x,
        accel_y=accel_y,
        accel_z=accel_z,
        vibration_rms=vibration_rms,
        kurtosis=kurtosis,
        crest_factor=crest_factor,
        dominant_frequency=dominant_frequency,
        health_score=computed_health,
    )
    db.add(record)

    # Update machine live snapshot
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if machine:
        if rpm is not None:
            machine.rpm = rpm
        if temperature is not None:
            machine.temperature = temperature
        if vibration_rms is not None:
            machine.vibration_rms = vibration_rms
        if kurtosis is not None:
            machine.kurtosis = kurtosis
        if crest_factor is not None:
            machine.crest_factor = crest_factor
        machine.health_score = computed_health

        # Auto-status based on health (strictly preserves STOPPED, MAINTENANCE, OFFLINE)
        if machine.status and machine.status.upper() not in ("STOPPED", "MAINTENANCE", "OFFLINE"):
            if computed_health < 40:
                machine.status = "CRITICAL"
            elif computed_health < 65:
                machine.status = "WARNING"
            elif machine.status in ("CRITICAL", "WARNING"):
                machine.status = "RUNNING"

    db.commit()
    db.refresh(record)
    logger.debug(f"Telemetry ingested for machine {machine_id}: RMS={vibration_rms}, health={computed_health:.1f}")
    return record


def get_recent_telemetry(db: Session, machine_id: int, limit: int = 60) -> List[Telemetry]:
    return (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )


def should_trigger_report(telemetry: Telemetry) -> Optional[str]:
    """
    Return a trigger reason string if this telemetry reading warrants a report,
    None otherwise.
    """
    if telemetry.vibration_rms and telemetry.vibration_rms >= 4.0:
        return f"RMS vibration {telemetry.vibration_rms:.2f} mm/s exceeds critical threshold (4.0)"
    if telemetry.kurtosis and telemetry.kurtosis >= 7.0:
        return f"Kurtosis {telemetry.kurtosis:.1f} exceeds critical threshold (7.0)"
    if telemetry.temperature and telemetry.temperature >= 80:
        return f"Temperature {telemetry.temperature:.1f}°C exceeds critical threshold (80°C)"
    if telemetry.health_score and telemetry.health_score < 40:
        return f"Health score {telemetry.health_score:.0f}% critically low"
    return None
