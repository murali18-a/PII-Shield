<#
.SYNOPSIS
    PII-Shield — Start all services (Backend + Dashboard)

.DESCRIPTION
    Starts the FastAPI backend on 127.0.0.1:8000 and the Vite dashboard
    dev server on localhost:5173. Press Ctrl+C to stop both.

.EXAMPLE
    .\start.ps1
    .\start.ps1 -BackendOnly
#>

param(
    [switch]$BackendOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Check prerequisites ──────────────────────────
Write-Host "`n🛡️  PII-Shield — Starting services`n" -ForegroundColor Cyan

# Check Python venv
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "❌ Virtual environment not found. Run:" -ForegroundColor Red
    Write-Host "   python -m venv .venv" -ForegroundColor Yellow
    Write-Host "   .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# ── Start backend ────────────────────────────────
Write-Host "▶ Starting FastAPI backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
$backend = Start-Process -FilePath $VenvPython -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info" -WorkingDirectory $Root -PassThru -NoNewWindow

# Wait for backend to be ready
$retries = 0
$ready = $false
while ($retries -lt 15 -and -not $ready) {
    Start-Sleep -Milliseconds 500
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
        $ready = $true
    } catch {
        $retries++
    }
}

if ($ready) {
    Write-Host "✅ Backend ready" -ForegroundColor Green
} else {
    Write-Host "⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

# ── Start dashboard ──────────────────────────────
$dashboard = $null
if (-not $BackendOnly) {
    $NpmPath = Join-Path $Root "dashboard"
    if (Test-Path (Join-Path $NpmPath "package.json")) {
        Write-Host "▶ Starting dashboard on http://localhost:5173 ..." -ForegroundColor Green
        $dashboard = Start-Process -FilePath "npx" -ArgumentList "vite", "--host", "127.0.0.1" -WorkingDirectory $NpmPath -PassThru -NoNewWindow
        Write-Host "✅ Dashboard starting" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Dashboard package.json not found, skipping" -ForegroundColor Yellow
    }
}

# ── Instructions ─────────────────────────────────
Write-Host "`n────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
if ($dashboard) {
    Write-Host "  Dashboard: http://localhost:5173" -ForegroundColor White
}
Write-Host "  Extension: Load extension/ folder in chrome://extensions/" -ForegroundColor White
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "`nPress Ctrl+C to stop all services`n" -ForegroundColor Cyan

# ── Wait and cleanup ─────────────────────────────
try {
    $backend | Wait-Process
} finally {
    Write-Host "`n🛑 Shutting down..." -ForegroundColor Yellow
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Backend stopped" -ForegroundColor Gray
    }
    if ($dashboard -and -not $dashboard.HasExited) {
        Stop-Process -Id $dashboard.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Dashboard stopped" -ForegroundColor Gray
    }
    Write-Host "👋 All services stopped`n" -ForegroundColor Cyan
}
