"""Tests for White's inbox folder. Run: python -m pytest plugins/white-core -q"""

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from white_inbox import Inbox, extract_text, load_folders  # noqa: E402


@pytest.fixture
def setup(tmp_path):
    local, drive = tmp_path / "founder" / "inbox", tmp_path / "drive"
    local.mkdir(parents=True)
    drive.mkdir()
    (tmp_path / "founder" / "inbox.yaml").write_text(f"folders:\n  - {drive}\n", encoding="utf-8")
    ib = Inbox(tmp_path / "white" / "inbox.db", load_folders(tmp_path))
    yield ib, local, drive
    ib.close()


def test_load_folders_local_plus_drive(setup, tmp_path):
    ib, local, drive = setup
    assert ib.folders == [local, drive]


def test_scan_finds_both_folders_with_text_and_source(setup):
    ib, local, drive = setup
    (local / "notes.md").write_text("Met Priya at LogiCo", encoding="utf-8")
    (drive / "call.txt").write_text("Ravi wants the model Friday", encoding="utf-8")
    items = ib.scan()
    assert {i["name"] for i in items} == {"notes.md", "call.txt"}
    assert all(i["source"].startswith("inbox:") for i in items)
    assert any("Priya" in i["text"] for i in items)


def test_rescan_is_noop_and_file_moves(setup):
    ib, local, _ = setup
    (local / "a.txt").write_text("x", encoding="utf-8")
    item = ib.scan()[0]
    assert len(ib.scan()) == 1
    res = ib.file(item["sha"], "test note", "nothing")
    assert Path(res["filed_to"]).exists() and not (local / "a.txt").exists()
    assert "Filed" in res["filed_to"]
    assert ib.scan() == []  # Filed/ is skipped


def test_file_requires_summary(setup):
    ib, local, _ = setup
    (local / "a.txt").write_text("x", encoding="utf-8")
    sha = ib.scan()[0]["sha"]
    with pytest.raises(ValueError):
        ib.file(sha, "  ")


def test_skips_hidden_and_office_lock_files(setup):
    ib, local, _ = setup
    (local / "~$deck.docx").write_text("lock", encoding="utf-8")
    (local / ".hidden").write_text("h", encoding="utf-8")
    (local / "desktop.ini").write_text("i", encoding="utf-8")
    assert ib.scan() == []


def test_docx_text_extracted(tmp_path):
    p = tmp_path / "memo.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>Seed round 500k</w:t></w:document>")
    assert "Seed round 500k" in extract_text(p)


def test_binary_without_text_gets_note(setup):
    ib, local, _ = setup
    (local / "photo.jpg").write_bytes(b"\xff\xd8\xff\x00")
    item = ib.scan()[0]
    assert item["text"] == "" and "note" in item
