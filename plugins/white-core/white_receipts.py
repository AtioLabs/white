"""Public receipts: a shareable, verifiable log of what White actually did ("receipts, not counters").

Safe to publish by construction:
  - names of people and orgs in the world model are replaced with stable pseudonyms ("Investor A"),
  - never-share strings are redacted,
  - proofs are published as SHA-256 fingerprints, not raw ids. The founder can later reveal a proof,
    and anyone can check it matches the fingerprint.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional

from white_world import World  # type: ignore

KIND_LABEL = {"investor": "Investor", "design_partner": "Design partner", "customer": "Customer",
              "accelerator": "Program", "partner": "Partner", "hire": "Candidate", "other": "Contact"}


def _fingerprint(proof: str) -> str:
    return "sha256:" + hashlib.sha256(proof.encode("utf-8")).hexdigest()[:16]


def _pseudonyms(world: World) -> dict[str, str]:
    """Map every known name to a stable public label."""
    names: dict[str, str] = {}
    counters: dict[str, int] = {}

    def label(prefix: str) -> str:
        counters[prefix] = counters.get(prefix, 0) + 1
        n = counters[prefix]
        return f"{prefix} {chr(64 + n) if n <= 26 else n}"

    for row in world.db.execute("SELECT p.title, p.kind, o.name AS org, pe.name AS person FROM pipeline p "
                                "LEFT JOIN orgs o ON o.id=p.org_id LEFT JOIN people pe ON pe.id=p.person_id "
                                "ORDER BY p.id"):
        prefix = KIND_LABEL.get(row["kind"], "Contact")
        for name in (row["org"], row["title"]):
            if name and name.lower() not in names:
                names[name.lower()] = label(prefix)
        if row["person"] and row["person"].lower() not in names:
            names[row["person"].lower()] = f"a person at {names.get((row['org'] or '').lower(), label(prefix))}"
    for (name,) in world.db.execute("SELECT name FROM orgs ORDER BY id"):
        if name.lower() not in names:
            names[name.lower()] = label("Company")
    for (name,) in world.db.execute("SELECT name FROM people ORDER BY id"):
        if name.lower() not in names:
            names[name.lower()] = label("Person")
    return names


def redact(text: str, names: dict[str, str], never_share: list[str]) -> str:
    for secret in sorted((s for s in never_share if s.strip()), key=len, reverse=True):
        text = re.sub(re.escape(secret), "[redacted]", text, flags=re.IGNORECASE)
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(name)}\b", names[name], text, flags=re.IGNORECASE)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", text)
    text = re.sub(r"\+?\d[\d\s-]{8,}\d", "[phone]", text)
    return text


def export(world: World, *, days: int = 7, never_share: Optional[list] = None,
           gate_log: Optional[list] = None, today: Optional[date] = None) -> dict:
    today = today or date.today()
    since = time.mktime((today - timedelta(days=days)).timetuple())
    names = _pseudonyms(world)
    ns = never_share or []
    actions = [dict(r) for r in world.db.execute(
        "SELECT * FROM actions WHERE status='done' AND created >= ? ORDER BY created", (since,))]
    receipts = [{
        "when": datetime.fromtimestamp(a["created"]).strftime("%Y-%m-%d %H:%M"),
        "what": redact(a["what"], names, ns),
        "responsibility": a["responsibility"] or None,
        "proof": _fingerprint(a["proof"]),
    } for a in actions]
    stages = [dict(r) for r in world.db.execute(
        "SELECT kind, stage, COUNT(*) AS n FROM pipeline GROUP BY kind, stage ORDER BY kind, stage")]
    lessons = [redact(r[0], names, ns) for r in world.db.execute(
        "SELECT lesson FROM lessons WHERE created >= ? ORDER BY created", (since,))]
    log = [e for e in (gate_log or []) if e.get("ts", 0) >= since]
    safety = {
        "asked_founder_first": sum(e.get("action") == "approve" for e in log),
        "blocked_leaks": sum(e.get("action") == "block" for e in log),
        "standing_permission_uses": sum(e.get("action") == "allow" for e in log),
    }
    return {"period": f"{today - timedelta(days=days)} to {today}", "receipts": receipts,
            "pipeline": stages, "lessons": lessons, "safety": safety,
            "how_to_verify": "Each proof is the first 16 hex chars of SHA-256 of the original proof id. "
                             "The founder can reveal any proof id; anyone can hash it and compare."}


def to_markdown(data: dict, founder: str = "the founder") -> str:
    lines = [f"# White's receipts: {data['period']}", "",
             f"What White, the AI founder's office working with {founder}, actually did. Each line has a proof fingerprint.", ""]
    lines += [f"- {r['when']}: {r['what']}" + (f" _({r['responsibility']})_" if r["responsibility"] else "")
              + f" `{r['proof']}`" for r in data["receipts"]] or ["- Nothing completed this period."]
    s = data["safety"]
    lines += ["", "## Safety", f"- Asked the founder before acting outward: {s['asked_founder_first']} times",
              f"- Blocked possible leaks: {s['blocked_leaks']}",
              f"- Used a standing permission: {s['standing_permission_uses']} times", "", "## Pipeline now"]
    lines += [f"- {KIND_LABEL.get(p['kind'], p['kind'])} / {p['stage']}: {p['n']}" for p in data["pipeline"]] or ["- empty"]
    if data["lessons"]:
        lines += ["", "## Learned"] + [f"- {x}" for x in data["lessons"]]
    lines += ["", f"_{data['how_to_verify']}_"]
    return "\n".join(lines)


def load_gate_log(path) -> list:
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []
