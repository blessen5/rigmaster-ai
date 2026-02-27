# RigMaster AI Startup Script with Auto Ollama
# This script automatically starts Ollama, warms up models, and starts your app

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "  🚀 RIGMASTER AI - AUTO STARTUP" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Ollama is running
Write-Host "1️⃣  Checking Ollama service..." -ForegroundColor Yellow

$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue

if ($ollamaProcess) {
    Write-Host "   ✅ Ollama is already running (PID: $($ollamaProcess[0].Id))" -ForegroundColor Green
}
else {
    Write-Host "   ⚠️  Ollama is not running. Starting it now..." -ForegroundColor Yellow
    
    try {
        # Start Ollama in a new window
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
        Write-Host "   ⏳ Waiting for Ollama to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Verify it started
        $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
        if ($ollamaProcess) {
            Write-Host "   ✅ Ollama started successfully!" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ Failed to start Ollama" -ForegroundColor Red
            Write-Host "   Please start Ollama manually: ollama serve" -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    catch {
        Write-Host "   ❌ Error starting Ollama: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""

# Step 2: Check if models need warming up
Write-Host "2️⃣  Checking if models are warm..." -ForegroundColor Yellow

# Quick test to see if models are already warm
try {
    $testStart = Get-Date
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" `
        -Method Post `
        -Body (@{
            model  = "qwen2.5:1.5b"
            prompt = "hi"
            stream = $false
        } | ConvertTo-Json) `
        -ContentType "application/json" `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    $testTime = ((Get-Date) - $testStart).TotalSeconds
    
    if ($testTime -lt 5) {
        Write-Host "   ✅ Models are already warm (response in $([math]::Round($testTime, 1))s)" -ForegroundColor Green
        $needsWarmup = $false
    }
    else {
        Write-Host "   ⚠️  Models need warming up (response took $([math]::Round($testTime, 1))s)" -ForegroundColor Yellow
        $needsWarmup = $true
    }
}
catch {
    Write-Host "   ⚠️  Models need warming up" -ForegroundColor Yellow
    $needsWarmup = $true
}

Write-Host ""

# Step 3: Warm up models if needed
if ($needsWarmup) {
    Write-Host "3️⃣  Warming up models (this takes ~40 seconds)..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        python warm_up_models.py
        Write-Host ""
    }
    catch {
        Write-Host "   ⚠️  Warning: Could not warm up models" -ForegroundColor Yellow
        Write-Host "   Models will warm up on first use (may be slower)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "3️⃣  Skipping warm-up (models already warm)" -ForegroundColor Green
    Write-Host ""
}

# Step 4: Start the RigMaster AI app
Write-Host "4️⃣  Starting RigMaster AI app..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Start the Flask app
python app.py

# If app exits, show message
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "  RigMaster AI has stopped" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
