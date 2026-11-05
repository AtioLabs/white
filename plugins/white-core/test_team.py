"""Tests for White's specialist team. Run: python -m pytest plugins/white-core -q"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import white_team as team  # noqa: E402

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills" / "founder"


def test_roles_load_and_white_skills_exist():
    roles = team.load_roles()
    assert set(roles) == {"outreach", "research", "content", "finance", "ops"}
    white_skills = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    external = {"humanizer", "competitor-news-monitor", "grounded-citations"}  # Hermes built-ins
    for name, r in roles.items():
        for s in r["skills"]:
            assert s in white_skills or s in external, f"{name} references unknown skill {s}"


def test_build_card_contract():
    card = team.build_card("outreach", "Find 40 logistics design-partner prospects in Pune",
                           "CSV with 40 rows, each with signal + source URL", inputs=["company.md"],
                           responsibility="design-partners", due="2026-12-05")
    assert card["title"].startswith("[outreach]") and card["assignee"] == "white"
    assert "design-partner-hunt" in card["skills"]
    body = card["body"]
    assert "Done means:" in body and "white_review" in body and "Never send" in body
    assert "source URL" in body
    again = team.build_card("outreach", "Find 40 logistics design-partner prospects in Pune",
                            "CSV with 40 rows, each with signal + source URL", responsibility="design-partners")
    assert again["idempotency_key"] == card["idempotency_key"]


def test_rejects_bad_cards():
    with pytest.raises(team.TeamError):
        team.build_card("marketing", "x", "evidence of done")
    with pytest.raises(team.TeamError):
        team.build_card("research", "", "evidence of done")
    with pytest.raises(team.TeamError):
        team.build_card("research", "Market size", "done")
