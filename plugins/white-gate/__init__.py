"""White authority gate: Hermes plugin entry point.

Registers a pre_tool_call hook. Every outward action is checked against
$HERMES_HOME/founder/authority.yaml (see gate.py). Decisions are appended to
$HERMES_HOME/white/gate-log.jsonl as proof of what was allowed, approved or blocked.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

try:  # loaded as a Hermes plugin package
    from .white_gate_rules import decide, load_authority
except ImportError:  # loaded directly (tests)
    from white_gate_rules import decide, load_authority  # type: ignore

logger = logging.getLogger(__name__)


def _home() -> Path:
    from hermes_constants import get_hermes_home
    return Path(get_hermes_home())


def _log(entry: dict) -> None:
    try:
        log_dir = _home() / "white"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "gate-log.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("white-gate: could not write log", exc_info=True)


def _on_pre_tool_call(tool_name: str = "", args: dict | None = None, **kwargs):
    try:
        authority = load_authority(_home() / "founder" / "authority.yaml")
        decision = decide(tool_name, args or {}, authority)
    except Exception as exc:  # never fail open on an error in the gate itself
        logger.warning("white-gate error on %s: %s", tool_name, exc)
        return {"action": "approve", "message": f"White's gate hit an error ({exc}); asking you first."}

    if decision.action != "allow" or decision.rule:
        _log({"ts": time.time(), "tool": tool_name, "action": decision.action,
              "reason": decision.reason, "rule": decision.rule,
              "session_id": kwargs.get("session_id", ""), "tool_call_id": kwargs.get("tool_call_id", "")})

    if decision.action == "block":
        return {"action": "block", "message": decision.reason}
    if decision.action == "approve":
        return {"action": "approve", "message": decision.reason, "rule_key": decision.rule}
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
