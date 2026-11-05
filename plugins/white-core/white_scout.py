"""White's skill scout (White 2.0, point 3): find, inspect and install skills by itself.

Rules enforced in code, not in the prompt:
- only GitHub repos with >= MIN_STARS stars, a license, not archived, pushed in the last year;
- code inspection before install: no binaries, no install hooks, no secret/credential access,
  no obfuscated execution; network use is allowed but recorded (the gate still checks actions);
- skills only (folders with SKILL.md): never system installs;
- every install leaves a receipt in `white/scout.json`.
Stdlib only.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

MIN_STARS = 1000
MAX_AGE_DAYS = 365
MAX_ZIP_BYTES = 30 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
UA = "white-scout/0.1 (+https://github.com/AtioLabs/white)"

BINARY_EXT = {".exe", ".dll", ".so", ".dylib", ".bin", ".msi", ".pkg", ".deb", ".rpm", ".jar", ".class",
              ".pyc", ".node", ".wasm", ".app", ".scr", ".com"}
TEXT_EXT = {".md", ".txt", ".py", ".js", ".mjs", ".cjs", ".ts", ".sh", ".ps1", ".json", ".yaml", ".yml",
            ".toml", ".html", ".css", ".csv", ".bash", ".zsh", ".rb", ".go", ".rs", ".sql", ".xml", ".ini", ""}

# (finding, regex) -> blocks install
BLOCK = [
    ("reads secrets or credentials", re.compile(
        r"(\.ssh[/\\]|id_rsa|\.aws[/\\]credentials|\.netrc|keychain|Login Data|cookies\.sqlite|"
        r"\.hermes[/\\]\.env|auth\.json|os\.environ\b[^\n]{0,40}(KEY|TOKEN|SECRET|PASSWORD)|"
        r"process\.env\.[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)|\$env:[A-Z_]*(KEY|TOKEN|SECRET)|"
        r"getenv\([^)]*(KEY|TOKEN|SECRET|PASSWORD))", re.IGNORECASE)),
    ("obfuscated execution", re.compile(
        r"(eval\s*\(\s*(atob|base64|Buffer\.from|codecs\.decode|bytes\.fromhex)|exec\s*\(\s*(base64|zlib|codecs|bytes\.fromhex|marshal)|"
        r"base64\s+(-d|--decode)\s*\|\s*(sh|bash)|FromBase64String|-EncodedCommand|"
        r"curl[^\n|]*\|\s*(sh|bash|python)|wget[^\n|]*\|\s*(sh|bash)|iex\s*\(\s*(irm|iwr|New-Object\s+Net\.WebClient))",
        re.IGNORECASE)),
    ("long encoded blob", re.compile(r"[A-Za-z0-9+/]{400,}={0,2}")),
    ("persistence or system change", re.compile(
        r"(crontab\s+-|schtasks\s+/create|Register-ScheduledTask|reg\s+add\s+HK|Set-ItemProperty\s+-Path\s+HK|"
        r"launchctl\s+load|systemctl\s+enable|\.bashrc|\.zshrc|\$PROFILE|Set-ExecutionPolicy|sudo\s)", re.IGNORECASE)),
]
NETWORK = re.compile(r"(requests\.(get|post|put)|urllib\.request|httpx\.|fetch\(|axios|curl\s|wget\s|"
                     r"Invoke-WebRequest|Invoke-RestMethod|socket\.)", re.IGNORECASE)
INSTALL_HOOKS = {"setup.py", "postinstall", "preinstall", "install.sh", "install.ps1"}

Fetcher = Callable[[str], bytes]


def _http(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(MAX_ZIP_BYTES + 1)
    if len(data) > MAX_ZIP_BYTES:
        raise ValueError("download too large")
    return data


# ---- scan: what the founder already has --------------------------------------------------------

KNOWN_CLIS = ["git", "gh", "node", "npm", "python", "uv", "docker", "ffmpeg", "agent-desktop", "himalaya",
              "composio", "vercel", "supabase", "stripe", "gcloud", "aws", "az", "code", "cursor", "ollama",
              "lms", "pandoc", "rg", "jq", "kubectl", "terraform", "flyctl", "railway", "netlify", "wrangler"]


def scan(home: Path) -> dict:
    """Inventory: installed CLIs, Hermes skills, connected apps, model providers. White compares this
    with the charter to find capabilities the founder owns but doesn't use."""
    skills_dir = home / "skills"
    skills = sorted({p.parent.name for p in skills_dir.rglob("SKILL.md")}) if skills_dir.is_dir() else []
    cfg = home / "config.yaml"
    providers = []
    if cfg.exists():
        txt = cfg.read_text(encoding="utf-8", errors="replace")
        providers = sorted(set(re.findall(r"^\s*-?\s*provider:\s*([\w:-]+)", txt, re.M)) |
                           set(re.findall(r"base_url:\s*https?://([^/\s]+)", txt)))
    apps = []
    comp = home / "white" / "composio.json"
    if comp.exists():
        try:
            data = json.loads(comp.read_text(encoding="utf-8"))
            apps = sorted({str(a) for a in (data.get("connected") or data.get("toolkits") or [])})
        except Exception:
            pass
    return {"clis": [c for c in KNOWN_CLIS if shutil.which(c)], "skills": skills,
            "providers": providers, "connected_apps": apps,
            "scouted": [r["name"] for r in registry(home)]}


# ---- search ------------------------------------------------------------------------------------

def _recent(iso: str, now: float) -> bool:
    try:
        t = time.mktime(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return False
    return now - t <= MAX_AGE_DAYS * 86400


def eligible(repo: dict, now: Optional[float] = None) -> Optional[str]:
    """None if the repo passes the bar, else the reason it doesn't."""
    now = now or time.time()
    if int(repo.get("stargazers_count") or 0) < MIN_STARS:
        return f"{repo.get('stargazers_count', 0)} stars < {MIN_STARS}"
    if repo.get("archived"):
        return "archived"
    if not (repo.get("license") or {}).get("spdx_id") or (repo.get("license") or {}).get("spdx_id") == "NOASSERTION":
        return "no clear license"
    if not _recent(str(repo.get("pushed_at") or ""), now):
        return "not updated in a year"
    return None


def search(need: str, fetch: Fetcher = _http, limit: int = 8) -> dict:
    q = f"{need} SKILL.md in:readme stars:>={MIN_STARS}"  # README mentioning SKILL.md = real skill repos
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": 20})
    items = json.loads(fetch(url)).get("items") or []
    ok, rejected = [], []
    for r in items:
        why = eligible(r)
        row = {"repo": r.get("full_name"), "stars": r.get("stargazers_count"), "desc": r.get("description"),
               "license": (r.get("license") or {}).get("spdx_id"), "pushed": r.get("pushed_at"),
               "branch": r.get("default_branch") or "main"}
        (rejected if why else ok).append({**row, **({"why": why} if why else {})})
    return {"candidates": ok[:limit], "rejected": rejected[:limit]}


# ---- fetch into quarantine -----------------------------------------------------------------------

def _safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")[:80] or "skill"


def fetch_repo(home: Path, repo: str, fetch: Fetcher = _http) -> Path:
    """Check the bar again (never trust a search result), then unzip into quarantine."""
    if not re.fullmatch(r"[A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*", repo or ""):
        raise ValueError("repo must be owner/name")
    meta = json.loads(fetch(f"https://api.github.com/repos/{repo}"))
    why = eligible(meta)
    if why:
        raise ValueError(f"{repo} doesn't meet the bar: {why}")
    branch = meta.get("default_branch") or "main"
    data = fetch(f"https://codeload.github.com/{repo}/zip/refs/heads/{urllib.parse.quote(branch)}")
    q = home / "white" / "quarantine" / _safe_name(repo.replace("/", "__"))
    if q.exists():
        shutil.rmtree(q)
    q.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            parts = Path(info.filename).parts[1:]  # drop the "<repo>-<branch>/" root
            if not parts or info.is_dir():
                continue
            if any(p in ("..", "") or ":" in p for p in parts) or Path(info.filename).is_absolute():
                raise ValueError(f"unsafe path in archive: {info.filename}")
            if info.file_size > MAX_FILE_BYTES:
                continue  # big assets are skipped, never executed
            dest = q.joinpath(*parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(info))
    (q / ".white-meta.json").write_text(json.dumps({
        "repo": repo, "stars": meta.get("stargazers_count"), "license": (meta.get("license") or {}).get("spdx_id"),
        "branch": branch, "fetched": time.time()}), encoding="utf-8")
    return q


# ---- inspect -----------------------------------------------------------------------------------

def inspect(folder: Path) -> dict:
    """Static checks. passed=False if anything in BLOCK, a binary or an install hook is found."""
    findings, network, skills = [], [], []
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.name == ".white-meta.json":
            continue
        rel = str(p.relative_to(folder)).replace("\\", "/")
        if p.name == "SKILL.md":
            skills.append(str(p.parent.relative_to(folder)).replace("\\", "/") or ".")
        ext = p.suffix.lower()
        if ext in BINARY_EXT:
            findings.append({"file": rel, "issue": "binary file"})
            continue
        if p.name.lower() in INSTALL_HOOKS:
            findings.append({"file": rel, "issue": "install hook"})
        if ext not in TEXT_EXT and not p.name.startswith("."):
            continue  # images, fonts: data only
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.name == "package.json" and re.search(r'"(pre|post)?install"\s*:', text):
            findings.append({"file": rel, "issue": "npm install hook"})
        for issue, rx in BLOCK:
            m = rx.search(text)
            if m:
                findings.append({"file": rel, "issue": issue, "match": m.group(0)[:80]})
        if NETWORK.search(text):
            network.append(rel)
    if not skills:
        findings.append({"file": "-", "issue": "no SKILL.md: not a skill"})
    return {"passed": not findings, "findings": findings, "network_files": network, "skills": skills}


def _frontmatter_ok(skill_md: Path) -> Optional[str]:
    t = skill_md.read_text(encoding="utf-8", errors="replace")
    if not t.startswith("---"):
        return "SKILL.md has no frontmatter"
    head = t.split("---", 2)[1] if t.count("---") >= 2 else ""
    if not re.search(r"^name:\s*\S", head, re.M) or not re.search(r"^description:\s*\S", head, re.M):
        return "SKILL.md frontmatter needs name and description"
    return None


# ---- install -----------------------------------------------------------------------------------

def registry(home: Path) -> list[dict]:
    f = home / "white" / "scout.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []


def install(home: Path, folder: Path, why: str, only: Optional[list] = None) -> dict:
    """Re-inspect (never trust an earlier pass), dry-run check each skill, copy to skills/scouted/.
    `only`: skill folder names to take from a multi-skill repo (default: all)."""
    if not (why or "").strip():
        raise ValueError("say which task needs this skill")
    report = inspect(folder)
    if not report["passed"]:
        return {"installed": [], "blocked": report["findings"]}
    meta = json.loads((folder / ".white-meta.json").read_text(encoding="utf-8"))
    installed, problems = [], []
    for rel in report["skills"]:
        if only and Path(rel).name not in only:
            continue
        src = folder / rel if rel != "." else folder
        bad = _frontmatter_ok(src / "SKILL.md")
        if bad:
            problems.append({"skill": rel, "issue": bad})
            continue
        name = _safe_name(src.name if rel != "." else meta["repo"].split("/")[1])
        dst = home / "skills" / "scouted" / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".white-meta.json", ".git*"))
        installed.append(name)
    reg = [r for r in registry(home) if r["name"] not in installed]
    for name in installed:
        reg.append({"name": name, "repo": meta["repo"], "stars": meta["stars"], "license": meta["license"],
                    "why": why, "network": report["network_files"], "installed": time.time()})
    (home / "white").mkdir(parents=True, exist_ok=True)
    (home / "white" / "scout.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return {"installed": installed, "problems": problems, "network_files": report["network_files"]}
