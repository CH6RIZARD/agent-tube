# Start Ollama server using full path (no PATH needed).
# Run: .\scripts\start_ollama.ps1
# Leave this window open while using the agent.

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
    Write-Host "Ollama not found. Install it first:" -ForegroundColor Red
    Write-Host "  .\scripts\install_ollama_to_d.ps1" -ForegroundColor Yellow
    Write-Host "Or download from https://ollama.com/download and install to D:\Ollama" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Ollama: $OllamaExe serve" -ForegroundColor Cyan
Write-Host "Leave this window open. In another terminal run:  & '$OllamaExe' pull llama3.2:1b" -ForegroundColor Gray
& $OllamaExe serve
