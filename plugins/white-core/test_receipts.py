"""Tests for public receipts. Run: python -m pytest plugins/white-core -q"""

import hashlib
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_world import World  # noqa: E402
import white_receipts as R  # noqa: E402


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path / "world.db")
    world.upsert("pipeline", {"kind": "investor", "title": "Arka VC", "org": "Arka VC", "stage": "meeting",
                              "source": "s"})
    world.upsert("people", {"name": "Ravi Kumar", "org": "Arka VC", "source": "s"})
    world.upsert("pipeline", {"kind": "design_partner", "title": "LogiCo pilot", "org": "LogiCo",
                              "stage": "signed", "source": "s"})
    world.log_action("Sent Ravi Kumar at Arka VC the model; burn of ₹4L explained", "done", "seed-round",
                     proof="gmail:msg-abc123")
    world.log_action("LogiCo signed the pilot, ravi@arka.vc cc'd, call +91 98765 43210", "done",
                     "design-partners", proof="contract:logico-1")
    world.log_action("draft only", "awaiting_approval", "seed-round")
    world.add_lesson("Arka VC liked the WhatsApp demo", ["action:1"])
    yield world
    world.close()


def test_export_redacts_names_secrets_contacts(w):
    data = R.export(w, never_share=["burn of ₹4L"], gate_log=[
        {"ts": time.time(), "action": "approve"}, {"ts": time.time(), "action": "block"}])
    text = str(data)
    for secret in ("Ravi", "Arka", "LogiCo", "₹4L", "ravi@arka.vc", "98765"):
        assert secret.lower() not in text.lower(), secret
    assert len(data["receipts"]) == 2            # only done actions
    assert "Investor A" in data["receipts"][0]["what"]
    assert data["safety"] == {"asked_founder_first": 1, "blocked_leaks": 1, "standing_permission_uses": 0}


def test_proofs_are_verifiable_fingerprints(w):
    data = R.export(w)
    expected = "sha256:" + hashlib.sha256(b"gmail:msg-abc123").hexdigest()[:16]
    assert data["receipts"][0]["proof"] == expected
    assert "msg-abc123" not in str(data)


def test_markdown(w):
    md = R.to_markdown(R.export(w), founder="Asrul")
    assert md.startswith("# White's receipts") and "Safety" in md and "sha256:" in md
