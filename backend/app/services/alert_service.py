"""
Alert service — threshold evaluation, alert creation, notification dispatch.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models.alert import Alert
from app.db.models.machine import Machine
from app.db.models.user import User
from app.db.models.engineer_machine_assignment import EngineerMachineAssignment
from app.services.notification_service import create_notification
from app.services.audit_service import log_action
from app.core.logging import logger

# Thresholds
THRESHOLDS = {
    "rms_warning":  2.3,
    "rms_critical": 4.0,
    "kurtosis_warning":  4.0,
    "kurtosis_critical": 7.0,
    "temperature_warning":  70.0,
    "temperature_critical": 80.0,
}


def evaluate_and_create_alert(
    db: Session,
    machine: Machine,
    vibration_rms: float = None,
    kurtosis: float = None,
    temperature: float = None,
    created_by: int = None,
) -> Optional[Alert]:
    """
    Evaluate telemetry against thresholds.
    If thresholds exceeded, create an alert and dispatch notifications.
    Returns the created Alert or None.
    """
    severity = None
    title = ""
    description = ""
    evidence_parts = []

    if vibration_rms is not None:
        if vibration_rms >= THRESHOLDS["rms_critical"]:
            severity = "CRITICAL"
            title = "Critical Vibration Level Detected"
            evidence_parts.append(f"RMS vibration: {vibration_rms:.2f} mm/s (threshold: {THRESHOLDS['rms_critical']})")
        elif vibration_rms >= THRESHOLDS["rms_warning"]:
            severity = severity or "HIGH"
            title = title or "Elevated Vibration Detected"
            evidence_parts.append(f"RMS vibration: {vibration_rms:.2f} mm/s (threshold: {THRESHOLDS['rms_warning']})")

    if kurtosis is not None:
        if kurtosis >= THRESHOLDS["kurtosis_critical"]:
            severity = "CRITICAL" if severity != "CRITICAL" else severity
            title = title or "Critical Kurtosis — Possible Bearing Fault"
            evidence_parts.append(f"Kurtosis: {kurtosis:.1f} (threshold: {THRESHOLDS['kurtosis_critical']})")
        elif kurtosis >= THRESHOLDS["kurtosis_warning"]:
            severity = severity or "MEDIUM"
            evidence_parts.append(f"Kurtosis: {kurtosis:.1f} (threshold: {THRESHOLDS['kurtosis_warning']})")

    if temperature is not None:
        if temperature >= THRESHOLDS["temperature_critical"]:
            severity = "CRITICAL" if severity != "CRITICAL" else severity
            title = title or "Critical Temperature"
            evidence_parts.append(f"Temperature: {temperature:.1f}°C (threshold: {THRESHOLDS['temperature_critical']}°C)")
        elif temperature >= THRESHOLDS["temperature_warning"]:
            severity = severity or "MEDIUM"
            evidence_parts.append(f"Temperature: {temperature:.1f}°C (threshold: {THRESHOLDS['temperature_warning']}°C)")

    if not severity:
        return None  # No threshold exceeded

    alert = Alert(
        machine_id=machine.id,
        severity=severity,
        alert_type="VIBRATION" if vibration_rms else "TEMPERATURE",
        title=title,
        description=f"Automated threshold alert for {machine.machine_code}",
        confidence=85.0,
        status="OPEN",
        evidence="; ".join(evidence_parts),
        recommended_action="Inspect machine immediately. Review telemetry trend.",
        created_by=created_by,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Dispatch notifications to assigned engineers and admins
    _notify_stakeholders(db, machine, alert)

    log_action(
        db,
        action="ALERT_SENT",
        description=f"Alert created: {title} on {machine.machine_code}",
        machine_id=machine.id,
        user_id=created_by,
        new_state={"alert_id": alert.id, "severity": severity},
    )

    logger.info(f"Alert created [{severity}] for {machine.machine_code}: {title}")
    return alert


def create_manual_alert(
    db: Session,
    machine_id: int,
    severity: str,
    alert_type: str,
    title: str,
    description: str,
    confidence: float,
    evidence: str,
    recommended_action: str,
    created_by: int,
) -> Alert:
    """Create a manually-submitted alert."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()

    alert = Alert(
        machine_id=machine_id,
        severity=severity,
        alert_type=alert_type,
        title=title,
        description=description,
        confidence=confidence,
        status="OPEN",
        evidence=evidence,
        recommended_action=recommended_action,
        created_by=created_by,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    if machine:
        _notify_stakeholders(db, machine, alert)

    log_action(
        db,
        action="ALERT_SENT",
        description=f"Manual alert: {title}",
        machine_id=machine_id,
        user_id=created_by,
        new_state={"alert_id": alert.id, "severity": severity},
    )

    return alert


def _notify_stakeholders(db: Session, machine: Machine, alert: Alert) -> None:
    """Notify assigned engineers and all admins about an alert."""
    assignments = (
        db.query(EngineerMachineAssignment)
        .filter(
            EngineerMachineAssignment.machine_id == machine.id,
            EngineerMachineAssignment.is_active == True,
        )
        .all()
    )

    for a in assignments:
        create_notification(
            db,
            recipient_id=a.engineer_id,
            title=f"Alert on {machine.machine_code}: {alert.title}",
            message=alert.description or "",
            type="ALERT",
            machine_id=machine.id,
            alert_id=alert.id,
        )

    admins = db.query(User).filter(User.role == "ADMIN", User.is_active == True).all()
    for admin in admins:
        create_notification(
            db,
            recipient_id=admin.id,
            title=f"[{alert.severity}] Alert on {machine.machine_code}",
            message=alert.title,
            type="ALERT",
            machine_id=machine.id,
            alert_id=alert.id,
        )


def resolve_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, "ALERT_RESOLVED", f"Alert {alert_id} resolved", user_id=user_id, machine_id=alert.machine_id)
    return alert


def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "ACKNOWLEDGED"
    db.commit()
    return alert
