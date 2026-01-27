@echo off
REM Presun do korenoveho adresare projektu
cd /d "%~dp0.."

REM Spusti novy PowerShell s aktivovanym virtualnim prostredim
powershell -NoExit -ExecutionPolicy Bypass -Command ". .\venv\Scripts\Activate.ps1; Write-Host 'Virtualni prostredi aktivovano' -ForegroundColor Green"
