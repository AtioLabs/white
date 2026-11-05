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
