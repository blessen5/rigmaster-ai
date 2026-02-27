@echo off
REM Ollama Multi-Model Setup Script for Windows
REM This script will pull all fast models for RigMaster AI

echo ============================================================
echo  OLLAMA MULTI-MODEL SETUP
echo  Setting up 4 fast models with NO rate limits!
echo ============================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ollama not found!
    echo Please install Ollama from: https://ollama.ai
    pause
    exit /b 1
)

echo [OK] Ollama is installed
echo.

REM Pull all models
echo ============================================================
echo  DOWNLOADING MODELS (This may take 10-20 minutes)
echo ============================================================
echo.

echo [1/4] Pulling llama3.2:1b (Meta - 1.3GB)...
ollama pull llama3.2:1b
if %ERRORLEVEL% EQU 0 (
    echo [OK] llama3.2:1b installed successfully!
) else (
    echo [WARNING] Failed to pull llama3.2:1b
)
echo.

echo [2/4] Pulling phi3:mini (Microsoft - 2.3GB)...
ollama pull phi3:mini
if %ERRORLEVEL% EQU 0 (
    echo [OK] phi3:mini installed successfully!
) else (
    echo [WARNING] Failed to pull phi3:mini
)
echo.

echo [3/4] Pulling gemma2:2b (Google - 1.6GB)...
ollama pull gemma2:2b
if %ERRORLEVEL% EQU 0 (
    echo [OK] gemma2:2b installed successfully!
) else (
    echo [WARNING] Failed to pull gemma2:2b
)
echo.

echo [4/4] Pulling qwen2.5:1.5b (Alibaba - 1.0GB)...
ollama pull qwen2.5:1.5b
if %ERRORLEVEL% EQU 0 (
    echo [OK] qwen2.5:1.5b installed successfully!
) else (
    echo [WARNING] Failed to pull qwen2.5:1.5b
)
echo.

REM Show installed models
echo ============================================================
echo  INSTALLED MODELS
echo ============================================================
echo.
ollama list
echo.

echo ============================================================
echo  SETUP COMPLETE!
echo ============================================================
echo.
echo Your RigMaster AI now has:
echo   - 4 fast Ollama models
echo   - Automatic model rotation
echo   - UNLIMITED requests (no rate limits!)
echo   - 1-3 second response times
echo.
echo Next steps:
echo   1. Make sure Ollama is running: ollama serve
echo   2. Start your app: python app.py
echo   3. Make PC recommendations and enjoy unlimited AI!
echo.
pause
