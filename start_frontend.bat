@echo off
echo ============================================================
echo   Bus App - Frontend (React + Vite)
echo   URL: http://localhost:3000
echo   LAN: Check your IP with "ipconfig" and use http://<IP>:3000
echo ============================================================

cd /d "%~dp0frontend"

:: Install node_modules if missing
if not exist "node_modules" (
    echo [INFO] Installing npm dependencies...
    npm install
)

:: Start dev server
echo [INFO] Starting frontend dev server...
npm run dev

pause
