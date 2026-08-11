from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from app.db.database import Base


class EngineerRecommendation(Base):
    __tablename__ = "engineer_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id"), nullable=True)

    recommendation = Column(Text, nullable=False)

    # LOW | MEDIUM | HIGH | URGENT
    priority = Column(String(20), nullable=False, default="MEDIUM")

    # PENDING | ACKNOWLEDGED | ACTIONED
    status = Column(String(20), nullable=False, default="PENDING")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
