@echo off
setlocal

REM Change to project directory
cd /d "%~dp0"

if exist "start_dashboard.ps1" (
  powershell -ExecutionPolicy Bypass -File "start_dashboard.ps1"
  goto :eof
)

REM Control panel display version and one-time lifetime baseline seed
set "HIREJOURNE_CONTROL_PANEL_VERSION=2025.12.18-v1.1"
set "HIREJOURNE_LIFETIME_BASELINE=17683"

REM Start webhook server in a new minimized window
start "HireJourne Webhook Server" /min cmd /k "python -m uvicorn src.app:app --host 0.0.0.0 --port 8080"

REM Delay to let the FastAPI server start listening on port 8080
ping 127.0.0.1 -n 6 >nul

REM Start ngrok in a new minimized window (assumes ngrok is on PATH)
start "ngrok 8080" /min cmd /k "ngrok http 8080"

REM Open the local dashboard in the default browser (server should now be ready)
start "" "http://127.0.0.1:8080/"

endlocal
