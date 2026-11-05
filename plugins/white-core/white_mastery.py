"""Tool mastery packs (White 2.0, point 3a): get 100% of the value out of any tool.

For each tool White learns, it keeps a pack in `founder/mastery/<tool>.json` (+ a readable .md):
- features: what the tool can do, which founder goal each serves, and where White learned it (source),
- uses: each time White used a feature, with the outcome,
- lessons: what worked, written back after each run.
Usage score = relevant features used in the last 90 days / relevant features. Stdlib only.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

WINDOW = 90 * 86400


def _slug(tool: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (tool or "").lower()).strip("-")
    if not s:
        raise ValueError("tool name required")
    return s[:60]


class Mastery:
    def __init__(self, home: Path):
        self.dir = home / "founder" / "mastery"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, tool: str) -> Path:
        return self.dir / f"{_slug(tool)}.json"

    def load(self, tool: str) -> dict:
        p = self._path(tool)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {"tool": tool, "how_to_drive": "", "features": {}, "uses": [], "lessons": []}

    def _save(self, pack: dict) -> None:
        self._path(pack["tool"]).write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        self._render(pack)

    def learn(self, tool: str, features: list, how_to_drive: str = "") -> dict:
        """Add or update features. Each: {name, what, goal (founder goal it serves, or ''), source}."""
        pack = self.load(tool)
        if how_to_drive:
            pack["how_to_drive"] = how_to_drive  # e.g. "API via Composio PLOY_*; else white_desktop"
        for f in features or []:
            name = str(f.get("name") or "").strip()
            if not name:
                continue
            if not str(f.get("source") or "").strip():
                raise ValueError(f"feature '{name}' needs a source (docs URL, changelog, tutorial)")
            pack["features"][name] = {"what": f.get("what", ""), "goal": f.get("goal", ""),
                                      "source": f["source"], "learned": time.time()}
        self._save(pack)
        return self.score(tool)

    def use(self, tool: str, feature: str, outcome: str, lesson: str = "") -> dict:
        pack = self.load(tool)
        if feature not in pack["features"]:
            raise ValueError(f"unknown feature '{feature}': learn it first")
        pack["uses"].append({"feature": feature, "outcome": outcome, "at": time.time()})
        if lesson.strip():
            pack["lessons"].append({"feature": feature, "lesson": lesson, "at": time.time()})
        self._save(pack)
        return self.score(tool)

    def score(self, tool: str, now: float | None = None) -> dict:
        pack = self.load(tool)
        now = now or time.time()
        relevant = [n for n, f in pack["features"].items() if f.get("goal")]
        used = {u["feature"] for u in pack["uses"] if now - u["at"] <= WINDOW}
        unused = [n for n in relevant if n not in used]
        pct = round(100 * (len(relevant) - len(unused)) / len(relevant)) if relevant else 0
        return {"tool": pack["tool"], "usage_pct": pct, "relevant": len(relevant),
                "unused": [{"name": n, "goal": pack["features"][n]["goal"]} for n in unused]}

    def report(self) -> list[dict]:
        out = []
        for p in sorted(self.dir.glob("*.json")):
            out.append(self.score(json.loads(p.read_text(encoding="utf-8"))["tool"]))
        return sorted(out, key=lambda r: r["usage_pct"])

    def _render(self, pack: dict) -> None:
        s = self.score(pack["tool"])
        lines = [f"# {pack['tool']}: mastery pack", "", f"White uses **{s['usage_pct']}%** of what fits your goals.", ""]
        if pack["how_to_drive"]:
            lines += [f"How White drives it: {pack['how_to_drive']}", ""]
        lines += ["| Feature | What it does | Your goal | Source |", "|---|---|---|---|"]
        for n, f in pack["features"].items():
            lines.append(f"| {n} | {f['what']} | {f['goal'] or '-'} | {f['source']} |")
        if pack["lessons"]:
            lines += ["", "## Lessons"] + [f"- {x['feature']}: {x['lesson']}" for x in pack["lessons"][-20:]]
        self._path(pack["tool"]).with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
