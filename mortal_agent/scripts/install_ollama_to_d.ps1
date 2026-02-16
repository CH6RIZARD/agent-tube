# Install Ollama to D: drive and prepare for the mortal agent.
# Run in PowerShell: .\scripts\install_ollama_to_d.ps1
# Or from repo root: .\mortal_agent\scripts\install_ollama_to_d.ps1

$ErrorActionPreference = "Stop"
$BaseDir = "D:\OllamaInstall"
$InstallDir = "D:\Ollama"
$InstallScriptUrl = "https://ollama.com/install.ps1"
$SetupUrl = "https://ollama.com/download/OllamaSetup.exe"

# Ensure D: exists
if (-not (Test-Path "D:\")) {
    Write-Host "Drive D: not found. Create it or edit this script to use another path." -ForegroundColor Red
    exit 1
}

# Create folder on D:
New-Item -ItemType Directory -Force -Path $BaseDir | Out-Null
Set-Location $BaseDir

# Download install.ps1 to disk (D:)
Write-Host "Downloading install.ps1 to $BaseDir\install.ps1 ..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $InstallScriptUrl -OutFile "$BaseDir\install.ps1" -UseBasicParsing

# Download OllamaSetup.exe to D:
Write-Host "Downloading OllamaSetup.exe to $BaseDir\OllamaSetup.exe ..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $SetupUrl -OutFile "$BaseDir\OllamaSetup.exe" -UseBasicParsing -MaximumRedirection 5
} catch {
    # Some sites redirect; try alternate
    $SetupUrlAlt = "https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe"
    Write-Host "Trying alternate URL ..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $SetupUrlAlt -OutFile "$BaseDir\OllamaSetup.exe" -UseBasicParsing -MaximumRedirection 5
}

if (-not (Test-Path "$BaseDir\OllamaSetup.exe")) {
    Write-Host "OllamaSetup.exe not found. Download manually from https://ollama.com/download and save to $BaseDir" -ForegroundColor Red
    exit 1
}

# Run installer with install path on D:
Write-Host "Running Ollama installer (install to $InstallDir) ..." -ForegroundColor Cyan
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "$BaseDir\OllamaSetup.exe"
$psi.Arguments = "/DIR=`"$InstallDir`""
$psi.UseShellExecute = $true
[System.Diagnostics.Process]::Start($psi) | Out-Null

Write-Host ""
Write-Host "Installer started. After it finishes:" -ForegroundColor Green
Write-Host "  1. If Ollama was installed to $InstallDir, add to PATH: $InstallDir" -ForegroundColor White
Write-Host "  2. Open a NEW PowerShell and run:  ollama serve" -ForegroundColor White
Write-Host "  3. In another terminal:  ollama pull llama3.2:1b" -ForegroundColor White
    Write-Host "  4. Set env (optional):  `$env:MODEL_NAME = 'llama3.2:1b'" -ForegroundColor White
Write-Host "  5. Run agent:  cd D:\agent;  python -m cli run --observer" -ForegroundColor White
Write-Host ""
Write-Host "Files saved on D:  $BaseDir\install.ps1  and  $BaseDir\OllamaSetup.exe" -ForegroundColor Gray
