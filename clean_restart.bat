@echo off
echo Killing ALL Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 3 /nobreak >nul

echo.
echo Starting Flask with Price Tracker...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python app.py
