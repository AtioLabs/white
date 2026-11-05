"""Tests for White's desktop wrapper (agent-desktop). Run: python -m pytest plugins/white-core -q"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import white_desktop as D  # noqa: E402

SNAP = {"ok": True, "data": {"tree": [
    {"ref_id": "@s1:e3", "role": "button", "name": "File"},
    {"ref_id": "@s1:e8", "role": "button", "name": "Send", "children": [
        {"ref_id": "@s1:e9", "role": "text", "name": None}]}]}}


def fake(calls):
    def runner(argv):
        calls.append(argv)
        return SNAP if argv[0] == "snapshot" else {"ok": True, "data": {}}
    return runner


def setup_function():
    D._seen.clear()


def test_act_needs_snapshot_ref_first():
    calls = []
    assert not D.run("click", ref="@s1:e3", label="File", runner=fake(calls))["ok"]
    D.run("snapshot", ["--app", "Mail", "-i"], runner=fake(calls))
    assert D.run("click", ref="@s1:e3", label="File", runner=fake(calls))["ok"]
    assert calls[-1] == ["click", "@s1:e3"]


def test_label_cannot_hide_send_button():
    calls = []
    D.run("snapshot", ["--app", "Mail"], runner=fake(calls))
    r = D.run("click", ref="@s1:e8", label="OK", runner=fake(calls))
    assert not r["ok"] and "Send" in r["error"]
    assert D.run("click", ref="@s1:e8", label="Send", runner=fake(calls))["ok"]


def test_rejects_bad_ref_and_unknown_command():
    assert not D.run("click", ref="@e8", label="x", runner=fake([]))["ok"]
    assert not D.run("format-disk", runner=fake([]))["ok"]


def test_nested_refs_indexed():
    D.run("snapshot", runner=fake([]))
    assert D.target_of("@s1:e9") == ("text", "")


def test_not_installed_message(monkeypatch):
    monkeypatch.setattr(D.shutil, "which", lambda _: None)
    assert D.run("version")["error"]["code"] == "NOT_INSTALLED"
