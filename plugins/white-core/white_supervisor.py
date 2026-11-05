"""White's supervisor: checks work before the founder sees it (the Sierra lesson).

Two layers:
  1. Deterministic checks in code: never-share leaks, voice violations, AI tells, length limits,
     missing sources for factual work, missing or broken proof.
  2. An optional model review against a rubric (facts, voice, contract, judgment), done by a
     separate LLM call so the worker doesn't grade its own homework in the same context.

A draft passes only if no check returns a "fail" issue. "warn" issues are shown but don't block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# Phrases that make writing sound machine-made (extend from the humanizer skill over time).
AI_TELLS = [
    "i hope this email finds you well", "i hope this finds you well", "delve", "in today's fast-paced",
    "game-changer", "game changer", "revolutionize", "revolutionise", "unlock the power", "leverage synergies",
    "cutting-edge", "seamless", "seamlessly", "i wanted to reach out", "just circling back",
    "just checking in", "touch base", "at the end of the day", "it's worth noting", "furthermore,",
    "moreover,", "in conclusion", "elevate your", "embark on", "a testament to", "navigate the complexities",
]

LIMITS = {  # kind → (max words, max chars); None = no limit
    "cold_email": (120, None),
    "investor_email": (150, None),
    "followup": (90, None),
    "linkedin_note": (None, 300),
    "post": (300, None),
    "checkin": (220, None),
}
FACTUAL_KINDS = {"report", "brief", "plan", "application", "investor_update", "checkin", "research"}
_NUMBER = re.compile(r"(\d[\d,.]*\s?(%|x|k|m|cr|crore|lakh|l|bn|b|months?|days?|users?|customers?)?)|[₹$€£]\s?\d",
                     re.IGNORECASE)
_URL = re.compile(r"https?://\S+")


@dataclass
class Issue:
    severity: str   # fail | warn
    check: str
    message: str

    def as_dict(self) -> dict:
        return {"severity": self.severity, "check": self.check, "message": self.message}


@dataclass
class Review:
    passed: bool
    issues: list[Issue] = field(default_factory=list)
    model_notes: Optional[str] = None

    def as_dict(self) -> dict:
        return {"pass": self.passed, "issues": [i.as_dict() for i in self.issues],
                "model_notes": self.model_notes}


# ---- founder context -------------------------------------------------------------------------------

def voice_never_words(voice_md: str) -> list[str]:
    """Bullet items under the '## Words they never use' heading of voice.md."""
    m = re.search(r"^##\s*Words they never use\s*$(.*?)(^##\s|\Z)", voice_md, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not m:
        return []
    words = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith(("-", "*")):
            w = line.lstrip("-* ").strip().strip('"\'')
            if w:
                words.append(w)
    return words


def never_share_list(authority_yaml: Path) -> list[str]:
    if not authority_yaml.is_file():
        return []
    try:
        try:
            import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
        except ImportError:
            import yaml
        data = yaml.safe_load(authority_yaml.read_text(encoding="utf-8")) or {}
        return [str(x) for x in (data.get("never_share") or []) if str(x).strip()]
    except Exception:
        return []


# ---- deterministic checks ----------------------------------------------------------------------------

def check(text: str, kind: str, *, sources: Optional[list] = None, proof: Optional[list] = None,
          never_share: Optional[list] = None, never_words: Optional[list] = None,
          proof_exists: Optional[Callable[[str], bool]] = None) -> list[Issue]:
    issues: list[Issue] = []
    low = text.lower()

    for item in never_share or []:
        if item.lower() in low:
            issues.append(Issue("fail", "never_share", f"Contains '{item}', which is on the never-share list."))

    for w in never_words or []:
        if re.search(rf"\b{re.escape(w.lower())}\b", low):
            issues.append(Issue("fail", "voice", f"Uses '{w}'; the founder never uses that word."))

    tells = [t for t in AI_TELLS if t in low]
    if tells:
        issues.append(Issue("fail" if len(tells) >= 2 else "warn", "ai_tells",
                            "Sounds machine-written: " + ", ".join(f"'{t}'" for t in tells) + ". Run humanizer."))
    if text.count("—") >= 3:
        issues.append(Issue("warn", "ai_tells", "Heavy em-dash use reads as AI-written."))

    max_words, max_chars = LIMITS.get(kind, (None, None))
    n_words = len(text.split())
    if max_words and n_words > max_words:
        issues.append(Issue("fail", "length", f"{n_words} words; a {kind} should be at most {max_words}."))
    if max_chars and len(text) > max_chars:
        issues.append(Issue("fail", "length", f"{len(text)} characters; a {kind} allows at most {max_chars}."))

    if kind in FACTUAL_KINDS and _NUMBER.search(text) and not (sources or _URL.search(text)):
        issues.append(Issue("fail", "sources", "Has numbers or facts but no sources. Cite where each comes from."))

    for p in proof or []:
        p = str(p).strip()
        if not p:
            issues.append(Issue("fail", "proof", "Empty proof entry."))
        elif proof_exists and not proof_exists(p):
            issues.append(Issue("fail", "proof", f"Proof '{p}' doesn't exist or can't be opened."))

    if re.search(r"\[(name|company|insert|todo|tbd)[^\]]*\]|\{\{.*?\}\}|<(name|company)>", text, re.IGNORECASE):
        issues.append(Issue("fail", "placeholder", "Unfilled placeholder left in the draft."))
    return issues


def default_proof_exists(p: str) -> bool:
    """Local paths must exist. URLs and message ids pass here; the model check verifies them."""
    if _URL.match(p) or ":" in p and not re.match(r"^[A-Za-z]:[\\/]", p):
        return True
    return Path(p).expanduser().exists()


# ---- model review ------------------------------------------------------------------------------------

RUBRIC = """You are White's supervisor: a demanding chief of staff checking work before the founder sees it.
Review the draft against:
1. Facts: is every factual claim supported by the listed sources? Flag anything unsupported or likely stale.
2. Voice: does it sound like the founder (voice profile below), specific and human, not generic?
3. Contract: does it achieve the stated goal ("done means")? Is the ask clear?
4. Judgment: would a sharp operator send this? Any risk to relationships or reputation?
Be strict but fair. Only fail for real problems."""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "pass": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["fail", "warn"]},
            "check": {"type": "string"}, "message": {"type": "string"}},
            "required": ["severity", "check", "message"]}},
        "notes": {"type": "string"},
    },
    "required": ["pass", "issues"],
}


def model_review(llm_structured: Callable[..., Any], text: str, kind: str, goal: str,
                 sources: list, voice_md: str) -> tuple[list[Issue], Optional[str]]:
    """llm_structured(instructions, input, json_schema, ...) → object with .parsed (ctx.llm shape)."""
    prompt = (f"Kind: {kind}\nGoal / done means: {goal or '(not given)'}\n"
              f"Sources: {sources or '(none)'}\n\nFounder voice profile:\n{voice_md[:3000]}\n\n"
              f"--- DRAFT ---\n{text}\n--- END ---")
    result = llm_structured(instructions=RUBRIC, input=[{"type": "text", "text": prompt}],
                            json_schema=REVIEW_SCHEMA, purpose="white.supervisor", temperature=0.0,
                            max_tokens=700)
    parsed = getattr(result, "parsed", None)
    if not isinstance(parsed, dict):
        return [Issue("warn", "model_review", "Supervisor model gave no valid verdict; deterministic checks only.")], None
    issues = [Issue(i.get("severity", "warn") if i.get("severity") in ("fail", "warn") else "warn",
                    str(i.get("check", "model")), str(i.get("message", "")))
              for i in parsed.get("issues") or [] if isinstance(i, dict)]
    if parsed.get("pass") is False and not any(i.severity == "fail" for i in issues):
        issues.append(Issue("fail", "model_review", parsed.get("notes") or "Supervisor model failed the draft."))
    return issues, parsed.get("notes")


def review(text: str, kind: str, *, goal: str = "", sources: Optional[list] = None,
           proof: Optional[list] = None, voice_md: str = "", never_share: Optional[list] = None,
           llm_structured: Optional[Callable[..., Any]] = None,
           proof_exists: Callable[[str], bool] = default_proof_exists) -> Review:
    issues = check(text, kind, sources=sources, proof=proof, never_share=never_share,
                   never_words=voice_never_words(voice_md), proof_exists=proof_exists)
    notes = None
    if llm_structured is not None:
        try:
            more, notes = model_review(llm_structured, text, kind, goal, sources or [], voice_md)
            issues += more
        except Exception as exc:
            issues.append(Issue("warn", "model_review", f"Supervisor model unavailable ({exc})."))
    return Review(passed=not any(i.severity == "fail" for i in issues), issues=issues, model_notes=notes)
