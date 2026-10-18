@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   PII-Shield - Demo Environment Launcher
echo   IBM Z Datathon 2026 - AI Secured: Innovation Without Exposure
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "DEMO_HTML=%SCRIPT_DIR%extension\demo\demo.html"
set "BACKEND_URL=http://127.0.0.1:8000/health"
set "DASHBOARD_URL=http://127.0.0.1:5173"

:: 1. Check Python virtual environment
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Please run: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: 2. Check if Backend is already running
echo [*] Checking Backend status on http://127.0.0.1:8000 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod -Uri '%BACKEND_URL%' -TimeoutSec 2; if ($r.status -eq 'healthy') { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend is already running and healthy.
) else (
    echo [*] Starting FastAPI backend on http://127.0.0.1:8000 ...
    start "PII-Shield Backend" /min "%VENV_PYTHON%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info
    
    :: Wait for backend to report healthy
    set /a RETRIES=0
    :WAIT_BACKEND
    timeout /t 1 /nobreak >nul
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod -Uri '%BACKEND_URL%' -TimeoutSec 2; if ($r.status -eq 'healthy') { exit 0 } else { exit 1 } } catch { exit 1 }"
    if %ERRORLEVEL% equ 0 (
        echo [OK] Backend is ready.
    ) else (
        set /a RETRIES+=1
        if !RETRIES! lss 15 (
            goto :WAIT_BACKEND
        ) else (
            echo [WARN] Backend took longer than expected to report ready.
        )
    )
)

:: 3. Check if Dashboard is already running
echo [*] Checking Vite Dashboard on http://127.0.0.1:5173 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri '%DASHBOARD_URL%' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% equ 0 (
    echo [OK] Dashboard is already running.
) else (
    echo [*] Starting Vite Dashboard on http://127.0.0.1:5173 ...
    start "PII-Shield Dashboard" /min cmd /c "cd /d ""%SCRIPT_DIR%dashboard"" && npx vite --host 127.0.0.1 --port 5173"
    timeout /t 2 /nobreak >nul
)

:: 4. Open URLs in browser
echo.
echo [*] Launching Demo Interfaces...
start "" "%DASHBOARD_URL%"
start "" "%DEMO_HTML%"

echo.
echo ============================================================
echo   PII-Shield is ready!
echo.
echo   - Backend Health:   http://127.0.0.1:8000/api/v1/health
echo   - API Documentation: http://127.0.0.1:8000/docs
echo   - Admin Dashboard:  http://127.0.0.1:5173
echo   - Extension Demo:   %DEMO_HTML%
echo.
echo   To install the unpacked Chrome Extension:
echo     1. Open Chrome and navigate to: chrome://extensions/
echo     2. Toggle ON "Developer mode" in the top-right corner.
echo     3. Click "Load unpacked" and select:
echo        %SCRIPT_DIR%extension
echo ============================================================
echo.
