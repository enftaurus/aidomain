# MachSense — Predictive Maintenance Platform

MachSense is an engineer-in-the-loop predictive maintenance platform for rotating machinery.

> **AI recommends. Humans decide.**

---

## Quick Start

### 1. Launch MachSense Application

Run `./dev.sh` from the repository root:

```bash
./dev.sh
```

- **FastAPI Backend**: `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
- **Next.js Frontend**: `http://localhost:3000`

---

## Configured Credentials

| Role | Email | Password |
|---|---|---|
| **Plant Admin** | `1602-24-733-160@vce.ac.in` | `admin123` |
| **Lead Engineer** | `1602-24-748-062@vce.ac.in` | `engineer123` |

---

## Key Modules & Features

- **ESP32 Wi-Fi Streaming**: Dedicated `/esp32/stream` endpoint for ESP32 time-series hardware data.
- **Explainable Signal Analytics**: Real-time vibration RMS, Kurtosis, Crest Factor, and RPM monitoring.
- **Engineer-in-the-Loop Decisions**: Human-controlled manual shutdowns and scheduled maintenance.
- **AI PDF & Email Reports**: Automated condition report generation powered by LangChain + Groq LLM and dispatched via Zoho SMTP.
