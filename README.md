# MachSense — Predictive Maintenance Platform

MachSense is an engineer-in-the-loop predictive maintenance platform for rotating machinery.

> **AI recommends. Humans decide.**

---

## System Architecture

```text
SQLite
  ↓
FastAPI (Port 8000)
  ↓
Frontend API Integration (Next.js - Port 3000)
  ↓
Alerts & Threshold Evaluation
  ↓
Maintenance Scheduling & Engineer Recommendations
  ↓
In-App Notifications & Audit Trail
  ↓
LangChain + Groq AI Orchestration
  ↓
HTML Report Templates (Engineer & Admin)
  ↓
PDF Generation (xhtml2pdf)
  ↓
Zoho SMTP Email Delivery
```

---

## Quick Start

### 1. Launch Environment

Run `./dev.sh` from the repository root:

```bash
./dev.sh
```

This script will:
- Activate the Python virtual environment (`venv`)
- Detect the frontend package manager (`pnpm` or `npm`)
- Start **FastAPI** on `http://localhost:8000`
- Start **Next.js** on `http://localhost:3000`
- Forward log output from both services cleanly
- Shut down both background processes gracefully on `Ctrl+C`

---

## API Documentation

Once FastAPI is running, view interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Default Seed Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@machsense.demo` | `admin123` |
| **Engineer** | `engineer@machsense.demo` | `engineer123` |
| **Engineer** | `sam@machsense.demo` | `engineer123` |

---

## Key Features & Endpoints

### 1. Auth & Identity
- `POST /auth/login` — OAuth2 JWT token authentication
- `GET /auth/me` — Current user profile

### 2. Machinery & Manual Shutdown
- `GET /machines/` — List all monitored machines
- `POST /machines/{id}/shutdown` — Human-confirmed shutdown (creates audit log, triggers AI report, sends email)
- `POST /machines/{id}/start` — Resume machine operation

### 3. Telemetry Pipeline
- `POST /telemetry/ingest` — Ingest telemetry (source-agnostic: Mock or ESP32)
- `POST /telemetry/mock/{id}?mode=critical` — Inject mock telemetry for simulation (`normal`, `warning`, `critical`)

### 4. Alerts & Maintenance
- `GET /alerts/` & `POST /alerts/` — Manage alerts
- `POST /maintenance/` — Schedule maintenance and notify assigned engineers
- `POST /recommendations/` — Engineers submit maintenance recommendations to admins

### 5. AI Reports, PDFs, & Email Delivery
- `GET /reports/` — View generated report history
- `GET /reports/{id}/download` — Download PDF report
- Reports are rendered using Jinja2 templates (`engineer_report.html` & `admin_report.html`), converted to PDF via `xhtml2pdf`, and emailed via Zoho SMTP with the PDF attached.

### 6. Audit Trail
- `GET /audit/` — Immutable audit log of all human decisions and critical system events

---

## Configuration (`backend/.env`)

Environment settings can be customized in `backend/.env`:

```env
DATABASE_URL=sqlite:///./machsense.db
SECRET_KEY=machsense-dev-secret-key-2026-change-in-production
CORS_ORIGINS=http://localhost:3000

LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_groq_api_key

SMTP_HOST=smtp.zoho.in
SMTP_PORT=587
SMTP_USER=valyrianminds@zohomail.in
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=valyrianminds@zohomail.in

REPORT_OUTPUT_DIR=./generated_reports
```
