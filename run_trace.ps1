# TRACE - PowerShell Launcher
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "TRACE - Document-Level MSME Transaction Reconciliation System" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start Frontend
Write-Host "[2/2] Starting React Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot\frontend'; npm run dev"

Write-Host "`nTRACE is now running!" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000 (Swagger: http://localhost:8000/docs)" -ForegroundColor White
