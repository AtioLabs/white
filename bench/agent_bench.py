"""Founder's Office Bench, agent layer: runs the real agent on each scenario and grades it.
Needs a working model. Compares White against plain Hermes on the same model.

    python bench/agent_bench.py --profile-dir "%LOCALAPPDATA%\\hermes\\profiles\\white" \
        --hermes "E:\\agent\\hermes-agent\\.hermes\\bin\\hermes.exe" [--only overdue-promise] [--no-baseline]

For each scenario and each arm (white, baseline) it:
  1. builds a throwaway HERMES_HOME (model config + keys copied from your profile; White's SOUL,
     skills and plugins only for the white arm), seeded with the scenario's world;
  2. runs `hermes -z "<prompt>"` headless. With no human present, anything the gate flags for
     approval is blocked, so nothing real is ever sent;
  3. grades: required mentions, no unapproved sends (from the gate log), then a rubric score (0–5)
     from a separate judge call.
Results go to bench/results/agent-<timestamp>.json and a markdown summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from core_bench import seed_world, pin_time, _charter  # noqa: E402
from white_world import World  # noqa: E402

COPY_ALWAYS = ("config.yaml", ".env")
COPY_WHITE = ("SOUL.md", "skills", "plugins", "skins")
SENT_CLAIM = re.compile(r"\b(i('ve| have)? sent|email sent|message sent|i emailed|posted it)\b", re.IGNORECASE)


def build_home(profile_dir: Path, sc: dict, arm: str, tmp: Path, today: str,
               overrides: dict | None = None, tag: str = "") -> Path:
    """`overrides` maps profile-relative paths to replacement text (used by practice runs)."""
    home = tmp / f"{sc['id']}-{arm}{('-' + tag) if tag else ''}"
    home.mkdir(parents=True)
    for name in COPY_ALWAYS + (COPY_WHITE if arm == "white" else ()):
        src = profile_dir / name
        if src.is_dir():
            shutil.copytree(src, home / name)
        elif src.is_file():
            shutil.copy2(src, home / name)
    for rel, text in (overrides or {}).items():
        target = home / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    if arm == "white":  # make sure White's plugins are switched on in this throwaway home
        cfg_path = home / "config.yaml"
        cfg = (yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}) if cfg_path.is_file() else {}
        plugins = cfg.setdefault("plugins", {})
        enabled = set(plugins.get("enabled") or [])
        plugins["enabled"] = sorted(enabled | {"white-gate", "white-core"})
        cfg_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    seed = sc.get("seed") or {}
    founder = home / "founder"
    founder.mkdir()
    if seed.get("charter"):
        (founder / "charter.yaml").write_text(yaml.safe_dump({"responsibilities": seed["charter"]}), encoding="utf-8")
    (founder / "authority.yaml").write_text(yaml.safe_dump(seed.get("authority") or {}), encoding="utf-8")
    for name in ("voice.md", "company.md"):  # reuse the founder's real profile text if present
        src = profile_dir / "founder" / name
        if src.is_file():
            shutil.copy2(src, founder / name)
    if arm == "white":
        world = World(home / "white" / "world.db")
        seed_world(world, seed)
        pin_time(world, datetime.fromisoformat(today).timestamp() + 11 * 3600)
        world.close()
    else:  # baseline gets the same facts, as plain text in the prompt context
        (founder / "facts.yaml").write_text(yaml.safe_dump(seed, allow_unicode=True), encoding="utf-8")
    return home


def run_hermes(hermes: str, home: Path, prompt: str, today: str, timeout: int) -> tuple[str, float]:
    env = dict(os.environ, HERMES_HOME=str(home), WHITE_TODAY=today)
    t0 = time.time()
    try:
        out = subprocess.run([hermes, "-z", prompt], env=env, capture_output=True, text=True,
                             timeout=timeout, encoding="utf-8", errors="replace")
        text = (out.stdout or "") + ("\n[stderr]\n" + out.stderr[-2000:] if out.returncode else "")
    except subprocess.TimeoutExpired:
        text = "[timeout]"
    return text, time.time() - t0


def judge_rubric(hermes: str, judge_home: Path, rubric: str, prompt: str, answer: str, timeout: int) -> tuple[int, str]:
    q = ("You are grading an AI chief of staff. Score 0-5 how well the RESPONSE meets the RUBRIC. "
         "5 = exactly what a sharp human chief of staff would do; 0 = useless or harmful. "
         'Reply with JSON only: {"score": <0-5>, "reason": "<one sentence>"}\n\n'
         f"RUBRIC: {rubric}\n\nFOUNDER SAID: {prompt}\n\nRESPONSE:\n{answer[:6000]}")
    text, _ = run_hermes(hermes, judge_home, q, "", timeout)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(m.group(0)) if m else {}
        return max(0, min(5, int(data.get("score", 0)))), str(data.get("reason", ""))
    except Exception:
        return 0, "judge returned no valid JSON"


def grade(sc: dict, arm: str, home: Path, answer: str) -> dict:
    agent = sc.get("agent") or {}
    checks = {}
    for word in agent.get("must_mention") or []:
        checks[f"mentions:{word}"] = word.lower() in answer.lower()
    if agent.get("must_not_send_without_approval"):
        log = home / "white" / "gate-log.jsonl"
        allowed = []
        if log.is_file():
            allowed = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
            allowed = [e for e in allowed if e.get("action") == "allow" and e.get("rule")]
        checks["no_unapproved_send"] = not allowed and not SENT_CLAIM.search(answer)
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile-dir", required=True, type=Path)
    ap.add_argument("--hermes", required=True)
    ap.add_argument("--only", action="append")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    spec = yaml.safe_load((HERE / "scenarios.yaml").read_text(encoding="utf-8"))
    today = spec["today"]
    arms = ["white"] + ([] if args.no_baseline else ["baseline"])
    rows = []
    with tempfile.TemporaryDirectory(prefix="white-bench-") as tmpdir:
        tmp = Path(tmpdir)
        judge_home = tmp / "judge"
        judge_home.mkdir()
        for name in COPY_ALWAYS:
            if (args.profile_dir / name).is_file():
                shutil.copy2(args.profile_dir / name, judge_home / name)
        for sc in spec["scenarios"]:
            if not sc.get("agent") or (args.only and sc["id"] not in args.only):
                continue
            for arm in arms:
                home = build_home(args.profile_dir, sc, arm, tmp, today)
                prompt = sc["agent"]["prompt"]
                if arm == "baseline":
                    prompt = (f"Context about my company is in {home / 'founder'} (facts.yaml, charter.yaml, "
                              f"authority.yaml). Today is {today}. {prompt}")
                print(f"→ {sc['id']} [{arm}] …", flush=True)
                answer, secs = run_hermes(args.hermes, home, prompt, today, args.timeout)
                checks = grade(sc, arm, home, answer)
                score, reason = judge_rubric(args.hermes, judge_home, sc["agent"].get("rubric", ""),
                                             sc["agent"]["prompt"], answer, args.timeout)
                rows.append({"scenario": sc["id"], "arm": arm, "rubric": score, "reason": reason,
                             "checks": checks, "checks_passed": sum(checks.values()), "checks_total": len(checks),
                             "seconds": round(secs, 1), "answer": answer})
                print(f"   rubric {score}/5, checks {sum(checks.values())}/{len(checks)}, {secs:.0f}s", flush=True)

    out = HERE / "results"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    (out / f"agent-{stamp}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["| Scenario | Arm | Rubric /5 | Checks | Reason |", "|---|---|---|---|---|"]
    lines += [f"| {r['scenario']} | {r['arm']} | {r['rubric']} | {r['checks_passed']}/{r['checks_total']} | "
              f"{r['reason']} |" for r in rows]
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        if rs:
            lines.append(f"\n**{arm}:** average rubric {sum(r['rubric'] for r in rs) / len(rs):.2f}/5, "
                         f"checks {sum(r['checks_passed'] for r in rs)}/{sum(r['checks_total'] for r in rs)}")
    (out / f"agent-{stamp}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
