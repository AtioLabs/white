"""White's judgment engine: decides what matters most, in code, from the world model + charter.

Code does the bookkeeping (scoring, pace, risks) so it is consistent and testable. The model
then reasons over the short ranked list to write the founder's check-in. Every item carries
the evidence it was scored on.

charter.yaml (in $HERMES_HOME/founder/):
  responsibilities:
    - id: design-partners
      outcome: "5 paying design partners"
      weight: 1.0                    # optional, default 1
      target: 5
      start: 2026-11-05              # optional; for pace
      due: 2027-01-31
      metric:
        pipeline_kind: design_partner
        stages: [signed, won]        # stages that count toward the target
      fundraising: false             # true → more urgent when runway is short
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from white_world import World  # type: ignore

DONE_STAGES_DEFAULT = ("won", "signed", "committed", "closed")
import re as _re
WAITING = _re.compile(r"\b(replied|asks?|asked|requests?|requested|waiting|send|needs?|before|deadline|"
                      r"by (mon|tue|wed|thu|fri|sat|sun|tomorrow|eod))", _re.IGNORECASE)


@dataclass
class Responsibility:
    id: str
    outcome: str
    target: float
    due: Optional[date]
    start: Optional[date] = None
    weight: float = 1.0
    metric: dict = field(default_factory=dict)
    fundraising: bool = False


@dataclass
class Item:
    kind: str          # responsibility | commitment | stalled | signal
    title: str
    score: float
    why: str
    evidence: list = field(default_factory=list)
    responsibility: Optional[str] = None

    def as_dict(self) -> dict:
        return {"kind": self.kind, "title": self.title, "score": round(self.score, 3), "why": self.why,
                "evidence": self.evidence, "responsibility": self.responsibility}


def _d(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def load_charter(path: Path) -> list[Responsibility]:
    if not path.is_file():
        return []
    try:
        import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
    except ImportError:
        import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for r in data.get("responsibilities") or []:
        if not isinstance(r, dict) or not r.get("id"):
            continue
        out.append(Responsibility(
            id=str(r["id"]), outcome=str(r.get("outcome", r["id"])), target=float(r.get("target") or 0),
            due=_d(r.get("due")), start=_d(r.get("start")), weight=float(r.get("weight") or 1.0),
            metric=dict(r.get("metric") or {}), fundraising=bool(r.get("fundraising"))))
    return out


def metric_value(world: World, resp: Responsibility, today: date) -> float:
    m = resp.metric
    if m.get("pipeline_kind"):
        stages = tuple(m.get("stages") or DONE_STAGES_DEFAULT)
        marks = ",".join("?" for _ in stages)
        row = world.db.execute(
            f"SELECT COUNT(*) FROM pipeline WHERE kind=? AND lower(stage) IN ({marks})",
            (m["pipeline_kind"], *[s.lower() for s in stages])).fetchone()
        return float(row[0])
    if m.get("overdue_commitments"):
        return float(len(world.overdue_commitments(today)))
    return 0.0


def _activity_days(world: World, resp: Responsibility, now_ts: float) -> Optional[float]:
    """Days since anything moved for this responsibility (pipeline or actions)."""
    kind = resp.metric.get("pipeline_kind")
    times = []
    if kind:
        row = world.db.execute("SELECT MAX(updated) FROM pipeline WHERE kind=?", (kind,)).fetchone()
        if row[0]:
            times.append(row[0])
    row = world.db.execute("SELECT MAX(updated) FROM actions WHERE responsibility=?", (resp.id,)).fetchone()
    if row[0]:
        times.append(row[0])
    return (now_ts - max(times)) / 86400 if times else None


def judge(world: World, charter: list[Responsibility], today: Optional[date] = None,
          now_ts: Optional[float] = None, learned: Optional[dict] = None) -> dict:
    """`learned` = per-responsibility multipliers from the founder's accept/reject history."""
    learned = learned or {}
    today = today or date.today()
    now_ts = now_ts or datetime.combine(today, datetime.min.time()).timestamp() + 12 * 3600
    runway = world.latest_runway()
    runway_months = float(runway["months"]) if runway and runway.get("months") is not None else None
    items: list[Item] = []
    challenges: list[dict] = []
    scorecard: list[dict] = []

    # 1. Responsibilities: gap × time pressure × pace × runway
    for r in charter:
        current = metric_value(world, r, today)
        lower_is_better = bool(r.metric.get("overdue_commitments"))
        if lower_is_better:
            gap = 1.0 if current > r.target else 0.0
        else:
            gap = max(0.0, (r.target - current) / r.target) if r.target else 0.0
        days_left = (r.due - today).days if r.due else None
        pressure = 1.0 if days_left is None else (2.0 if days_left <= 0 else min(2.0, 30 / max(days_left, 1) + 0.5))
        expected = None
        behind = False
        if r.start and r.due and r.due > r.start and not lower_is_better:
            frac = min(1.0, max(0.0, (today - r.start).days / (r.due - r.start).days))
            expected = round(r.target * frac, 2)
            behind = current < expected
        runway_mult = 1.5 if (r.fundraising and runway_months is not None and runway_months < 9) else 1.0
        idle = _activity_days(world, r, now_ts)
        idle_mult = 1.3 if (idle is None or idle > 7) else 1.0
        score = r.weight * learned.get(r.id, 1.0) * gap * pressure * (1.3 if behind else 1.0) * runway_mult * idle_mult
        status = "met" if gap == 0 else ("behind" if behind else "on track" if expected is not None else "open")
        scorecard.append({"id": r.id, "outcome": r.outcome, "current": current, "target": r.target,
                          "expected_by_now": expected, "due": str(r.due) if r.due else None, "status": status,
                          "days_since_activity": round(idle, 1) if idle is not None else None})
        if gap > 0:
            why = f"{current:g}/{r.target:g}"
            if days_left is not None:
                why += f", {days_left} days left"
            if behind:
                why += f", behind pace (expected {expected:g} by now)"
            if runway_mult > 1:
                why += f", runway only {runway_months:g} months"
            if idle_mult > 1:
                why += ", nothing moved in 7+ days" if idle is not None else ", no activity recorded yet"
            items.append(Item("responsibility", r.outcome, score, why,
                              evidence=[f"charter:{r.id}", "world:pipeline"], responsibility=r.id))
        if gap > 0 and (idle is None or idle > 7) and (behind or (days_left is not None and days_left < 45)):
            challenges.append({
                "about": r.id,
                "message": f"'{r.outcome}' is at {current:g}/{r.target:g}"
                           + (f" with {days_left} days left" if days_left is not None else "")
                           + (", and nothing has moved in over a week" if idle is not None else ", with no activity logged")
                           + ". This needs time this week, or the target or date should change.",
                "evidence": [f"charter:{r.id}"]})

    # 2. Overdue commitments: broken promises hurt trust, so they score high
    for c in world.overdue_commitments(today):
        late = (today - _d(c["due"])).days
        items.append(Item("commitment", f"{c['owner']} → {c['to_whom'] or '?'}: {c['what']}",
                          1.2 + min(late, 14) * 0.1, f"overdue by {late} day(s)",
                          evidence=[f"commitment:{c['id']}", c["source"]]))

    # 3. Stalled pipeline items
    for p in world.stalled_pipeline(7, now=now_ts):
        stale = (now_ts - p["updated"]) / 86400
        items.append(Item("stalled", f"[{p['kind']}] {p['title']} ({p['stage']})",
                          0.6 + min(stale, 30) * 0.02, f"no movement for {stale:.0f} days",
                          evidence=[f"pipeline:{p['id']}", p["source"]], responsibility=p.get("responsibility")))

    # 4. Unhandled signals. Someone waiting on us (a reply, a request) outranks housekeeping:
    #    a good chief of staff answers people first.
    for s in world.unhandled_signals():
        age = max(0.0, (now_ts - s["created"]) / 86400)
        waiting = bool(WAITING.search(s["summary"]))
        base = 1.4 if waiting else 0.5
        why = (f"someone is waiting on us ({age:.1f} days)" if waiting else f"unhandled for {age:.1f} days")
        items.append(Item("signal", f"{s['type']}: {s['summary']}", base + min(age, 7) * 0.05, why,
                          evidence=[f"signal:{s['id']}", s["source"]]))

    # Runway challenge
    if runway_months is not None and runway_months < 6:
        challenges.append({"about": "runway",
                           "message": f"Runway is {runway_months:g} months. Fundraising usually needs to start "
                                      "well before cash runs out; anything that doesn't move the round or revenue "
                                      "should wait.",
                           "evidence": [f"runway:{runway['as_of']}", runway["source"]]})
    if not charter:
        challenges.append({"about": "charter", "message": "White has no charter yet, so it can't judge priorities. "
                           "Set 2–3 responsibilities with targets and dates.", "evidence": []})

    items.sort(key=lambda i: i.score, reverse=True)
    top = [i.as_dict() for i in items[:7]]
    return {"date": str(today), "one_thing": top[0] if top else None, "ranked": top,
            "challenges": challenges, "scorecard": scorecard,
            "runway_months": runway_months}
