$path = 'app.py'
$content = Get-Content $path -Raw
$count_p = ([regex]::Matches($content, "(?s)run_power_analysis\(\{.*?\}\)")).Count
$count_v = ([regex]::Matches($content, "(?s)run_validation_logic\(\{.*?\}\)")).Count
Write-Host "Found matches: Power=$count_p, Validation=$count_v"

if ($count_p -gt 0 -or $count_v -gt 0) {
    $content = $content -replace "(?s)run_power_analysis\(\{.*?\}\)", "run_power_analysis(build)"
    $content = $content -replace "(?s)run_validation_logic\(\{.*?\}\)", "run_validation_logic(build)"
    Set-Content -Path $path -Value $content -Encoding UTF8
    Write-Host "Success: app.py updated."
} else {
    Write-Host "Failure: No regex matches found."
}
