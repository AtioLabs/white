"""Tests for Composio Platform setup (no network: the HTTP call is faked)."""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))

import white_composio as C  # noqa: E402

KEY = "ak_TESTSECRET999"


def home_with(tmp_path, env=f"COMPOSIO_API_KEY={KEY}\n", cfg="model: {default: m}\nplugins: {enabled: [white-core]}\n"):
    (tmp_path / ".env").write_text(env, encoding="utf-8")
    (tmp_path / "config.yaml").write_text(cfg, encoding="utf-8")
    return tmp_path


def fake_post(seen):
    def post(url, headers, body):
        seen.update(url=url, headers=headers, body=body)
        return {"session_id": "trs_1", "mcp": {"url": "https://backend.composio.dev/tool_router/trs_1/mcp",
                                               "headers": {"x-api-key": headers["x-api-key"], "x-project-id": "p1"}}}
    return post


def test_setup_writes_env_reference_not_key(tmp_path):
    seen = {}
    home = home_with(tmp_path)
    out = C.setup(home, user_id="asrul", post=fake_post(seen))
    assert seen["url"] == C.API and seen["body"] == {"user_id": "asrul"} and seen["headers"]["x-api-key"] == KEY
    cfg_text = (home / "config.yaml").read_text(encoding="utf-8")
    assert KEY not in cfg_text
    cfg = yaml.safe_load(cfg_text)
    assert cfg["model"] == {"default": "m"} and cfg["plugins"]["enabled"] == ["white-core"]  # preserved
    comp = cfg["mcp_servers"]["composio"]
    assert comp["headers"] == {"x-api-key": "${COMPOSIO_API_KEY}", "x-project-id": "p1"}
    assert comp["url"].endswith("/mcp")
    state = json.loads((home / "white" / "composio.json").read_text())
    assert state["session_id"] == "trs_1" and KEY not in json.dumps(state)
    assert Path(out["config_backup"]).is_file()


def test_missing_or_wrong_key(tmp_path):
    with pytest.raises(C.ComposioSetupError):
        C.setup(home_with(tmp_path, env=""), post=fake_post({}))
    with pytest.raises(C.ComposioSetupError):
        C.setup(home_with(tmp_path, env="COMPOSIO_API_KEY=ck_consumer\n"), post=fake_post({}))


def test_http_error_does_not_leak_key(tmp_path):
    def boom(url, headers, body):
        raise RuntimeError(f"401 for key {headers['x-api-key']}")
    with pytest.raises(C.ComposioSetupError) as e:
        C.setup(home_with(tmp_path), post=boom)
    assert KEY not in str(e.value)


def test_phone_setup(tmp_path):
    home = home_with(tmp_path, env=f"COMPOSIO_API_KEY={KEY}\nAGENTPHONE_API_KEY=sk_live_SECRET\n")
    C.setup(home, post=fake_post({}))
    C.phone_setup(home)
    text = (home / "config.yaml").read_text(encoding="utf-8")
    assert "sk_live_SECRET" not in text and KEY not in text
    servers = yaml.safe_load(text)["mcp_servers"]
    assert set(servers) == {"composio", "agentphone"}
    assert servers["agentphone"]["headers"]["Authorization"] == "Bearer ${AGENTPHONE_API_KEY}"
    with pytest.raises(C.ComposioSetupError):
        C.add_http_mcp(home, "x", "https://x", {"Authorization": "Bearer raw"})
    with pytest.raises(C.ComposioSetupError):
        C.phone_setup(home_with(tmp_path / "n" if (tmp_path / "n").mkdir() is None else tmp_path, env=""))


def test_no_mcp_url(tmp_path):
    with pytest.raises(C.ComposioSetupError):
        C.setup(home_with(tmp_path), post=lambda u, h, b: {"session_id": "x"})
