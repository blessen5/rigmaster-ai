# Ollama Multi-Model Setup Script for Windows PowerShell
# This script will pull all fast models for RigMaster AI

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " OLLAMA MULTI-MODEL SETUP" -ForegroundColor Cyan
Write-Host " Setting up 4 fast models with NO rate limits!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
try {
    $null = Get-Command ollama -ErrorAction Stop
    Write-Host "[OK] Ollama is installed" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Ollama not found!" -ForegroundColor Red
    Write-Host "Please install Ollama from: https://ollama.ai" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Define models to install
$models = @(
    @{Name = "llama3.2:1b"; Description = "Meta - 1.3GB"; Provider = "Meta" },
    @{Name = "phi3:mini"; Description = "Microsoft - 2.3GB"; Provider = "Microsoft" },
    @{Name = "gemma2:2b"; Description = "Google - 1.6GB"; Provider = "Google" },
    @{Name = "qwen2.5:1.5b"; Description = "Alibaba - 1.0GB"; Provider = "Alibaba" }
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DOWNLOADING MODELS (This may take 10-20 minutes)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$installed = @()
$failed = @()

for ($i = 0; $i -lt $models.Count; $i++) {
    $model = $models[$i]
    $num = $i + 1
    
    Write-Host "[$num/4] Pulling $($model.Name) ($($model.Description))..." -ForegroundColor Yellow
    
    try {
        & ollama pull $model.Name 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $($model.Name) installed successfully!" -ForegroundColor Green
            $installed += $model.Name
        }
        else {
            Write-Host "[WARNING] Failed to pull $($model.Name)" -ForegroundColor Red
            $failed += $model.Name
        }
    }
    catch {
        Write-Host "[ERROR] Exception pulling $($model.Name): $_" -ForegroundColor Red
        $failed += $model.Name
    }
    
    Write-Host ""
}

# Show installed models
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INSTALLED MODELS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

& ollama list

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SETUP SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Successfully installed: $($installed.Count)/$($models.Count) models" -ForegroundColor $(if ($installed.Count -eq $models.Count) { "Green" } else { "Yellow" })

if ($installed.Count -gt 0) {
    Write-Host "`nInstalled models:" -ForegroundColor Green
    foreach ($m in $installed) {
        Write-Host "  ✓ $m" -ForegroundColor Green
    }
}

if ($failed.Count -gt 0) {
    Write-Host "`nFailed models:" -ForegroundColor Red
    foreach ($m in $failed) {
        Write-Host "  ✗ $m" -ForegroundColor Red
    }
    Write-Host "`nYou can retry failed models manually:" -ForegroundColor Yellow
    foreach ($m in $failed) {
        Write-Host "  ollama pull $m" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BENEFITS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your RigMaster AI now has:" -ForegroundColor White
Write-Host "  ✓ $($installed.Count) fast Ollama models" -ForegroundColor Green
Write-Host "  ✓ Automatic model rotation" -ForegroundColor Green
Write-Host "  ✓ UNLIMITED requests (no rate limits!)" -ForegroundColor Green
Write-Host "  ✓ 1-3 second response times" -ForegroundColor Green
Write-Host "  ✓ 100% private & local processing" -ForegroundColor Green
Write-Host "  ✓ Completely FREE forever" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NEXT STEPS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Make sure Ollama is running:" -ForegroundColor Yellow
Write-Host "   ollama serve" -ForegroundColor White
Write-Host ""
Write-Host "2. Start your RigMaster AI app:" -ForegroundColor Yellow
Write-Host "   python app.py" -ForegroundColor White
Write-Host ""
Write-Host "3. Make PC recommendations and enjoy unlimited AI!" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"
