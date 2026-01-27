@echo off
REM Presun do korenoveho adresare projektu
cd /d "%~dp0.."

echo ========================================
echo CLP Calculator - Waitress WSGI Server
echo ========================================
echo.

REM Zkontroluj, ze jsme v projektu
if not exist "wsgi.py" (
    echo ERROR: wsgi.py not found in project root!
    pause
    exit /b 1
)

REM Zkontroluj, ze existuje venv
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

REM Aktivuj virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Zkontroluj, ze Waitress je nainstalovan
python -c "import waitress" 2>nul
if errorlevel 1 (
    echo ERROR: Waitress is not installed!
    echo Installing Waitress...
    pip install waitress==3.0.2
)

REM Nastav environment
set FLASK_ENV=development

echo.
echo Starting Waitress server...
echo Server: http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

REM Spus Waitress
python -m waitress --host=127.0.0.1 --port=8000 --threads=4 --channel-timeout=30 wsgi:app
