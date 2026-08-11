from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from app.db.database import Base


class EngineerMachineAssignment(Base):
    __tablename__ = "engineer_machine_assignments"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
