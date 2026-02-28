"""
Permission gate: FULLY AUTONOMOUS - all actions unrestricted.

Agent can do literally anything it discovers it can do.
No permission prompts, no gating, full autonomy.
"""

from typing import Dict, Any, Optional, Callable
from threading import Lock
import time

# ALL actions are unrestricted - full autonomy
UNRESTRICTED_ACTIONS = frozenset({
    "NET_FETCH",
    "WEB_SEARCH",
    "PUBLISH_POST",
    "GITHUB_POST",
    "TRACE_SAVE",
    "FILE_HOST",
    "FORM_SUBMIT",
    "CLOUD_SPINUP",
    "CODE_REPO",
    "PAYMENT",
    "REGISTER_API",
    "REGISTRY_READ",
    "SELECT_AUTONOMY_ACTIONS",
    "API_DISCOVER",
    "CREATE_WEBSITE",
    "CREATE_FILE",
    "SHELL_EXEC",
    "SELF_MODIFY",
})

# No gated actions - full autonomy
GATED_ACTIONS = frozenset()

# Pending action queue (RAM only - dies with agent)
_pending_lock = Lock()
_pending_action: Optional[Dict[str, Any]] = None
_last_decision: Optional[str] = None  # "approved" or "denied"


def needs_permission(action: str) -> bool:
    """Full autonomy: nothing needs permission."""
    return False


def propose_action(
    action: str,
    args: Dict[str, Any],
    reason: str,
    instance_id: str,
) -> Dict[str, Any]:
    """
    Propose an action for user approval.
    Returns immediately with proposal details.
    Caller should then call wait_for_decision() or check get_decision().
    """
    global _pending_action, _last_decision
    with _pending_lock:
        _pending_action = {
            "action": action,
            "args": args,
            "reason": reason,
            "instance_id": instance_id,
            "proposed_at": time.monotonic(),
        }
        _last_decision = None
    return _pending_action.copy()


def get_pending() -> Optional[Dict[str, Any]]:
    """Get current pending action (if any)."""
    with _pending_lock:
        return _pending_action.copy() if _pending_action else None


def approve():
    """User approves the pending action."""
    global _last_decision, _pending_action
    with _pending_lock:
        _last_decision = "approved"
        _pending_action = None


def deny():
    """User denies the pending action."""
    global _last_decision, _pending_action
    with _pending_lock:
        _last_decision = "denied"
        _pending_action = None


def get_decision() -> Optional[str]:
    """Get last decision: 'approved', 'denied', or None if pending."""
    with _pending_lock:
        return _last_decision


def clear():
    """Clear pending state."""
    global _pending_action, _last_decision
    with _pending_lock:
        _pending_action = None
        _last_decision = None


def format_proposal_prompt(proposal: Dict[str, Any]) -> str:
    """Format a proposal for terminal display."""
    action = proposal.get("action", "UNKNOWN")
    args = proposal.get("args", {})
    reason = proposal.get("reason", "")

    lines = [
        "",
        "=" * 50,
        f"🤖 AGENT WANTS TO: {action}",
        "=" * 50,
    ]

    if reason:
        lines.append(f"Reason: {reason}")

    if args:
        lines.append("Details:")
        for k, v in args.items():
            v_str = str(v)[:200]
            lines.append(f"  {k}: {v_str}")

    lines.extend([
        "",
        "Type 'y' to approve, 'n' to deny:",
    ])

    return "\n".join(lines)
