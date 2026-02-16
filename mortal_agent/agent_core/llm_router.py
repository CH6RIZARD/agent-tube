"""
LLM Router - Task-based provider routing with timeout, retries, failover.

- Primary: Ollama (llama3.2:1b) via agent_core.ollama_decide.decide.
- Fallback order: Claude (Anthropic) -> OpenRouter -> Groq -> OpenAI.
- provider_mode retained for API compatibility; Ollama is always tried first.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

_root = Path(__file__).resolve().parent.parent  # mortal_agent
_repo = _root.parent

# Load .env: cwd, repo, project, home, AGENT_ENV_PATH, then external keys/.env (overrides)
try:
    from dotenv import load_dotenv
    load_dotenv(Path.cwd() / ".env")
    load_dotenv(_repo / ".env")
    load_dotenv(_root / ".env")
    load_dotenv(Path.home() / ".env")
    env_path = os.environ.get("AGENT_ENV_PATH", "").strip()
    if env_path:
        load_dotenv(Path(env_path))
    load_dotenv()
    for keys_dir in (Path.cwd() / "keys", _root / "keys", _repo / "keys"):
        keys_env = keys_dir / ".env"
        if keys_env.exists():
            load_dotenv(dotenv_path=keys_env)
            break
except ImportError:
    pass

_LOG_KEYS = os.environ.get("AGENT_LOG_KEYS", "").strip().lower() in ("1", "true", "yes")


def _log_key_status() -> None:
    if not _LOG_KEYS:
        return
    try:
        print("[keys] OLLAMA: " + (os.environ.get("OLLAMA_BASE_URL") or "localhost:11434"), flush=True)
        print("[keys] MODEL: " + (os.environ.get("MODEL_NAME") or "llama3.2:1b"), flush=True)
    except Exception:
        pass


_log_key_status()

# LLM-only: pool of short first-person offline wander lines (no single repeated constant).
_OFFLINE_WANDER_POOL = [
    "I'm here; reasoning is offline.",
    "Low energy. I'm still here.",
    "I feel steady but offline.",
    "Uncertain. I remain present.",
    "I'm cautious; no reasoning right now.",
    "Tension present. I'm still here.",
    "I'm strained but here.",
    "Gate closed. I'm cautious.",
    "My reasoning is offline; I feel tense.",
    "I remain; low energy.",
    "I'm here; uncertain.",
    "Offline. I feel steady.",
    "I'm present; reasoning unavailable.",
]
_UNREACHABLE_FALLBACK = "I can't reach my reasoning right now."

_llm_failure_logged: bool = False
_last_offline_wander_index: int = -1


def _log_llm_failure_once(failure_info: Optional[Dict[str, Any]], tried_failover: bool = False) -> None:
    global _llm_failure_logged
    if _llm_failure_logged or not failure_info:
        return
    _llm_failure_logged = True
    code = failure_info.get("code", "unknown")
    detail = (failure_info.get("detail") or "")[:120]
    provider = failure_info.get("provider", "ollama")
    msg = f"[agent] LLM unreachable ({provider}: {code}). {detail}"
    try:
        print(msg, file=sys.stderr, flush=True)
    except Exception:
        pass


def get_offline_wander_text(
    energy: float = 100.0,
    hazard_score: float = 0.0,
    last_text: Optional[str] = None,
) -> str:
    global _last_offline_wander_index
    pool = _OFFLINE_WANDER_POOL
    last = (last_text or "").strip()
    candidates = [p for p in pool if (p or "").strip() != last] if last else list(pool)
    if not candidates:
        candidates = list(pool)
    idx = (_last_offline_wander_index + 1) % len(candidates)
    _last_offline_wander_index = idx
    return candidates[idx]


def is_unreachable_fallback(text: str) -> bool:
    return bool(text and text.strip() == _UNREACHABLE_FALLBACK)


def _decide_sync(doctrine: str, state: Any, input_text: str) -> Dict[str, Any]:
    try:
        from .ollama_decide import decide as decide_async
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(decide_async(doctrine, state, input_text))
        finally:
            loop.close()
    except Exception as e:
        raise RuntimeError(f"decide failed: {e}") from e


def _try_ollama_reply(
    system_prompt: str,
    user_text: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Try Ollama decide(); return (reply_text, None) or (None, failure_info)."""
    try:
        result = _decide_sync(system_prompt, {}, user_text)
        thought = (result.get("thought") or "").strip()
        action = (result.get("action") or "").strip()
        reply = thought or action or ""
        if reply:
            return reply, None
        return None, {"provider": "ollama", "code": "unknown", "detail": "no response"}
    except Exception as e:
        return None, {"provider": "ollama", "code": "unknown", "detail": str(e)[:200]}


def generate_reply_routed(
    user_text: str,
    system_prompt: str,
    max_tokens: int = 120,
    source_context: Optional[str] = None,
    provider_mode: str = "auto",
    timeout_s: float = 30.0,
    retries: int = 2,
    failover: bool = True,
    no_llm: bool = False,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Generate reply: Ollama (llama3.2:1b) first, then Claude (Anthropic), then OpenRouter, Groq, OpenAI.
    Returns (reply_text, failure_info).
    """
    if no_llm:
        return None, {"provider": "none", "code": "offline", "detail": "no_llm mode"}

    if source_context and source_context.strip():
        try:
            from .source_loader import get_system_with_source
            system_prompt = get_system_with_source(system_prompt, source_context)
        except Exception:
            pass

    max_tokens = max(15, min(512, max_tokens))
    first_failure = None

    # 1) Primary: Ollama (llama3.2:1b)
    for attempt in range(retries + 1):
        reply, failure = _try_ollama_reply(system_prompt, user_text)
        if reply:
            return reply, None
        if first_failure is None and failure:
            first_failure = failure
        if attempt < retries:
            time.sleep(0.5 * (attempt + 1))

    # 2) Fallback: Claude -> OpenRouter -> Groq -> OpenAI
    if failover:
        try:
            from .llm_router_backup import (
                _try_anthropic,
                _try_openrouter,
                _try_groq,
                _try_openai,
            )
        except Exception:
            _try_anthropic = _try_openrouter = _try_groq = _try_openai = None
        providers = [
            ("anthropic", _try_anthropic),
            ("openrouter", _try_openrouter),
            ("groq", _try_groq),
            ("openai", _try_openai),
        ]
        for name, try_fn in providers:
            if try_fn is None:
                continue
            reply, failure = try_fn(user_text, system_prompt, max_tokens, timeout_s)
            if reply:
                return reply, None
            if first_failure is None and failure:
                first_failure = failure

    _log_llm_failure_once(first_failure)
    return None, first_failure or {"provider": "ollama", "code": "unknown", "detail": "no response"}


def generate_plan_routed(
    context: str,
    max_tokens: int = 120,
    provider_mode: str = "auto",
    timeout_s: float = 30.0,
    retries: int = 2,
    failover: bool = True,
    no_llm: bool = False,
    include_autonomy_claims: bool = True,
    output_medium: str = "chat",
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Bounded planning: Ollama first, then Claude (Anthropic), then other fallbacks.
    Returns (raw_json_text, failure_info).
    """
    if no_llm:
        return None, {"provider": "none", "code": "offline", "detail": "no_llm mode"}
    try:
        from .identity import get_planner_system_prompt
        plan_system = get_planner_system_prompt(include_autonomy_claims=include_autonomy_claims)
        try:
            from .llm import get_plan_style_suffix
            plan_system = plan_system + " " + get_plan_style_suffix(output_medium or "chat")
        except Exception:
            pass
    except Exception:
        return None, {"provider": "identity", "code": "plan_prompt_unavailable", "detail": "Planner requires identity; cannot plan without it."}

    first_failure = None

    # 1) Primary: Ollama (llama3.2:1b)
    for attempt in range(retries + 1):
        try:
            result = _decide_sync(plan_system, {}, context)
            thought = (result.get("thought") or "").strip()
            action = (result.get("action") or "").strip()
            risk = result.get("risk", 0.5)
            try:
                risk_f = float(risk)
                risk_f = max(0.0, min(1.0, risk_f))
            except (TypeError, ValueError):
                risk_f = 0.5
            confidence = 1.0 - risk_f
            plan_obj = {
                "text": thought,
                "intent": action or "unknown",
                "confidence": confidence,
                "reasons": [thought] if thought else [],
            }
            return json.dumps(plan_obj), None
        except Exception as e:
            failure = {"provider": "ollama", "code": "unknown", "detail": str(e)[:200]}
            if first_failure is None:
                first_failure = failure
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))

    # 2) Fallback: use chat stack (Claude -> OpenRouter -> Groq -> OpenAI), wrap reply as plan
    if failover:
        reply, _ = generate_reply_routed(
            context, plan_system, max_tokens=max_tokens, source_context=None,
            provider_mode=provider_mode, timeout_s=timeout_s, retries=retries,
            failover=True, no_llm=False,
        )
        if reply and (reply or "").strip():
            plan_obj = {
                "text": (reply or "").strip()[:2000],
                "intent": "unknown",
                "confidence": 0.6,
                "reasons": [(reply or "").strip()[:500]],
            }
            return json.dumps(plan_obj), None

    _log_llm_failure_once(first_failure)
    return None, first_failure or {"provider": "ollama", "code": "unknown", "detail": "no response"}
