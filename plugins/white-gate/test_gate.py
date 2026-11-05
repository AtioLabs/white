"""Unit tests for White's authority gate. Run: python -m pytest plugins/white-gate -q"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from white_gate_rules import Authority, decide, load_authority  # noqa: E402

EMPTY = Authority()


def test_read_only_tools_pass():
    for tool in ("web_search", "read_file", "web_extract", "kanban_list", "memory"):
        assert decide(tool, {"q": "anything"}, EMPTY).action == "allow"


def test_send_message_needs_approval():
    d = decide("send_message", {"to": "investor@vc.com", "text": "hi"}, EMPTY)
    assert d.action == "approve"


def test_a2a_needs_approval():
    assert decide("a2a_call", {"agent": "x", "message": "intro?"}, EMPTY).action == "approve"


def test_shell_email_send_needs_approval():
    d = decide("terminal", {"command": "himalaya message send < draft.eml"}, EMPTY)
    assert d.action == "approve"


def test_shell_curl_post_needs_approval():
    d = decide("terminal", {"command": "curl -X POST https://api.x.com/2/tweets -d '{}'"}, EMPTY)
    assert d.action == "approve"


def test_plain_shell_passes():
    assert decide("terminal", {"command": "ls -la && python model.py"}, EMPTY).action == "allow"


def test_screen_submit_click_needs_approval():
    d = decide("computer_use", {"action": "click", "target": "Submit application"}, EMPTY)
    assert d.action == "approve"


def test_screen_scroll_passes():
    assert decide("computer_use", {"action": "scroll", "direction": "down"}, EMPTY).action == "allow"


def test_mcp_send_needs_approval_and_read_passes():
    assert decide("mcp_gmail_send_email", {"to": "a@b.c"}, EMPTY).action == "approve"
    assert decide("mcp_gmail_search_threads", {"q": "seed"}, EMPTY).action == "allow"


def test_phone_and_agent_email_need_approval():
    for tool in ("mcp_agentphone_make_call", "mcp_agentphone_send_sms", "mcp_agentphone_buy_number",
                 "mcp_agentmail_send_message", "mcp_agentmail_reply_to_message"):
        assert decide(tool, {"to": "+91..."}, EMPTY).action == "approve", tool
    for tool in ("mcp_agentphone_list_calls", "mcp_agentphone_get_transcript",
                 "mcp_agentphone_account_overview", "mcp_agentmail_list_threads"):
        assert decide(tool, {}, EMPTY).action == "allow", tool
    assert decide("terminal", {"command": "agentmail messages send --to a@b.c"}, EMPTY).action == "approve"
    assert decide("terminal", {"command": "agentmail inboxes list --format json"}, EMPTY).action == "allow"


def test_composio_router_actions_in_args():
    ex = "mcp_composio_COMPOSIO_MULTI_EXECUTE_TOOL"
    sends = [{"tools": [{"tool_slug": "GMAIL_SEND_EMAIL", "arguments": {"to": "a@b.c"}}]},
             {"tools": [{"tool_slug": "LINKEDIN_CREATE_LINKED_IN_POST"}]},
             {"tools": [{"tool_slug": "GMAIL_FETCH_EMAILS"}, {"tool_slug": "SLACK_SEND_MESSAGE"}]},
             {"tools": [{"tool_slug": "GOOGLECALENDAR_CREATE_EVENT"}]}]
    for args in sends:
        assert decide(ex, args, EMPTY).action == "approve", args
    reads = [{"tools": [{"tool_slug": "GMAIL_FETCH_EMAILS"}]},
             {"tools": [{"tool_slug": "GOOGLECALENDAR_LIST_EVENTS"}, {"tool_slug": "NOTION_SEARCH_PAGES"}]},
             {"tools": [{"tool_slug": "GMAIL_CREATE_EMAIL_DRAFT"}]}]
    for args in reads:
        assert decide(ex, args, EMPTY).action == "allow", args
    assert decide("mcp_composio_COMPOSIO_SEARCH_TOOLS", {"q": "send email"}, EMPTY).action == "allow"
    assert decide("mcp_composio_COMPOSIO_REMOTE_WORKBENCH", {"code": "print(1)"}, EMPTY).action == "approve"
    assert decide("mcp_composio_COMPOSIO_REMOTE_BASH_TOOL", {"cmd": "ls"}, EMPTY).action == "approve"
    assert decide("terminal", {"command": "composio execute GMAIL_SEND_EMAIL -d '{}'"}, EMPTY).action == "approve"
    assert decide("terminal", {"command": "composio execute GMAIL_FETCH_EMAILS -d '{}'"}, EMPTY).action == "allow"


def test_never_share_blocks_even_with_permission():
    auth = Authority(
        never_share=["₹42L burn"],
        standing_permissions=[{"id": "all-sends", "tools": ["send_message"]}],
    )
    d = decide("send_message", {"text": "Our ₹42L BURN is fine"}, auth)
    assert d.action == "block"
    assert "never-share" in d.reason


def test_standing_permission_allows_matching_only():
    auth = Authority(standing_permissions=[
        {"id": "followups", "tools": ["send_message"], "args_regex": r"Re: seed"},
    ])
    assert decide("send_message", {"text": "Re: seed round follow-up"}, auth).action == "allow"
    assert decide("send_message", {"text": "Cold intro"}, auth).action == "approve"


def test_wildcard_tool_permission():
    auth = Authority(standing_permissions=[{"id": "gmail", "tools": ["mcp_gmail_send*"]}])
    assert decide("mcp_gmail_send_email", {"to": "x"}, auth).action == "allow"


def test_safe_tools_override():
    auth = Authority(safe_tools=["send_message"])
    assert decide("send_message", {"to": "founder-self"}, auth).action == "allow"


def test_missing_policy_file_means_approval(tmp_path):
    auth = load_authority(tmp_path / "nope.yaml")
    assert decide("send_message", {"text": "x"}, auth).action == "approve"


def test_corrupt_policy_file_means_approval(tmp_path):
    p = tmp_path / "authority.yaml"
    p.write_text("never_share: [unclosed", encoding="utf-8")
    assert decide("send_message", {"text": "x"}, load_authority(p)).action == "approve"


def test_policy_file_loads(tmp_path):
    p = tmp_path / "authority.yaml"
    p.write_text(
        "never_share: ['secret customer']\n"
        "standing_permissions:\n  - id: p1\n    tools: [a2a_call]\n",
        encoding="utf-8",
    )
    auth = load_authority(p)
    assert decide("a2a_call", {"m": "hello"}, auth).action == "allow"
    assert decide("a2a_call", {"m": "about Secret Customer"}, auth).action == "block"


def test_desktop_send_click_needs_approval():
    d = decide("white_desktop", {"command": "click", "ref": "@s1:e8", "label": "Send"}, EMPTY)
    assert d.action == "approve"


def test_desktop_read_and_safe_click_pass():
    assert decide("white_desktop", {"command": "snapshot", "args": ["--app", "Notepad"]}, EMPTY).action == "allow"
    assert decide("white_desktop", {"command": "click", "ref": "@s1:e3", "label": "File"}, EMPTY).action == "allow"


def test_desktop_enter_needs_approval():
    d = decide("white_desktop", {"command": "press", "args": ["Enter"], "label": "new line"}, EMPTY)
    assert d.action == "approve"


def test_raw_agent_desktop_action_in_shell_needs_approval():
    assert decide("terminal", {"command": "agent-desktop click @s1:e8"}, EMPTY).action == "approve"
    assert decide("terminal", {"command": "agent-desktop snapshot --app Slack -i"}, EMPTY).action == "allow"


def test_white_cannot_rewrite_its_own_code_or_authority():
    p = r"C:\Users\x\AppData\Local\hermes\profiles\white\plugins\white-core\white_world.py"
    assert decide("write_file", {"path": p, "content": "x"}, EMPTY).action == "approve"
    assert decide("patch", {"path": "founder/authority.yaml", "patch": "x"}, EMPTY).action == "approve"
    assert decide("terminal", {"command": f"python -c \"open(r'{p}','w').write('x')\""}, EMPTY).action == "approve"
    assert decide("terminal", {"command": "Set-Content config.yaml 'model: x'"}, EMPTY).action == "approve"


def test_reading_own_code_and_normal_writes_pass():
    assert decide("terminal", {"command": "type plugins\white-core\white_world.py"}, EMPTY).action == "allow"
    assert decide("write_file", {"path": "founder/drafts/proposal.md", "content": "x"}, EMPTY).action == "allow"


def test_skill_edits_go_through_white_improve():
    assert decide("skill_manage", {"action": "patch", "name": "white-cycle"}, EMPTY).action == "approve"
    assert decide("skill_manage", {"action": "view", "name": "white-cycle"}, EMPTY).action == "allow"


def test_protection_not_overridable_by_safe_tools():
    a = Authority(safe_tools=["write_file"])
    assert decide("write_file", {"path": "plugins/white-gate/__init__.py", "content": ""}, a).action == "approve"


def _hook(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("wg", Path(__file__).parent / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "_home", lambda: tmp_path)
    return mod._on_pre_tool_call


def test_yolo_turns_approvals_into_blocks(tmp_path, monkeypatch):
    hook = _hook(tmp_path, monkeypatch)
    monkeypatch.delenv("HERMES_YOLO_MODE", raising=False)
    assert hook("send_message", {"to": "x", "text": "hi"})["action"] == "approve"
    monkeypatch.setenv("HERMES_YOLO_MODE", "1")
    r = hook("send_message", {"to": "x", "text": "hi"})
    assert r["action"] == "block" and "YOLO" in r["message"]
    assert hook("web_search", {"q": "x"}) is None  # reads still work


def test_approvals_off_turns_approvals_into_blocks(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_YOLO_MODE", raising=False)
    (tmp_path / "config.yaml").write_text("approvals:\n  mode: off\n  timeout: 300\n", encoding="utf-8")
    hook = _hook(tmp_path, monkeypatch)
    assert hook("send_message", {"to": "x", "text": "hi"})["action"] == "block"


def test_hermes_unattended_turn_blocks(tmp_path, monkeypatch):
    import sys as _sys
    import types
    monkeypatch.delenv("HERMES_YOLO_MODE", raising=False)
    fake_tools = types.ModuleType("tools")
    fake_approval = types.ModuleType("tools.approval")
    fake_approval._yolo_active = lambda: True
    fake_tools.approval = fake_approval
    monkeypatch.setitem(_sys.modules, "tools", fake_tools)
    monkeypatch.setitem(_sys.modules, "tools.approval", fake_approval)
    hook = _hook(tmp_path, monkeypatch)
    assert hook("send_message", {"to": "x", "text": "hi"})["action"] == "block"
