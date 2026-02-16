# Mortal Agent

A mortal, embodied agent whose identity exists only during continuous runtime.

## Core Principle

**Identity = Uninterrupted Embodied Execution**

- Δt accumulates ONLY while BODY gate is open (power ∧ sensors ∧ actuators)
- Observer is NON-CRITICAL - disconnect never kills agent
- Restart = different being
- Death is terminal (BODY gate failure only)

## Quick Start

```bash
cd mortal_agent

# If you see "Canon required at boot: constitution.yaml not found", run once:
#   python -m cli.main ensure-canon

# Run agent with observer UI
python -m cli.main run --demo-pages

# Open http://127.0.0.1:8080 — use the CHAT panel to talk to the agent.
# LLM: Ollama (llama3.2:1b) first, then Claude and other cloud fallbacks. Run: ollama pull llama3.2:1b. See docs/OLLAMA_WINDOWS.md.
# Legacy: ANTHROPIC_API_KEY or OPENAI_API_KEY in .env for cloud providers.

# Test death (in another terminal)
python -m cli.main kill-gate power
```

## Run Modes

- `sim_body` (default): Simulated body, gate defaults TRUE
- `real_body` (future): Requires live 3D connection

## Commands

```bash
python -m cli run                         # Start agent (or python -m cli.main run)
python -m cli run --death-after 10        # Auto-die after 10s
python -m cli observe                     # Observer only
python -m cli test-death                  # Death semantics tests (in-process)
python -m cli mortality-test              # Kill process, restart, verify NEW instance_id
python -m cli ensure-canon                # Create config/canon/constitution.yaml if missing
```

**Health:** `GET http://127.0.0.1:8080/health` or `/api/health` returns `{ "status": "ok", "instance_id": "...", "alive": true }`.

## Ideology / source material (what the agent feeds from)

The agent’s system prompt is built from identity + **source context** loaded once at start:

- **saved/bundles** — `final_agent_bundle.md`, `additional_docs.md`, `creati_pack.md`, `save_chats.md`
- **saved/claude_export** — `memories.json` (conversations_memory, project_memories)
- **saved/claude_web_chats/save** — sample of exported Claude web chat markdown files
- **agent_source_data/extracted** — if present: constitution_raw.md, doctrine_raw.md, theological_statements.md, red_lines.md, style_samples.txt (run `python agent_source_data/extract_from_bundle.py` from repo root to generate from `saved/bundles/final_agent_bundle.md`)
- **Downloads docx** — `theology.docx`, `surgents file .docx`, `closed loop code open world.docx`, `LOCKED ROOM RIGHT impact.docx` (or similar names under `C:\Users\<you>\Downloads`)

Total source text is capped so it fits in the LLM system context.

## Ollama on Windows (install to D:)

The agent uses **Ollama** for the LLM by default. To install Ollama on D: and run the agent:

1. **Download and install to D:**  
   From PowerShell: `cd mortal_agent` then `.\scripts\install_ollama_to_d.ps1`
2. **Start Ollama** (new terminal): `ollama serve`
3. **Pull the model:** `ollama pull llama3.2:1b`
4. **Run agent** from repo root: `cd D:\agent` then `python -m cli run --observer`

Full steps and troubleshooting: **[docs/OLLAMA_WINDOWS.md](docs/OLLAMA_WINDOWS.md)**.

## Chat and network

- **Chat**: In the Observer UI (http://127.0.0.1:8080), use the **CHAT** panel, or type at the `> ` prompt in the terminal. Replies use identity + source context and LLM. **Same API keys as the model you chat with**: put `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in any of: `mortal_agent/.env`, repo root `.env`, or your user home `~/.env`. To use the exact .env file another app uses, set `AGENT_ENV_PATH` to that file path.
- **Network / WiFi**: The agent can do outbound HTTP via `NET_FETCH` (network pipeline wired on by default). Uses the machine’s network (WiFi/ethernet).

## Invariants

1. BODY gate failure = immediate death
2. Observer failure = agent continues
3. Each start = new instance_id
4. internal_state = RAM only
5. Δt only increases while BODY gate open

## Quick tests (wander heartbeat)

- **LLM ON:** Run `python -m cli.main run` for 2–3 minutes; expect at least 2–4 wander heartbeat posts (every ~25–30s, subject to post cooldown).
- **LLM OFF:** Run `python -m cli.main run --no-llm` for 2–3 minutes; expect varied wander lines (ideology/source/state), no single repeated sentence.
- Wander respects existing post cooldown and skips if a post was just made (no spam).
