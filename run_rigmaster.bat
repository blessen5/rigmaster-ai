@echo off
set VERSION=8.2
set MONGO_PATH="C:\Program Files\MongoDB\Server\%VERSION%\bin\mongod.exe"
set DB_PATH="C:\data\db"

echo ====================================================================
echo   🚀 RIGMASTER AI - SUPER STARTUP (Port 5005)
echo ====================================================================
echo.

REM Step 1: Start MongoDB
echo [1/4] Checking MongoDB...
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo       [OK] MongoDB is already running.
) else (
    echo       [!] Starting MongoDB...
    start "RigMaster-DB-Engine" /MIN %MONGO_PATH% --dbpath %DB_PATH%
    timeout /t 3 /nobreak >NUL
)

echo.

REM Step 2: Consolidate Database
echo [2/4] Optimizing Component Database...
python consolidate_db.py
echo       [OK] Database consolidated.

echo.

REM Step 3: Check for Ollama
echo [3/4] Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    start /MIN ollama serve
    timeout /t 3 /nobreak >NUL
)

echo.

REM Step 4: Start RigMaster
echo [4/4] Starting RigMaster AI...
echo ====================================================================
echo   Web Interface will be at: http://127.0.0.1:5005
echo ====================================================================
echo.

python app.py
pause
