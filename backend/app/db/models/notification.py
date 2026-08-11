from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id"), nullable=True)

    # ALERT | MAINTENANCE | ASSIGNMENT | REPORT | SHUTDOWN | SYSTEM
    type = Column(String(30), nullable=False, default="SYSTEM")
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
