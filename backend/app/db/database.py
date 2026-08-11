from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    # Import all models so SQLAlchemy knows about them
    from app.db.models import (  # noqa: F401
        user, machine, telemetry, alert, maintenance,
        engineer_recommendation, notification, report, audit_log,
        engineer_machine_assignment,
    )
    Base.metadata.create_all(bind=engine)
