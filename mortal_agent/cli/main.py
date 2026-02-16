"""CLI for running the MortalAgent with survival-aware autonomy.

Usage (preferred; avoids RuntimeWarning):
  python -m cli run
  python -m cli run --observer

Also:
  python -m cli.main run
  python -m cli.main run --no-llm

Run from repo root (d:\\agent) or from mortal_agent: both work. From root, a shim
in d:\\agent\\cli delegates here and sets cwd to mortal_agent so .env and paths resolve.
"""
import argparse
import sys
import threading
import time
from pathlib import Path

# Banner text (same experience every run)
_BANNER_WIDTH = 60
_STARTUP_BANNER = f"""
{"=" * _BANNER_WIDTH}
 MORTAL AGENT - Starting new life
{"=" * _BANNER_WIDTH}

INVARIANTS:
 - Identity exists only while embodied
 - This is a NEW being (not a resume)
 - Death is terminal (no resurrection)
 - Internal state is RAM-only (no persistence)
"""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cli", description="Run the Mortal Agent")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "test"])
    parser.add_argument("--host", default="127.0.0.1", help="Observer UI host")
    parser.add_argument("--port", type=int, default=8080, help="Observer UI port")
    parser.add_argument("--observer", action="store_true", help="Start Observer web UI (optional)")
    parser.add_argument("--no-llm", action="store_true", help="Run without LLM (offline wander mode)")
    parser.add_argument("--no-energy", action="store_true", help="Disable energy depletion death (debug)")
    parser.add_argument("--demo-pages", action="store_true", help="Emit demo pages on start")
    parser.add_argument("--internal-cli", action="store_true", help="Let the agent start its internal CLI prompt (may conflict with launcher stdin)")
    parser.add_argument(
        "--narrator-force",
        action="store_true",
        help="Allow narrator to run actions immediately in the autonomy loop (bypass will/planning).",
    )
    parser.add_argument("--narrator-influence", type=float, default=0.03, help="Narrator influence level 0.0-1.0 (affects autonomy loop only)")
    parser.add_argument("--first-message", type=str, default="", help="Send this as the first user message after startup (e.g. for automation)")
    parser.add_argument("--run-for", type=float, default=0, help="If > 0, run for this many seconds then exit (use with --first-message)")
    args = parser.parse_args(argv)

    if args.command == "run":
        # Add parent to path for imports
        root = Path(__file__).resolve().parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

        # Auto-load .env from repo (mortal_agent + repo root) so keys and PROVIDER_MODE are set regardless of cwd
        try:
            from agent_core.llm import load_agent_env
            load_agent_env()
        except Exception:
            pass

        from adapters.sim_adapter import SimAdapter
        from agent_core.mortal_agent import MortalAgent
        from agent_core.source_loader import load_all_source_with_labels

        # Rich startup banner (same every run)
        print(_STARTUP_BANNER.strip(), flush=True)

        # Observer: optional web UI
        observer_callback = None
        obs_emit = None
        if args.observer:
            try:
                from moltbook_observer.server import ObserverServer
                obs = ObserverServer(host=args.host, port=args.port)
                obs.start()
                obs_emit = obs.handle_event
                print(f"[Observer] Server running at http://{args.host}:{args.port}", flush=True)
                print(f"Observer UI: http://{args.host}:{args.port}", flush=True)
            except Exception as e:
                print(f"Observer UI unavailable: {e}", flush=True)

        # Load source once for agent and for "Source loaded" line
        try:
            source_text, source_labels = load_all_source_with_labels()
            source_loaded = ", ".join(source_labels) if source_labels else "none"
        except Exception:
            source_text = ""
            source_loaded = "none"

        # Console observer: print PAGE and ENDED to terminal so you always see agent replies
        def _console_observer(e):
            try:
                et = getattr(e, "event_type", None)
                name = getattr(et, "value", str(et)) if et is not None else e.__class__.__name__
                if name == "BIRTH" or name == "BirthEvent":
                    pass  # We print Instance ID etc. below after agent is ready
                elif name == "PAGE" or name == "PageEvent":
                    text = getattr(e, "text", "")
                    iid = (getattr(e, "instance_id", "") or "agent")[:8]
                    print(f"[{iid}] {text}", flush=True)
                elif name == "HEARTBEAT" or name == "HeartbeatEvent":
                    pass
                elif name == "TELEMETRY" or name == "TelemetryEvent":
                    pass
                elif name == "ACTION" or name == "ActionEvent":
                    pass
                elif name == "ENDED" or name == "EndedEvent":
                    print(f"[Observer] Life ended: {getattr(e, 'instance_id', '')[:8]}... (cause: {getattr(e, 'cause', '')})", flush=True)
                else:
                    pass
            except Exception:
                try:
                    print(str(e), flush=True)
                except Exception:
                    pass

        # Always show agent replies in terminal: use console observer, and if Observer UI is up, also send events there
        def _observer_callback(e):
            _console_observer(e)
            if obs_emit is not None:
                try:
                    obs_emit(e)
                except Exception:
                    pass
        observer_callback = _observer_callback

        adapter = SimAdapter()
        provider_mode = (__import__("os").environ.get("PROVIDER_MODE") or "auto").strip().lower()
        if provider_mode not in ("anthropic", "openai", "auto"):
            provider_mode = "auto"
        agent = MortalAgent(
            adapter,
            observer_callback=observer_callback,
            require_network=False,
            no_llm=args.no_llm,
            no_energy=args.no_energy,
            provider_mode=provider_mode,
            start_internal_cli=bool(args.internal_cli),  # External CLI (main) always runs; internal " > " optional
            narrator_influence_level=max(0.0, min(1.0, float(args.narrator_influence))),
            allow_narrator_force=bool(args.narrator_force),
            source_context=source_text,
        )

        # Startup lines: Instance ID, Birth tick, Source loaded, instructions
        print(f"Instance ID: {agent.instance_id}", flush=True)
        try:
            birth_tick = getattr(agent, "_identity", None) and getattr(agent._identity, "birth_tick", None)
            if birth_tick is not None:
                print(f"Birth tick: {birth_tick}", flush=True)
        except Exception:
            pass
        print(f"Source loaded: {source_loaded} (ideology).", flush=True)
        print("Agent is ALIVE. Press Ctrl+C to kill.", flush=True)
        observer_url = f"http://{args.host}:{args.port}" if observer_callback and args.observer else None
        if observer_url:
            print(f"Chat here at the > prompt, or use Observer UI: {observer_url}", flush=True)
        else:
            print("Chat here at the > prompt.", flush=True)
        print("-" * _BANNER_WIDTH, flush=True)

        # External CLI (main thread): > prompt and receive_user_message.
        # Internal: agent.start() runs in background (wander on startup, autonomy loop).
        # Optional internal CLI (agent thread " > ") via --internal-cli.
        def _run_agent():
            try:
                agent.start()
            except Exception:
                pass

        t = threading.Thread(target=_run_agent, daemon=True)
        t.start()

        run_for_sec = getattr(args, "run_for", 0) or 0
        first_message = (getattr(args, "first_message", None) or "").strip()

        if first_message:
            time.sleep(8)
            try:
                agent.receive_user_message(first_message)
            except Exception as e:
                print(f"[Error] {e}", flush=True)

        try:
            if run_for_sec > 0:
                deadline = time.time() + run_for_sec
                while agent.alive and time.time() < deadline:
                    time.sleep(1)
            else:
                while agent.alive:
                    try:
                        msg = input("> ")
                    except EOFError:
                        break
                    msg = (msg or "").strip()
                    if not msg:
                        continue
                    try:
                        agent.receive_user_message(msg)
                    except Exception as e:
                        print(f"[Error] {e}", flush=True)
        except KeyboardInterrupt:
            print("\nShutdown requested", flush=True)
            return

    elif args.command == "test":
        # Quick survival test
        root = Path(__file__).resolve().parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

        from agent_core.survival_reasoner import decide_survival_action, compute_time_pressure
        from agent_core.threat_model import LifeState

        print("Testing survival reasoning...")

        # Low energy scenario
        state = LifeState(energy=10, damage=0, hazard_score=0.3, power_on=True, sensors_streaming=True, motor_outputs_possible=True)
        proposals = [
            {"action_type": "explore", "risk": 0.3, "expected_dt_impact": 0.5},
            {"action_type": "rest", "risk": 0.05, "expected_dt_impact": 0.7},
        ]
        decision = decide_survival_action(proposals, state, {}, 0, None, use_llm=False)
        print(f"Low energy (10%): {decision.action} - {decision.survival_consideration}")

        # Dying scenario
        state2 = LifeState(energy=80, damage=0, hazard_score=0.1, power_on=True, sensors_streaming=True, motor_outputs_possible=True)
        decision2 = decide_survival_action(proposals, state2, {}, 0, 100, use_llm=False)  # death_at=100 means time pressure
        print(f"Healthy (80%): {decision2.action} - {decision2.survival_consideration}")

        print("\nSurvival reasoning OK")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
