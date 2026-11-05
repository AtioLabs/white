"""Monitor source for the `white-inbox` cron job (runs every tick, no model).

Prints a stable fingerprint: the sorted names of every file in White's inbox folders,
INCLUDING Filed/. A new drop changes the output (the agent wakes once); filing a file
doesn't (it keeps its name in Filed/), so there is no second run. Stdlib only.
"""

import os
import re
import sys
from pathlib import Path

SKIP = {"desktop.ini", "thumbs.db", ".ds_store"}


def home() -> Path:
    h = os.environ.get("HERMES_HOME")
    if h:
        return Path(h)
    try:
        from hermes_constants import get_hermes_home
        return Path(get_hermes_home())
    except Exception:
        return Path(__file__).resolve().parent.parent


def folders(h: Path) -> list:
    out = [h / "founder" / "inbox"]
    cfg = h / "founder" / "inbox.yaml"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"\s*-\s*[\"']?(.+?)[\"']?\s*$", line)
            if m and not line.strip().startswith("#"):
                out.append(Path(m.group(1)).expanduser())
    return out


def fingerprint(h: Path) -> list:
    names = set()
    for f in folders(h):
        if not f.exists():
            continue
        for p in f.rglob("*"):
            if p.is_file() and p.name.lower() not in SKIP and not p.name.startswith((".", "~$")):
                names.add(p.name)
    return sorted(names)


if __name__ == "__main__":
    for n in fingerprint(home()):
        sys.stdout.write(n + "\n")
