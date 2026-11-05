"""Tests for memory that ages. Run: python -m pytest plugins/white-core -q"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import white_memory as M  # noqa: E402
from white_intent import Intents  # noqa: E402
from white_world import World  # noqa: E402


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path / "world.db")
    yield world
    world.close()


def test_changes_keep_history_with_source(w):
    w.upsert("people", {"name": "Meera", "org": "Lumen", "role": "Ops Lead", "source": "inbox:a"})
    w.upsert("people", {"name": "Meera", "org": "Lumen", "role": "Head of Ops", "source": "gmail:9"})
    h = M.history(w.db, "people", "Meera")
    assert h["now"]["role"] == "Head of Ops"
    assert h["before"][0]["value"] == "Ops Lead" and h["before"][0]["source"] == "inbox:a"


def test_as_of_returns_what_was_known_then(w):
    w.upsert("pipeline", {"kind": "customer", "title": "Lumen pilot", "stage": "discovery", "source": "inbox:a"})
    t = time.time() + 0.01
    time.sleep(0.02)
    w.upsert("pipeline", {"kind": "customer", "title": "Lumen pilot", "stage": "signed", "source": "gmail:2"})
    assert M.as_of(w.db, "pipeline", "Lumen pilot", t)["stage"] == "discovery"
    assert M.as_of(w.db, "pipeline", "Lumen pilot", time.time())["stage"] == "signed"


def test_consolidate_merges_flags_archives_expires(w):
    now = time.time()
    w.db.execute("INSERT INTO people (name, source, created, updated) VALUES ('Ravi  K', 's1', 1, 1)")
    w.db.execute("INSERT INTO people (name, source, created, updated) VALUES ('ravi k', 's2', 1, 1)")
    sid = w.add_signal("email", "old", "gmail:old")
    w.db.execute("UPDATE signals SET handled=1, created=? WHERE id=?", (now - 90 * 86400, sid))
    it = Intents(w.db)
    s1, s2 = w.add_signal("email", "a", "gmail:a"), w.add_signal("email", "b", "gmail:b")
    i = it.propose("Old guess", [s1, s2], 0.5, "none")["id"]
    w.db.execute("UPDATE intents SET created=? WHERE id=?", (now - 20 * 86400, i))
    w.db.commit()
    r = M.consolidate(w.db, now)
    assert r["merged_people"] == 1 and r["archived_signals"] == 1 and r["expired_guesses"] == 1
    assert any("Ravi" in s for s in r["stale_to_recheck"])
    assert w.add_signal("email", "old again", "gmail:old") == sid  # archived = still seen
