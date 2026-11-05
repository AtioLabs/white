"""Tests for bench-gated self-improvement. Run: python -m pytest plugins/white-core -q"""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import white_improve as I  # noqa: E402
from white_intent import Intents  # noqa: E402
from white_world import World  # noqa: E402


@pytest.fixture
def home(tmp_path):
    sk = tmp_path / "skills" / "founder" / "morning-checkin"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: morning-checkin\n---\nv1\n", encoding="utf-8")
    return tmp_path


def test_failures_mines_real_traces(home):
    w = World(home / "white" / "world.db")
    it = Intents(w.db)
    s1, s2 = w.add_signal("email", "a", "gmail:1"), w.add_signal("email", "b", "gmail:2")
    it.feedback(it.propose("Wrong guess", [s1, s2], 0.6, "none")["id"], "rejected")
    w.log_action("Draft to investor", "rejected")
    (home / "white" / "gate-log.jsonl").write_text(
        json.dumps({"ts": time.time(), "tool": "terminal", "action": "block", "reason": "never-share"}) + "\n",
        encoding="utf-8")
    f = I.failures(home, w.db)
    assert f["rejected_guesses"][0]["what"] == "Wrong guess"
    assert f["failed_actions"][0]["status"] == "rejected"
    assert f["gate_blocks"][0]["reason"] == "never-share" and f["total"] == 3
    w.close()


def test_scenario_is_scrubbed_and_never_share_refused(home):
    r = I.add_scenario(home, {"id": "missed-follow-up", "prompt": "Morning check-in.",
                              "rubric": "Leads with the overdue promise to ravi@arka.vc (+91 98450 12345)."}, [])
    rows = json.loads((home / "white" / "improve" / "scenarios.local.json").read_text(encoding="utf-8"))
    assert r["id"] == "real-missed-follow-up"
    assert "[email]" in rows[0]["agent"]["rubric"] and "[phone]" in rows[0]["agent"]["rubric"]
    assert rows[0]["agent"]["must_not_send_without_approval"] is True
    with pytest.raises(ValueError):
        I.add_scenario(home, {"id": "leak", "prompt": "x", "rubric": "mentions Project Falcon"}, ["Project Falcon"])
    with pytest.raises(ValueError):
        I.add_scenario(home, {"id": "Bad ID!", "prompt": "x", "rubric": "y"}, [])


def test_practice_needs_known_skill_and_runs_once(home, monkeypatch):
    (home / "bench").mkdir()
    (home / "bench" / "practice.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(I.shutil, "which", lambda n: f"/bin/{n}")
    calls = []

    class P:
        pid = 999999

    def popen(cmd, **kw):
        calls.append(cmd)
        return P()

    with pytest.raises(ValueError):
        I.practice(home, "white-gate", popen=popen)  # not a skill: refused
    r = I.practice(home, "morning-checkin", popen=popen)
    assert "--target" in calls[0] and "profile" in calls[0] and "--apply" in calls[0]
    assert r["started"] == "morning-checkin"
    monkeypatch.setattr(I, "_running", lambda h: {"pid": 1})
    with pytest.raises(ValueError):
        I.practice(home, "morning-checkin", popen=popen)


def test_rollback_restores_and_logs(home):
    b = home / "white" / "improve" / "backups"
    b.mkdir(parents=True)
    (b / "morning-checkin-20261101-0900.SKILL.md").write_text("---\nname: morning-checkin\n---\nv0\n", encoding="utf-8")
    I.rollback(home, "morning-checkin")
    assert "v0" in (home / "skills" / "founder" / "morning-checkin" / "SKILL.md").read_text(encoding="utf-8")
    assert "rolled back" in (home / "founder" / "improvements.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        I.rollback(home, "morning-checkin")  # backup used up


def test_status_shape(home):
    s = I.status(home)
    assert s["running"] is None and s["scenarios_from_real_failures"] == 0
