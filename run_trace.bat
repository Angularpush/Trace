@echo off
title TRACE - Starting Full-Stack Application
echo ==============================================================================
echo TRACE - Document-Level MSME Transaction Reconciliation System
echo ==============================================================================
echo.

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

echo [1/3] Checking Python & Node.js environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/3] Starting FastAPI Backend on http://localhost:8000 ...
start "TRACE - Backend Server" cmd /k "cd /d "%PROJECT_ROOT%backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting React Frontend on http://localhost:5173 ...
start "TRACE - Frontend UI" cmd /k "cd /d "%PROJECT_ROOT%frontend" && npm run dev"

echo.
echo ==============================================================================
echo TRACE is starting up!
echo - Frontend: http://localhost:5173
echo - Backend:  http://localhost:8000 (Swagger docs: http://localhost:8000/docs)
echo ==============================================================================
echo.
pause
