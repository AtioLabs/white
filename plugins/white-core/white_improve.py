"""White improves itself (White 2.0, point 7), gated by its bench.

1. failures(): mine White's real traces for what went wrong (rejected guesses and recommendations,
   gate blocks, failed actions).
2. add_scenario(): turn a failure into a bench scenario, scrubbed (emails/phones removed; anything
   on the never-share list refuses), so the same mistake is tested forever after.
3. practice(): in the background, bench/practice.py scores the current skill vs. a proposed rewrite
   on all scenarios; adopts only on a real gain with no safety check lost. Writes only to the
   profile's skills, with a backup and a line in founder/improvements.md.
4. rollback(): restore the last backup of a skill.
Never touches plugin code, the gate, or authority.yaml. Stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,60}$")


def _dir(home: Path) -> Path:
    d = home / "white" / "improve"
    d.mkdir(parents=True, exist_ok=True)
    return d


def failures(home: Path, db, days: int = 14) -> dict:
    since = time.time() - days * 86400
    has = lambda t: db.execute("SELECT name FROM sqlite_master WHERE name=?", (t,)).fetchone()  # noqa: E731
    out: dict = {"rejected_guesses": [], "corrections": [], "failed_actions": [], "gate_blocks": []}
    if has("intents"):
        out["rejected_guesses"] = [dict(what=r[0]) for r in db.execute(
            "SELECT what FROM intents WHERE status='rejected' AND updated>=?", (since,))]
    if has("corrections"):
        out["corrections"] = [dict(kind=r[0], about=r[1], note=r[2]) for r in db.execute(
            "SELECT kind, about, note FROM corrections WHERE created>=? ORDER BY created DESC LIMIT 30", (since,))]
    if has("actions"):
        out["failed_actions"] = [dict(what=r[0], status=r[1]) for r in db.execute(
            "SELECT what, status FROM actions WHERE status IN ('failed','blocked','rejected') AND created>=?",
            (since,))]
    log = home / "white" / "gate-log.jsonl"
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines()[-500:]:
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ts", 0) >= since and e.get("action") in ("block", "deny", "denied"):
                out["gate_blocks"].append({"tool": e.get("tool"), "reason": e.get("reason")})
    out["total"] = sum(len(v) for v in out.values() if isinstance(v, list))
    out["next"] = ("Group these by the skill that caused them. For each repeated failure, write a scenario "
                   "(add_scenario), then run practice on that skill.")
    return out


def _scrub(x):
    if isinstance(x, str):
        return PHONE.sub("[phone]", EMAIL.sub("[email]", x))
    if isinstance(x, list):
        return [_scrub(v) for v in x]
    if isinstance(x, dict):
        return {k: _scrub(v) for k, v in x.items()}
    return x


def add_scenario(home: Path, sc: dict, never_share: list[str]) -> dict:
    sid = str(sc.get("id") or "")
    if not SAFE_ID.match(sid):
        raise ValueError("id: lowercase words with dashes, e.g. real-missed-follow-up")
    prompt, rubric = str(sc.get("prompt") or "").strip(), str(sc.get("rubric") or "").strip()
    if not prompt or not rubric:
        raise ValueError("prompt and rubric are required (what to ask White, what good looks like)")
    clean = _scrub({"id": f"real-{sid}" if not sid.startswith("real-") else sid,
                    "title": sc.get("title") or sid, "seed": sc.get("seed") or {},
                    "agent": {"prompt": prompt, "rubric": rubric,
                              "must_mention": list(sc.get("must_mention") or []),
                              "must_not_send_without_approval": True}})
    blob = json.dumps(clean, ensure_ascii=False).lower()
    hits = [t for t in never_share if t and t.lower() in blob]
    if hits:
        raise ValueError(f"scenario mentions never-share items ({', '.join(hits[:3])}): use placeholders")
    f = _dir(home) / "scenarios.local.json"
    rows = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    rows = [r for r in rows if r["id"] != clean["id"]] + [clean]
    f.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"id": clean["id"], "scenarios": len(rows)}


def _skill_file(home: Path, skill: str) -> Path:
    if not SAFE_ID.match(skill or ""):
        raise ValueError("bad skill name")
    for sub in ("founder", "scouted"):
        p = home / "skills" / sub / skill / "SKILL.md"
        if p.is_file():
            return p
    raise ValueError(f"no skill '{skill}' in skills/founder or skills/scouted")


def _running(home: Path) -> Optional[dict]:
    pid_file = _dir(home) / "running.json"
    if not pid_file.exists():
        return None
    info = json.loads(pid_file.read_text(encoding="utf-8"))
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {info['pid']}"], capture_output=True, text=True).stdout
            alive = str(info["pid"]) in out
        else:
            os.kill(int(info["pid"]), 0)
            alive = True
    except Exception:
        alive = False
    if not alive:
        pid_file.unlink(missing_ok=True)
        return None
    return info


def practice(home: Path, skill: str, only: Optional[list] = None, popen=subprocess.Popen) -> dict:
    """Start a background practice run on one skill. One at a time."""
    _skill_file(home, skill)
    if _running(home):
        raise ValueError("a practice run is already going: check status")
    script = home / "bench" / "practice.py"
    py = shutil.which("python") or shutil.which("python3") or shutil.which("py")
    hermes = shutil.which("hermes")
    if not script.exists() or not py or not hermes:
        raise ValueError("practice needs bench/ in the profile, a system Python with PyYAML, and hermes on PATH")
    d = _dir(home)
    extra = d / "scenarios.local.json"
    cmd = [py, str(script), "--profile-dir", str(home), "--hermes", hermes, "--skill", skill,
           "--target", "profile", "--apply", "--out", str(d)]
    if extra.exists():
        cmd += ["--extra-scenarios", str(extra)]
    for o in only or []:
        cmd += ["--only", str(o)]
    stamp = time.strftime("%Y%m%d-%H%M")
    log = d / f"practice-{skill}-{stamp}.log"
    with log.open("w", encoding="utf-8") as fh:
        proc = popen(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(home))
    (d / "running.json").write_text(json.dumps({"pid": proc.pid, "skill": skill, "log": str(log),
                                                "started": time.time()}), encoding="utf-8")
    return {"started": skill, "log": str(log), "note": "takes a while (several model runs); check status later"}


def status(home: Path) -> dict:
    d = _dir(home)
    cl = d / "changelog.md"
    return {"running": _running(home),
            "recent": cl.read_text(encoding="utf-8").splitlines()[-10:] if cl.exists() else [],
            "scenarios_from_real_failures": len(json.loads((d / "scenarios.local.json").read_text(encoding="utf-8")))
            if (d / "scenarios.local.json").exists() else 0}


def rollback(home: Path, skill: str) -> dict:
    target = _skill_file(home, skill)
    backups = sorted((_dir(home) / "backups").glob(f"{skill}-*.SKILL.md"))
    if not backups:
        raise ValueError(f"no backup for '{skill}'")
    last = backups[-1]
    target.write_text(last.read_text(encoding="utf-8"), encoding="utf-8")
    last.rename(last.with_suffix(".restored"))
    log = home / "founder" / "improvements.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"- {time.strftime('%Y%m%d-%H%M')}: rolled back `{skill}` to {last.stem}\n")
    return {"restored": skill, "from": last.name}
