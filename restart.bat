@echo off
echo ========================================
echo   RESTARTING RIGMASTER AI
echo ========================================
echo.

echo [1/2] Stopping existing Flask processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq RigMaster*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/2] Starting RigMaster AI on port 5001...
echo.
echo ========================================
echo   Access at: http://localhost:5001
echo ========================================
echo.

python app.py
pause
