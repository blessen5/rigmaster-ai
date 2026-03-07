@echo off
echo ============================================================
echo  RESTARTING RIGMASTER AI WITH PRICE TRACKER FEATURE
echo ============================================================
echo.

echo [1/3] Stopping existing Flask processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq RigMaster*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Starting Flask app with new Price Tracker routes...
start "RigMaster AI - Price Tracker" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python app.py"

echo [3/3] Waiting for server to start...
timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo  RESTART COMPLETE!
echo ============================================================
echo.
echo  The Price Tracker feature is now active!
echo  Navigate to: http://localhost:5005/analysis
echo.
echo  New Features Available:
echo   - Real-time component pricing
echo   - Total build cost calculator
echo   - Price insights and recommendations
echo.
pause
