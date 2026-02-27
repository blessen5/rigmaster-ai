# Quick Download - Essential Ollama Models
# Downloads the 6 most important models (balanced speed + quality)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RigMaster AI - Quick Model Setup" -ForegroundColor Cyan
Write-Host "  Downloading 6 Essential FREE Models" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{Name = "qwen2.5:1.5b"; Desc = "Ultra-Fast (13s)"; Size = "~1GB" },
    @{Name = "gemma2:2b"; Desc = "Very Fast (19s)"; Size = "~1.5GB" },
    @{Name = "phi3:mini"; Desc = "Fast + Quality (39s)"; Size = "~2GB" },
    @{Name = "mistral:7b"; Desc = "High Quality (50s)"; Size = "~4GB" },
    @{Name = "llama3.1:8b"; Desc = "Best All-Rounder (55s)"; Size = "~4.5GB" },
    @{Name = "deepseek-r1:7b"; Desc = "Reasoning Expert (60s)"; Size = "~4GB" }
)

Write-Host "This will download 6 essential models (~17GB total)" -ForegroundColor Yellow
Write-Host "Estimated time: 15-30 minutes" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Continue? (Y/N)"
if ($response -ne "Y" -and $response -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
$success = 0
$failed = @()

for ($i = 0; $i -lt $models.Count; $i++) {
    $model = $models[$i]
    $num = $i + 1
    
    Write-Host "[$num/6] Downloading: $($model.Name)" -ForegroundColor Cyan
    Write-Host "      Description: $($model.Desc)" -ForegroundColor Gray
    Write-Host "      Size: $($model.Size)" -ForegroundColor Gray
    
    try {
        ollama pull $model.Name
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      ✅ SUCCESS!" -ForegroundColor Green
            $success++
        }
        else {
            Write-Host "      ❌ FAILED!" -ForegroundColor Red
            $failed += $model.Name
        }
    }
    catch {
        Write-Host "      ❌ ERROR: $_" -ForegroundColor Red
        $failed += $model.Name
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Success: $success/6 models" -ForegroundColor Green

if ($failed.Count -gt 0) {
    Write-Host "❌ Failed: $($failed.Count) models" -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host "   - $f" -ForegroundColor Red
    }
}
else {
    Write-Host ""
    Write-Host "🎉 ALL MODELS DOWNLOADED!" -ForegroundColor Green
    Write-Host "Your RigMaster AI is ready to use 6 FREE AI models!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next: Restart your app with 'python app.py'" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
