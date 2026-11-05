"""Tests for White's learning loop. Run: python -m pytest plugins/white-core -q"""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_world import World, WorldError  # noqa: E402
from white_judgment import Responsibility, judge  # noqa: E402
import white_learning as L  # noqa: E402


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path / "world.db")
    yield world
    world.close()


def test_draft_edit_diff(w):
    s = L.record_draft_edit(w, "Hi Priya, I hope you're well. Quick question about LogiCo. Best regards, Asrul",
                            "Priya, quick question about LogiCo. A")
    assert any("hope" in r for r in s["removed"]) and any("regards" in r for r in s["removed"])
    assert s["length_after"] < s["length_before"]
    with pytest.raises(WorldError):
        L.record_draft_edit(w, "", "x")


def test_rejections_lower_weight_within_bounds(w, tmp_path):
    p = tmp_path / "weights.yaml"
    for _ in range(20):
        out = L.record_recommendation(w, p, "content", accepted=False)
    assert out["weight_after"] == L.W_MIN
    for _ in range(40):
        out = L.record_recommendation(w, p, "content", accepted=True)
    assert out["weight_after"] == L.W_MAX
    assert L.load_weights(p)["content"] == L.W_MAX


def test_learned_weight_changes_ranking(w, tmp_path):
    a = Responsibility(id="a", outcome="A", target=1, due=date(2027, 1, 1), metric={"pipeline_kind": "other", "stages": ["done"]})
    b = Responsibility(id="b", outcome="B", target=1, due=date(2027, 1, 1), metric={"pipeline_kind": "hire", "stages": ["done"]})
    today = date(2026, 12, 1)
    first = judge(w, [a, b], today=today)["one_thing"]["responsibility"]
    other = "b" if first == "a" else "a"
    flipped = judge(w, [a, b], today=today, learned={first: 0.5})["one_thing"]["responsibility"]
    assert flipped == other


def test_scorecard(w):
    w.log_action("sent intro to LogiCo", "done", "design-partners", proof="gmail:1")
    w.log_action("draft to Arka", "awaiting_approval", "seed")
    w.log_action("form submit", "failed", "accelerators")
    w.add_lesson("warm intros convert", ["action:1"])
    L.record_recommendation(w, w.path.parent / "weights.yaml", "seed", accepted=True)
    w.add_commitment("founder", "send deck", "email:9", due="2026-11-01")
    r = Responsibility(id="design-partners", outcome="5 DPs", target=5, start=date(2026, 10, 1), due=date(2027, 1, 31),
                       metric={"pipeline_kind": "design_partner", "stages": ["signed"]})
    today = date.today()
    sc = L.scorecard(w, judge(w, [r], today=today), today=today)
    assert sc["actions_done"] == 1 and sc["actions_done_by_responsibility"] == {"design-partners": 1}
    assert sc["awaiting_approval"] == 1 and sc["failed"] == ["form submit"]
    assert sc["corrections"]["recommendations_accepted"] == 1
    assert sc["lessons_learned"] and any("Promise overdue" in m for m in sc["misses"])
