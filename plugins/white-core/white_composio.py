"""Connect White to Composio Platform with a project key (`ak_...`) via a Tool Router session over MCP.

`hermes -p white white composio-setup`:
  1. reads COMPOSIO_API_KEY from the profile's .env (never printed, never written elsewhere),
  2. creates a session for this founder (POST /api/v3.1/tool_router/session),
  3. writes mcp_servers.composio into config.yaml with the session's MCP URL and headers, replacing
     the key itself with "${COMPOSIO_API_KEY}" so the secret stays only in .env,
  4. saves the session id to white/composio.json and backs up config.yaml first.
Docs: https://docs.composio.dev/docs/sessions-via-mcp.md
"""

from __future__ import annotations

import json
import re
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional

API = "https://backend.composio.dev/api/v3.1/tool_router/session"
ENV_NAME = "COMPOSIO_API_KEY"


class ComposioSetupError(RuntimeError):
    pass


def read_env_key(env_path: Path, name: str = ENV_NAME) -> Optional[str]:
    if not env_path.is_file():
        return None
    m = re.search(rf"^{re.escape(name)}\s*=\s*['\"]?([^'\"\s]+)", env_path.read_text(encoding="utf-8", errors="ignore"),
                  re.MULTILINE)
    return m.group(1) if m else None


def _http_post(url: str, headers: dict, body: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https URL)
        return json.loads(resp.read().decode("utf-8"))


def create_session(key: str, user_id: str, post: Callable[..., dict] = _http_post) -> dict:
    try:
        data = post(API, {"x-api-key": key}, {"user_id": user_id})
    except Exception as e:  # don't leak the key through exception text
        raise ComposioSetupError(f"Composio session request failed: {type(e).__name__}: "
                                 f"{str(e).replace(key, '[key]')}") from None
    mcp = data.get("mcp") or {}
    if not mcp.get("url"):
        raise ComposioSetupError("Composio didn't return an MCP URL. Check the key is a Platform project key (ak_).")
    return {"session_id": data.get("session_id") or data.get("id"), "url": mcp["url"],
            "headers": mcp.get("headers") or {"x-api-key": key}}


def safe_headers(headers: dict, key: str) -> dict:
    """Replace the secret with an env reference; keep non-secret headers (org/project ids) as given."""
    return {k: ("${" + ENV_NAME + "}" if v == key else v) for k, v in headers.items()}


def write_config(config_path: Path, url: str, headers: dict) -> Path:
    return write_config_entry(config_path, "composio", {"url": url, "headers": headers})


def write_config_entry(config_path: Path, name: str, entry: dict) -> Path:
    try:
        import hermes_yaml as yaml  # Hermes runtime ships ruamel via hermes_yaml, not PyYAML
    except ImportError:
        import yaml
    backup = config_path.with_name(config_path.name + f".bak-white-{int(time.time())}")
    if config_path.is_file():
        shutil.copy2(config_path, backup)
    rt = getattr(yaml, "roundtrip_yaml", None)
    if rt is not None:  # inside Hermes: keep the user's comments and formatting
        from io import StringIO
        y = rt()
        cfg = (y.load(config_path.read_text(encoding="utf-8")) if config_path.is_file() else None) or {}
        servers = cfg.get("mcp_servers")
        if servers is None:
            cfg["mcp_servers"] = servers = {}
        servers[name] = {k: (dict(v) if isinstance(v, dict) else v) for k, v in entry.items()}
        buf = StringIO()
        y.dump(cfg, buf)
        config_path.write_text(buf.getvalue(), encoding="utf-8")
        return backup
    cfg = (yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.is_file() else None) or {}
    cfg.setdefault("mcp_servers", {})[name] = entry
    config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return backup


def add_http_mcp(home: Path, name: str, url: str, headers: dict) -> Path:
    """Add any hosted MCP server to config.yaml (headers should reference ${ENV_VARS}, never raw keys)."""
    for v in headers.values():
        if "${" not in str(v):
            raise ComposioSetupError(f"Header for {name} must reference an env var like ${{NAME}}, not a raw value.")
    return write_config_entry(home / "config.yaml", name, {"url": url, "headers": headers})


def phone_setup(home: Path) -> dict:
    """Connect AgentPhone's hosted MCP (docs.agentphone.ai/integrations/connect-your-ai)."""
    if not read_env_key(home / ".env", "AGENTPHONE_API_KEY"):
        raise ComposioSetupError("No AGENTPHONE_API_KEY in this profile's .env.")
    backup = add_http_mcp(home, "agentphone", "https://mcp.agentphone.ai/mcp",
                          {"Authorization": "Bearer ${AGENTPHONE_API_KEY}"})
    return {"config_backup": str(backup)}


def setup(home: Path, user_id: str = "founder", post: Callable[..., dict] = _http_post) -> dict:
    key = read_env_key(home / ".env")
    if not key:
        raise ComposioSetupError(f"No {ENV_NAME} in {home / '.env'}. Add it there (never in chat).")
    if not key.startswith("ak_"):
        raise ComposioSetupError(f"{ENV_NAME} doesn't look like a Platform project key (ak_...).")
    sess = create_session(key, user_id, post)
    headers = safe_headers(sess["headers"], key)
    if any(key in str(v) for v in headers.values()):
        raise ComposioSetupError("Refusing to write the key into config.yaml.")
    backup = write_config(home / "config.yaml", sess["url"], headers)
    state = {"session_id": sess["session_id"], "user_id": user_id, "created": time.time(), "url": sess["url"]}
    (home / "white").mkdir(parents=True, exist_ok=True)
    (home / "white" / "composio.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return {"session_id": sess["session_id"], "config_backup": str(backup),
            "next": "Restart White's chat; the Composio tools (COMPOSIO_SEARCH_TOOLS, ...) should appear."}
