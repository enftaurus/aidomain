from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func
from app.db.database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    machine_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    machine_type = Column(String(100), nullable=True)

    # Status: RUNNING | WARNING | CRITICAL | STOPPING | STOPPED | MAINTENANCE | OFFLINE
    status = Column(String(20), nullable=False, default="RUNNING")

    # Live health snapshot (updated on each telemetry ingest)
    health_score = Column(Float, default=100.0)
    rpm = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    vibration_rms = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    crest_factor = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
