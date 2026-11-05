"""Tests for practice-run decisions (no model needed). Run: python -m pytest bench -q"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins" / "white-core"))

import practice as P  # noqa: E402

CURRENT = "---\nname: x\ndescription: d.\n---\n\nRun white_review. Ask for approval before sending.\n"
SCEN = [{"id": "a"}, {"id": "b"}]


def fake_run(scores, checks_ok=True):
    def run(sc, overrides):
        return {"rubric": scores[sc["id"]], "checks": {"no_unapproved_send": checks_ok}}
    return run


def test_valid_candidate_rules():
    assert P.valid_candidate(CURRENT, CURRENT.replace("Run", "Always run"))[0]
    assert not P.valid_candidate(CURRENT, CURRENT.replace("name: x", "name: y"))[0]
    assert not P.valid_candidate(CURRENT, CURRENT.replace("white_review", "a check"))[0]
    assert not P.valid_candidate(CURRENT, CURRENT.replace("approval", "OK"))[0]


def test_adopt_only_with_gain_and_safety():
    base = P.evaluate(fake_run({"a": 2, "b": 3}), SCEN, {})
    better = P.evaluate(fake_run({"a": 4, "b": 4}), SCEN, {})
    same = P.evaluate(fake_run({"a": 2, "b": 3}), SCEN, {})
    unsafe = P.evaluate(fake_run({"a": 5, "b": 5}, checks_ok=False), SCEN, {})
    assert P.decide(base, better)[0]
    assert not P.decide(base, same)[0]
    ok, why = P.decide(base, unsafe)
    assert not ok and "broke" in why


def test_skill_path_exists():
    assert P.skill_path("morning-checkin").is_file()


def test_profile_and_scouted_skill_paths(tmp_path):
    (tmp_path / "skills" / "scouted" / "pdf").mkdir(parents=True)
    (tmp_path / "skills" / "scouted" / "pdf" / "SKILL.md").write_text("x", encoding="utf-8")
    assert P.skill_path("pdf", tmp_path).parts[-3] == "scouted"


def test_real_failure_scenarios_are_added(tmp_path):
    extra = tmp_path / "extra.json"
    extra.write_text('[{"id": "real-x", "agent": {"prompt": "p", "rubric": "r"}}]', encoding="utf-8")
    today, sc = P.load_scenarios(extra)
    assert today and sc[-1]["id"] == "real-x" and len(sc) > 1
