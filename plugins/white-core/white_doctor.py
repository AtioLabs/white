"""`hermes -p white white doctor`: checks that White is set up to work, and says how to fix what isn't."""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILLS_REQUIRED = ("founder-onboarding", "white-cycle", "morning-checkin", "weekly-review", "outcome-engine")
CRON_NAMES = ("white-cycle", "white-morning", "white-weekly", "white-wiki")


def _yaml(path: Path):
    try:
        import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
    except ImportError:
        import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run(home: Path) -> list[dict]:
    """Return checks: {name, ok, level (error|warn), detail, fix}."""
    out: list[dict] = []

    def add(name, ok, detail="", fix="", level="error"):
        out.append({"name": name, "ok": bool(ok), "level": level, "detail": detail, "fix": fix})

    # Model
    cfg = {}
    cfg_path = home / "config.yaml"
    if cfg_path.is_file():
        try:
            cfg = _yaml(cfg_path)
        except Exception as e:
            add("config.yaml readable", False, str(e), "Fix the YAML syntax in config.yaml.")
    model = cfg.get("model")
    model_name = model.get("default") if isinstance(model, dict) else model
    add("model configured", bool(model_name), f"model: {model_name or '(none)'}",
        "Run: hermes -p white model")

    # Plugins
    enabled = set(((cfg.get("plugins") or {}).get("enabled")) or [])
    for p in ("white-gate", "white-core"):
        add(f"plugin {p} enabled", p in enabled, "", f"Run: hermes -p white plugins enable {p}")
        add(f"plugin {p} installed", (home / "plugins" / p / "plugin.yaml").is_file(), "",
            "Run: hermes profile update white")

    # Composio (optional): referenced by env var, never a raw key in config.yaml
    comp = (cfg.get("mcp_servers") or {}).get("composio")
    env_path = home / ".env"
    env_text = env_path.read_text(encoding="utf-8", errors="ignore") if env_path.is_file() else ""
    if isinstance(comp, dict):
        headers = comp.get("headers") or {}
        secret_hdrs = {k: str(v) for k, v in headers.items() if k.lower() in ("x-api-key", "x-consumer-api-key",
                                                                              "x-user-api-key")}
        add("Composio key not stored in config.yaml",
            all(v.startswith("${") for v in secret_hdrs.values()), "",
            "Move the key into this profile's .env and reference it as ${COMPOSIO_API_KEY} "
            "(Platform) or ${COMPOSIO_CONSUMER_KEY} (For You).")
        platform = any(k.lower() == "x-api-key" for k in secret_hdrs)
        var = "COMPOSIO_API_KEY" if platform else "COMPOSIO_CONSUMER_KEY"
        prefix = "ak_" if platform else "ck_"
        m = re.search(rf"^{var}=(\S*)", env_text, re.MULTILINE)
        add(f"Composio key in .env ({var})", bool(m and m.group(1)), "",
            f"Add {var}={prefix}... to this profile's .env.")
        if m and m.group(1) and not m.group(1).startswith(prefix):
            add("Composio key matches its product", False, f"{var} doesn't start with {prefix}",
                "Platform keys start with ak_ (header x-api-key); For You keys start with ck_ "
                "(header x-consumer-api-key).")
        if platform and not (home / "white" / "composio.json").is_file():
            add("Composio session recorded", False, "", "Run: hermes -p white white composio-setup", level="warn")
    else:
        fix = ("Run: hermes -p white white composio-setup" if re.search(r"^COMPOSIO_API_KEY=ak_", env_text, re.MULTILINE)
               else "Say 'run white-connect' to connect Gmail, Calendar, LinkedIn and more.")
        add("Composio connected", False, "not configured (optional)", fix, level="warn")

    # Approval safety
    cron_mode = ((cfg.get("approvals") or {}).get("cron_mode")) or "deny"
    add("scheduled runs can't auto-approve", cron_mode == "deny", f"approvals.cron_mode = {cron_mode}",
        "Set approvals.cron_mode: deny in config.yaml so scheduled runs can't send without you.")

    import shutil as _sh
    add("agent-desktop installed (computer use)", bool(_sh.which("agent-desktop")), "",
        "Run once: npm install -g agent-desktop", level="warn")

    # Skills and soul
    for s in SKILLS_REQUIRED:
        found = any((home / "skills").rglob(f"{s}/SKILL.md")) if (home / "skills").is_dir() else False
        add(f"skill {s}", found, "", "Run: hermes profile update white")
    add("SOUL.md is White's", (home / "SOUL.md").is_file() and "White" in (home / "SOUL.md").read_text(
        encoding="utf-8", errors="ignore"), "", "Run: hermes profile update white")

    # Founder files
    f = home / "founder"
    for name, fix in (("voice.md", "Say 'run founder-onboarding' in chat."),
                      ("company.md", "Say 'run founder-onboarding' in chat.")):
        add(f"founder/{name}", (f / name).is_file(), "", fix)
    auth = f / "authority.yaml"
    if auth.is_file():
        try:
            data = _yaml(auth)
            add("authority.yaml valid", isinstance(data, dict),
                f"{len(data.get('never_share') or [])} never-share items, "
                f"{len(data.get('standing_permissions') or [])} standing permissions")
        except Exception as e:
            add("authority.yaml valid", False, str(e), "Fix the YAML, or delete it to require approval for everything.")
    else:
        add("authority.yaml", False, "missing → everything outward needs your approval (safe)",
            "Onboarding writes it; optional.", level="warn")
    ch = f / "charter.yaml"
    if ch.is_file():
        try:
            resp = _yaml(ch).get("responsibilities") or []
            bad = [r.get("id", "?") for r in resp if not isinstance(r, dict) or "target" not in r or "metric" not in r]
            add("charter.yaml valid", resp and not bad,
                f"{len(resp)} responsibilities" + (f"; missing target/metric: {bad}" if bad else ""),
                "Each responsibility needs id, target and metric (see charter.example.yaml).")
        except Exception as e:
            add("charter.yaml valid", False, str(e), "Fix the YAML syntax.")
    else:
        add("charter.yaml", False, "White can't judge priorities without it",
            "Say 'run founder-onboarding' (step 4b) in chat.")

    # World model
    db = home / "white" / "world.db"
    if db.is_file():
        try:
            import sqlite3
            con = sqlite3.connect(str(db))
            n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                 for t in ("people", "pipeline", "commitments", "signals")}
            con.close()
            add("world model", True, ", ".join(f"{k}: {v}" for k, v in n.items()))
        except Exception as e:
            add("world model", False, str(e), "Move white/world.db aside; White recreates it.")
    else:
        add("world model", False, "not created yet", "Created on first use of a White tool.", level="warn")

    # Schedule
    jobs_file = home / "cron" / "jobs.json"
    names = set()
    if jobs_file.is_file():
        try:
            data = json.loads(jobs_file.read_text(encoding="utf-8"))
            jobs = data.get("jobs", data) if isinstance(data, dict) else data
            names = {j.get("name") for j in (jobs.values() if isinstance(jobs, dict) else jobs) if isinstance(j, dict)}
        except Exception:
            pass
    missing = [n for n in CRON_NAMES if n not in names]
    add("White's schedule", not missing, f"missing: {missing}" if missing else "all jobs present",
        "Say 'run white-cycle' in chat; step 0 creates the schedule.", level="warn")
    return out


def format_report(checks: list[dict]) -> str:
    lines = []
    for c in checks:
        mark = "✓" if c["ok"] else ("!" if c["level"] == "warn" else "✗")
        lines.append(f" {mark} {c['name']}" + (f"  ({c['detail']})" if c["detail"] else ""))
        if not c["ok"] and c["fix"]:
            lines.append(f"     → {c['fix']}")
    errors = sum(1 for c in checks if not c["ok"] and c["level"] == "error")
    warns = sum(1 for c in checks if not c["ok"] and c["level"] == "warn")
    lines.append("")
    lines.append("White is ready." if not errors else f"{errors} problem(s) to fix" + (f", {warns} warning(s)" if warns else "") + ".")
    return "\n".join(lines)
