"""White core: Hermes plugin entry point.

Gives White a world model it can read and write through tools, kept in
$HERMES_HOME/white/world.db, plus a wiki view in $HERMES_HOME/founder/wiki/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from white_world import World, WorldError  # noqa: E402
import white_wiki as wiki  # noqa: E402
import white_judgment as judgment  # noqa: E402
import white_supervisor as supervisor  # noqa: E402
import white_learning as learning  # noqa: E402
import white_doctor as doctor  # noqa: E402
import white_team as team  # noqa: E402
import white_receipts as receipts  # noqa: E402
from white_inbox import Inbox, load_folders  # noqa: E402
from white_intent import Intents, IntentError  # noqa: E402
import white_desktop as desktop  # noqa: E402
import white_scout as scout  # noqa: E402
from white_mastery import Mastery  # noqa: E402
import white_gaps as gaps  # noqa: E402
import white_models as models  # noqa: E402

_ctx = None  # set in register(); gives the supervisor its own LLM call via ctx.llm

_world_cache: dict[str, World] = {}


def _home() -> Path:
    from hermes_constants import get_hermes_home
    return Path(get_hermes_home())


def get_world(home: Path | None = None) -> World:
    home = home or _home()
    key = str(home)
    if key not in _world_cache:
        _world_cache[key] = World(home / "white" / "world.db")
    return _world_cache[key]


def _ok(payload: Any) -> str:
    return json.dumps({"ok": True, "result": payload}, ensure_ascii=False, default=str)


def _err(msg: str) -> str:
    return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)


# ---- tool handlers --------------------------------------------------------------------------------

def white_record(args: dict | None = None, **_: Any) -> str:
    """Upsert a person, org or pipeline item."""
    args = args or {}
    try:
        table = {"person": "people", "org": "orgs", "pipeline": "pipeline"}.get(args.get("kind", ""))
        if not table:
            return _err("kind must be person, org or pipeline")
        rid = get_world().upsert(table, dict(args.get("data") or {}))
        return _ok({"id": rid})
    except WorldError as e:
        return _err(str(e))


def white_log(args: dict | None = None, **_: Any) -> str:
    """Log a commitment, signal, decision, action, lesson or runway update."""
    args = args or {}
    w = get_world()
    d = dict(args.get("data") or {})
    try:
        kind = args.get("kind")
        if kind == "commitment":
            rid = w.add_commitment(d.get("owner", "founder"), d.get("what", ""), d.get("source", ""),
                                   d.get("to_whom", ""), d.get("due"))
        elif kind == "commitment_status":
            w.set_commitment(int(d["id"]), d.get("status", ""))
            rid = int(d["id"])
        elif kind == "signal":
            rid = w.add_signal(d.get("type", "note"), d.get("summary", ""), d.get("source", ""), d.get("related"))
        elif kind == "signal_handled":
            w.mark_signal_handled(int(d["id"]))
            rid = int(d["id"])
        elif kind == "decision":
            rid = w.log_decision(d.get("what", ""), d.get("by_whom", "founder"), d.get("why", ""), d.get("links"))
        elif kind == "action":
            rid = w.log_action(d.get("what", ""), d.get("status", ""), d.get("responsibility", ""), d.get("proof", ""))
        elif kind == "lesson":
            rid = w.add_lesson(d.get("lesson", ""), list(d.get("evidence") or []), d.get("topic", ""))
        elif kind == "runway":
            rid = w.set_runway(d.get("as_of", ""), d.get("source", ""), d.get("cash", ""),
                               d.get("monthly_burn", ""), d.get("months"))
        elif kind == "confirm":
            return _ok({"confirmed": w.confirm(d.get("table", ""), d.get("name", ""))})
        else:
            return _err("kind must be commitment, commitment_status, signal, signal_handled, decision, "
                        "action, lesson, runway or confirm")
        return _ok({"id": rid})
    except (WorldError, KeyError, ValueError) as e:
        return _err(str(e))


def white_query(args: dict | None = None, **_: Any) -> str:
    """Read the world model."""
    args = args or {}
    w = get_world()
    view = args.get("view", "snapshot")
    try:
        if view == "snapshot":
            return _ok(w.snapshot())
        if view == "pipeline":
            return _ok(w.pipeline(args.get("pipeline_kind")))
        if view == "search":
            return _ok(w.search(args.get("text", "")))
        if view == "overdue":
            return _ok(w.overdue_commitments())
        if view == "stalled":
            return _ok(w.stalled_pipeline(int(args.get("days", 7))))
        if view == "signals":
            return _ok(w.unhandled_signals())
        return _err("view must be snapshot, pipeline, search, overdue, stalled or signals")
    except (WorldError, ValueError) as e:
        return _err(str(e))


def white_wiki(args: dict | None = None, **_: Any) -> str:
    """Regenerate the readable wiki pages from the world model."""
    paths = wiki.render(get_world(), _home() / "founder" / "wiki")
    return _ok({"pages": [str(p) for p in paths]})


def white_judge(args: dict | None = None, **_: Any) -> str:
    """Rank what matters most today from the charter and world model."""
    try:
        import os
        charter = judgment.load_charter(_home() / "founder" / "charter.yaml")
        today = judgment._d(os.environ.get("WHITE_TODAY"))  # bench pins the date; normally unset
        learned = learning.load_weights(_home() / "white" / "weights.yaml")
        return _ok(judgment.judge(get_world(), charter, today=today, learned=learned))
    except Exception as e:  # surface, don't crash the turn
        return _err(f"judgment failed: {e}")


def white_feedback(args: dict | None = None, **_: Any) -> str:
    """Turn founder feedback into policy: draft edits and accepted/rejected recommendations."""
    args = args or {}
    w = get_world()
    try:
        kind = args.get("kind")
        if kind == "draft_edit":
            return _ok(learning.record_draft_edit(w, str(args.get("before", "")), str(args.get("after", "")),
                                                  str(args.get("about", ""))))
        if kind in ("accepted", "rejected"):
            return _ok(learning.record_recommendation(w, _home() / "white" / "weights.yaml",
                                                      str(args.get("responsibility", "")), kind == "accepted",
                                                      str(args.get("note", ""))))
        return _err("kind must be draft_edit, accepted or rejected")
    except WorldError as e:
        return _err(str(e))


def white_scorecard(args: dict | None = None, **_: Any) -> str:
    """The week in outcomes, actions with proof, misses, and what White learned."""
    try:
        import os
        charter = judgment.load_charter(_home() / "founder" / "charter.yaml")
        today = judgment._d(os.environ.get("WHITE_TODAY"))
        learned = learning.load_weights(_home() / "white" / "weights.yaml")
        judged = judgment.judge(get_world(), charter, today=today, learned=learned)
        return _ok(learning.scorecard(get_world(), judged, today=today))
    except Exception as e:
        return _err(f"scorecard failed: {e}")


def white_review(args: dict | None = None, **_: Any) -> str:
    """Supervisor check of a draft or result before the founder sees it or it counts as done."""
    args = args or {}
    home = _home()
    voice_path = home / "founder" / "voice.md"
    voice_md = voice_path.read_text(encoding="utf-8") if voice_path.is_file() else ""
    llm = getattr(getattr(_ctx, "llm", None), "complete_structured", None) if args.get("use_model", True) else None
    try:
        result = supervisor.review(
            str(args.get("text", "")), str(args.get("kind", "other")), goal=str(args.get("goal", "")),
            sources=list(args.get("sources") or []), proof=list(args.get("proof") or []),
            voice_md=voice_md, never_share=supervisor.never_share_list(home / "founder" / "authority.yaml"),
            llm_structured=llm)
        return _ok(result.as_dict())
    except Exception as e:
        return _err(f"review failed: {e}")


_FACE_TRAITS = ("face", "hair", "eyes", "brows", "glasses", "nose", "mouth", "beard", "clothes")


def white_face(args: dict | None = None, **_: Any) -> str:
    """Make or change White's face (its avatar in the Hermes app)."""
    import white_face as wf
    args = args or {}
    try:
        traits = {k: args.get(k) for k in _FACE_TRAITS if args.get(k)}
        if args.get("action") == "choices":
            return _ok(wf.choices(_home(), traits=traits))
        if args.get("action") == "options":
            return _ok(wf.OPTIONS)
        seed = args.get("seed")
        return _ok(wf.make(_home(), seed=int(seed) if seed not in (None, "") else None,
                           photo=args.get("photo"), traits=traits))
    except (ValueError, OSError) as e:
        return _err(str(e))


def white_status(args: dict | None = None, **_: Any) -> str:
    """White's own setup health (the doctor), for guiding the founder in chat. Never contains secrets."""
    try:
        checks = doctor.run(_home())
        todo = [c for c in checks if not c["ok"]]
        return _ok({"ready": not any(c["level"] == "error" for c in todo),
                    "todo": [{"name": c["name"], "level": c["level"], "fix": c["fix"], "detail": c["detail"]}
                             for c in todo],
                    "done": [c["name"] for c in checks if c["ok"]]})
    except Exception as e:
        return _err(f"status failed: {e}")


def white_dispatch(args: dict | None = None, **_: Any) -> str:
    """Build a specialist card. The caller then passes `kanban_create` exactly as returned."""
    args = args or {}
    try:
        card = team.build_card(
            str(args.get("role", "")), str(args.get("goal", "")), str(args.get("done_means", "")),
            inputs=list(args.get("inputs") or []), responsibility=str(args.get("responsibility", "")),
            due=str(args.get("due", "")), priority=int(args.get("priority") or 0))
        get_world().log_action(f"dispatched to {args.get('role')}: {args.get('goal')}", "proposed",
                               str(args.get("responsibility", "")))
        return _ok({"kanban_create": card,
                    "next": "Call kanban_create with exactly these fields. Don't do this work yourself."})
    except (team.TeamError, ValueError) as e:
        return _err(str(e))


_inbox_cache: dict[str, Inbox] = {}


def get_inbox(home: Path | None = None) -> Inbox:
    home = home or _home()
    key = str(home)
    if key not in _inbox_cache:
        (home / "founder" / "inbox").mkdir(parents=True, exist_ok=True)
        _inbox_cache[key] = Inbox(home / "white" / "inbox.db", load_folders(home))
    return _inbox_cache[key]


def white_inbox(args: dict | None = None, **_: Any) -> str:
    """The founder's drop folder: scan for new files, file them once handled, or list recent."""
    args = args or {}
    try:
        ib = get_inbox()
        action = args.get("action", "scan")
        if action == "scan":
            items = ib.scan()
            for it in items:  # each drop is also a signal, so judgment sees it
                get_world().add_signal("inbox", f"Founder dropped {it['name']}", it["source"])
            return _ok({"folders": [str(f) for f in ib.folders], "new": items,
                        "next": "For each item: record facts with source=item.source, do the work it implies "
                                "(risky work → ask the founder), then call action=file with summary and work."})
        if action == "file":
            return _ok(ib.file(str(args.get("sha", "")), str(args.get("summary", "")), str(args.get("work", ""))))
        if action == "recent":
            return _ok(ib.recent(int(args.get("limit") or 20)))
        return _err("action must be scan, file or recent")
    except (ValueError, WorldError) as e:
        return _err(str(e))


def white_intent(args: dict | None = None, **_: Any) -> str:
    """Infer what the founder is trying to do, and decide act / ask / wait by one policy."""
    args = args or {}
    try:
        it = Intents(get_world().db)
        a = args.get("action", "context")
        if a == "context":
            return _ok(it.context(int(args.get("limit") or 30)))
        if a == "propose":
            return _ok(it.propose(str(args.get("what", "")), list(args.get("evidence") or []),
                                  float(args.get("confidence") or 0), str(args.get("risk", "")),
                                  str(args.get("next_step", ""))))
        if a == "quiet":
            return _ok({"id": it.quiet(str(args.get("why", "")))})
        if a == "feedback":
            return _ok(it.feedback(int(args.get("id") or 0), str(args.get("verdict", ""))))
        if a == "close":
            it.close(int(args.get("id") or 0), str(args.get("status") or "done"))
            return _ok({"id": args.get("id")})
        if a == "list":
            return _ok(it.list(args.get("status")))
        return _err("action must be context, propose, quiet, feedback, close or list")
    except (IntentError, ValueError) as e:
        return _err(str(e))


def white_desktop(args: dict | None = None, **_: Any) -> str:
    """Drive any desktop app through its accessibility tree (agent-desktop), gate-visible."""
    args = args or {}
    out = desktop.run(str(args.get("command", "")), list(args.get("args") or []),
                      str(args.get("ref", "")), str(args.get("label", "")))
    return _ok(out) if out.get("ok") else _err(json.dumps(out.get("error"), ensure_ascii=False))


def white_scout(args: dict | None = None, **_: Any) -> str:
    """Know what the founder owns; find, inspect and install skills White needs, by itself."""
    args = args or {}
    home = _home()
    try:
        a = args.get("action", "scan")
        if a == "scan":
            return _ok(scout.scan(home))
        if a == "search":
            return _ok(scout.search(str(args.get("need", ""))))
        if a == "fetch":
            q = scout.fetch_repo(home, str(args.get("repo", "")))
            return _ok({"quarantine": str(q), "inspection": scout.inspect(q)})
        if a == "install":
            q = home / "white" / "quarantine" / scout._safe_name(str(args.get("repo", "")).replace("/", "__"))
            if not q.exists():
                return _err("fetch the repo first")
            res = scout.install(home, q, str(args.get("why", "")), list(args.get("only") or []) or None)
            if res.get("installed"):
                get_world().log_action(f"Installed skill(s) {', '.join(res['installed'])} from {args.get('repo')}",
                                       "done", proof=str(home / "white" / "scout.json"))
            return _ok(res)
        if a == "list":
            return _ok(scout.registry(home))
        return _err("action must be scan, search, fetch, install or list")
    except Exception as e:  # network errors, bad archives, rule failures: report, never crash the loop
        return _err(str(e))


def white_mastery(args: dict | None = None, **_: Any) -> str:
    """Expert playbooks per tool: learn its features, record use, score how much of it White uses."""
    args = args or {}
    try:
        m = Mastery(_home())
        a = args.get("action", "report")
        if a == "learn":
            return _ok(m.learn(str(args.get("tool", "")), list(args.get("features") or []),
                               str(args.get("how_to_drive", ""))))
        if a == "use":
            return _ok(m.use(str(args.get("tool", "")), str(args.get("feature", "")),
                             str(args.get("outcome", "")), str(args.get("lesson", ""))))
        if a == "pack":
            return _ok(m.load(str(args.get("tool", ""))))
        if a == "report":
            return _ok(m.report())
        return _err("action must be learn, use, pack or report")
    except ValueError as e:
        return _err(str(e))


def white_gaps(args: dict | None = None, **_: Any) -> str:
    """What the founder and company lack: gather evidence, then write the report."""
    args = args or {}
    try:
        if args.get("action", "gather") == "gather":
            return _ok(gaps.gather(_home(), get_world()))
        if args.get("action") == "write":
            return _ok({"file": str(gaps.write(_home(), list(args.get("gaps") or [])))})
        return _err("action must be gather or write")
    except ValueError as e:
        return _err(str(e))


def white_models(args: dict | None = None, **_: Any) -> str:
    """Open-weight model advice from live data: this machine, trending models, White's own routing."""
    a = (args or {}).get("action", "hardware")
    try:
        if a == "hardware":
            return _ok(models.hardware())
        if a == "open_models":
            return _ok(models.open_models())
        if a == "routing":
            return _ok(models.routing(_home()))
        return _err("action must be hardware, open_models or routing")
    except Exception as e:
        return _err(f"model advisor failed: {e}")


_TOOLS = {
    "white_gaps": (
        white_gaps,
        "Growth partner: what the founder and company LACK to hit the charter. action=gather: evidence (charter "
        "pace vs. time, overdue promises, stalled deals, runway, tool usage %, owned capabilities, rejected "
        "guesses). action=write (gaps=[{gap, evidence, fix, owner white|founder|hire|partner}]): writes "
        "founder/reports/gaps-<date>.md. Every gap needs evidence and a fix.",
        {"action": {"type": "string"}, "gaps": {"type": "array", "items": {"type": "object"}}},
        ["action"],
    ),
    "white_models": (
        white_models,
        "Model advisor. action=hardware: RAM, GPU, local runtimes, how big a model fits here. action=open_models: "
        "live trending open-weight models (Hugging Face) with size, license and whether a 4-bit build fits this "
        "machine. action=routing: what White runs on now. Explain in plain words; propose switches with cost/"
        "speed/quality trade-offs and let the founder decide.",
        {"action": {"type": "string"}},
        ["action"],
    ),
    "white_scout": (
        white_scout,
        "Capabilities. action=scan: what the founder already has (CLIs, skills, connected apps, model "
        "providers). action=search (need): GitHub skill repos with >=1000 stars, licensed, active. "
        "action=fetch (repo owner/name): download to quarantine and inspect the code. action=install (repo, "
        "why, only=[skill names]): installs only if inspection passes; blocked findings are returned. "
        "action=list: installed scouted skills. Use when a task needs a skill you don't have; no need to ask "
        "the founder unless inspection blocks it.",
        {"action": {"type": "string"}, "need": {"type": "string"}, "repo": {"type": "string"},
         "why": {"type": "string"}, "only": {"type": "array", "items": {"type": "string"}}},
        ["action"],
    ),
    "white_mastery": (
        white_mastery,
        "Tool mastery packs: get 100% out of any tool. action=learn (tool, features=[{name, what, goal, "
        "source}], how_to_drive): record features from docs/changelogs/expert guides, each mapped to a founder "
        "goal ('' if none) and with a source. action=use (tool, feature, outcome, lesson): log a use and what "
        "worked. action=pack (tool): the playbook. action=report: every tool's usage %, lowest first, with "
        "unused features that fit the founder's goals.",
        {"action": {"type": "string"}, "tool": {"type": "string"},
         "features": {"type": "array", "items": {"type": "object"}}, "how_to_drive": {"type": "string"},
         "feature": {"type": "string"}, "outcome": {"type": "string"}, "lesson": {"type": "string"}},
        ["action"],
    ),
    "white_desktop": (
        white_desktop,
        "Use any desktop app (Windows/macOS/Linux) through its accessibility tree: cheaper and more reliable "
        "than screenshots. Flow: command=snapshot args=['--app','<App>','-i','--compact'] -> read refs "
        "(@sXXXX:eN with role and name) -> act: command=click|set-value|type|select|toggle|scroll ref=<ref> "
        "label=<the element's real name> args=[value...]. press: args=['Enter'] with label = what it does. "
        "launch/close-app/focus-window: args=['<App>']. Always snapshot again after acting to verify. "
        "Send/pay/post/delete-type targets go to the founder for approval. Use screenshots only if an app "
        "exposes no tree.",
        {"command": {"type": "string"}, "args": {"type": "array", "items": {"type": "string"}},
         "ref": {"type": "string"}, "label": {"type": "string"}},
        ["command"],
    ),
    "white_intent": (
        white_intent,
        "Work out what the founder is trying to do without being asked. action=context: recent signals, open "
        "intents, learned trust. action=propose (what, evidence=[signal ids], confidence 0-1, risk none|risky, "
        "next_step): returns decision act|ask|wait. act = do it now; ask = prepare it and ask ONE question; "
        "wait = do nothing yet. action=quiet (why): nothing worth doing, say so. action=feedback (id, verdict "
        "confirmed|rejected) when the founder reacts. action=close (id, status done|expired). action=list.",
        {"action": {"type": "string"}, "what": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "integer"}},
         "confidence": {"type": "number"}, "risk": {"type": "string"}, "next_step": {"type": "string"},
         "why": {"type": "string"}, "id": {"type": "integer"}, "verdict": {"type": "string"},
         "status": {"type": "string"}, "limit": {"type": "integer"}},
        ["action"],
    ),
    "white_inbox": (
        white_inbox,
        "The founder's inbox folder (founder/inbox plus folders in founder/inbox.yaml, e.g. Google Drive). "
        "action=scan: new files with extracted text and a source id. action=file (sha, summary, work): mark "
        "handled and move to Filed/YYYY-MM. action=recent (limit): what was filed.",
        {"action": {"type": "string"}, "sha": {"type": "string"}, "summary": {"type": "string"},
         "work": {"type": "string"}, "limit": {"type": "integer"}},
        ["action"],
    ),
    "white_face": (
        white_face,
        "White's face: a 1-bit pixel portrait used as its avatar in the Hermes app. action=choices shows a sheet "
        "of 12 faces to pick from (by seed); action=make (default) sets one by seed and/or traits, or from a photo "
        "the founder provides (processed locally, never uploaded); action=options lists traits. Tweaking a trait "
        "keeps the rest of the current face.",
        {"action": {"type": "string", "enum": ["make", "choices", "options"]},
         "seed": {"type": "integer"}, "photo": {"type": "string", "description": "Local image path."},
         **{k: {"type": "string"} for k in _FACE_TRAITS}},
        [],
    ),
    "white_status": (
        white_status,
        "White's setup health: what's ready and what's missing (model, plugins, founder files, charter, "
        "apps, WhatsApp schedule), each with the fix. Call at the start of a conversation; if anything is "
        "missing, use the white-setup skill to walk the founder through it in plain words.",
        {},
        [],
    ),
    "white_receipts": (
        lambda args=None, **kw: white_receipts(args, **kw),  # defined below with the CLI helpers
        "Write a public, verifiable log of what White did (names pseudonymized, never-share redacted, proofs "
        "as SHA-256 fingerprints) to founder/receipts/. For build-in-public posts. The founder reviews before sharing.",
        {"days": {"type": "integer"}},
        [],
    ),
    "white_dispatch": (
        white_dispatch,
        "Hand a unit of work to a White specialist (outreach, research, content, finance, ops). Returns the "
        "exact kanban_create payload (title, assignee, body with the role's rules, skills, idempotency key). "
        "Then call kanban_create with it. Use for anything bigger than a few minutes, so White stays the "
        "orchestrator. 'done_means' must be checkable evidence.",
        {"role": {"type": "string", "enum": ["outreach", "research", "content", "finance", "ops"]},
         "goal": {"type": "string"}, "done_means": {"type": "string"},
         "inputs": {"type": "array", "items": {"type": "string"}},
         "responsibility": {"type": "string"}, "due": {"type": "string"}, "priority": {"type": "integer"}},
        ["role", "goal", "done_means"],
    ),
    "white_feedback": (
        white_feedback,
        "Learn from the founder. kind=draft_edit (before = your draft, after = what the founder actually sent "
        "or edited it to, about) returns exactly what they cut and added; then write the lesson into voice.md. "
        "kind=accepted|rejected (responsibility, note) when the founder takes or turns down a recommendation; "
        "it adjusts how White prioritizes that responsibility, within bounds.",
        {"kind": {"type": "string", "enum": ["draft_edit", "accepted", "rejected"]},
         "before": {"type": "string"}, "after": {"type": "string"}, "about": {"type": "string"},
         "responsibility": {"type": "string"}, "note": {"type": "string"}},
        ["kind"],
    ),
    "white_scorecard": (
        white_scorecard,
        "Weekly scorecard: outcomes vs targets, actions done with proof by responsibility, approvals waiting, "
        "failures, misses (behind pace, overdue promises), founder corrections, and lessons learned. "
        "Use for the Monday review. Report misses plainly, with a fix for each.",
        {},
        [],
    ),
    "white_review": (
        white_review,
        "White's supervisor. Run on EVERY draft (email, post, application, update, check-in, report) "
        "before showing it to the founder or requesting approval, and on results before marking them done. "
        "Checks never-share leaks, voice, AI tells, length, sources and proof in code, then a separate model "
        "review. If pass=false, fix the issues and review again (max 2 retries), then escalate.",
        {"text": {"type": "string"},
         "kind": {"type": "string", "description": "cold_email | investor_email | followup | linkedin_note | "
                  "post | checkin | report | brief | plan | application | investor_update | research | other"},
         "goal": {"type": "string", "description": "What this must achieve (the card's 'done means')."},
         "sources": {"type": "array", "items": {"type": "string"}},
         "proof": {"type": "array", "items": {"type": "string"}, "description": "Files, URLs, message ids."},
         "use_model": {"type": "boolean", "description": "Default true. False = code checks only."}},
        ["text", "kind"],
    ),
    "white_judge": (
        white_judge,
        "White's judgment engine. Returns today's one thing, the ranked top items (each with why and "
        "evidence), challenges for the founder, and the charter scorecard. Call before any check-in or "
        "planning, and reason over its output; don't re-rank from scratch.",
        {},
        [],
    ),
    "white_record": (
        white_record,
        "Save or update a person, org or pipeline item in White's world model. Every fact needs a "
        "'source' (URL, email id, 'founder said', call log). Use names for org/person; ids are resolved.",
        {"kind": {"type": "string", "enum": ["person", "org", "pipeline"]},
         "data": {"type": "object", "description":
                  "person: name, org, role, email, linkedin, relationship, warm_path, notes, last_contact, source. "
                  "org: name, kind, sector, size, city, website, notes, source. "
                  "pipeline: kind (design_partner|investor|customer|accelerator|partner|hire|other), title, "
                  "org, person, stage, next_step, next_due (YYYY-MM-DD), value, signal, responsibility, source."}},
        ["kind", "data"],
    ),
    "white_log": (
        white_log,
        "Log to White's world model: commitment (owner, to_whom, what, due, source), commitment_status "
        "(id, status open|done|dropped), signal (type, summary, source, related), signal_handled (id), "
        "decision (what, by_whom, why, links), action (what, status, responsibility, proof; 'done' needs "
        "proof), lesson (lesson, evidence[list], topic; no evidence = rejected), runway (as_of, cash, "
        "monthly_burn, months, source), confirm (table people|orgs, name) when the founder certifies a fact.",
        {"kind": {"type": "string"}, "data": {"type": "object"}},
        ["kind", "data"],
    ),
    "white_query": (
        white_query,
        "Read White's world model. view: snapshot (everything judgment needs), pipeline (optional "
        "pipeline_kind), search (text), overdue, stalled (days), signals.",
        {"view": {"type": "string"}, "pipeline_kind": {"type": "string"},
         "text": {"type": "string"}, "days": {"type": "integer"}},
        ["view"],
    ),
    "white_wiki": (
        white_wiki,
        "Regenerate the founder-readable wiki (now, people, pipeline, commitments, lessons) from the world model.",
        {},
        [],
    ),
}


def write_receipts(days: int = 7) -> Path:
    home = _home()
    data = receipts.export(get_world(), days=days,
                           never_share=supervisor.never_share_list(home / "founder" / "authority.yaml"),
                           gate_log=receipts.load_gate_log(home / "white" / "gate-log.jsonl"))
    out = home / "founder" / "receipts"
    out.mkdir(parents=True, exist_ok=True)
    from datetime import date as _date
    stamp = _date.today().isoformat()
    (out / f"receipts-{stamp}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    md = out / f"receipts-{stamp}.md"
    md.write_text(receipts.to_markdown(data), encoding="utf-8")
    return md


def white_receipts(args: dict | None = None, **_: Any) -> str:
    try:
        return _ok({"file": str(write_receipts(int((args or {}).get("days") or 7))),
                    "note": "Show the founder before anything is shared publicly."})
    except Exception as e:
        return _err(f"receipts failed: {e}")


def _cli_setup(parser) -> None:
    sub = parser.add_subparsers(dest="white_cmd")
    sub.add_parser("doctor", help="Check that White is set up to work")
    sub.add_parser("wiki", help="Regenerate the founder wiki")
    sub.add_parser("judge", help="Print what White thinks matters most today")
    cp = sub.add_parser("composio-setup", help="Connect Composio (Platform ak_ key in .env) via an MCP session")
    cp.add_argument("--user-id", default="founder")
    fp = sub.add_parser("face", help="Make White's face: --choices, --seed N, --photo PATH, or traits like --hair curly")
    fp.add_argument("--choices", action="store_true", help="Show 12 faces to pick from")
    fp.add_argument("--options", action="store_true", help="List every trait and its values")
    fp.add_argument("--seed", type=int)
    fp.add_argument("--photo")
    for t in _FACE_TRAITS:
        fp.add_argument(f"--{t}")
    sub.add_parser("phone-setup", help="Connect AgentPhone (AGENTPHONE_API_KEY in .env) via its hosted MCP")
    rp = sub.add_parser("receipts", help="Write a public, redacted, verifiable log of what White did")
    rp.add_argument("--days", type=int, default=7)


def _cli_handler(args) -> int:
    cmd = getattr(args, "white_cmd", None) or "doctor"
    if cmd == "doctor":
        checks = doctor.run(_home())
        print(doctor.format_report(checks))
        return 0 if all(c["ok"] or c["level"] == "warn" for c in checks) else 1
    if cmd == "wiki":
        print(white_wiki({}))
        return 0
    if cmd == "composio-setup":
        import white_composio
        try:
            out = white_composio.setup(_home(), user_id=getattr(args, "user_id", "founder"))
        except white_composio.ComposioSetupError as e:
            print(f"✗ {e}")
            return 1
        print(f"✓ Composio session {out['session_id']} written to config.yaml (key kept in .env only).")
        print(f"  Backup: {out['config_backup']}\n  {out['next']}")
        return 0
    if cmd == "face":
        action = "choices" if getattr(args, "choices", False) else ("options" if getattr(args, "options", False) else "make")
        payload = {"action": action, "seed": getattr(args, "seed", None), "photo": getattr(args, "photo", None),
                   **{t: getattr(args, t, None) for t in _FACE_TRAITS}}
        out = json.loads(white_face(payload))
        if not out["ok"]:
            print(f"✗ {out['error']}")
            return 1
        r = out["result"]
        if action == "choices":
            print(f"Opened 12 faces: {r['sheet']}\nPick one:  hermes -p white white face --seed <number>")
            try:
                import os
                os.startfile(r["sheet"])  # Windows: show the sheet
            except Exception:
                pass
        elif action == "options":
            for k, v in r.items():
                print(f"  --{k:<8} {' | '.join(v)}")
        else:
            print(f"✓ White's face is set ({r['source']}). It shows in the Hermes app: {r['avatar']}")
            if r.get("face"):
                f = r["face"]
                print("  " + ", ".join(f"{k}={f[k]}" for k in _FACE_TRAITS) + f", seed={f['seed']}")
        return 0
    if cmd == "phone-setup":
        import white_composio
        try:
            out = white_composio.phone_setup(_home())
        except white_composio.ComposioSetupError as e:
            print(f"✗ {e}")
            return 1
        print(f"✓ AgentPhone MCP added to config.yaml (key kept in .env only). Backup: {out['config_backup']}")
        return 0
    if cmd == "receipts":
        path = write_receipts(int(getattr(args, "days", 7)))
        print(f"Wrote {path}. Read it before sharing; names are pseudonymized and never-share items redacted.")
        return 0
    if cmd == "judge":
        print(json.dumps(json.loads(white_judge({}))["result"], indent=2, ensure_ascii=False, default=str))
        return 0
    return 1


_HOME_TOKENS = ("${HERMES_HOME}", "$HERMES_HOME", "%HERMES_HOME%")


def expand_home(value: Any, home: str) -> Any:
    """Recursively replace $HERMES_HOME-style tokens in tool arguments with the real profile path."""
    if isinstance(value, str):
        for tok in _HOME_TOKENS:
            if tok in value:
                value = value.replace(tok, home)
        return value
    if isinstance(value, dict):
        return {k: expand_home(v, home) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_home(v, home) for v in value]
    return value


def _on_pre_tool_call(tool_name: str = "", args: dict | None = None, **_: Any):
    """White's skills say `$HERMES_HOME/founder/...`; Hermes file tools don't expand it, which once
    wrote the founder's files into a folder literally named '$HERMES_HOME'. Expand it here."""
    if not isinstance(args, dict):
        return None
    try:
        text = json.dumps(args, default=str)
    except Exception:
        return None
    if not any(tok in text for tok in _HOME_TOKENS):
        return None
    home = str(_home()).replace("\\", "/")
    return {"action": "modify", "args": expand_home(args, home)}


def register(ctx) -> None:
    global _ctx
    _ctx = ctx
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    try:
        ctx.register_cli_command(name="white", help="White: doctor, wiki, judge", setup_fn=_cli_setup,
                                 handler_fn=_cli_handler, description="White founder's office utilities")
    except Exception:  # older Hermes without plugin CLI commands: tools still work
        pass
    for name, (handler, description, properties, required) in _TOOLS.items():
        parameters: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            parameters["required"] = required
        ctx.register_tool(name=name, toolset="white", handler=handler, description=description,
                          schema={"name": name, "description": description, "parameters": parameters},
                          emoji="◇")
