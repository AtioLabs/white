"""The plugin registers exactly the tools its manifest declares, each with a valid schema."""

import importlib.util
from pathlib import Path

import yaml

HERE = Path(__file__).parent


def load_plugin():
    spec = importlib.util.spec_from_file_location("white_core_plugin", HERE / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeCtx:
    def __init__(self):
        self.tools, self.cli, self.hooks = {}, [], {}

    def register_hook(self, name, cb):
        self.hooks[name] = cb

    def register_tool(self, name, toolset, schema, handler, **kw):
        self.tools[name] = (toolset, schema, handler)

    def register_cli_command(self, **kw):
        self.cli.append(kw["name"])


def test_registers_manifest_tools():
    mod = load_plugin()
    ctx = FakeCtx()
    mod.register(ctx)
    declared = set(yaml.safe_load((HERE / "plugin.yaml").read_text(encoding="utf-8"))["provides_tools"])
    assert set(ctx.tools) == declared
    for name, (toolset, schema, handler) in ctx.tools.items():
        assert toolset == "white" and callable(handler)
        assert schema["name"] == name and schema["parameters"]["type"] == "object"
        assert len(schema["description"]) > 40
    assert ctx.cli == ["white"]
    assert "pre_tool_call" in ctx.hooks


def test_hermes_home_token_expanded(tmp_path):
    mod = load_plugin()
    mod._home = lambda: tmp_path
    home = str(tmp_path).replace("\\", "/")
    out = mod._on_pre_tool_call("write_file", {"path": "$HERMES_HOME/founder/voice.md", "content": "x"})
    assert out == {"action": "modify", "args": {"path": f"{home}/founder/voice.md", "content": "x"}}
    out = mod._on_pre_tool_call("terminal", {"command": "type ${HERMES_HOME}\\founder\\company.md"})
    assert out["args"]["command"].startswith(f"type {home}")
    assert mod._on_pre_tool_call("read_file", {"path": "C:/x.md"}) is None
