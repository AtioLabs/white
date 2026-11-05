"""White's inbox: a folder the founder drops anything into (White 2.0, point 1).

Sources: the local folder `$HERMES_HOME/founder/inbox/` plus any extra folders in
`founder/inbox.yaml` (e.g. a Google Drive for desktop folder, so phone drops land too).

Flow: scan -> new or changed files become items (keyed by content hash, so re-scans are no-ops)
-> White reads the text, records facts with source `inbox:<sha>` and does the work they imply
-> `file` moves the original to `<folder>/Filed/YYYY-MM/` and logs what was done.
Stdlib only.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS inbox_items (
  sha TEXT PRIMARY KEY, path TEXT NOT NULL, name TEXT NOT NULL, folder TEXT NOT NULL,
  size INTEGER, status TEXT DEFAULT 'new', summary TEXT, work TEXT, filed_to TEXT,
  created REAL, updated REAL);
"""

FILED = "Filed"
SKIP_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".html", ".htm", ".eml", ".log", ".tsv"}
MAX_TEXT = 12000
MAX_BYTES = 50 * 1024 * 1024


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_folders(home: Path) -> list[Path]:
    """Local inbox first, then extra folders listed in founder/inbox.yaml (`folders: [..]`)."""
    folders = [home / "founder" / "inbox"]
    cfg = home / "founder" / "inbox.yaml"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*-\s*[\"']?(.+?)[\"']?\s*$", line)
            if m and not line.strip().startswith("#"):
                folders.append(Path(m.group(1)).expanduser())
    seen, out = set(), []
    for f in folders:
        k = str(f).lower()
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def extract_text(path: Path) -> str:
    """Best-effort text. Plain text, .docx/.pptx/.xlsx (zip XML) built in; PDF if pypdf is installed."""
    ext = path.suffix.lower()
    try:
        if ext in TEXT_EXT:
            return path.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT]
        if ext in {".docx", ".pptx", ".xlsx"}:
            parts = []
            with zipfile.ZipFile(path) as z:
                for n in sorted(z.namelist()):
                    if n.endswith(".xml") and (n.startswith("word/document") or n.startswith("ppt/slides/slide")
                                               or n == "xl/sharedStrings.xml"):
                        xml = z.read(n).decode("utf-8", errors="replace")
                        parts.append(re.sub(r"<[^>]+>", " ", xml))
            return re.sub(r"\s+", " ", " ".join(parts)).strip()[:MAX_TEXT]
        if ext == ".pdf":
            try:
                from pypdf import PdfReader  # optional
            except ImportError:
                return ""
            return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)[:MAX_TEXT]
    except Exception:
        return ""
    return ""


class Inbox:
    def __init__(self, db_path: Path, folders: list[Path]):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.folders = folders

    def close(self) -> None:
        self.db.close()

    def _files(self):
        for folder in self.folders:
            if not folder.exists():
                continue
            for p in folder.rglob("*"):
                rel = p.relative_to(folder).parts
                if (not p.is_file() or rel[0] == FILED or p.name.lower() in SKIP_NAMES
                        or any(part.startswith(".") or part.startswith("~$") for part in rel)):
                    continue
                yield folder, p

    def scan(self) -> list[dict]:
        """Register new files. Returns every item still waiting (new), with extracted text."""
        now = time.time()
        for folder, p in self._files():
            try:
                size = p.stat().st_size
                if size > MAX_BYTES:
                    continue
                sha = _sha(p)
            except OSError:  # still syncing / locked
                continue
            self.db.execute(
                "INSERT INTO inbox_items(sha,path,name,folder,size,created,updated) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(sha) DO UPDATE SET path=excluded.path, updated=excluded.updated "
                "WHERE inbox_items.status='new'",
                (sha, str(p), p.name, str(folder), size, now, now))
        self.db.commit()
        out = []
        for r in self.db.execute("SELECT * FROM inbox_items WHERE status='new' ORDER BY created"):
            item = dict(r)
            path = Path(item["path"])
            if not path.exists():
                continue
            item["source"] = f"inbox:{item['sha']}"
            item["text"] = extract_text(path)
            if not item["text"]:
                item["note"] = "No text extracted: open the file with your own tools (vision, office, pdf)."
            out.append(item)
        return out

    def file(self, sha: str, summary: str, work: str = "", move: bool = True) -> dict:
        """Mark an item handled; move it to Filed/YYYY-MM/ so the founder sees it was taken."""
        r = self.db.execute("SELECT * FROM inbox_items WHERE sha=?", (sha,)).fetchone()
        if not r:
            raise ValueError(f"unknown inbox item {sha}")
        if not summary.strip():
            raise ValueError("summary required: say what the file was and what you did with it")
        dest = ""
        src = Path(r["path"])
        if move and src.exists():
            target = Path(r["folder"]) / FILED / datetime.now().strftime("%Y-%m")
            target.mkdir(parents=True, exist_ok=True)
            d = target / src.name
            if d.exists():
                d = target / f"{src.stem}-{sha[:6]}{src.suffix}"
            shutil.move(str(src), str(d))
            dest = str(d)
        self.db.execute("UPDATE inbox_items SET status='filed', summary=?, work=?, filed_to=?, updated=? "
                        "WHERE sha=?", (summary, work, dest, time.time(), sha))
        self.db.commit()
        return {"sha": sha, "filed_to": dest}

    def recent(self, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.db.execute(
            "SELECT sha,name,status,summary,work,filed_to,updated FROM inbox_items ORDER BY updated DESC LIMIT ?",
            (limit,))]
