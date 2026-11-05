"""Tests for White's world model. Run: python -m pytest plugins/white-core -q"""

import json
import sys
import time
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_world import World, WorldError  # noqa: E402
import white_wiki as wiki  # noqa: E402


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path / "world.db")
    yield world
    world.close()


def test_fact_without_source_rejected(w):
    with pytest.raises(WorldError):
        w.upsert("people", {"name": "Priya"})


def test_person_with_org_creates_org_and_upserts(w):
    pid = w.upsert("people", {"name": "Priya", "org": "LogiCo", "role": "Ops Head", "source": "linkedin.com/in/p"})
    assert w.org_id("logico")
    again = w.upsert("people", {"name": "priya", "org": "LogiCo", "notes": "replied", "source": "email:123"})
    assert again == pid
    row = w._rows("SELECT * FROM people")[0]
    assert row["notes"] == "replied" and row["role"] == "Ops Head"


def test_pipeline_rules(w):
    with pytest.raises(WorldError):
        w.upsert("pipeline", {"kind": "bogus", "title": "x", "stage": "new", "source": "s"})
    with pytest.raises(WorldError):
        w.upsert("pipeline", {"kind": "investor", "title": "x", "stage": "new", "next_due": "next friday", "source": "s"})
    pid = w.upsert("pipeline", {"kind": "design_partner", "title": "LogiCo pilot", "org": "LogiCo",
                                "stage": "contacted", "next_step": "follow up", "next_due": "2026-11-10",
                                "source": "email:1"})
    items = w.pipeline("design_partner")
    assert items[0]["id"] == pid and items[0]["org"] == "LogiCo"


def test_unknown_field_rejected(w):
    with pytest.raises(WorldError):
        w.upsert("orgs", {"name": "A", "source": "s", "revenue": "1cr"})


def test_overdue_commitments(w):
    w.add_commitment("founder", "send deck", "email:9", to_whom="Ravi (VC)", due="2026-11-01")
    w.add_commitment("white", "follow up", "call log", due="2026-12-01")
    overdue = w.overdue_commitments(today=date(2026, 11, 6))
    assert [c["what"] for c in overdue] == ["send deck"]


def test_stalled_pipeline(w):
    w.upsert("pipeline", {"kind": "investor", "title": "Fund A", "stage": "contacted", "source": "s"})
    w.upsert("pipeline", {"kind": "investor", "title": "Fund B", "stage": "committed", "source": "s"})
    future = time.time() + 10 * 86400
    titles = [r["title"] for r in w.stalled_pipeline(days=7, now=future)]
    assert titles == ["Fund A"]


def test_signal_dedupe_by_source(w):
    a = w.add_signal("email", "Ravi replied", "gmail:msg-1")
    b = w.add_signal("email", "Ravi replied (rescanned)", "gmail:msg-1")
    assert a == b and len(w.unhandled_signals()) == 1


def test_done_action_needs_proof(w):
    with pytest.raises(WorldError):
        w.log_action("sent intro", "done")
    assert w.log_action("sent intro", "done", proof="gmail:msg-abc")


def test_lesson_needs_evidence(w):
    with pytest.raises(WorldError):
        w.add_lesson("signal-first openers work", [])
    assert w.add_lesson("signal-first openers work", ["action:12", "action:15"], "outreach")


def test_confirm(w):
    w.upsert("orgs", {"name": "LogiCo", "source": "web"})
    assert w.confirm("orgs", "logico")
    assert w._rows("SELECT confirmed FROM orgs")[0]["confirmed"] == 1


def test_snapshot_and_wiki(w, tmp_path):
    w.upsert("people", {"name": "Priya", "org": "LogiCo", "source": "web"})
    w.upsert("pipeline", {"kind": "design_partner", "title": "LogiCo pilot", "stage": "call booked", "source": "s"})
    w.add_commitment("founder", "send deck", "email:9", due="2026-11-01")
    w.add_signal("email", "Priya replied: interested", "gmail:1")
    w.set_runway("2026-11-01", "founder said", months=9)
    w.add_lesson("warm intros convert", ["action:3"], "outreach")
    snap = w.snapshot(today=date(2026, 11, 6))
    assert snap["runway"]["months"] == 9 and len(snap["unhandled_signals"]) == 1
    pages = wiki.render(w, tmp_path / "wiki", today=date(2026, 11, 6))
    names = {p.name for p in pages}
    assert names == {"now.md", "people.md", "pipeline.md", "commitments.md", "lessons.md"}
    assert "send deck" in (tmp_path / "wiki" / "commitments.md").read_text(encoding="utf-8")
    assert "9" in (tmp_path / "wiki" / "now.md").read_text(encoding="utf-8")


def test_tool_handlers(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("white_core_pkg", Path(__file__).parent / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "_home", lambda: tmp_path)
    out = json.loads(mod.white_record({"kind": "person", "data": {"name": "A"}}))
    assert out["ok"] is False and "source" in out["error"]
    out = json.loads(mod.white_record({"kind": "person", "data": {"name": "A", "source": "web"}}))
    assert out["ok"] is True
    out = json.loads(mod.white_log({"kind": "lesson", "data": {"lesson": "x", "evidence": []}}))
    assert out["ok"] is False
    out = json.loads(mod.white_query({"view": "snapshot"}))
    assert out["ok"] is True
    out = json.loads(mod.white_wiki({}))
    assert out["ok"] is True and len(out["result"]["pages"]) == 5
