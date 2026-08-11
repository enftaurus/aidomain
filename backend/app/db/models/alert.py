from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from app.db.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)

    # INFO | LOW | MEDIUM | HIGH | CRITICAL
    severity = Column(String(20), nullable=False, default="MEDIUM")
    alert_type = Column(String(100), nullable=False, default="VIBRATION")
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    # OPEN | ACKNOWLEDGED | RESOLVED | DISMISSED
    status = Column(String(20), nullable=False, default="OPEN")

    evidence = Column(Text, nullable=True)       # JSON string
    recommended_action = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
