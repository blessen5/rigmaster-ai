@echo off
REM RigMaster AI Auto-Startup Script
REM Automatically starts Ollama and your app

echo ====================================================================
echo   RIGMASTER AI - AUTO STARTUP
echo ====================================================================
echo.

REM Step 1: Check if Ollama is running
echo [1/4] Checking Ollama service...

tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo       [OK] Ollama is already running
) else (
    echo       [!] Ollama is not running. Starting it now...
    start /MIN ollama serve
    echo       [!] Waiting for Ollama to start...
    timeout /t 5 /nobreak >NUL
    echo       [OK] Ollama started
)

echo.

REM Step 2: Warm up models (optional, comment out if you want to skip)
echo [2/4] Warming up AI models...
echo       This takes about 40 seconds...
echo.

python warm_up_models.py

echo.

REM Step 3: Start the app
echo [3/4] Starting RigMaster AI...
echo.
echo ====================================================================
echo.

python app.py

REM Step 4: Cleanup message
echo.
echo ====================================================================
echo   RigMaster AI has stopped
echo ====================================================================
echo.

pause
