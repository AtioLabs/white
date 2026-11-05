"""White's specialist team: turns a unit of work into a well-formed Kanban card for the right specialist.

The card contract is fixed in code so every specialist gets the same discipline: a goal, a checkable
"done means", inputs, role rules, and the closing duties (supervisor review, proof, logging).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

_ROLES_FILE = Path(__file__).with_name("specialists.yaml")

COMMON_RULES = [
    "Read founder/voice.md, founder/company.md and founder/authority.yaml before writing anything.",
    "Use white_query to check what's already known, and record new facts with white_record (with sources).",
    "Run white_review on your result before finishing. Fix and recheck up to 2 times.",
    "Anything that would go out in the founder's name: kanban_request_review with the draft. Never send.",
    "Finish with kanban_complete: a 1–3 sentence summary, artifacts (file paths), and proof (URLs/ids).",
    "Log the outcome with white_log kind=action (status done needs proof).",
]


class TeamError(ValueError):
    pass


def load_roles(path: Path = _ROLES_FILE) -> dict:
    try:
        import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
    except ImportError:
        import yaml
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("roles") or {}


def build_card(role: str, goal: str, done_means: str, *, inputs: Optional[list] = None,
               responsibility: str = "", due: str = "", assignee: str = "white",
               priority: int = 0, roles: Optional[dict] = None) -> dict:
    roles = roles if roles is not None else load_roles()
    if role not in roles:
        raise TeamError(f"Unknown specialist '{role}'. Use one of: {', '.join(sorted(roles))}.")
    if not goal.strip():
        raise TeamError("A card needs a goal.")
    if len(done_means.strip()) < 10:
        raise TeamError("A card needs a checkable 'done means' (what evidence proves it's finished).")
    r = roles[role]
    lines = [
        f"# {r['title']}",
        f"_{r['mission']}_",
        "",
        f"**Goal:** {goal}",
        f"**Done means:** {done_means}",
    ]
    if responsibility:
        lines.append(f"**Responsibility:** {responsibility}")
    if due:
        lines.append(f"**Due:** {due}")
    if inputs:
        lines += ["", "**Inputs:**"] + [f"- {i}" for i in inputs]
    lines += ["", "**Rules for this role:**"] + [f"- {x}" for x in r.get("rules") or []]
    lines += ["", "**Every White specialist:**"] + [f"- {x}" for x in COMMON_RULES]
    key = hashlib.sha256(f"{role}|{goal}|{responsibility}".encode()).hexdigest()[:16]
    return {
        "title": f"[{role}] {goal[:80]}",
        "assignee": assignee,
        "body": "\n".join(lines),
        "skills": list(r.get("skills") or []),
        "priority": int(priority),
        "idempotency_key": f"white-{key}",
    }
