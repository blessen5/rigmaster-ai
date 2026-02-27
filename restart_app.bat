@echo off
echo Restarting Flask app with Price Tracker routes...
echo.

REM Kill existing Python processes
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start the app
echo Starting RigMaster AI...
cd /d "%~dp0"
call .venv\Scripts\activate
python app.py
