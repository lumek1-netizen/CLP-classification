@echo off
REM Spusti novy PowerShell s aktivovanym virtualnim prostredim
powershell -NoExit -ExecutionPolicy Bypass -Command ". .\venv\Scripts\Activate.ps1; Write-Host 'Virtualni prostredi aktivovano' -ForegroundColor Green"
