#!/usr/bin/env bash
# ============================================================
# MachSense Development Environment Launcher
# Usage: ./dev.sh
# Starts FastAPI (port 8000) + Next.js (port 3000)
# ============================================================

set -e

# ── Colours ──────────────────────────────────────────────────
RESET='\033[0m'
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'

log()  { echo -e "${BOLD}${CYAN}[MachSense]${RESET} $*"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }
err()  { echo -e "${RED}✗${RESET}  $*" >&2; }

# Track child process PIDs
FASTAPI_PID=""
NEXTJS_PID=""

# ── Cleanup on exit ──────────────────────────────────────────
cleanup() {
    # Disarm trap immediately to prevent recursive loop
    trap - EXIT INT TERM
    echo ""
    log "Shutting down MachSense services..."

    if [ -n "$FASTAPI_PID" ] && kill -0 "$FASTAPI_PID" 2>/dev/null; then
        kill "$FASTAPI_PID" 2>/dev/null || true
    fi

    if [ -n "$NEXTJS_PID" ] && kill -0 "$NEXTJS_PID" 2>/dev/null; then
        kill "$NEXTJS_PID" 2>/dev/null || true
    fi

    # Terminate any remaining child processes of this script
    pkill -P $$ 2>/dev/null || true
    
    ok "All services stopped cleanly."
    exit 0
}

trap cleanup EXIT INT TERM

# ── Banner ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  MachSense Development Environment${RESET}"
echo "  ─────────────────────────────────────────"
echo ""

# ── Root detection ───────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend/machsense"
VENV_DIR="$SCRIPT_DIR/venv"

# ── Prerequisite checks ──────────────────────────────────────
log "Checking prerequisites..."

if [ ! -d "$VENV_DIR" ]; then
    err "Python venv not found at $VENV_DIR"
    err "Run: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi
ok "Python venv: $VENV_DIR"

if [ ! -f "$BACKEND_DIR/.env" ]; then
    warn ".env not found — copying from .env.example"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env" 2>/dev/null || true
fi
ok "Backend .env: present"

# Detect frontend package manager (prefer pnpm, fall back to npm)
if [ -f "$FRONTEND_DIR/pnpm-lock.yaml" ] && command -v pnpm &>/dev/null; then
    PKG_MANAGER="pnpm"
elif command -v npm &>/dev/null; then
    PKG_MANAGER="npm"
else
    err "No package manager found (tried pnpm, npm)"
    exit 1
fi
ok "Frontend package manager: $PKG_MANAGER"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    log "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && $PKG_MANAGER install)
fi
ok "Frontend dependencies: installed"

echo ""
echo -e "  ${BOLD}Starting FastAPI${RESET}  → http://localhost:8000"
echo -e "  ${BOLD}Starting Next.js${RESET}  → http://localhost:3000"
echo -e "  ${BOLD}API Docs${RESET}          → http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo ""

# ── Start FastAPI ────────────────────────────────────────────
# Ensure port 8000 is free before starting uvicorn
fuser -k 8000/tcp 2>/dev/null || true

(
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    exec uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 2>&1 | sed "s/^/  ${CYAN}[FastAPI]${RESET}  /"
) &

FASTAPI_PID=$!

# Brief pause to let FastAPI initialize
sleep 2

# ── Start Next.js ────────────────────────────────────────────
(
    cd "$FRONTEND_DIR"
    exec $PKG_MANAGER run dev 2>&1 | sed "s/^/  ${GREEN}[Next.js]${RESET}  /"
) &

NEXTJS_PID=$!

log "Both services started. Waiting..."
wait $FASTAPI_PID $NEXTJS_PID 2>/dev/null || true
