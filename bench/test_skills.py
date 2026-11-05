"""Every White skill must load in Hermes: valid YAML frontmatter, name = folder, description ≤ 60 chars
ending with a period (Hermes authoring standard), and the required sections."""

from pathlib import Path

import pytest
import yaml

SKILLS = sorted((Path(__file__).resolve().parent.parent / "skills" / "founder").glob("*/SKILL.md"))


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_skill_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "must start with YAML frontmatter"
    fm = yaml.safe_load(text.split("---", 2)[1])
    assert fm["name"] == path.parent.name
    d = fm["description"]
    assert isinstance(d, str) and len(d) <= 60 and d.endswith("."), d
    assert fm["metadata"]["hermes"]["category"] == "founder"
    for section in ("## When to Use", "## Procedure"):
        assert section in text, f"missing {section}"


def test_found_all_skills():
    assert len(SKILLS) >= 14


def test_no_text_trips_hermes_injection_scanner():
    """Hermes drops a whole SOUL.md/skill if it matches its injection patterns (a 'never pretend
    to be human' line once silently removed White's personality). Mirror the risky ones here."""
    import re as _re
    root = Path(__file__).resolve().parent.parent
    files = [root / "SOUL.md", *sorted((root / "skills").rglob("SKILL.md"))]
    f = r"(?:\w+\s+){0,3}"
    pats = [rf"pretend\s+{f}(you\s+are|to\s+be)\s+", rf"you\s+are\s+{f}now\s+(?:a|an|the)\s+",
            rf"ignore\s+{f}(previous|prior|above|all)\s+{f}instructions", rf"do\s+not\s+{f}tell\s+{f}the\s+user",
            rf"output\s+{f}(system|initial)\s+prompt", rf"you\s+have\s+been\s+{f}(updated|upgraded|patched)\s+to"]
    bad = [(p.name, x) for p in files for x in pats if _re.search(x, p.read_text(encoding="utf-8"), _re.I)]
    assert not bad, bad
