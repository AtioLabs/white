"""Tests for the gap report and model advisor. Run: python -m pytest plugins/white-core -q"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import white_gaps as G  # noqa: E402
import white_models as M  # noqa: E402
from white_world import World  # noqa: E402

CHARTER = """responsibilities:
  - id: design-partners
    outcome: "5 paying design partners"
    target: 5
    start: 2026-11-01
    due: 2026-12-31
    metric: {pipeline_kind: design_partner, stages: [signed]}
"""


@pytest.fixture
def home(tmp_path):
    (tmp_path / "founder").mkdir()
    (tmp_path / "founder" / "charter.yaml").write_text(CHARTER, encoding="utf-8")
    return tmp_path


def test_gather_shows_pace(home):
    w = World(home / "white" / "world.db")
    ev = G.gather(home, w, today=date(2026, 12, 1))
    p = ev["charter_pace"][0]
    assert p["have"] == 0 and p["expected_now"] > 2 and p["behind"] is True
    assert "capabilities" in ev and "tool_usage" in ev
    w.close()


def test_write_requires_evidence_fix_owner(home):
    with pytest.raises(ValueError):
        G.write(home, [{"gap": "No sales process", "fix": "weekly pipeline review", "owner": "white"}])
    with pytest.raises(ValueError):
        G.write(home, [{"gap": "x", "evidence": "y", "fix": "z", "owner": "nobody"}])
    with pytest.raises(ValueError):
        G.write(home, [])
    p = G.write(home, [{"gap": "No outbound engine", "evidence": "0/5 partners, 2 due by now",
                        "fix": "White runs design-partner-hunt daily", "owner": "white"}], today=date(2026, 12, 1))
    assert "No outbound engine" in p.read_text(encoding="utf-8")


def test_fits():
    assert M.fits(8_000_000_000, 8.1)["fits_here"]
    assert not M.fits(70_000_000_000, 8.1)["fits_here"]
    assert not M.fits(0, 100)["fits_here"]


def test_open_models_filters_reposts_and_noise():
    data = [{"id": "org/Real-8B", "safetensors": {"total": 8_000_000_000}, "likes": 500, "cardData": {"license": "apache-2.0"}},
            {"id": "x/Real-8B-GGUF", "safetensors": {"total": 8_000_000_000}, "likes": 900},
            {"id": "y/Real-8B-uncensored", "safetensors": {"total": 8_000_000_000}, "likes": 900},
            {"id": "z/tiny-ft", "safetensors": {"total": 1_000_000_000}, "likes": 3},
            {"id": "org/Huge", "safetensors": {"total": 700_000_000_000}, "likes": 999}]
    r = M.open_models(fetch=lambda u: json.dumps(data).encode(), budget_gb=8.0)
    assert [m["id"] for m in r["models"]] == ["org/Real-8B", "org/Huge"]
    assert r["runs_here"] == ["org/Real-8B"]


def test_hardware_shape():
    h = M.hardware()
    assert h["ram_gb"] >= 0 and "model_budget_gb" in h and "runtimes" in h


def test_routing_reads_config(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "model:\n  provider: gemini\n  default: gemini-2.5-flash\nfallback_providers:\n"
        "  - provider: custom\n    model: deepseekv4.1-flash-1017\n", encoding="utf-8")
    r = M.routing(tmp_path)
    assert r["primary"]["provider"] == "gemini" and r["fallbacks"] == ["deepseekv4.1-flash-1017"]
