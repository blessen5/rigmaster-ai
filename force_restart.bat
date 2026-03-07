@echo off
echo ========================================
echo   FORCE RESTART RIGMASTER AI
echo ========================================
echo.

echo [1/3] Killing ALL Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Waiting for ports to clear...
timeout /t 3 /nobreak >nul

echo [3/3] Starting RigMaster AI with UPDATED code...
echo.
echo ========================================
echo   Access at: http://localhost:5005
echo ========================================
echo.

start "RigMaster-AI-Server" cmd /k "python app.py"

echo.
echo ✅ Server started in new window!
echo    Check the new window for startup logs.
echo.
pause
