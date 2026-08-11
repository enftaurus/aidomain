"""Seed the database with default users and machines."""
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.machine import Machine
from app.core.security import hash_password
from app.core.logging import logger


def seed_db(db: Session) -> None:
    _seed_users(db)
    _seed_machines(db)


def _seed_users(db: Session) -> None:
    # Only keep specified Admin and Engineer emails
    allowed_emails = ["1602-24-733-160@vce.ac.in", "1602-24-748-062@vce.ac.in"]
    
    # Remove any other non-allowed user accounts
    db.query(User).filter(User.email.notin_(allowed_emails)).delete(synchronize_session=False)

    defaults = [
        {"name": "Admin Manager", "email": "1602-24-733-160@vce.ac.in", "password": "admin123", "role": "ADMIN"},
        {"name": "Lead Reliability Engineer", "email": "1602-24-748-062@vce.ac.in", "password": "engineer123", "role": "ENGINEER"},
    ]
    for u in defaults:
        exists = db.query(User).filter(User.email == u["email"]).first()
        if not exists:
            db.add(User(
                name=u["name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                is_active=True,
            ))
    db.commit()
    logger.info("Users seeded.")


def _seed_machines(db: Session) -> None:
    defaults = [
        {"machine_code": "M-001", "name": "Motor Assembly A",   "location": "Assembly / Line A", "machine_type": "Electric Motor"},
        {"machine_code": "M-002", "name": "Hydraulic Pump 12",  "location": "Assembly / Line B", "machine_type": "Hydraulic Pump"},
        {"machine_code": "M-003", "name": "CNC Milling Cell 04","location": "Machining / Line A","machine_type": "CNC Machine"},
        {"machine_code": "M-004", "name": "Air Compressor 07",  "location": "Utilities / Plant 1","machine_type": "Air Compressor"},
    ]
    for m in defaults:
        exists = db.query(Machine).filter(Machine.machine_code == m["machine_code"]).first()
        if not exists:
            db.add(Machine(
                machine_code=m["machine_code"],
                name=m["name"],
                location=m["location"],
                machine_type=m["machine_type"],
                status="RUNNING",
                health_score=94.0,
                rpm=1485.0,
                temperature=54.0,
                vibration_rms=1.7,
                kurtosis=3.2,
                crest_factor=2.8,
            ))
    db.commit()

    # Seed engineer assignments for 1602-24-748-062@vce.ac.in across all machines
    from app.db.models.engineer_machine_assignment import EngineerMachineAssignment
    eng = db.query(User).filter(User.email == "1602-24-748-062@vce.ac.in").first()
    machines = db.query(Machine).all()
    if eng and machines:
        for m in machines:
            existing_ass = db.query(EngineerMachineAssignment).filter(
                EngineerMachineAssignment.engineer_id == eng.id,
                EngineerMachineAssignment.machine_id == m.id,
                EngineerMachineAssignment.is_active == True,
            ).first()
            if not existing_ass:
                db.add(EngineerMachineAssignment(engineer_id=eng.id, machine_id=m.id, is_active=True))
        db.commit()

    logger.info("Machines and assignments seeded.")

