"""Plugins must run inside Hermes's Python, which has no PyYAML (only hermes_yaml / ruamel).
A bare `import yaml` in plugin code once made the gate silently ignore authority.yaml."""

import re
from pathlib import Path

PLUGINS = Path(__file__).resolve().parent.parent / "plugins"


def test_no_bare_pyyaml_imports():
    offenders = []
    for py in PLUGINS.rglob("*.py"):
        if py.name.startswith("test_"):
            continue
        lines = py.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if re.match(r"\s*import yaml\b", line):
                prev = lines[i - 1].strip() if i else ""
                if prev != "except ImportError:":
                    offenders.append(f"{py.relative_to(PLUGINS)}:{i + 1}")
    assert not offenders, f"use the hermes_yaml fallback pattern: {offenders}"
