from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "ENGINEER"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Machines ──────────────────────────────────────────────────────────────────

class MachineCreate(BaseModel):
    machine_code: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    machine_type: Optional[str] = None


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    machine_type: Optional[str] = None
    status: Optional[str] = None


class MachineOut(BaseModel):
    id: int
    machine_code: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    machine_type: Optional[str] = None
    status: str
    health_score: Optional[float] = None
    rpm: Optional[float] = None
    temperature: Optional[float] = None
    vibration_rms: Optional[float] = None
    kurtosis: Optional[float] = None
    crest_factor: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ShutdownRequest(BaseModel):
    reason: str
    confirmed: bool


# ── Telemetry ─────────────────────────────────────────────────────────────────

class TelemetryCreate(BaseModel):
    machine_id: int
    rpm: Optional[float] = None
    temperature: Optional[float] = None
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    vibration_rms: Optional[float] = None
    kurtosis: Optional[float] = None
    crest_factor: Optional[float] = None
    dominant_frequency: Optional[float] = None
    health_score: Optional[float] = None


class TelemetryOut(BaseModel):
    id: int
    machine_id: int
    timestamp: Optional[datetime] = None
    rpm: Optional[float] = None
    temperature: Optional[float] = None
    vibration_rms: Optional[float] = None
    kurtosis: Optional[float] = None
    crest_factor: Optional[float] = None
    dominant_frequency: Optional[float] = None
    health_score: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    machine_id: int
    severity: str = "MEDIUM"
    alert_type: str = "VIBRATION"
    title: str
    description: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    recommended_action: Optional[str] = None


class AlertUpdate(BaseModel):
    status: Optional[str] = None


class AlertOut(BaseModel):
    id: int
    machine_id: int
    severity: str
    alert_type: str
    title: str
    description: Optional[str] = None
    confidence: Optional[float] = None
    status: str
    evidence: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Maintenance ───────────────────────────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    machine_id: int
    engineer_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    maintenance_type: str = "Inspection"
    description: Optional[str] = None
    factory_notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    status: Optional[str] = None
    engineer_notes: Optional[str] = None
    factory_notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class MaintenanceOut(BaseModel):
    id: int
    machine_id: int
    engineer_id: Optional[int] = None
    scheduled_by: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    maintenance_type: str
    description: Optional[str] = None
    status: str
    engineer_notes: Optional[str] = None
    factory_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Engineer Recommendations ──────────────────────────────────────────────────

class RecommendationCreate(BaseModel):
    machine_id: int
    maintenance_id: Optional[int] = None
    recommendation: str
    priority: str = "MEDIUM"


class RecommendationOut(BaseModel):
    id: int
    machine_id: int
    engineer_id: int
    maintenance_id: Optional[int] = None
    recommendation: str
    priority: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    recipient_id: int
    machine_id: Optional[int] = None
    alert_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    type: str
    title: str
    message: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    id: int
    machine_id: int
    alert_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    report_type: str
    trigger_event: Optional[str] = None
    ai_result: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Assignments ───────────────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    engineer_id: int
    machine_id: int


class AssignmentOut(BaseModel):
    id: int
    engineer_id: int
    machine_id: int
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[int] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    machine_id: Optional[int] = None
    action: str
    description: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
