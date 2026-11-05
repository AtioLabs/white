"""White's computer use (White 2.0, point 4) via Vercel Labs agent-desktop.

agent-desktop reads apps through the OS accessibility tree and acts on refs like `@s8f3k2p9:e8`.
A ref says nothing about WHAT is clicked, so White acts only through this wrapper:
1. it resolves the element's real name/role from the snapshot White just took,
2. it refuses if White's stated `label` hides an outward target (e.g. label "OK" on a "Send" button),
3. the white-gate plugin sees `white_desktop` calls with the real target in the args and sends
   send/pay/post/delete-type actions to the founder for approval.
Stdlib only; agent-desktop is an external CLI (npm install -g agent-desktop).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, Callable, Optional

OBSERVE = {"snapshot", "find", "get", "is", "list-apps", "list-windows", "list-surfaces", "status", "version",
           "permissions", "screenshot"}
ACT = {"click", "double-click", "right-click", "type", "set-value", "clear", "focus", "select", "toggle", "check",
       "uncheck", "expand", "collapse", "scroll", "scroll-to", "press", "hover", "launch", "close-app",
       "focus-window"}
REF = re.compile(r"^@[A-Za-z0-9]+:e\d+$")
OUTWARD = re.compile(r"\b(send|submit|post|publish|tweet|reply|apply|pay|purchase|buy|checkout|confirm|"
                     r"sign|accept|invite|connect|share|delete|remove|transfer|order|book)\b", re.IGNORECASE)

Runner = Callable[[list[str]], dict]


def _default_runner(argv: list[str]) -> dict:
    exe = shutil.which("agent-desktop")
    if not exe:
        return {"ok": False, "error": {"code": "NOT_INSTALLED",
                                       "message": "agent-desktop is not installed (npm install -g agent-desktop)"}}
    p = subprocess.run([exe, *argv], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "error": {"code": "BAD_OUTPUT", "message": (p.stderr or p.stdout)[-500:]}}


# The last snapshot's refs -> (role, name), so a ref can be mapped to what it really is.
_seen: dict[str, tuple[str, str]] = {}


def _index(node: Any) -> None:
    if isinstance(node, dict):
        ref = node.get("ref_id") or node.get("ref")
        if ref:
            _seen[str(ref)] = (str(node.get("role") or ""), str(node.get("name") or ""))
        for v in node.values():
            _index(v)
    elif isinstance(node, list):
        for v in node:
            _index(v)


def target_of(ref: str) -> Optional[tuple[str, str]]:
    return _seen.get(ref)


def run(command: str, args: list[str] | None = None, ref: str = "", label: str = "",
        runner: Runner | None = None) -> dict:
    runner = runner or _default_runner
    args = [str(a) for a in (args or [])]
    if command not in OBSERVE | ACT:
        return {"ok": False, "error": f"unknown or unsupported command '{command}'"}
    if command in ACT and command not in ("launch", "close-app", "focus-window", "press"):
        if not REF.match(ref or ""):
            return {"ok": False, "error": "acting needs a ref from a fresh snapshot, e.g. @s8f3k2p9:e8"}
        real = target_of(ref)
        if real is None:
            return {"ok": False, "error": "unknown ref: take a snapshot of this app first, then act on its refs"}
        role, name = real
        if OUTWARD.search(name) and not OUTWARD.search(label or ""):
            return {"ok": False, "error": f"label '{label}' hides the real target '{name}' ({role}); "
                                          f"call again with label='{name}' so the founder can approve it"}
    argv = [command] + ([ref] if ref else []) + args
    out = runner(argv)
    if command in ("snapshot", "find") and out.get("ok"):
        _index(out.get("data"))
    return out
