# ============================================================
# SoulSync AI — Backend Startup Script (PowerShell)
# Enforces virtual environment — will NOT run outside venv
# ============================================================

$ErrorActionPreference = "Stop"

$ProjectRoot  = Split-Path -Parent $PSScriptRoot
$VenvPython   = Join-Path $ProjectRoot "soulsync_env\Scripts\python.exe"
$VenvPip      = Join-Path $ProjectRoot "soulsync_env\Scripts\pip.exe"
$BackendDir   = $PSScriptRoot

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Cyan
Write-Host "  SoulSync AI | Backend Startup" -ForegroundColor Cyan
Write-Host " ============================================================" -ForegroundColor Cyan

# ── Check venv exists ─────────────────────────────────────────
if (-not (Test-Path $VenvPython)) {
    Write-Host ""
    Write-Host " [ERROR] Virtual environment not found at:" -ForegroundColor Red
    Write-Host "         $ProjectRoot\soulsync_env\" -ForegroundColor Red
    Write-Host ""
    Write-Host " Create it first:" -ForegroundColor Yellow
    Write-Host "   python -m venv soulsync_env"
    Write-Host "   soulsync_env\Scripts\pip install -r soulsync-ai\requirements.txt"
    Write-Host ""
    exit 1
}

# ── Confirm we are using venv Python ──────────────────────────
$VenvPythonResolved = (Resolve-Path $VenvPython).Path
Write-Host " [OK] Venv Python : $VenvPythonResolved" -ForegroundColor Green

# ── Verify critical packages ──────────────────────────────────
Write-Host " [..] Verifying packages in venv..." -ForegroundColor Yellow
try {
    & $VenvPython -c "import groq, fastapi, uvicorn, psycopg2, sentence_transformers, faiss, jose, passlib" 2>&1 | Out-Null
    Write-Host " [OK] All packages verified" -ForegroundColor Green
} catch {
    Write-Host " [ERROR] Missing packages in venv. Run:" -ForegroundColor Red
    Write-Host "   soulsync_env\Scripts\pip install -r soulsync-ai\requirements.txt" -ForegroundColor Yellow
    exit 1
}

# ── Start server ──────────────────────────────────────────────
Write-Host " [OK] Starting backend on http://localhost:8000" -ForegroundColor Green
Write-Host " [OK] Swagger docs  at http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host " Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host " ============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $BackendDir
& $VenvPython -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
