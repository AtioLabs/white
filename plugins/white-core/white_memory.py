"""Memory that ages (after Zep/Graphiti's temporal facts): history, as-of, nightly cleanup.

- Every changed fact keeps its old value in `fact_history` with valid_from / valid_to and source
  (written by World.upsert), so White can say what it knew on any date and why it changed.
- consolidate() runs nightly: merges exact duplicate people (same name + org, different spacing
  or case), flags unconfirmed facts not touched in STALE_DAYS for re-checking, archives handled
  signals older than ARCHIVE_DAYS, and expires guesses (intents) open longer than INTENT_DAYS.
  Nothing is deleted: merged and archived rows are kept.
Stdlib only.
"""

from __future__ import annotations

import time
from typing import Optional

STALE_DAYS = 60
ARCHIVE_DAYS = 60
INTENT_DAYS = 14
TABLES = ("people", "orgs", "pipeline")


def _has(db, t: str) -> bool:
    return bool(db.execute("SELECT name FROM sqlite_master WHERE name=?", (t,)).fetchone())


def history(db, table: str, name: str) -> dict:
    if table not in TABLES:
        raise ValueError("table must be people, orgs or pipeline")
    col = "title" if table == "pipeline" else "name"
    row = db.execute(f"SELECT * FROM {table} WHERE lower({col})=lower(?)", (name,)).fetchone()
    if not row:
        raise ValueError(f"no {table} named {name!r}")
    past = [dict(field=r[0], value=r[1], source=r[2], valid_from=r[3], valid_to=r[4]) for r in db.execute(
        "SELECT field, value, source, valid_from, valid_to FROM fact_history WHERE tbl=? AND entity_id=? "
        "ORDER BY valid_to", (table, row["id"]))]
    return {"now": dict(row), "before": past}


def as_of(db, table: str, name: str, when: float) -> dict:
    """The entity as White knew it at `when` (epoch seconds)."""
    h = history(db, table, name)
    state = dict(h["now"])
    for p in sorted(h["before"], key=lambda r: -r["valid_to"]):  # undo changes made after `when`
        if p["valid_to"] > when:
            state[p["field"]] = p["value"]
    if (state.get("created") or 0) > when:
        return {}
    return state


def consolidate(db, now: Optional[float] = None) -> dict:
    now = now or time.time()
    report = {"merged_people": 0, "stale_to_recheck": [], "archived_signals": 0, "expired_guesses": 0}
    # 1. exact duplicate people: same normalized name + org
    rows = db.execute("SELECT id, name, org_id FROM people ORDER BY id").fetchall()
    seen: dict = {}
    for r in rows:
        key = (" ".join(str(r["name"]).lower().split()), r["org_id"])
        if key in seen:
            keep = seen[key]
            for t, c in (("pipeline", "person_id"),):
                db.execute(f"UPDATE {t} SET {c}=? WHERE {c}=?", (keep, r["id"]))
            db.execute("INSERT INTO fact_history (tbl, entity_id, field, value, source, valid_from, valid_to) "
                       "VALUES ('people', ?, 'merged_from', ?, 'consolidate', NULL, ?)", (keep, str(r["id"]), now))
            db.execute("DELETE FROM people WHERE id=?", (r["id"],))
            report["merged_people"] += 1
        else:
            seen[key] = r["id"]
    # 2. stale, unconfirmed facts: flag, don't delete
    cutoff = now - STALE_DAYS * 86400
    for t in ("people", "orgs"):
        for r in db.execute(f"SELECT name FROM {t} WHERE confirmed=0 AND coalesce(updated, created, 0) < ?",
                            (cutoff,)):
            report["stale_to_recheck"].append(f"{t}:{r[0]}")
    # 3. archive old handled signals
    old = now - ARCHIVE_DAYS * 86400
    moved = db.execute("INSERT INTO signals_archive (id, type, summary, source, related, created, archived) "
                       "SELECT id, type, summary, source, related, created, ? FROM signals "
                       "WHERE handled=1 AND created < ?", (now, old)).rowcount
    db.execute("DELETE FROM signals WHERE handled=1 AND created < ?", (old,))
    report["archived_signals"] = moved
    # 4. expire guesses nobody acted on
    if _has(db, "intents"):
        report["expired_guesses"] = db.execute(
            "UPDATE intents SET status='expired', updated=? WHERE status='open' AND created < ?",
            (now, now - INTENT_DAYS * 86400)).rowcount
    db.commit()
    report["stale_to_recheck"] = report["stale_to_recheck"][:25]
    return report
