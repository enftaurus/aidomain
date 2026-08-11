from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from app.db.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id"), nullable=True)

    # ENGINEER | ADMIN
    report_type = Column(String(20), nullable=False)

    # Trigger event description
    trigger_event = Column(String(300), nullable=True)

    # Stored AI result (JSON)
    ai_result = Column(Text, nullable=True)

    # Paths to generated files
    html_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
