@echo off
echo ============================================================
echo   Bus App - Backend (FastAPI)
echo   URL: http://localhost:8080
echo   API Docs: http://localhost:8080/docs
echo   Health: http://localhost:8080/api/health
echo ============================================================

cd /d "%~dp0backend"

:: Check if virtual environment exists
if not exist "env\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv env
)

:: Install / update dependencies
echo [INFO] Installing dependencies...
env\Scripts\pip.exe install -r requirements.txt --quiet

:: Start server
echo [INFO] Starting backend server...
env\Scripts\python.exe main.py

pause
