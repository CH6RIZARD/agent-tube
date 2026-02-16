# Ollama on Windows (install to D: and run the agent)

The agent uses **Ollama** for LLM inference by default. Install Ollama on Windows and run the agent as follows.

## 1. Download and install Ollama to D:

From PowerShell (run as Administrator if you want to install for all users):

```powershell
cd D:\agent\mortal_agent
.\scripts\install_ollama_to_d.ps1
```

This script:

- Saves `https://ollama.com/install.ps1` to **D:\OllamaInstall\install.ps1**
- Downloads **OllamaSetup.exe** to **D:\OllamaInstall\OllamaSetup.exe**
- Runs the installer with install path **D:\Ollama**

If the download URL fails, get the installer manually from [ollama.com/download](https://ollama.com/download) and run it with:

```powershell
D:\OllamaInstall\OllamaSetup.exe /DIR="D:\Ollama"
```

## 2. Start Ollama (no PATH needed)

In PowerShell from `mortal_agent`:

```powershell
cd D:\agent\mortal_agent
.\scripts\start_ollama.ps1
```

Leave that window open. The script finds `ollama.exe` in `D:\Ollama`, or in `%LOCALAPPDATA%\Programs\Ollama`, or in `Program Files\Ollama`.

**If you added Ollama to PATH**, you can instead run `ollama serve` in any terminal.

## 3. Pull a model

In a **second** PowerShell (Ollama must be installed; you don't need it on PATH):

```powershell
cd D:\agent\mortal_agent
.\scripts\pull_ollama_model.ps1
```

This pulls **llama3.2:1b** (the only Ollama model the agent uses; ~1.3GB, fits 8–11GB RAM).

**If you added Ollama to PATH:** `ollama pull llama3.2:1b`

**One command: pull model then run agent**

```powershell
cd D:\agent\mortal_agent
.\scripts\run_agent_with_ollama.ps1
```

This starts Ollama in the background (if needed), pulls `llama3.2:1b`, then runs the agent. LLM order: Ollama first, then Claude (Anthropic) and other cloud fallbacks if Ollama is unreachable.

## 4. Optional: set env vars

In the terminal where you will run the agent:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:MODEL_NAME = "llama3.2:1b"
```

Or add to `mortal_agent\.env`:

```
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.2:1b
```

## 5. Run the agent

From repo root:

```powershell
cd D:\agent
python -m cli run --observer
```

Then open **http://127.0.0.1:8080** for the Observer UI and type in the terminal `> ` prompt to chat.

## Troubleshooting

- **"429: Rate exceeded" when pulling a model**  
  Ollama’s registry is rate-limiting you. The scripts `pull_ollama_model.ps1` and `run_agent_with_ollama.ps1` now retry automatically (up to 5 times with increasing waits). If it still fails, wait 5–10 minutes and run the pull again, or try again later.

- **"ollama: The term 'ollama' is not recognized"**  
  Install Ollama (step 1–2) and ensure `ollama.exe` is on PATH or run it by full path.

- **"Ollama not reachable at http://localhost:11434"**  
  Start Ollama in a separate terminal: `ollama serve`.

- **"model not found"**  
  Pull the model: `ollama pull llama3.2:1b`.

- **"No module named cli.__main__"**  
  Run from the repo root: `cd D:\agent` then `python -m cli run --observer`. The repo includes `cli/__main__.py` so `python -m cli` works from `D:\agent`.
