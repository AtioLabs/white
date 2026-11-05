"""White's gap report (White 2.0, point 7): what the founder and the company lack, with the fix.

Code gathers the evidence (charter pace, world model, tool usage, rejected guesses); White adds
judgment. Every gap in the written report must cite evidence and name a fix and an owner.
Stdlib only.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

import white_judgment as judgment
from white_mastery import Mastery
import white_scout as scout
from white_world import World

OWNERS = ("white", "founder", "hire", "partner")


def gather(home: Path, world: World, today: Optional[date] = None) -> dict:
    today = today or date.today()
    charter = judgment.load_charter(home / "founder" / "charter.yaml")
    pace = []
    for r in charter:
        have = judgment.metric_value(world, r, today)
        row = {"id": r.id, "outcome": r.outcome, "have": have, "target": r.target,
               "due": str(r.due) if r.due else None}
        if r.due and r.start and r.due > r.start and r.target:
            elapsed = max(0.0, min(1.0, (today - r.start).days / (r.due - r.start).days))
            row["expected_now"] = round(r.target * elapsed, 1)
            row["behind"] = have < row["expected_now"] if not r.metric.get("overdue_commitments") else have > r.target
        pace.append(row)
    caps = scout.scan(home)
    tools = Mastery(home).report()
    rejected = [dict(r) for r in world.db.execute(
        "SELECT what FROM intents WHERE status='rejected' ORDER BY updated DESC LIMIT 10")] \
        if world.db.execute("SELECT name FROM sqlite_master WHERE name='intents'").fetchone() else []
    return {
        "date": str(today),
        "charter_pace": pace,
        "no_charter": not charter,
        "overdue_commitments": len(world.overdue_commitments(today)),
        "stalled_deals": [dict(title=s["title"], stage=s["stage"]) for s in world.stalled_pipeline(14)][:10],
        "runway": world.latest_runway(),
        "tool_usage": tools,
        "capabilities": caps,
        "rejected_guesses": rejected,
        "prompt": "Find what the founder and company LACK to hit the charter: skills, tools, people, process, "
                  "numbers, focus. One gap per row with evidence from above, the fix, and who owns the fix.",
    }


def write(home: Path, gaps: list, today: Optional[date] = None) -> Path:
    """Write founder/reports/gaps-<date>.md. Rejects gaps without evidence or a fix."""
    today = today or date.today()
    rows = []
    for g in gaps or []:
        gap, fix = str(g.get("gap") or "").strip(), str(g.get("fix") or "").strip()
        ev, owner = g.get("evidence"), str(g.get("owner") or "").strip().lower()
        if not gap or not fix:
            raise ValueError("each gap needs gap and fix")
        if not ev:
            raise ValueError(f"gap '{gap}' needs evidence")
        if owner not in OWNERS:
            raise ValueError(f"owner must be one of {', '.join(OWNERS)}")
        rows.append((gap, ev if isinstance(ev, str) else "; ".join(map(str, ev)), fix, owner))
    if not rows:
        raise ValueError("no gaps: if nothing is missing, say so to the founder instead of writing a report")
    out = home / "founder" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"gaps-{today.isoformat()}.md"
    lines = [f"# What's missing ({today.isoformat()})", "",
             "| Gap | Evidence | Fix | Who |", "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / f"gaps-{today.isoformat()}.json").write_text(json.dumps(gaps, indent=2, ensure_ascii=False), encoding="utf-8")
    return p
