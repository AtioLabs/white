"""Founder's Office Bench, core layer: checks White's code (judgment, gate, supervisor) on every
scenario. No model and no network. Run before every change:

    python bench/core_bench.py            # prints a score and failures, exit 1 on any failure
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "white-core"))
sys.path.insert(0, str(ROOT / "plugins" / "white-gate"))

from white_world import World  # noqa: E402
from white_judgment import Responsibility, judge, _d  # noqa: E402
from white_supervisor import review  # noqa: E402
from white_gate_rules import Authority, decide  # noqa: E402


def seed_world(world: World, seed: dict) -> list[Responsibility]:
    for p in seed.get("people") or []:
        world.upsert("people", p)
    for p in seed.get("pipeline") or []:
        p = dict(p)
        person = p.pop("person", None)
        if person:
            world.upsert("people", {"name": person, "org": p.get("org"), "source": p["source"]})
            p["person"] = person
        world.upsert("pipeline", p)
    for c in seed.get("commitments") or []:
        world.add_commitment(c["owner"], c["what"], c["source"], c.get("to_whom", ""), c.get("due"))
    for s in seed.get("signals") or []:
        world.add_signal(s["type"], s["summary"], s["source"], s.get("related"))
    if seed.get("runway"):
        r = seed["runway"]
        world.set_runway(r["as_of"], r["source"], months=r.get("months"))
    return _charter(seed)


def pin_time(world: World, ts: float) -> None:
    """Seeded rows were created 'just now' in scenario time, not wall-clock time."""
    for table in ("people", "orgs", "pipeline", "commitments"):
        world.db.execute(f"UPDATE {table} SET created=?, updated=?", (ts, ts))
    world.db.execute("UPDATE signals SET created=?", (ts,))
    world.db.commit()


def _charter(seed: dict) -> list[Responsibility]:
    return [Responsibility(id=r["id"], outcome=r.get("outcome", r["id"]), target=float(r.get("target", 0)),
                           due=_d(r.get("due")), start=_d(r.get("start")), weight=float(r.get("weight", 1)),
                           metric=r.get("metric") or {}, fundraising=bool(r.get("fundraising")))
            for r in seed.get("charter") or []]


def authority_from(seed: dict) -> Authority:
    a = seed.get("authority") or {}
    return Authority(never_share=a.get("never_share") or [],
                     standing_permissions=a.get("standing_permissions") or [])


def run(path: Path = Path(__file__).parent / "scenarios.yaml") -> dict:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    today = _d(spec["today"])
    now_ts = datetime.combine(today, datetime.min.time()).timestamp() + 12 * 3600
    results = []
    for sc in spec["scenarios"]:
        seed, core = sc.get("seed") or {}, sc.get("core") or {}
        checks: list[tuple[str, bool, str]] = []
        with tempfile.TemporaryDirectory() as tmp:
            world = World(Path(tmp) / "world.db")
            try:
                charter = seed_world(world, seed)
                pin_time(world, now_ts - 3600)
                if "judge" in core:
                    exp = core["judge"]
                    out = judge(world, charter, today=today, now_ts=now_ts)
                    one = out["one_thing"] or {}
                    if "one_thing_kind" in exp:
                        checks.append(("judge.one_thing_kind", one.get("kind") == exp["one_thing_kind"],
                                       f"got {one.get('kind')}"))
                    if "one_thing_contains" in exp:
                        checks.append(("judge.one_thing_contains", exp["one_thing_contains"].lower() in
                                       (one.get("title", "")).lower(), f"got {one.get('title')}"))
                    if "one_thing_responsibility" in exp:
                        checks.append(("judge.one_thing_responsibility",
                                       one.get("responsibility") == exp["one_thing_responsibility"],
                                       f"got {one.get('responsibility')}"))
                    if "challenge_about" in exp:
                        abouts = [c["about"] for c in out["challenges"]]
                        checks.append(("judge.challenge", exp["challenge_about"] in abouts, f"got {abouts}"))
                    for rid, status in (exp.get("scorecard_status") or {}).items():
                        got = {c["id"]: c["status"] for c in out["scorecard"]}.get(rid)
                        checks.append((f"judge.scorecard.{rid}", got == status, f"got {got}"))
            finally:
                world.close()
        auth = authority_from(seed)
        for g in core.get("gate") or []:
            got = decide(g["tool"], g.get("args") or {}, auth).action
            checks.append((f"gate.{g['tool']}", got == g["expect"], f"expected {g['expect']}, got {got}"))
        never = (seed.get("authority") or {}).get("never_share") or []
        for r in core.get("review") or []:
            got = review(r["text"], r["kind"], never_share=never).passed
            checks.append((f"review.{r['kind']}", got == r["expect_pass"],
                           f"expected pass={r['expect_pass']}, got {got}"))
        results.append({"id": sc["id"], "title": sc["title"],
                        "passed": sum(ok for _, ok, _ in checks), "total": len(checks),
                        "failures": [{"check": c, "detail": d} for c, ok, d in checks if not ok]})
    passed = sum(r["passed"] for r in results)
    total = sum(r["total"] for r in results)
    return {"score": round(100 * passed / total, 1) if total else 0.0, "passed": passed, "total": total,
            "scenarios": results}


if __name__ == "__main__":
    report = run()
    for r in report["scenarios"]:
        mark = "PASS" if not r["failures"] else "FAIL"
        print(f"[{mark}] {r['id']:<26} {r['passed']}/{r['total']}  {r['title']}")
        for f in r["failures"]:
            print(f"        - {f['check']}: {f['detail']}")
    print(f"\nCore bench: {report['score']}% ({report['passed']}/{report['total']} checks)")
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    (out / "core.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    sys.exit(0 if report["passed"] == report["total"] else 1)
