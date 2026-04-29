@echo off
:: ============================================================
:: SoulSync AI — Backend Startup Script
:: Enforces virtual environment — will NOT run outside venv
:: ============================================================

setlocal

:: Resolve project root (one level up from soulsync-ai/)
set "PROJECT_ROOT=%~dp0.."
set "VENV_PYTHON=%PROJECT_ROOT%\soulsync_env\Scripts\python.exe"
set "VENV_ACTIVATE=%PROJECT_ROOT%\soulsync_env\Scripts\activate.bat"

echo.
echo  ============================================================
echo   SoulSync AI ^| Backend Startup
echo  ============================================================

:: ── Check venv exists ────────────────────────────────────────
if not exist "%VENV_PYTHON%" (
    echo.
    echo  [ERROR] Virtual environment not found at:
    echo          %PROJECT_ROOT%\soulsync_env\
    echo.
    echo  Create it first:
    echo    python -m venv soulsync_env
    echo    soulsync_env\Scripts\pip install -r soulsync-ai\requirements.txt
    echo.
    pause
    exit /b 1
)

:: ── Check we are NOT already using system Python ─────────────
:: Get the currently active python path
for /f "delims=" %%i in ('where python 2^>nul') do (
    set "ACTIVE_PYTHON=%%i"
    goto :check_done
)
:check_done

:: ── Always use venv Python explicitly ────────────────────────
echo  [OK] Using venv: %VENV_PYTHON%
echo  [OK] Working dir: %~dp0
echo.

:: ── Verify critical packages inside venv ─────────────────────
"%VENV_PYTHON%" -c "import groq, fastapi, uvicorn, psycopg2" 2>nul
if errorlevel 1 (
    echo  [ERROR] Required packages missing from venv.
    echo  Run: soulsync_env\Scripts\pip install -r soulsync-ai\requirements.txt
    echo.
    pause
    exit /b 1
)

echo  [OK] All packages verified in venv
echo  [OK] Starting backend on http://localhost:8000
echo  [OK] Swagger docs at http://localhost:8000/docs
echo.
echo  Press Ctrl+C to stop the server.
echo  ============================================================
echo.

:: ── Start uvicorn using venv Python ──────────────────────────
cd /d "%~dp0"
"%VENV_PYTHON%" -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

endlocal
