"""
Ollama-based decision layer. Single inference entry point: decide(doctrine, state, input).
Rate limited; returns structured JSON { thought, action, args, risk, updated_state }.
"""

import asyncio
import json
import os
import re
import time
from typing import Any, Dict

import requests

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
# Only model used: llama3.2:1b (run: ollama pull llama3.2:1b). Env override kept for compatibility.
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2:1b").strip() or "llama3.2:1b"


def _ollama_timeout() -> int:
    try:
        return max(30, min(300, int(os.environ.get("OLLAMA_TIMEOUT", "120"))))
    except Exception:
        return 120

MAX_CALLS_PER_MINUTE = 30
MAX_TOKENS_PER_MINUTE = 50000


class _RateLimiter:
    def __init__(self, max_calls: int = MAX_CALLS_PER_MINUTE, max_tokens: int = MAX_TOKENS_PER_MINUTE):
        self.max_calls = max_calls
        self.max_tokens = max_tokens
        self._calls_ts: list = []
        self._tokens_ts: list = []

    def _prune_old(self, window_sec: float = 60.0) -> None:
        now = time.monotonic()
        self._calls_ts = [t for t in self._calls_ts if now - t < window_sec]
        self._tokens_ts = [(t, n) for t, n in self._tokens_ts if now - t < window_sec]

    def allow(self, estimated_tokens: int) -> bool:
        self._prune_old()
        if len(self._calls_ts) >= self.max_calls:
            return False
        total_tokens = sum(n for _, n in self._tokens_ts) + estimated_tokens
        if total_tokens > self.max_tokens:
            return False
        return True

    def record(self, estimated_tokens: int) -> None:
        now = time.monotonic()
        self._calls_ts.append(now)
        self._tokens_ts.append((now, estimated_tokens))

    def wait_if_needed(self, estimated_tokens: int) -> None:
        while not self.allow(estimated_tokens):
            time.sleep(1.0)
            self._prune_old()


_limiter = _RateLimiter(MAX_CALLS_PER_MINUTE, MAX_TOKENS_PER_MINUTE)


def _estimate_tokens(text: str) -> int:
    return max(1, len((text or "").strip()) // 4)


def _build_user_message(state: Any, input_text: str) -> str:
    return (
        "### STATE\n"
        + json.dumps(state, default=str)
        + "\n\n### INPUT\n"
        + str(input_text)
        + "\n\n### OUTPUT\n"
        "Respond with VALID JSON ONLY in this format:\n"
        '{"thought": string, "action": string, "args": object, "risk": number, "updated_state": object}'
    )


def _extract_json_block(raw: str) -> str:
    raw = (raw or "").strip()
    start = raw.find("{")
    if start < 0:
        return raw
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if m:
        return m.group(0)
    return raw


def _parse_decide_response(raw: str) -> Dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")
    thought = data.get("thought")
    action = data.get("action")
    args = data.get("args")
    risk = data.get("risk")
    updated_state = data.get("updated_state")
    return {
        "thought": str(thought) if thought is not None else "",
        "action": str(action) if action is not None else "",
        "args": args if isinstance(args, dict) else {},
        "risk": float(risk) if risk is not None else 0.5,
        "updated_state": updated_state if isinstance(updated_state, dict) else {},
    }


async def decide(doctrine: str, state: Any, input_text: str) -> Dict[str, Any]:
    """
    Call remote Ollama with fixed prompt format; return parsed { thought, action, args, risk, updated_state }.
    Rate limited (30 calls/min, 50000 tokens/min). JSON parse with regex fallback and up to 2 repair retries.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("MODEL_NAME", MODEL_NAME)
    user_body = _build_user_message(state, input_text)
    system_content = f"SYSTEM:\n{doctrine}"
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_body},
    ]
    payload = {"model": model, "messages": messages, "stream": False}
    estimated = _estimate_tokens(doctrine) + _estimate_tokens(user_body) + 200

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _limiter.wait_if_needed(estimated))

    def _post() -> str:
        _limiter.record(estimated)
        r = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=_ollama_timeout(),
        )
        if not r.ok:
            body = (r.text or "").strip()[:500]
            try:
                err = r.json()
                if isinstance(err, dict) and err.get("error"):
                    body = err.get("error", body)
            except Exception:
                pass
            raise RuntimeError(
                f"Ollama {r.status_code}: {body or r.reason}. "
                f"Model '{model}' may be missing — run: ollama pull {model}"
            ) from None
        data = r.json()
        msg = data.get("message") or {}
        content = (msg.get("content") or "").strip()
        return content

    raw_content = await loop.run_in_executor(None, _post)
    if not raw_content:
        raise ValueError("Empty response from Ollama")

    max_repair_retries = 2
    last_error = None
    for attempt in range(max_repair_retries + 1):
        try:
            parsed = _parse_decide_response(raw_content)
            return parsed
        except Exception as e:
            last_error = e
        if attempt < max_repair_retries:
            extracted = _extract_json_block(raw_content)
            if extracted != raw_content:
                try:
                    parsed = _parse_decide_response(extracted)
                    return parsed
                except Exception:
                    pass
            repair_prompt = (
                "Rewrite the following into valid JSON matching schema ONLY:\n"
                '{"thought": string, "action": string, "args": object, "risk": number, "updated_state": object}\n\n'
                + raw_content
            )
            repair_messages = [
                {"role": "system", "content": "You output only valid JSON. No markdown, no explanation."},
                {"role": "user", "content": repair_prompt},
            ]
            repair_payload = {"model": model, "messages": repair_messages, "stream": False}
            try:
                def _repair_post() -> str:
                    _limiter.record(_estimate_tokens(repair_prompt) + 100)
                    r = requests.post(f"{base_url}/api/chat", json=repair_payload, timeout=_ollama_timeout())
                    r.raise_for_status()
                    return (r.json().get("message") or {}).get("content") or ""
                raw_content = await loop.run_in_executor(None, _repair_post)
                if not raw_content:
                    break
                raw_content = raw_content.strip()
            except Exception:
                break
    raise last_error or ValueError("Invalid JSON after retries")
