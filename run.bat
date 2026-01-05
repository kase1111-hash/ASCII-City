@echo off
REM ============================================
REM ShadowEngine Run Script for Windows
REM ============================================
REM Starts the game with proper environment.
REM ============================================

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Set Python path
set PYTHONPATH=%CD%\src

REM Check for command line arguments
if "%1"=="--test" goto :runtest
if "%1"=="--ollama" goto :checkollama
if "%1"=="--help" goto :showhelp
goto :rungame

:showhelp
echo.
echo ShadowEngine - A Procedural ASCII Storytelling Game
echo.
echo Usage: run.bat [option]
echo.
echo Options:
echo   (none)     Run the game
echo   --test     Run the test suite
echo   --ollama   Check Ollama status and run game
echo   --help     Show this help message
echo.
goto :eof

:runtest
echo Running tests...
python -m pytest -v
goto :eof

:checkollama
echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is running.
    echo Available models:
    curl -s http://localhost:11434/api/tags 2>nul | findstr /i "name"
) else (
    echo [WARNING] Ollama is not running.
    echo Starting Ollama...
    start /min ollama serve
    timeout /t 3 >nul
)
goto :rungame

:rungame
echo.
echo ========================================
echo         Starting ShadowEngine
echo ========================================
echo.

REM Run the game
python main.py

REM Exit code handling
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Game exited with error code %errorlevel%
    pause
)
