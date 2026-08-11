from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from app.db.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scheduled_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    # Inspection | Lubrication | Bearing Replacement | Calibration | General
    maintenance_type = Column(String(100), nullable=False, default="Inspection")
    description = Column(Text, nullable=True)

    # SCHEDULED | IN_PROGRESS | COMPLETED | CANCELLED | OVERDUE
    status = Column(String(20), nullable=False, default="SCHEDULED")

    engineer_notes = Column(Text, nullable=True)
    factory_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
