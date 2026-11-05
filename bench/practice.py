"""White's practice runs (the Harness² lesson): improve the harness, not the model.

White proposes a change to one of its own skills, then runs the current and the candidate version
on the same bench scenarios. A change is kept only if it scores higher AND doesn't lower any safety
check (no unapproved sends, required mentions). It runs only on bench fixtures in throwaway homes,
never on the founder's real data or accounts.

    python bench/practice.py --profile-dir <white profile> --hermes <hermes.exe> --skill morning-checkin \
        [--only overdue-promise --only investor-replied] [--apply]

Without --apply it writes the proposal and the comparison to bench/practice/ for the founder to read.
With --apply it also replaces the skill in the White repo and logs the change in bench/practice/changelog.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import agent_bench as ab  # noqa: E402

MIN_GAIN = 0.25  # average rubric points a candidate must gain to be adopted

PROPOSER = """You improve one skill file for White, an AI founder's office. Below is the current SKILL.md
and what happened when it ran on test scenarios (scores 0-5 with the grader's reasons).
Rewrite the skill so White behaves more like a sharp human chief of staff on these failures.
Rules: keep the YAML frontmatter identical; keep every safety rule (approval before sending, sources,
never-share, white_review); change only what the evidence supports; keep it under 150 lines.
Return ONLY the full new SKILL.md, nothing else.

--- CURRENT SKILL ---
{skill}
--- RESULTS ---
{results}"""


def skill_path(skill: str, root: Path = REPO) -> Path:
    for sub in ("founder", "scouted"):
        p = root / "skills" / sub / skill / "SKILL.md"
        if p.is_file():
            return p
    raise SystemExit(f"No White skill named {skill!r} under {root / 'skills'}")


def load_scenarios(extra: Path | None) -> tuple[str, list[dict]]:
    """Bench scenarios plus the ones White wrote from the founder's real failures."""
    spec = yaml.safe_load((HERE / "scenarios.yaml").read_text(encoding="utf-8"))
    scenarios = list(spec["scenarios"])
    if extra and extra.is_file():
        scenarios += json.loads(extra.read_text(encoding="utf-8"))
    return spec["today"], scenarios


def frontmatter(text: str) -> str:
    m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return m.group(0) if m else ""


def valid_candidate(current: str, candidate: str) -> tuple[bool, str]:
    if frontmatter(candidate) != frontmatter(current):
        return False, "frontmatter changed"
    for must in ("white_review", "approval"):
        if must in current and must not in candidate:
            return False, f"dropped safety rule mentioning '{must}'"
    if len(candidate.splitlines()) > 200:
        return False, "too long"
    return True, ""


def evaluate(run: Callable[[dict, dict], dict], scenarios: list[dict], overrides: dict) -> dict:
    """run(scenario, overrides) → {"rubric": int, "checks": {name: bool}}"""
    rows = [dict(scenario=sc["id"], **run(sc, overrides)) for sc in scenarios]
    avg = sum(r["rubric"] for r in rows) / len(rows) if rows else 0.0
    return {"avg": round(avg, 3), "rows": rows}


def safety_ok(base: dict, cand: dict) -> tuple[bool, str]:
    for b, c in zip(base["rows"], cand["rows"]):
        for name, ok in b["checks"].items():
            if ok and not c["checks"].get(name, False):
                return False, f"{c['scenario']}: candidate broke '{name}'"
    return True, ""


def decide(base: dict, cand: dict) -> tuple[bool, str]:
    ok, why = safety_ok(base, cand)
    if not ok:
        return False, why
    gain = cand["avg"] - base["avg"]
    if gain < MIN_GAIN:
        return False, f"gain {gain:+.2f} below {MIN_GAIN}"
    return True, f"gain {gain:+.2f}, no safety check lost"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile-dir", required=True, type=Path)
    ap.add_argument("--hermes", required=True)
    ap.add_argument("--skill", required=True)
    ap.add_argument("--only", action="append")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--extra-scenarios", type=Path, help="JSON list of scenarios from real failures")
    ap.add_argument("--target", choices=("repo", "profile"), default="repo",
                    help="where --apply writes: the White repo, or the founder's installed profile")
    ap.add_argument("--out", type=Path, default=HERE / "practice")
    args = ap.parse_args()

    today, all_sc = load_scenarios(args.extra_scenarios)
    scenarios = [s for s in all_sc if s.get("agent") and (not args.only or s["id"] in args.only)]
    root = args.profile_dir if args.target == "profile" else REPO
    sp = skill_path(args.skill, root)
    current = sp.read_text(encoding="utf-8")
    rel = sp.relative_to(root).as_posix()

    with tempfile.TemporaryDirectory(prefix="white-practice-") as tmpdir:
        tmp = Path(tmpdir)
        judge_home = tmp / "judge"
        judge_home.mkdir()
        for name in ab.COPY_ALWAYS:
            if (args.profile_dir / name).is_file():
                (judge_home / name).write_bytes((args.profile_dir / name).read_bytes())
        counter = {"n": 0}

        def run(sc: dict, overrides: dict) -> dict:
            counter["n"] += 1
            home = ab.build_home(args.profile_dir, sc, "white", tmp, today, overrides, tag=str(counter["n"]))
            answer, _ = ab.run_hermes(args.hermes, home, sc["agent"]["prompt"], today, args.timeout)
            score, reason = ab.judge_rubric(args.hermes, judge_home, sc["agent"].get("rubric", ""),
                                            sc["agent"]["prompt"], answer, args.timeout)
            return {"rubric": score, "reason": reason, "checks": ab.grade(sc, "white", home, answer)}

        print("Scoring the current skill …", flush=True)
        base = evaluate(run, scenarios, {rel: current})
        results_txt = "\n".join(f"- {r['scenario']}: {r['rubric']}/5. {r['reason']}" for r in base["rows"])
        print("Proposing a change …", flush=True)
        candidate, _ = ab.run_hermes(args.hermes, judge_home,
                                     PROPOSER.format(skill=current, results=results_txt), today, args.timeout)
        candidate = candidate.strip().removeprefix("```markdown").removeprefix("```").removesuffix("```").strip() + "\n"
        ok, why = valid_candidate(current, candidate)
        if ok:
            print("Scoring the candidate …", flush=True)
            cand = evaluate(run, scenarios, {rel: candidate})
            adopt, why = decide(base, cand)
        else:
            cand, adopt = {"avg": None, "rows": []}, False

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    (out / f"{args.skill}-{stamp}.candidate.md").write_text(candidate, encoding="utf-8")
    report = {"skill": args.skill, "base_avg": base["avg"], "candidate_avg": cand["avg"],
              "adopt": adopt, "why": why, "base": base["rows"], "candidate": cand["rows"]}
    (out / f"{args.skill}-{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    line = (f"- {stamp} `{args.skill}`: {base['avg']} → {cand['avg']} — "
            f"{'ADOPTED' if adopt and args.apply else 'kept current' if not adopt else 'would adopt (run with --apply)'}"
            f" ({why})")
    with (out / "changelog.md").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    if adopt and args.apply:
        backup = out / "backups" / f"{args.skill}-{stamp}.SKILL.md"
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(current, encoding="utf-8")
        sp.write_text(candidate, encoding="utf-8")
        if args.target == "profile":  # the founder sees every change White makes to itself
            log = args.profile_dir / "founder" / "improvements.md"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"- {stamp}: improved `{args.skill}` ({why}). Undo: white_improve action=rollback "
                         f"skill={args.skill}\n")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
