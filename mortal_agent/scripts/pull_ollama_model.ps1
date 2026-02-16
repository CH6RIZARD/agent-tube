# Pull the Ollama model used by the agent (llama3.2:1b only).
# Run: .\scripts\pull_ollama_model.ps1

param([string]$Model = "llama3.2:1b")

$Paths = @(
    "D:\Ollama\ollama.exe",
    "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    "${env:ProgramFiles}\Ollama\ollama.exe",
    "${env:ProgramFiles(x86)}\Ollama\ollama.exe"
)

$OllamaExe = $null
foreach ($p in $Paths) {
    if ($p -and (Test-Path $p)) {
        $OllamaExe = $p
        break
    }
}

if (-not $OllamaExe) {
    Write-Host "Ollama not found. Install first: .\scripts\install_ollama_to_d.ps1" -ForegroundColor Red
    exit 1
}

$MaxRetries = 5
$RetryDelaySeconds = 60

for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
    Write-Host "Pulling $Model with $OllamaExe (attempt $attempt of $MaxRetries) ..." -ForegroundColor Cyan
    $output = & $OllamaExe pull $Model 2>&1
    $exitCode = $LASTEXITCODE
    $outText = $output | Out-String

    if ($exitCode -eq 0) {
        Write-Host "Pull succeeded." -ForegroundColor Green
        exit 0
    }

    $isRateLimit = $outText -match "429|Rate exceeded"
    if ($isRateLimit -and $attempt -lt $MaxRetries) {
        Write-Host "Rate limited (429). Waiting $RetryDelaySeconds seconds before retry ..." -ForegroundColor Yellow
        Start-Sleep -Seconds $RetryDelaySeconds
        $RetryDelaySeconds = [Math]::Min(300, $RetryDelaySeconds + 30)
        continue
    }

    $output | Write-Host
    exit $exitCode
}
