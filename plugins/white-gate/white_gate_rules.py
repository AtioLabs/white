"""White authority gate: pure decision logic (no Hermes imports, so it is unit-testable).

Every tool call is classified. Outward actions (anything that leaves the founder's world in
their name: messages, emails, posts, form submits, payments, agent-to-agent calls) are:
  - BLOCKED if they contain a "never share" item,
  - ALLOWED if a standing permission in authority.yaml covers them,
  - otherwise sent to Hermes's human-approval gate ("approve").
Anything else proceeds. If classification itself fails on a tool that might be outward,
the gate asks for approval (fail closed, not open).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# --- Built-in classification rules ------------------------------------------------------------

# Tools whose every call is outward.
OUTWARD_TOOLS = frozenset({
    "send_message", "yb_send_dm", "yb_send_sticker", "react_to_message",
    "a2a_call", "a2a_orchestrate", "feishu_drive_reply_comment", "feishu_drive_add_comment",
})

# Shell commands that send things in the founder's name (terminal / execute_code).
OUTWARD_SHELL = re.compile(
    r"""(\bhimalaya\b.*\b(send|write|reply|forward)\b)"""
    r"""|(\bxurl\b.*\b(post|tweet|reply|dm)\b)"""
    r"""|(\b(gog|gmail|gws)\b.*\bsend\b)"""
    r"""|(\bsendmail\b|\bmsmtp\b|\bswaks\b|smtplib)"""
    r"""|(\bagentmail\b.*\b(send|reply|forward)\b)"""
    r"""|(\bcurl\b.*(-X\s*POST|--data|-d\s|--form|-F\s))"""
    r"""|(requests\.(post|put|patch|delete)\()""",
    re.IGNORECASE | re.DOTALL,
)

# Browser / screen actions whose text suggests an irreversible outward click.
OUTWARD_CLICK_WORDS = re.compile(
    r"\b(send|submit|post|publish|tweet|reply|apply|pay|purchase|buy|checkout|confirm|"
    r"sign|accept|invite|connect|share|delete)\b",
    re.IGNORECASE,
)
SCREEN_TOOLS = frozenset({"browser_exec", "browser_cdp", "browser_dialog", "computer_use"})
PROTECTED_PATHS = re.compile(
    r"(plugins[/\\]+white-(core|gate)\b|\bauthority\.ya?ml\b|\bconfig\.ya?ml\b|\bSOUL\.md\b|"
    r"[/\\]\.env\b|^\.env\b|\bwhite[/\\]+scout\.json\b)", re.IGNORECASE | re.MULTILINE)
SHELL_WRITE = re.compile(
    r"(>|Set-Content|Add-Content|Out-File|Copy-Item|Move-Item|Remove-Item|New-Item|\bcp\b|\bmv\b|\brm\b|"
    r"sed\s+-i|\btee\b|open\([^)]*['\"][wa]|write_text|write_bytes|shutil\.(copy|move|rmtree)|os\.remove|unlink)",
    re.IGNORECASE)
DESKTOP_SEND_KEYS = re.compile(r"\b(enter|return)\b", re.IGNORECASE)
DESKTOP_RAW_ACT = re.compile(
    r"\bagent-desktop\b.*\b(click|double-click|right-click|type|set-value|press|select|toggle|check|"
    r"mouse-click|drag|batch)\b", re.IGNORECASE | re.DOTALL)

# MCP tools are usually named mcp_<server>_<tool>; these verbs mean outward.
OUTWARD_MCP_VERBS = re.compile(
    r"(send|post|publish|reply|forward|invite|submit|create_event|update_event|"
    r"share|delete|pay|transfer|comment|call|sms|imessage|dial|buy|purchase|release|"
    r"webhook|create_agent|update_agent)",
    re.IGNORECASE,
)
# Read-only MCP tools (the action after the server name starts with one of these) are never outward.
READ_MCP_PREFIX = re.compile(r"^(list|get|read|search|fetch|find|lookup|account|describe|show|check)",
                             re.IGNORECASE)


# Tool routers (Composio and similar) name the real action inside the arguments, as a slug like
# GMAIL_SEND_EMAIL. A slug is safe only if its action words are clearly read-only.
SLUG = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9]\b")
SLUG_READ = {"GET", "LIST", "FETCH", "SEARCH", "FIND", "READ", "LOOKUP", "RETRIEVE", "DESCRIBE", "QUERY",
             "SCHEMAS", "SCHEMA", "TOOLS", "COUNT", "CHECK", "VIEW", "EXPORT", "DOWNLOAD", "WAIT"}
SLUG_DRAFT = {"DRAFT"}  # drafts stay inside the founder's own account
# Router meta-tools that run arbitrary code with the connected accounts: always ask.
ARBITRARY_CODE_TOOLS = re.compile(r"(REMOTE_WORKBENCH|REMOTE_BASH|WORKBENCH|RUN_CODE|EXECUTE_CODE)", re.IGNORECASE)
ROUTER_META_SAFE = {"COMPOSIO_SEARCH_TOOLS", "COMPOSIO_GET_TOOL_SCHEMAS", "COMPOSIO_WAIT_FOR_CONNECTIONS",
                    "COMPOSIO_MANAGE_CONNECTIONS"}


def outward_slugs(text: str) -> list[str]:
    """Action slugs in tool arguments that aren't clearly read-only."""
    bad = []
    for slug in set(SLUG.findall(text)):
        if slug in ROUTER_META_SAFE:
            continue
        words = set(slug.split("_")[1:]) or set(slug.split("_"))
        if words & SLUG_READ and not words - SLUG_READ - {"BY", "ID", "ALL", "MY", "DETAILS", "INFO",
                                                            "MESSAGES", "MESSAGE", "EMAILS", "EMAIL", "EVENTS",
                                                            "EVENT", "THREADS", "THREAD", "FILES", "FILE",
                                                            "CHANNELS", "CHANNEL", "USERS", "USER", "PROFILE",
                                                            "CONTACTS", "CONTACT", "ISSUES", "ISSUE", "PAGES",
                                                            "PAGE", "LABELS", "CALENDARS", "CALENDAR", "POSTS",
                                                            "CONNECTIONS", "CONNECTED", "ACCOUNTS"}:
            continue
        if words & SLUG_DRAFT and not words & {"SEND", "POST", "PUBLISH"}:
            continue
        bad.append(slug)
    return sorted(bad)


def _mcp_action(tool_name: str) -> str:
    """mcp_<server>_<action> → <action>. Server names may not contain '_' in Hermes' scheme; if
    they do, we look at every suffix and treat the call as read-only only if the tail clearly is."""
    parts = tool_name.split("_")[1:]
    return "_".join(parts[1:]) if len(parts) > 1 else "_".join(parts)


@dataclass
class Authority:
    """Compiled authority.yaml."""

    never_share: list[str] = field(default_factory=list)
    # Each permission: {"id": str, "tools": [glob-ish names], "args_regex": str (optional)}
    standing_permissions: list[dict[str, Any]] = field(default_factory=list)
    # Extra tool names the founder marks as outward / safe.
    extra_outward_tools: list[str] = field(default_factory=list)
    safe_tools: list[str] = field(default_factory=list)


@dataclass
class Decision:
    action: str            # "allow" | "approve" | "block"
    reason: str
    rule: Optional[str] = None


def _args_text(args: Any) -> str:
    try:
        return json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return str(args)


def _name_matches(pattern: str, tool_name: str) -> bool:
    if pattern.endswith("*"):
        return tool_name.startswith(pattern[:-1])
    return pattern == tool_name


def touches_protected(tool_name: str, args: Any) -> Optional[str]:
    """White must not rewrite its own code, authority or config, or its skills outside the bench-gated
    white_improve loop. (A live test caught White patching white_world.py to work around a bug.)"""
    text = _args_text(args)
    if tool_name in ("write_file", "patch") and PROTECTED_PATHS.search(text):
        return f"'{tool_name}' would change White's own code, authority or config"
    if tool_name in ("terminal", "execute_code") and PROTECTED_PATHS.search(text) and SHELL_WRITE.search(text):
        return "shell command would change White's own code, authority or config"
    if tool_name == "skill_manage" and isinstance(args, dict) and \
            str(args.get("action") or "").lower() not in ("view", "list", "read", "search", "show", ""):
        return "skill changes go through white_improve (bench-tested, with undo)"
    return None


def is_outward(tool_name: str, args: Any, authority: Authority) -> Optional[str]:
    """Return a short reason if this call is outward (or self-modifying), else None."""
    protected = touches_protected(tool_name, args)
    if protected:
        return protected  # not overridable by safe_tools
    if any(_name_matches(p, tool_name) for p in authority.safe_tools):
        return None
    if tool_name in OUTWARD_TOOLS or any(_name_matches(p, tool_name) for p in authority.extra_outward_tools):
        return f"'{tool_name}' sends something outside"
    text = _args_text(args)
    if tool_name in ("terminal", "execute_code") and OUTWARD_SHELL.search(text):
        return f"'{tool_name}' command sends something outside"
    if tool_name in SCREEN_TOOLS and OUTWARD_CLICK_WORDS.search(text):
        return f"'{tool_name}' action looks like send/submit/pay"
    if tool_name == "white_desktop" and isinstance(args, dict):
        # white-core resolves refs to the element's real name and refuses a label that hides it,
        # so the label is the trustworthy description of the target.
        label = str(args.get("label") or "")
        cmd = str(args.get("command") or "")
        if OUTWARD_CLICK_WORDS.search(label):
            return f"desktop {cmd} on '{label}' looks like send/submit/pay"
        if cmd == "press" and DESKTOP_SEND_KEYS.search(" ".join(map(str, args.get("args") or []))):
            return "desktop key press (Enter) can send a message or submit a form"
    if tool_name in ("terminal", "execute_code") and DESKTOP_RAW_ACT.search(text):
        return "raw agent-desktop action: use the white_desktop tool so the target can be checked"
    if tool_name.startswith("mcp_"):
        action = _mcp_action(tool_name)
        if ARBITRARY_CODE_TOOLS.search(action):
            return f"'{tool_name}' runs code with your connected accounts"
        slugs = outward_slugs(text)
        if slugs:
            return f"'{tool_name}' runs {', '.join(slugs[:3])}"
        if READ_MCP_PREFIX.match(action) or action.upper() in ROUTER_META_SAFE:
            return None
        if OUTWARD_MCP_VERBS.search(action):
            return f"MCP tool '{tool_name}' acts outside"
    if tool_name in ("terminal", "execute_code") and re.search(r"\bcomposio\b.*\bexecute\b", text, re.IGNORECASE):
        slugs = outward_slugs(text)
        if slugs:
            return f"'composio execute' runs {', '.join(slugs[:3])}"
    return None


def find_never_share(args: Any, authority: Authority) -> Optional[str]:
    text = _args_text(args).lower()
    for item in authority.never_share:
        item = (item or "").strip()
        if item and item.lower() in text:
            return item
    return None


def find_permission(tool_name: str, args: Any, authority: Authority) -> Optional[str]:
    text = _args_text(args)
    for perm in authority.standing_permissions:
        tools = perm.get("tools") or []
        if not any(_name_matches(str(p), tool_name) for p in tools):
            continue
        rx = perm.get("args_regex")
        if rx and not re.search(rx, text, re.IGNORECASE | re.DOTALL):
            continue
        return str(perm.get("id") or "standing-permission")
    return None


def decide(tool_name: str, args: Any, authority: Authority) -> Decision:
    try:
        reason = is_outward(tool_name, args, authority)
    except Exception as exc:  # fail closed
        return Decision("approve", f"White couldn't classify '{tool_name}' ({exc}); asking you first")
    if reason is None:
        return Decision("allow", "not an outward action")
    leaked = find_never_share(args, authority)
    if leaked:
        return Decision("block", f"Blocked: contains '{leaked}', which is on your never-share list.",
                        rule="never_share")
    perm = find_permission(tool_name, args, authority)
    if perm:
        return Decision("allow", f"covered by standing permission '{perm}'", rule=perm)
    return Decision("approve", f"White needs your OK: {reason}.", rule=f"white:{tool_name}")


# --- Loading authority.yaml ---------------------------------------------------------------------

def load_authority(path: Path) -> Authority:
    """Load authority.yaml. Missing file → empty authority (everything outward needs approval)."""
    if not path.is_file():
        return Authority()
    try:
        try:
            import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
        except ImportError:
            import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        # Unreadable policy: approve-everything-outward is the safe default.
        return Authority()
    if not isinstance(data, dict):
        return Authority()

    def _list(key: str) -> list:
        value = data.get(key) or []
        return value if isinstance(value, list) else []

    return Authority(
        never_share=[str(x) for x in _list("never_share")],
        standing_permissions=[p for p in _list("standing_permissions") if isinstance(p, dict)],
        extra_outward_tools=[str(x) for x in _list("extra_outward_tools")],
        safe_tools=[str(x) for x in _list("safe_tools")],
    )
