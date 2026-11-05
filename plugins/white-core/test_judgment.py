"""Tests for White's judgment engine. Run: python -m pytest plugins/white-core -q"""

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_world import World  # noqa: E402
from white_judgment import Responsibility, judge, load_charter  # noqa: E402

TODAY = date(2026, 12, 1)


def ts(d: date) -> float:
    return datetime.combine(d, datetime.min.time()).timestamp()


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path / "world.db")
    yield world
    world.close()


def dp_resp(**kw):
    base = dict(id="design-partners", outcome="5 paying design partners", target=5,
                start=date(2026, 11, 1), due=date(2027, 1, 31),
                metric={"pipeline_kind": "design_partner", "stages": ["signed"]})
    base.update(kw)
    return Responsibility(**base)


def test_no_charter_raises_challenge(w):
    out = judge(w, [], today=TODAY)
    assert any(c["about"] == "charter" for c in out["challenges"])


def test_scorecard_and_behind_pace(w):
    w.upsert("pipeline", {"kind": "design_partner", "title": "A", "stage": "signed", "source": "s"})
    out = judge(w, [dp_resp()], today=TODAY)
    card = out["scorecard"][0]
    assert card["current"] == 1 and card["target"] == 5
    assert card["status"] == "behind"          # 1/3 of the way through → expected ~1.6
    assert out["one_thing"]["responsibility"] == "design-partners"


def test_met_responsibility_not_ranked(w):
    for t in "ABCDE":
        w.upsert("pipeline", {"kind": "design_partner", "title": t, "stage": "signed", "source": "s"})
    out = judge(w, [dp_resp()], today=TODAY)
    assert out["scorecard"][0]["status"] == "met"
    assert all(i["kind"] != "responsibility" for i in out["ranked"])


def test_overdue_commitment_outranks_idle_signal(w):
    w.add_commitment("founder", "send deck to Ravi", "email:9", to_whom="Ravi", due="2026-11-25")
    w.add_signal("email", "newsletter", "gmail:2")
    out = judge(w, [], today=TODAY, now_ts=ts(TODAY))
    kinds = [i["kind"] for i in out["ranked"]]
    assert kinds.index("commitment") < kinds.index("signal")
    assert "overdue by 6" in out["ranked"][0]["why"]


def test_neglected_responsibility_challenged(w):
    out = judge(w, [dp_resp(due=date(2026, 12, 20))], today=TODAY)
    msgs = [c for c in out["challenges"] if c["about"] == "design-partners"]
    assert msgs and "0/5" in msgs[0]["message"]


def test_short_runway_boosts_fundraising_and_challenges(w):
    w.set_runway("2026-11-30", "founder said", months=4)
    seed = Responsibility(id="seed", outcome="Seed committed", target=1, due=date(2027, 3, 31),
                          metric={"pipeline_kind": "investor", "stages": ["committed"]}, fundraising=True)
    other = Responsibility(id="content", outcome="Weekly posts", target=1, due=date(2027, 3, 31),
                           metric={"pipeline_kind": "other", "stages": ["done"]})
    out = judge(w, [other, seed], today=TODAY)
    assert out["one_thing"]["responsibility"] == "seed"
    assert any(c["about"] == "runway" for c in out["challenges"])


def test_stalled_pipeline_ranked(w):
    w.upsert("pipeline", {"kind": "investor", "title": "Fund A", "stage": "contacted", "source": "email:1"})
    out = judge(w, [], today=TODAY, now_ts=ts(TODAY) + 20 * 86400)
    assert any(i["kind"] == "stalled" and "Fund A" in i["title"] for i in out["ranked"])


def test_load_charter(tmp_path):
    p = tmp_path / "charter.yaml"
    p.write_text((Path(__file__).parent / "charter.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    ch = load_charter(p)
    assert [r.id for r in ch] == ["design-partners", "follow-ups", "seed-round"]
    assert ch[2].fundraising and ch[0].due == date(2027, 1, 31)


def test_follow_ups_metric(w):
    w.add_commitment("founder", "x", "s", due="2026-11-20")
    fu = Responsibility(id="follow-ups", outcome="No overdue promises", target=0, due=None,
                        metric={"overdue_commitments": True})
    out = judge(w, [fu], today=TODAY)
    assert out["scorecard"][0]["current"] == 1 and out["scorecard"][0]["status"] != "met"
