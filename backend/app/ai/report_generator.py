"""
Report generator — entry point for the AI report pipeline.
Gathers all data, calls LangChain, returns structured result.
"""
import json
import statistics
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.machine import Machine
from app.db.models.telemetry import Telemetry
from app.db.models.alert import Alert
from app.db.models.maintenance import Maintenance
from app.db.models.engineer_recommendation import EngineerRecommendation
from app.db.models.user import User
from app.ai.chains.report_chain import run_report_chain, AIReportResult
from app.core.logging import logger


def _telemetry_stats(records: List[Telemetry]) -> str:
    if not records:
        return "No telemetry data available."

    def _stat(values: List[float]) -> str:
        if not values:
            return "N/A"
        return f"min={min(values):.2f}, max={max(values):.2f}, mean={statistics.mean(values):.2f}"

    rms_vals    = [r.vibration_rms for r in records if r.vibration_rms is not None]
    temp_vals   = [r.temperature   for r in records if r.temperature   is not None]
    rpm_vals    = [r.rpm           for r in records if r.rpm           is not None]
    kurt_vals   = [r.kurtosis      for r in records if r.kurtosis      is not None]
    cf_vals     = [r.crest_factor  for r in records if r.crest_factor  is not None]

    return (
        f"Samples: {len(records)}\n"
        f"RMS vibration (mm/s): {_stat(rms_vals)}\n"
        f"Temperature (°C): {_stat(temp_vals)}\n"
        f"RPM: {_stat(rpm_vals)}\n"
        f"Kurtosis: {_stat(kurt_vals)}\n"
        f"Crest Factor: {_stat(cf_vals)}"
    )


def _baseline_deviations(machine: Machine, records: List[Telemetry]) -> str:
    if not records or not machine.vibration_rms:
        return "Baseline comparison not available."

    latest = records[-1]
    lines = []
    if machine.vibration_rms and latest.vibration_rms:
        delta = latest.vibration_rms - machine.vibration_rms
        lines.append(f"RMS: current={latest.vibration_rms:.2f}, baseline≈{machine.vibration_rms:.2f}, delta={delta:+.2f} mm/s")
    if machine.temperature and latest.temperature:
        delta = latest.temperature - machine.temperature
        lines.append(f"Temperature: current={latest.temperature:.1f}°C, baseline≈{machine.temperature:.1f}°C, delta={delta:+.1f}°C")
    if machine.rpm and latest.rpm:
        delta = latest.rpm - machine.rpm
        lines.append(f"RPM: current={latest.rpm:.0f}, baseline≈{machine.rpm:.0f}, delta={delta:+.0f}")
    return "\n".join(lines) if lines else "No significant deviations detected."


def generate_report(
    db: Session,
    machine: Machine,
    trigger_event: str = "Manual",
) -> AIReportResult:
    """
    Gather all machine context from DB and run the AI chain.
    Returns an AIReportResult.
    """
    # Recent 50 telemetry records
    telemetry = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine.id)
        .order_by(Telemetry.timestamp.desc())
        .limit(50)
        .all()
    )

    # Open alerts
    alerts = (
        db.query(Alert)
        .filter(Alert.machine_id == machine.id, Alert.status == "OPEN")
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )
    alerts_str = "\n".join(
        f"[{a.severity}] {a.title} — {a.description or ''} (confidence: {a.confidence or 'N/A'}%)"
        for a in alerts
    ) or "No open alerts."

    # Recent maintenance (last 5)
    maintenance = (
        db.query(Maintenance)
        .filter(Maintenance.machine_id == machine.id)
        .order_by(Maintenance.created_at.desc())
        .limit(5)
        .all()
    )
    maint_str = "\n".join(
        f"{m.maintenance_type} — {m.status} — {m.scheduled_at}"
        for m in maintenance
    ) or "No maintenance history."

    # Engineer recommendations
    recs = (
        db.query(EngineerRecommendation)
        .filter(EngineerRecommendation.machine_id == machine.id)
        .order_by(EngineerRecommendation.created_at.desc())
        .limit(5)
        .all()
    )
    recs_str = "\n".join(
        f"[{r.priority}] {r.recommendation}"
        for r in recs
    ) or "No engineer recommendations."

    # FFT data from latest telemetry
    latest = telemetry[0] if telemetry else None
    fft_str = (
        f"Dominant frequency: {latest.dominant_frequency:.1f} Hz"
        if latest and latest.dominant_frequency
        else "FFT data not available."
    )

    machine_data = (
        f"ID: {machine.machine_code}\n"
        f"Name: {machine.name}\n"
        f"Location: {machine.location}\n"
        f"Type: {machine.machine_type}\n"
        f"Current Status: {machine.status}\n"
        f"Health Score: {machine.health_score:.1f}%\n"
        f"Trigger: {trigger_event}"
    )

    logger.info(f"Running AI report chain for {machine.machine_code}")

    return run_report_chain(
        machine_data=machine_data,
        telemetry_stats=_telemetry_stats(telemetry),
        baseline_deviations=_baseline_deviations(machine, telemetry),
        alerts=alerts_str,
        fft_data=fft_str,
        maintenance_history=maint_str,
        engineer_recommendations=recs_str,
    )
