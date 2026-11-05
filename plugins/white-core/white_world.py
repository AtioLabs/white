"""White's world model: the company's state, kept outside the model.

Plain SQLite (stdlib only) so it runs anywhere Hermes runs. Every fact carries a source and a
`confirmed` flag (founder-certified, the auto-ontology idea). The rule enforced in code: no source,
no fact. Lessons need evidence.
"""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, org_id INTEGER, role TEXT, email TEXT,
  linkedin TEXT, relationship TEXT, warm_path TEXT, notes TEXT,
  source TEXT NOT NULL, confirmed INTEGER DEFAULT 0, last_contact TEXT,
  created REAL, updated REAL, UNIQUE(name, org_id));
CREATE TABLE IF NOT EXISTS orgs (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT, sector TEXT, size TEXT, city TEXT,
  website TEXT, notes TEXT, source TEXT NOT NULL, confirmed INTEGER DEFAULT 0,
  created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS pipeline (
  id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, org_id INTEGER, person_id INTEGER,
  stage TEXT NOT NULL, next_step TEXT, next_due TEXT, value TEXT, signal TEXT,
  source TEXT NOT NULL, responsibility TEXT, created REAL, updated REAL, UNIQUE(kind, title));
CREATE TABLE IF NOT EXISTS commitments (
  id INTEGER PRIMARY KEY, owner TEXT NOT NULL, to_whom TEXT, what TEXT NOT NULL, due TEXT,
  status TEXT DEFAULT 'open', source TEXT NOT NULL, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY, type TEXT NOT NULL, summary TEXT NOT NULL, source TEXT NOT NULL,
  related TEXT, handled INTEGER DEFAULT 0, created REAL);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY, what TEXT NOT NULL, by_whom TEXT NOT NULL, why TEXT, links TEXT, created REAL);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY, what TEXT NOT NULL, status TEXT NOT NULL, responsibility TEXT,
  proof TEXT, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY, lesson TEXT NOT NULL, evidence TEXT NOT NULL, topic TEXT, created REAL);
CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY, kind TEXT NOT NULL, about TEXT, before TEXT, after TEXT, note TEXT, created REAL);
CREATE TABLE IF NOT EXISTS runway (
  id INTEGER PRIMARY KEY, as_of TEXT NOT NULL, cash TEXT, monthly_burn TEXT, months REAL,
  source TEXT NOT NULL, created REAL);
"""

PIPELINE_KINDS = {"design_partner", "investor", "customer", "accelerator", "partner", "hire", "other"}
COMMITMENT_STATUS = {"open", "done", "dropped"}
ACTION_STATUS = {"proposed", "awaiting_approval", "done", "failed", "rejected"}
_TABLE_COLS = {
    "people": {"name", "org_id", "role", "email", "linkedin", "relationship", "warm_path", "notes",
               "source", "confirmed", "last_contact"},
    "orgs": {"name", "kind", "sector", "size", "city", "website", "notes", "source", "confirmed"},
    "pipeline": {"kind", "title", "org_id", "person_id", "stage", "next_step", "next_due", "value",
                 "signal", "source", "responsibility"},
}


class WorldError(ValueError):
    """A rule of the world model was broken (e.g. a fact without a source)."""


def _now() -> float:
    return time.time()


def _require_source(data: dict) -> None:
    src = str(data.get("source") or "").strip()
    if not src:
        raise WorldError("Every fact needs a 'source' (URL, email id, 'founder said', call log).")


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        raise WorldError(f"Dates must be YYYY-MM-DD, got {value!r}")


class World:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(str(path), check_same_thread=False)  # Hermes calls tools from worker threads
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    # ---- entities ------------------------------------------------------------------------------

    def org_id(self, name: Optional[str]) -> Optional[int]:
        if not name:
            return None
        row = self.db.execute("SELECT id FROM orgs WHERE lower(name)=lower(?)", (name,)).fetchone()
        return row["id"] if row else None

    def person_id(self, name: Optional[str]) -> Optional[int]:
        if not name:
            return None
        row = self.db.execute("SELECT id FROM people WHERE lower(name)=lower(?)", (name,)).fetchone()
        return row["id"] if row else None

    def upsert(self, table: str, data: dict) -> int:
        """Insert or update a person, org or pipeline item. Returns its id."""
        if table not in _TABLE_COLS:
            raise WorldError(f"Unknown table {table!r}; use people, orgs or pipeline.")
        data = dict(data)
        _require_source(data)
        # Resolve names to ids so the model can speak in names.
        if "org" in data and table in ("people", "pipeline"):
            org_name = data.pop("org")
            if org_name and not self.org_id(org_name):
                self.upsert("orgs", {"name": org_name, "source": data["source"]})
            data["org_id"] = self.org_id(org_name)
        if "person" in data and table == "pipeline":
            data["person_id"] = self.person_id(data.pop("person"))
        if table == "pipeline":
            if data.get("kind") not in PIPELINE_KINDS:
                raise WorldError(f"pipeline.kind must be one of {sorted(PIPELINE_KINDS)}")
            if not data.get("stage"):
                raise WorldError("pipeline items need a 'stage'")
            _parse_date(data.get("next_due"))
        unknown = set(data) - _TABLE_COLS[table]
        if unknown:
            raise WorldError(f"Unknown fields for {table}: {sorted(unknown)}")

        key_sql, key_vals = {
            "people": ("lower(name)=lower(?) AND org_id IS ?", (data.get("name"), data.get("org_id"))),
            "orgs": ("lower(name)=lower(?)", (data.get("name"),)),
            "pipeline": ("kind=? AND lower(title)=lower(?)", (data.get("kind"), data.get("title"))),
        }[table]
        if not key_vals[0] and table != "pipeline":
            raise WorldError("'name' is required")
        if table == "pipeline" and not data.get("title"):
            raise WorldError("'title' is required")
        row = self.db.execute(f"SELECT id FROM {table} WHERE {key_sql}", key_vals).fetchone()
        now = _now()
        if row:
            sets = ", ".join(f"{k}=?" for k in data)
            self.db.execute(f"UPDATE {table} SET {sets}, updated=? WHERE id=?",
                            (*data.values(), now, row["id"]))
            rid = row["id"]
        else:
            cols = ", ".join(list(data) + ["created", "updated"])
            marks = ", ".join("?" for _ in range(len(data) + 2))
            cur = self.db.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})",
                                  (*data.values(), now, now))
            rid = cur.lastrowid
        self.db.commit()
        return int(rid)

    def confirm(self, table: str, name: str) -> bool:
        """The founder certified this entity as correct."""
        if table not in ("people", "orgs"):
            raise WorldError("Only people and orgs can be confirmed.")
        cur = self.db.execute(f"UPDATE {table} SET confirmed=1, updated=? WHERE lower(name)=lower(?)",
                              (_now(), name))
        self.db.commit()
        return cur.rowcount > 0

    # ---- logs ----------------------------------------------------------------------------------

    def add_commitment(self, owner: str, what: str, source: str, to_whom: str = "",
                       due: Optional[str] = None) -> int:
        _require_source({"source": source})
        _parse_date(due)
        now = _now()
        cur = self.db.execute(
            "INSERT INTO commitments (owner, to_whom, what, due, source, created, updated) "
            "VALUES (?,?,?,?,?,?,?)", (owner, to_whom, what, due, source, now, now))
        self.db.commit()
        return int(cur.lastrowid)

    def set_commitment(self, cid: int, status: str) -> None:
        if status not in COMMITMENT_STATUS:
            raise WorldError(f"status must be one of {sorted(COMMITMENT_STATUS)}")
        self.db.execute("UPDATE commitments SET status=?, updated=? WHERE id=?", (status, _now(), cid))
        self.db.commit()

    def add_signal(self, type_: str, summary: str, source: str, related: Any = None) -> int:
        """Record an event. The same source (e.g. one email id) is only ingested once, so the loop
        can re-scan the inbox safely."""
        _require_source({"source": source})
        existing = self.db.execute("SELECT id FROM signals WHERE source=?", (source,)).fetchone()
        if existing:
            return int(existing["id"])
        cur = self.db.execute(
            "INSERT INTO signals (type, summary, source, related, created) VALUES (?,?,?,?,?)",
            (type_, summary, source, json.dumps(related) if related else None, _now()))
        self.db.commit()
        return int(cur.lastrowid)

    def mark_signal_handled(self, sid: int) -> None:
        self.db.execute("UPDATE signals SET handled=1 WHERE id=?", (sid,))
        self.db.commit()

    def log_decision(self, what: str, by_whom: str, why: str = "", links: Any = None) -> int:
        cur = self.db.execute(
            "INSERT INTO decisions (what, by_whom, why, links, created) VALUES (?,?,?,?,?)",
            (what, by_whom, why, json.dumps(links) if links else None, _now()))
        self.db.commit()
        return int(cur.lastrowid)

    def log_action(self, what: str, status: str, responsibility: str = "", proof: str = "") -> int:
        if status not in ACTION_STATUS:
            raise WorldError(f"status must be one of {sorted(ACTION_STATUS)}")
        if status == "done" and not proof.strip():
            raise WorldError("A 'done' action needs proof (file path, URL, message id).")
        now = _now()
        cur = self.db.execute(
            "INSERT INTO actions (what, status, responsibility, proof, created, updated) "
            "VALUES (?,?,?,?,?,?)", (what, status, responsibility, proof, now, now))
        self.db.commit()
        return int(cur.lastrowid)

    def add_lesson(self, lesson: str, evidence: list, topic: str = "") -> int:
        if not evidence or not all(str(e).strip() for e in evidence):
            raise WorldError("A lesson needs evidence: links to the actions, emails or results behind it.")
        cur = self.db.execute(
            "INSERT INTO lessons (lesson, evidence, topic, created) VALUES (?,?,?,?)",
            (lesson, json.dumps(evidence), topic, _now()))
        self.db.commit()
        return int(cur.lastrowid)

    def set_runway(self, as_of: str, source: str, cash: str = "", monthly_burn: str = "",
                   months: Optional[float] = None) -> int:
        _require_source({"source": source})
        _parse_date(as_of)
        cur = self.db.execute(
            "INSERT INTO runway (as_of, cash, monthly_burn, months, source, created) VALUES (?,?,?,?,?,?)",
            (as_of, cash, monthly_burn, months, source, _now()))
        self.db.commit()
        return int(cur.lastrowid)

    # ---- views ---------------------------------------------------------------------------------

    def _rows(self, sql: str, params: tuple = ()) -> list[dict]:
        return [dict(r) for r in self.db.execute(sql, params).fetchall()]

    def overdue_commitments(self, today: Optional[date] = None) -> list[dict]:
        today = today or date.today()
        return [r for r in self._rows("SELECT * FROM commitments WHERE status='open' AND due IS NOT NULL")
                if _parse_date(r["due"]) and _parse_date(r["due"]) < today]

    def stalled_pipeline(self, days: int = 7, now: Optional[float] = None) -> list[dict]:
        cutoff = (now or _now()) - days * 86400
        return self._rows(
            "SELECT p.*, o.name AS org FROM pipeline p LEFT JOIN orgs o ON o.id=p.org_id "
            "WHERE p.stage NOT IN ('won','lost','committed','passed','signed','closed') AND p.updated < ?",
            (cutoff,))

    def unhandled_signals(self) -> list[dict]:
        return self._rows("SELECT * FROM signals WHERE handled=0 ORDER BY created")

    def pipeline(self, kind: Optional[str] = None) -> list[dict]:
        sql = ("SELECT p.*, o.name AS org, pe.name AS person FROM pipeline p "
               "LEFT JOIN orgs o ON o.id=p.org_id LEFT JOIN people pe ON pe.id=p.person_id")
        return self._rows(sql + (" WHERE p.kind=?" if kind else "") + " ORDER BY p.updated DESC",
                          (kind,) if kind else ())

    def search(self, text: str) -> dict[str, list[dict]]:
        like = f"%{text}%"
        return {
            "people": self._rows("SELECT * FROM people WHERE name LIKE ? OR notes LIKE ? OR role LIKE ?",
                                 (like, like, like)),
            "orgs": self._rows("SELECT * FROM orgs WHERE name LIKE ? OR notes LIKE ? OR sector LIKE ?",
                               (like, like, like)),
            "pipeline": self._rows("SELECT * FROM pipeline WHERE title LIKE ? OR signal LIKE ? OR next_step LIKE ?",
                                   (like, like, like)),
            "lessons": self._rows("SELECT * FROM lessons WHERE lesson LIKE ? OR topic LIKE ?", (like, like)),
        }

    def latest_runway(self) -> Optional[dict]:
        rows = self._rows("SELECT * FROM runway ORDER BY as_of DESC, created DESC LIMIT 1")
        return rows[0] if rows else None

    def snapshot(self, today: Optional[date] = None) -> dict:
        """Everything the judgment engine needs in one call."""
        return {
            "overdue_commitments": self.overdue_commitments(today),
            "open_commitments": self._rows("SELECT * FROM commitments WHERE status='open' ORDER BY due"),
            "stalled_pipeline": self.stalled_pipeline(),
            "unhandled_signals": self.unhandled_signals(),
            "pipeline_counts": self._rows(
                "SELECT kind, stage, COUNT(*) AS n FROM pipeline GROUP BY kind, stage ORDER BY kind"),
            "runway": self.latest_runway(),
            "recent_decisions": self._rows("SELECT * FROM decisions ORDER BY created DESC LIMIT 10"),
        }
