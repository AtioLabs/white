"""Tests for `white doctor`. Run: python -m pytest plugins/white-core -q"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import white_doctor as doctor  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def by_name(checks):
    return {c["name"]: c for c in checks}


def test_empty_home_reports_fixes(tmp_path):
    checks = by_name(doctor.run(tmp_path))
    assert not checks["model configured"]["ok"] and "hermes -p white model" in checks["model configured"]["fix"]
    assert not checks["plugin white-gate enabled"]["ok"]
    assert not checks["charter.yaml"]["ok"]
    assert "problem" in doctor.format_report(list(checks.values()))


def test_ready_home(tmp_path):
    shutil.copytree(ROOT / "skills", tmp_path / "skills")
    shutil.copytree(ROOT / "plugins", tmp_path / "plugins")
    shutil.copy2(ROOT / "SOUL.md", tmp_path / "SOUL.md")
    (tmp_path / "config.yaml").write_text(
        "model: {default: gemini-flash}\nplugins: {enabled: [white-gate, white-core]}\n", encoding="utf-8")
    f = tmp_path / "founder"
    f.mkdir()
    (f / "voice.md").write_text("v")
    (f / "company.md").write_text("c")
    (f / "authority.yaml").write_text("never_share: [x]\n")
    shutil.copy2(ROOT / "plugins" / "white-core" / "charter.example.yaml", f / "charter.yaml")
    (tmp_path / "cron").mkdir()
    (tmp_path / "cron" / "jobs.json").write_text(json.dumps(
        {"jobs": [{"name": n} for n in doctor.CRON_NAMES]}), encoding="utf-8")
    checks = doctor.run(tmp_path)
    bad = [c for c in checks if not c["ok"] and c["level"] == "error"]
    assert not bad, bad
    assert doctor.format_report(checks).endswith("White is ready.")


def test_cron_auto_approve_flagged(tmp_path):
    (tmp_path / "config.yaml").write_text("approvals: {cron_mode: approve}\n", encoding="utf-8")
    assert not by_name(doctor.run(tmp_path))["scheduled runs can't auto-approve"]["ok"]


def test_composio_checks(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "mcp_servers: {composio: {url: 'https://connect.composio.dev/mcp', "
        "headers: {x-consumer-api-key: 'ck_rawsecret'}}}\n", encoding="utf-8")
    c = by_name(doctor.run(tmp_path))
    assert not c["Composio key not stored in config.yaml"]["ok"]
    (tmp_path / "config.yaml").write_text(
        "mcp_servers: {composio: {url: 'https://connect.composio.dev/mcp', "
        "headers: {x-consumer-api-key: '${COMPOSIO_CONSUMER_KEY}'}}}\n", encoding="utf-8")
    (tmp_path / ".env").write_text("COMPOSIO_CONSUMER_KEY=ak_platformkey\n", encoding="utf-8")
    c = by_name(doctor.run(tmp_path))
    assert c["Composio key not stored in config.yaml"]["ok"]
    assert c["Composio key in .env (COMPOSIO_CONSUMER_KEY)"]["ok"]
    assert not c["Composio key matches its product"]["ok"]
    report = doctor.format_report(list(c.values()))
    assert "ak_platformkey" not in report  # never echo the key


def test_composio_platform_checks(tmp_path):
    (tmp_path / ".env").write_text("COMPOSIO_API_KEY=ak_secret123\n", encoding="utf-8")
    c = by_name(doctor.run(tmp_path))
    assert "composio-setup" in c["Composio connected"]["fix"]
    (tmp_path / "config.yaml").write_text(
        "mcp_servers: {composio: {url: 'https://x/mcp', headers: {x-api-key: '${COMPOSIO_API_KEY}'}}}\n",
        encoding="utf-8")
    c = by_name(doctor.run(tmp_path))
    assert c["Composio key not stored in config.yaml"]["ok"] and c["Composio key in .env (COMPOSIO_API_KEY)"]["ok"]
    assert "Composio key matches its product" not in c
    assert not c["Composio session recorded"]["ok"]
    assert "ak_secret123" not in doctor.format_report(list(c.values()))


def test_bad_charter_flagged(tmp_path):
    (tmp_path / "founder").mkdir()
    (tmp_path / "founder" / "charter.yaml").write_text("responsibilities: [{id: x}]\n", encoding="utf-8")
    assert not by_name(doctor.run(tmp_path))["charter.yaml valid"]["ok"]
