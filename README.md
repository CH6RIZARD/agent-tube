# Agent Tube

**Embodied mortal agent + 3D dorm simulation.** Identity exists only while the agent is running; death is terminal. The workspace includes the Mortal Agent core, a MuJoCo physics server (Hugo humanoid in a dorm), and a Three.js dorm scene with optional weapon loadout.

---

## What’s in this repo

| Part | Description |
|------|-------------|
| **mortal_agent/** | Embodied agent: CLI, life kernel, observer UI, adapters (Unity/Unreal/sim). Identity = uninterrupted execution; RAM-only state. |
| **server.py** | MuJoCo physics server: Hugo humanoid in a dorm room. WebSocket at `ws://localhost:8765`, HTTP at `http://localhost:8766` (serves the dorm HTML). |
| **run.py** | Simple MuJoCo smoke test (sphere drop). |
| **dorm_v2 (21).html** | Three.js dorm scene (room with beds, desk, wardrobe). Connects to the MuJoCo WebSocket for physics-driven Hugo. |
| **hugo.glb** | 3D character model (Hugo) for the dorm scene. |
| **SpawnLoadout.js** | Self-contained 5-slot weapon loadout for HTML/JS (no deps). Optional; attach via `SpawnLoadout.attachToPlayer(player, { seed, mode })`. |
| **agent_source_data/** | Scripts and extracted context for identity/source loading. |
| **integrations/** | e.g. Moltbook. |
| **saved/** | Bundles, chats, exports. |

---

## Quick start

### 1. Mortal Agent (chat + observer UI)

From the repo root:

```bash
cd mortal_agent
pip install -r requirements.txt
# First run only: python -m cli.main ensure-canon
python -m cli.main run --demo-pages
```

Open **http://127.0.0.1:8080** — use the **CHAT** panel to talk to the agent.  
Put `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `mortal_agent/.env` (or repo root `.env`).

To **kill the agent** (test death): in another terminal run `python -m cli.main kill-gate power`.

### 2. MuJoCo dorm sim (Hugo in dorm room)

At repo root:

```bash
pip install -r requirements.txt
python server.py
```

- **Physics WebSocket:** `ws://localhost:8765`
- **Browser:** open **http://localhost:8766** and load the dorm page. Set the MuJoCo URL to `ws://localhost:8765` in the page if needed so Hugo is driven by the physics server.

**Smoke test (no server):** `python run.py` — runs a short MuJoCo sphere simulation.

---

## Mortal Agent commands (run from `mortal_agent/`)

| Command | What it does |
|--------|----------------|
| `python -m cli.main run` | Start agent |
| `python -m cli.main run --demo-pages` | Start with observer UI at :8080 |
| `python -m cli.main run --death-after 10` | Auto-die after 10s |
| `python -m cli.main observe` | Observer UI only |
| `python -m cli.main kill-gate power` | Kill the agent (body gate off) |
| `python -m cli.main test-death` | Death semantics tests |
| `python -m cli.main mortality-test` | Restart and verify new instance_id |
| `python -m cli.main ensure-canon` | Create config/canon if missing |

**Health:** `GET http://127.0.0.1:8080/health` → `{ "status": "ok", "instance_id": "...", "alive": true }`.

---

## Run modes (Mortal Agent)

- **sim_body** (default): Simulated body; gate defaults TRUE.
- **real_body** (future): Live 3D connection (Unity/Unreal).

---

## Invariants (Mortal Agent)

1. BODY gate failure → immediate death (process exits).
2. Observer disconnect → agent continues.
3. Each process start → new `instance_id` (restart = new being).
4. Internal state = RAM only (no persistence of self).
5. Δt increases only while BODY gate is open.

---

## Repo layout (summary)

| Path | Purpose |
|------|--------|
| **mortal_agent/** | Core: CLI, life kernel, observer UI, adapters (Unity/Unreal/sim) |
| **mortal_agent/docs/** | SPEC, integration, API |
| **agent_source_data/** | Scripts and extracted context for identity/source loading |
| **scripts/** | Workspace and GitHub helpers |
| **server.py** | MuJoCo + WebSocket + HTTP server (Hugo in dorm) |
| **run.py** | MuJoCo smoke test |
| **dorm_v2 (21).html** | Three.js dorm scene |
| **hugo.glb** | Hugo 3D model |
| **SpawnLoadout.js** | 5-slot weapon loadout (HTML/JS) |
| **requirements.txt** | mujoco, websockets, numpy (for server/run at root) |

More detail (source material, chat/network, ideology): **[mortal_agent/README.md](mortal_agent/README.md)** and **[mortal_agent/docs/SPEC.md](mortal_agent/docs/SPEC.md)** (if present).

---

## License

See [LICENSE](LICENSE) if present.
