# Pull the Ollama model (if needed), then run the agent.
# Run from mortal_agent: .\scripts\run_agent_with_ollama.ps1
# Or from repo root: .\mortal_agent\scripts\run_agent_with_ollama.ps1

param([string]$Model = "llama3.2:1b")

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MortalAgentRoot = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $MortalAgentRoot

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

# Start Ollama in background if not already responding
$base = "http://localhost:11434"
$ok = $false
try {
    $r = Invoke-WebRequest -Uri "$base/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $ok = $true
} catch {}

if (-not $ok) {
    Write-Host "Starting Ollama in background ..." -ForegroundColor Cyan
    Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WindowStyle Hidden
    $max = 15
    for ($i = 0; $i -lt $max; $i++) {
        Start-Sleep -Seconds 1
        try {
            $null = Invoke-WebRequest -Uri "$base/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            Write-Host "Ollama is up." -ForegroundColor Green
            break
        } catch {
            if ($i -eq $max - 1) {
                Write-Host "Ollama did not start in time. Run .\scripts\start_ollama.ps1 in another window, then run this again." -ForegroundColor Red
                exit 1
            }
        }
    }
}

# Pull model (retry on 429 rate limit)
$MaxRetries = 5
$RetryDelaySeconds = 60
$pullOk = $false
for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
    Write-Host "Pulling model: $Model (attempt $attempt of $MaxRetries) ..." -ForegroundColor Cyan
    $pullOut = & $OllamaExe pull $Model 2>&1
    $pullExit = $LASTEXITCODE
    $pullText = $pullOut | Out-String

    if ($pullExit -eq 0) {
        $pullOk = $true
        break
    }

    $isRateLimit = $pullText -match "429|Rate exceeded"
    if ($isRateLimit -and $attempt -lt $MaxRetries) {
        Write-Host "Rate limited (429). Waiting $RetryDelaySeconds seconds before retry ..." -ForegroundColor Yellow
        Start-Sleep -Seconds $RetryDelaySeconds
        $RetryDelaySeconds = [Math]::Min(300, $RetryDelaySeconds + 30)
        continue
    }

    $pullOut | Write-Host
    Write-Host "Pull failed. Fix errors above and try again." -ForegroundColor Red
    exit 1
}
if (-not $pullOk) { exit 1 }

# Run agent from repo root
$env:MODEL_NAME = $Model
Write-Host "Running agent (MODEL_NAME=$Model) ..." -ForegroundColor Cyan
Set-Location $RepoRoot
python -m cli run --observer
