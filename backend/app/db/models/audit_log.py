from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)

    action = Column(String(100), nullable=False)       # e.g. MACHINE_SHUTDOWN_CONFIRMED
    description = Column(Text, nullable=True)
    previous_state = Column(Text, nullable=True)       # JSON
    new_state = Column(Text, nullable=True)            # JSON
    metadata_json = Column(Text, nullable=True)        # JSON — extra context

    created_at = Column(DateTime(timezone=True), server_default=func.now())
