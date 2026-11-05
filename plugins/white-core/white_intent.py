"""White's intent engine (White 2.0, point 2: little or no prompting).

The model does the inferring; this module keeps it honest:
- every guess cites real signals (no evidence, no intent),
- confidence is adjusted by what the founder confirmed or rejected before (per signal type),
- one deterministic policy decides: act / ask / wait,
- "nothing worth doing" is a valid, logged answer.
Stored in the world model's SQLite file. Stdlib only.
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS intents (
  id INTEGER PRIMARY KEY, what TEXT NOT NULL, evidence TEXT NOT NULL, confidence REAL NOT NULL,
  risk TEXT NOT NULL, decision TEXT NOT NULL, next_step TEXT, status TEXT DEFAULT 'open',
  created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS intent_weights (
  signal_type TEXT PRIMARY KEY, confirmed INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS intent_quiet (id INTEGER PRIMARY KEY, why TEXT, created REAL);
"""

RISKS = ("none", "risky")
ACT_AT = 0.7      # confident enough to just do it (no-risk work only)
ASK_AT = 0.4      # below this: wait for more evidence
MAX_OPEN = 3      # White keeps at most 3 live guesses: focus, not a todo list


class IntentError(ValueError):
    pass


def decide(confidence: float, risk: str) -> str:
    """The one policy. Risky work never runs on a guess; it becomes one question to the founder."""
    if confidence < ASK_AT:
        return "wait"
    if risk == "risky":
        return "ask"
    return "act" if confidence >= ACT_AT else "ask"


class Intents:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.db.executescript(SCHEMA)
        self.db.commit()

    def _signals(self, ids: Iterable[int]) -> list[sqlite3.Row]:
        ids = [int(i) for i in ids]
        if not ids:
            return []
        q = f"SELECT id, type FROM signals WHERE id IN ({','.join('?' * len(ids))})"
        return list(self.db.execute(q, ids))

    def weight(self, signal_type: str) -> float:
        """Laplace-smoothed trust in a signal type, from founder feedback. 0.5 = no history."""
        r = self.db.execute("SELECT confirmed, rejected FROM intent_weights WHERE signal_type=?",
                            (signal_type,)).fetchone()
        c, j = (r[0], r[1]) if r else (0, 0)
        return (c + 1) / (c + j + 2)

    def adjusted(self, confidence: float, types: list[str]) -> float:
        """Shift the model's confidence by learned trust: weight 0.5 leaves it unchanged."""
        if not types:
            return confidence
        avg = sum(self.weight(t) for t in types) / len(types)
        return max(0.0, min(1.0, confidence + (avg - 0.5)))

    def context(self, limit: int = 30) -> dict:
        """What the model needs to infer intent: recent signals, live guesses, learned trust."""
        sig = [dict(id=r[0], type=r[1], summary=r[2], source=r[3], created=r[4]) for r in self.db.execute(
            "SELECT id, type, summary, source, created FROM signals ORDER BY created DESC LIMIT ?", (limit,))]
        return {"signals": sig, "open_intents": self.list("open"),
                "trust": {r[0]: round(self.weight(r[0]), 2)
                          for r in self.db.execute("SELECT signal_type FROM intent_weights")},
                "policy": {"act_at": ACT_AT, "ask_at": ASK_AT, "max_open": MAX_OPEN}}

    def propose(self, what: str, evidence: list, confidence: float, risk: str, next_step: str = "") -> dict:
        what = (what or "").strip()
        if not what:
            raise IntentError("what is required")
        if risk not in RISKS:
            raise IntentError("risk must be none or risky")
        rows = self._signals(evidence or [])
        if not rows:
            raise IntentError("no evidence, no intent: cite signal ids from white_intent context")
        conf = self.adjusted(float(confidence), [r[1] for r in rows])
        if len(rows) == 1:
            conf = min(conf, ACT_AT - 0.01)  # one signal alone never justifies acting unasked
        dup = self.db.execute("SELECT id FROM intents WHERE status='open' AND lower(what)=lower(?)",
                              (what,)).fetchone()
        if dup:
            raise IntentError(f"already open as intent {dup[0]}")
        open_n = self.db.execute("SELECT count(*) FROM intents WHERE status='open'").fetchone()[0]
        if open_n >= MAX_OPEN:
            raise IntentError(f"{MAX_OPEN} intents already open: close or expire one first")
        d = decide(conf, risk)
        now = time.time()
        cur = self.db.execute(
            "INSERT INTO intents (what, evidence, confidence, risk, decision, next_step, created, updated) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (what, json.dumps([r[0] for r in rows]), round(conf, 3), risk, d, next_step, now, now))
        self.db.commit()
        return {"id": cur.lastrowid, "confidence": round(conf, 3), "decision": d}

    def quiet(self, why: str) -> int:
        """Log a deliberate 'nothing worth doing' so silence is a decision, not a failure."""
        if not (why or "").strip():
            raise IntentError("say why nothing is worth doing")
        cur = self.db.execute("INSERT INTO intent_quiet (why, created) VALUES (?,?)", (why, time.time()))
        self.db.commit()
        return int(cur.lastrowid)

    def feedback(self, intent_id: int, verdict: str) -> dict:
        """Founder confirms or rejects a guess; every cited signal type learns from it."""
        if verdict not in ("confirmed", "rejected"):
            raise IntentError("verdict must be confirmed or rejected")
        r = self.db.execute("SELECT evidence FROM intents WHERE id=?", (int(intent_id),)).fetchone()
        if not r:
            raise IntentError(f"unknown intent {intent_id}")
        col = "confirmed" if verdict == "confirmed" else "rejected"
        for t in {row[1] for row in self._signals(json.loads(r[0]))}:
            self.db.execute("INSERT INTO intent_weights (signal_type) VALUES (?) ON CONFLICT DO NOTHING", (t,))
            self.db.execute(f"UPDATE intent_weights SET {col}={col}+1 WHERE signal_type=?", (t,))
        self.db.execute("UPDATE intents SET status=?, updated=? WHERE id=?", (verdict, time.time(), int(intent_id)))
        self.db.commit()
        return {"id": int(intent_id), "status": verdict}

    def close(self, intent_id: int, status: str = "done") -> None:
        if status not in ("done", "expired"):
            raise IntentError("status must be done or expired")
        self.db.execute("UPDATE intents SET status=?, updated=? WHERE id=?", (status, time.time(), int(intent_id)))
        self.db.commit()

    def list(self, status: str | None = None) -> list[dict]:
        q, p = "SELECT * FROM intents", ()
        if status:
            q, p = q + " WHERE status=?", (status,)
        cols = [c[1] for c in self.db.execute("PRAGMA table_info(intents)")]
        return [dict(zip(cols, r)) for r in self.db.execute(q + " ORDER BY id DESC LIMIT 20", p)]
