"""Tests for White's intent engine. Run: python -m pytest plugins/white-core -q"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_intent import ACT_AT, IntentError, Intents, decide  # noqa: E402
from white_world import World  # noqa: E402


@pytest.fixture
def env(tmp_path):
    w = World(tmp_path / "world.db")
    s1 = w.add_signal("inbox", "Founder dropped essay", "inbox:aa")
    s2 = w.add_signal("email", "Investor asked for deck", "gmail:1")
    s3 = w.add_signal("email", "Second investor intro", "gmail:2")
    yield Intents(w.db), (s1, s2, s3)
    w.close()


def test_policy():
    assert decide(0.9, "none") == "act"
    assert decide(0.9, "risky") == "ask"
    assert decide(0.5, "none") == "ask"
    assert decide(0.2, "none") == "wait"
    assert decide(0.2, "risky") == "wait"


def test_no_evidence_no_intent(env):
    it, _ = env
    with pytest.raises(IntentError):
        it.propose("Raise a seed round", [], 0.9, "none")
    with pytest.raises(IntentError):
        it.propose("Raise a seed round", [9999], 0.9, "none")  # fake signal id


def test_pattern_acts_but_risky_asks(env):
    it, (s1, s2, s3) = env
    assert it.propose("Prepare fundraise story", [s1, s2, s3], 0.85, "none")["decision"] == "act"
    assert it.propose("Email investors the essay", [s2, s3], 0.9, "risky")["decision"] == "ask"


def test_single_signal_never_acts_alone(env):
    it, (s1, _, _) = env
    r = it.propose("Publish the essay", [s1], 0.99, "none")
    assert r["decision"] == "ask" and r["confidence"] < ACT_AT


def test_quiet_is_a_logged_decision(env):
    it, _ = env
    assert it.quiet("only newsletters since last cycle") > 0
    with pytest.raises(IntentError):
        it.quiet("  ")


def test_feedback_shifts_trust(env):
    it, (s1, s2, s3) = env
    a = it.propose("A", [s2, s3], 0.6, "none")
    it.feedback(a["id"], "rejected")
    b = it.propose("B", [s2, s3], 0.6, "none")
    it.feedback(b["id"], "rejected")
    assert it.weight("email") < 0.5
    c = it.propose("C", [s2, s3], 0.75, "none")
    assert c["decision"] != "act"  # White learned email-only guesses get rejected


def test_focus_limit_and_duplicates(env):
    it, (s1, s2, s3) = env
    it.propose("One", [s1, s2], 0.5, "none")
    with pytest.raises(IntentError):
        it.propose("one", [s1, s2], 0.5, "none")
    it.propose("Two", [s1, s2], 0.5, "none")
    it.propose("Three", [s1, s2], 0.5, "none")
    with pytest.raises(IntentError):
        it.propose("Four", [s1, s2], 0.5, "none")


def test_context_shape(env):
    it, _ = env
    ctx = it.context()
    assert len(ctx["signals"]) == 3 and ctx["policy"]["max_open"] == 3
