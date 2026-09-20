#!/usr/bin/env bash
echo "=============================================================================="
echo "                     Starting TRACE System (Local Mode)                      "
echo "=============================================================================="

# Trap to kill background processes on exit
trap 'kill 0' EXIT

echo "[1/2] Starting TRACE FastAPI Backend on http://localhost:8000 ..."
(cd backend && python -m uvicorn app.main:app --port 8000 --reload) &

sleep 2

echo "[2/2] Starting TRACE React Frontend on http://localhost:5173 ..."
(cd frontend && npm run dev) &

echo "TRACE is running!"
echo "Backend API Docs: http://localhost:8000/docs"
echo "Frontend Web UI:  http://localhost:5173"
echo "Press Ctrl+C to stop all servers."

wait
