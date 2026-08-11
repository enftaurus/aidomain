from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from app.db.database import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    rpm = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    accel_x = Column(Float, nullable=True)
    accel_y = Column(Float, nullable=True)
    accel_z = Column(Float, nullable=True)
    vibration_rms = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    crest_factor = Column(Float, nullable=True)
    dominant_frequency = Column(Float, nullable=True)
    health_score = Column(Float, nullable=True)
