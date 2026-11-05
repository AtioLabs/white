"""How White gets better at the job: founder feedback becomes policy, and the week gets a scorecard.

- Draft edits: store before/after and return what changed (words cut and added), so the model can
  write a precise voice lesson instead of guessing.
- Recommendations accepted or rejected: adjust that responsibility's judgment weight a little,
  within bounds, so White learns what this founder actually prioritizes. Every change is logged.
- Weekly scorecard: outcomes against targets, actions with proof, misses, and what White learned.
"""

from __future__ import annotations

import difflib
import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from white_world import World, WorldError  # type: ignore

W_MIN, W_MAX = 0.4, 1.6
REJECT_FACTOR, ACCEPT_FACTOR = 0.85, 1.05


# ---- weights --------------------------------------------------------------------------------------------

def load_weights(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    try:
        try:
            import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
        except ImportError:
            import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {str(k): float(v) for k, v in data.items()}
    except Exception:
        return {}


def save_weights(path: Path, weights: dict[str, float]) -> None:
    try:
        import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
    except ImportError:
        import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({k: round(v, 3) for k, v in sorted(weights.items())}), encoding="utf-8")


# ---- corrections ----------------------------------------------------------------------------------------

def _words(text: str) -> list[str]:
    return re.findall(r"[\w'’₹$%.-]+|[^\w\s]", text)


def diff_summary(before: str, after: str) -> dict:
    a, b = _words(before), _words(after)
    removed, added = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            removed.append(" ".join(a[i1:i2]))
        if op in ("insert", "replace"):
            added.append(" ".join(b[j1:j2]))
    return {"removed": removed, "added": added,
            "length_before": len(before.split()), "length_after": len(after.split())}


def record_draft_edit(world: World, before: str, after: str, about: str = "") -> dict:
    if not before.strip() or not after.strip():
        raise WorldError("Need both the draft White wrote ('before') and the founder's version ('after').")
    summary = diff_summary(before, after)
    world.db.execute("INSERT INTO corrections (kind, about, before, after, note, created) VALUES (?,?,?,?,?,?)",
                     ("draft_edit", about, before, after, str(summary), time.time()))
    world.db.commit()
    return summary


def record_recommendation(world: World, weights_path: Path, responsibility: str, accepted: bool,
                          note: str = "") -> dict:
    if not responsibility:
        raise WorldError("Say which responsibility the recommendation was about.")
    weights = load_weights(weights_path)
    old = weights.get(responsibility, 1.0)
    new = min(W_MAX, max(W_MIN, old * (ACCEPT_FACTOR if accepted else REJECT_FACTOR)))
    weights[responsibility] = new
    save_weights(weights_path, weights)
    kind = "accepted_recommendation" if accepted else "rejected_recommendation"
    world.db.execute("INSERT INTO corrections (kind, about, before, after, note, created) VALUES (?,?,?,?,?,?)",
                     (kind, responsibility, str(round(old, 3)), str(round(new, 3)), note, time.time()))
    world.db.commit()
    return {"responsibility": responsibility, "weight_before": round(old, 3), "weight_after": round(new, 3)}


# ---- weekly scorecard ------------------------------------------------------------------------------------

def scorecard(world: World, judged: dict, today: Optional[date] = None, days: int = 7) -> dict:
    """Combine the judgment engine's scorecard with what happened this week."""
    today = today or date.today()
    since = time.mktime((today - timedelta(days=days)).timetuple())
    q = lambda sql, p=(): [dict(r) for r in world.db.execute(sql, p).fetchall()]  # noqa: E731
    actions = q("SELECT * FROM actions WHERE created >= ?", (since,))
    done = [a for a in actions if a["status"] == "done"]
    by_resp: dict[str, int] = {}
    for a in done:
        by_resp[a["responsibility"] or "other"] = by_resp.get(a["responsibility"] or "other", 0) + 1
    corrections = q("SELECT kind, about, note FROM corrections WHERE created >= ?", (since,))
    lessons = q("SELECT lesson, evidence FROM lessons WHERE created >= ?", (since,))
    misses = []
    for card in judged.get("scorecard", []):
        if card["status"] == "behind":
            misses.append(f"{card['outcome']}: {card['current']:g}/{card['target']:g}, expected "
                          f"{card['expected_by_now']:g} by now")
    for c in judged.get("ranked", []):
        if c["kind"] == "commitment":
            misses.append(f"Promise overdue: {c['title']} ({c['why']})")
    return {
        "week_ending": str(today),
        "outcomes": judged.get("scorecard", []),
        "actions_done": len(done),
        "actions_done_by_responsibility": by_resp,
        "awaiting_approval": len([a for a in actions if a["status"] == "awaiting_approval"]),
        "failed": [a["what"] for a in actions if a["status"] == "failed"],
        "misses": misses,
        "corrections": {
            "draft_edits": sum(c["kind"] == "draft_edit" for c in corrections),
            "recommendations_accepted": sum(c["kind"] == "accepted_recommendation" for c in corrections),
            "recommendations_rejected": sum(c["kind"] == "rejected_recommendation" for c in corrections),
        },
        "lessons_learned": lessons,
    }
