"""
MachSense FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db, SessionLocal
from app.db.seed import seed_db

from app.routers import (
    auth,
    machines,
    engineers,
    alerts,
    maintenance,
    notifications,
    reports,
    telemetry,
    recommendations,
    audit,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB and seed defaults."""
    logger.info("MachSense starting up...")
    init_db()
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
    settings.ensure_report_dir()
    logger.info("MachSense ready.")
    yield
    logger.info("MachSense shutting down.")


app = FastAPI(
    title="MachSense API",
    description="Engineer-in-the-loop predictive maintenance platform for rotating machinery.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(engineers.router)
app.include_router(alerts.router)
app.include_router(maintenance.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(telemetry.router)
app.include_router(recommendations.router)
app.include_router(audit.router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "MachSense API", "version": "2.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
