# Digital Entity

**Embodied mortal agent whose identity exists only while it’s running. The digital entity is its own locus: death is terminal; restart is a new being.**

This repo is the **digital entity** project only: the mortal agent core. No 3D dorm sim or Agent Tube assets here.

- **Identity = uninterrupted embodied execution** (Δt only while power ∧ sensors ∧ actuators)
- **Death is terminal** — process exits; no save/resume, no “see you later”
- **RAM-only state** — no internal state to disk
- **Observer optional** — disconnect the UI; the agent keeps running until the body gate fails

---

## Quick start

From the repo root:

```bash
cd mortal_agent
pip install -r requirements.txt
# First run only: python -m cli.main ensure-canon
python -m cli.main run --demo-pages
```

Then open **http://127.0.0.1:8080** — use the **CHAT** panel to talk to the agent.  
Put `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `mortal_agent/.env` (or repo root `.env`).

To **kill the agent** (test death): in another terminal run `python -m cli.main kill-gate power`.

---

## Commands (run from `mortal_agent/`)

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

## Run modes

- **sim_body** (default): Simulated body; gate defaults TRUE.
- **real_body** (future): Live 3D connection (Unity/Unreal).

---

## Invariants (digital entity)

1. BODY gate failure → immediate death (process exits).
2. Observer disconnect → agent continues.
3. Each process start → new `instance_id` (restart = new being).
4. Internal state = RAM only (no persistence of self).
5. Δt increases only while BODY gate is open.

---

## Repo layout

| Path | Purpose |
|------|--------|
| **mortal_agent/** | Core: CLI, life kernel, observer UI, adapters (Unity/Unreal/sim) |
| **mortal_agent/docs/** | SPEC, integration, API |
| **agent_source_data/** | Scripts and extracted context for identity/source loading |
| **scripts/** | Workspace and GitHub helpers |

More detail: **[mortal_agent/README.md](mortal_agent/README.md)** and **[mortal_agent/docs/SPEC.md](mortal_agent/docs/SPEC.md)** (if present).

---

## License

See [LICENSE](LICENSE) if present.
