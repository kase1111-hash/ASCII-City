@echo off
REM ============================================
REM ShadowEngine Build Script for Windows
REM ============================================
REM This script sets up the Python environment
REM and installs all dependencies.
REM ============================================

echo.
echo ========================================
echo    ShadowEngine Build Setup
echo ========================================
echo.

REM Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10 or later.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10 or later is required.
    python --version
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.
echo.

REM Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] pip upgraded.
echo.

REM Install dependencies
echo [*] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some optional dependencies may have failed.
    echo Core game should still work.
)
echo [OK] Dependencies installed.
echo.

REM Run tests to verify installation
echo [*] Running tests to verify installation...
set PYTHONPATH=%CD%\src
python -m pytest --tb=no -q 2>nul
if %errorlevel% equ 0 (
    echo [OK] All tests passed!
) else (
    echo [WARNING] Some tests may have failed.
)
echo.

REM Check for Ollama (optional)
echo [*] Checking for Ollama (optional LLM support)...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama found. LLM features available.
    echo     To use: ollama run llama3.2
) else (
    echo [INFO] Ollama not found. Game will use fallback responses.
    echo     Install from: https://ollama.ai
)
echo.

echo ========================================
echo    Build Complete!
echo ========================================
echo.
echo To run the game, use: run.bat
echo Or: python main.py
echo.
pause
