"""Tests for White's supervisor. Run: python -m pytest plugins/white-core -q"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

from white_supervisor import review, voice_never_words, never_share_list  # noqa: E402

VOICE = """# Founder voice
## Words they use
- ledger
## Words they never use
- synergy
- "AI-powered"
## Real examples
> Tell River what happened.
"""

GOOD = "Hi Priya, saw LogiCo is hiring 3 accountants in Pune. River records bills from a WhatsApp message. Worth 20 minutes Thursday? Asrul"


def test_clean_email_passes():
    r = review(GOOD, "cold_email", voice_md=VOICE)
    assert r.passed, r.as_dict()


def test_never_share_fails():
    r = review(GOOD + " Our burn is 4L.", "cold_email", never_share=["burn is 4L"])
    assert not r.passed and r.issues[0].check == "never_share"


def test_voice_never_words():
    assert voice_never_words(VOICE) == ["synergy", "AI-powered"]
    r = review("Our AI-powered synergy helps.", "followup", voice_md=VOICE)
    assert not r.passed and sum(i.check == "voice" for i in r.issues) == 2


def test_ai_tells():
    r = review("I hope this email finds you well. I wanted to reach out about a game-changer.", "followup")
    assert not r.passed and any(i.check == "ai_tells" for i in r.issues)


def test_length_limits():
    assert not review("word " * 130, "cold_email").passed
    assert not review("x" * 301, "linkedin_note").passed


def test_factual_work_needs_sources():
    assert not review("Seed rounds in India average ₹4 Cr.", "report").passed
    assert review("Seed rounds in India average ₹4 Cr.", "report", sources=["https://example.com/report"]).passed


def test_placeholder_fails():
    assert not review("Hi [Name], quick one.", "followup").passed


def test_proof_checked(tmp_path):
    f = tmp_path / "model.xlsx"
    f.write_text("x")
    assert review("Model ready.", "other", proof=[str(f)]).passed
    assert not review("Model ready.", "other", proof=[str(tmp_path / "missing.xlsx")]).passed
    assert review("Sent.", "other", proof=["gmail:msg-123"]).passed


def test_model_review_can_fail_and_is_called_with_draft():
    seen = {}

    def fake_llm(**kw):
        seen.update(kw)
        return SimpleNamespace(parsed={"pass": False, "issues": [
            {"severity": "fail", "check": "facts", "message": "Hiring claim not in sources"}]})

    r = review(GOOD, "cold_email", llm_structured=fake_llm, goal="book a call")
    assert not r.passed and r.issues[-1].check == "facts"
    assert "LogiCo" in seen["input"][0]["text"] and seen["purpose"] == "white.supervisor"


def test_model_failure_degrades_to_warning():
    def broken(**kw):
        raise RuntimeError("rate limited")
    r = review(GOOD, "cold_email", llm_structured=broken)
    assert r.passed and r.issues[0].severity == "warn"


def test_never_share_list(tmp_path):
    p = tmp_path / "authority.yaml"
    p.write_text("never_share: ['cap table', '']\n", encoding="utf-8")
    assert never_share_list(p) == ["cap table"]
    assert never_share_list(tmp_path / "none.yaml") == []
