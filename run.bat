@echo off
title ATLAS Master Launcher
echo ======================================================
echo    ATLAS COGNITIVE SYSTEM - QUICK SERVICES LAUNCHER
echo ======================================================
echo.

:: -------------------------------------------------------
:: STEP 0: Kill ANY zombie Python processes holding port 5000
:: This is the ROOT CAUSE of "connection refused" errors
:: when reopening the project. Old Flask processes linger
:: as zombies and block the port for the new instance.
:: -------------------------------------------------------
echo [0/2] Cleaning up stale backend processes on port 5000...
for /f "tokens=5" %%a in ('netstat -o -n -a ^| findstr "LISTENING" ^| findstr "127.0.0.1:5000"') do (
    echo       Killing zombie process PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
:: Also kill any lingering python processes running app.py
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq ATLAS Backend Service" /NH 2^>nul ^| findstr /I "python"') do (
    echo       Killing stale ATLAS backend PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
:: Give the OS a moment to release the port
timeout /t 2 /nobreak > nul

:: -------------------------------------------------------
:: STEP 1: Start a FRESH Flask backend (always fresh start)
:: -------------------------------------------------------
echo [1/2] Spinning up Flask REST API Backend in background...
start /min "ATLAS Backend Service" "venv\Scripts\python.exe" "backend\app.py"
echo       Flask server process launched.

:: Wait for Flask to bind to port 5000 (up to 15 seconds)
echo       Waiting for Flask to accept connections...
set /a retries=0
:wait_loop
timeout /t 1 /nobreak > nul
set /a retries+=1
netstat -o -n -a | findstr "LISTENING" | findstr "127.0.0.1:5000" > nul
if %errorlevel% equ 0 (
    echo       Flask REST API is now listening on port 5000.
    goto :flask_ready
)
if %retries% lss 15 goto :wait_loop
echo       [WARNING] Flask did not bind within 15 seconds. Opening frontend anyway...

:flask_ready
:: -------------------------------------------------------
:: STEP 2: Launch the frontend interface
:: -------------------------------------------------------
echo [2/2] Launching premium frontend interface...
start "" "frontend\index.html"

echo.
echo ======================================================
echo    ATLAS COGNITIVE SERVICES ARE FULLY ONLINE!
echo ======================================================
echo    NOTE: The backend may still be loading ML models.
echo    The frontend will show boot progress automatically.
echo    Wait for "ATLAS PIPELINE ACTIVE" before querying.
echo ======================================================
echo.
pause